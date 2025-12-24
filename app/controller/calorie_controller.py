from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.calorie_service import CalorieService
from app.utils.jwt_utils import get_current_user_email

calorie_bp = Blueprint("calorie", __name__, url_prefix="/api/v2/calories")


@calorie_bp.route("/food-records", methods=["POST"])
@jwt_required()
def add_food_records():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    return CalorieService.add_food_records(user_email, data)


@calorie_bp.route("/food-records", methods=["PUT"])
@jwt_required()
def update_food_records():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    return CalorieService.update_food_records(user_email, data)
@calorie_bp.route("/food-records", methods=["GET"])
@jwt_required()
def get_food_records():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    log_date = request.args.get("log_date")
    return CalorieService.get_food_records(user_email, log_date)

