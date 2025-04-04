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
    portfolios = []
    
    for db_portfolio in db_portfolios:
        portfolio = convert_db_to_model(db_portfolio)
        
        # Calculate total value
        total_value = sum(asset.quantity * asset.purchase_price for asset in portfolio.assets)
        
        # Add total value and asset count to the portfolio
        portfolio_dict = portfolio.dict()
        portfolio_dict["total_value"] = total_value
        portfolio_dict["asset_count"] = len(portfolio.assets)
        
        portfolios.append(portfolio_dict)
    
    return portfolios

@router.get("/portfolios/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get summary of all portfolios."""
    portfolios = db.query(PortfolioDB).all()
    
    if not portfolios:
        return {
            "total_value": 0,
            "asset_allocation": {},
            "risk_metrics": {
                "beta": 0,
                "sharpe_ratio": 0,
                "volatility": 0
            }
        }
    
    total_value = 0
    asset_allocation = {}
    all_assets = []
    
    # Collect all assets and calculate total value
    for portfolio in portfolios:
        for asset in portfolio.assets:
            total_value += asset.quantity * asset.purchase_price
            asset_type = asset.asset_type
            if asset_type not in asset_allocation:
                asset_allocation[asset_type] = 0
            asset_allocation[asset_type] += asset.quantity * asset.purchase_price
            all_assets.append(asset)
    
    # Normalize asset allocation to percentages
    if total_value > 0:
        asset_allocation = {k: (v / total_value) * 100 for k, v in asset_allocation.items()}
    
    # Calculate risk metrics
    risk_metrics = {"beta": 0, "sharpe_ratio": 0, "volatility": 0}
    
    if all_assets:
        try:
            # Get market data (using SPY as market proxy)
            market = yf.Ticker("SPY")
            market_hist = market.history(period="1y")["Close"]
            market_returns = market_hist.pct_change().dropna()
            
            # Calculate portfolio returns
            portfolio_returns = []
            portfolio_weights = []
            
            for asset in all_assets:
                try:
                    ticker = yf.Ticker(asset.symbol)
                    hist = ticker.history(period="1y")["Close"]
                    returns = hist.pct_change().dropna()
                    portfolio_returns.append(returns)
                    portfolio_weights.append((asset.quantity * asset.purchase_price) / total_value)
                except Exception as e:
                    print(f"Error fetching data for {asset.symbol}: {str(e)}")
            
            if portfolio_returns:
                # Calculate portfolio beta
                portfolio_return_series = sum(returns * weight for returns, weight in zip(portfolio_returns, portfolio_weights))
                covariance = portfolio_return_series.cov(market_returns)
                market_variance = market_returns.var()
                beta = covariance / market_variance if market_variance != 0 else 1
                
                # Calculate volatility (annualized)
                volatility = portfolio_return_series.std() * (252 ** 0.5)  # 252 trading days
                
                # Calculate Sharpe ratio (assuming risk-free rate of 2%)
                risk_free_rate = 0.02
                excess_returns = portfolio_return_series.mean() * 252 - risk_free_rate
                sharpe_ratio = excess_returns / volatility if volatility != 0 else 0
                
                risk_metrics = {
                    "beta": round(beta, 2),
                    "sharpe_ratio": round(sharpe_ratio, 2),
                    "volatility": round(volatility * 100, 2)  # Convert to percentage
                }
        except Exception as e:
            print(f"Error calculating risk metrics: {str(e)}")
    
    return {
        "total_value": total_value,
        "asset_allocation": asset_allocation,
        "risk_metrics": risk_metrics
    }

@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio = convert_db_to_model(db_portfolio)
    
    # Fetch current prices for all assets
    for asset in portfolio.assets:
        try:
            ticker = yf.Ticker(asset.symbol)
            current_price = ticker.history(period="1d")['Close'].iloc[-1]
            asset.current_price = float(current_price)
            asset.total_value = asset.quantity * current_price
        except Exception as e:
            print(f"Error fetching price for {asset.symbol}: {str(e)}")
            asset.current_price = asset.purchase_price  # Fallback to purchase price
            asset.total_value = asset.quantity * asset.purchase_price
    
    return portfolio

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

@router.get("/learn/etfs")
async def learn_about_etfs():
    """Educational endpoint to learn about ETF investing."""
    return {
        "description": "Exchange-Traded Funds (ETFs) are investment funds traded on stock exchanges, offering diversified exposure to various assets.",
        "categories": [
            {
                "name": "Index ETFs",
                "examples": ["SPY", "VTI", "QQQ"],
                "benefits": [
                    "Broad market exposure",
                    "Low cost",
                    "High liquidity"
                ],
                "typical_allocation": "40-60% of portfolio"
            },
            {
                "name": "Sector ETFs",
                "examples": ["XLF", "XLK", "XLE"],
                "benefits": [
                    "Industry-specific exposure",
                    "Tactical allocation",
                    "Thematic investing"
                ],
                "typical_allocation": "10-30% of portfolio"
            },
            {
                "name": "Smart Beta ETFs",
                "examples": ["USMV", "QUAL", "MTUM"],
                "benefits": [
                    "Factor-based investing",
                    "Enhanced diversification",
                    "Potential outperformance"
                ],
                "typical_allocation": "10-20% of portfolio"
            }
        ],
        "investment_methods": [
            {
                "method": "Core-Satellite",
                "description": "Using broad market ETFs as core holdings with specialized ETFs as satellite positions",
                "advantages": [
                    "Balanced approach",
                    "Cost-effective",
                    "Easy to rebalance"
                ]
            },
            {
                "method": "Asset Allocation",
                "description": "Using ETFs to build a diversified portfolio across asset classes",
                "advantages": [
                    "Complete diversification",
                    "Low maintenance",
                    "Easy to adjust"
                ]
            },
            {
                "method": "Tactical Trading",
                "description": "Using ETFs for short-term market opportunities",
                "advantages": [
                    "High liquidity",
                    "Lower risk than individual stocks",
                    "Sector rotation strategies"
                ]
            }
        ],
        "risks": [
            "Market risk",
            "Tracking error",
            "Trading volume/liquidity risk",
            "Management fee impact",
            "Complex ETF structures (leveraged/inverse)"
        ],
        "portfolio_integration": [
            "Use broad market ETFs as portfolio foundation",
            "Add sector ETFs for tactical positions",
            "Consider factor ETFs for enhanced returns",
            "Monitor total expense ratios",
            "Regular rebalancing to maintain allocations"
        ]
    }

@router.get("/learn/stocks")
async def learn_about_stocks():
    """Educational endpoint to learn about stocks investing."""
    return {
        "description": "Stocks represent ownership in a company and are one of the most common investment vehicles.",
        "categories": [
            {
                "name": "Growth Stocks",
                "examples": ["AAPL", "MSFT", "AMZN"],
                "benefits": [
                    "High potential returns",
                    "Capital appreciation",
                    "Market leadership potential"
                ],
                "typical_allocation": "20-40% of portfolio"
            },
            {
                "name": "Value Stocks",
                "examples": ["BRK.B", "JNJ", "PG"],
                "benefits": [
                    "Lower valuations",
                    "Dividend income",
                    "Defensive characteristics"
                ],
                "typical_allocation": "20-40% of portfolio"
            },
            {
                "name": "Dividend Stocks",
                "examples": ["KO", "PEP", "VZ"],
                "benefits": [
                    "Regular income",
                    "Lower volatility",
                    "Inflation protection"
                ],
                "typical_allocation": "10-30% of portfolio"
            }
        ],
        "investment_methods": [
            {
                "method": "Individual Stocks",
                "description": "Direct ownership of company shares",
                "advantages": [
                    "Full control over portfolio",
                    "No management fees",
                    "Tax efficiency"
                ]
            },
            {
                "method": "ETFs",
                "description": "Exchange-traded funds that track stock indices or sectors",
                "advantages": [
                    "Diversification",
                    "Lower costs",
                    "Easy to trade"
                ]
            },
            {
                "method": "Mutual Funds",
                "description": "Professionally managed investment vehicles",
                "advantages": [
                    "Professional management",
                    "Broad diversification",
                    "Regular investment options"
                ]
            }
        ],
        "risks": [
            "Market volatility",
            "Company-specific risks",
            "Economic cycle sensitivity",
            "Interest rate sensitivity",
            "Political and regulatory risks"
        ],
        "portfolio_integration": [
            "Start with a core position in broad market ETFs",
            "Add individual stocks for specific themes or opportunities",
            "Maintain sector diversification",
            "Consider both growth and value styles",
            "Regular rebalancing to maintain target allocation"
        ]
    }

@router.get("/learn/bonds")
async def learn_about_bonds():
    """Educational endpoint to learn about bonds investing."""
    return {
        "description": "Bonds are debt securities that provide regular interest payments and return of principal at maturity.",
        "categories": [
            {
                "name": "Government Bonds",
                "examples": ["U.S. Treasury Bonds", "T-Bills", "TIPS"],
                "benefits": [
                    "Highest credit quality",
                    "Tax advantages",
                    "Liquidity"
                ],
                "typical_allocation": "20-40% of portfolio"
            },
            {
                "name": "Corporate Bonds",
                "examples": ["Investment Grade", "High Yield", "Convertible Bonds"],
                "benefits": [
                    "Higher yields than government bonds",
                    "Diversification",
                    "Regular income"
                ],
                "typical_allocation": "10-30% of portfolio"
            },
            {
                "name": "Municipal Bonds",
                "examples": ["State Bonds", "Local Government Bonds"],
                "benefits": [
                    "Tax-exempt income",
                    "Lower default risk",
                    "Community investment"
                ],
                "typical_allocation": "5-15% of portfolio"
            }
        ],
        "investment_methods": [
            {
                "method": "Individual Bonds",
                "description": "Direct ownership of bond securities",
                "advantages": [
                    "Known return at maturity",
                    "No management fees",
                    "Customizable duration"
                ]
            },
            {
                "method": "Bond ETFs",
                "description": "Exchange-traded funds that track bond indices",
                "advantages": [
                    "Diversification",
                    "Liquidity",
                    "Lower minimum investment"
                ]
            },
            {
                "method": "Bond Mutual Funds",
                "description": "Professionally managed bond portfolios",
                "advantages": [
                    "Professional management",
                    "Active duration management",
                    "Regular income distributions"
                ]
            }
        ],
        "risks": [
            "Interest rate risk",
            "Credit risk",
            "Inflation risk",
            "Liquidity risk",
            "Call risk"
        ],
        "portfolio_integration": [
            "Use bonds to reduce portfolio volatility",
            "Match bond duration to investment horizon",
            "Consider tax implications",
            "Diversify across bond types",
            "Regular rebalancing to maintain target allocation"
        ]
    }

@router.put("/portfolios/{portfolio_id}", response_model=Portfolio)
async def update_portfolio(portfolio_id: str, portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    db_portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not db_portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db_portfolio.name = portfolio.name
    db_portfolio.description = portfolio.description
    db_portfolio.updated_at = datetime.now()
    
    db.commit()
    db.refresh(db_portfolio)
    return convert_db_to_model(db_portfolio) 