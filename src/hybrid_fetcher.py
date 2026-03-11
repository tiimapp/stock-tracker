#!/usr/bin/env python3
"""
Hybrid Fetcher Module - Works from overseas servers.

Strategy:
- A-Shares: Direct multi-provider API calls (Tencent → Sina → NetEase fallback)
- Futures: AKShare (Sina-based, works overseas)
- News: AKShare stock_news_em() (works overseas)

This module bypasses AKShare for A-shares to avoid connectivity issues from overseas.
"""

import requests
import re
import json
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

# AKShare imports (only for futures and news)
import akshare as ak

logger = logging.getLogger(__name__)

# Data delay warning
DATA_DELAY_WARNING = "⚠️ 免费数据延迟约 15-20 分钟"

# API URLs for A-shares (direct calls, work from overseas)
TENCENT_PRICE_URL = "https://qt.gtimg.cn/q={symbol}"
SINA_PRICE_URL = "https://hq.sinajs.cn/list={symbol}"
NETEASE_PRICE_URL = "https://api.money.126.net/data/feed/{symbol}"

# Headers to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://finance.qq.com/',
    'Connection': 'keep-alive',
}


def fetch_price_data(symbol: str, symbol_type: str = "A", retry: int = 3) -> Optional[Dict]:
    """
    Fetch real-time price data using hybrid approach.
    
    Args:
        symbol: Stock/futures symbol (e.g., '688777' for A-shares, 'C2605' for futures)
        symbol_type: Type of symbol - "A" for A-shares, "futures" for commodity futures
        retry: Number of retry attempts
    
    Returns:
        Dictionary with price data and freshness info, or None if failed
    """
    logger.info(f"Fetching price data for {symbol} (type: {symbol_type})")
    
    if symbol_type == "A":
        # A-shares: Use direct multi-provider approach (works from overseas)
        apis = [
            ('Tencent 财经', fetch_price_tencent),
            ('Sina 财经', fetch_price_sina),
            ('NetEase 财经', fetch_price_netease),
        ]
    elif symbol_type == "futures":
        # Futures: Use AKShare (Sina-based, works overseas)
        apis = [
            ('AKShare 期货实时行情', fetch_price_futures_zh_realtime),
            ('AKShare 新浪财经期货历史', fetch_price_futures_zh_daily_sina),
        ]
    else:
        logger.error(f"Unknown symbol type: {symbol_type}")
        return None
    
    for api_name, api_func in apis:
        logger.info(f"Trying {api_name} for {symbol}")
        try:
            price_data = api_func(symbol, retry)
            if price_data:
                # Add freshness indicator
                price_data['data_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                price_data['data_delay_warning'] = DATA_DELAY_WARNING
                price_data['provider'] = api_name
                logger.info(f"✓ Successfully fetched from {api_name}: {price_data['name']} ¥{price_data['current_price']}")
                return price_data
        except Exception as e:
            logger.warning(f"{api_name} failed: {type(e).__name__}: {e}")
            continue
    
    logger.error(f"✗ All sources failed for {symbol}")
    return None


def fetch_price_tencent(symbol: str, retry: int = 3) -> Optional[Dict]:
    """
    Fetch A-share price from Tencent Finance API.
    Most reliable from overseas servers.
    
    Args:
        symbol: Stock symbol (e.g., 'sh688777' or '688777')
        retry: Number of retries
    
    Returns:
        Price data dictionary or None
    """
    # Add market prefix if not present
    if not symbol.startswith('sh') and not symbol.startswith('sz'):
        if symbol.startswith('6') or symbol.startswith('9'):
            symbol = f'sh{symbol}'
        else:
            symbol = f'sz{symbol}'
    
    url = TENCENT_PRICE_URL.format(symbol=symbol)
    
    for attempt in range(retry):
        try:
            logger.debug(f"Tencent attempt {attempt + 1}/{retry} for {symbol}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            # Decode as GBK (Chinese encoding)
            content = response.content.decode('gbk', errors='ignore').strip()
            match = re.search(r'v_\w+="([^"]+)"', content)
            
            if not match:
                logger.debug("No data match in Tencent response")
                if attempt < retry - 1:
                    time.sleep(2)
                continue
            
            data_str = match.group(1)
            fields = data_str.split('~')
            
            if len(fields) < 10:
                logger.debug("Insufficient fields in Tencent response")
                continue
            
            # Tencent format:
            # 0:type, 1:name, 2:symbol, 3:price, 4:prev_close, 5:open
            # 6:volume, 7:turnover, 31:change, 32:change_percent, 33:high, 34:low
            price_data = {
                'symbol': symbol.replace('sh', '').replace('sz', ''),
                'name': fields[1] if len(fields) > 1 else 'UNKNOWN',
                'current_price': float(fields[3]) if fields[3] else 0.0,
                'previous_close': float(fields[4]) if fields[4] else 0.0,
                'open': float(fields[5]) if fields[5] else 0.0,
                'high': float(fields[33]) if len(fields) > 33 and fields[33] else 0.0,
                'low': float(fields[34]) if len(fields) > 34 and fields[34] else 0.0,
                'volume': float(fields[6]) if len(fields) > 6 and fields[6] else 0.0,
                'turnover': float(fields[7]) if len(fields) > 7 and fields[7] else 0.0,
            }
            
            # Calculate change
            if price_data['previous_close'] > 0:
                price_data['change'] = price_data['current_price'] - price_data['previous_close']
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            else:
                price_data['change'] = 0.0
                price_data['change_percent'] = 0.0
            
            return price_data
            
        except Exception as e:
            logger.warning(f"Tencent attempt {attempt + 1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(2)
            continue
    
    return None


def fetch_price_sina(symbol: str, retry: int = 3) -> Optional[Dict]:
    """
    Fetch A-share price from Sina Finance API.
    Secondary fallback for A-shares.
    
    Args:
        symbol: Stock symbol (e.g., 'sh688777')
        retry: Number of retries
    
    Returns:
        Price data dictionary or None
    """
    # Add market prefix if not present
    if not symbol.startswith('sh') and not symbol.startswith('sz'):
        if symbol.startswith('6') or symbol.startswith('9'):
            symbol = f'sh{symbol}'
        else:
            symbol = f'sz{symbol}'
    
    url = SINA_PRICE_URL.format(symbol=symbol)
    
    for attempt in range(retry):
        try:
            logger.debug(f"Sina attempt {attempt + 1}/{retry} for {symbol}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            content = response.text.strip()
            match = re.search(r'hq_str_\w+="([^"]+)"', content)
            
            if not match:
                logger.debug("No data match in Sina response")
                if attempt < retry - 1:
                    time.sleep(2)
                continue
            
            data_str = match.group(1)
            fields = data_str.split(',')
            
            if len(fields) < 32:
                logger.debug("Insufficient fields in Sina response")
                continue
            
            # Sina format:
            # 0:name, 1:open, 2:close (previous), 3:current, 4:high, 5:low
            # 6:bid, 7:ask, 8:volume (shares), 9:turnover (yuan)
            price_data = {
                'symbol': symbol.replace('sh', '').replace('sz', ''),
                'name': fields[0] if len(fields) > 0 else 'UNKNOWN',
                'current_price': float(fields[3]) if fields[3] else 0.0,
                'previous_close': float(fields[2]) if fields[2] else 0.0,
                'open': float(fields[1]) if fields[1] else 0.0,
                'high': float(fields[4]) if fields[4] else 0.0,
                'low': float(fields[5]) if fields[5] else 0.0,
                'volume': float(fields[8]) if len(fields) > 8 and fields[8] else 0.0,
                'turnover': float(fields[9]) if len(fields) > 9 and fields[9] else 0.0,
            }
            
            # Calculate change
            if price_data['previous_close'] > 0:
                price_data['change'] = price_data['current_price'] - price_data['previous_close']
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            else:
                price_data['change'] = 0.0
                price_data['change_percent'] = 0.0
            
            return price_data
            
        except Exception as e:
            logger.warning(f"Sina attempt {attempt + 1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(2)
            continue
    
    return None


def fetch_price_netease(symbol: str, retry: int = 3) -> Optional[Dict]:
    """
    Fetch A-share price from NetEase (163) Finance API.
    Final fallback for A-shares.
    
    Args:
        symbol: Stock symbol (e.g., 'sh688777')
        retry: Number of retries
    
    Returns:
        Price data dictionary or None
    """
    # NetEase uses symbol with market prefix
    if not symbol.startswith('sh') and not symbol.startswith('sz'):
        if symbol.startswith('6') or symbol.startswith('9'):
            symbol = f'sh{symbol}'
        else:
            symbol = f'sz{symbol}'
    
    netease_symbol = symbol.upper()
    url = NETEASE_PRICE_URL.format(symbol=netease_symbol)
    
    for attempt in range(retry):
        try:
            logger.debug(f"NetEase attempt {attempt + 1}/{retry} for {symbol}")
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            content = response.text.strip()
            # NetEase returns: _ntes_quote_callback({"sh688777": {...}})
            match = re.search(r'\((.+)\)', content)
            
            if not match:
                logger.debug("No data match in NetEase response")
                if attempt < retry - 1:
                    time.sleep(2)
                continue
            
            data = json.loads(match.group(1))
            stock_data = data.get(netease_symbol, {})
            
            if not stock_data:
                logger.debug("No stock data in NetEase JSON")
                continue
            
            price_data = {
                'symbol': symbol.replace('sh', '').replace('sz', ''),
                'name': stock_data.get('name', 'UNKNOWN'),
                'current_price': float(stock_data.get('price', 0)),
                'previous_close': float(stock_data.get('yestclose', 0)),
                'open': float(stock_data.get('open', 0)),
                'high': float(stock_data.get('high', 0)),
                'low': float(stock_data.get('low', 0)),
                'volume': float(stock_data.get('volume', 0)),
                'turnover': float(stock_data.get('turnover', 0)),
            }
            
            # Calculate change
            if price_data['previous_close'] > 0:
                price_data['change'] = price_data['current_price'] - price_data['previous_close']
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            else:
                price_data['change'] = 0.0
                price_data['change_percent'] = 0.0
            
            return price_data
            
        except Exception as e:
            logger.warning(f"NetEase attempt {attempt + 1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(2)
            continue
    
    return None


def fetch_price_futures_zh_realtime(symbol: str, retry: int = 3) -> Optional[Dict]:
    """
    Fetch futures real-time price from AKShare futures_zh_realtime().
    Works from overseas (Sina-based).
    
    Args:
        symbol: Futures symbol (e.g., 'C2605')
        retry: Number of retries
    
    Returns:
        Price data dictionary or None
    """
    for attempt in range(retry):
        try:
            logger.debug(f"Futures realtime attempt {attempt + 1}/{retry} for {symbol}")
            futures_df = ak.futures_zh_realtime()
            
            if futures_df is None or futures_df.empty:
                logger.debug("No futures realtime data returned")
                if attempt < retry - 1:
                    time.sleep(3)
                continue
            
            # Filter for our symbol (case-insensitive)
            symbol_upper = symbol.upper()
            futures_row = futures_df[futures_df['symbol'].str.upper() == symbol_upper]
            
            if futures_row.empty:
                # Try matching continuous contract
                base_symbol = symbol[0].upper() if symbol else ''
                if base_symbol:
                    continuous = futures_df[futures_df['symbol'].str.startswith(base_symbol) & 
                                           futures_df['symbol'].str.endswith('0', na=False)]
                    if not continuous.empty:
                        logger.info(f"Using continuous contract {continuous.iloc[0]['symbol']} instead of {symbol}")
                        futures_row = continuous.head(1)
            
            if futures_row.empty:
                logger.debug(f"Futures symbol {symbol} not found")
                return None
            
            row = futures_row.iloc[0]
            
            price_data = {
                'symbol': symbol,
                'name': str(row.get('name', 'UNKNOWN')),
                'current_price': float(row.get('trade', 0) or row.get('close', 0) or 0),
                'previous_close': float(row.get('preclose', 0) or row.get('pre settlement', 0) or 0),
                'open': float(row.get('open', 0) or 0),
                'high': float(row.get('high', 0) or 0),
                'low': float(row.get('low', 0) or 0),
                'volume': float(row.get('volume', 0) or 0),
                'open_interest': float(row.get('position', 0) or row.get('hold', 0) or 0),
                'change': float(row.get('trade', 0) or row.get('close', 0) or 0) - float(row.get('preclose', 0) or 0),
                'change_percent': float(row.get('changepercent', 0) or 0),
            }
            
            # Calculate change percent if needed
            if price_data['current_price'] > 0 and price_data['previous_close'] > 0 and price_data['change_percent'] == 0:
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            
            return price_data
            
        except Exception as e:
            logger.warning(f"Futures realtime attempt {attempt + 1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(3)
            continue
    
    return None


def fetch_price_futures_zh_daily_sina(symbol: str, retry: int = 3) -> Optional[Dict]:
    """
    Fetch futures daily data from AKShare futures_zh_daily_sina().
    Fallback for realtime data.
    
    Args:
        symbol: Futures symbol (e.g., 'C2605')
        retry: Number of retries
    
    Returns:
        Price data dictionary or None
    """
    for attempt in range(retry):
        try:
            logger.debug(f"Futures Sina daily attempt {attempt + 1}/{retry} for {symbol}")
            symbol_lower = symbol.lower()
            hist_df = ak.futures_zh_daily_sina(symbol=symbol_lower)
            
            if hist_df is None or hist_df.empty:
                logger.debug(f"No historical data from Sina for {symbol}")
                if attempt < retry - 1:
                    time.sleep(3)
                continue
            
            # Use the latest row as current price
            row = hist_df.iloc[-1]
            prev_row = hist_df.iloc[-2] if len(hist_df) > 1 else row
            
            price_data = {
                'symbol': symbol,
                'name': f"{symbol.upper()} 期货",
                'current_price': float(row.get('close', 0) or 0),
                'previous_close': float(prev_row.get('close', 0) or row.get('close', 0) or 0),
                'open': float(row.get('open', 0) or 0),
                'high': float(row.get('high', 0) or 0),
                'low': float(row.get('low', 0) or 0),
                'volume': float(row.get('volume', 0) or 0),
                'open_interest': float(row.get('hold', 0) or 0),
                'change': float(row.get('close', 0) or 0) - float(prev_row.get('close', 0) or 0),
                'change_percent': 0.0,
            }
            
            # Calculate change percent
            if price_data['current_price'] > 0 and price_data['previous_close'] > 0:
                price_data['change'] = price_data['current_price'] - price_data['previous_close']
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            
            return price_data
            
        except Exception as e:
            logger.warning(f"Futures Sina daily attempt {attempt + 1} failed: {e}")
            if attempt < retry - 1:
                time.sleep(3)
            continue
    
    return None


def fetch_news(stock_name: str, limit: int = 5) -> List[Dict]:
    """
    Fetch news using AKShare stock_news_em().
    Works from overseas.
    
    Args:
        stock_name: Stock name in Chinese
        limit: Maximum number of news items to return
    
    Returns:
        List of news items
    """
    news_list = []
    
    try:
        logger.info(f"Fetching news for: {stock_name}")
        
        # Use AKShare news interface (works overseas)
        news_df = ak.stock_news_em(symbol=stock_name)
        
        if news_df is not None and not news_df.empty:
            for _, row in news_df.head(limit).iterrows():
                news_item = {
                    'source': '东方财富',
                    'title': row.get('新闻标题', '无标题'),
                    'time': row.get('发布时间', 'N/A'),
                    'url': row.get('新闻链接', '')
                }
                news_list.append(news_item)
        
        logger.info(f"Found {len(news_list)} news items")
        
    except Exception as e:
        logger.warning(f"Failed to fetch news: {e}")
    
    return news_list


def fetch_historical_prices(symbol: str, days: int = 30, symbol_type: str = "A") -> List[float]:
    """
    Fetch historical price data for MACD calculation.
    
    Args:
        symbol: Stock/futures symbol
        days: Number of days of historical data
        symbol_type: Type of symbol - "A" for A-shares, "futures" for commodity futures
    
    Returns:
        List of closing prices (oldest to newest)
    """
    logger.info(f"Fetching {days} days of historical data for {symbol}")
    
    try:
        if symbol_type == "A":
            # Use AKShare A-share historical data
            from historical import fetch_historical_prices as fetch_hist
            prices = fetch_hist(symbol, days)
        else:
            # Use AKShare futures historical data
            from historical import get_futures_historical_prices as fetch_hist_futures
            prices = fetch_hist_futures(symbol, days)
        
        if prices:
            logger.info(f"Fetched {len(prices)} days of historical data")
        else:
            logger.warning("No historical data available")
        
        return prices
        
    except ImportError as e:
        logger.error(f"Failed to import historical module: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to fetch historical data: {e}")
        return []


if __name__ == "__main__":
    # Test the hybrid fetcher
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("=" * 70)
    print("HYBRID FETCHER TEST - Overseas Server Compatibility")
    print("=" * 70)
    
    print("\n" + "=" * 70)
    print("Test 1: A-share 688777 (中控技术) - Should use Tencent/Sina/NetEase")
    print("=" * 70)
    price_data = fetch_price_data("688777", symbol_type="A", retry=3)
    if price_data:
        print(f"\n✓ SUCCESS - Provider: {price_data.get('provider', 'Unknown')}")
        print(f"  Name: {price_data['name']}")
        print(f"  Price: ¥{price_data['current_price']}")
        print(f"  Change: {price_data['change']:+.2f} ({price_data['change_percent']:+.2f}%)")
        print(f"  Timestamp: {price_data.get('data_timestamp', 'N/A')}")
    else:
        print("\n✗ FAILED to fetch A-share data")
    
    print("\n" + "=" * 70)
    print("Test 2: Futures C2605 (玉米 2605) - Should use AKShare")
    print("=" * 70)
    futures_data = fetch_price_data("C2605", symbol_type="futures", retry=3)
    if futures_data:
        print(f"\n✓ SUCCESS - Provider: {price_data.get('provider', 'Unknown')}")
        print(f"  Name: {futures_data['name']}")
        print(f"  Price: ¥{futures_data['current_price']}")
        print(f"  Change: {futures_data['change']:+.2f} ({futures_data['change_percent']:+.2f}%)")
        print(f"  Timestamp: {futures_data.get('data_timestamp', 'N/A')}")
    else:
        print("\n✗ FAILED to fetch futures data")
    
    print("\n" + "=" * 70)
    print("Test 3: News for 中控技术 - Should use AKShare")
    print("=" * 70)
    news_data = fetch_news("中控技术", limit=3)
    if news_data:
        print(f"\n✓ SUCCESS - Found {len(news_data)} news items")
        for i, news in enumerate(news_data[:3], 1):
            print(f"  {i}. {news['title'][:60]}...")
    else:
        print("\n✗ FAILED to fetch news")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
