from datetime import datetime, timedelta

import jwt

from app.core.settings import settings


def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    data["exp"] = expire
    data["mode"] = "access_token"

    encoded_jwt = jwt.encode(data, settings.jwt_user_secret_key, settings.algorithm)

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    data["exp"] = expire
    data["mode"] = "refresh_token"

    encoded_jwt = jwt.encode(data, settings.jwt_user_secret_key, settings.algorithm)

    return encoded_jwt
