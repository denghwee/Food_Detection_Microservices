from flask_jwt_extended import get_jwt_identity

def get_current_user_email():
    return get_jwt_identity()
