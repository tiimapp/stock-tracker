#!/usr/bin/env python3
"""
Historical data fetcher - Fetches historical price data for technical analysis.
"""

import requests
import logging
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Sina Finance historical data API
SINA_HISTORY_URL = "https://quotes.sina.cn/cn/api/jsonp.php/var=/CN_MarketDataService.getKLineData?symbol={symbol}&scale={scale}&datalen={days}"

# Tencent Finance historical data
TENCENT_HISTORY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=s{code},day,,,{days},qfq"


def fetch_historical_prices_tencent(symbol: str, days: int = 30) -> List[dict]:
    """
    Fetch historical daily prices from Tencent Finance.
    
    Args:
        symbol: Stock symbol (e.g., 'sh688777' or just '688777')
        days: Number of days of historical data
    
    Returns:
        List of daily price data dictionaries
    """
    # Extract just the numeric code
    code = symbol.replace('sh', '').replace('sz', '')
    url = TENCENT_HISTORY_URL.format(code=code, days=days)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://stockapp.finance.qq.com/'
    }
    
    try:
        logger.info(f"Fetching {days} days of historical data from Tencent for {symbol}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Navigate the JSON structure
        # Structure: {"code": 0, "data": {"sh688777": {"day": [...], ...}}}
        stock_data = data.get('data', {}).get(symbol, {})
        day_data = stock_data.get('day', [])
        
        if not day_data:
            logger.warning(f"No historical data found for {symbol}")
            return []
        
        # Parse daily data: [date, open, close, high, low, volume, turnover, ?]
        historical = []
        for day in day_data:
            if len(day) >= 7:
                daily = {
                    'date': day[0],
                    'open': float(day[1]) if day[1] else 0.0,
                    'close': float(day[2]) if day[2] else 0.0,
                    'high': float(day[3]) if day[3] else 0.0,
                    'low': float(day[4]) if day[4] else 0.0,
                    'volume': float(day[5]) if day[5] else 0.0,
                    'turnover': float(day[6]) if day[6] else 0.0,
                }
                historical.append(daily)
        
        logger.info(f"Fetched {len(historical)} days of historical data")
        return historical
        
    except Exception as e:
        logger.error(f"Failed to fetch historical data from Tencent: {e}")
        return []


def fetch_historical_prices_sina(symbol: str, days: int = 100) -> List[dict]:
    """
    Fetch historical daily prices from Sina Finance.
    
    Args:
        symbol: Stock symbol (e.g., 'sh688777')
        days: Number of days (note: Sina returns year-end data points)
    
    Returns:
        List of daily price data
    """
    # Sina scale: 240=daily K-line (best for historical data)
    # Request more days to ensure we get enough data points
    url = SINA_HISTORY_URL.format(symbol=symbol, scale=240, days=max(days, 100))
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/'
    }
    
    try:
        logger.info(f"Fetching {days} days from Sina for {symbol}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        content = response.text
        
        # Parse JSONP: var _var=[{...}, {...}]
        import re
        match = re.search(r'\[(.+)\]', content)
        if not match:
            logger.warning("Failed to parse Sina JSONP response")
            return []
        
        import json
        data = json.loads(f'[{match.group(1)}]')
        
        historical = []
        for day in data:
            daily = {
                'date': day.get('day', ''),
                'open': float(day.get('open', 0)),
                'close': float(day.get('close', 0)),
                'high': float(day.get('high', 0)),
                'low': float(day.get('low', 0)),
                'volume': float(day.get('volume', 0)),
                'turnover': 0.0,  # Not provided in this API
            }
            historical.append(daily)
        
        logger.info(f"Fetched {len(historical)} days from Sina")
        return historical
        
    except Exception as e:
        logger.error(f"Failed to fetch historical data from Sina: {e}")
        return []


def fetch_historical_prices(symbol: str, days: int = 100) -> List[dict]:
    """
    Fetch historical prices from best available source.
    
    Args:
        symbol: Stock symbol
        days: Number of days (note: actual data points may vary by API)
    
    Returns:
        List of closing prices (oldest to newest)
    """
    # Try Sina first (has historical data)
    data = fetch_historical_prices_sina(symbol, days)
    
    if data and len(data) > 0:
        # Sort by date to ensure oldest first
        data.sort(key=lambda x: x['date'])
        logger.info(f"Got {len(data)} historical data points from Sina")
        return [d['close'] for d in data]
    
    # Try Tencent as fallback
    data = fetch_historical_prices_tencent(symbol, days)
    
    if data:
        data.sort(key=lambda x: x['date'])
        logger.info(f"Got {len(data)} historical data points from Tencent")
        return [d['close'] for d in data]
    
    logger.warning("No historical data available from any source")
    return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Testing historical data fetcher...")
    prices = fetch_historical_prices("sh688777", days=30)
    
    if prices:
        print(f"\n✓ Successfully fetched {len(prices)} days of data")
        print(f"Latest close: ¥{prices[-1]:.2f}")
        print(f"Oldest close: ¥{prices[0]:.2f}")
        print(f"Sample (last 5 days): {prices[-5:]}")
    else:
        print("\n✗ Failed to fetch historical data")
