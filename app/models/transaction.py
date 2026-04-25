from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String(50), primary_key=True)
    merchant_id = Column(String(50), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(19, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    payment_status = Column(String(50), nullable=False, default="initiated")
    settlement_status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    merchant = relationship("Merchant", backref="transactions")
