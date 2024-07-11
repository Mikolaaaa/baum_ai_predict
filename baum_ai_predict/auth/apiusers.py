"""
Управление авторизацией пользователя.
"""

from typing import Any
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_users import BaseUserManager, FastAPIUsers, db, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport
from fastapi_users.db import SQLAlchemyUserDatabase
from schemas.user_schema import UserCreate, UserDB
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

from .const import (
    ACCESS_TOKEN_COOKIE_LIFETIME_SECONDS, API_SECRET_KEY, API_URL_PREFIX,
    REFRESH_TOKEN_COOKIE_LIFETIME_SECONDS, TOKEN_TYPE,
)
from .db import get_user_db
from .token_manager import (
    create_token, get_jwt_strategy, get_payload,
)
from schemas.auth_schema import AuthResponse

limiter = Limiter(key_func=get_remote_address, default_limits=['100/minute'])
depends_get_user_db = Depends(get_user_db)


class UserManager(UUIDIDMixin, BaseUserManager[UserDB, uuid.UUID]):
    user_db_model = UserDB
    reset_password_token_secret = API_SECRET_KEY
    verification_token_secret = API_SECRET_KEY


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


def set_cookies(response, access_token: str, refresh_token: str):
    """
    Установка куки в ответ.

    :param response: Ответ
    :param access_token: Маркер доступа
    :param refresh_token: Токен обновления маркера доступа
    """
    response.set_cookie(
        'access_token',
        access_token,
        httponly=False,
        path='/',
        max_age=ACCESS_TOKEN_COOKIE_LIFETIME_SECONDS,
    )
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
        path='/',
        max_age=REFRESH_TOKEN_COOKIE_LIFETIME_SECONDS,
    )


class AuthTransport(BearerTransport):
    """
    Класс транспорта для авторизации.
    """

    async def get_login_response(
        self,
        token: str
    ) -> Any:
        """
        Ответ при запросе на вход в приложение.

        :param token: Токен
        :param response: Ответ
        :return: Ответ с установленным токеном
        """
        payload = get_payload(token)
        if payload.is_refresh_token:
            return None

        refresh_token = create_token(payload, is_refresh_token=True)
        response = JSONResponse(status_code=200, content=dict(AuthResponse(
            access_token=token,
            token_type=TOKEN_TYPE,
        )))
        set_cookies(response, token, refresh_token)
        return response


    async def get_logout_response(self) -> Any:
        """
        Ответ при запросе на выход из приложения.

        :param response: Ответ
        :return: Ответ
        """
        response = JSONResponse(status_code=200, content={'message': 'logged_out'})
        response.set_cookie(
            'access_token',
            '',
            httponly=False,
            path='/',
            max_age=-1,
        )
        response.set_cookie(
            'refresh_token',
            '',
            httponly=True,
            path='/',
            max_age=-1,
        )
        return response


bearer_transport = AuthTransport(
    tokenUrl='auth/login',
)

auth_backend = AuthenticationBackend(
    name='jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


fastapi_users = FastAPIUsers[UserDB, uuid.uuid4](get_user_manager, [auth_backend])
current_user = Depends(fastapi_users.current_user(active=True))
current_superuser = Depends(fastapi_users.current_user(active=True, superuser=True))
