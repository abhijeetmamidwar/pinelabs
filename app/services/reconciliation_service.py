from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from app.models.transaction import Transaction
from app.models.merchant import Merchant
from app.models.event import Event
from datetime import datetime, date, timedelta
from typing import Optional, List


class ReconciliationService:
    
    @staticmethod
    async def get_summary(
        session: AsyncSession,
        group_by: str,
        merchant_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[dict]:
        """
        Get reconciliation summary grouped by specified dimension.
        """
        # Build base columns
        base_columns = [
            func.count(Transaction.id).label('total_transactions'),
            func.sum(Transaction.amount).label('total_amount'),
            func.sum(case((Transaction.payment_status == 'processed', 1), else_=0)).label('payment_processed_count'),
            func.sum(case((Transaction.payment_status == 'failed', 1), else_=0)).label('payment_failed_count'),
            func.sum(case((Transaction.settlement_status == 'settled', 1), else_=0)).label('settled_count'),
            func.sum(case((Transaction.settlement_status == 'pending', 1), else_=0)).label('pending_settlement_count')
        ]
        
        # Build query based on group_by
        if group_by == "merchant":
            query = (
                select(
                    Transaction.merchant_id,
                    Merchant.name.label('merchant_name'),
                    *base_columns
                )
                .join(Merchant, Transaction.merchant_id == Merchant.id)
                .group_by(Transaction.merchant_id, Merchant.name)
            )
        elif group_by == "date":
            query = (
                select(
                    func.date(Transaction.created_at).label('date'),
                    *base_columns
                )
                .group_by(func.date(Transaction.created_at))
            )
        elif group_by == "status":
            query = (
                select(
                    Transaction.payment_status,
                    *base_columns
                )
                .group_by(Transaction.payment_status)
            )
        elif group_by == "merchant_date":
            query = (
                select(
                    Transaction.merchant_id,
                    Merchant.name.label('merchant_name'),
                    func.date(Transaction.created_at).label('date'),
                    *base_columns
                )
                .join(Merchant, Transaction.merchant_id == Merchant.id)
                .group_by(Transaction.merchant_id, Merchant.name, func.date(Transaction.created_at))
            )
        else:
            raise ValueError(f"Invalid group_by value: {group_by}")
        
        # Apply filters
        conditions = []
        if merchant_id:
            conditions.append(Transaction.merchant_id == merchant_id)
        if start_date:
            conditions.append(func.date(Transaction.created_at) >= start_date)
        if end_date:
            conditions.append(func.date(Transaction.created_at) <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await session.execute(query)
        rows = result.all()
        
        # Convert to list of dicts
        summary = []
        for row in rows:
            item = {
                "total_transactions": row.total_transactions,
                "total_amount": float(row.total_amount) if row.total_amount else 0,
                "payment_processed_count": row.payment_processed_count or 0,
                "payment_failed_count": row.payment_failed_count or 0,
                "settled_count": row.settled_count or 0,
                "pending_settlement_count": row.pending_settlement_count or 0
            }
            
            if group_by in ["merchant", "merchant_date"]:
                item["merchant_id"] = row.merchant_id
                item["merchant_name"] = row.merchant_name
            if group_by in ["date", "merchant_date"]:
                item["date"] = row.date.isoformat() if row.date else None
            if group_by == "status":
                item["status"] = row.payment_status
            
            summary.append(item)
        
        return summary
    
    @staticmethod
    async def get_discrepancies(
        session: AsyncSession,
        merchant_id: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """
        Get transactions with payment/settlement discrepancies.
        Returns (list of discrepancies, total count)
        """
        # Build query for discrepancies
        # Discrepancy types:
        # 1. payment_processed but not settled
        # 2. settlement for failed payment
        # 3. stale initiated transactions (> 24 hours)
        
        stale_threshold = datetime.utcnow() - timedelta(hours=24)
        
        query = (
            select(
                Transaction.id.label('transaction_id'),
                Transaction.merchant_id,
                Merchant.name.label('merchant_name'),
                Transaction.amount,
                Transaction.payment_status,
                Transaction.settlement_status,
                Transaction.created_at,
                case(
                    (and_(
                        Transaction.payment_status == 'processed',
                        Transaction.settlement_status == 'pending'
                    ), 'payment_processed_but_not_settled'),
                    (and_(
                        Transaction.payment_status == 'failed',
                        Transaction.settlement_status == 'settled'
                    ), 'settlement_for_failed_payment'),
                    (and_(
                        Transaction.payment_status == 'initiated',
                        Transaction.created_at < stale_threshold
                    ), 'stale_initiated_transaction'),
                    else_='other'
                ).label('discrepancy_type')
            )
            .join(Merchant, Transaction.merchant_id == Merchant.id)
            .where(
                or_(
                    and_(
                        Transaction.payment_status == 'processed',
                        Transaction.settlement_status == 'pending'
                    ),
                    and_(
                        Transaction.payment_status == 'failed',
                        Transaction.settlement_status == 'settled'
                    ),
                    and_(
                        Transaction.payment_status == 'initiated',
                        Transaction.created_at < stale_threshold
                    )
                )
            )
        )
        
        if merchant_id:
            query = query.where(Transaction.merchant_id == merchant_id)
        
        # Get count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar()
        
        # Get data
        result = await session.execute(query)
        rows = result.all()
        
        discrepancies = []
        for row in rows:
            discrepancies.append({
                "transaction_id": row.transaction_id,
                "merchant_id": row.merchant_id,
                "merchant_name": row.merchant_name,
                "amount": float(row.amount),
                "payment_status": row.payment_status,
                "settlement_status": row.settlement_status,
                "discrepancy_type": row.discrepancy_type,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        return discrepancies, total
