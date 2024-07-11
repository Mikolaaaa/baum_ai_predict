"""
Схемы связанные с авторизацией.
"""

from uuid import UUID
from fastapi_users.authentication.transport.bearer import BearerResponse
from pydantic import BaseModel, Field
from typing_extensions import Annotated

Id = UUID


class AuthResponse(BearerResponse):
    """
    Схема ответа при аутентификации.
    """

    access_token: str
    token_type: str


class JWTPayload(BaseModel):
    """
    Полезная нагрузка токена.
    """

    user_id: Id
    exp: Annotated[float, Field(description='Время жизни токена')]
    aud: Annotated[
        list[str],
        Field(description='Строка идентификации токена'),
    ] = ['fastapi-users:auth']
    is_refresh_token: bool = False
