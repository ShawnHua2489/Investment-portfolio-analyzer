from typing import Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import requests
import json
import os
import pickle
from pathlib import Path
import logging
import stat
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCache:
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Use user's home directory
            home_dir = Path.home()
            cache_dir = home_dir / ".investment_cache"
        self.cache_dir = Path(cache_dir).resolve()
        try:
            self.cache_dir.mkdir(mode=0o755, exist_ok=True)
            # Ensure directory is writable
            os.chmod(str(self.cache_dir), 
                    stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |  # User RWX
                    stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |  # Group RWX
                    stat.S_IROTH | stat.S_IXOTH)                   # Others RX
        except Exception as e:
            logger.error(f"Failed to create/set permissions on cache directory: {e}")
            # Fallback to current directory
            self.cache_dir = Path.cwd() / ".cache"
            self.cache_dir.mkdir(mode=0o755, exist_ok=True)
        
        logger.info(f"Cache directory initialized at: {self.cache_dir}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cache_duration = timedelta(minutes=5)  # Cache data for 5 minutes
        self.last_request_time = {}
        self.min_request_interval = 1.0  # Minimum seconds between requests for the same symbol

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get data for a symbol, using cache if available."""
        cache_file = self.cache_dir / f"{symbol}_{period}.pkl"
        current_time = datetime.now()
        
        # Check if we need to wait due to rate limiting
        if symbol in self.last_request_time:
            time_since_last_request = (current_time - self.last_request_time[symbol]).total_seconds()
            if time_since_last_request < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last_request)
        
        # Try to load from cache first
        if cache_file.exists():
            cache_age = current_time - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < self.cache_duration:
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    logger.info(f"Loaded cached data for {symbol}")
                    return data
                except Exception as e:
                    logger.warning(f"Failed to load cache for {symbol}: {e}")
        
        # Fetch new data
        data = self._fetch_data(symbol, period)
        if data is not None and not data.empty:
            self.last_request_time[symbol] = current_time
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f)
                # Ensure file is readable/writable by user and group
                os.chmod(str(cache_file), 
                        stat.S_IRUSR | stat.S_IWUSR |  # User RW
                        stat.S_IRGRP | stat.S_IWGRP)   # Group RW
                logger.info(f"Cached data for {symbol}")
            except Exception as e:
                logger.error(f"Failed to cache data for {symbol}: {e}")
        
        return data

    def _fetch_data(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Fetch data from Yahoo Finance with fallback to direct API."""
        try:
            # Try yfinance download first (most reliable method)
            logger.info(f"Attempting to fetch data for {symbol} using yfinance...")
            data = yf.download(symbol, period=period, progress=False)
            if not data.empty:
                logger.info(f"Successfully fetched data for {symbol} using yfinance")
                return data
            logger.warning(f"No data returned from yfinance for {symbol}")

            # Fallback to direct API with rate limiting
            logger.info(f"Attempting to fetch data for {symbol} using direct API...")
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                "range": period,
                "interval": "1d",
                "includePrePost": False
            }
            
            # Add delay between requests
            time.sleep(self.min_request_interval)
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
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
                    logger.info(f"Successfully fetched data for {symbol} using direct API")
                    return df
                else:
                    logger.warning(f"Unexpected API response format for {symbol}")
            elif response.status_code == 429:  # Rate limit
                logger.warning(f"Rate limited for {symbol}, will retry with backoff")
                raise Exception("Rate limited")
            else:
                logger.error(f"API request failed for {symbol} with status {response.status_code}")

            return None
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for a specific symbol or all symbols."""
        if symbol:
            for cache_file in self.cache_dir.glob(f"{symbol}_*.pkl"):
                cache_file.unlink()
            if symbol in self.last_request_time:
                del self.last_request_time[symbol]
        else:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            self.last_request_time.clear()

    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache."""
        logger.info(f"Getting cache stats from: {self.cache_dir}")
        cache_files = list(self.cache_dir.glob("*.pkl"))
        logger.info(f"Found {len(cache_files)} cache files")
        stats = {
            "total_cached_symbols": len(cache_files),
            "cache_size_mb": sum(f.stat().st_size for f in cache_files) / (1024 * 1024),
            "oldest_cache": min((f.stat().st_mtime for f in cache_files), default=None),
            "newest_cache": max((f.stat().st_mtime for f in cache_files), default=None),
            "active_symbols": len(self.last_request_time)
        }
        logger.info(f"Cache stats: {stats}")
        return stats 