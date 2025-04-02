from sqlalchemy import create_engine, Column, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PortfolioDB(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    assets = relationship("AssetDB", back_populates="portfolio")
    transactions = relationship("TransactionDB", back_populates="portfolio")

class AssetDB(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id"))
    symbol = Column(String)
    name = Column(String)
    quantity = Column(Float)
    purchase_price = Column(Float)
    purchase_date = Column(DateTime)
    asset_type = Column(String)

    portfolio = relationship("PortfolioDB", back_populates="assets")

class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id"))
    asset_symbol = Column(String)
    transaction_type = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    date = Column(DateTime)

    portfolio = relationship("PortfolioDB", back_populates="transactions")

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 