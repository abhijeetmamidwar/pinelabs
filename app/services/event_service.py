from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.dialects.postgresql import insert
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.event import Event
from app.schemas.event import EventCreate, BulkEventResponse
from datetime import datetime
from typing import List


class EventService:
    
    @staticmethod
    async def ingest_event(session: AsyncSession, event_data: EventCreate) -> dict:
        """
        Ingest a single event with idempotency.
        Returns dict with status information.
        """
        # Check if event already exists (idempotency)
        result = await session.execute(
            select(Event).where(Event.id == event_data.event_id)
        )
        existing_event = result.scalar_one_or_none()
        
        if existing_event:
            return {
                "status": "duplicate",
                "event_id": event_data.event_id,
                "message": "Event already processed"
            }
        
        # Upsert merchant
        merchant_stmt = insert(Merchant).values(
            id=event_data.merchant_id,
            name=event_data.merchant_name
        ).on_conflict_do_update(
            index_elements=['id'],
            set_={'name': event_data.merchant_name}
        )
        await session.execute(merchant_stmt)
        
        # Get or create transaction
        result = await session.execute(
            select(Transaction).where(Transaction.id == event_data.transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            transaction = Transaction(
                id=event_data.transaction_id,
                merchant_id=event_data.merchant_id,
                amount=event_data.amount,
                currency=event_data.currency,
                payment_status="initiated",
                settlement_status="pending",
                created_at=event_data.timestamp
            )
            session.add(transaction)
        
        # Update transaction status based on event type
        await EventService._update_transaction_status(
            session, transaction, event_data.event_type, event_data.timestamp
        )
        
        # Insert event
        event = Event(
            id=event_data.event_id,
            transaction_id=event_data.transaction_id,
            merchant_id=event_data.merchant_id,
            event_type=event_data.event_type,
            amount=event_data.amount,
            currency=event_data.currency,
            timestamp=event_data.timestamp
        )
        session.add(event)
        
        await session.flush()
        
        return {
            "status": "processed",
            "event_id": event_data.event_id,
            "message": "Event processed successfully"
        }
    
    @staticmethod
    async def ingest_events_bulk(
        session: AsyncSession, 
        events: List[EventCreate],
        batch_size: int = 100
    ) -> BulkEventResponse:
        """
        Ingest multiple events in batches.
        """
        total_events = len(events)
        processed = 0
        duplicates = 0
        errors = 0
        
        for i in range(0, total_events, batch_size):
            batch = events[i:i + batch_size]
            
            for event_data in batch:
                try:
                    result = await EventService.ingest_event(session, event_data)
                    if result["status"] == "processed":
                        processed += 1
                    elif result["status"] == "duplicate":
                        duplicates += 1
                except Exception as e:
                    errors += 1
                    print(f"Error processing event {event_data.event_id}: {e}")
            
            await session.commit()
        
        return BulkEventResponse(
            total_events=total_events,
            processed=processed,
            duplicates=duplicates,
            errors=errors
        )
    
    @staticmethod
    async def _update_transaction_status(
        session: AsyncSession,
        transaction: Transaction,
        event_type: str,
        timestamp: datetime
    ):
        """Update transaction status based on event type."""
        if event_type == "payment_initiated":
            transaction.payment_status = "initiated"
        elif event_type == "payment_processed":
            transaction.payment_status = "processed"
        elif event_type == "payment_failed":
            transaction.payment_status = "failed"
        elif event_type == "settled":
            transaction.settlement_status = "settled"
        
        # Update created_at if this is the first event
        if transaction.created_at is None or timestamp < transaction.created_at:
            transaction.created_at = timestamp
