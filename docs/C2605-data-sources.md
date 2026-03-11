# C2605 玉米期货数据源文档

**最后更新:** 2026-03-11  
**维护者:** ClawBot  
**项目:** stock-tracker

---

## 📊 数据源总览

C2605 玉米期货监控系统使用多层数据源架构，确保数据获取的可靠性和实时性。

### 数据源优先级列表

| 优先级 | 数据源 | 类型 | 用途 | 可靠性 | 延迟 |
|--------|--------|------|------|--------|------|
| **P0** | 新浪财经实时 API | HTTP API | 实时价格 | ⭐⭐⭐⭐⭐ | <1s |
| **P1** | AKShare (新浪源) | Python 库 | 历史/备用数据 | ⭐⭐⭐⭐ | ~2-5s |
| **P2** | Tavily AI Search | AI 搜索 API | 夜盘状态验证 | ⭐⭐⭐⭐ | ~5-10s |
| **P3** | 大商所官网 | 官方网站 | 官方公告验证 | ⭐⭐⭐⭐⭐ | N/A (被墙) |
| **P4** | Mock 数据 | 本地生成 | 测试/降级 | ⭐ | 0s |

---

## 🔍 详细数据源说明

### P0: 新浪财经实时 API ⭐⭐⭐⭐⭐

**端点:** `https://hq.sinajs.cn/list=fu_C2605`

**特点:**
- 实时行情数据，延迟<1 秒
- 支持 GBK 编码返回
- 无需 API Key
- 海外访问稳定

**数据格式:**
```
var hq_str_fu_C2605="玉米 2605,开盘价，昨收价，现价，最高价，最低价，买价，卖价，持仓量，成交量，..."
```

**字段映射:**
| 索引 | 字段 | 说明 |
|------|------|------|
| 0 | name | 合约名称 |
| 1 | open | 开盘价 |
| 2 | prev_close | 昨结算价 |
| 3 | current_price | 最新价 |
| 4 | high | 最高价 |
| 5 | low | 最低价 |
| 10 | volume | 成交量 |

**使用示例:**
```python
import urllib.request
import re

url = "https://hq.sinajs.cn/list=fu_C2605"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as response:
    content = response.read().decode('gbk')
    match = re.search(r'hq_str_fu_C2605="([^"]+)"', content)
    data = match.group(1).split(',')
```

**优缺点:**
| 优点 | 缺点 |
|------|------|
| ✅ 实时数据 | ❌ 非官方源 |
| ✅ 无需认证 | ❌ 格式需手动解析 |
| ✅ 访问稳定 | ❌ 盘后数据可能延迟 |
| ✅ 免费 | |

---

### P1: AKShare (新浪源) ⭐⭐⭐⭐

**模块:** `ak.futures_zh_daily_sina(symbol="C2605")`

**特点:**
- Python 库，易于集成
- 底层调用新浪 API
- 自动解析为 DataFrame
- 支持历史数据

**安装:**
```bash
pip install akshare
```

**使用示例:**
```python
import akshare as ak

futures_df = ak.futures_zh_daily_sina(symbol="C2605")
row = futures_df.iloc[-1]
price = row['close']
volume = row['volume']
date = row['date']
```

**数据字段:**
| 字段 | 说明 |
|------|------|
| symbol | 合约代码 |
| date | 交易日期 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| open_interest | 持仓量 |

**优缺点:**
| 优点 | 缺点 |
|------|------|
| ✅ 易于使用 | ❌ 依赖第三方库 |
| ✅ 自动解析 | ❌ 历史数据非实时 |
| ✅ 支持多合约 | ❌ 盘后数据可能过期 |
| ✅ 中文文档 | |

---

### P2: Tavily AI Search ⭐⭐⭐⭐

**端点:** `https://api.tavily.com/search`

**特点:**
- AI 驱动的搜索 API
- 专为 AI Agent 优化
- 支持时间范围过滤
- 返回综合答案 + 引用来源

**安装:**
```bash
pip install tavily-python
export TAVILY_API_KEY='tvly-xxxxxxxxxxxxxxxxxxxx'
```

**使用示例:**
```python
from tavily import TavilyClient
import os

client = TavilyClient(api_key=os.environ['TAVILY_API_KEY'])
response = client.search(
    query="大连商品交易所 玉米期货 夜盘交易时间 2026",
    search_depth="advanced",
    max_results=5,
    include_answer=True,
    topic="finance",
    days=7
)
print(response['answer'])
```

**主要用途:**
- 验证夜盘交易状态
- 获取最新官方公告
- 交叉验证多源信息
- 检测交易时间变更

**优缺点:**
| 优点 | 缺点 |
|------|------|
| ✅ AI 综合答案 | ❌ 需要 API Key |
| ✅ 时间过滤 | ❌ 付费额度限制 |
| ✅ 引用可追溯 | ❌ 延迟较高 (5-10s) |
| ✅ 无广告干扰 | |

---

### P3: 大商所官网 ⭐⭐⭐⭐⭐

**URL:** `https://www.dce.com.cn`

**特点:**
- 官方权威数据源
- 最可靠的交易时间信息
- 发布官方公告
- 海外访问受限

**主要页面:**
- 交易时间：`/dalianshangpin/jyyl/jysj/index.html`
- 通知公告：`/dalianshangpin/tzgg/index.html`
- 行情数据：`/dalianshangpin/mrhq/index.html`

**优缺点:**
| 优点 | 缺点 |
|------|------|
| ✅ 官方权威 | ❌ 海外 IP 被封锁 |
| ✅ 信息最准确 | ❌ 网页结构复杂 |
| ✅ 第一手公告 | ❌ 无公开 API |
| ✅ 免费 | ❌ 需人工验证 |

**替代方案:**
- 使用国内代理服务器
- 通过期货公司官网间接获取
- 依赖 Tavily 搜索聚合

---

### P4: Mock 数据 ⭐

**位置:** `c2605_monitor.py` 中的 `generate_mock_data()`

**特点:**
- 本地生成测试数据
- 用于开发和测试
- 所有数据源失败时的降级方案

**使用场景:**
- 开发环境测试
- 网络故障降级
- API 限流保护

**示例数据:**
```python
{
    'symbol': 'C2605',
    'name': '玉米 2605',
    'current_price': 2450.0,
    'open': 2445.0,
    'high': 2460.0,
    'low': 2440.0,
    'volume': 50000,
    'change_percent': 0.2
}
```

---

## 🔄 数据源降级策略

### 降级流程图

```
┌─────────────────────────────────────┐
│  开始获取 C2605 数据                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  P0: 新浪财经实时 API                │
│  https://hq.sinajs.cn/list=fu_C2605 │
└──────────────┬──────────────────────┘
               │ 失败 (超时/解析错误)
               ▼
┌─────────────────────────────────────┐
│  P1: AKShare 历史数据                │
│  ak.futures_zh_daily_sina("C2605")  │
└──────────────┬──────────────────────┘
               │ 失败 (库不可用/网络错误)
               ▼
┌─────────────────────────────────────┐
│  P4: Mock 数据 (降级)                │
│  generate_mock_data()               │
└─────────────────────────────────────┘
```

### 夜盘验证独立流程

```
┌─────────────────────────────────────┐
│  每日夜盘状态验证                    │
│  (首次心跳时执行)                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  P2: Tavily AI Search                │
│  查询"玉米期货 夜盘 2026"            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  P3: 大商所官网 (如可访问)           │
│  交叉验证                            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  更新状态文件                        │
│  memory/dce-trading-state.json      │
└─────────────────────────────────────┘
```

---

## 📁 相关文件位置

| 文件 | 路径 | 用途 |
|------|------|------|
| 主监控脚本 | `stock-tracker/c2605_monitor.py` | 数据获取 + 报告生成 |
| 夜盘验证器 | `stock-tracker/dce_trading_verifier.py` | 夜盘状态验证 |
| Tavily 示例 | `stock-tracker/docs/tavily-verification-example.py` | Tavily 使用示例 |
| Tavily Fetcher | `stock-tracker/fetchers/c2605_tavily_fetcher.py` | Tavily 价格获取 |
| 心跳检查 | `workspace/heartbeat_trading_check.py` | 交易日验证 |
| 状态文件 | `workspace/memory/dce-trading-state.json` | 夜盘状态缓存 |
| 状态文件 | `workspace/memory/heartbeat-state.json` | 交易日状态缓存 |

---

## 🔧 配置说明

### 环境变量

```bash
# Tavily API Key (可选，用于夜盘验证)
export TAVILY_API_KEY='tvly-xxxxxxxxxxxxxxxxxxxx'

# 添加到 ~/.openclaw/.env 永久生效
```

### 配置文件

**c2605_config.json:**
```json
{
  "symbol": "C2605",
  "symbol_name": "玉米 2605",
  "discord_channel_id": "1475775915844960428",
  "trading_hours": {
    "sessions": [
      {"start": "09:00", "end": "10:15"},
      {"start": "10:30", "end": "11:30"},
      {"start": "13:30", "end": "15:00"}
    ]
  }
}
```

---

## 📊 数据源对比总结

| 特性 | 新浪实时 | AKShare | Tavily | 大商所 | Mock |
|------|---------|---------|--------|--------|------|
| 实时性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | N/A |
| 可靠性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| 易用性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 成本 | 免费 | 免费 | 付费额度 | 免费 | 免费 |
| 适用场景 | 实时价格 | 历史数据 | 信息验证 | 官方确认 | 测试降级 |

---

## 🎯 最佳实践

1. **优先使用新浪实时 API** - 获取最新价格
2. **AKShare 作为备用** - 当新浪 API 不可用时
3. **Tavily 用于验证** - 每日验证夜盘状态
4. **Mock 数据兜底** - 确保系统不会完全失效
5. **多源交叉验证** - 关键信息至少 2 个独立来源确认

---

*文档维护：ClawBot | 最后更新：2026-03-11*
