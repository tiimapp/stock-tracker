#!/usr/bin/env python3
"""
Reporter module - Formats markdown report and sends to Discord via OpenClaw message tool.
"""

import logging
import subprocess
import json
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Discord channel ID from configuration
DEFAULT_CHANNEL_ID = "1475775915844960428"


def format_price_section(price_data: Dict) -> str:
    """
    Format price information section.
    
    Args:
        price_data: Price data dictionary from fetcher
    
    Returns:
        Formatted markdown string
    """
    if not price_data:
        return "💰 价格信息\n- 数据暂缺"
    
    # Format numbers
    current = price_data.get('current_price', 0)
    change = price_data.get('change', 0)
    change_pct = price_data.get('change_percent', 0)
    
    # Color coding for change
    if change > 0:
        change_str = f"+{change:.2f} (+{change_pct:.2f}%) 📈"
    elif change < 0:
        change_str = f"{change:.2f} ({change_pct:.2f}%) 📉"
    else:
        change_str = f"0.00 (0.00%) ➡️"
    
    # Format volume (convert to 万手)
    volume = price_data.get('volume', 0)
    volume_wan = volume / 10000  # Convert to 万手
    
    # Format turnover (convert to 亿)
    turnover = price_data.get('turnover', 0)
    turnover_yi = turnover / 100000000  # Convert to 亿
    
    section = f"""💰 价格信息
- 当前价：¥{current:.2f}
- 涨跌：{change_str}
- 今开：¥{price_data.get('open', 0):.2f}
- 最高：¥{price_data.get('high', 0):.2f}
- 最低：¥{price_data.get('low', 0):.2f}
- 成交量：{volume_wan:.2f} 万手
- 成交额：{turnover_yi:.2f} 亿"""
    
    return section


def format_trend_section(trend_data: Dict) -> str:
    """
    Format trend analysis section.
    
    Args:
        trend_data: Trend data from analyzer
    
    Returns:
        Formatted markdown string
    """
    if not trend_data or trend_data.get('direction') == 'UNKNOWN':
        return "📈 趋势分析\n- 数据不足，无法计算趋势"
    
    direction = trend_data.get('direction', 'FLAT')
    symbol = trend_data.get('symbol', '→')
    change_pct = trend_data.get('change_percent', 0)
    
    # Map direction to Chinese
    direction_cn = {
        'UP': '上涨',
        'DOWN': '下跌',
        'FLAT': '盘整'
    }.get(direction, '盘整')
    
    section = f"""📈 趋势分析
- 5 日趋势：{symbol} {direction_cn} ({change_pct:+.2f}%)
- 区间最高：¥{trend_data.get('high', 0):.2f}
- 区间最低：¥{trend_data.get('low', 0):.2f}"""
    
    return section


def format_macd_section(macd_data: Dict) -> str:
    """
    Format MACD signal section.
    
    Args:
        macd_data: MACD data from analyzer
    
    Returns:
        Formatted markdown string
    """
    if not macd_data or macd_data.get('error'):
        return "📊 MACD 信号\n- 数据不足，无法计算 MACD"
    
    signal = macd_data.get('signal', 'HOLD')
    signal_icon = {
        'BUY': '🟢',
        'SELL': '🔴',
        'HOLD': '⚪'
    }.get(signal, '⚪')
    
    # Signal explanation
    signal_explanation = {
        'BUY': '金叉信号，短期均线向上穿越长期均线，看涨',
        'SELL': '死叉信号，短期均线向下穿越长期均线，看跌',
        'HOLD': '无明显交叉信号，保持观望'
    }.get(signal, '信号不明')
    
    dif = macd_data.get('dif', 0)
    dea = macd_data.get('dea', 0)
    macd = macd_data.get('macd', 0)
    
    section = f"""📊 MACD 信号
- 状态：{signal_icon} {signal}
- DIF: {dif:.4f}
- DEA: {dea:.4f}
- MACD 柱：{macd:.4f}
- 说明：{signal_explanation}"""
    
    return section


def format_news_section(news_data: Dict[str, List[Dict]], limit: int = 3) -> str:
    """
    Format news section.
    
    Args:
        news_data: News data from fetcher (dict with source keys)
        limit: Max news items per source
    
    Returns:
        Formatted markdown string
    """
    if not news_data:
        return "📰 重要新闻\n- 暂无新闻"
    
    sections = []
    
    # Source name mapping
    source_names = {
        'sse': '【上交所公告】',
        'sina': '【Sina 财经】',
        'eastmoney': '【东方财富】'
    }
    
    for source, items in news_data.items():
        if not items:
            continue
        
        source_name = source_names.get(source, f'【{source}】')
        sections.append(source_name)
        
        for i, item in enumerate(items[:limit], 1):
            title = item.get('title', '无标题')
            time = item.get('time', 'N/A')
            
            # Truncate long titles
            if len(title) > 60:
                title = title[:57] + '...'
            
            sections.append(f"{i}. {title} - {time}")
        
        sections.append("")  # Empty line between sources
    
    if not sections:
        return "📰 重要新闻\n- 暂无新闻"
    
    return "📰 重要新闻\n" + "\n".join(sections)


def format_attention_section() -> str:
    """
    Format "things to watch tomorrow" section.
    
    Returns:
        Formatted markdown string
    """
    # Static content for now - could be enhanced with calendar/events
    section = """🔍 明日关注
- 关注大盘走势及成交量变化
- 留意公司公告及行业动态
- 注意宏观经济数据发布"""
    
    return section


def format_report(price_data: Dict, analysis: Dict, news_data: Dict) -> str:
    """
    Format complete stock report.
    
    Args:
        price_data: Price data from fetcher
        analysis: Analysis data from analyzer
        news_data: News data from fetcher
    
    Returns:
        Complete formatted markdown report
    """
    logger.info("Formatting report...")
    
    stock_name = price_data.get('name', '中控技术')
    symbol = price_data.get('symbol', 'sh688777')
    stock_code = symbol.replace('sh', '').replace('sz', '')
    
    # Header
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d %H:%M')
    
    header = f"""📊 {stock_name} ({stock_code}) 日报
━━━━━━━━━━━━━━━━━━━━━━
📅 {date_str}
"""
    
    # Build report sections
    sections = [
        header,
        format_price_section(price_data),
        "",
        format_trend_section(analysis.get('trend', {})),
        "",
        format_macd_section(analysis.get('macd', {})),
        "",
        format_news_section(news_data),
        "",
        format_attention_section(),
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"数据来源：Sina 财经、东方财富网、上交所",
        f"生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    
    report = "\n".join(sections)
    
    logger.info(f"Report formatted ({len(report)} characters)")
    return report


def send_to_discord(report: str, channel_id: str = None) -> bool:
    """
    Send report to Discord channel via OpenClaw message tool.
    
    Args:
        report: Formatted markdown report
        channel_id: Discord channel ID (optional, uses default if not provided)
    
    Returns:
        True if successful, False otherwise
    """
    if channel_id is None:
        channel_id = DEFAULT_CHANNEL_ID
    
    logger.info(f"Sending report to Discord channel {channel_id}")
    
    try:
        # Use OpenClaw message tool via subprocess
        # Command: openclaw message send --target <channel_id> --message "<report>"
        
        cmd = [
            'openclaw', 'message', 'send',
            '--target', channel_id,
            '--message', report
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info("Report sent to Discord successfully")
            return True
        else:
            logger.error(f"Failed to send report: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Timeout sending report to Discord")
        return False
    except Exception as e:
        logger.error(f"Error sending report to Discord: {e}")
        return False


def send_report_via_tool(report: str, channel_id: str = None) -> bool:
    """
    Alternative: Send report using the message tool directly.
    This is called from main.py which has access to the message tool.
    
    Args:
        report: Formatted markdown report
        channel_id: Discord channel ID
    
    Returns:
        True if successful
    """
    if channel_id is None:
        channel_id = DEFAULT_CHANNEL_ID
    
    logger.info(f"Preparing to send report to Discord channel {channel_id}")
    
    # Return the report and channel_id for main.py to send
    # This function is a placeholder - actual sending happens in main.py
    return True


def save_report(report: str, filepath: str = None) -> str:
    """
    Save report to file.
    
    Args:
        report: Formatted report
        filepath: Output file path (optional)
    
    Returns:
        Path to saved file
    """
    if filepath is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = f"logs/report_{timestamp}.md"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Report saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        return None


if __name__ == "__main__":
    # Test the reporter
    logging.basicConfig(level=logging.INFO)
    
    print("Testing reporter module...")
    
    # Sample data
    price_data = {
        'name': '中控技术',
        'symbol': 'sh688777',
        'current_price': 45.67,
        'previous_close': 44.50,
        'change': 1.17,
        'change_percent': 2.63,
        'open': 44.80,
        'high': 46.00,
        'low': 44.50,
        'volume': 12345678,
        'turnover': 567890123
    }
    
    analysis = {
        'trend': {
            'direction': 'UP',
            'symbol': '↑',
            'change_percent': 3.45,
            'high': 46.50,
            'low': 43.20
        },
        'macd': {
            'signal': 'BUY',
            'dif': 0.5234,
            'dea': 0.4123,
            'macd': 0.2222
        }
    }
    
    news_data = {
        'sina': [
            {'title': '中控技术发布新产品，市场反响热烈', 'time': '10:30'},
            {'title': '科创板今日走势分析', 'time': '09:15'}
        ],
        'eastmoney': [
            {'title': '中控技术：工业自动化龙头持续成长', 'time': '08:00'}
        ]
    }
    
    report = format_report(price_data, analysis, news_data)
    print("\n" + "=" * 60)
    print(report)
    print("=" * 60)
