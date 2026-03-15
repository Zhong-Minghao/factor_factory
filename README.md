# 量化因子工厂 (Factor Factory)

一个轻量级的个人量化研究工具，专注于因子的研发、回测和评估。

## 特性

### ✅ 已实现
- 🏠 **轻量级部署**：本地化设计，无需复杂的服务器配置
- 📊 **多数据源支持**：内置Tushare、AKShare、Baostock等免费数据源
- 🧮 **强大的因子系统**：40+内置因子、自动注册、并行计算
- 📅 **交易日历工具**：完整的A股交易日历查询
- 💾 **灵活的存储系统**：支持HDF5和Parquet格式
- ⚡ **高效缓存机制**：内存和磁盘双层缓存

### 🚧 开发中
- 📈 **回测引擎**：事件驱动、支持A股T+1规则
- 📝 **因子分析工具**：IC/IR分析、分层回测、因子相关性分析
- 🛠️ **CLI工具**：命令行界面
- 📊 **Web界面**：可视化界面（未来计划）

## 快速开始

### 📚 详细文档

- **[快速开始指南](QUICKSTART.md)** - 5分钟上手教程
- **[测试指南](TESTING.md)** - 完整的测试说明
- **[实施计划](.claude/plans/squishy-toasting-scott.md)** - 项目开发计划

### 🔧 安装

```bash
# 1. 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt
```

### ⚡ 立即开始

#### Python代码方式

```python
# 使用内置因子
from factors.registry import factor_registry
import pandas as pd

# 获取因子
factor = factor_registry.get("MA", window=20)

# 计算因子
data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
values = factor.compute(data)
print(values)
```

#### 创建自定义因子

```python
from factors.base import TechnicalFactor
from factors.registry import factor_registry

@factor_registry.register("MY_FACTOR")
class MyFactor(TechnicalFactor):
    """自定义因子"""

    name = "MY_FACTOR"
    description = "我的因子"
    author = "Your Name"
    version = "1.0.0"
    params = {"period": 10}

    def compute(self, data):
        return data["close"].pct_change(self.params["period"])

# 使用自定义因子
factor = factor_registry.get("MY_FACTOR", period=5)
```

### 🧪 测试系统

```bash
# 运行所有测试
python run_tests.py

# 或单独测试
python tests/test_config.py      # 测试配置
python tests/test_calendar.py    # 测试交易日历
python tests/test_factors.py     # 测试因子系统
python examples/demo.py          # 查看示例
```

## 项目结构

```
factor_factory/
├── data/              # 数据模块
├── factors/           # 因子模块
├── backtest/          # 回测模块
├── analysis/          # 分析模块
├── storage/           # 存储模块
├── cli/               # 命令行工具
├── utils/             # 工具函数
└── config/            # 配置管理
```

## 开发自定义因子

1. 在 `factors/library/` 目录下创建因子文件：

```python
from factors.base import Factor, factor_registry

@factor_registry.register("MY_FACTOR")
class MyFactor(Factor):
    """我的自定义因子"""

    name = "MY_FACTOR"
    description = "因子描述"
    author = "Your Name"
    version = "1.0.0"

    def compute(self, data):
        """计算因子值"""
        # 实现你的因子计算逻辑
        return data["close"].pct_change(20)
```

2. 使用自定义因子：

```bash
factor-cli factor calc --name MY_FACTOR
```

## 📊 内置因子库

### 技术指标 (9个)
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

**总计：37个内置因子**

## 依赖

- Python 3.10+
- pandas, numpy
- h5py, pyarrow (数据存储)
- tushare, akshare, baostock (数据源)
- scipy, scikit-learn (分析)
- plotly, matplotlib (可视化)

## 文档

- [配置指南](docs/configuration.md)
- [因子开发指南](docs/factor_development.md)
- [API文档](docs/api.md)
- [示例代码](examples/)

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

- GitHub Issues: [提交问题](https://github.com/yourusername/factor-factory/issues)
- Email: your.email@example.com

## 🗺️ 开发路线图

### ✅ 已完成 (v0.1.0)
- [x] 项目初始化和配置管理
- [x] 数据层实现（多数据源支持）
- [x] 因子系统核心（37个内置因子）
- [x] 交易日历工具
- [x] 数据存储和缓存系统

### 🚧 开发中 (v0.2.0)
- [ ] 因子数据库
- [ ] 因子分析工具（IC/IR、分层回测）
- [ ] 事件驱动回测引擎
- [ ] 绩效指标计算

### 📋 计划中 (v0.3.0)
- [ ] CLI命令行工具
- [ ] HTML报告生成
- [ ] 风险管理模块
- [ ] 多因子组合优化

### 🎯 未来版本
- [ ] Web可视化界面
- [ ] 机器学习因子挖掘
- [ ] 实盘交易接口
- [ ] 分布式计算支持

## 致谢

感谢以下开源项目：
- [Tushare](https://tushare.pro)
- [AKShare](https://akshare.akfamily.xyz)
- [Backtrader](https://www.backtrader.com)

---

**免责声明**：本工具仅供学习研究使用，不构成任何投资建议。使用本工具进行实盘交易的风险由使用者自行承担。
