# app/services/calorie_service.py
from datetime import date
from flask import jsonify
from app import db
from app.models.daily_energy_log import DailyEnergyLog
from app.models.food_record import FoodRecord
from app.utils import calculate_tdee

class CalorieService:

    @staticmethod
    def add_food_records(user_email: str, payload: dict):
        log_date = date.fromisoformat(payload.get("log_date")) if payload.get("log_date") else date.today()
        foods = payload.get("foods", [])
        if not foods:
            return jsonify({"error": "No food provided"}), 400

        daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()
        if not daily_log:
            daily_log = DailyEnergyLog(user_email=user_email, log_date=log_date)
            db.session.add(daily_log)
            db.session.flush()

        total_calorie = 0
        records = []
        for food in foods:
            calorie = int(food["calorie"])
            quantity = food.get("quantity", 1)
            record = FoodRecord(
                daily_log_id=daily_log.id,
                food_name=food["food_name"],
                calorie=calorie,
                quantity=quantity,
                input_method=food.get("input_method", "manual")
            )
            total_calorie += calorie * quantity
            records.append(record)

        db.session.add_all(records)

        # --- Cập nhật BMR / TDEE / target_calorie ---
        bmr, tdee, target_calorie = calculate_tdee(user_email)
        daily_log.base_calorie_out = bmr
        daily_log.tdee = tdee
        daily_log.target_calorie = target_calorie

        daily_log.total_calorie_in += total_calorie
        daily_log.net_calorie = daily_log.total_calorie_in - daily_log.target_calorie - daily_log.activity_calorie_out

        db.session.commit()

        return jsonify({
            "status": "success",
            "action": "add",
            "log_date": str(log_date),
            "items_added": len(records),
            "total_calorie_added": total_calorie,
            "base_calorie_out": bmr,
            "tdee": tdee,
            "target_calorie": target_calorie,
            "net_calorie": daily_log.net_calorie
        }), 201

    @staticmethod
    def update_food_records(user_email: str, payload: dict):
        log_date = date.fromisoformat(payload.get("log_date")) if payload.get("log_date") else date.today()
        foods = payload.get("foods", [])
        if foods is None:
            return jsonify({"error": "Invalid foods list"}), 400

        daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()
        if not daily_log:
            return jsonify({"error": "Daily log not found"}), 404

        # Xóa foods cũ
        FoodRecord.query.filter_by(daily_log_id=daily_log.id).delete()
        daily_log.total_calorie_in = 0

        total_calorie = 0
        records = []
        for food in foods:
            calorie = int(food["calorie"])
            quantity = food.get("quantity", 1)
            record = FoodRecord(
                daily_log_id=daily_log.id,
                food_name=food["food_name"],
                calorie=calorie,
                quantity=quantity,
                input_method=food.get("input_method", "manual")
            )
            total_calorie += calorie * quantity
            records.append(record)

        db.session.add_all(records)

        bmr, tdee, target_calorie = calculate_tdee(user_email)
        daily_log.base_calorie_out = bmr
        daily_log.tdee = tdee
        daily_log.target_calorie = target_calorie

        daily_log.total_calorie_in = total_calorie
        daily_log.net_calorie = daily_log.total_calorie_in - daily_log.target_calorie - daily_log.activity_calorie_out

        db.session.commit()

        return jsonify({
            "status": "success",
            "action": "update",
            "log_date": str(log_date),
            "items_saved": len(records),
            "total_calorie": total_calorie,
            "base_calorie_out": bmr,
            "tdee": tdee,
            "target_calorie": target_calorie,
            "net_calorie": daily_log.net_calorie
        }), 200

    @staticmethod
    def get_food_records(user_email: str, log_date: str | None):
        log_date = date.fromisoformat(log_date) if log_date else date.today()
        daily_log = DailyEnergyLog.query.filter_by(user_email=user_email, log_date=log_date).first()

        if not daily_log:
            return jsonify({
                "status": "success",
                "log_date": str(log_date),
                "summary": {"total_calorie_in": 0, "base_calorie_out": 0, "tdee":0, "target_calorie":0, "activity_calorie_out": 0, "net_calorie": 0},
                "foods": []
            }), 200

        foods = FoodRecord.query.filter_by(daily_log_id=daily_log.id).all()

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
            "foods": [
                {
                    "id": f.id,
                    "food_name": f.food_name,
                    "calorie": f.calorie,
                    "quantity": f.quantity,
                    "input_method": f.input_method,
                    "created_at": f.created_at.isoformat()
                } for f in foods
            ]
        }), 200
