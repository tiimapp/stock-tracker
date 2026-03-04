#!/usr/bin/env python3
"""
Analyzer module - Technical analysis with MACD, trend detection, and support/resistance levels.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# MACD parameters (standard values)
EMA_SHORT = 12
EMA_LONG = 26
EMA_SIGNAL = 9


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        series: Price series
        period: EMA period
    
    Returns:
        EMA series
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_macd(close_prices: List[float]) -> Dict:
    """
    Calculate MACD indicator.
    
    MACD Line = EMA(12) - EMA(26)
    Signal Line = EMA(9) of MACD Line
    MACD Histogram = (MACD Line - Signal Line) * 2
    
    For limited data, use shorter periods:
    - If < 26 days: Use EMA(6) - EMA(13) with Signal EMA(5)
    
    Args:
        close_prices: List of closing prices (oldest to newest)
    
    Returns:
        Dictionary with MACD values and signal
    """
    if len(close_prices) < 10:
        logger.warning(f"Insufficient data for MACD: {len(close_prices)} < 10")
        return {
            'dif': None,
            'dea': None,
            'macd': None,
            'signal': 'HOLD',
            'error': 'Insufficient data (need at least 10 data points)'
        }
    
    # Adjust parameters for limited data
    if len(close_prices) < EMA_LONG:
        # Use shorter periods for limited data
        short_period = min(6, len(close_prices) // 2)
        long_period = min(13, len(close_prices) - 1)
        signal_period = min(5, short_period // 2)
        logger.info(f"Using adjusted MACD periods: {short_period}/{long_period}/{signal_period}")
    else:
        short_period = EMA_SHORT
        long_period = EMA_LONG
        signal_period = EMA_SIGNAL
    
    try:
        # Convert to pandas Series
        series = pd.Series(close_prices)
        
        # Calculate EMAs with adjusted or standard periods
        ema_short = calculate_ema(series, short_period)
        ema_long = calculate_ema(series, long_period)
        
        # MACD Line (DIF)
        dif = ema_short - ema_long
        
        # Signal Line (DEA)
        dea = calculate_ema(dif, signal_period)
        
        # MACD Histogram
        macd_hist = (dif - dea) * 2
        
        # Get latest values
        current_dif = dif.iloc[-1]
        current_dea = dea.iloc[-1]
        current_macd = macd_hist.iloc[-1]
        
        # Get previous values for signal detection
        prev_dif = dif.iloc[-2] if len(dif) > 1 else current_dif
        prev_dea = dea.iloc[-2] if len(dea) > 1 else current_dea
        
        # Detect signal
        signal = detect_macd_signal(current_dif, current_dea, prev_dif, prev_dea)
        
        result = {
            'dif': float(current_dif),
            'dea': float(current_dea),
            'macd': float(current_macd),
            'signal': signal,
            'ema_short': float(ema_short.iloc[-1]),
            'ema_long': float(ema_long.iloc[-1])
        }
        
        logger.info(f"MACD calculated: DIF={result['dif']:.4f}, DEA={result['dea']:.4f}, Signal={signal}")
        return result
        
    except Exception as e:
        logger.error(f"MACD calculation failed: {e}")
        return {
            'dif': None,
            'dea': None,
            'macd': None,
            'signal': 'HOLD',
            'error': str(e)
        }


def detect_macd_signal(current_dif: float, current_dea: float, 
                       prev_dif: float, prev_dea: float) -> str:
    """
    Detect MACD buy/sell signal based on crossovers.
    
    BUY: DIF crosses above DEA (golden cross)
    SELL: DIF crosses below DEA (death cross)
    HOLD: No crossover
    
    Args:
        current_dif: Current DIF value
        current_dea: Current DEA value
        prev_dif: Previous DIF value
        prev_dea: Previous DEA value
    
    Returns:
        Signal string: 'BUY', 'SELL', or 'HOLD'
    """
    # Golden cross: DIF was below DEA, now above
    if prev_dif <= prev_dea and current_dif > current_dea:
        return 'BUY'
    
    # Death cross: DIF was above DEA, now below
    if prev_dif >= prev_dea and current_dif < current_dea:
        return 'SELL'
    
    # Maintain current state
    if current_dif > current_dea:
        return 'BUY'  # Bullish but no new crossover
    elif current_dif < current_dea:
        return 'SELL'  # Bearish but no new crossover
    else:
        return 'HOLD'


def calculate_trend(prices: List[float], days: int = 5) -> Dict:
    """
    Calculate price trend over specified days.
    
    Args:
        prices: List of closing prices (oldest to newest)
        days: Number of days to analyze
    
    Returns:
        Dictionary with trend information
    """
    if len(prices) < days:
        logger.warning(f"Insufficient data for trend: {len(prices)} < {days}")
        return {
            'direction': 'UNKNOWN',
            'change': 0.0,
            'change_percent': 0.0,
            'error': 'Insufficient data'
        }
    
    try:
        # Get prices for the period
        recent_prices = prices[-days:]
        
        start_price = recent_prices[0]
        end_price = recent_prices[-1]
        
        change = end_price - start_price
        change_percent = (change / start_price) * 100 if start_price > 0 else 0
        
        # Determine direction
        if change > 0.5:  # Threshold to avoid noise
            direction = 'UP'
            symbol = '↑'
        elif change < -0.5:
            direction = 'DOWN'
            symbol = '↓'
        else:
            direction = 'FLAT'
            symbol = '→'
        
        result = {
            'direction': direction,
            'symbol': symbol,
            'change': change,
            'change_percent': change_percent,
            'start_price': start_price,
            'end_price': end_price,
            'high': max(recent_prices),
            'low': min(recent_prices)
        }
        
        logger.info(f"5-day trend: {symbol} {change_percent:+.2f}%")
        return result
        
    except Exception as e:
        logger.error(f"Trend calculation failed: {e}")
        return {
            'direction': 'UNKNOWN',
            'change': 0.0,
            'change_percent': 0.0,
            'error': str(e)
        }


def calculate_support_resistance(prices: List[float], volume: List[float] = None) -> Dict:
    """
    Calculate support and resistance levels.
    
    Uses recent highs/lows and volume-weighted average price.
    
    Args:
        prices: List of prices (recent data)
        volume: Optional volume data
    
    Returns:
        Dictionary with support and resistance levels
    """
    if len(prices) < 5:
        return {
            'support': None,
            'resistance': None,
            'error': 'Insufficient data'
        }
    
    try:
        recent_prices = prices[-20:] if len(prices) >= 20 else prices
        
        # Simple approach: use recent low/high
        support = min(recent_prices)
        resistance = max(recent_prices)
        
        # Calculate pivot point
        pivot = (support + resistance) / 2
        
        result = {
            'support': support,
            'resistance': resistance,
            'pivot': pivot,
            'range': resistance - support
        }
        
        logger.info(f"Support/Resistance: ¥{support:.2f} / ¥{resistance:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"Support/Resistance calculation failed: {e}")
        return {
            'support': None,
            'resistance': None,
            'error': str(e)
        }


def analyze_stock(price_data: Dict, historical_prices: List[float] = None) -> Dict:
    """
    Perform complete technical analysis on a stock.
    
    Args:
        price_data: Current price data from fetcher
        historical_prices: List of historical closing prices
    
    Returns:
        Dictionary with all analysis results
    """
    logger.info("Starting technical analysis...")
    
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'symbol': price_data.get('symbol', 'UNKNOWN'),
        'name': price_data.get('name', 'UNKNOWN'),
        'current_price': price_data.get('current_price', 0),
    }
    
    # Prepare price series for analysis
    close_prices = historical_prices.copy() if historical_prices else []
    
    # Add current price if we have historical data
    if close_prices and price_data.get('current_price'):
        # Don't duplicate if already in the list
        if close_prices[-1] != price_data['current_price']:
            close_prices.append(price_data['current_price'])
    elif price_data.get('current_price'):
        # Only current price available
        close_prices = [price_data['current_price']]
    
    # MACD Analysis
    analysis['macd'] = calculate_macd(close_prices)
    
    # Trend Analysis
    analysis['trend'] = calculate_trend(close_prices, days=5)
    
    # Support/Resistance
    analysis['levels'] = calculate_support_resistance(close_prices)
    
    # Generate summary
    analysis['summary'] = generate_analysis_summary(analysis)
    
    logger.info("Technical analysis complete")
    return analysis


def generate_analysis_summary(analysis: Dict) -> str:
    """
    Generate a human-readable summary of the analysis.
    
    Args:
        analysis: Complete analysis dictionary
    
    Returns:
        Summary string
    """
    parts = []
    
    # MACD signal
    macd = analysis.get('macd', {})
    signal = macd.get('signal', 'HOLD')
    signal_icon = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(signal, '⚪')
    parts.append(f"MACD 信号：{signal_icon} {signal}")
    
    # Trend
    trend = analysis.get('trend', {})
    if trend.get('direction') != 'UNKNOWN':
        trend_symbol = trend.get('symbol', '→')
        change_pct = trend.get('change_percent', 0)
        parts.append(f"5 日趋势：{trend_symbol} {change_pct:+.2f}%")
    
    # Levels
    levels = analysis.get('levels', {})
    if levels.get('support') and levels.get('resistance'):
        parts.append(f"支撑/阻力：¥{levels['support']:.2f} / ¥{levels['resistance']:.2f}")
    
    return " | ".join(parts)


if __name__ == "__main__":
    # Test the analyzer
    logging.basicConfig(level=logging.INFO)
    
    print("Testing analyzer module...")
    
    # Test with sample data
    test_prices = [100.0, 101.0, 100.5, 102.0, 103.0, 102.5, 104.0, 105.0, 104.5, 106.0,
                   107.0, 106.5, 108.0, 109.0, 108.5, 110.0, 111.0, 110.5, 112.0, 113.0,
                   112.5, 114.0, 115.0, 114.5, 116.0, 117.0, 116.5, 118.0, 119.0, 118.5]
    
    print("\nMACD Calculation:")
    macd_result = calculate_macd(test_prices)
    for key, value in macd_result.items():
        print(f"  {key}: {value}")
    
    print("\nTrend Analysis:")
    trend_result = calculate_trend(test_prices, days=5)
    for key, value in trend_result.items():
        print(f"  {key}: {value}")
    
    print("\nSupport/Resistance:")
    levels_result = calculate_support_resistance(test_prices)
    for key, value in levels_result.items():
        print(f"  {key}: {value}")
