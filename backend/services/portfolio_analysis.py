from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from api.models.portfolio import Portfolio, Asset
from services.data_cache import DataCache
import logging

logger = logging.getLogger(__name__)

class PortfolioAnalyzer:
    def __init__(self, portfolio: Portfolio):
        self.portfolio = portfolio
        self.data_cache = DataCache()
        self.logger = logging.getLogger(__name__)

    def _get_ticker_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical data for a ticker using the data cache."""
        try:
            return self.data_cache.get_data(symbol, period)
        except Exception as e:
            self.logger.error(f"Failed to fetch data for {symbol}: {str(e)}")
            return None

    def calculate_total_value(self) -> float:
        """Calculate the total current value of the portfolio."""
        total_value = 0.0
        for asset in self.portfolio.assets:
            try:
                hist_data = self._get_ticker_data(asset.symbol, period="1d")
                current_price = hist_data['Close'].iloc[-1] if hist_data is not None and not hist_data.empty else asset.purchase_price
                total_value += asset.quantity * current_price
            except Exception as e:
                self.logger.warning(f"Using purchase price for {asset.symbol} due to error: {str(e)}")
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
                current_price = hist_data['Close'].iloc[-1] if hist_data is not None and not hist_data.empty else asset.purchase_price
                asset_value = asset.quantity * current_price
            except Exception as e:
                self.logger.warning(f"Using purchase price for {asset.symbol} due to error: {str(e)}")
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