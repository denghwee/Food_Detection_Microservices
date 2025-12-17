import requests

AUTH_SERVICE_URL = "http://localhost:8080/api/users/profile"

def fetch_user_basic_info(jwt_token: str, user_email: str):
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    response = requests.get(
        AUTH_SERVICE_URL,
        headers=headers,
        params={"email": user_email},
        timeout=5
    )

    if response.status_code != 200:
        raise Exception("Failed to fetch user info from AuthService")

    return response.json()
