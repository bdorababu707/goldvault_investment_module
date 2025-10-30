# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Optional


class DocumentFile(BaseModel):
    """Individual document like passport, Aadhaar, etc."""
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    front: Optional[str] = None
    back: Optional[str] = None


class UserKycDocuments(BaseModel):
    """Holds multiple documents under 'documents' key"""
    documents: Dict[str, DocumentFile]


class CreateUserSchema(BaseModel):
    email: EmailStr
    country_code: str
    phone_number: str
    country: str
    full_name: str
    date_of_birth: Optional[str] = Field(None, description="dd/mm/yyyy format")
    nationality: Optional[str] = None
    country_of_residence: Optional[str] = None
    country_of_birth: Optional[str] = None
    full_address: Optional[str] = None
    kyc_documents: Optional[UserKycDocuments] = None  # <- wrapper for multiple docs
