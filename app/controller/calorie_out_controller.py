from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.services.calorie_out_service import CalorieOutService
from app.utils.jwt_utils import get_current_user_email

calorie_out_bp = Blueprint("calorie_out", __name__, url_prefix="/api/v2/calories-out")


@calorie_out_bp.route("/activities", methods=["POST"])
@jwt_required()
def add_activities():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    return CalorieOutService.add_activities(user_email, data)


@calorie_out_bp.route("/activities", methods=["PUT"])
@jwt_required()
def update_activities():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    return CalorieOutService.update_activities(user_email, data)


@calorie_out_bp.route("/activities", methods=["GET"])
@jwt_required()
def get_activities():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    log_date = request.args.get("log_date")
    return CalorieOutService.get_activities(user_email, log_date)
