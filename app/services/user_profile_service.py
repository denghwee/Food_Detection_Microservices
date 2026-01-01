from datetime import date, datetime
from flask import jsonify
from app.extensions import db

from app.models import UserProfile, DailyEnergyLog
from app.models.user_profile_weight_history import UserProfileWeightHistory
from app.external.auth_service import fetch_user_profile

from app.mappers.ai_profile_mapper import (
    ACTIVITY_TO_EXPERIENCE,
    ACTIVITY_TO_DAYS,
    ACTIVITY_TO_SESSION_DURATION,
    GOAL_MAPPING
)
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

        # Lấy thông tin từ Auth Service
        try:
            user_info = fetch_user_profile(jwt_token)
        except Exception as e:
            return jsonify({"error": str(e)}), 502

        # ---- Tạo UserProfile ----
        profile = UserProfile(
            user_id=user_id,
            gender=user_info.get("gender"),
            date_of_birth=(
                date.fromisoformat(user_info["dateOfBirth"])
                if user_info.get("dateOfBirth") else None
            ),
            activity_level=payload["activity_level"],  # REQUIRED
            aim_weight=payload["aim_weight"],  # REQUIRED
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

        # ---- Weight history (chiều cao / cân nặng) ----
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

        db.session.commit()


        return jsonify(
            build_user_profile_response(profile)
        ), 201
    # =========================
    # UPDATE PROFILE
    # =========================
    @staticmethod
    def update_user_profile(user_id: int, payload: dict):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404


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

        height_changed = (
                new_height is not None and new_height != current_height
        )
        weight_changed = (
                new_weight is not None and new_weight != current_weight
        )


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
            profile.aim_day = (
                date.fromisoformat(payload["aim_day_end"])
                if payload["aim_day_end"] else None
            )

        if "day_of_activities" in payload:
            profile.day_of_activities = payload["day_of_activities"]

        if "date_of_birth" in payload:
            profile.date_of_birth = date.fromisoformat(payload["date_of_birth"])

        profile.updated_at = datetime.utcnow()
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

    # =========================
    # AI INPUT
    # =========================
    @staticmethod
    def build_ai_input(user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return None, "User profile not found"

        if not profile.date_of_birth:
            return None, "Date of birth not set"

        today = date.today()
        age = today.year - profile.date_of_birth.year - (
            (today.month, today.day) <
            (profile.date_of_birth.month, profile.date_of_birth.day)
        )

        wh = (
            UserProfileWeightHistory.query
            .filter_by(user_profile_id=profile.id)
            .order_by(UserProfileWeightHistory.created_at.desc())
            .first()
        )

        if not wh:
            return None, "Weight/height history not found"

        log = (
            DailyEnergyLog.query
            .filter_by(user_id=user_id)
            .order_by(DailyEnergyLog.log_date.desc())
            .first()
        )

        calorie_target = log.target_calorie if log else 0

        return {
            "age": age,
            "gender": profile.gender,
            "height_cm": int(wh.height_cm),
            "weight_kg": float(wh.weight_kg),
            "experience_level": ACTIVITY_TO_EXPERIENCE.get(profile.activity_level, "beginner"),
            "goal": GOAL_MAPPING.get(profile.goal_type, "maintenance"),
            "available_days_per_week": ACTIVITY_TO_DAYS.get(profile.activity_level, 4),
            "session_duration_minutes": ACTIVITY_TO_SESSION_DURATION.get(profile.activity_level, 60),
            "injuries": [],
            "calorie_target": calorie_target
        }, None
