#!/usr/bin/env python3
"""
Main entry point - Orchestrates fetch → analyze → report pipeline.

Usage:
    python src/main.py [--config <path>] [--test]
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Optional

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetcher import fetch_price_data, fetch_all_news, fetch_historical_prices
from analyzer import analyze_stock
from reporter import format_report, save_report

# Configure logging
def setup_logging(log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_file: Path to log file (optional)
        level: Logging level
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger('stock_tracker')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    return logger


def load_config(config_path: str = None) -> Dict:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Default config path
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'settings.json'
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logging.info(f"Configuration loaded from {config_path}")
        return config
        
    except FileNotFoundError:
        logging.warning(f"Config file not found: {config_path}, using defaults")
        return get_default_config()
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        return get_default_config()


def get_default_config() -> Dict:
    """
    Get default configuration.
    
    Returns:
        Default configuration dictionary
    """
    return {
        'schedule': {
            'time': '15:30',
            'timezone': 'Asia/Shanghai'
        },
        'delivery': {
            'channel': 'discord',
            'channel_id': '1475775915844960428'
        },
        'data_sources': {
            'price': {
                'provider': 'sina',
                'endpoint': 'https://hq.sinajs.cn/list={symbol}'
            }
        },
        'analysis': {
            'macd': {
                'ema_short': 12,
                'ema_long': 26,
                'ema_signal': 9,
                'history_days': 30
            },
            'trend': {
                'days': 5
            }
        },
        'retry': {
            'max_attempts': 3,
            'delay_seconds': 5
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/stock-tracker.log'
        }
    }


def load_stocks(config_path: str = None) -> list:
    """
    Load stock symbols from configuration.
    
    Args:
        config_path: Path to stocks.json
    
    Returns:
        List of stock configurations
    """
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'stocks.json'
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            stocks_config = json.load(f)
        
        stocks = stocks_config.get('stocks', [])
        logging.info(f"Loaded {len(stocks)} stock(s) from configuration")
        return stocks
        
    except Exception as e:
        logging.error(f"Failed to load stocks config: {e}")
        # Default stock
        return [{
            'symbol': 'sh688777',
            'name': '中控技术',
            'active': True
        }]


def run_pipeline(stock: Dict, config: Dict, logger: logging.Logger) -> Dict:
    """
    Run the complete fetch → analyze → report pipeline.
    
    Args:
        stock: Stock configuration
        config: Application configuration
        logger: Logger instance
    
    Returns:
        Pipeline result dictionary
    """
    symbol = stock.get('symbol', 'sh688777')
    stock_name = stock.get('name', '中控技术')
    stock_code = symbol.replace('sh', '').replace('sz', '')
    
    result = {
        'success': False,
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'error': None
    }
    
    try:
        # Step 1: Fetch price data
        logger.info(f"Step 1: Fetching price data for {stock_name} ({symbol})")
        retry_config = config.get('retry', {})
        price_data = fetch_price_data(
            symbol,
            retry=retry_config.get('max_attempts', 3),
            delay=retry_config.get('delay_seconds', 5)
        )
        
        if not price_data:
            raise Exception("Failed to fetch price data after retries")
        
        result['price_data'] = price_data
        logger.info(f"Price data fetched: ¥{price_data.get('current_price', 0):.2f}")
        
        # Step 2: Fetch historical data (for MACD calculation)
        logger.info("Step 2: Fetching historical data")
        historical_prices = fetch_historical_prices(
            symbol,
            days=config.get('analysis', {}).get('macd', {}).get('history_days', 30)
        )
        
        # If no historical data, use current price as placeholder
        if not historical_prices:
            logger.warning("No historical data available, using current price only")
            # MACD will handle this gracefully
        
        # Step 3: Fetch news
        logger.info("Step 3: Fetching news")
        news_data = fetch_all_news(stock_name, stock_code)
        result['news_data'] = news_data
        
        # Step 4: Analyze
        logger.info("Step 4: Performing technical analysis")
        analysis = analyze_stock(price_data, historical_prices)
        result['analysis'] = analysis
        
        # Step 5: Format report
        logger.info("Step 5: Formatting report")
        report = format_report(price_data, analysis, news_data)
        result['report'] = report
        
        # Step 6: Save report to file
        logger.info("Step 6: Saving report")
        report_path = save_report(report)
        result['report_path'] = report_path
        
        # Step 7: Send to Discord (via message tool)
        logger.info("Step 7: Preparing to send to Discord")
        channel_id = config.get('delivery', {}).get('channel_id', '1475775915844960428')
        result['channel_id'] = channel_id
        result['ready_to_send'] = True
        
        result['success'] = True
        logger.info("Pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        result['error'] = str(e)
        result['success'] = False
    
    return result


def send_to_discord(report: str, channel_id: str) -> bool:
    """
    Send report to Discord using the message tool.
    This function is called by the OpenClaw integration.
    
    Args:
        report: Formatted report
        channel_id: Discord channel ID
    
    Returns:
        True if successful
    """
    # This will be called from main session with the message tool
    # For now, just log that we're ready to send
    logging.info(f"Report ready to send to Discord channel {channel_id}")
    logging.info(f"Report length: {len(report)} characters")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Stock Tracker - Daily Report Generator')
    parser.add_argument('--config', '-c', help='Path to settings.json')
    parser.add_argument('--stocks', '-s', help='Path to stocks.json')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode (no Discord send)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_config = config.get('logging', {})
    log_level = 'DEBUG' if args.verbose else log_config.get('level', 'INFO')
    log_file = log_config.get('file', 'logs/stock-tracker.log')
    logger = setup_logging(log_file, log_level)
    
    logger.info("=" * 60)
    logger.info("Stock Tracker - Daily Report Generator")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Load stocks
    stocks = load_stocks(args.stocks)
    
    # Process each stock
    all_results = []
    for stock in stocks:
        if not stock.get('active', True):
            logger.info(f"Skipping inactive stock: {stock.get('symbol')}")
            continue
        
        logger.info(f"\nProcessing: {stock.get('name')} ({stock.get('symbol')})")
        result = run_pipeline(stock, config, logger)
        all_results.append(result)
        
        if result['success']:
            logger.info(f"✓ Successfully processed {stock.get('symbol')}")
            
            # Print report preview
            if result.get('report'):
                print("\n" + "=" * 60)
                print(result['report'][:500] + "..." if len(result['report']) > 500 else result['report'])
                print("=" * 60)
            
            # Send to Discord (unless test mode)
            if not args.test and result.get('ready_to_send'):
                logger.info("Sending report to Discord...")
                # In actual execution, this would use the message tool
                # For CLI execution, we use subprocess
                from reporter import send_to_discord as send_report
                send_report(result['report'], result['channel_id'])
        else:
            logger.error(f"✗ Failed to process {stock.get('symbol')}: {result.get('error')}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline Summary")
    logger.info("=" * 60)
    success_count = sum(1 for r in all_results if r['success'])
    logger.info(f"Total: {len(all_results)}, Success: {success_count}, Failed: {len(all_results) - success_count}")
    logger.info(f"End time: {datetime.now().isoformat()}")
    
    # Return exit code
    return 0 if success_count == len(all_results) else 1


if __name__ == "__main__":
    sys.exit(main())
