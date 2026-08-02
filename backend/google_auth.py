import requests

from config import GOOGLE_CLIENT_ID


def verify_google_token(token):

    response = requests.get(
        f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
    )

    if response.status_code != 200:
        return None

    user_info = response.json()

    if user_info["aud"] != GOOGLE_CLIENT_ID:
        return None

    return {
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "google_id": user_info.get("sub")
    }