from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Event(Base):
    __tablename__ = "events"
    
    id = Column(String(50), primary_key=True)
    transaction_id = Column(String(50), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    merchant_id = Column(String(50), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    amount = Column(Numeric(19, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    transaction = relationship("Transaction", backref="events")
    merchant = relationship("Merchant", backref="events")
    
    __table_args__ = (
        Index("idx_events_transaction", "transaction_id"),
        Index("idx_events_merchant", "merchant_id"),
        Index("idx_events_type", "event_type"),
        Index("idx_events_timestamp", "timestamp"),
    )
