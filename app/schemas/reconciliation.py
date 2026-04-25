from pydantic import BaseModel
from typing import List, Optional


class ReconciliationSummaryItem(BaseModel):
    merchant_id: Optional[str] = None
    merchant_name: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    total_transactions: int
    total_amount: float
    payment_processed_count: int
    payment_failed_count: int
    settled_count: int
    pending_settlement_count: int


class ReconciliationSummaryResponse(BaseModel):
    summary: List[ReconciliationSummaryItem]


class DiscrepancyItem(BaseModel):
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float
    payment_status: str
    settlement_status: str
    discrepancy_type: str
    created_at: str


class DiscrepanciesResponse(BaseModel):
    discrepancies: List[DiscrepancyItem]
    total: int
