from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.calorie_service import CalorieService
from app.utils.jwt_utils import get_current_user_id

calorie_bp = Blueprint(
    "calorie",
    __name__,
    url_prefix="/api/v2/calories"
)


@calorie_bp.route("/food-records", methods=["POST"])
@jwt_required()
def add_food_records():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json()
    return CalorieService.add_food_records(user_id, payload)


@calorie_bp.route("/food-records/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_food_record(record_id):
    user_id = get_current_user_id()
    payload = request.get_json()
    payload["id"] = record_id
    return CalorieService.update_food_record(user_id, payload)



@calorie_bp.route("/food-records", methods=["GET"])
@jwt_required()
def get_food_records():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    log_date = request.args.get("log_date")
    return CalorieService.get_food_records(user_id, log_date)
@calorie_bp.route("/food-records/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_food_record(record_id):
    user_id = get_current_user_id()
    if not user_id:
        return {"error": "Unauthorized"}, 401

    return CalorieService.delete_food_record(user_id, record_id)
