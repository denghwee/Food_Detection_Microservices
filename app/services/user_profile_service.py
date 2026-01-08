from datetime import date, datetime
from flask import jsonify
from app.extensions import db
from app.mappers.ai_profile_mapper import ACTIVITY_TO_EXPERIENCE, ACTIVITY_TO_SESSION_DURATION, GOAL_MAPPING

from app.models import UserProfile, DailyEnergyLog
from app.models.user_profile_weight_history import UserProfileWeightHistory
from app.external.auth_service import fetch_user_profile
from app.services.daily_log_service import calculate_tdee

def _get_profile_and_latest_weight(user_id: int):
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return None, None, "User profile not found"

    if not profile.date_of_birth:
        return None, None, "Date of birth not set"

    wh = (
        UserProfileWeightHistory.query
        .filter_by(user_profile_id=profile.id)
        .order_by(UserProfileWeightHistory.created_at.desc())
        .first()
    )

    if not wh:
        return None, None, "Weight/height history not found"

    return profile, wh, None

def upsert_today_daily_log(user_id: int):
    """
    Tạo hoặc cập nhật DailyEnergyLog của hôm nay cho user
    """
    log_date = date.today()

    result = calculate_tdee(user_id)
    if not result:
        return False

    bmr, tdee, target_calorie = result

    daily_log = DailyEnergyLog.query.filter_by(
        user_id=user_id,
        log_date=log_date
    ).first()

    if daily_log:
        # UPDATE
        daily_log.tdee = tdee
        daily_log.target_calorie = target_calorie
        daily_log.updated_at = datetime.utcnow()
    else:
        # CREATE
        daily_log = DailyEnergyLog(
            user_id=user_id,
            log_date=log_date,
            tdee=tdee,
            target_calorie=target_calorie,
            total_calorie_in=0,
            total_steps=0,
            steps_calorie_out=0
        )
        db.session.add(daily_log)

    return True

def build_user_profile_response(profile: UserProfile):
    latest_weight = (
        UserProfileWeightHistory.query
        .filter_by(user_profile_id=profile.id)
        .order_by(UserProfileWeightHistory.created_at.desc())
        .first()
    )

    return {
        "user_id": profile.user_id,
        "gender": profile.gender,
        "date_of_birth": (
            profile.date_of_birth.isoformat()
            if profile.date_of_birth else None
        ),
        "activity_level": profile.activity_level.value
        if profile.activity_level else None,

        "aim_weight": profile.aim_weight,
        "aim_day": (
            profile.aim_day.isoformat()
            if profile.aim_day else None
        ),
        "aim_day_end": (
            profile.aim_day_end.isoformat()
            if profile.aim_day_end else None
        ),
        "day_of_activities": profile.day_of_activities,

        "height_cm": latest_weight.height_cm if latest_weight else None,
        "weight_kg": latest_weight.weight_kg if latest_weight else None,
        "bmi": latest_weight.bmi if latest_weight else None,

        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat()
    }


class UserProfileService:

    # =========================
    # GET PROFILE
    # =========================
    @staticmethod
    def get_user_profile(user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        return jsonify(
            build_user_profile_response(profile)
        ), 200

    # =========================
    # CREATE PROFILE
    # =========================
    @staticmethod
    def create_user_profile(user_id: int, payload: dict, jwt_token: str):
        existing = UserProfile.query.filter_by(user_id=user_id).first()
        if existing:
            return jsonify({"error": "Profile already exists"}), 400

        # ---- Lấy thông tin từ Auth Service ----
        try:
            user_info = fetch_user_profile(jwt_token)
        except Exception as e:
            print("AUTH SERVICE ERROR:", e)
            return jsonify({"error": str(e)}), 502

        # ---- Tạo UserProfile ----
        profile = UserProfile(
            user_id=user_id,
            gender=user_info.get("gender"),
            date_of_birth=(
                date.fromisoformat(user_info["dateOfBirth"])
                if user_info.get("dateOfBirth") else None
            ),
            activity_level=payload["activity_level"],
            aim_weight=payload["aim_weight"],
            aim_day=(
                date.fromisoformat(payload["aim_day"])
                if payload.get("aim_day") else None
            ),
            aim_day_end=(
                date.fromisoformat(payload["aim_day_end"])
                if payload.get("aim_day_end") else None
            ),
            day_of_activities=payload.get("day_of_activities")
        )

        db.session.add(profile)
        db.session.flush()  # lấy profile.id

        # ---- Weight history ----
        height_cm = payload.get("height_cm")
        weight_kg = payload.get("weight_kg")

        if height_cm is not None or weight_kg is not None:
            bmi = (
                round(weight_kg / ((height_cm / 100) ** 2), 2)
                if height_cm and weight_kg else None
            )

            db.session.add(
                UserProfileWeightHistory(
                    user_profile_id=profile.id,
                    height_cm=height_cm,
                    weight_kg=weight_kg,
                    bmi=bmi
                )
            )

        # ---- Daily log hôm nay ----
        upsert_today_daily_log(user_id)

        db.session.commit()

        return jsonify(
            build_user_profile_response(profile)
        ), 201

    # =========================
    # UPDATE PROFILE
    # =========================
    @staticmethod
    def update_user_profile(user_id: int, payload: dict, jwt_token: str):
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        # =========================
        # Nếu CHƯA CÓ profile → tạo mới
        # =========================
        if not profile:
            return UserProfileService.create_user_profile(
                user_id=user_id,
                payload=payload,
                jwt_token=jwt_token
            )

        # ---- Lấy weight history mới nhất ----
        latest = (
            UserProfileWeightHistory.query
            .filter_by(user_profile_id=profile.id)
            .order_by(UserProfileWeightHistory.created_at.desc())
            .first()
        )

        current_height = latest.height_cm if latest else None
        current_weight = latest.weight_kg if latest else None

        new_height = payload.get("height_cm")
        new_weight = payload.get("weight_kg")

        height_changed = new_height is not None and new_height != current_height
        weight_changed = new_weight is not None and new_weight != current_weight

        # ---- Thêm weight history nếu có thay đổi ----
        if height_changed or weight_changed:
            height_cm = new_height if height_changed else current_height
            weight_kg = new_weight if weight_changed else current_weight

            bmi = None
            if height_cm is not None and weight_kg is not None:
                bmi = round(weight_kg / ((height_cm / 100) ** 2), 2)

            db.session.add(
                UserProfileWeightHistory(
                    user_profile_id=profile.id,
                    height_cm=height_cm,
                    weight_kg=weight_kg,
                    bmi=bmi
                )
            )

        # ---- Update profile fields ----
        if "gender" in payload:
            profile.gender = payload["gender"]

        if "activity_level" in payload:
            profile.activity_level = payload["activity_level"]

        if "aim_weight" in payload:
            profile.aim_weight = payload["aim_weight"]

        if "aim_day" in payload:
            profile.aim_day = (
                date.fromisoformat(payload["aim_day"])
                if payload["aim_day"] else None
            )

        if "aim_day_end" in payload:
            profile.aim_day_end = (
                date.fromisoformat(payload["aim_day_end"])
                if payload["aim_day_end"] else None
            )

        if "day_of_activities" in payload:
            profile.day_of_activities = payload["day_of_activities"]

        if "date_of_birth" in payload:
            profile.date_of_birth = date.fromisoformat(payload["date_of_birth"])

        profile.updated_at = datetime.utcnow()

        # ---- Daily log hôm nay ----
        upsert_today_daily_log(user_id)

        db.session.commit()

        return jsonify(
            build_user_profile_response(profile)
        ), 200

    # =========================
    # WEIGHT HISTORY
    # =========================
    @staticmethod
    def get_weight_history(user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        histories = (
            UserProfileWeightHistory.query
            .filter_by(user_profile_id=profile.id)
            .order_by(UserProfileWeightHistory.created_at.desc())
            .all()
        )

        def bmi_comment(bmi):
            if bmi is None:
                return "No data"
            if bmi < 18.5:
                return "Underweight"
            if bmi < 25:
                return "Normal"
            if bmi < 30:
                return "Overweight"
            return "Obese"

        return jsonify({
            "user_id": profile.user_id,
            "weight_history": [
                {
                    "height_cm": h.height_cm,
                    "weight_kg": h.weight_kg,
                    "bmi": h.bmi,
                    "comment": bmi_comment(h.bmi),
                    "recorded_at": h.created_at.isoformat()
                }
                for h in histories
            ]
        }), 200

    @staticmethod
    def build_ai_profile_input(user_id: int):
        profile, wh, error = _get_profile_and_latest_weight(user_id)
        if error:
            return None, error

        today = date.today()
        age = today.year - profile.date_of_birth.year - (
                (today.month, today.day) <
                (profile.date_of_birth.month, profile.date_of_birth.day)
        )

        return {
            "age": age,
            "gender": profile.gender,
            "height_cm": int(wh.height_cm),
            "weight_kg": float(wh.weight_kg),
            "experience_level": ACTIVITY_TO_EXPERIENCE.get(
                profile.activity_level, "beginner"
            ),
            "available_days_per_week": profile.day_of_activities
        }, None

    @staticmethod
    def build_ai_goal_input(user_id: int):
        profile, wh, error = _get_profile_and_latest_weight(user_id)
        if error:
            return None, error

        log = (
            DailyEnergyLog.query
            .filter_by(user_id=user_id)
            .order_by(DailyEnergyLog.log_date.desc())
            .first()
        )

        if profile.aim_weight - wh.weight_kg > 0:
            goal = "gain weight"
        elif profile.aim_weight - wh.weight_kg == 0:
            goal = "maintenance"
        else:
            goal = "lose weight"

        return {
            "gender": profile.gender,
            "weight_kg": float(wh.weight_kg),
            "goal": goal,
            "calorie_target": log.target_calorie if log else 0
        }, None
