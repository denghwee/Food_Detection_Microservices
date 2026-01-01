from flask_jwt_extended import get_jwt_identity, get_jwt


def get_current_user_id():

    claims = get_jwt()
    user_id = claims.get("userId")
    if not user_id:
        return None
    return user_id
