# Payment Event Ingestion Service

A lightweight backend service for payment lifecycle event ingestion, transaction management, and reconciliation reporting.

## Overview

This service ingests payment events from multiple systems, maintains transaction and reconciliation state, and exposes APIs for operations teams to identify discrepancies between payment and settlement status.

## Architecture

### Tech Stack
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy (async with asyncpg)
- **Migrations**: Alembic
- **API Documentation**: Auto-generated OpenAPI/Swagger

### System Components
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   FastAPI App   │
│                 │
│  ┌───────────┐  │
│  │   Events  │  │
│  │   API     │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │Transaction│  │
│  │   API     │  │
│  └───────────┘  │
│  ┌───────────┐  │
│  │Reconcil.  │  │
│  │   API     │  │
│  └───────────┘  │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│   PostgreSQL    │
│                 │
│  ┌───────────┐  │
│  │ Merchants │  │
│  ├───────────┤  │
│  │Transac.   │  │
│  ├───────────┤  │
│  │  Events   │  │
│  └───────────┘  │
└─────────────────┘
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 15
- Docker (optional, for containerized setup)

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd PineLabs
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
# Note: Docker Compose uses port 5435 to avoid conflicts
```

5. **Set up PostgreSQL**
```bash
# Option 1: Using Docker (recommended - uses port 5435)
docker-compose up -d db

# Option 2: Using local PostgreSQL
# Create database and user, then update .env with your port
# (default PostgreSQL uses port 5432)
```

6. **Run migrations**
```bash
source venv/bin/activate
alembic upgrade head
```

7. **Start the application**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

8. **Load sample data**
```bash
python app/utils/data_loader.py http://localhost:8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## API Documentation

### Endpoints

#### 1. POST /events
Ingest a single payment lifecycle event.

**Request Body:**
```json
{
  "event_id": "uuid",
  "event_type": "payment_initiated|payment_processed|payment_failed|settled",
  "transaction_id": "uuid",
  "merchant_id": "string",
  "merchant_name": "string",
  "amount": 15248.29,
  "currency": "INR",
  "timestamp": "2026-01-08T12:11:58.085567+00:00"
}
```

**Response:**
- `201 Created`: Event processed successfully
- `200 OK`: Event already exists (idempotent)

**Idempotency**: Submitting the same event twice will not corrupt transaction state.

#### 2. POST /events/bulk
Ingest multiple payment lifecycle events in bulk.

**Request Body:**
```json
{
  "events": [
    { ...event object... },
    ...
  ]
}
```

**Response:**
```json
{
  "total_events": 10000,
  "processed": 9500,
  "duplicates": 500,
  "errors": 0
}
```

#### 3. GET /transactions
List transactions with filtering, pagination, and sorting.

**Query Parameters:**
- `merchant_id` (optional): Filter by merchant
- `status` (optional): Filter by payment_status
- `settlement_status` (optional): Filter by settlement_status
- `start_date` (optional): Filter by date range (YYYY-MM-DD)
- `end_date` (optional): Filter by date range (YYYY-MM-DD)
- `page` (default: 1): Page number
- `limit` (default: 50, max: 100): Items per page
- `sort_by` (default: created_at): Field to sort by
- `sort_order` (default: desc): asc or desc

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "merchant_id": "string",
      "merchant_name": "string",
      "amount": 15248.29,
      "currency": "INR",
      "payment_status": "processed",
      "settlement_status": "settled",
      "created_at": "2026-01-08T12:11:58.085567+00:00",
      "updated_at": "2026-01-08T14:00:00.000000+00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1000,
    "total_pages": 20
  }
}
```

#### 4. GET /transactions/{transaction_id}
Get transaction details with event history.

**Response:**
```json
{
  "id": "uuid",
  "merchant_id": "string",
  "merchant_name": "string",
  "amount": 15248.29,
  "currency": "INR",
  "payment_status": "processed",
  "settlement_status": "settled",
  "created_at": "2026-01-08T12:11:58.085567+00:00",
  "updated_at": "2026-01-08T14:00:00.000000+00:00",
  "event_history": [
    {
      "event_id": "uuid",
      "event_type": "payment_initiated",
      "timestamp": "2026-01-08T12:11:58.085567+00:00"
    }
  ]
}
```

#### 5. GET /reconciliation/summary
Get reconciliation summary grouped by specified dimension.

**Query Parameters:**
- `group_by` (required): merchant, date, status, or merchant_date
- `merchant_id` (optional): Filter by merchant
- `start_date` (optional): Filter by date range
- `end_date` (optional): Filter by date range

**Response (group_by=merchant):**
```json
{
  "summary": [
    {
      "merchant_id": "merchant_1",
      "merchant_name": "QuickMart",
      "total_transactions": 500,
      "total_amount": 5000000.00,
      "payment_processed_count": 450,
      "payment_failed_count": 50,
      "settled_count": 440,
      "pending_settlement_count": 10
    }
  ]
}
```

#### 6. GET /reconciliation/discrepancies
Get transactions with payment/settlement discrepancies.

**Query Parameters:**
- `merchant_id` (optional): Filter by merchant

**Response:**
```json
{
  "discrepancies": [
    {
      "transaction_id": "uuid",
      "merchant_id": "string",
      "merchant_name": "string",
      "amount": 15248.29,
      "payment_status": "processed",
      "settlement_status": "pending",
      "discrepancy_type": "payment_processed_but_not_settled",
      "created_at": "2026-01-08T12:11:58.085567+00:00"
    }
  ],
  "total": 50
}
```

**Discrepancy Types:**
- `payment_processed_but_not_settled`: Payment marked processed but never settled
- `settlement_for_failed_payment`: Settlement recorded for a failed payment
- `stale_initiated_transaction`: Payment initiated but not updated for > 24 hours

## Database Schema

### Merchants Table
```sql
CREATE TABLE merchants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id VARCHAR(50) PRIMARY KEY,
    merchant_id VARCHAR(50) NOT NULL REFERENCES merchants(id),
    amount DECIMAL(19, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_status VARCHAR(50) NOT NULL DEFAULT 'initiated',
    settlement_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Events Table
```sql
CREATE TABLE events (
    id VARCHAR(50) PRIMARY KEY,
    transaction_id VARCHAR(50) NOT NULL REFERENCES transactions(id),
    merchant_id VARCHAR(50) NOT NULL REFERENCES merchants(id),
    event_type VARCHAR(50) NOT NULL,
    amount DECIMAL(19, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes
- All foreign keys indexed
- Composite indexes for common filter combinations
- Unique constraint on events.id for idempotency

## Testing

### Running Tests
```bash
pytest tests/
```

### Manual Testing with Postman
Import the provided Postman collection to test all endpoints.

### Test Coverage
- Event ingestion with idempotency
- Transaction filtering and pagination
- Reconciliation summary aggregations
- Discrepancy detection
- Error handling and validation

## Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Railway Deployment
1. Create Railway account
2. Create PostgreSQL database
3. Connect GitHub repository
4. Set environment variables
5. Deploy

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: production
- `LOG_LEVEL`: INFO

### Deployment URL
[To be added after deployment]

## Assumptions and Tradeoffs

### Assumptions
1. Event timestamps are in UTC
2. Amount is in decimal (e.g., 15248.29 for INR)
3. Merchant information can be updated from events
4. Transaction IDs are unique across all merchants
5. Events arrive in order (no out-of-order event handling)

### Tradeoffs

**Simplified State Machine**
- Decision: Not handling state reversals (e.g., processed → failed)
- Justification: Assignment scope; production system would need a proper state machine
- Future: Implement state transition rules with validation

**No Authentication**
- Decision: APIs are public without authentication
- Justification: Assignment scope; production would use API keys
- Future: Add API key authentication or OAuth

**No Rate Limiting**
- Decision: No protection against API abuse
- Justification: Assignment scope; production would add rate limiting
- Future: Implement rate limiting with Redis

**Synchronous Processing**
- Decision: No message queue for event processing
- Justification: Assignment scope with ~10K events
- Future: Add Celery + RabbitMQ for async processing

**Single Database**
- Decision: No sharding or read replicas
- Justification: Sample data size is manageable
- Future: Add read replicas for query performance

**Idempotency via Unique Constraint**
- Decision: Database-level unique constraint on event_id
- Justification: Simple and reliable
- Tradeoff: Requires database round-trip for duplicate check
- Future: Consider Redis-based deduplication cache

## Performance Considerations

### Database Optimization
- Strategic indexes on frequently queried columns
- Composite indexes for common filter combinations
- All aggregations performed in SQL (not Python loops)

### Query Optimization
- Pagination at database level (OFFSET/LIMIT)
- Efficient JOIN queries to avoid N+1 problems
- Batch processing for bulk operations

### Connection Pooling
- SQLAlchemy connection pool with appropriate size
- Async database operations for better concurrency

## Future Improvements

1. **Authentication**: Add API key or OAuth authentication
2. **Rate Limiting**: Implement rate limiting per merchant
3. **Async Processing**: Add message queue for event processing
4. **Caching**: Add Redis cache for frequently accessed data
5. **Monitoring**: Add Prometheus metrics and logging
6. **State Machine**: Implement proper state transition validation
7. **Webhooks**: Add webhook notifications for discrepancies
8. **Data Retention**: Implement archival policy for old events
9. **Read Replicas**: Add read replicas for query performance
10. **API Versioning**: Implement versioned API endpoints

## Sample Data

The provided `sample_events.json` contains:
- ~10,355 events across 5 merchants
- Event types: payment_initiated (3,864), payment_processed (3,004), payment_failed (665), settled (2,822)
- Date range: 2026-01-08 to 2026-01-10
- Merchants: QuickMart, FreshBasket, UrbanEats, TechBazaar, StyleHub

Load sample data using:
```bash
python app/utils/data_loader.py http://localhost:8000
```

## License

This project is part of a hiring assignment for PineLabs.
