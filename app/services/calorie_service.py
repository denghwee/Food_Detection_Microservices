from datetime import date
from flask import jsonify
from sqlalchemy import func

from app.extensions import db
from app.models.daily_energy_log import DailyEnergyLog
from app.models.food_record import FoodRecord
from app.services.daily_log_service import (
    get_latest_user_metrics,
    calculate_bmr_from_metrics,
    calculate_tdee,
)


class CalorieService:

    # =========================
    # ADD FOOD
    # =========================
    @staticmethod
    def add_food_records(user_id: int, payload: dict):
        log_date = (
            date.fromisoformat(payload.get("log_date"))
            if payload.get("log_date") else date.today()
        )

        foods = payload.get("foods", [])
        if not foods:
            return jsonify({"error": "No food provided"}), 400

        daily_log = DailyEnergyLog.query.filter_by(
            user_id=user_id,
            log_date=log_date
        ).first()

        if not daily_log:
            daily_log = DailyEnergyLog(
                user_id=user_id,
                log_date=log_date,
                total_calorie_in=0,
                steps_calorie_out=0
            )
            db.session.add(daily_log)
            db.session.flush()

        total_calorie_added = 0
        records = []

        for food in foods:
            calorie = int(food["calorie"])
            quantity = food.get("quantity", 1)

            records.append(FoodRecord(
                daily_log_id=daily_log.id,
                food_name=food["food_name"],
                calorie=calorie,
                quantity=quantity,
                input_method=food.get("input_method", "manual")
            ))

            total_calorie_added += calorie * quantity

        db.session.add_all(records)

        daily_log.total_calorie_in += total_calorie_added


        db.session.commit()

        return jsonify({
            "status": "success",
            "action": "add",
            "log_date": log_date.isoformat(),
            "items_added": len(records),
            "total_calorie_added": total_calorie_added,
            "total_calorie_in_by_day": daily_log.total_calorie_in
        }), 201

    @staticmethod
    def update_food_record(user_id: int, payload: dict):
        try:
            record_id = payload.get("id")
            if not record_id:
                return {"error": "Food record id is required"}, 400

            # 1. Lấy food record theo ID
            record = FoodRecord.query.filter_by(id=record_id).first()
            if not record:
                return {"error": "Food record not found"}, 404

            # 2. Kiểm tra ownership (rất quan trọng)
            daily_log = DailyEnergyLog.query.filter_by(
                id=record.daily_log_id,
                user_id=user_id
            ).first()

            if not daily_log:
                return {"error": "Unauthorized"}, 403

            # 3. Update CHỈ record này
            if "food_name" in payload:
                record.food_name = payload["food_name"]

            if "quantity" in payload:
                record.quantity = payload["quantity"]

            if "calorie" in payload:
                record.calorie = payload["calorie"]
            # 4. Tính lại tổng calo ăn vào
            total_calorie = (
                    db.session.query(func.sum(FoodRecord.calorie))
                    .filter_by(daily_log_id=daily_log.id)
                    .scalar()
                    or 0
            )

            daily_log.total_calorie_in = total_calorie
            db.session.commit()

            return {
                "id": record.id,
                "food_name": record.food_name,
                "quantity": record.quantity,
                "calorie": record.calorie,
                "updated_at": record.updated_at.isoformat()
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    # =========================
    # GET FOOD
    # =========================
    @staticmethod
    def get_food_records(user_id: int, log_date: str | None):
        log_date = date.fromisoformat(log_date) if log_date else date.today()

        daily_log = DailyEnergyLog.query.filter_by(
            user_id=user_id,
            log_date=log_date
        ).first()

        if not daily_log:
            return jsonify({
                "status": "success",
                "log_date": log_date.isoformat(),
                "summary": {
                    "total_calorie_in": 0,
                    "target_calorie": 0,
                },
                "foods": []
            }), 200

        foods = FoodRecord.query.filter_by(
            daily_log_id=daily_log.id
        ).all()

        return jsonify({
            "status": "success",
            "log_date": log_date.isoformat(),
            "summary": {
                "total_calorie_in": daily_log.total_calorie_in,
                "target_calorie": daily_log.target_calorie,
            },
            "foods": [
                {
                    "id": f.id,
                    "food_name": f.food_name,
                    "calorie": f.calorie,
                    "quantity": f.quantity,
                    "input_method": f.input_method,
                    "created_at": f.created_at.isoformat()
                }
                for f in foods
            ]
        }), 200
    @staticmethod
    def delete_food_record(user_id: int, record_id: int):
        try:
            # 1. Lấy food record
            record = FoodRecord.query.filter_by(id=record_id).first()
            if not record:
                return {"error": "Food record not found"}, 404

            # 2. Lấy daily log + check ownership
            daily_log = DailyEnergyLog.query.filter_by(
                id=record.daily_log_id,
                user_id=user_id
            ).first()

            if not daily_log:
                return {"error": "Unauthorized"}, 403

            # 3. Xoá record
            db.session.delete(record)
            db.session.flush()  # để record bị xoá khỏi session

            # 4. Tính lại tổng calo ăn vào
            total_calorie = (
                db.session.query(func.sum(FoodRecord.calorie))
                .filter_by(daily_log_id=daily_log.id)
                .scalar()
                or 0
            )

            daily_log.total_calorie_in = total_calorie



            db.session.commit()

            return {
                "message": "Food record deleted successfully",
                "daily_log_id": daily_log.id,
                "total_calorie_in": daily_log.total_calorie_in,
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500