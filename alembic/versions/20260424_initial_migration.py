"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create merchants table
    op.create_table(
        'merchants',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('idx_merchants_name', 'merchants', ['name'])
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('merchant_id', sa.String(50), sa.ForeignKey('merchants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount', sa.Numeric(19, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('payment_status', sa.String(50), nullable=False, server_default='initiated'),
        sa.Column('settlement_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now())
    )
    op.create_index('idx_transactions_merchant', 'transactions', ['merchant_id'])
    op.create_index('idx_transactions_payment_status', 'transactions', ['payment_status'])
    op.create_index('idx_transactions_settlement_status', 'transactions', ['settlement_status'])
    op.create_index('idx_transactions_created_at', 'transactions', ['created_at'])
    op.create_index('idx_transactions_merchant_status', 'transactions', ['merchant_id', 'payment_status'])
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('transaction_id', sa.String(50), sa.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('merchant_id', sa.String(50), sa.ForeignKey('merchants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(19, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.create_index('idx_events_transaction', 'events', ['transaction_id'])
    op.create_index('idx_events_merchant', 'events', ['merchant_id'])
    op.create_index('idx_events_type', 'events', ['event_type'])
    op.create_index('idx_events_timestamp', 'events', ['timestamp'])


def downgrade() -> None:
    op.drop_index('idx_events_timestamp', 'events')
    op.drop_index('idx_events_type', 'events')
    op.drop_index('idx_events_merchant', 'events')
    op.drop_index('idx_events_transaction', 'events')
    op.drop_table('events')
    
    op.drop_index('idx_transactions_merchant_status', 'transactions')
    op.drop_index('idx_transactions_created_at', 'transactions')
    op.drop_index('idx_transactions_settlement_status', 'transactions')
    op.drop_index('idx_transactions_payment_status', 'transactions')
    op.drop_index('idx_transactions_merchant', 'transactions')
    op.drop_table('transactions')
    
    op.drop_index('idx_merchants_name', 'merchants')
    op.drop_table('merchants')
