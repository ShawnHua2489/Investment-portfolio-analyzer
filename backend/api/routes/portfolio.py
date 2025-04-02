from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from sqlalchemy.orm import Session
from api.models.portfolio import Portfolio, PortfolioCreate, Asset, Transaction
from services.portfolio_analysis import PortfolioAnalyzer
from services.risk_management import RiskManagement
from datetime import datetime
import uuid
from database import get_db, PortfolioDB, AssetDB, TransactionDB
import yfinance as yf
import requests

router = APIRouter()

# Create a global portfolio analyzer instance
portfolio_analyzer = None

def get_portfolio_analyzer():
    global portfolio_analyzer
    if portfolio_analyzer is None:
        portfolio_analyzer = PortfolioAnalyzer(None)
    return portfolio_analyzer

def convert_db_to_model(db_portfolio: PortfolioDB) -> Portfolio:
    """Convert database model to API model."""
    return Portfolio(
        id=db_portfolio.id,
        name=db_portfolio.name,
        description=db_portfolio.description,
        assets=[Asset(
            symbol=asset.symbol,
            name=asset.name,
            quantity=asset.quantity,
            purchase_price=asset.purchase_price,
            purchase_date=asset.purchase_date,
            asset_type=asset.asset_type
        ) for asset in db_portfolio.assets],
        transactions=[Transaction(
            id=trans.id,
            asset_symbol=trans.asset_symbol,
            transaction_type=trans.transaction_type,
            quantity=trans.quantity,
            price=trans.price,
            date=trans.date
        ) for trans in db_portfolio.transactions],
        created_at=db_portfolio.created_at,
        updated_at=db_portfolio.updated_at
    )

@router.post("/portfolios/", response_model=Portfolio)
async def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    portfolio_id = str(uuid.uuid4())
    db_portfolio = PortfolioDB(
        id=portfolio_id,
        name=portfolio.name,
        description=portfolio.description
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return convert_db_to_model(db_portfolio)

@router.get("/portfolios/", response_model=List[Portfolio])
async def get_portfolios(db: Session = Depends(get_db)):
    db_portfolios = db.query(PortfolioDB).all()
    return [convert_db_to_model(p) for p in db_portfolios]

@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return convert_db_to_model(db_portfolio)

@router.get("/portfolios/{portfolio_id}/analysis")
async def analyze_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    analyzer = PortfolioAnalyzer(portfolio)
    return analyzer.calculate_portfolio_metrics()

@router.post("/portfolios/{portfolio_id}/assets", response_model=Portfolio)
async def add_asset(portfolio_id: str, asset: Asset, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db_asset = AssetDB(
        id=str(uuid.uuid4()),
        portfolio_id=portfolio_id,
        symbol=asset.symbol,
        name=asset.name,
        quantity=asset.quantity,
        purchase_price=asset.purchase_price,
        purchase_date=asset.purchase_date,
        asset_type=asset.asset_type
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_portfolio)
    return convert_db_to_model(db_portfolio)

# Risk Management Endpoints
@router.get("/portfolios/{portfolio_id}/risk/var")
async def get_value_at_risk(portfolio_id: str, confidence_level: float = 0.95, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    risk_manager = RiskManagement(portfolio)
    return risk_manager.calculate_var(confidence_level)

@router.get("/portfolios/{portfolio_id}/risk/correlation")
async def get_correlation_matrix(portfolio_id: str, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    risk_manager = RiskManagement(portfolio)
    return risk_manager.calculate_correlation_matrix()

@router.get("/portfolios/{portfolio_id}/risk/efficient-frontier")
async def get_efficient_frontier(portfolio_id: str, num_portfolios: int = 100, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    risk_manager = RiskManagement(portfolio)
    return risk_manager.calculate_efficient_frontier(num_portfolios)

@router.post("/portfolios/{portfolio_id}/risk/stress")
async def stress_test_portfolio(
    portfolio_id: str, 
    scenarios: Dict[str, List[Dict[str, float]]], 
    db: Session = Depends(get_db)
):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    risk_manager = RiskManagement(portfolio)
    return risk_manager.stress_test(scenarios["scenarios"])

@router.delete("/portfolios/cache")
async def clear_portfolio_cache(symbol: str = None):
    """Clear the portfolio data cache for a specific symbol or all symbols."""
    analyzer = get_portfolio_analyzer()
    analyzer.clear_cache(symbol)
    return {"message": f"Cache cleared for {symbol if symbol else 'all symbols'}"}

@router.get("/test/yahoo/{symbol}")
async def test_yahoo_data(symbol: str):
    """Test endpoint to verify Yahoo Finance data fetching."""
    try:
        # Try multiple methods to get data
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "methods": {}
        }

        # Method 1: Using yfinance Ticker
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            current_price = ticker.history(period="1d", interval="1m").iloc[-1]['Close']
            results["methods"]["yfinance_ticker"] = {
                "success": True,
                "current_price": float(current_price),
                "company_name": info.get('longName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A')
            }
        except Exception as e:
            results["methods"]["yfinance_ticker"] = {
                "success": False,
                "error": str(e)
            }

        # Method 2: Using yfinance download
        try:
            data = yf.download(symbol, period="1d", interval="1m", progress=False)
            if not data.empty:
                results["methods"]["yfinance_download"] = {
                    "success": True,
                    "current_price": float(data['Close'].iloc[-1]),
                    "volume": int(data['Volume'].iloc[-1]),
                    "high": float(data['High'].iloc[-1]),
                    "low": float(data['Low'].iloc[-1])
                }
            else:
                results["methods"]["yfinance_download"] = {
                    "success": False,
                    "error": "No data returned"
                }
        except Exception as e:
            results["methods"]["yfinance_download"] = {
                "success": False,
                "error": str(e)
            }

        # Method 3: Direct API call
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "range": "1d",
                "interval": "1m",
                "includePrePost": False
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                    result = data['chart']['result'][0]
                    quotes = result['indicators']['quote'][0]
                    results["methods"]["direct_api"] = {
                        "success": True,
                        "current_price": float(quotes['close'][-1]),
                        "volume": int(quotes['volume'][-1]),
                        "high": float(quotes['high'][-1]),
                        "low": float(quotes['low'][-1])
                    }
                else:
                    results["methods"]["direct_api"] = {
                        "success": False,
                        "error": "Invalid response format"
                    }
            else:
                results["methods"]["direct_api"] = {
                    "success": False,
                    "error": f"API request failed with status {response.status_code}"
                }
        except Exception as e:
            results["methods"]["direct_api"] = {
                "success": False,
                "error": str(e)
            }

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing Yahoo Finance data: {str(e)}")

@router.get("/learn/metrics/{metric}")
async def learn_about_metric(metric: str):
    """Educational endpoint to learn about financial metrics."""
    metrics = {
        "beta": {
            "name": "Beta",
            "description": "A measure of a stock's volatility compared to the overall market.",
            "interpretation": {
                "beta > 1": "Stock is more volatile than the market",
                "beta = 1": "Stock moves in line with the market",
                "beta < 1": "Stock is less volatile than the market"
            },
            "example": "A stock with beta 1.5 means it's 50% more volatile than the market",
            "formula": "Beta = Covariance(Stock Returns, Market Returns) / Variance(Market Returns)"
        },
        "sharpe_ratio": {
            "name": "Sharpe Ratio",
            "description": "A measure of risk-adjusted returns, indicating how much excess return you get for the extra volatility.",
            "interpretation": {
                "ratio > 1": "Good risk-adjusted returns",
                "ratio > 2": "Very good risk-adjusted returns",
                "ratio > 3": "Excellent risk-adjusted returns"
            },
            "example": "A Sharpe ratio of 1.5 means the investment returns 1.5 units of return per unit of risk",
            "formula": "Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation"
        },
        "var": {
            "name": "Value at Risk (VaR)",
            "description": "A measure of the potential loss in value of a portfolio over a defined period for a given confidence interval.",
            "interpretation": {
                "high_var": "Higher potential losses",
                "low_var": "Lower potential losses"
            },
            "example": "A 95% VaR of $10,000 means there's a 5% chance of losing more than $10,000",
            "formula": "VaR = Portfolio Value × Z-Score × Portfolio Standard Deviation"
        },
        "correlation": {
            "name": "Correlation",
            "description": "A measure of how two assets move in relation to each other.",
            "interpretation": {
                "correlation = 1": "Perfect positive correlation",
                "correlation = 0": "No correlation",
                "correlation = -1": "Perfect negative correlation"
            },
            "example": "A correlation of 0.7 between stocks A and B means they tend to move in the same direction",
            "formula": "Correlation = Covariance(A,B) / (Standard Deviation(A) × Standard Deviation(B))"
        },
        "diversification": {
            "name": "Diversification",
            "description": "A risk management strategy that mixes a wide variety of investments within a portfolio.",
            "benefits": [
                "Reduces portfolio volatility",
                "Minimizes the impact of any single investment",
                "Improves risk-adjusted returns"
            ],
            "example": "A diversified portfolio might include stocks, bonds, real estate, and commodities",
            "tips": [
                "Spread investments across different asset classes",
                "Consider geographic diversification",
                "Include both growth and value investments"
            ]
        }
    }
    
    if metric.lower() not in metrics:
        raise HTTPException(status_code=404, detail=f"Metric '{metric}' not found. Available metrics: {', '.join(metrics.keys())}")
    
    return metrics[metric.lower()]

@router.get("/learn/portfolio-analysis/{portfolio_id}")
async def learn_portfolio_analysis(portfolio_id: str, db: Session = Depends(get_db)):
    """Educational endpoint to understand your portfolio's analysis."""
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    analyzer = PortfolioAnalyzer(portfolio)
    metrics = analyzer.calculate_portfolio_metrics()
    
    # Add educational content to the analysis
    educational_content = {
        "portfolio_summary": {
            "total_value": metrics["total_value"],
            "explanation": "This represents the current market value of all your investments combined.",
            "tips": [
                "Regularly monitor your total portfolio value",
                "Consider rebalancing if allocations drift significantly",
                "Track performance against your investment goals"
            ]
        },
        "asset_allocation": {
            "current_allocation": metrics["asset_allocation"],
            "explanation": "This shows how your investments are distributed across different asset types.",
            "recommendations": {
                "stocks": "Consider 40-60% for growth",
                "bonds": "Consider 20-40% for stability",
                "etfs": "Consider 10-20% for diversification"
            },
            "tips": [
                "Rebalance when allocations deviate by more than 5%",
                "Consider your age and risk tolerance",
                "Diversify within each asset class"
            ]
        },
        "risk_metrics": {
            "beta": "Measures portfolio volatility compared to the market",
            "sharpe_ratio": "Indicates risk-adjusted returns",
            "var": "Shows potential maximum loss",
            "tips": [
                "Higher returns usually come with higher risk",
                "Diversification can help reduce risk",
                "Regular rebalancing helps maintain risk levels"
            ]
        }
    }
    
    return {
        "metrics": metrics,
        "educational_content": educational_content
    }

@router.get("/learn/commodities")
async def learn_about_commodities():
    """Educational endpoint to learn about commodities investing."""
    return {
        "commodities_overview": {
            "description": "Commodities are basic goods used in commerce that are interchangeable with other goods of the same type.",
            "categories": {
                "precious_metals": {
                    "examples": ["Gold (GLD)", "Silver (SLV)", "Platinum (PPLT)"],
                    "benefits": [
                        "Hedge against inflation",
                        "Safe haven during market turmoil",
                        "Portfolio diversification"
                    ],
                    "typical_allocation": "5-10% of portfolio"
                },
                "energy": {
                    "examples": ["Oil (USO)", "Natural Gas (UNG)", "Gasoline (UGA)"],
                    "benefits": [
                        "Inflation protection",
                        "Geopolitical risk hedge",
                        "Economic growth exposure"
                    ],
                    "typical_allocation": "5-10% of portfolio"
                },
                "agricultural": {
                    "examples": ["Corn (CORN)", "Wheat (WEAT)", "Soybeans (SOYB)"],
                    "benefits": [
                        "Weather risk hedge",
                        "Population growth exposure",
                        "Diversification from financial assets"
                    ],
                    "typical_allocation": "3-7% of portfolio"
                },
                "industrial_metals": {
                    "examples": ["Copper (CPER)", "Aluminum (JJN)", "Zinc (ZINC)"],
                    "benefits": [
                        "Industrial growth exposure",
                        "Infrastructure development play",
                        "Economic cycle hedge"
                    ],
                    "typical_allocation": "3-7% of portfolio"
                }
            },
            "investment_methods": {
                "etfs": {
                    "description": "Exchange-traded funds that track commodity prices",
                    "advantages": [
                        "Easy to trade",
                        "Liquid markets",
                        "Low cost"
                    ]
                },
                "futures": {
                    "description": "Contracts to buy or sell commodities at a future date",
                    "advantages": [
                        "Direct exposure",
                        "Leverage potential",
                        "Price discovery"
                    ]
                },
                "stocks": {
                    "description": "Shares of companies involved in commodity production",
                    "advantages": [
                        "Dividend potential",
                        "Management expertise",
                        "Operational leverage"
                    ]
                }
            },
            "risk_considerations": [
                "Commodity prices can be highly volatile",
                "Storage and transportation costs",
                "Geopolitical risks",
                "Weather impacts on agricultural commodities",
                "Currency effects on international commodities"
            ],
            "portfolio_integration": {
                "recommendations": [
                    "Start with a small allocation (5-10%)",
                    "Diversify across different commodity types",
                    "Consider using ETFs for easier access",
                    "Rebalance regularly to maintain target allocation",
                    "Monitor correlation with other portfolio assets"
                ],
                "monitoring": [
                    "Track commodity price trends",
                    "Watch for contango/backwardation in futures",
                    "Monitor global supply and demand",
                    "Consider seasonal factors",
                    "Watch currency impacts"
                ]
            }
        }
    }

@router.get("/learn/commodities/{symbol}")
async def learn_about_specific_commodity(symbol: str):
    """Learn about a specific commodity ETF."""
    commodity_info = {
        "GLD": {
            "name": "SPDR Gold Trust",
            "description": "The largest physically-backed gold ETF in the world",
            "key_facts": {
                "inception_date": "2004-11-18",
                "expense_ratio": "0.40%",
                "underlying_asset": "Physical Gold",
                "storage_location": "London, UK"
            },
            "investment_thesis": [
                "Hedge against inflation",
                "Safe haven during market turmoil",
                "Portfolio diversification",
                "Currency hedge"
            ],
            "risks": [
                "Gold price volatility",
                "Storage and insurance costs",
                "Counterparty risk with custodians",
                "Currency exchange rate risk"
            ],
            "historical_performance": {
                "1_year": "Typically tracks gold spot price",
                "5_year": "Long-term inflation hedge",
                "10_year": "Store of value preservation"
            }
        },
        "SLV": {
            "name": "iShares Silver Trust",
            "description": "The largest physically-backed silver ETF",
            "key_facts": {
                "inception_date": "2006-04-28",
                "expense_ratio": "0.50%",
                "underlying_asset": "Physical Silver",
                "storage_location": "London, UK"
            },
            "investment_thesis": [
                "Industrial and precious metal exposure",
                "Inflation hedge",
                "Portfolio diversification",
                "Lower price point than gold"
            ],
            "risks": [
                "Higher volatility than gold",
                "Industrial demand sensitivity",
                "Storage costs",
                "Market manipulation concerns"
            ],
            "historical_performance": {
                "1_year": "Typically tracks silver spot price",
                "5_year": "Industrial and monetary demand play",
                "10_year": "Long-term value preservation"
            }
        },
        "USO": {
            "name": "United States Oil Fund",
            "description": "ETF that tracks the price of crude oil",
            "key_facts": {
                "inception_date": "2006-04-10",
                "expense_ratio": "0.45%",
                "underlying_asset": "Crude Oil Futures",
                "benchmark": "Near-month NYMEX crude oil futures"
            },
            "investment_thesis": [
                "Direct oil price exposure",
                "Inflation hedge",
                "Geopolitical risk hedge",
                "Economic growth play"
            ],
            "risks": [
                "Contango/backwardation effects",
                "High volatility",
                "Geopolitical risks",
                "Storage and transportation costs"
            ],
            "historical_performance": {
                "1_year": "Tracks oil price movements",
                "5_year": "Energy sector exposure",
                "10_year": "Long-term energy price trends"
            }
        }
    }
    
    if symbol not in commodity_info:
        raise HTTPException(status_code=404, detail=f"Commodity ETF '{symbol}' not found. Available ETFs: {', '.join(commodity_info.keys())}")
    
    return commodity_info[symbol] 