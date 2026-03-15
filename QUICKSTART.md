# 量化因子工厂 - 快速开始

## 🎯 项目简介

这是一个轻量级的个人量化研究工具，专注于因子的研发、回测和评估。

### 核心特性

- ✅ **灵活的数据源**：支持Tushare、AKShare、Baostock等免费数据源
- ✅ **强大的因子系统**：40+内置因子，支持自定义因子
- ✅ **高效计算引擎**：并行计算、批量处理、结果缓存
- ✅ **完整的工具链**：交易日历、数据存储、因子管理
- 🚧 **回测系统**：正在开发中
- 🚧 **CLI工具**：正在开发中

## 📦 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd 因子工厂
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 快速上手

### 示例1: 使用内置因子

```python
from factors.registry import factor_registry
import pandas as pd

# 获取因子
factor = factor_registry.get("MA", window=20)

# 准备数据
data = pd.DataFrame({
    "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
})

# 计算因子
factor_values = factor.compute(data)
print(factor_values)
```

### 示例2: 创建自定义因子

```python
from factors.base import TechnicalFactor
from factors.registry import factor_registry

@factor_registry.register("MY_FACTOR")
class MyFactor(TechnicalFactor):
    """自定义因子"""

    name = "MY_FACTOR"
    description = "我的第一个因子"
    author = "Your Name"
    version = "1.0.0"
    params = {"period": 10}

    def compute(self, data):
        period = self.params.get("period", 10)
        return data["close"].pct_change(period)

# 使用自定义因子
factor = factor_registry.get("MY_FACTOR", period=5)
```

### 示例3: 批量计算因子

```python
from factors.engine import FactorEngine

engine = FactorEngine()

# 批量计算
factors = ["MA", "RETURN", "RSI"]
results = engine.compute_factors_batch(factors, data, parallel=True)

for name, values in results.items():
    print(f"{name}: {values.mean():.4f}")
```

### 示例4: 获取市场数据

```python
from data.providers.akshare import AKShareSource

# 连接数据源
source = AKShareSource()
source.connect()

# 获取股票列表
stock_list = source.get_stock_list()
print(f"共 {len(stock_list)} 只股票")

# 获取日线数据
data = source.get_daily_data(
    ts_code="000001.SZ",
    start_date="2024-01-01",
    end_date="2024-03-15"
)

print(data.head())
```

### 示例5: 使用交易日历

```python
from utils.calendar import get_calendar

calendar = get_calendar()

# 判断交易日
is_trading = calendar.is_trading_day("2024-03-15")
print(f"是否交易日: {is_trading}")

# 获取交易日列表
trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
print(f"1月交易日: {len(trading_days)}天")
```

## 📊 可用因子

### 技术指标因子 (9个)
- `MA` - 移动平均线
- `EMA` - 指数移动平均
- `MACD` - 指数平滑异同移动平均线
- `RSI` - 相对强弱指标
- `BOLL` - 布林带
- `ATR` - 平均真实波幅
- `KDJ` - 随机指标
- `CCI` - 顺势指标
- `OBV` - 能量潮

### 动量因子 (9个)
- `RETURN` - N日收益率
- `MOM` - N日动量
- `ACCELERATION` - 价格加速度
- `RSQ` - R平方（趋势强度）
- `MAX_RETURN` - 最大收益率
- `DOWNSIDE_RISK` - 下行风险
- `UPSIDE_POTENTIAL` - 上行潜力
- `RATE_OF_CHANGE` - 变化率
- `WILLIAMS_R` - 威廉指标

### 成交量因子 (9个)
- `VOLUME_RATIO` - 量比
- `VOLUME_MA` - 成交量均线
- `TURNOVER` - 换手率
- `VPRICE` - 量价配合度
- `VOLATILITY` - 成交量波动率
- `NET_FLOW` - 资金净流入
- `VOLUME_TREND` - 成交量趋势
- `PRICE_VOLUME_TREND` - 价量趋势
- `VOLUME_OSCILLATOR` - 成交量震荡

### 基本面因子 (9个)
- `PE` - 市盈率
- `PB` - 市净率
- `PS` - 市销率
- `MARKET_CAP` - 总市值
- `CIRCULATING_CAP` - 流通市值
- `EP` - 盈利收益率
- `BP` - 账面市值比
- `LOG_MARKET_CAP` - 对数市值

## 🔧 配置

### 配置文件

编辑 `config/config.yaml`：

```yaml
data:
  primary_provider: "tushare"  # 主要数据源
  storage_format: "hdf5"       # 存储格式
  enable_cache: true           # 启用缓存

factor:
  parallel: true               # 并行计算
  n_workers: -1                # 工作进程数(-1=全部)

backtest:
  initial_capital: 1000000.0   # 初始资金
  commission_rate: 0.0003      # 手续费率
  slippage_rate: 0.0001        # 滑点率
```

### 环境变量

创建 `.env` 文件：

```bash
TUSHARE_TOKEN=your_token_here
DATA_PRIMARY_PROVIDER=tushare
LOG_LEVEL=INFO
```

## 🧪 测试

运行完整测试套件：

```bash
python run_tests.py
```

运行单独测试：

```bash
# 测试配置
python tests/test_config.py

# 测试交易日历
python tests/test_calendar.py

# 测试因子系统
python tests/test_factors.py

# 测试数据源
python tests/test_data_source.py
```

查看示例：

```bash
python examples/demo.py
```

## 📚 项目结构

```
factor_factory/
├── config/              # 配置管理
│   ├── settings.py      # 配置类
│   └── config.yaml      # 配置文件
├── data/               # 数据层
│   ├── base.py         # 数据源基类
│   ├── store.py        # 数据存储
│   ├── cache.py        # 缓存系统
│   └── providers/      # 数据源实现
├── factors/            # 因子层
│   ├── base.py         # 因子基类
│   ├── registry.py     # 因子注册
│   ├── engine.py       # 计算引擎
│   └── library/        # 内置因子库
├── utils/              # 工具函数
│   ├── calendar.py     # 交易日历
│   └── helpers.py      # 辅助函数
├── tests/              # 测试代码
└── examples/           # 示例代码
```

## 🎯 使用场景

### 场景1: 因子研发

```python
# 1. 创建自定义因子
@factor_registry.register("ALPHA001")
class Alpha001(TechnicalFactor):
    # ... 实现因子逻辑

# 2. 计算因子值
factor = factor_registry.get("ALPHA001")
values = factor.compute(data)

# 3. 分析因子效果
# （待实现：IC分析、分层回测等）
```

### 场景2: 批量因子计算

```python
# 1. 准备数据
data = load_stock_data("000001.SZ")

# 2. 批量计算多个因子
engine = FactorEngine()
factors = ["MA", "RETURN", "RSI", "VOLUME_RATIO"]
results = engine.compute_factors_batch(factors, data)

# 3. 保存结果
# （待实现：因子存储）
```

### 场景3: 数据获取与管理

```python
# 1. 获取数据
source = AKShareSource()
source.connect()

# 2. 下载历史数据
data = source.get_daily_data("000001.SZ", "2020-01-01", "2024-12-31")

# 3. 存储数据
store = DataStore()
store.save_daily_data("000001.SZ", data)
```

## 🚧 待实现功能

### 第四阶段：因子管理与分析
- [ ] 因子数据库
- [ ] IC/IR分析
- [ ] 分层回测
- [ ] 因子相关性分析

### 第五阶段：回测系统
- [ ] 事件驱动回测引擎
- [ ] 模拟经纪商
- [ ] 绩效指标计算
- [ ] HTML报告生成

### 第六阶段：CLI工具
- [ ] 命令行界面
- [ ] 数据管理命令
- [ ] 因子计算命令
- [ ] 回测命令

## 📖 学习资源

- [测试指南](TESTING.md) - 详细的测试说明
- [配置说明](config/config.yaml) - 配置文件示例
- [因子开发](factors/library/) - 内置因子示例

## 💡 提示

1. **开发环境**：建议使用虚拟环境隔离项目依赖
2. **数据源**：AKShare免费但可能不稳定，Tushare需要注册
3. **因子计算**：使用并行计算可以显著提升速度
4. **自定义因子**：参考内置因子的实现方式

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## ⚠️ 免责声明

本工具仅供学习研究使用，不构成任何投资建议。
使用本工具进行实盘交易的风险由使用者自行承担。

---

**Happy Quant!** 📈
