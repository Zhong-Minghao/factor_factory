# 向量回测框架使用指南

## 概述

向量回测框架是一个轻量级、快速的回测工具，专门用于**因子有效性验证**。

## 核心特性

- ✅ **向量化计算**：比事件驱动快 10-100 倍
- ✅ **三种选股方式**：Top N、分层、百分比
- ✅ **三种调仓频率**：日度、周度、月度
- ✅ **考虑交易成本**：手续费、滑点
- ✅ **DataFrame 友好**：所有结果都是 DataFrame 格式

## 快速开始

### 1. Top N 回测

```python
from backtest import VectorBacktest

# 运行回测
backtest = VectorBacktest(
    factor_data=factor_df,    # 因子数据（宽表格式）
    price_data=price_df,      # 价格数据（宽表格式）
    select_method="top_n",
    select_params={"top_n": 10},       # 选择因子值最高的10只股票
    rebalance_freq="monthly",          # 每月调仓
    commission_rate=0.0003,            # 万三手续费
    slippage_rate=0.0001,              # 万一滑点
    initial_capital=1000000.0,         # 100万初始资金
)

result = backtest.run()

# 查看结果
print(result.metrics)           # 绩效指标 DataFrame
print(result.returns.head())    # 收益率序列
print(result.positions.head())  # 持仓明细
```

### 2. 分层回测

```python
# 选择第5层（因子值最高的一层）
backtest = VectorBacktest(
    factor_data=factor_df,
    price_data=price_df,
    select_method="layer",
    select_params={"n_layers": 5, "layer_id": 4},  # 分5层，选第5层
    rebalance_freq="monthly",
)

result = backtest.run()
```

### 3. 百分比回测

```python
# 选择因子值最高的前20%股票
backtest = VectorBacktest(
    factor_data=factor_df,
    price_data=price_df,
    select_method="percentile",
    select_params={"percentile": 0.2},  # 前20%
    rebalance_freq="weekly",           # 每周调仓
)

result = backtest.run()
```

### 4. 带基准的回测

```python
# 提供基准数据（如沪深300指数）
benchmark_data = pd.Series(...)  # 指数价格序列

backtest = VectorBacktest(
    factor_data=factor_df,
    price_data=price_df,
    benchmark_data=benchmark_data,
    select_method="top_n",
    select_params={"top_n": 10},
)

result = backtest.run()

# 查看超额收益
print(result.excess_returns.mean())
```

## 输出结果

### BacktestResult 对象

```python
result = backtest.run()

# 1. 收益相关
result.returns                 # 收益率序列（Series）
result.equity_curve            # 净值曲线（Series）
result.cumulative_returns      # 累计收益率（Series）

# 2. 持仓相关
result.positions               # 持仓明细（DataFrame）
result.holdings                # 市值明细（DataFrame）
result.turnover                # 换手率序列（Series）

# 3. 绩效指标
result.metrics                 # 绩效指标 DataFrame
# 包含：累计收益率、年化收益率、波动率、最大回撤、夏普比率、索提诺比率、卡尔玛比率、胜率

# 4. 基准对比（如果有基准）
result.benchmark_returns       # 基准收益率（Series）
result.excess_returns          # 超额收益（Series）

# 5. 快速摘要
print(result.summary())        # 回测摘要（Series）
```

### 导出所有结果

```python
# 导出为 DataFrame 字典
results_dict = result.to_dataframe()

# 保存到 Excel
with pd.ExcelWriter('backtest_results.xlsx') as writer:
    for key, df in results_dict.items():
        df.to_excel(writer, sheet_name=key)
```

## 绩效指标说明

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| 累计收益率 | 整个回测期间的总收益 | (1 + r).prod() - 1 |
| 年化收益率 | 折算为年度收益 | (1 + r)^(252/n) - 1 |
| 波动率 | 收益率标准差（年化） | std() * sqrt(252) |
| 最大回撤 | 最大亏损幅度 | max((cumulative - running_max) / running_max) |
| 夏普比率 | 风险调整收益 | (mean - rf) / std * sqrt(252) |
| 索提诺比率 | 下行风险调整收益 | (mean - rf) / downside_std * sqrt(252) |
| 卡尔玛比率 | 收益/回撤比 | annual_return / abs(max_drawdown) |
| 胜率 | 正收益占比 | (returns > 0).mean() |

## 数据格式要求

### 因子数据（factor_data）

```
格式：DataFrame（宽表）
index：交易日期（DatetimeIndex）
columns：股票代码（如 sz000001, sz000002, ...）
values：因子值（float）

示例：
                sz000001  sz000002  sz000003
2023-01-01       1.23      0.87      1.45
2023-01-02       1.25      0.89      1.43
...
```

### 价格数据（price_data）

```
格式：DataFrame（宽表）
index：交易日期（DatetimeIndex）
columns：股票代码
values：收盘价（float）

示例：
                sz000001  sz000002  sz000003
2023-01-01      100.5     50.3      30.2
2023-01-02      101.2     50.8      30.1
...
```

### 基准数据（benchmark_data，可选）

```
格式：Series
index：交易日期（DatetimeIndex）
values：指数价格（float）

示例：
2023-01-01    3000.5
2023-01-02    3010.2
...
```

## 参数说明

### 选股方式（select_method）

- **top_n**：选择因子值最高的 N 只股票
  - 参数：`{"top_n": 10}`

- **layer**：按因子值分层，选择指定层
  - 参数：`{"n_layers": 5, "layer_id": 4}`（layer_id 从 0 开始，4 表示第5层）

- **percentile**：选择因子值最高的前 X% 股票
  - 参数：`{"percentile": 0.2}`（20%）

### 调仓频率（rebalance_freq）

- **daily**：每个交易日调仓
- **weekly**：每周调仓（最后一个交易日）
- **monthly**：每月调仓（最后一个交易日）

### 权重方式（weight_method）

- **equal**：等权（默认）
- **market_cap**：市值加权（暂未实现）

### 交易成本

- **commission_rate**：手续费率（默认 0.0003 = 万三）
- **min_commission**：最低手续费（默认 5.0 元）
- **slippage_rate**：滑点率（默认 0.0001 = 万一）

## 与现有模块的集成

### 使用 SmartDataLoader 加载数据

```python
from storage.data_loader import SmartDataLoader
from data.store import DataStore

store = DataStore()
loader = SmartDataLoader(data_store=store)

# 加载因子数据
factor_data = loader.load_factor_values(
    factor_name="MA",
    params={"window": 20},
    start_date="2023-01-01",
    end_date="2023-12-31",
)

# 加载价格数据
price_data = loader.load_daily_data_batch(
    stock_codes=factor_data.columns.tolist(),
    start_date="2023-01-01",
    end_date="2023-12-31",
)
```

### 因子预处理

```python
from analysis.preprocessing import preprocess_factor

# 去极值、标准化
factor_data = preprocess_factor(
    factor_data,
    outlier_method="mad",      # MAD 去极值
    standardize=True,          # 标准化
)
```

## 完整示例

```python
from backtest import VectorBacktest
from storage.data_loader import SmartDataLoader
from data.store import DataStore
from analysis.preprocessing import preprocess_factor

# 1. 加载数据
store = DataStore()
loader = SmartDataLoader(data_store=store)

factor_data = loader.load_factor_values("MA", {"window": 20}, "2023-01-01", "2023-12-31")
price_data = loader.load_daily_data_batch(factor_data.columns, "2023-01-01", "2023-12-31")

# 2. 预处理因子
factor_data = preprocess_factor(factor_data)

# 3. 运行回测
backtest = VectorBacktest(
    factor_data=factor_data,
    price_data=price_data,
    select_method="top_n",
    select_params={"top_n": 10},
    rebalance_freq="monthly",
)

result = backtest.run()

# 4. 查看结果
print(result.summary())
print(result.metrics)

# 5. 导出结果
results_dict = result.to_dataframe()
```

## 注意事项

1. **数据对齐**：因子数据和价格数据的日期会自动对齐
2. **缺失值处理**：自动跳过没有数据的股票
3. **交易日历**：使用因子数据中的日期作为交易日
4. **交易成本**：第一次建仓不计算交易成本，后续调仓计算换手率

## 性能

- **速度**：秒级完成回测（1000个交易日，50只股票）
- **内存**：约 100MB（正常规模）
- **适用场景**：因子验证、参数优化、大规模测试

## 后续扩展

- [ ] 市值加权
- [ ] 止盈止损
- [ ] 行业中性化
- [ ] 多因子组合
- [ ] 参数优化（网格搜索）
