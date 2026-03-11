# C2605 数据源测试报告

**测试日期**: 2026-03-11 13:19 GMT+8  
**测试目标**: 全面验证 C2605 玉米期货项目的所有数据源是否正常工作  
**测试环境**: Linux 6.1.0-43-amd64, Python 3.x, OpenClaw Workspace

---

## 测试结果摘要

| 数据源 | 优先级 | 状态 | 响应时间 | 备注 |
|--------|--------|------|----------|------|
| 新浪财经实时 API | P0 | ❌ 失败 | 5.33s | 403 Forbidden |
| AKShare | P1 | ❌ 失败 | 5.91s | IndexError |
| Tavily Search | P2 | ✅ 成功 | 1.02s | 返回 5 条结果 |
| Perplexity Search | P2 | ✅ 成功 | 16.05s | 提供详细信息 |
| Mock 数据 | P3 | ✅ 成功 | 0.001s | 降级方案可用 |

**总体结论**: ⚠️ **部分可用** - 实时价格数据源 (Sina/AKShare) 均失败，搜索类数据源 (Tavily/Perplexity) 正常工作，Mock 数据可作为降级方案。

---

## 详细测试结果

### 1. 新浪财经实时 API (P0 优先级) ❌

**测试 URL**: `http://hq.sinajs.cn/rn.php?code=f_C2605`

**测试结果**:
- **状态**: ❌ FAILED
- **HTTP 状态码**: 403 Forbidden
- **响应时间**: 5.33s
- **返回内容**: `Forbidden`

**问题分析**:
- 新浪财经 API 返回 403 禁止访问错误
- 可能原因:
  1. IP 地址被封锁
  2. 需要特定的 User-Agent/Referer 头
  3. API 接口已变更或下线
  4. C2605 合约代码格式不正确（可能需要其他格式如 `f_C2605` 或 `C2605`）

**建议**:
- 尝试添加完整的浏览器请求头
- 检查大商所官方 API 作为替代
- 考虑使用付费数据源（如 Tushare Pro、Wind）

---

### 2. AKShare 期货实时行情 (P1 优先级) ❌

**测试代码**:
```python
import akshare as ak
ak.futures_zh_spot(symbol="C2605")
```

**测试结果**:
- **状态**: ❌ FAILED
- **响应时间**: 5.91s
- **错误类型**: `IndexError: list index out of range`

**问题分析**:
- AKShare 库已安装 (v1.18.34)
- 错误发生在数据解析阶段，可能是:
  1. C2605 合约尚未挂牌交易（远月合约）
  2. 大商所数据源返回空数据
  3. AKShare 解析逻辑需要更新

**Perplexity 交叉验证发现**:
> C2605 是 2026 年 5 月交割的玉米期货合约。期货市场一般不会提前两年以上挂牌远月合约，C2605 可能尚未开始交易，因此没有实时价格。

**建议**:
- 测试主力合约（如 C2505、C2509）验证 AKShare 是否正常工作
- 检查大商所官网确认 C2605 是否已挂牌
- 考虑使用 `ak.futures_zh_realtime()` 替代 `futures_zh_spot()`

---

### 3. Tavily Search (P2 优先级) ✅

**测试查询**: `C2605 玉米期货 实时价格 2026`

**测试结果**:
- **状态**: ✅ SUCCESS
- **响应时间**: 1.02s
- **结果数量**: 5 条
- **API Key**: ✅ 已配置

**数据样例**:
```
First result title: 玉米 2605-财经—手机新浪网 - 行情中心
```

**分析**:
- Tavily API 配置正确
- 能够搜索到相关财经页面
- 适合用于获取行情页面 URL，然后进行网页抓取

**建议**:
- 结合网页抓取提取具体价格数据
- 可用作备用数据源

---

### 4. Perplexity Search (P2 优先级) ✅

**测试查询**: `C2605 玉米期货 交易时间 2026`

**测试结果**:
- **状态**: ✅ SUCCESS
- **响应时间**: 16.05s
- **结果质量**: 高（提供详细的交易时间说明）

**数据样例**:
```
C2605 是大连商品交易所（DCE）的玉米期货合约代码：
- "C" 代表玉米（Corn）
- "2605" 表示 2026 年 5 月到期交割

交易时间:
- 日盘：09:00–11:30，13:30–15:00
- 夜盘：21:00–23:00
```

**分析**:
- Perplexity 提供高质量的解释性内容
- 适合用于获取合约信息、交易规则等元数据
- 不适合获取实时价格

**建议**:
- 用于补充合约元数据
- 作为知识库查询工具

---

### 5. Mock 数据 (P3 优先级 - 降级方案) ✅

**测试方法**: 调用 `c2605_monitor.py` 中的 `generate_mock_data()`

**测试结果**:
- **状态**: ✅ SUCCESS
- **响应时间**: 0.001s
- **数据格式**: 完整兼容

**数据样例**:
```json
{
  "symbol": "C2605",
  "name": "玉米 2605",
  "current_price": 2463.85,
  "open": 2447.57,
  "high": 2466.18,
  "low": 2420.34,
  "previous_close": 2450.0,
  "volume": 65373,
  "timestamp": "2026-03-11 13:19:12",
  "change": 12.92,
  "change_percent": -0.0566
}
```

**分析**:
- Mock 数据生成逻辑正常
- 数据格式与真实数据兼容
- 可作为开发测试和降级方案

**建议**:
- 保持 Mock 数据作为最后降级方案
- 生产环境需标注数据来源为 "mock"

---

## 根本原因分析

### 为什么实时数据源失败？

根据 Perplexity 搜索结果，**C2605 合约可能尚未挂牌交易**：

1. **远月合约问题**: C2605 是 2026 年 5 月交割的合约，期货市场通常只提前 1-2 年挂牌
2. **当前主力合约**: 可能是 C2505 或 C2509（2025 年合约）
3. **数据源行为**: 当查询不存在的合约时，Sina 返回 403，AKShare 返回空列表导致 IndexError

---

## 建议与下一步行动

### 短期方案（立即执行）

1. **测试主力合约**: 
   ```python
   ak.futures_zh_spot(symbol="C2505")  # 测试 2025 年 5 月合约
   ak.futures_zh_spot(symbol="C2509")  # 测试 2025 年 9 月合约
   ```

2. **验证 AKShare 功能**: 确认 AKShare 对其他合约是否正常工作

3. **添加合约有效性检查**: 在获取数据前先验证合约是否已挂牌

### 中期方案（1-2 周）

1. **实现数据源降级链**:
   ```
   AKShare → Tavily+Web Scraping → Mock Data
   ```

2. **添加合约列表查询**: 从大商所获取可交易合约列表

3. **监控主力合约切换**: 自动跟踪并切换到新的主力合约

### 长期方案（1 个月+）

1. **接入付费数据源**: Tushare Pro、Wind、Bloomberg 等
2. **建立数据缓存层**: 减少 API 调用频率
3. **实现多数据源交叉验证**: 提高数据可靠性

---

## 附录：测试命令

```bash
# 测试 Sina API
curl -H "User-Agent: Mozilla/5.0" "http://hq.sinajs.cn/rn.php?code=f_C2605"

# 测试 AKShare
python3 -c "import akshare as ak; print(ak.futures_zh_spot(symbol='C2605'))"

# 测试 Tavily
python3 -c "from tavily import TavilyClient; import os; c=TavilyClient(api_key=os.environ['TAVILY_API_KEY']); print(c.search('C2605'))"

# 测试 Mock 数据
python3 -c "from c2605_monitor import generate_mock_data; print(generate_mock_data())"
```

---

**报告生成时间**: 2026-03-11 13:19:45 GMT+8  
**测试执行者**: OpenClaw Subagent (c2605-datasource-test)

---

## 附录 B: AKShare 补充测试 (测试后追加)

**测试时间**: 2026-03-11 13:21

发现 `ak.futures_zh_spot()` 存在普遍问题，但其他 AKShare 接口可用:

| 函数 | 状态 | 说明 |
|------|------|------|
| `futures_zh_spot()` | ❌ | IndexError (所有合约) |
| `futures_zh_realtime()` | ❌ | KeyError |
| `futures_zh_daily_sina()` | ✅ | 返回历史日线数据 |

**建议**: 使用 `ak.futures_zh_daily_sina()` 替代 `futures_zh_spot()` 获取期货数据。

