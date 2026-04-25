from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import events, transactions, reconciliation

settings = get_settings()

app = FastAPI(
    title="Payment Event Ingestion Service",
    description="Backend service for payment lifecycle event ingestion and reconciliation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)


@app.get("/")
async def root():
    return {
        "service": "Payment Event Ingestion Service",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
