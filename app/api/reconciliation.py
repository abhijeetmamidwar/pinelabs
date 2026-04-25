from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.reconciliation import ReconciliationSummaryResponse, DiscrepanciesResponse
from app.services.reconciliation_service import ReconciliationService
from datetime import date
from typing import Optional

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.get("/summary", response_model=ReconciliationSummaryResponse)
async def get_reconciliation_summary(
    group_by: str = Query(..., description="Group by: merchant, date, status, or merchant_date"),
    merchant_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db)
):
    """
    Get reconciliation summary grouped by specified dimension.
    
    Valid group_by values:
    - merchant: Group by merchant
    - date: Group by date
    - status: Group by payment status
    - merchant_date: Group by merchant and date
    """
    summary = await ReconciliationService.get_summary(
        session,
        group_by=group_by,
        merchant_id=merchant_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return ReconciliationSummaryResponse(summary=summary)


@router.get("/discrepancies", response_model=DiscrepanciesResponse)
async def get_discrepancies(
    merchant_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db)
):
    """
    Get transactions with payment/settlement discrepancies.
    
    Discrepancy types:
    - payment_processed_but_not_settled: Payment marked processed but never settled
    - settlement_for_failed_payment: Settlement recorded for a failed payment
    - stale_initiated_transaction: Payment initiated but not updated for > 24 hours
    """
    discrepancies, total = await ReconciliationService.get_discrepancies(
        session,
        merchant_id=merchant_id
    )
    
    return DiscrepanciesResponse(
        discrepancies=discrepancies,
        total=total
    )
