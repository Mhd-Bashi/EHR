from itsdangerous import URLSafeTimedSerializer
from flask import current_app


def _ts() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=current_app.config["SECRET_KEY"],
        salt=current_app.config["SECURITY_PASSWORD_SALT"],
    )


def generate_token(doctor_id: int, purpose: str) -> str:
    """purpose = 'confirm' or 'reset'"""
    return _ts().dumps({"id": doctor_id, "p": purpose})


def load_token(token: str, max_age_seconds: int, expected_purpose: str):
    data = _ts().loads(token, max_age=max_age_seconds)
    if data.get("p") != expected_purpose:
        raise ValueError("Wrong token purpose")
    return data["id"]
