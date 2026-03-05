# AKShare Migration Audit Report

**Date:** 2026-03-05  
**Auditor:** Code_G (Subagent)  
**Task:** Phase 1.1 & 1.2 - Codebase Audit & API Documentation  
**Repo:** https://github.com/tiimapp/stock-tracker

---

## 1. Repository Structure Overview

```
stock-tracker/
├── README.md                    # Project documentation with API source details
├── REPORT_SPEC.md               # Report format specification
├── PROJECT_PLAN.md              # Development roadmap (in docs/)
├── run_report.sh                # Shell script to run reports
├── config/
│   ├── stocks.json              # Stock/futures symbols configuration
│   └── settings.json            # Application settings
├── src/
│   ├── main.py                  # Entry point, orchestrates pipeline
│   ├── fetcher.py               # Price & news data fetching (AKShare)
│   ├── historical.py            # Historical price data fetching (AKShare)
│   ├── analyzer.py              # Technical analysis (MACD, trends)
│   ├── reporter.py              # Report formatting & Discord delivery
│   └── __pycache__/             # Python bytecode cache
├── logs/
│   ├── stock-tracker.log        # Runtime logs
│   └── report_*.md              # Generated reports
└── docs/
    └── PROJECT_PLAN.md          # Development roadmap
```

**Total Source Files:** 5 Python files  
**Total Config Files:** 2 JSON files  
**Lines of Code:** ~1,800 lines (excluding comments/blank lines)

---

## 2. Current API Integrations (AKShare-Based)

### 2.1 Price Data APIs

| File | Function | AKShare API | Symbol Type | Description |
|------|----------|-------------|-------------|-------------|
| `fetcher.py` | `fetch_price_zh_a_spot_em()` | `ak.stock_zh_a_spot_em()` | A-shares | Fetches all A-share real-time quotes, filters by symbol |
| `fetcher.py` | `fetch_price_futures_zh_realtime()` | `ak.futures_zh_realtime()` | Futures | Fetches all futures real-time quotes, filters by symbol |
| `fetcher.py` | `fetch_price_futures_zh_daily_sina()` | `ak.futures_zh_daily_sina()` | Futures | Fallback: Fetches futures daily historical data from Sina |
| `historical.py` | `fetch_historical_prices_zh_a()` | `ak.stock_zh_a_hist()` | A-shares | Fetches A-share historical daily prices (前复权) |
| `historical.py` | `fetch_historical_prices_futures()` | `ak.futures_zh_daily_sina()` | Futures | Fetches futures historical daily prices |

### 2.2 News Data APIs

| File | Function | AKShare API | Symbol Type | Description |
|------|----------|-------------|-------------|-------------|
| `fetcher.py` | `fetch_news_sina()` | `ak.stock_news_em()` | A-shares | Fetches news from Sina Finance |
| `fetcher.py` | `fetch_news_eastmoney()` | `ak.stock_news_em()` | A-shares | Fetches news from 东方财富 |

**Note:** News is only fetched for A-shares, not futures.

### 2.3 Data Flow Diagram

```
main.py (Entry Point)
    │
    ├──→ fetcher.fetch_price_data()
    │       ├──→ fetch_price_zh_a_spot_em() → ak.stock_zh_a_spot_em()
    │       ├──→ fetch_price_futures_zh_realtime() → ak.futures_zh_realtime()
    │       └──→ fetch_price_futures_zh_daily_sina() → ak.futures_zh_daily_sina()
    │
    ├──→ fetcher.fetch_historical_prices()
    │       ├──→ fetch_historical_prices_zh_a() → ak.stock_zh_a_hist()
    │       └──→ get_futures_historical_prices() → ak.futures_zh_daily_sina()
    │
    ├──→ fetcher.fetch_all_news()
    │       ├──→ fetch_news_sina() → ak.stock_news_em()
    │       └──→ fetch_news_eastmoney() → ak.stock_news_em()
    │
    ├──→ analyzer.analyze_stock() → MACD, trend analysis (no external API)
    │
    └──→ reporter.format_report() → Markdown formatting
            └──→ reporter.send_to_discord() → OpenClaw message tool
```

---

## 3. Tracked Symbols & Markets

### 3.1 Currently Tracked Symbols (from `config/stocks.json`)

| Symbol | Name | Type | Market | Sector | Status |
|--------|------|------|--------|--------|--------|
| `688777` | 中控技术 | A-share | 科创板 (STAR Market) | 工业自动化 | ✅ Active |
| `C2605` | 玉米 2605 | Futures | DCE (大连商品交易所) | 农产品期货 | ✅ Active |

### 3.2 Symbol Format Requirements

| Type | Format | Example | Notes |
|------|--------|---------|-------|
| A-shares | 6-digit code only | `688777` | No market prefix (sh/sz) needed |
| Futures | Commodity code + contract month | `C2605` | C=Corn, 2605=May 2026 |

### 3.3 Supported Markets (by AKShare API)

**A-Shares:**
- 沪深 A 股 (Shanghai & Shenzhen)
- 科创板 (STAR Market)
- 创业板 (ChiNext)

**Futures:**
- DCE (大连商品交易所) - e.g., 玉米 C, 豆粕 M
- SHFE (上海期货交易所) - e.g., 铜 CU, 铝 AL
- CZCE (郑州商品交易所) - e.g., 棉花 CF, 白糖 SR
- CFFEX (中国金融期货交易所) - e.g., 股指期货 IF

---

## 4. API Call Details

### 4.1 `ak.stock_zh_a_spot_em()` - A-Share Real-Time Quotes

**Location:** `fetcher.py:fetch_price_zh_a_spot_em()`  
**Purpose:** Fetch real-time price data for all A-shares, then filter by symbol  
**Response Columns Used:**
- `代码` → symbol
- `名称` → name
- `最新价` → current_price
- `昨收` → previous_close
- `今开` → open
- `最高` → high
- `最低` → low
- `成交量` → volume (converted from 手 to shares)
- `成交额` → turnover
- `涨跌额` → change
- `涨跌幅` → change_percent

**Retry Logic:** Up to 5 attempts with exponential backoff (5s, 10s, 15s max)  
**Fallback:** Uses historical data if realtime fails

---

### 4.2 `ak.futures_zh_realtime()` - Futures Real-Time Quotes

**Location:** `fetcher.py:fetch_price_futures_zh_realtime()`  
**Purpose:** Fetch real-time futures data  
**Response Columns Used:**
- `symbol` → contract symbol
- `name` → contract name
- `trade` or `close` → current_price
- `preclose` or `pre settlement` → previous_close
- `open`, `high`, `low` → OHLC
- `volume` → trading volume
- `position` or `hold` → open_interest
- `changepercent` → change_percent

**Special Logic:** Falls back to continuous contract (e.g., C0) if specific contract not found

---

### 4.3 `ak.futures_zh_daily_sina()` - Futures Historical Data

**Location:** `fetcher.py:fetch_price_futures_zh_daily_sina()`, `historical.py:fetch_historical_prices_futures()`  
**Purpose:** Fetch historical daily futures prices (fallback for realtime)  
**Symbol Format:** Lowercase (e.g., `c2605` not `C2605`)  
**Response Columns Used:**
- `date` → date
- `open`, `high`, `low`, `close` → OHLC
- `volume` → volume
- `hold` → open_interest

---

### 4.4 `ak.stock_zh_a_hist()` - A-Share Historical Data

**Location:** `historical.py:fetch_historical_prices_zh_a()`  
**Purpose:** Fetch historical daily A-share prices  
**Parameters:**
- `symbol`: Stock code (e.g., `688777`)
- `period`: "daily"
- `start_date`, `end_date`: YYYYMMDD format
- `adjust`: "qfq" (前复权 - forward adjusted)

**Response Columns Used:**
- `日期` → date
- `开盘` → open
- `收盘` → close
- `最高` → high
- `最低` → low
- `成交量` → volume
- `成交额` → turnover

**Retry Logic:** Up to 5 attempts with exponential backoff

---

### 4.5 `ak.stock_news_em()` - Stock News

**Location:** `fetcher.py:fetch_news_sina()`, `fetcher.py:fetch_news_eastmoney()`  
**Purpose:** Fetch news articles for a stock  
**Parameters:** `symbol` (stock name in Chinese)  
**Response Columns Used:**
- `新闻标题` → title
- `发布时间` → time
- `新闻链接` → url

**Note:** Both functions use the same API but label sources differently

---

## 5. Technical Analysis (No External API)

**File:** `src/analyzer.py`

### 5.1 MACD Calculation

**Function:** `calculate_macd()`  
**Standard Parameters:**
- EMA Short: 12 days
- EMA Long: 26 days
- EMA Signal: 9 days

**Adjusted Parameters (if < 26 days data):**
- EMA Short: 6 days
- EMA Long: 13 days
- EMA Signal: 5 days

**Signal Detection:**
- **BUY:** DIF crosses above DEA (golden cross)
- **SELL:** DIF crosses below DEA (death cross)
- **HOLD:** No crossover

### 5.2 Trend Analysis

**Function:** `calculate_trend()`  
**Period:** 5 days (configurable)  
**Output:** Direction (UP/DOWN/FLAT), change %, high/low

### 5.3 Support/Resistance

**Function:** `calculate_support_resistance()`  
**Method:** Recent 20-day high/low

---

## 6. Configuration & Dependencies

### 6.1 Python Dependencies

```python
import akshare as ak        # Financial data library
import pandas as pd         # Data manipulation
import numpy as np          # Numerical operations
```

**Required Packages:**
- `akshare` (latest)
- `pandas`
- `numpy`

### 6.2 Configuration Files

**`config/stocks.json`:**
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

**`config/settings.json`:**
- Schedule: 15:30 Asia/Shanghai (Mon-Fri)
- Discord channel: #show-me-the-money (ID: 1475775915844960428)
- MACD parameters: 12/26/9
- Retry: 3 attempts, 5s delay

---

## 7. Data Freshness & Limitations

### 7.1 Data Delay

**Warning:** ⚠️ 免费数据延迟约 15-20 分钟

**Reason:** AKShare free data sources update every 15-20 minutes  
**Acceptable For:**
- ✅ Daily summary reports
- ✅ Long-term trend analysis
- ✅ Portfolio monitoring

**NOT Acceptable For:**
- ❌ Real-time trading decisions
- ❌ High-frequency trading
- ❌ Arbitrage

### 7.2 Known Issues

1. **东方财富 API Connectivity:** May experience timeouts from some networks
   - Mitigation: 5 retry attempts with exponential backoff
   - Fallback: Historical data

2. **Symbol Format Sensitivity:**
   - A-shares: No prefix needed
   - Futures: Case-sensitive (uppercase for realtime, lowercase for Sina)

---

## 8. Recommended AKShare Equivalents (Migration Reference)

**Note:** This codebase is ALREADY using AKShare (migrated in v2.0 on 2026-03-05).  
The following table shows the current AKShare APIs in use:

| Feature | Current AKShare API | Status |
|---------|---------------------|--------|
| A-share realtime | `ak.stock_zh_a_spot_em()` | ✅ In use |
| A-share historical | `ak.stock_zh_a_hist()` | ✅ In use |
| Futures realtime | `ak.futures_zh_realtime()` | ✅ In use |
| Futures historical | `ak.futures_zh_daily_sina()` | ✅ In use |
| Stock news | `ak.stock_news_em()` | ✅ In use |

**No migration needed** - the codebase has already completed the AKShare migration.

---

## 9. Files Summary

### 9.1 Files Making API Calls

| File | API Type | AKShare Functions Used |
|------|----------|------------------------|
| `src/fetcher.py` | Price, News | `stock_zh_a_spot_em()`, `futures_zh_realtime()`, `futures_zh_daily_sina()`, `stock_news_em()` |
| `src/historical.py` | Historical | `stock_zh_a_hist()`, `futures_zh_daily_sina()` |
| `src/main.py` | Orchestration | Imports from fetcher/historical |
| `src/analyzer.py` | None | Pure calculation (pandas/numpy) |
| `src/reporter.py` | None | Formatting only (Discord via OpenClaw) |

### 9.2 Files NOT Making External API Calls

| File | Purpose |
|------|---------|
| `src/analyzer.py` | Technical analysis (MACD, trends) |
| `src/reporter.py` | Report formatting, Discord delivery |
| `src/main.py` | Pipeline orchestration (calls other modules) |
| `config/*.json` | Configuration data |

---

## 10. Conclusions & Recommendations

### 10.1 Current State

✅ **AKShare Migration: COMPLETE**  
This codebase has already been migrated to AKShare (v2.0, 2026-03-05). All data sources are AKShare-based.

### 10.2 API Coverage

| Data Type | Coverage | Notes |
|-----------|----------|-------|
| A-share prices | ✅ Complete | Realtime + historical |
| Futures prices | ✅ Complete | Realtime + historical |
| News | ✅ Complete | Sina + Eastmoney |
| Technical analysis | ✅ Complete | MACD, trends, support/resistance |

### 10.3 Recommendations for Future Enhancements

1. **Add More Symbols:**
   - Consider adding major indices (上证指数，深证成指)
   - Add more liquid futures contracts (螺纹钢 RB, 铁矿石 I, 原油 SC)

2. **Improve Error Handling:**
   - Add circuit breaker pattern for repeated API failures
   - Implement health check endpoint

3. **Data Caching:**
   - Cache API responses to reduce rate limiting
   - Implement Redis or file-based caching

4. **Enhanced Analysis:**
   - Add RSI, Bollinger Bands, KDJ indicators
   - Add volume analysis (OBV, volume-weighted average price)

5. **Multi-Stock Reports:**
   - Consolidate multiple stocks into single daily report
   - Add portfolio-level summary

---

## 11. Audit Metadata

- **Audit Duration:** ~5 minutes
- **Files Analyzed:** 7 (5 Python, 2 JSON)
- **Lines Reviewed:** ~1,800
- **AKShare APIs Identified:** 5 unique functions
- **Symbols Tracked:** 2 (1 A-share, 1 futures)

---

**End of Audit Report**
