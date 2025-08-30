from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from backend.api.models import User
from backend.api.deps import db_dependency, bcrypt_context

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = os.getenv("AUTH_ALGORITHM")


class UserCreateRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(username: str, password: str, db) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user


def create_access_token(username: str, user_id: int, expires_delta: timedelta) -> str:
    to_encode = {"sub": username, "id": user_id}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: UserCreateRequest):
    hashed_password = bcrypt_context.hash(create_user_request.password)
    create_user_model = User(
        username=create_user_request.username, hashed_password=hashed_password
    )
    db.add(create_user_model)
    db.commit()

    return { "message": "User created successfully", "status": status.HTTP_201_CREATED }


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username, user.id, timedelta(minutes=30))
    return { "access_token": access_token, "token_type": "bearer" }
