from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from api.models.portfolio import Portfolio, Asset
import requests
import json

class PortfolioAnalyzer:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cache = {}

    def clear_cache(self, symbol: str = None):
        """Clear the data cache for a specific symbol or all symbols."""
        if symbol:
            # Clear cache for specific symbol
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(symbol)]
            for k in keys_to_remove:
                del self.cache[k]
        else:
            # Clear entire cache
            self.cache.clear()

    def _get_ticker_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical data for a ticker with multiple fallback methods."""
        # Check cache first
        cache_key = f"{symbol}_{period}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        data = None
        errors = []

        # Method 1: Try yfinance's download method
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            if not data.empty:
                self.cache[cache_key] = data
                return data
        except Exception as e:
            errors.append(f"yfinance download failed: {str(e)}")

        # Method 2: Try Yahoo Finance API directly
        try:
            intervals = {"1d": "1d", "1mo": "1mo", "1y": "1d", "5y": "1wk"}
            interval = intervals.get(period, "1d")
            
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "range": period,
                "interval": interval,
                "includePrePost": False
            }
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                json_data = response.json()
                if 'chart' in json_data and 'result' in json_data['chart'] and json_data['chart']['result']:
                    result = json_data['chart']['result'][0]
                    timestamps = result['timestamp']
                    quotes = result['indicators']['quote'][0]
                    
                    if all(key in quotes for key in ['open', 'high', 'low', 'close', 'volume']):
                        df = pd.DataFrame({
                            'Open': quotes['open'],
                            'High': quotes['high'],
                            'Low': quotes['low'],
                            'Close': quotes['close'],
                            'Volume': quotes['volume']
                        }, index=pd.to_datetime(timestamps, unit='s'))
                        df = df.dropna()
                        
                        if not df.empty:
                            self.cache[cache_key] = df
                            return df
        except Exception as e:
            errors.append(f"Yahoo Finance API failed: {str(e)}")

        # Method 3: Try alternative Yahoo Finance endpoint
        try:
            url = f"https://finance.yahoo.com/quote/{symbol}/history"
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Extract the data from the page's embedded JSON
                html = response.text
                json_str = html[html.find('"HistoricalPriceStore":')+23:html.find(',"isPending"')]
                json_data = json.loads(json_str)
                
                if 'prices' in json_data:
                    prices = json_data['prices']
                    df = pd.DataFrame(prices)
                    df['date'] = pd.to_datetime(df['date'], unit='s')
                    df.set_index('date', inplace=True)
                    df = df.rename(columns={
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'volume': 'Volume'
                    })
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
                    
                    if not df.empty:
                        self.cache[cache_key] = df
                        return df
        except Exception as e:
            errors.append(f"Alternative Yahoo Finance endpoint failed: {str(e)}")

        # If all methods fail, try to return cached data if available
        if data is not None and not data.empty:
            self.cache[cache_key] = data
            return data

        # Log all errors for debugging
        print(f"Failed to fetch data for {symbol}. Errors: {'; '.join(errors)}")
        return None

    def calculate_total_value(self) -> float:
        """Calculate the total current value of the portfolio."""
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

    def calculate_asset_allocation(self) -> Dict[str, float]:
        """Calculate the percentage allocation of each asset type."""
        total_value = self.calculate_total_value()
        allocation = {}
        
        if total_value == 0:
            return {}
        
        for asset in self.portfolio.assets:
            try:
                hist_data = self._get_ticker_data(asset.symbol, period="1d")
                if hist_data is not None and not hist_data.empty:
                    current_price = hist_data['Close'].iloc[-1]
                else:
                    current_price = asset.purchase_price
                asset_value = asset.quantity * current_price
            except:
                asset_value = asset.quantity * asset.purchase_price
                
            percentage = (asset_value / total_value) * 100 if total_value > 0 else 0
            
            if asset.asset_type in allocation:
                allocation[asset.asset_type] += percentage
            else:
                allocation[asset.asset_type] = percentage
                
        return {k: round(v, 2) for k, v in allocation.items()}

    def calculate_risk_metrics(self) -> Dict:
        """Calculate risk metrics including Beta and Sharpe ratio."""
        try:
            # Get historical data for portfolio and market (S&P 500)
            portfolio_returns = self._calculate_portfolio_returns()
            market_returns = self._get_market_returns()
            
            # Calculate Beta
            beta = self._calculate_beta(portfolio_returns, market_returns)
            
            # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
            risk_free_rate = 0.02
            sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns, risk_free_rate)
            
            return {
                "beta": round(beta, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "volatility": round(np.std(portfolio_returns) * np.sqrt(252), 2)  # Annualized volatility
            }
        except Exception as e:
            return {
                "beta": 0.0,
                "sharpe_ratio": 0.0,
                "volatility": 0.0,
                "error": str(e)
            }

    def calculate_sector_diversification(self) -> Dict:
        """Calculate sector allocation of the portfolio."""
        sector_allocation = {}
        total_value = self.calculate_total_value()
        
        for asset in self.portfolio.assets:
            try:
                hist_data = self._get_ticker_data(asset.symbol, period="1d")
                if hist_data is not None and not hist_data.empty:
                    current_price = hist_data['Close'].iloc[-1]
                else:
                    current_price = asset.purchase_price
                asset_value = asset.quantity * current_price
            except:
                asset_value = asset.quantity * asset.purchase_price
                
            percentage = (asset_value / total_value) * 100
            
            # Get sector information from yfinance
            try:
                ticker = yf.Ticker(asset.symbol)
                sector = ticker.info.get('sector', 'Unknown')
                if sector in sector_allocation:
                    sector_allocation[sector] += percentage
                else:
                    sector_allocation[sector] = percentage
            except:
                if 'Unknown' in sector_allocation:
                    sector_allocation['Unknown'] += percentage
                else:
                    sector_allocation['Unknown'] = percentage
                    
        return sector_allocation

    def generate_rebalancing_suggestions(self) -> List[Dict]:
        """Generate portfolio rebalancing suggestions."""
        try:
            current_allocation = self.calculate_asset_allocation()
            target_allocation = {
                "stock": 60.0,
                "bond": 30.0,
                "etf": 10.0
            }
            
            suggestions = []
            for asset_type, target in target_allocation.items():
                current = current_allocation.get(asset_type, 0.0)
                difference = target - current
                
                if abs(difference) > 5:  # Only suggest if difference is more than 5%
                    suggestions.append({
                        "asset_type": asset_type,
                        "current_percentage": round(current, 2),
                        "target_percentage": target,
                        "suggested_action": "buy" if difference > 0 else "sell",
                        "adjustment_needed": round(abs(difference), 2)
                    })
                    
            return suggestions
        except Exception as e:
            return [{"error": str(e)}]

    def calculate_portfolio_metrics(self) -> Dict:
        """Calculate comprehensive portfolio metrics."""
        try:
            total_value = sum(asset.quantity * asset.purchase_price for asset in self.portfolio.assets)
            
            # Calculate asset allocation
            allocation = {}
            for asset in self.portfolio.assets:
                asset_value = asset.quantity * asset.purchase_price
                percentage = (asset_value / total_value) * 100 if total_value > 0 else 0
                if asset.asset_type in allocation:
                    allocation[asset.asset_type] += percentage
                else:
                    allocation[asset.asset_type] = percentage
            
            # Round allocation percentages
            allocation = {k: round(v, 2) for k, v in allocation.items()}
            
            return {
                "total_value": round(total_value, 2),
                "asset_allocation": allocation,
                "number_of_assets": len(self.portfolio.assets),
                "assets": [{
                    "symbol": asset.symbol,
                    "name": asset.name,
                    "value": round(asset.quantity * asset.purchase_price, 2),
                    "percentage": round((asset.quantity * asset.purchase_price / total_value) * 100 if total_value > 0 else 0, 2)
                } for asset in self.portfolio.assets],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }

    def _calculate_portfolio_returns(self) -> np.ndarray:
        """Calculate historical portfolio returns."""
        try:
            returns = []
            for asset in self.portfolio.assets:
                hist_data = self._get_ticker_data(asset.symbol)
                if hist_data is not None and not hist_data.empty:
                    returns.append(hist_data['Close'].pct_change().dropna())
                    
            if returns:
                return np.mean(returns, axis=0)
            return np.array([])
        except:
            return np.array([])

    def _get_market_returns(self) -> np.ndarray:
        """Get market returns (S&P 500)."""
        try:
            hist_data = self._get_ticker_data("^GSPC")
            if hist_data is not None and not hist_data.empty:
                return hist_data['Close'].pct_change().dropna().values
            return np.array([])
        except:
            return np.array([])

    def _calculate_beta(self, portfolio_returns: np.ndarray, market_returns: np.ndarray) -> float:
        """Calculate portfolio beta."""
        try:
            if len(portfolio_returns) == 0 or len(market_returns) == 0:
                return 0.0
            covariance = np.cov(portfolio_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            return covariance / market_variance if market_variance != 0 else 0.0
        except:
            return 0.0

    def _calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float) -> float:
        """Calculate Sharpe ratio."""
        try:
            if len(returns) == 0:
                return 0.0
            excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
            return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) != 0 else 0.0
        except:
            return 0.0 