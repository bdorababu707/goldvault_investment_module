from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

class CreateInvestmentPlan(BaseModel):
    plan_name: str
    description: str
    bonus_percentage: float = Field(..., ge=0, description="Bonus percentage must be greater than or equal to 0")
    relaxation_days: int = Field(..., ge=0, description="Relaxation days must be greater than or equal 0")
    minimum_investment_amount: int = Field(..., gt=0, description="Minimum investment amount will be greater than 0")


class UpdateInvestmentPlan(BaseModel):
    plan_name: Optional[str] = None
    description: Optional[str] = None
    bonus_percentage: Optional[float] = None
    relaxation_days: Optional[int] = None
    status: Optional[Literal["ACTIVE", "INACTIVE"]] = None



class CreateInvestmentSubscription(BaseModel):
    user_id: str
    plan_id: str
    plan_start_date: str

    @field_validator("plan_start_date")
    @classmethod
    def validate_start_date_format(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%d-%m-%Y")
            return value
        except ValueError:
            raise ValueError("plan_start_date must be in DD-MM-YYYY format")

        

class CreateMonthlyInvestment(BaseModel):
    user_id: str
    subscription_id: str
    deposit_date: str
    amount_invested: float = Field(..., gt=0)
    gold_rate: float = Field(..., gt=0)
    grams_purchased: float = Field(..., gt=0)
    payment_method: Literal["CASH", "CARD", "BANK_TRANSFER"]
    transaction_ref: Optional[str] = None
    payment_proof_url: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator("deposit_date")
    @classmethod
    def validate_date_format(cls, value):
        try:
            datetime.strptime(value, "%d-%m-%Y")
            return value
        except ValueError:
            raise ValueError("deposit_date must be in DD-MM-YYYY format")