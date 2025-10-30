# --- app/schemas/admin_schema.py ---
from pydantic import BaseModel, EmailStr
from typing import List

class CreateSuperAdmin(BaseModel):
    firstname: str
    surname: str
    email: EmailStr
    country: str
    country_code: str
    phone_number: str
    password: str

class CreateDepartmentAdmin(BaseModel):
    firstname: str
    surname: str 
    email: EmailStr
    country: str
    country_code: str
    phone_number: str
    password: str 

class CreateAdmin(BaseModel):
    firstname: str
    surname: str
    email: EmailStr
    country: str
    country_code: str
    phone_number: str
    password: str
    user_roles: List[str]

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str