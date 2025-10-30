from pydantic import BaseModel, EmailStr, Field
from typing import Dict, Optional, Literal

class InvestmentPlan(BaseModel):
    uuid: str
    plan_name: str
    description: str
    bonus_percentage: float
    relaxation_days: int
    minimum_investment_amount: int
    status: Literal["ACTIVE", "INACTIVE"]
    bonus_percentage: float
    metadata: Optional[dict] = None
    created_at: int = 0
    updated_at: int = 0


class UserInvestmentSubscription(BaseModel):
    uuid: str = Field(..., description="Unique subscription ID")
    user_id: str = Field(..., description="Linked user UUID")
    plan_id: str = Field(..., description="Linked base plan UUID")
    plan_start_date: str = Field(..., description="Subscription start date (DD-MM-YYYY)")
    is_eligible_for_bonus: bool = True
    metadata: Optional[dict] = None
    status: Literal["ACTIVE", "INACTIVE", "COMPLETED"] = "ACTIVE"
    created_at: int = 0
    updated_at: int = 0


class InvestmentEntry(BaseModel):
    uuid: str
    user_id: str
    subscription_id: str
    deposit_date: str
    amount_invested: float
    gold_rate: float
    grams_purchased: float
    payment_method: str
    transaction_reference: Optional[str] = None
    payment_proof_url: Optional[str] = None
    bonus_earned: float
    is_bonus_eligible: bool
    is_bonus_credited: bool
    remarks: Optional[str] = None
    status: str = "SUCCESS"
    metadata: Optional[dict] = None
    created_at: int = 0
    updated_at: int = 0

