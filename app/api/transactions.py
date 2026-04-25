from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from app.database import get_db
from app.models.transaction import Transaction
from app.models.merchant import Merchant
from app.models.event import Event
from app.schemas.transaction import TransactionResponse, TransactionDetail, TransactionListResponse
from datetime import date, datetime
from typing import Optional

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    merchant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by payment_status"),
    settlement_status: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    session: AsyncSession = Depends(get_db)
):
    """
    List transactions with filtering, pagination, and sorting.
    """
    # Build base query
    query = (
        select(
            Transaction.id,
            Transaction.merchant_id,
            Transaction.amount,
            Transaction.currency,
            Transaction.payment_status,
            Transaction.settlement_status,
            Transaction.created_at,
            Transaction.updated_at,
            Merchant.name.label('merchant_name')
        )
        .join(Merchant, Transaction.merchant_id == Merchant.id)
    )
    
    # Build count query
    count_query = select(func.count()).select_from(query.subquery())
    
    # Apply filters
    conditions = []
    if merchant_id:
        conditions.append(Transaction.merchant_id == merchant_id)
    if status:
        conditions.append(Transaction.payment_status == status)
    if settlement_status:
        conditions.append(Transaction.settlement_status == settlement_status)
    if start_date:
        conditions.append(func.date(Transaction.created_at) >= start_date)
    if end_date:
        conditions.append(func.date(Transaction.created_at) <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = select(func.count()).select_from(
            select(Transaction).where(and_(*conditions)).subquery()
        )
    
    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    sort_column = getattr(Transaction, sort_by, Transaction.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await session.execute(query)
    rows = result.all()
    
    # Convert to response format
    transactions = []
    for row in rows:
        transactions.append({
            "id": row.id,
            "merchant_id": row.merchant_id,
            "amount": float(row.amount),
            "currency": row.currency,
            "payment_status": row.payment_status,
            "settlement_status": row.settlement_status,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "merchant_name": row.merchant_name
        })
    
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    
    return TransactionListResponse(
        data=transactions,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    )


@router.get("/{transaction_id}", response_model=TransactionDetail)
async def get_transaction(
    transaction_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Get transaction details with event history.
    """
    # Get transaction
    query = (
        select(
            Transaction.id,
            Transaction.merchant_id,
            Transaction.amount,
            Transaction.currency,
            Transaction.payment_status,
            Transaction.settlement_status,
            Transaction.created_at,
            Transaction.updated_at,
            Merchant.name.label('merchant_name')
        )
        .join(Merchant, Transaction.merchant_id == Merchant.id)
        .where(Transaction.id == transaction_id)
    )
    
    result = await session.execute(query)
    transaction = result.first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get event history
    events_query = (
        select(Event)
        .where(Event.transaction_id == transaction_id)
        .order_by(Event.timestamp)
    )
    
    events_result = await session.execute(events_query)
    events = events_result.scalars().all()
    
    event_history = [
        {
            "event_id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat()
        }
        for event in events
    ]
    
    return TransactionDetail(
        id=transaction.id,
        merchant_id=transaction.merchant_id,
        amount=float(transaction.amount),
        currency=transaction.currency,
        payment_status=transaction.payment_status,
        settlement_status=transaction.settlement_status,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
        merchant_name=transaction.merchant_name,
        event_history=event_history
    )
