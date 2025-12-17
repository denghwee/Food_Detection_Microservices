# app/services/daily_log_service.py
from datetime import date, timedelta

from sqlalchemy import func

from app import db
from app.models.daily_energy_log import DailyEnergyLog
from app.models.user_profile import UserProfile
from app.models.user_profile_weight_history import UserProfileWeightHistory
from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum

def get_latest_user_metrics(user_email: str):
    """
    Lấy thông tin chiều cao, cân nặng gần nhất của user
    từ bảng UserProfileWeightHistory để tính BMR/TDEE
    """
    profile = UserProfile.query.filter_by(user_email=user_email).first()
    if not profile:
        return None, None, None, None, None, None  # height_cm, weight_kg, gender, dob, activity_level, goal_type

    last_history = (
        UserProfileWeightHistory.query
        .filter_by(user_profile_id=profile.id)
        .order_by(UserProfileWeightHistory.created_at.desc())
        .first()
    )

    height_cm = last_history.height_cm if last_history else profile.height_cm
    weight_kg = last_history.weight_kg if last_history else None
    gender = profile.gender
    dob = profile.date_of_birth
    activity_level = profile.activity_level
    goal_type = profile.goal_type

    return height_cm, weight_kg, gender, dob, activity_level, goal_type

def calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob):
    """
    Tính BMR theo công thức Mifflin-St Jeor
    """
    if not all([height_cm, weight_kg, gender, dob]):
        return 0

    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    return int(bmr)

def calculate_tdee(bmr: int, activity_level: ActivityLevelEnum):
    """
    TDEE = BMR * activity factor
    """
    factor_map = {
        ActivityLevelEnum.sedentary: 1.2,
        ActivityLevelEnum.lightly_active: 1.375,
        ActivityLevelEnum.moderately_active: 1.55,
        ActivityLevelEnum.very_active: 1.725
    }
    factor = factor_map.get(activity_level, 1.2)
    return int(bmr * factor)

def calculate_target_calorie(tdee: int, goal_type: GoalTypeEnum):
    """
    Điều chỉnh calories theo mục tiêu của user
    """
    if goal_type == GoalTypeEnum.lose_weight:
        return int(tdee - 500)  # deficit 500 kcal/day
    elif goal_type == GoalTypeEnum.gain_weight:
        return int(tdee + 500)  # surplus 500 kcal/day
    else:
        return tdee  # duy trì

def create_daily_logs_for_all_users():
    """
    Tạo DailyEnergyLog chuẩn y khoa cho mỗi user vào ngày mới
    """
    today = date.today()
    users = UserProfile.query.all()
    created_count = 0

    for user in users:
        # Nếu đã có log hôm nay thì bỏ qua
        if DailyEnergyLog.query.filter_by(user_email=user.user_email, log_date=today).first():
            continue

        # Lấy metrics gần nhất
        height_cm, weight_kg, gender, dob, activity_level, goal_type = get_latest_user_metrics(user.user_email)
        bmr = calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob)
        tdee = calculate_tdee(bmr, activity_level)
        target_calorie = calculate_target_calorie(tdee, goal_type)

        # Tạo log mới
        daily_log = DailyEnergyLog(
            user_email=user.user_email,
            log_date=today,
            base_calorie_out=bmr,
            tdee=tdee,
            target_calorie=target_calorie,
            total_calorie_in=0,
            activity_calorie_out=0,
            net_calorie=-bmr  # chưa có food/activity
        )

        db.session.add(daily_log)
        created_count += 1

    db.session.commit()
    print(f"[DailyLogService] Created {created_count} DailyEnergyLog(s) for {today}")


def update_daily_log_for_user(user_email: str, log_date: date | None = None):
    """
    Cập nhật DailyEnergyLog hiện tại của user:
    - Tính lại BMR, TDEE, target_calorie
    - Giữ nguyên total_calorie_in, activity_calorie_out
    - Cập nhật net_calorie
    """
    log_date = log_date or date.today()

    daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()
    if not daily_log:
        print(f"[DailyLogService] No DailyEnergyLog found for {user_email} on {log_date}")
        return None

    # Lấy thông tin user
    height_cm, weight_kg, gender, dob, activity_level, goal_type = get_latest_user_metrics(user_email)
    bmr = calculate_bmr_from_metrics(height_cm, weight_kg, gender, dob)
    tdee = calculate_tdee(bmr, activity_level)
    target_calorie = calculate_target_calorie(tdee, goal_type)

    # Cập nhật log
    daily_log.base_calorie_out = bmr
    daily_log.tdee = tdee
    daily_log.target_calorie = target_calorie
    daily_log.net_calorie = (
            daily_log.total_calorie_in
            - daily_log.base_calorie_out
            - daily_log.activity_calorie_out
    )

    db.session.commit()
    print(f"[DailyLogService] Updated DailyEnergyLog for {user_email} on {log_date}")
    return daily_log


class DailyLogService:

    @staticmethod
    def get_daily_logs(user_email: str, start_date: str | None = None, end_date: str | None = None):
        from datetime import datetime

        try:
            start = datetime.fromisoformat(start_date).date() if start_date else None
            end = datetime.fromisoformat(end_date).date() if end_date else None
        except ValueError:
            return None, "Invalid date format"

        query = DailyEnergyLog.query.filter_by(user_email=user_email)
        if start:
            query = query.filter(DailyEnergyLog.log_date >= start)
        if end:
            query = query.filter(DailyEnergyLog.log_date <= end)

        logs = query.order_by(DailyEnergyLog.log_date.asc()).all()

        result = [
            {
                "log_date": log.log_date.isoformat(),
                "total_calorie_in": log.total_calorie_in,
                "base_calorie_out": log.base_calorie_out,
                "tdee": log.tdee,
                "target_calorie": log.target_calorie,
                "activity_calorie_out": log.activity_calorie_out,
                "net_calorie": log.net_calorie
            }
            for log in logs
        ]
        return result, None

    @staticmethod
    def get_summary(user_email: str, period: str = "week"):
        today = date.today()
        if period == "week":
            start_date = today - timedelta(days=today.weekday())
        elif period == "month":
            start_date = today.replace(day=1)
        else:
            return None, "Invalid period, use 'week' or 'month'"

        summary = (
            db.session.query(
                func.sum(DailyEnergyLog.total_calorie_in).label("total_in"),
                func.sum(DailyEnergyLog.base_calorie_out).label("total_bmr"),
                func.sum(DailyEnergyLog.tdee).label("total_tdee"),
                func.sum(DailyEnergyLog.target_calorie).label("total_target"),
                func.sum(DailyEnergyLog.activity_calorie_out).label("total_activity"),
                func.sum(DailyEnergyLog.net_calorie).label("total_net")
            )
            .filter(DailyEnergyLog.user_email == user_email)
            .filter(DailyEnergyLog.log_date >= start_date)
            .first()
        )

        return {
            "total_calorie_in": summary.total_in or 0,
            "base_calorie_out": summary.total_bmr or 0,
            "tdee": summary.total_tdee or 0,
            "target_calorie": summary.total_target or 0,
            "activity_calorie_out": summary.total_activity or 0,
            "net_calorie": summary.total_net or 0
        }, None
