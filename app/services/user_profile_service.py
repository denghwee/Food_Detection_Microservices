from datetime import date, datetime
from flask import jsonify
from app import db
from app.models import UserProfile, DailyEnergyLog
from app.external.auth_service import fetch_user_profile
from app.models.user_profile_weight_history import UserProfileWeightHistory
from app.mappers.ai_profile_mapper import (
    ACTIVITY_TO_EXPERIENCE,
    ACTIVITY_TO_DAYS,
    ACTIVITY_TO_SESSION_DURATION,
    GOAL_MAPPING
)

from app.enums.app_enum import ActivityLevelEnum, GoalTypeEnum
class UserProfileService:

    @staticmethod
    def get_user_profile(user_email: str):
        profile = UserProfile.query.filter_by(user_email=user_email).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        # 🔹 Lấy bản ghi height/weight gần nhất
        from app.models.user_profile_weight_history import UserProfileWeightHistory
        latest_weight = (
            UserProfileWeightHistory.query
            .filter_by(user_profile_id=profile.id)
            .order_by(UserProfileWeightHistory.created_at.desc())
            .first()
        )

        height_cm = latest_weight.height_cm if latest_weight else None
        weight_kg = latest_weight.weight_kg if latest_weight else None

        return jsonify({
            "user_email": profile.user_email,
            "gender": profile.gender,
            "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "activity_level": profile.activity_level,
            "goal_type": profile.goal_type,
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }), 200

    @staticmethod
    def create_user_profile(user_email: str, payload: dict, jwt_token: str):
        # Kiểm tra profile local
        existing_profile = UserProfile.query.filter_by(user_email=user_email).first()
        if existing_profile:
            return jsonify({"error": "Profile already exists"}), 400

        # Gọi Spring Auth Service, chỉ cần JWT
        try:
            user_info = fetch_user_profile(jwt_token)
        except Exception as e:
            return jsonify({"error": str(e)}), 502

        # Tạo UserProfile chính
        profile = UserProfile(
            user_email=user_email,
            gender=user_info.get("gender"),
            date_of_birth=date.fromisoformat(user_info.get("dateOfBirth")) if user_info.get("dateOfBirth") else None,
            activity_level=payload.get("activity_level", "sedentary"),
            goal_type=payload.get("goal_type", "maintain")
        )
        db.session.add(profile)
        db.session.flush()

        # Tạo weight history nếu có
        height_cm = payload.get("height_cm")
        weight_kg = payload.get("weight_kg")
        if height_cm is not None or weight_kg is not None:
            bmi = round(weight_kg / ((height_cm / 100) ** 2), 2) if height_cm and weight_kg else None
            weight_history = UserProfileWeightHistory(
                user_profile_id=profile.id,
                height_cm=height_cm,
                weight_kg=weight_kg,
                bmi=bmi
            )
            db.session.add(weight_history)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Profile created"
        }), 201

    @staticmethod
    def update_user_profile(user_email: str, payload: dict):
        profile = UserProfile.query.filter_by(user_email=user_email).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        new_height = payload.get("height_cm")
        new_weight = payload.get("weight_kg")

        from app.models.user_profile_weight_history import UserProfileWeightHistory

        # Lấy bản ghi gần nhất
        latest_history = (
            UserProfileWeightHistory.query
            .filter_by(user_profile_id=profile.id)
            .order_by(UserProfileWeightHistory.created_at.desc())
            .first()
        )

        # Giá trị hiện tại lấy từ lịch sử gần nhất, nếu không có lấy từ profile cũ
        current_height = latest_history.height_cm if latest_history else getattr(profile, "height_cm", None)
        current_weight = latest_history.weight_kg if latest_history else getattr(profile, "weight_kg", None)

        # Chỉ tạo history mới khi có sự thay đổi thực sự
        if (new_height is not None and new_height != current_height) or \
                (new_weight is not None and new_weight != current_weight):

            height_cm = new_height if new_height is not None else current_height
            weight_kg = new_weight if new_weight is not None else current_weight

            bmi = None
            if height_cm and weight_kg:
                height_m = height_cm / 100
                bmi = round(weight_kg / (height_m ** 2), 2)

            history = UserProfileWeightHistory(
                user_profile_id=profile.id,
                height_cm=height_cm,
                weight_kg=weight_kg,
                bmi=bmi
            )
            db.session.add(history)

            # Đồng bộ profile tạm thời
            profile.height_cm = height_cm
            profile.weight_kg = weight_kg

        # Cập nhật các trường còn lại
        profile.gender = payload.get("gender", profile.gender)
        if payload.get("date_of_birth"):
            profile.date_of_birth = date.fromisoformat(payload.get("date_of_birth"))
        profile.activity_level = payload.get("activity_level", profile.activity_level)
        profile.goal_type = payload.get("goal_type", profile.goal_type)
        profile.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({"status": "success", "message": "Profile updated"}), 200

    @staticmethod
    def get_weight_history(user_email: str):
        profile = UserProfile.query.filter_by(user_email=user_email).first()
        if not profile:
            return jsonify({"error": "Profile not found"}), 404

        histories = UserProfileWeightHistory.query.filter_by(user_profile_id=profile.id) \
            .order_by(UserProfileWeightHistory.created_at.desc()).all()

        def bmi_comment(bmi: float):
            if bmi is None:
                return "No data"
            if bmi < 18.5:
                return "Underweight"
            elif 18.5 <= bmi < 24.9:
                return "Normal weight"
            elif 25 <= bmi < 29.9:
                return "Overweight"
            else:
                return "Obese"

        data = [
            {
                "height_cm": h.height_cm,
                "weight_kg": h.weight_kg,
                "bmi": h.bmi,
                "comment": bmi_comment(h.bmi),
                "recorded_at": h.created_at.isoformat()
            }
            for h in histories
        ]

        return jsonify({
            "user_email": profile.user_email,
            "weight_history": data
        }), 200

    @staticmethod
    def build_ai_input(user_email: str):
        # 1️⃣ User profile
        profile = UserProfile.query.filter_by(user_email=user_email).first()
        if not profile:
            return None, "User profile not found"

        if not profile.date_of_birth:
            return None, "Date of birth not set"

        # Age
        today = date.today()
        age = today.year - profile.date_of_birth.year - (
                (today.month, today.day) <
                (profile.date_of_birth.month, profile.date_of_birth.day)
        )

        # 2️⃣ Latest weight & height
        wh = (
            UserProfileWeightHistory.query
            .filter_by(user_profile_id=profile.id)
            .order_by(UserProfileWeightHistory.created_at.desc())
            .first()
        )

        if not wh:
            return None, "Weight/height history not found"

        # 3️⃣ Latest calorie target
        log = (
            DailyEnergyLog.query
            .filter_by(user_email=user_email)
            .order_by(DailyEnergyLog.log_date.desc())
            .first()
        )

        calorie_target = log.target_calorie if log else 0

        # 4️⃣ Mapping
        experience_level = ACTIVITY_TO_EXPERIENCE.get(
            profile.activity_level, "beginner"
        )

        goal = GOAL_MAPPING.get(
            profile.goal_type, "maintenance"
        )

        available_days = ACTIVITY_TO_DAYS.get(
            profile.activity_level, 4
        )

        session_duration = ACTIVITY_TO_SESSION_DURATION.get(
            profile.activity_level, 60
        )

        # 5️⃣ Final payload
        return {
            "age": age,
            "gender": profile.gender,
            "height_cm": int(wh.height_cm),
            "weight_kg": float(wh.weight_kg),
            "experience_level": experience_level,
            "goal": goal,
            "available_days_per_week": available_days,
            "session_duration_minutes": session_duration,
            "injuries": [],
            "calorie_target": calorie_target
        }, None

