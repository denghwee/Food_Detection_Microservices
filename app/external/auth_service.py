import requests

AUTH_SERVICE_URL = "http://localhost:8080/api/users/profile"

def fetch_user_profile(jwt_token: str):
    headers = {
        "Authorization": f"Bearer {jwt_token}"
    }

    response = requests.get(
        AUTH_SERVICE_URL,
        headers=headers,
        timeout=5
    )

    if response.status_code != 200:
        raise Exception(f"Failed to fetch user profile: {response.status_code}")

    return response.json()
