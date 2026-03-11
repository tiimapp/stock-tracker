# Stock Tracker 📊

Automated daily stock and futures monitoring system for Chinese markets.

## Overview

This project provides automated monitoring and reporting for:
- **A-Share Stocks** (科创板) - Daily reports at 15:30
- **DCE Corn Futures** (C2605 玉米 2605) - Hourly reports during trading hours + daily summary

All reports are delivered to Discord automatically.

---

## 📈 A-Share Stock Monitor

### Target Stock

| Field | Value |
|-------|-------|
| **Name** | 中控技术 |
| **Symbol** | 688777 (SH) |
| **Market** | 科创板 (STAR Market) |

### Schedule

- **Run Time:** 15:30 Asia/Shanghai (daily, trading days)
- **Delivery:** Discord #show-me-the-money channel

### Features

- ✅ Real-time price data from Sina Finance API
- ✅ MACD buy/sell signal analysis
- ✅ News aggregation from multiple sources
- ✅ Automated daily reports via Discord

### Project Structure (A-Share)

```
stock-tracker/
├── src/
│   ├── fetcher.py      # Data fetching (price + news)
│   ├── analyzer.py     # Technical analysis (MACD, trends)
│   ├── reporter.py     # Report generation & Discord delivery
│   └── main.py         # Entry point
├── config/
│   ├── stocks.json     # Stock symbols to track
│   └── settings.json   # Configuration
└── logs/               # Runtime logs
```

---

## 🌽 C2605 Corn Futures Monitor

### Contract Details

| Field | Value |
|-------|-------|
| **Name** | 玉米 2605 (Corn May 2026) |
| **Symbol** | C2605 |
| **Exchange** | DCE (大连商品交易所) |

### Trading Hours (Asia/Shanghai UTC+8)

| Session | Time |
|---------|------|
| Morning 1 | 09:00 - 10:15 |
| Morning 2 | 10:30 - 11:30 |
| Afternoon | 13:30 - 15:00 |
| Night Session | ⚠️ **UNCERTAIN** (21:00-23:00, under verification) |

**Trading Days:** Monday - Friday (excluding Chinese public holidays)

### Schedule

| Report Type | Time | Frequency |
|-------------|------|-----------|
| Hourly Report | 09:00, 10:00, 11:00, 14:00, 15:00 | During trading hours |
| Daily Summary | 15:30 | After market close |
| Night Report | 21:00, 22:00, 23:00 | ⚠️ Pending verification |

### Features

- ✅ Real-time price data from Sina Finance API
- ✅ Fallback to AKShare historical data
- ✅ Trading day detection (Chinese holiday calendar)
- ✅ Night session status verification (daily)
- ✅ Hourly intraday reports during trading
- ✅ Daily summary with OHLCV data
- ✅ Automated Discord delivery

### Project Files (C2605)

```
stock-tracker/
├── c2605_monitor.py              # Main monitoring script ⭐
├── trading_time_checker.py       # Trading time detection module
├── dce_trading_verifier.py       # Night session verifier
├── c2605_config.json             # Configuration file
├── c2605_test.py                 # Test script
│
├── fetchers/
│   └── c2605_tavily_fetcher.py   # Tavily price fetcher
│
├── docs/
│   ├── C2605-data-sources.md     # Data source documentation ⭐
│   ├── C2605-architecture.md     # Architecture documentation ⭐
│   ├── C2605-night-trading-research.md  # Night trading research
│   └── tavily-verification-example.py   # Tavily example
│
├── logs/
│   └── c2605_YYYYMMDD.log        # Daily logs
│
└── memory/
    └── dce-trading-state.json    # Night session state cache
```

---

## 🚀 Quick Start

### Install Dependencies

```bash
cd stock-tracker
pip install akshare requests tavily-python pandas numpy
```

### Configure Environment

```bash
# Add to ~/.openclaw/.env for Tavily API (optional, for night trading verification)
export TAVILY_API_KEY='tvly-xxxxxxxxxxxxxxxxxxxx'
```

### Manual Testing

```bash
# Test C2605 hourly report
python3 c2605_monitor.py --type hourly

# Test C2605 daily summary
python3 c2605_monitor.py --type daily

# Test trading time detection
python3 trading_time_checker.py

# Test night trading verification
python3 dce_trading_verifier.py --json

# Full test mode
python3 c2605_monitor.py --test
```

---

## ⏰ Scheduling

### Option 1: Cron Jobs

```bash
# Edit crontab
crontab -e

# Add C2605 monitoring tasks
0 9,10,11,14,15 * * 1-5 /home/admin/.openclaw/workspace/stock-tracker/c2605_monitor.py --type hourly
30 15 * * 1-5 /home/admin/.openclaw/workspace/stock-tracker/c2605_monitor.py --type daily

# Optional: Night reports (pending verification)
0 21,22,23 * * 1-5 /home/admin/.openclaw/workspace/stock-tracker/c2605_monitor.py --type hourly
```

### Option 2: Systemd Timers (Recommended for C2605)

```bash
# Install systemd timers (requires sudo)
cd stock-tracker
sudo ./install-systemd-timers.sh

# Verify installation
systemctl list-timers | grep c2605

# Check status
systemctl status c2605-monitor.timer
systemctl status c2605-monitor-daily.timer

# View logs
journalctl -u c2605-monitor.service -f
journalctl -u c2605-monitor-daily.service -f
```

### Option 3: OpenClaw Heartbeat Integration

The C2605 monitor integrates with OpenClaw's heartbeat system:

- **Daily trading day verification** - First heartbeat of the day
- **Night trading status verification** - Daily check via Tavily/Perplexity
- **Automatic report scheduling** - Based on trading day status

**State files:**
- `workspace/memory/heartbeat-state.json` - Trading day status
- `stock-tracker/memory/dce-trading-state.json` - Night session status

**Check status:**
```bash
# Trading day verification
python3 heartbeat_trading_check.py --json

# Night trading verification
cd stock-tracker && python3 dce_trading_verifier.py --json
```

---

## 📊 Data Sources

### C2605 Price Data

| Priority | Source | Type | Usage |
|----------|--------|------|-------|
| **P0** | 新浪财经 | HTTP API | Real-time prices |
| **P1** | AKShare | Python Library | Historical/fallback |
| **P4** | Mock Data | Local | Testing/degradation |

### Night Trading Verification

| Source | Type | Usage |
|--------|------|-------|
| **Tavily AI Search** | AI Search API | Daily verification |
| **Perplexity Search** | AI Search | Cross-validation |
| **DCE Official Website** | Official | Authoritative (blocked overseas) |

**See detailed documentation:** [docs/C2605-data-sources.md](docs/C2605-data-sources.md)

---

## 🏗️ Architecture

### C2605 Monitoring Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Cron/Timer  │────→│ c2605_      │────→│ Discord     │
│ Trigger     │     │ monitor.py  │     │ Report      │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
           ┌─────────────┐ ┌─────────────┐
           │ Trading     │ │ Data        │
           │ Time Check  │ │ Fetch       │
           │ (P0→P1→P4)  │ │             │
           └─────────────┘ └─────────────┘
```

### Night Trading Verification Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Daily       │────→│ dce_trading │────→│ State File  │
│ Heartbeat   │     │ _verifier.py│     │ Update      │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
           ┌─────────────┐ ┌─────────────┐
           │ Tavily AI   │ │ Perplexity  │
           │ Search      │ │ Search      │
           └─────────────┘ └─────────────┘
```

**See detailed documentation:** [docs/C2605-architecture.md](docs/C2605-architecture.md)

---

## 📝 Configuration

### C2605 Configuration (c2605_config.json)

```json
{
  "symbol": "C2605",
  "symbol_name": "玉米 2605",
  "exchange": "DCE",
  "discord_channel_id": "1475775915844960428",
  "trading_hours": {
    "sessions": [
      {"start": "09:00", "end": "10:15"},
      {"start": "10:30", "end": "11:30"},
      {"start": "13:30", "end": "15:00"}
    ]
  },
  "report_preferences": {
    "hourly_report": true,
    "daily_summary": true,
    "include_chart": false
  }
}
```

### Chinese Holidays 2026

The system includes a built-in Chinese holiday calendar for 2026:

- New Year's Day: Jan 1-3
- Spring Festival: Feb 17-23
- Qingming Festival: Apr 5-7
- Labor Day: May 1-5
- Dragon Boat Festival: Jun 19-21
- Mid-Autumn Festival: Sep 25-27
- National Day: Oct 1-8

**Location:** `trading_time_checker.py` - `DCE_HOLIDAYS_2026`

---

## 🛠️ Troubleshooting

### No Data from Price Sources

```bash
# Check internet connection
curl -I https://hq.sinajs.cn/list=fu_C2605

# Test AKShare
python3 -c "import akshare as ak; print(ak.futures_zh_daily_sina('C2605'))"

# Check logs
tail -f stock-tracker/logs/c2605_$(date +%Y%m%d).log
```

### Night Trading Verification Fails

```bash
# Check Tavily API key
echo $TAVILY_API_KEY

# Force re-verification
cd stock-tracker
python3 dce_trading_verifier.py --force --json

# Check state file
cat stock-tracker/memory/dce-trading-state.json
```

### Reports Not Sending to Discord

- Verify channel ID in `c2605_config.json`
- Check Discord bot permissions
- Review logs for delivery errors
- Test OpenClaw gateway status

### Timer Not Running

```bash
# Check timer status
systemctl list-timers | grep c2605

# Restart timers
sudo systemctl restart c2605-monitor.timer
sudo systemctl restart c2605-monitor-daily.timer

# Check logs
journalctl -u c2605-monitor.service --since today
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [docs/C2605-data-sources.md](docs/C2605-data-sources.md) | Data source comparison and priorities |
| [docs/C2605-architecture.md](docs/C2605-architecture.md) | System architecture and flows |
| [docs/C2605-night-trading-research.md](docs/C2605-night-trading-research.md) | Night trading research report |
| [docs/tavily-verification-example.py](docs/tavily-verification-example.py) | Tavily API usage example |

---

## 📊 Report Formats

### Hourly Report (盘中快报)

```
🌽 C2605 玉米期货 实时快报 📈

合约：玉米 2605 (C2605)
当前价格：¥2450.00
涨跌：+15.00 (+0.62%)
开盘：¥2440.00
最高：¥2455.00
最低：¥2435.00
成交量：50,000

更新时间：2026-03-11 10:00:00
数据来源：sina_realtime

下次报告：1 小时后 (交易时段内)
```

### Daily Summary (每日总结)

```
🌽 C2605 玉米期货 每日总结 📈

合约：玉米 2605 (C2605)
收盘价：¥2450.00
日涨跌：+15.00 (+0.62%)
今日区间：¥2435.00 - ¥2455.00
成交量：50,000

交易日期：2026-03-11
数据来源：sina_realtime

明日报告：09:00 (开盘后)
```

---

## 🔒 Security Notes

- **API Keys:** Store in `~/.openclaw/.env`, never commit to git
- **Discord Channel ID:** Keep private, do not share publicly
- **State Files:** Contain trading decisions, handle with care

---

## 📈 Future Enhancements

- [ ] Add support for more futures contracts (soybean meal, iron ore, etc.)
- [ ] Technical indicator analysis (MACD, KDJ, RSI)
- [ ] Price alert notifications
- [ ] Historical data database
- [ ] Multi-exchange support (SHFE, CZCE)
- [ ] Web dashboard
- [ ] REST API exposure

---

## 👥 Author

Created for tiim🐮 - Discord Server: 1238361831328845896

## 📄 License

Private project

---

*Last updated: 2026-03-11*
*System version: 1.0*
