from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.services.daily_log_service import DailyLogService, create_daily_logs_for_all_users
from app.utils.jwt_utils import get_current_user_id

daily_log_bp = Blueprint(
    "daily_log_bp",
    __name__,
    url_prefix="/api/v2"
)


@daily_log_bp.route("/daily-logs", methods=["GET"])
@jwt_required()
def get_daily_logs():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    logs, error = DailyLogService.get_daily_logs(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )

    if error:
        return jsonify({"error": error}), 400

    return jsonify({"status": "success", "logs": logs}), 200


@daily_log_bp.route("/daily-logs/generate", methods=["POST"])
@jwt_required()
def generate_daily_logs():
    """
    API test: gọi tay logic tạo DailyEnergyLog
    """
    payload = request.get_json(silent=True) or {}
    date_str = payload.get("date")

    target_date = None
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format (YYYY-MM-DD)"}), 400

    result = create_daily_logs_for_all_users(target_date)

    return jsonify({
        "status": "success",
        "data": result
    }), 200

@daily_log_bp.route("/daily-logs/steps", methods=["POST"])
@jwt_required()
def update_daily_steps():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    steps = data.get("steps")
    log_date = data.get("log_date")  # optional YYYY-MM-DD

    if steps is None or steps < 0:
        return jsonify({"error": "steps is required and must be >= 0"}), 400

    result, error = DailyLogService.update_daily_steps(
        user_id=user_id,
        steps=steps,
        log_date=log_date
    )

    if error:
        return jsonify({"error": error}), 400

    return result, 200
