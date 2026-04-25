from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.event import EventCreate, EventResponse, BulkEventRequest, BulkEventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    event_data: EventCreate,
    session: AsyncSession = Depends(get_db)
):
    """
    Ingest a single payment lifecycle event.
    
    This endpoint is idempotent - submitting the same event twice will not
    corrupt transaction state.
    """
    result = await EventService.ingest_event(session, event_data)
    await session.commit()
    
    if result["status"] == "duplicate":
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail=result
        )
    
    return result


@router.post("/bulk", response_model=BulkEventResponse)
async def ingest_events_bulk(
    bulk_request: BulkEventRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Ingest multiple payment lifecycle events in bulk.
    
    Processes events in batches for better performance.
    Returns summary of processing results.
    """
    result = await EventService.ingest_events_bulk(
        session, 
        bulk_request.events
    )
    
    return result
