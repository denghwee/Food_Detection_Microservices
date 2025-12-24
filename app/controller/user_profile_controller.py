from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.user_profile_service import UserProfileService
from app.utils.jwt_utils import get_current_user_email

user_profile_bp = Blueprint("user_profile", __name__, url_prefix="/api/v2/user-profile")


@user_profile_bp.route("", methods=["GET"])
@jwt_required()
def get_user_profile():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    return UserProfileService.get_user_profile(user_email)


@user_profile_bp.route("", methods=["POST"])
@jwt_required()
def create_user_profile():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    jwt_token = request.headers.get("Authorization").split(" ")[1]
    data = request.get_json()

    return UserProfileService.create_user_profile(
        user_email=user_email,
        payload=data,
        jwt_token=jwt_token
    )



@user_profile_bp.route("", methods=["PUT"])
@jwt_required()
def update_user_profile():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    return UserProfileService.update_user_profile(user_email, data)
@user_profile_bp.route("/weight-history", methods=["GET"])
@jwt_required()
def weight_history():
    user_email = get_current_user_email()
    if not user_email:
        return jsonify({"error": "Unauthorized"}), 401

    return UserProfileService.get_weight_history(user_email)