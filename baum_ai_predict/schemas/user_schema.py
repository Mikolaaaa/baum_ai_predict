import uuid
from pydantic import UUID4, BaseModel, EmailStr, Field, field_validator
from typing_extensions import Annotated


class CreateUpdateDictModel(BaseModel):
    def create_update_dict(self):
        return self.dict(
            exclude_unset=True,
            exclude={
                'id',
                'is_superuser',
                'is_active',
                'is_verified',
                'oauth_accounts',
            },
        )

    def create_update_dict_superuser(self):
        return self.dict(
            exclude_unset=True,
            exclude={'id'},
        )


class CreateDictModel(BaseModel):
    def create_update_dict(self):
        return self.dict(
            exclude={
                'id',
                'oauth_accounts',
            },
        )

    def create_update_dict_superuser(self):
        return self.dict(exclude={'id'})


class BaseUserModel(BaseModel):
    id: Annotated[UUID4, Field(default_factory=uuid.uuid4)]
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False


class BaseUser(CreateUpdateDictModel, BaseUserModel):
    """Base User model."""

    pass


class BaseUserCreate(CreateDictModel):
    email: EmailStr
    password: str
    is_active: bool | None = True
    is_superuser: bool | None = False
    is_verified: bool | None = False


class BaseUserUpdate(CreateUpdateDictModel):
    password: str | None
    email: EmailStr | None
    is_active: bool | None
    is_superuser: bool | None
    is_verified: bool | None


class BaseUserDB(BaseUser):
    hashed_password: str

    class Config:
        orm_mode = True
        from_attributes = True


class UserData(BaseModel):
    name: str | None = ''
    surname: str | None = ''
    patronymic: str | None = ''
    phone: str | None = ''


class UserClass(BaseUser, UserData):
    pass


class UserCreate(BaseUserCreate, UserData):
    pass


class UserCreateWithoutPassword(UserCreate):
    password: str | None = None

    class Config:
        orm_mode = True
        from_attributes = True


class UserUpdate(BaseUserUpdate, UserData):
    pass


class UserDB(UserClass, BaseUserDB):
    pass


class UserExpand(BaseUserModel, UserData):
    pass


class UserOrm(UserDB):
    class Config:
        orm_mode = True
        from_attributes = True
