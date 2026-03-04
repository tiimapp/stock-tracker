# Stock Tracker - Project Plan 📋

## Status: Phase 1-4 Complete ✅ | Phase 5 (Futures) Planned 🚧

---

## Phase 1: Project Setup (DONE ✅)

- [x] Create project folder structure
- [x] Write README.md
- [x] Write REPORT_SPEC.md (detailed specification)
- [x] Create config files (stocks.json, settings.json)
- [x] Document MACD logic and data sources
- [x] Define report format and delivery schedule

**Deliverables:**
- ✅ `/home/admin/.openclaw/workspace/stock-tracker/` created
- ✅ All documentation in place
- ✅ Git initialized

---

## Phase 2: Core Development (DONE ✅)

### 2.1 Data Fetcher (`src/fetcher.py`)

- [x] Implement Sina API price fetcher
- [x] Parse Sina API response (comma-separated values)
- [x] Implement news search (Sina + 东方财富 + 上交所)
- [x] Handle retries and error cases
- [x] Cache responses for debugging

### 2.2 Analyzer (`src/analyzer.py`)

- [x] Calculate MACD (12, 26, 9 EMA)
- [x] Detect buy/sell signals (golden/death cross)
- [x] Calculate 5-day trend
- [x] Identify support/resistance levels
- [x] Generate technical analysis summary

### 2.3 Reporter (`src/reporter.py`)

- [x] Format report in markdown
- [x] Insert price data, MACD signals, news
- [x] Send to Discord via OpenClaw message tool
- [x] Handle delivery failures gracefully

### 2.4 Main Entry Point (`src/main.py`)

- [x] Load configuration
- [x] Orchestrate fetch → analyze → report pipeline
- [x] Log all operations
- [x] Handle exceptions and edge cases

**Evidence:** 6 successful report runs on 2026-03-03 for 中控技术 (688777)

---

## Phase 3: Integration & Testing (DONE ✅)

### 3.1 Manual Testing

- [x] Run script manually
- [x] Verify price data accuracy
- [x] Verify MACD calculation
- [x] Verify news fetching
- [x] Test Discord delivery

### 3.2 Cron Setup ⏳

- [ ] Create OpenClaw cron job
- [ ] Set schedule: 15:30 Asia/Shanghai (Mon-Fri)
- [ ] Test cron trigger
- [ ] Verify automatic delivery

### 3.3 Monitoring ⏳

- [ ] Set up log rotation
- [ ] Add error notifications
- [ ] Create health check endpoint (optional)

---

## Phase 4: GitHub & Deployment (DONE ✅)

### 4.1 GitHub Setup

- [x] Git repo initialized
- [x] .gitignore created
- [x] Pushed to GitHub: https://github.com/tiimapp/stock-tracker

### 4.2 Documentation

- [ ] Add LICENSE file
- [ ] Update README with GitHub badge
- [ ] Add contribution guidelines (optional)

---

## Timeline

| Phase | Tasks | Owner | Status |
|-------|-------|-------|--------|
| 1 | Project setup | ClawBot | ✅ Done |
| 2 | Core development | Code_G | ✅ Done |
| 3 | Integration & testing | Both | ✅ Done |
| 4 | GitHub & deployment | ClawBot | ✅ Done |
| 5 | Futures support | Code_G | 📋 Planned |

---

## Next Steps

1. **Add LICENSE file** (optional)
2. **Update README with GitHub badge**
3. **Deploy cron job** for daily reports (15:30 Asia/Shanghai, Mon-Fri)
4. **Phase 5: Futures Support** (see below)

---

## Open Questions

- [ ] Any additional stocks to track?
- [ ] Any specific news keywords to filter?
- [ ] Which futures to track first? (棉花 CF, 螺纹钢 RB, 铁矿石 I, etc.)

---

## Phase 5: Futures Support (PLANNED 📋)

**Status:** Capability verified by Code_G (2026-03-04)

### 5.1 Research & API Selection ✅

- [x] Verify current fetcher capabilities (stocks only)
- [x] Research futures API endpoints (Sina, Tencent, AKShare)
- [x] Document required changes
- [x] Create capability report: `FUTURES_CAPABILITY_REPORT.md`

### 5.2 Core Implementation (TODO)

**Recommended Approach:** Use AKShare library (handles all Chinese exchanges)

- [ ] Add AKShare dependency to requirements
- [ ] Create `src/futures_fetcher.py`
- [ ] Add futures symbol format detection (czce_, DCE_, SHF_, etc.)
- [ ] Implement futures-specific field parsing:
  - Open interest (持仓量)
  - Settlement price (结算价)
  - Change vs settlement (涨跌)
- [ ] Update `src/main.py` to support both stocks and futures

### 5.3 Configuration (TODO)

- [ ] Create `config/futures.json` (futures contracts to track)
- [ ] Update `config/settings.json` with futures options
- [ ] Add exchange prefix mapping (czce_, DCE_, SHF_, CFFEX_)

### 5.4 Reporting (TODO)

- [ ] Create futures report template (similar to stock reports)
- [ ] Add futures-specific analysis (basis, term structure)
- [ ] Update Discord delivery for futures reports

### 5.5 Testing & Deployment (TODO)

- [ ] Test with CF2605 (棉花) and other liquid contracts
- [ ] Verify data accuracy against exchange official data
- [ ] Set up separate cron job for futures (different market hours)
- [ ] Document usage in README

**Estimated Effort:** 15-22 hours (full implementation)
**Quick Path (AKShare only):** 4-6 hours

**API Endpoints Verified:**
| API | Symbol Format | Status |
|-----|---------------|--------|
| Sina | `czce_cf2605` | ✅ Works |
| Tencent | `CF2605` | ⚠️ Needs verification |
| AKShare | `CF2605` | ✅ Recommended |

**Priority Futures to Track:**
1. 棉花 (CF) - Zhengzhou
2. 螺纹钢 (RB) - Shanghai
3. 铁矿石 (I) - Dalian
4. 原油 (SC) - Shanghai Energy

---

**Last Updated:** 2026-03-04 (Phase 5 added)  
**Project Owner:** tiim🐮  
**Developer:** ClawBot (with Code_G collaboration)  
**GitHub:** https://github.com/tiimapp/stock-tracker  
**Docs:** Futures capability verified - AKShare recommended
