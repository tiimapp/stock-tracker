#!/usr/bin/env python3
"""
Fetcher module - Fetches price data from Sina API and news from multiple sources.
"""

import requests
import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Multiple API endpoints for redundancy
# Tencent Finance API (primary - most reliable from overseas VPS)
TENCENT_PRICE_URL = "https://qt.gtimg.cn/q={symbol}"

# Alternative: Sina Finance API
SINA_PRICE_URL = "https://hq.sinajs.cn/list={symbol}"

# Alternative: 163 Finance API
NETEASE_PRICE_URL = "https://api.money.126.net/data/feed/{symbol}"

# Headers to avoid blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Referer': 'https://finance.qq.com/',
    'Connection': 'keep-alive',
}

# News search URLs
SINA_NEWS_SEARCH = "https://search.sina.com.cn/?q={query}&range=title&c=finance"
EASTMONEY_NEWS_SEARCH = "https://search.eastmoney.com/search.aspx?keyword={query}"
SSE_ANNOUNCEMENTS = "https://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/{year}-01/{stock_code}.json"


def fetch_price_data(symbol: str, retry: int = 3, delay: int = 5) -> Optional[Dict]:
    """
    Fetch real-time price data from multiple Chinese finance APIs.
    Tries Tencent first (most reliable), then Sina, then NetEase as fallback.
    
    Args:
        symbol: Stock symbol (e.g., 'sh688777')
        retry: Number of retry attempts per API
        delay: Delay between retries in seconds
    
    Returns:
        Dictionary with price data or None if failed
    """
    # Try multiple APIs in order of preference (Tencent first - works from overseas)
    apis = [
        ('Tencent', fetch_price_tencent),
        ('Sina', fetch_price_sina),
        ('NetEase', fetch_price_netease),
    ]
    
    for api_name, api_func in apis:
        logger.info(f"Trying {api_name} API for {symbol}")
        try:
            price_data = api_func(symbol, retry, delay)
            if price_data:
                logger.info(f"Successfully fetched from {api_name}: {price_data['name']} ¥{price_data['current_price']}")
                return price_data
        except Exception as e:
            logger.warning(f"{api_name} API failed: {e}")
            continue
    
    logger.error(f"All APIs failed for {symbol}")
    return None


def fetch_price_sina(symbol: str, retry: int = 3, delay: int = 5) -> Optional[Dict]:
    """Fetch from Sina Finance API."""
    url = SINA_PRICE_URL.format(symbol=symbol)
    
    for attempt in range(retry):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            content = response.text.strip()
            match = re.search(r'hq_str_\w+="([^"]+)"', content)
            
            if not match:
                continue
            
            data_str = match.group(1)
            fields = data_str.split(',')
            
            if len(fields) < 32:
                continue
            
            return parse_sina_fields(symbol, fields)
            
        except Exception as e:
            if attempt < retry - 1:
                import time
                time.sleep(delay)
            continue
    
    return None


def fetch_price_tencent(symbol: str, retry: int = 3, delay: int = 5) -> Optional[Dict]:
    """
    Fetch from Tencent Finance API.
    Format: v_sh688777="1~中控技术~688777~70.55~77.97~78.10~42112500~20407085~..."
    Fields: type~name~symbol~price~prev_close~open~high~low~volume~turnover~...
    Note: Response is in GBK encoding
    """
    url = TENCENT_PRICE_URL.format(symbol=symbol)
    
    for attempt in range(retry):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            # Decode as GBK (Chinese encoding)
            content = response.content.decode('gbk', errors='ignore').strip()
            match = re.search(r'v_\w+="([^"]+)"', content)
            
            if not match:
                continue
            
            data_str = match.group(1)
            fields = data_str.split('~')
            
            if len(fields) < 10:
                continue
            
            # Tencent format (actual field positions):
            # 0:type, 1:name, 2:symbol, 3:price, 4:prev_close, 5:open
            # 6:volume (shares), 7:turnover (yuan), 8:unknown
            # 31:change, 32:change_percent, 33:high, 34:low
            price_data = {
                'symbol': symbol,
                'name': fields[1] if len(fields) > 1 else 'UNKNOWN',
                'current_price': float(fields[3]) if fields[3] else 0.0,
                'previous_close': float(fields[4]) if fields[4] else 0.0,
                'open': float(fields[5]) if fields[5] else 0.0,
                'high': float(fields[33]) if len(fields) > 33 and fields[33] else 0.0,
                'low': float(fields[34]) if len(fields) > 34 and fields[34] else 0.0,
                'volume': float(fields[6]) if len(fields) > 6 and fields[6] else 0.0,  # Volume in shares
                'turnover': float(fields[7]) if len(fields) > 7 and fields[7] else 0.0,  # Turnover in yuan
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
                import time
                time.sleep(delay)
            continue
    
    return None


def fetch_price_netease(symbol: str, retry: int = 3, delay: int = 5) -> Optional[Dict]:
    """
    Fetch from NetEase (163) Finance API.
    Returns JSON format.
    """
    # NetEase uses different symbol format
    netease_symbol = symbol.upper()
    url = NETEASE_PRICE_URL.format(symbol=netease_symbol)
    
    for attempt in range(retry):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            content = response.text.strip()
            # NetEase returns: _ntes_quote_callback({"sh688777": {...}})
            match = re.search(r'\((.+)\)', content)
            
            if not match:
                continue
            
            data = json.loads(match.group(1))
            stock_data = data.get(netease_symbol, {})
            
            if not stock_data:
                continue
            
            price_data = {
                'symbol': symbol,
                'name': stock_data.get('name', 'UNKNOWN'),
                'current_price': float(stock_data.get('price', 0)),
                'previous_close': float(stock_data.get('yestclose', 0)),
                'open': float(stock_data.get('open', 0)),
                'high': float(stock_data.get('high', 0)),
                'low': float(stock_data.get('low', 0)),
                'volume': float(stock_data.get('volume', 0)),
                'turnover': float(stock_data.get('turnover', 0)),
            }
            
            if price_data['previous_close'] > 0:
                price_data['change'] = price_data['current_price'] - price_data['previous_close']
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            else:
                price_data['change'] = 0.0
                price_data['change_percent'] = 0.0
            
            return price_data
            
        except Exception as e:
            if attempt < retry - 1:
                import time
                time.sleep(delay)
            continue
    
    return None


def parse_sina_fields(symbol: str, fields: list) -> Dict:
    """Parse Sina API fields into price data dictionary."""
    price_data = {
        'symbol': symbol,
        'name': fields[0],
        'current_price': float(fields[1]) if fields[1] else 0.0,
        'previous_close': float(fields[2]) if fields[2] else 0.0,
        'open': float(fields[3]) if fields[3] else 0.0,
        'high': float(fields[4]) if fields[4] else 0.0,
        'low': float(fields[5]) if fields[5] else 0.0,
        'volume': float(fields[8]) if fields[8] else 0.0,
        'turnover': float(fields[9]) if fields[9] else 0.0,
        'date': fields[30] if len(fields) > 30 else '',
        'time': fields[31] if len(fields) > 31 else '',
    }
    
    if price_data['previous_close'] > 0:
        price_data['change'] = price_data['current_price'] - price_data['previous_close']
        price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
    else:
        price_data['change'] = 0.0
        price_data['change_percent'] = 0.0
    
    return price_data


def fetch_news_sina(stock_name: str, limit: int = 5) -> List[Dict]:
    """
    Fetch news from Sina Finance.
    
    Args:
        stock_name: Stock name in Chinese
        limit: Maximum number of news items to return
    
    Returns:
        List of news items
    """
    news_list = []
    query = f"{stock_name} 新浪财经"
    url = SINA_NEWS_SEARCH.format(query=query)
    
    try:
        logger.info(f"Searching Sina Finance news for: {query}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Extract news from HTML (simplified parsing)
        # Look for news titles and timestamps
        title_pattern = r'<h[23][^>]*>([^<]+)</h[23]>'
        time_pattern = r'<span[^>]*class="time"[^>]*>([^<]+)</span>'
        
        titles = re.findall(title_pattern, response.text)
        times = re.findall(time_pattern, response.text)
        
        for i, title in enumerate(titles[:limit]):
            news_item = {
                'source': 'Sina 财经',
                'title': title.strip(),
                'time': times[i].strip() if i < len(times) else 'N/A',
                'url': url
            }
            news_list.append(news_item)
        
        logger.info(f"Found {len(news_list)} news items from Sina Finance")
        
    except Exception as e:
        logger.warning(f"Failed to fetch Sina Finance news: {e}")
    
    return news_list


def fetch_news_eastmoney(stock_name: str, limit: int = 5) -> List[Dict]:
    """
    Fetch news from 东方财富网.
    
    Args:
        stock_name: Stock name in Chinese
        limit: Maximum number of news items to return
    
    Returns:
        List of news items
    """
    news_list = []
    query = f"{stock_name} 东方财富网"
    url = EASTMONEY_NEWS_SEARCH.format(query=query)
    
    try:
        logger.info(f"Searching Eastmoney news for: {query}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Simplified HTML parsing for news items
        title_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        
        matches = re.findall(title_pattern, response.text)
        for href, title in matches[:limit]:
            if stock_name in title and 'news' in href.lower():
                news_item = {
                    'source': '东方财富',
                    'title': title.strip(),
                    'time': 'N/A',
                    'url': href if href.startswith('http') else f"https://search.eastmoney.com{href}"
                }
                news_list.append(news_item)
        
        logger.info(f"Found {len(news_list)} news items from Eastmoney")
        
    except Exception as e:
        logger.warning(f"Failed to fetch Eastmoney news: {e}")
    
    return news_list


def fetch_news_sse(stock_code: str, year: int = 2026, limit: int = 5) -> List[Dict]:
    """
    Fetch official announcements from Shanghai Stock Exchange.
    
    Args:
        stock_code: Stock code (e.g., '688777')
        year: Year for announcements
        limit: Maximum number of announcements to return
    
    Returns:
        List of announcement items
    """
    news_list = []
    # Simplified - in production would use actual SSE API
    logger.info(f"Checking SSE announcements for {stock_code}")
    
    # Placeholder - SSE requires more complex API interaction
    # For now, return empty list with log message
    logger.info("SSE announcements require specialized API - skipped for now")
    
    return news_list


def fetch_all_news(stock_name: str, stock_code: str) -> Dict[str, List[Dict]]:
    """
    Fetch news from all sources.
    
    Args:
        stock_name: Stock name in Chinese
        stock_code: Stock code (e.g., '688777')
    
    Returns:
        Dictionary with news from each source
    """
    logger.info(f"Fetching all news for {stock_name}")
    
    news = {
        'sse': fetch_news_sse(stock_code),
        'sina': fetch_news_sina(stock_name),
        'eastmoney': fetch_news_eastmoney(stock_name)
    }
    
    total = sum(len(v) for v in news.values())
    logger.info(f"Total news items collected: {total}")
    
    return news


def fetch_historical_prices(symbol: str, days: int = 30) -> List[float]:
    """
    Fetch historical price data for MACD calculation.
    Imports from historical module.
    
    Args:
        symbol: Stock symbol
        days: Number of days of historical data
    
    Returns:
        List of closing prices (oldest to newest)
    """
    logger.info(f"Fetching {days} days of historical data for {symbol}")
    
    try:
        from historical import fetch_historical_prices as fetch_hist
        prices = fetch_hist(symbol, days)
        
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
    # Test the fetcher
    logging.basicConfig(level=logging.INFO)
    
    print("Testing fetcher module...")
    price_data = fetch_price_data("sh688777")
    if price_data:
        print(f"\nPrice Data:")
        for key, value in price_data.items():
            print(f"  {key}: {value}")
    
    print("\nFetching news...")
    news = fetch_all_news("中控技术", "688777")
    for source, items in news.items():
        print(f"\n{source}: {len(items)} items")
        for item in items[:2]:
            print(f"  - {item['title']}")
