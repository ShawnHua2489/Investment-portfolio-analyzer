from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Asset(BaseModel):
    symbol: str
    name: str
    quantity: float
    purchase_price: float
    purchase_date: datetime
    asset_type: str  # e.g., "stock", "bond", "etf"
    current_price: Optional[float] = None
    total_value: Optional[float] = None

class Transaction(BaseModel):
    id: str
    asset_symbol: str
    transaction_type: str  # "buy" or "sell"
    quantity: float
    price: float
    date: datetime

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None

class Portfolio(PortfolioCreate):
    id: str
    assets: List[Asset] = []
    transactions: List[Transaction] = []
    created_at: datetime
    updated_at: datetime
    total_value: Optional[float] = 0
    asset_count: Optional[int] = 0

    class Config:
        from_attributes = True 