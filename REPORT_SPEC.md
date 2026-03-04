# Report Specification 📋

## Report Format

The daily stock report follows this structure:

---

### Template

```
📊 中控技术 (688777) 日报
━━━━━━━━━━━━━━━━━━━━━━
📅 YYYY-MM-DD 15:30

💰 价格信息
- 当前价：¥XX.XX
- 涨跌：+X.XX% (vs previous close)
- 今开：¥XX.XX
- 最高：¥XX.XX
- 最低：¥XX.XX
- 成交量：XXXX.XX 万手
- 成交额：X.XX 亿

📈 趋势分析
- 5 日趋势：↑ 上涨 / ↓ 下跌 / → 盘整
- 支撑位：¥XX.XX
- 阻力位：¥XX.XX

📊 MACD 信号
- 状态：🟢 BUY / 🔴 SELL / ⚪ HOLD
- DIF: X.XXXX
- DEA: X.XXXX
- MACD 柱：X.XXXX
- 说明：[简要解释信号含义]

📰 重要新闻
【Sina 财经】
1. [新闻标题] - [时间]
   [简要摘要]

【东方财富】
2. [新闻标题] - [时间]
   [简要摘要]

【公司公告】
3. [公告标题] - [时间]
   [简要摘要]

🔍 明日关注
- [事件 1]: 描述
- [事件 2]: 描述

---
数据来源：Sina 财经、东方财富网、上交所
生成时间：YYYY-MM-DD HH:MM:SS
```

---

## Data Fields

### Price Data (from Sina API)

Sina API returns comma-separated values:

```
var hq_str_sh688777="名称，当前价，昨日收盘，今开，最高，最低，买价，卖价，成交量，成交额，买1量，买1价，买2量，买2价，买3量，买3价，买4量，买4价，买5量，买5价，卖1量，卖1价，卖2量，卖2价，卖3量，卖3价，卖4量，卖4价，卖5量，卖5价，日期，时间"
```

| Index | Field | Description |
|-------|-------|-------------|
| 0 | 名称 | Stock name |
| 1 | 当前价 | Current price |
| 2 | 昨日收盘 | Previous close |
| 3 | 今开 | Open |
| 4 | 最高 | High |
| 5 | 最低 | Low |
| 8 | 成交量 | Volume (shares) |
| 9 | 成交额 | Turnover (yuan) |
| 30 | 日期 | Date |
| 31 | 时间 | Time |

### MACD Calculation

```python
# Standard MACD parameters
EMA_SHORT = 12
EMA_LONG = 26
EMA_SIGNAL = 9

# Calculation
DIF = EMA(close, 12) - EMA(close, 26)
DEA = EMA(DIF, 9)
MACD = (DIF - DEA) * 2

# Signal detection
if DIF crosses above DEA: BUY
if DIF crosses below DEA: SELL
else: HOLD
```

### News Sources Priority

1. **上交所公告** (Official announcements) - Highest priority
2. **Sina 财经** - Major financial news
3. **东方财富网** - Community + analysis
4. **General web search** - Broader coverage

---

## Signal Icons

| Icon | Meaning | Condition |
|------|---------|-----------|
| 🟢 | BUY | Golden cross (DIF > DEA, bullish) |
| 🔴 | SELL | Death cross (DIF < DEA, bearish) |
| ⚪ | HOLD | No clear signal / neutral |

---

## Error Handling

If data fetch fails:
- Retry up to 3 times with 5s delay
- Log error to `logs/error.log`
- Send partial report with available data
- Mark missing fields as "数据暂缺"

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-01 | Initial spec |
