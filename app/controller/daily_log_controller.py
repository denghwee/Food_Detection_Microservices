# app/controller/daily_log_controller.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.daily_log_service import DailyLogService

daily_log_bp = Blueprint("daily_log_bp", __name__, url_prefix="/api/v2")

@daily_log_bp.route("/daily-logs", methods=["GET"])
@jwt_required()
def get_daily_logs():
    user_email = get_jwt_identity()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    logs, error = DailyLogService.get_daily_logs(user_email, start_date, end_date)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"status": "success", "logs": logs}), 200


@daily_log_bp.route("/daily-logs/summary", methods=["GET"])
@jwt_required()
def get_summary():
    user_email = get_jwt_identity()
    period = request.args.get("period", "week")

    summary, error = DailyLogService.get_summary(user_email, period)
    if error:
        return jsonify({"error": error}), 400

    return jsonify({"status": "success", "period": period, "summary": summary}), 200
