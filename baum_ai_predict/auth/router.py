from fastapi import APIRouter, Depends, Request, Response, UploadFile, File, HTTPException
from fastapi.security import HTTPBearer
from fastapi_users import BaseUserManager
from fastapi_users.password import PasswordHelper
from typing import List
from fastapi import FastAPI, HTTPException
from .db import async_session_maker, get_async_session, User
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.auth_schema import Id
from schemas.user_schema import UserExpand, UserDB, UserUpdate, UserCreate, UserOrm, \
    UserCreateWithoutPassword, BaseUserCreate, BaseUserModel, UserClass
from fastapi.responses import JSONResponse
from .register import get_register_router
from .apiusers import auth_backend, set_cookies, current_user, fastapi_users, current_superuser
from .token_manager import get_new_tokens
from fastapi_restful import Resource, set_responses
from models import user
from sqlalchemy import insert, delete, update, select

security = HTTPBearer()


class APIAuthRouter(APIRouter):
    url = "/auth"
    tags = ['auth']

    def __init__(self):
        super().__init__(prefix=self.url, tags=self.tags)
        self.include_router(get_register_router(
            fastapi_users.get_user_manager,
            UserCreateWithoutPassword,
            UserCreate,
        ))
        self.include_router(fastapi_users.get_auth_router(auth_backend))
        self.add_api_route('/refresh_token', self.refresh_token)
        self.add_api_route(
            '/update_password',
            self.update_password,
            methods=['POST'],
        )

    @staticmethod
    def refresh_token(request: Request, response: Response):
        if request.cookies.get('refresh_token') is None:
            raise HTTPException(
                status_code=404,
                detail="Refresh token не передан"
            )
        tokens = get_new_tokens(request.cookies.get('refresh_token'))
        set_cookies(response, **tokens)
        return tokens.get('access_token')

    @staticmethod
    async def update_password(password_old: str, password_new: str, cur_user: UserDB = current_user,
                              session: AsyncSession = Depends(get_async_session)):
        verify_password, new_hash_password = PasswordHelper().verify_and_update(password_old,
                                                                                cur_user.hashed_password)
        if not verify_password:
            raise HTTPException(status_code=400, detail="Неверный пароль")
        if password_new == password_old:
            raise HTTPException(status_code=400, detail="Новый пароль совпадает со старым")
        new_pass = PasswordHelper().hash(password_new)
        nc = user.update().where(user.c.id == cur_user.id).values(hashed_password=new_pass)
        await session.execute(nc)
        await session.commit()
        return "Пароль успешно изменен"


class APIUserRouter(APIRouter):
    url = "/users"
    tags = ['users']

    def __init__(self):
        super().__init__(prefix=self.url, tags=self.tags)
        self.add_api_route('/', self.get_user, methods=['GET'])
        self.add_api_route('/', self.change_user, methods=['PUT'])
        self.add_api_route('/', self.delete_user, methods=['DELETE'])
        self.add_api_route('/me', self.get_me, methods=['GET'])
        self.add_api_route('/me', self.change_me, methods=['PATCH'])

    @staticmethod
    async def get_user(id: Id = None, expand: bool = True, session: AsyncSession = Depends(get_async_session),
                       superuser=current_superuser):
        """
        Получение информации о пользователях
        @param id: идентификатор пользователя
        @param expand: развернуть ли информацию об вложенных объектах
        @param superuser: информация о пользователе, если он является superuser
        @return: информация о пользователях
        :param session:
        :param session:
        """
        query = select(user).where(user.c.id == id)
        results = await session.execute(query)
        u = results.mappings().all()
        if u:
            u = u[0]
            if not expand:
                return BaseUserModel(id=u.id, email=u.email, is_active=u.is_active, is_superuser=u.is_superuser,
                                     is_verified=u.is_verified)
            else:
                return UserExpand(id=u.id, name=u.name, surname=u.surname, patronymic=u.patronymic, phone=u.phone,
                                  email=u.email, is_active=u.is_active, is_superuser=u.is_superuser,
                                  is_verified=u.is_verified)
        else:
            return JSONResponse(status_code=404, content={"message": "User not found"})

    @staticmethod
    async def change_user(id: Id, user_update: UserUpdate, session: AsyncSession = Depends(get_async_session),
                          superuser=current_superuser):
        """
        Обновление информации
        @param id: идентификатор пользователя
        @param user_update: новая информация о пользователе
        @param superuser: информация о пользователе, если он является superuser
        @return: статус операции
        """
        query = select(user).where(user.c.id == id)
        results = await session.execute(query)
        u = results.mappings().all()
        if u:
            new_pass = PasswordHelper().hash(user_update.password)
            nc = user.update().where(user.c.id == id).values(name=user_update.name, surname=user_update.surname,
                                                             patronymic=user_update.patronymic,
                                                             phone=user_update.phone, email=user_update.email,
                                                             is_active=user_update.is_active,
                                                             is_superuser=user_update.is_superuser,
                                                             hashed_password=new_pass)
            await session.execute(nc)
            await session.commit()
            query = select(user).where(user.c.id == id)
            results = await session.execute(query)
            u = results.mappings().all()[0]
            return UserExpand(**dict(u))
        else:
            return JSONResponse(status_code=404, content={"message": "User not found"})

    @staticmethod
    async def delete_user(id: Id, superuser=current_superuser, session: AsyncSession = Depends(get_async_session)):
        """
        Удаление пользователя
        @param id: идентификатор пользователя
        @param superuser: информация о пользователе, если он является superuser
        @return: статус операции
        """
        query = select(user).where(user.c.id == id)
        results = await session.execute(query)
        u = results.mappings().all()
        if u:
            stmt = (delete(user).where(user.c.id == id))
            await session.execute(stmt)
            await session.commit()
            return JSONResponse(status_code=200, content={"message": "Deleted"})
        else:
            return JSONResponse(status_code=404, content={"message": "User not found"})

    @staticmethod
    async def get_me(cur_user: UserDB = current_user) -> UserExpand:
        """
        Получение информации о текущем пользователе
        @param user: информация о пользователе, который отправляет запрос
        @return: информация о пользователе
        """
        return cur_user

    @staticmethod
    async def change_me(user_update: UserUpdate, cur_user: UserDB = current_user,
                        session: AsyncSession = Depends(get_async_session), ) -> UserExpand:
        """
        Изменение информации о текущем пользователе
        @param user: информация о пользователе, который отправляет запрос
        @return: информация о пользователе
        """
        new_pass = PasswordHelper().hash(user_update.password)
        nc = user.update().where(user.c.id == cur_user.id).values(name=user_update.name, surname=user_update.surname,
                                                                  patronymic=user_update.patronymic,
                                                                  phone=user_update.phone, email=user_update.email,
                                                                  is_active=user_update.is_active,
                                                                  is_superuser=user_update.is_superuser,
                                                                  hashed_password=new_pass)
        await session.execute(nc)
        await session.commit()
        query = select(user).where(user.c.id == cur_user.id)
        results = await session.execute(query)
        u = results.mappings().all()[0]
        return UserExpand(**dict(u))
