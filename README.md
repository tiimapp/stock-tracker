# Stock Tracker 📊

Automated daily stock report system for Chinese A-shares (科创板) and commodity futures.

## ⚠️ Important: Data Delay Notice

**This system uses AKShare cost-free data sources.** All price data has a **15-20 minute delay** compared to real-time market data. This is acceptable for daily reports but should not be used for real-time trading decisions.

## Overview

This project fetches stock/futures data and news via AKShare, analyzes trends with MACD signals, and delivers a concise daily report to Discord.

## Target Symbols

### A-Shares
- **Name:** 中控技术
- **Symbol:** 688777 (SH)
- **Market:** 科创板 (STAR Market)

### Commodity Futures
- **Name:** 玉米 2605
- **Symbol:** C2605
- **Market:** DCE (大连商品交易所)

## Schedule

- **Run Time:** 15:30 Asia/Shanghai (daily, trading days)
- **Delivery:** Discord #show-me-the-money channel

## Features

- ✅ **Cost-free data** via AKShare (no paid API subscriptions)
- ✅ Real-time price data from 东方财富 and 新浪财经
- ✅ MACD buy/sell signal analysis
- ✅ News aggregation from multiple sources (A-shares only)
- ✅ Automated daily reports via Discord
- ✅ **Data freshness indicators** (timestamp + delay warning)
- ✅ **Fallback logic** (multiple AKShare sources per symbol type)
- ✅ Support for both A-shares and commodity futures
- ✅ GitHub version control

## Project Structure

```
stock-tracker/
├── README.md           # This file
├── REPORT_SPEC.md      # Detailed report specification
├── src/
│   ├── fetcher.py      # Data fetching via AKShare (price + news)
│   ├── historical.py   # Historical data via AKShare
│   ├── analyzer.py     # Technical analysis (MACD, trends)
│   ├── reporter.py     # Report generation & Discord delivery
│   └── main.py         # Entry point
├── config/
│   ├── stocks.json     # Stock/futures symbols to track
│   └── settings.json   # Configuration (time, channels, etc.)
├── logs/               # Runtime logs
└── docs/               # Additional documentation
```

## Quick Start

```bash
# Install dependencies
pip install akshare pandas numpy

# Run manually
python src/main.py

# Test mode (no Discord send)
python src/main.py --test

# Check logs
tail -f logs/stock-tracker.log
```

## Configuration

Edit `config/stocks.json`:

```json
{
  "stocks": [
    {
      "symbol": "688777",
      "name": "中控技术",
      "type": "A",
      "active": true
    },
    {
      "symbol": "C2605",
      "name": "玉米 2605",
      "type": "futures",
      "active": true
    }
  ]
}
```

### Symbol Types

| Type | Description | Example |
|------|-------------|---------|
| `A` | Chinese A-shares | `688777` |
| `futures` | Commodity futures | `C2605` |

## Data Sources

### Hybrid Fetcher Architecture (v3.0+)

This system uses a **hybrid data fetching approach** optimized for overseas server deployment:

| Data Type | A-Shares | Futures | News |
|-----------|----------|---------|------|
| **Primary Source** | Tencent 财经 (direct API) | AKShare (futures_zh_realtime) | AKShare (stock_news_em) |
| **Fallback 1** | Sina 财经 (direct API) | AKShare (futures_zh_daily_sina) | - |
| **Fallback 2** | NetEase 财经 (direct API) | - | - |

**Why Hybrid?**
- **A-shares**: Direct API calls (Tencent/Sina/NetEase) work reliably from overseas servers, avoiding AKShare connectivity issues with 东方财富
- **Futures**: AKShare's Sina-based APIs work well from overseas
- **News**: AKShare's 东方财富 news API works from overseas

### Price Data

| Symbol Type | Primary Source | Fallback Sources |
|-------------|---------------|------------------|
| A-shares | Tencent 财经 (qt.gtimg.cn) | Sina 财经 → NetEase 财经 |
| Futures | AKShare 期货实时行情 | AKShare 新浪财经期货历史 |

### Connectivity Notes

✅ **Overseas Server Compatible**: The hybrid fetcher is specifically designed to work from overseas VPS/servers where direct access to Chinese financial APIs may be restricted or slow.

**Fallback Logic:**
- Automatic retry with exponential backoff (up to 3 attempts per provider)
- Multi-provider chain: If Tencent fails, tries Sina, then NetEase
- Comprehensive logging shows which provider succeeded
- Graceful degradation when historical data unavailable

### Historical Data

| Symbol Type | Source | Function |
|-------------|--------|----------|
| A-shares | 东方财富 | stock_zh_a_hist() |
| Futures | 新浪财经 | futures_zh_daily_sina() |

### News Data

| Source | Function |
|--------|----------|
| Sina 财经 | stock_news_em() |
| 东方财富 | stock_news_em() |

## Data Freshness

All reports include:
- **Data timestamp:** When the data was fetched
- **Delay warning:** ⚠️ 免费数据延迟约 15-20 分钟

This delay is inherent to free data sources and is acceptable for:
- ✅ Daily summary reports
- ✅ Long-term trend analysis
- ✅ Portfolio monitoring

This delay is **NOT** acceptable for:
- ❌ Real-time trading decisions
- ❌ High-frequency trading
- ❌ Arbitrage opportunities

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

## Migration History

### v3.0 - Hybrid Fetcher for Overseas Servers (2026-03-05)
- Implemented hybrid fetcher (`hybrid_fetcher.py`) for overseas server compatibility
- **A-shares**: Direct API calls (Tencent → Sina → NetEase) bypass AKShare
- **Futures**: AKShare (Sina-based, works overseas)
- **News**: AKShare `stock_news_em()` (works overseas)
- Automatic provider fallback with logging
- Optimized for VPS deployment outside China

### v2.0 - AKShare Migration (2026-03-05)
- Migrated from direct API calls to AKShare library
- Added support for commodity futures
- Implemented data freshness indicators
- Added fallback logic for multiple data sources
- **Breaking change:** All data now has 15-20min delay (cost-free)

### v1.0 - Initial Release (2026-03-01)
- Basic A-share tracking
- Direct API calls to Tencent/Sina/NetEase
- MACD analysis
- Discord integration

## Troubleshooting

### No data returned
1. Check if the symbol is correct (e.g., `688777` not `sh688777` for A-shares)
2. Verify the market is open (no data on weekends/holidays)
3. Check logs for specific error messages

### AKShare import error
```bash
pip install --upgrade akshare
```

### Data appears stale
- This is expected! Free data has 15-20min delay
- Reports run at 15:30, after market close (15:00), so data is final

## Author

Created for tiim🐮 - Discord Server: 1238361831328845896

## License

Private project

## References

- AKShare Documentation: https://akshare.akfamily.xyz/
- 东方财富：https://www.eastmoney.com/
- 新浪财经：https://finance.sina.com.cn/
