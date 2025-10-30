
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError, ExpiredSignatureError, PyJWTError
from app.db.mongo.mongodb import find_one
from app.core.config import settings

# Configure the password hashing context
password_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode,settings.JWT.SECRET_KEY, algorithm=settings.JWT.ALGORITHM)
    return encoded_jwt


async def create_verification_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT.VERIFICATION_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT.SECRET_KEY, algorithm=settings.JWT.ALGORITHM)
    return encoded_jwt


async def decode_jwt_token(token: str):
        payload = jwt.decode(token, settings.JWT.SECRET_KEY, algorithms=[settings.JWT.ALGORITHM])
        return payload

async def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    """
    return password_context.hash(password)

async def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against the hashed password.
    """
    return password_context.verify(plain_password, hashed_password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

async def get_current_admin(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = await decode_jwt_token(token)
        # print("DECODED PAYLOAD:", payload, type(payload))

        admin_id = payload.get("uuid")

        if admin_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing admin_id",
                headers={"WWW-Authenticate": "Bearer"},
            )

        admin = await find_one(settings.DB_TABLE.ADMINS, {"uuid": admin_id})

        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found",
            )

        return admin

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
