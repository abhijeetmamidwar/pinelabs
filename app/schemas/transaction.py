from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class TransactionBase(BaseModel):
    id: str
    merchant_id: str
    amount: float
    currency: str
    payment_status: str
    settlement_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class TransactionResponse(TransactionBase):
    merchant_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class TransactionDetail(TransactionResponse):
    event_history: List[dict] = []


class TransactionListResponse(BaseModel):
    data: List[TransactionResponse]
    pagination: dict
