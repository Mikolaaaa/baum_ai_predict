"""
Упрвление токенами авторизации.
"""
import time
from typing import Dict

from fastapi_users.authentication import JWTStrategy
from fastapi_users.jwt import decode_jwt, generate_jwt

from .const import (
    ACCESS_TOKEN_LIFETIME_SECONDS, API_SECRET_KEY,
    REFRESH_TOKEN_LIFETIME_SECONDS,
)
from schemas.auth_schema import JWTPayload


def get_jwt_strategy() -> JWTStrategy:
    """
    Получить объект класса проверки jwt токена.

    :return: Объект класса проверки
    """
    return JWTStrategy(
        secret=API_SECRET_KEY,
        lifetime_seconds=ACCESS_TOKEN_LIFETIME_SECONDS,
    )


def jwt_encode(payload, lifetime_seconds=None) -> str:
    """
    Создание jwt токена.

    :param payload: Полезная нагрузка
    :param lifetime_seconds: Время жизни
    :return: Токен jwt
    """
    token = generate_jwt(
        payload,
        secret=API_SECRET_KEY,
        lifetime_seconds=lifetime_seconds,
    )
    return token


def jwt_decode(token: str) -> dict:
    """
    Распаковка токета и получение payload.

    :param token: Токен
    :return: Полезная нагрузка
    """
    return decode_jwt(token, API_SECRET_KEY, audience=['fastapi-users:auth'])


def create_token(payload: JWTPayload, is_refresh_token: bool = False) -> str:
    """
    Сформировать токен jwt.

    :param payload: Полезная нагрузка
    :param is_refresh_token: Если это токен обновления
    :return: jwt токен
    """
    lifetime = (
        REFRESH_TOKEN_LIFETIME_SECONDS
        if is_refresh_token else ACCESS_TOKEN_LIFETIME_SECONDS
    )
    jwt_payload = JWTPayload(
        user_id=payload.user_id,
        exp=time.time() + lifetime,
        is_refresh_token=is_refresh_token,
    )
    payload_dict = jwt_payload.dict()
    payload_dict['user_id'] = str(payload_dict.get('user_id'))
    return jwt_encode(
        payload=payload_dict,
        lifetime_seconds=lifetime,
    )


def get_payload(token: str) -> JWTPayload:
    """
    Получить данные из jwt токена.

    :param token: Токен
    :return: Полезная нагрузка токена
    """
    token_dict = jwt_decode(token)
    token_dict['user_id'] = token_dict.get('user_id') or token_dict.get('sub')
    return JWTPayload.parse_obj(token_dict)


def get_new_tokens(refresh_token: str) -> None | Dict[str, str]:
    """
    Получить новые токены.

    :param refresh_token: Токен обновления
    :return: access и refresh
    """
    payload = get_payload(refresh_token)
    if not payload.is_refresh_token or time.time() > payload.exp:
        return None
    return {
        'access_token': create_token(payload),
        'refresh_token': create_token(payload, is_refresh_token=True),
    }
