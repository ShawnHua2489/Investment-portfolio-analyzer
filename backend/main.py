from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import uuid

from api.routes import portfolio
from database import get_db, engine
from services.data_cache import DataCache

app = FastAPI(
    title="Investment Portfolio Analyzer API",
    description="API for analyzing investment portfolios and managing assets",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolios"])

# Initialize data cache
data_cache = DataCache()

@app.get("/")
async def root():
    return {"message": "Welcome to the Investment Portfolio Analyzer API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Get statistics about the data cache."""
    return data_cache.get_cache_stats()

@app.delete("/api/v1/cache")
async def clear_cache(symbol: Optional[str] = None):
    """Clear the data cache for a specific symbol or all symbols."""
    data_cache.clear_cache(symbol)
    return {"message": f"Cache cleared for {symbol if symbol else 'all symbols'}"}

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    from database import Base
    Base.metadata.create_all(bind=engine) 