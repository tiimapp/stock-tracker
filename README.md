# Stock Tracker 📊

Automated daily stock report system for Chinese A-shares (科创板).

## Overview

This project fetches real-time stock data and news, analyzes trends with MACD signals, and delivers a concise daily report to Discord.

## Target Stock

- **Name:** 中控技术
- **Symbol:** 688777 (SH)
- **Market:** 科创板 (STAR Market)

## Schedule

- **Run Time:** 15:30 Asia/Shanghai (daily, trading days)
- **Delivery:** Discord #show-me-the-money channel

## Features

- ✅ Real-time price data from Sina Finance API
- ✅ MACD buy/sell signal analysis
- ✅ News aggregation from multiple sources
- ✅ Automated daily reports via Discord
- ✅ GitHub version control

## Project Structure

```
stock-tracker/
├── README.md           # This file
├── REPORT_SPEC.md      # Detailed report specification
├── src/
│   ├── fetcher.py      # Data fetching (price + news)
│   ├── analyzer.py     # Technical analysis (MACD, trends)
│   ├── reporter.py     # Report generation & Discord delivery
│   └── main.py         # Entry point
├── config/
│   ├── stocks.json     # Stock symbols to track
│   └── settings.json   # Configuration (time, channels, etc.)
├── logs/               # Runtime logs
└── docs/               # Additional documentation
```

## Quick Start

```bash
# Install dependencies
pip install requests pandas numpy

# Run manually
python src/main.py

# Check logs
tail -f logs/stock-tracker.log
```

## Configuration

Edit `config/settings.json`:

```json
{
  "schedule": "15:30",
  "timezone": "Asia/Shanghai",
  "discord_channel": "1475775915844960428",
  "stocks": ["sh688777"]
}
```

## Data Sources

| Type | Provider | Endpoint |
|------|----------|----------|
| Price | Sina Finance | `https://hq.sinajs.cn/list={symbol}` |
| News | Sina Finance | Web search + fetch |
| News | 东方财富网 | Web search + fetch |
| News | 上交所公告 | Web search |

## MACD Signal Logic

```
BUY:  MACD line crosses above Signal line (golden cross)
SELL: MACD line crosses below Signal line (death cross)
HOLD: No crossover, maintain previous signal
```

## Cron Job

Managed via OpenClaw cron system:
- Job runs daily at 15:30 Shanghai time
- Automatic retry on failure
- Logs stored in `logs/` directory

## Author

Created for tiim🐮 - Discord Server: 1238361831328845896

## License

Private project
