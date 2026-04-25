from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class EventBase(BaseModel):
    event_id: str = Field(..., description="Unique identifier for the event")
    event_type: str = Field(..., description="Type of event: payment_initiated, payment_processed, payment_failed, settled")
    transaction_id: str = Field(..., description="Transaction identifier")
    merchant_id: str = Field(..., description="Merchant identifier")
    merchant_name: str = Field(..., description="Merchant name")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., description="Currency code (e.g., INR)")
    timestamp: datetime = Field(..., description="Event timestamp")


class EventCreate(EventBase):
    pass


class EventResponse(BaseModel):
    id: str
    event_type: str
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    timestamp: datetime
    processed_at: datetime
    
    class Config:
        from_attributes = True


class BulkEventRequest(BaseModel):
    events: List[EventCreate]


class BulkEventResponse(BaseModel):
    total_events: int
    processed: int
    duplicates: int
    errors: int
