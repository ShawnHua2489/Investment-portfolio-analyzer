from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .data_cache import DataCache
import logging

logger = logging.getLogger(__name__)

class PortfolioAnalyzer:
    def __init__(self):
        self.data_cache = DataCache()

    def analyze_portfolio(self, portfolio: Dict) -> Dict:
        """Analyze portfolio performance and metrics."""
        total_value = 0
        asset_allocations = {}
        asset_breakdown = []

        print("\n=== Starting Portfolio Analysis ===")

        for asset in portfolio['assets']:
            symbol = asset['symbol']
            quantity = asset['quantity']
            purchase_price = asset['purchase_price']
            
            print(f"\nProcessing {symbol}...")
            # Force real-time data fetch
            data = self.data_cache.get_data(symbol, period="1d")
            print(f"Data received for {symbol}: {'Not Empty' if data is not None and not data.empty else 'Empty'}")
            
            if data is not None and not data.empty:
                try:
                    current_price = float(data['Close'].iloc[-1])
                    print(f"✓ Got live price for {symbol}: ${current_price:.2f}")
                except Exception as e:
                    print(f"Error getting price from data: {e}")
                    print(f"Data head: {data.head()}")
                    current_price = purchase_price
            else:
                current_price = purchase_price  # Fallback to purchase price if data unavailable
                print(f"⚠️ Using purchase price for {symbol}: ${purchase_price:.2f}")
            
            value = quantity * current_price
            total_value += value
            
            # Calculate allocation
            asset_type = asset['asset_type']
            asset_allocations[asset_type] = asset_allocations.get(asset_type, 0) + value
            
            # Add to breakdown with more details
            asset_info = {
                'symbol': symbol,
                'name': asset['name'],
                'quantity': quantity,
                'current_price': current_price,
                'purchase_price': purchase_price,
                'gain_loss': ((current_price - purchase_price) / purchase_price) * 100,
                'value': value,
                'allocation': 0,  # Will be calculated after total is known
                'asset_type': asset_type,
                'data_source': 'live' if data is not None and not data.empty else 'fallback'
            }
            asset_breakdown.append(asset_info)
            
            print(f"Asset details:")
            print(f"  Quantity: {quantity}")
            print(f"  Current Value: ${value:.2f}")
            print(f"  Gain/Loss: {asset_info['gain_loss']:+.2f}%")
            print(f"  Data Source: {asset_info['data_source']}")

        # Calculate allocations
        for asset in asset_breakdown:
            asset['allocation'] = (asset['value'] / total_value) * 100 if total_value > 0 else 0

        # Convert allocations to percentages
        asset_allocations = {
            k: (v / total_value) * 100 
            for k, v in asset_allocations.items()
        }

        print(f"\nPortfolio Summary:")
        print(f"Total Value: ${total_value:.2f}")
        print("Asset Allocations:")
        for asset_type, percentage in asset_allocations.items():
            print(f"  {asset_type}: {percentage:.1f}%")

        return {
            'total_value': total_value,
            'asset_allocations': asset_allocations,
            'number_of_assets': len(asset_breakdown),
            'assets': asset_breakdown,
            'last_updated': datetime.now().isoformat()
        }

    def calculate_var(self, portfolio: Dict, confidence_level: float = 0.95) -> Dict:
        """Calculate Value at Risk (VaR) for the portfolio."""
        returns_data = []
        weights = []
        total_value = 0

        # Get portfolio value and weights
        for asset in portfolio['assets']:
            symbol = asset['symbol']
            quantity = asset['quantity']
            purchase_price = asset['purchase_price']
            
            data = self.data_cache.get_data(symbol, period="1y")
            if data is not None and not data.empty:
                current_price = data['Close'].iloc[-1]
                value = quantity * current_price
                total_value += value
                weights.append(value)
                returns_data.append(data['Close'].pct_change().dropna())

        if not returns_data:
            return {
                "var_amount": 0,
                "var_percentage": 0,
                "confidence_level": confidence_level
            }

        # Calculate portfolio returns
        weights = np.array(weights) / total_value
        portfolio_returns = pd.concat(returns_data, axis=1).dot(weights)

        # Calculate VaR
        var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        var_amount = abs(var * total_value)
        var_percentage = abs(var * 100)

        return {
            "var_amount": var_amount,
            "var_percentage": var_percentage,
            "confidence_level": confidence_level
        }

    def calculate_correlation_matrix(self, portfolio: Dict) -> Dict:
        """Calculate correlation matrix for portfolio assets."""
        returns_data = {}
        
        for asset in portfolio['assets']:
            symbol = asset['symbol']
            data = self.data_cache.get_data(symbol, period="1y")
            if data is not None and not data.empty:
                returns_data[symbol] = data['Close'].pct_change().dropna()

        if not returns_data:
            return {"correlation_matrix": {}}

        # Create correlation matrix
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr().to_dict()

        return {
            "correlation_matrix": correlation_matrix,
            "period": "1y"
        }

    def calculate_efficient_frontier(self, portfolio: Dict, num_portfolios: int = 1000) -> Dict:
        """Calculate efficient frontier for portfolio optimization."""
        returns_data = {}
        prices_data = {}
        
        for asset in portfolio['assets']:
            symbol = asset['symbol']
            data = self.data_cache.get_data(symbol, period="1y")
            if data is not None and not data.empty:
                returns_data[symbol] = data['Close'].pct_change().dropna()
                prices_data[symbol] = data['Close']

        if not returns_data:
            return {
                "efficient_frontier": [],
                "optimal_portfolio": None
            }

        # Calculate returns and covariance
        returns_df = pd.DataFrame(returns_data)
        mean_returns = returns_df.mean()
        cov_matrix = returns_df.cov()

        # Generate random portfolios
        portfolios = []
        for _ in range(num_portfolios):
            weights = np.random.random(len(returns_data))
            weights /= np.sum(weights)
            
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            portfolios.append({
                "weights": dict(zip(returns_data.keys(), weights)),
                "return": portfolio_return,
                "risk": portfolio_risk
            })

        # Find optimal portfolio (highest Sharpe ratio)
        risk_free_rate = 0.02  # Assuming 2% risk-free rate
        optimal_portfolio = max(
            portfolios,
            key=lambda p: (p["return"] - risk_free_rate) / p["risk"]
        )

        return {
            "efficient_frontier": portfolios,
            "optimal_portfolio": optimal_portfolio
        }

    def run_stress_test(self, portfolio: Dict, scenarios: List[Dict] = None) -> Dict:
        """Run stress test scenarios on the portfolio."""
        if scenarios is None:
            scenarios = [
                {"name": "Market Crash", "impact": -0.20},
                {"name": "Recession", "impact": -0.10},
                {"name": "Interest Rate Hike", "impact": -0.05},
                {"name": "Inflation Spike", "impact": -0.15}
            ]

        results = []
        for scenario in scenarios:
            scenario_value = 0
            for asset in portfolio['assets']:
                symbol = asset['symbol']
                quantity = asset['quantity']
                purchase_price = asset['purchase_price']
                
                data = self.data_cache.get_data(symbol, period="1d")
                if data is not None and not data.empty:
                    current_price = data['Close'].iloc[-1]
                else:
                    current_price = purchase_price
                
                # Apply scenario impact
                scenario_price = current_price * (1 + scenario['impact'])
                scenario_value += quantity * scenario_price

            results.append({
                "scenario": scenario['name'],
                "impact": scenario['impact'],
                "portfolio_value": scenario_value,
                "loss_amount": scenario_value - portfolio['total_value'],
                "loss_percentage": (scenario_value - portfolio['total_value']) / portfolio['total_value'] * 100
            })

        return {
            "scenarios": results,
            "base_portfolio_value": portfolio['total_value']
        } 