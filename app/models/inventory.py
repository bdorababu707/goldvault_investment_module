from pydantic import BaseModel, EmailStr
from typing import List, Literal, Optional

class InvestmentInventory(BaseModel):
    uuid: str
    user_id: str
    subscription_id: str
    gold_grams_24k: float
    invested_amount: float
    bonus_percentage_earned: float = 0
    status: str
    currency: str
    created_at: int = 0
    updated_at: int = 0