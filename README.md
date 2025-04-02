# Investment Portfolio Analyzer

A comprehensive investment portfolio analysis tool that helps you track, analyze, and optimize your investment portfolio. Built with FastAPI and React.

## Features

- Portfolio tracking and management
- Real-time market data integration with Yahoo Finance
- Risk analysis and metrics calculation
- Asset allocation optimization
- Commodity investment tracking
- Educational content for financial concepts
- Interactive web interface

## Tech Stack

### Backend
- FastAPI (Python)
- SQLAlchemy (Database ORM)
- yfinance (Market data)
- pandas (Data analysis)
- numpy (Numerical computations)

### Frontend
- React
- TypeScript
- Material-UI
- Chart.js

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 14+
- npm or yarn

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
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── README.md
```

## Features in Detail

### Portfolio Management
- Create and manage multiple portfolios
- Track assets and their performance
- Monitor portfolio value and returns

### Risk Analysis
- Calculate key risk metrics (Beta, Sharpe Ratio, VaR)
- Portfolio correlation analysis
- Efficient frontier optimization

### Market Data
- Real-time stock and ETF data
- Historical price tracking
- Commodity price monitoring

### Educational Content
- Financial metrics explanation
- Investment strategy guides
- Risk management tips

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
- FastAPI for the backend framework
- React for the frontend framework 