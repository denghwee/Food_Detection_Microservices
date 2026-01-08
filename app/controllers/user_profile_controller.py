from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.user_profile_service import UserProfileService
from app.utils.jwt_utils import get_current_user_id

user_profile_bp = Blueprint(
    "user_profile",
    __name__,
    url_prefix="/api/v2/user-profile"
)


@user_profile_bp.route("", methods=["GET"])
@jwt_required()
def get_user_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    return UserProfileService.get_user_profile(user_id)


@user_profile_bp.route("", methods=["POST"])
@jwt_required()
def create_user_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    jwt_token = request.headers.get("Authorization").split(" ")[1]
    payload = request.get_json()

    return UserProfileService.create_user_profile(
        user_id=user_id,
        payload=payload,
        jwt_token=jwt_token
    )


@user_profile_bp.route("", methods=["PUT"])
@jwt_required()
def update_user_profile():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json()

    jwt_token = request.headers.get("Authorization")

    return UserProfileService.update_user_profile(
        user_id=user_id,
        payload=payload,
        jwt_token=jwt_token
    )


@user_profile_bp.route("/weight-history", methods=["GET"])
@jwt_required()
def weight_history():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    return UserProfileService.get_weight_history(user_id)


@user_profile_bp.route("/ai/profile-input", methods=["GET"])
@jwt_required()
def get_ai_profile_input():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data, error = UserProfileService.build_ai_profile_input(user_id)
    if error:
        return jsonify({"error": error}), 400

    return jsonify(data), 200

@user_profile_bp.route("/ai/goal-input", methods=["GET"])
@jwt_required()
def get_ai_goal_input():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data, error = UserProfileService.build_ai_goal_input(user_id)
    if error:
        return jsonify({"error": error}), 400

    return jsonify(data), 200

