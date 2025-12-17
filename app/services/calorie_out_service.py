# app/services/calorie_out_service.py
from datetime import date
from flask import jsonify
from app import db
from app.models.daily_energy_log import DailyEnergyLog
from app.models.activity import Activity
from app.utils import calculate_tdee

class CalorieOutService:

    @staticmethod
    def add_activities(user_email: str, payload: dict):
        log_date = date.fromisoformat(payload.get("log_date")) if payload.get("log_date") else date.today()
        activities_data = payload.get("activities", [])
        if not activities_data:
            return jsonify({"error": "No activities provided"}), 400

        daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()
        if not daily_log:
            daily_log = DailyEnergyLog(user_email=user_email, log_date=log_date)
            db.session.add(daily_log)
            db.session.flush()

        total_burned = 0
        records = []
        for act in activities_data:
            calorie_burned = int(act["calorie_burned"])
            record = Activity(
                daily_log_id=daily_log.id,
                activity_type=act["activity_type"],
                duration_minutes=act.get("duration_minutes"),
                calorie_burned=calorie_burned
            )
            total_burned += calorie_burned
            records.append(record)

        db.session.add_all(records)

        bmr, tdee, target_calorie = calculate_tdee(user_email)
        daily_log.base_calorie_out = bmr
        daily_log.tdee = tdee
        daily_log.target_calorie = target_calorie

        daily_log.activity_calorie_out += total_burned
        daily_log.net_calorie = daily_log.total_calorie_in - daily_log.target_calorie - daily_log.activity_calorie_out

        db.session.commit()

        return jsonify({
            "status": "success",
            "action": "add",
            "log_date": str(log_date),
            "items_added": len(records),
            "total_calorie_burned": total_burned,
            "base_calorie_out": bmr,
            "tdee": tdee,
            "target_calorie": target_calorie,
            "net_calorie": daily_log.net_calorie
        }), 201

    @staticmethod
    def update_activities(user_email: str, payload: dict):
        log_date = date.fromisoformat(payload.get("log_date")) if payload.get("log_date") else date.today()
        activities_data = payload.get("activities", [])
        if activities_data is None:
            return jsonify({"error": "Invalid activities list"}), 400

        daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()
        if not daily_log:
            return jsonify({"error": "Daily log not found"}), 404

        # Xóa activities cũ
        Activity.query.filter_by(daily_log_id=daily_log.id).delete()
        daily_log.activity_calorie_out = 0

        total_burned = 0
        records = []
        for act in activities_data:
            calorie_burned = int(act["calorie_burned"])
            record = Activity(
                daily_log_id=daily_log.id,
                activity_type=act["activity_type"],
                duration_minutes=act.get("duration_minutes"),
                calorie_burned=calorie_burned
            )
            total_burned += calorie_burned
            records.append(record)

        db.session.add_all(records)

        bmr, tdee, target_calorie = calculate_tdee(user_email)
        daily_log.base_calorie_out = bmr
        daily_log.tdee = tdee
        daily_log.target_calorie = target_calorie

        daily_log.activity_calorie_out = total_burned
        daily_log.net_calorie = daily_log.total_calorie_in - daily_log.target_calorie - daily_log.activity_calorie_out

        db.session.commit()

        return jsonify({
            "status": "success",
            "action": "update",
            "log_date": str(log_date),
            "items_saved": len(records),
            "total_calorie_burned": total_burned,
            "base_calorie_out": bmr,
            "tdee": tdee,
            "target_calorie": target_calorie,
            "net_calorie": daily_log.net_calorie
        }), 200

    @staticmethod
    def get_activities(user_email: str, log_date: str | None):
        log_date = date.fromisoformat(log_date) if log_date else date.today()
        daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()

        if not daily_log:
            return jsonify({
                "status": "success",
                "log_date": str(log_date),
                "summary": {"total_calorie_in": 0, "base_calorie_out": 0, "tdee":0, "target_calorie":0, "activity_calorie_out": 0, "net_calorie": 0},
                "activities": []
            }), 200

        activities = Activity.query.filter_by(daily_log_id=daily_log.id).all()

        return jsonify({
            "status": "success",
            "log_date": str(log_date),
            "summary": {
                "total_calorie_in": daily_log.total_calorie_in,
                "base_calorie_out": daily_log.base_calorie_out,
                "tdee": daily_log.tdee,
                "target_calorie": daily_log.target_calorie,
                "activity_calorie_out": daily_log.activity_calorie_out,
                "net_calorie": daily_log.net_calorie
            },
            "activities": [
                {
                    "id": a.id,
                    "activity_type": a.activity_type,
                    "duration_minutes": a.duration_minutes,
                    "calorie_burned": a.calorie_burned,
                    "created_at": a.created_at.isoformat()
                } for a in activities
            ]
        }), 200
