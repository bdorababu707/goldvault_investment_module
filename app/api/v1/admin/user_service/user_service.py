from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from app.db.mongo.mongodb import find_one
from app.models.base import OutModel
from app.core.security import create_access_token, decode_jwt_token, get_current_admin
from app.schemas.user import CreateUserSchema
from app.services.user_service.user_service import UserService
from pydantic import EmailStr
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/create-user", response_model=OutModel)
async def create_user(
    request: CreateUserSchema,
    current_admin = Depends(get_current_admin)
):

    try:
        result = await UserService.create_user(request, current_admin)
        return result
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to create user",
            data=str(e),
        )

@router.get("/all-users", response_model=OutModel)
async def get_all_users(
    current_admin = Depends(get_current_admin)
):

    try:
        result = await UserService.get_all_users(current_admin)
        return result
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to fetch users",
            data=str(e),
        )

@router.get("/user-id", response_model=OutModel)
async def get_user_details(
    user_id: str,
    current_admin = Depends(get_current_admin)
):

    try:
        result = await UserService.get_user_by_id(user_id, current_admin)
        return result
    except Exception as e:
        return OutModel(
            status="error",
            status_code=500,
            comment="Failed to fetch user details",
            data=str(e),
        )