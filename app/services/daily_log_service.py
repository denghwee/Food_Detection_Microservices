# app/services/daily_log_service.py
from datetime import date, timedelta, datetime

from sqlalchemy import func

from app import db
from app.models.daily_energy_log import DailyEnergyLog
from app.models.user_profile import UserProfile
from app.models.user_profile_weight_history import UserProfileWeightHistory
from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum

ACTIVITY_FACTOR = {
    ActivityLevelEnum.sedentary: 1.2,
    ActivityLevelEnum.lightly_active: 1.375,
    ActivityLevelEnum.moderately_active: 1.55,
    ActivityLevelEnum.very_active: 1.725,
    ActivityLevelEnum.extremely_active: 1.9,
}



def get_latest_user_metrics(user_id: int):
    """
    Lấy chiều cao, cân nặng gần nhất của user
    """
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None, None, None, None

    last_history = (
        UserProfileWeightHistory.query
        .filter_by(user_profile_id=profile.id)
        .order_by(UserProfileWeightHistory.created_at.desc())
        .first()
    )

    if last_history and last_history.height_cm and last_history.weight_kg:
        return (
            last_history.height_cm,
            last_history.weight_kg,
            profile.gender,
            profile.date_of_birth
        )

    return None, None, profile.gender, profile.date_of_birth

def calculate_bmr_from_metrics(height_cm, weight_kg, gender, date_of_birth) -> int:
    """
    Tính BMR theo công thức Mifflin-St Jeor
    """
    if not all([height_cm, weight_kg, gender, date_of_birth]):
        return 0

    today = date.today()
    age = today.year - date_of_birth.year - (
        (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
    )

    gender = gender.lower()

    if gender == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    return int(bmr)

def calculate_bmr(user_id: int) -> int:
    """
    Wrapper để tiện test
    """
    height_cm, weight_kg, gender, dob = get_latest_user_metrics(user_id)
    return calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob)

from datetime import date, datetime

def calculate_tdee(user_id: int):
    """
    Tính BMR, TDEE và target calories
    """
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None

    height_cm, weight_kg, gender, dob = get_latest_user_metrics(user_id)
    if not height_cm or not weight_kg:
        return None

    bmr = calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob)
    activity_factor = ACTIVITY_FACTOR.get(profile.activity_level, 1.2)
    tdee = int(bmr * activity_factor)
    target_calorie = tdee

    # --- Goal handling ---
    if (
        profile.aim_weight
        and profile.day_of_activities
        and profile.day_of_activities > 0
        and profile.aim_day
        and profile.aim_day_end
    ):
        CALORIES_PER_KG = 7700
        MAX_DEFICIT = -1000
        MAX_SURPLUS = 500

        # 🔒 Chuẩn hóa kiểu date
        aim_day = profile.aim_day
        aim_day_end = profile.aim_day_end

        if isinstance(aim_day, datetime):
            aim_day = aim_day.date()

        if isinstance(aim_day_end, datetime):
            aim_day_end = aim_day_end.date()

        total_days = (aim_day_end - aim_day).days

        if total_days <= 0:
            daily_calorie_change = 0
        else:
            weight_diff = profile.aim_weight - weight_kg
            total_calories_needed = weight_diff * CALORIES_PER_KG
            daily_calorie_change = total_calories_needed / total_days

        daily_calorie_change = max(
            MAX_DEFICIT,
            min(MAX_SURPLUS, daily_calorie_change)
        )

        target_calorie = int(tdee + daily_calorie_change)

    # --- Medical limits ---
    if gender:
        gender = gender.lower()
        if gender == "female":
            target_calorie = max(target_calorie, 1200)
        elif gender == "male":
            target_calorie = max(target_calorie, 1500)

    return int(bmr), int(tdee), int(target_calorie)


def create_daily_logs_for_all_users(target_date=None):
    """
    Tạo DailyEnergyLog cho mỗi user vào ngày mới
    """
    log_date = target_date or date.today()
    users = UserProfile.query.all()
    created_count = 0
    skipped_users = 0

    for user in users:
        exists = DailyEnergyLog.query.filter_by(
            user_id=user.user_id,
            log_date=log_date
        ).first()

        if exists:
            continue

        result = calculate_tdee(user.user_id)
        if not result:
            skipped_users += 1
            continue

        bmr, tdee, target_calorie = result

        daily_log = DailyEnergyLog(
            user_id=user.user_id,
            log_date=log_date,
            tdee=tdee,
            target_calorie=target_calorie,
            total_calorie_in=0,
            total_steps=0,
            steps_calorie_out=0
        )

        db.session.add(daily_log)
        created_count += 1

    db.session.commit()

    return {
        "log_date": log_date.isoformat(),
        "created_logs": created_count,
        "skipped_users": skipped_users,
        "total_users": len(users)
    }

class DailyLogService:

    @staticmethod
    def get_daily_logs(user_id: int, start_date=None, end_date=None):
        try:
            start = datetime.fromisoformat(start_date).date() if start_date else None
            end = datetime.fromisoformat(end_date).date() if end_date else None
        except ValueError:
            return None, "Invalid date format (YYYY-MM-DD)"

        query = DailyEnergyLog.query.filter_by(user_id=user_id)

        if start:
            query = query.filter(DailyEnergyLog.log_date >= start)
        if end:
            query = query.filter(DailyEnergyLog.log_date <= end)

        logs = query.order_by(DailyEnergyLog.log_date.asc()).all()

        return [
            {
                "log_date": log.log_date.isoformat(),
                "total_steps": log.total_steps or 0,
                "total_calorie_in": log.total_calorie_in or 0,
                "steps_calorie_out": log.steps_calorie_out or 0,
                "tdee": log.tdee or 0,
                "target_calorie": log.target_calorie or 0,
            }
            for log in logs
        ], None

    # @staticmethod
    # def get_summary(user_id: int, period="week"):
    #     today = date.today()
    #     if period == "week":
    #         start_date = today - timedelta(days=today.weekday())
    #     elif period == "month":
    #         start_date = today.replace(day=1)
    #     else:
    #         return None, "Invalid period"
    #
    #     summary = (
    #         db.session.query(
    #             func.sum(DailyEnergyLog.total_calorie_in),
    #             func.sum(DailyEnergyLog.base_calorie_out),
    #             func.sum(DailyEnergyLog.steps_calorie_out),
    #             func.sum(DailyEnergyLog.activity_calorie_out),
    #             func.sum(DailyEnergyLog.net_calorie)
    #         )
    #         .filter(DailyEnergyLog.user_id == user_id)
    #         .filter(DailyEnergyLog.log_date >= start_date)
    #         .first()
    #     )
    #
    #     return {
    #         "total_calorie_in": summary[0] or 0,
    #         "base_calorie_out": summary[1] or 0,
    #         "steps_calorie_out": summary[2] or 0,
    #         "activity_calorie_out": summary[3] or 0,
    #         "net_calorie": summary[4] or 0
    #     }, None

    @staticmethod
    def update_daily_steps(user_id: int, steps: int, log_date=None):
        try:
            log_date = (
                datetime.strptime(log_date, "%Y-%m-%d").date()
                if log_date else date.today()
            )

            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                return None, "User profile not found"

            user_profile_id = profile.id
            # lấy cân nặng mới nhất
            last_history = (
                UserProfileWeightHistory.query
                .filter_by(user_profile_id=user_profile_id)
                .order_by(UserProfileWeightHistory.created_at.desc())
                .first()
            )

            if not last_history or not last_history.weight_kg:
                return None, "User weight not found"

            weight_kg = last_history.weight_kg

            # công thức mới
            total_step_calorie = int(steps * 0.0005 * weight_kg)

            log = DailyEnergyLog.query.filter_by(
                user_id=user_id,
                log_date=log_date
            ).first()

            if not log:
                return None, "Daily log not found"

            log.total_steps = steps
            log.steps_calorie_out = total_step_calorie

            db.session.commit()

            return {
                "log_date": log_date.isoformat(),
                "total_steps": steps,
                "weight_kg": weight_kg,
                "step_calorie": total_step_calorie,
            }, None

        except Exception as e:
            db.session.rollback()
            return None, str(e)


