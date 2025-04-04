# Investment Portfolio Analyzer

A sophisticated investment portfolio analysis tool that helps you track, analyze, and optimize your investment portfolio. Built with FastAPI and React, featuring an elegant UI and robust financial analytics.

## Features

- Portfolio tracking and management with real-time updates
- Advanced risk metrics calculation (Beta, Sharpe Ratio, Volatility)
- Multi-source market data integration with fallback options
- Intelligent asset allocation optimization
- Interactive data visualizations and charts
- Comprehensive educational content
- Elegant, responsive web interface
- Robust error handling and data validation

## Tech Stack

### Backend
- FastAPI (Python 3.9+)
- SQLAlchemy (Database ORM)
- yfinance & Direct Yahoo Finance API integration
- pandas & numpy for financial calculations
- Advanced caching system for market data

### Frontend
- React with TypeScript
- Material-UI components
- Chart.js for data visualization
- Responsive design with modern aesthetics
- Real-time data updates

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 14+
- npm or yarn
- Git

### Backend Setup

1. Create and activate virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the backend server:
```bash
PYTHONPATH=. uvicorn main:app --reload --log-level debug
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm run dev
```

## API Documentation

Once the backend server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
investment-portfolio-analyzer/
├── backend/
│   ├── api/
│   │   ├── models/
│   │   └── routes/
│   ├── services/
│   │   ├── data_cache.py
│   │   ├── portfolio_analysis.py
│   │   └── risk_management.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── public/
│   └── package.json
└── README.md
```

## Features in Detail

### Portfolio Management
- Create and manage multiple investment portfolios
- Real-time tracking of assets and performance
- Automated portfolio value updates
- Transaction history tracking

### Risk Analysis
- Advanced risk metrics calculation:
  - Beta (market correlation)
  - Sharpe Ratio (risk-adjusted returns)
  - Value at Risk (VaR)
  - Portfolio volatility
- Correlation matrix analysis
- Efficient frontier optimization
- Stress testing capabilities

### Market Data Integration
- Multi-source market data fetching
- Intelligent caching system
- Rate limit handling
- Fallback mechanisms for data reliability
- Historical price analysis

### Educational Content
- Comprehensive financial metrics explanations
- Investment strategy guides
- Risk management tutorials
- Market analysis tools

## Recent Updates

- Enhanced market data reliability with multiple data sources
- Improved error handling and data validation
- Advanced caching system for better performance
- Robust risk metrics calculation
- Elegant UI design with modern aesthetics
- Comprehensive educational content

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Yahoo Finance API for market data
- FastAPI for the robust backend framework
- React and Material-UI for the frontend implementation
- Open source community for various tools and libraries 