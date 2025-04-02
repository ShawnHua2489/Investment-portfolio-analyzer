from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from api.models.portfolio import Portfolio, Asset
import time
from functools import wraps
import requests
import json

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class RiskManagement:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.risk_free_rate = 0.02  # 2% risk-free rate
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @retry_on_failure(max_retries=3, delay=1)
    def _get_ticker_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical data for a ticker with retry logic and fallback methods."""
        try:
            # First try using yfinance's download method
            data = yf.download(symbol, period=period, progress=False)
            if not data.empty:
                print(f"Successfully retrieved data for {symbol}")
                return data

            # If that fails, try using the Yahoo Finance API directly
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "range": "1y",
                "interval": "1d"
            }
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    df = pd.DataFrame({
                        'Open': quotes['open'],
                        'High': quotes['high'],
                        'Low': quotes['low'],
                        'Close': quotes['close'],
                        'Volume': quotes['volume']
                    }, index=pd.to_datetime(timestamps, unit='s'))
                    print(f"Successfully retrieved data for {symbol} via direct API")
                    return df

            print(f"Warning: No data available for {symbol}")
            return None
        except Exception as e:
            print(f"Warning: Error fetching data for {symbol}")
            return None

    def calculate_var(self, confidence_level: float = 0.95) -> Dict:
        """Calculate Value at Risk (VaR) for the portfolio."""
        try:
            portfolio_value = self._calculate_portfolio_value()
            if portfolio_value <= 0:
                return {"error": "Invalid portfolio value"}

            # Get historical returns with retry logic
            returns_data = []
            for asset in self.portfolio.assets:
                hist_data = self._get_ticker_data(asset.symbol)
                if hist_data is not None and not hist_data.empty:
                    returns = hist_data['Close'].pct_change().dropna()
                    weight = (asset.quantity * asset.purchase_price) / portfolio_value
                    returns_data.append(returns * weight)

            if not returns_data:
                return {
                    "warning": "Using simplified VaR calculation due to data limitations",
                    "var_estimate": round(portfolio_value * 0.02, 2),  # Conservative 2% daily VaR estimate
                    "confidence_level": confidence_level
                }

            portfolio_returns = pd.concat(returns_data, axis=1).sum(axis=1)
            var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
            
            return {
                "var_amount": round(abs(var * portfolio_value), 2),
                "var_percentage": round(abs(var * 100), 2),
                "confidence_level": confidence_level
            }
        except Exception as e:
            return {"error": str(e)}

    def calculate_correlation_matrix(self) -> Dict:
        """Calculate correlation matrix between all assets."""
        try:
            prices = {}
            for asset in self.portfolio.assets:
                hist_data = self._get_ticker_data(asset.symbol)
                if hist_data is not None and not hist_data.empty:
                    prices[asset.symbol] = hist_data['Close']

            if not prices:
                return {"warning": "No historical price data available"}

            df = pd.DataFrame(prices)
            correlation = df.corr().round(3)
            
            # Convert correlation matrix to a format that's JSON serializable
            correlation_dict = {}
            for col in correlation.columns:
                correlation_dict[col] = {
                    k: float(v) if not np.isnan(v) else None
                    for k, v in correlation[col].items()
                }
            
            return {
                "correlation_matrix": correlation_dict,
                "assets": list(correlation.columns)
            }
        except Exception as e:
            return {"error": str(e)}

    def calculate_efficient_frontier(self, num_portfolios: int = 100) -> Dict:
        """Calculate efficient frontier for portfolio optimization."""
        try:
            # Get historical returns and covariance matrix
            returns = self._get_historical_returns()
            if returns.empty:
                return {"error": "No historical data available"}

            # Calculate mean returns and covariance
            mean_returns = returns.mean()
            cov_matrix = returns.cov()

            # Generate random portfolio weights
            weights_list = []
            returns_list = []
            volatility_list = []
            sharpe_list = []

            for _ in range(num_portfolios):
                weights = np.random.random(len(self.portfolio.assets))
                weights = weights / np.sum(weights)
                weights_list.append(weights)

                # Calculate portfolio return
                portfolio_return = np.sum(mean_returns * weights)
                returns_list.append(portfolio_return)

                # Calculate portfolio volatility
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                volatility_list.append(portfolio_volatility)

                # Calculate Sharpe ratio
                sharpe = (portfolio_return - self.risk_free_rate) / portfolio_volatility
                sharpe_list.append(sharpe)

            # Find optimal portfolio (maximum Sharpe ratio)
            optimal_idx = np.argmax(sharpe_list)
            optimal_weights = weights_list[optimal_idx]

            return {
                "optimal_weights": dict(zip([asset.symbol for asset in self.portfolio.assets], 
                                          [round(w, 4) for w in optimal_weights])),
                "optimal_return": round(returns_list[optimal_idx], 4),
                "optimal_volatility": round(volatility_list[optimal_idx], 4),
                "optimal_sharpe": round(sharpe_list[optimal_idx], 4)
            }
        except Exception as e:
            return {"error": str(e)}

    def stress_test(self, scenarios: List[Dict[str, float]]) -> Dict:
        """Perform stress testing on the portfolio."""
        try:
            current_value = self._calculate_portfolio_value()
            results = []

            for scenario in scenarios:
                scenario_value = current_value
                for asset in self.portfolio.assets:
                    if asset.symbol in scenario:
                        price_change = scenario[asset.symbol]
                        asset_value = asset.quantity * asset.purchase_price
                        scenario_value += asset_value * price_change

                results.append({
                    "scenario": scenario,
                    "portfolio_value": round(scenario_value, 2),
                    "change_percentage": round((scenario_value - current_value) / current_value * 100, 2)
                })

            return {
                "current_value": round(current_value, 2),
                "scenarios": results
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_historical_returns(self) -> pd.DataFrame:
        """Get historical returns for all assets."""
        returns = {}
        for asset in self.portfolio.assets:
            try:
                ticker = yf.Ticker(asset.symbol)
                hist = ticker.history(period="1y")
                returns[asset.symbol] = hist['Close'].pct_change()
            except:
                continue
        return pd.DataFrame(returns)

    def _calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value with fallback to purchase price."""
        total_value = 0.0
        for asset in self.portfolio.assets:
            try:
                hist_data = self._get_ticker_data(asset.symbol, period="1d")
                if hist_data is not None and not hist_data.empty:
                    current_price = hist_data['Close'].iloc[-1]
                else:
                    current_price = asset.purchase_price
                total_value += asset.quantity * current_price
            except:
                total_value += asset.quantity * asset.purchase_price
        return total_value

    def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info.get('regularMarketPrice', 0.0)
        except:
            return 0.0 