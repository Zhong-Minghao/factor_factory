# 测试指南

本文档说明如何测试量化因子工厂的各个功能。

## 前置准备

### 1. 安装依赖

首先确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置数据源（可选）

如果要测试数据源功能，需要配置Tushare Token：

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑`.env`文件，填写你的Tushare Token：
```
TUSHARE_TOKEN=your_token_here
```

获取Token: https://tushare.pro/register

## 运行测试

### 方法1: 运行所有测试

使用统一的测试脚本：

```bash
python run_tests.py
```

这个脚本会依次测试：
- 配置管理系统
- 交易日历工具
- 因子系统
- 数据源接口（可选）

### 方法2: 单独运行测试

#### 测试1: 配置管理系统

```bash
python tests/test_config.py
```

**测试内容：**
- 加载默认配置
- 路径获取功能
- 配置信息展示

**预期输出：**
```
============================================================
测试配置管理系统
============================================================

[测试1] 加载默认配置...
✓ 项目根目录: /path/to/factor_factory
✓ 数据目录: data
✓ 缓存目录: cache
...
```

#### 测试2: 交易日历工具

```bash
python tests/test_calendar.py
```

**测试内容：**
- 交易日判断
- 交易日列表获取
- 前后交易日查询

**预期输出：**
```
============================================================
测试交易日历工具
============================================================

[测试1] 基本交易日判断...
  2024-03-15 (Friday): 交易日
  2024-03-16 (Saturday): 非交易日
...
```

#### 测试3: 因子系统

```bash
python tests/test_factors.py
```

**测试内容：**
- 因子注册表
- 因子计算
- 因子引擎

**预期输出：**
```
============================================================
🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬
因子系统测试套件
🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬

============================================================
测试因子注册表
============================================================

[测试1] 列出所有已注册因子...
  ✓ 已注册因子总数: 37
  所有因子: MA, EMA, MACD, RSI, ...
```

#### 测试4: 数据源接口（需要网络）

```bash
python tests/test_data_source.py
```

**测试内容：**
- AKShare数据源（免费，无需token）
- Tushare数据源（需要token）

**预期输出：**
```
============================================================
测试数据源接口
============================================================

[测试1] 测试AKShare数据源...
  正在连接AKShare...
  ✓ AKShare连接成功

  获取股票列表...
  ✓ 获取到 5000+ 只股票
...
```

### 方法3: 运行示例代码

```bash
python examples/demo.py
```

这个示例会展示：
- 配置管理
- 交易日历使用
- 因子注册表
- 因子计算
- 自定义因子创建
- 数据源使用（可选）

## 手动测试

### 测试配置管理

在Python交互环境中：

```python
from config.settings import get_settings

settings = get_settings()
print(f"项目根目录: {settings.project_root}")
print(f"数据目录: {settings.data.data_dir}")
print(f"缓存目录: {settings.data.cache_dir}")
```

### 测试交易日历

```python
from utils.calendar import get_calendar
from datetime import date

calendar = get_calendar()

# 判断是否为交易日
is_trading = calendar.is_trading_day(date(2024, 3, 15))
print(f"2024-03-15 是交易日: {is_trading}")

# 获取交易日列表
trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
print(f"2024年1月的交易日: {len(trading_days)}天")
```

### 测试因子系统

```python
from factors.registry import factor_registry
import pandas as pd
import numpy as np

# 列出所有因子
all_factors = factor_registry.list_factors()
print(f"可用因子: {len(all_factors)}个")
print(f"因子列表: {', '.join(all_factors[:10])}")

# 计算因子
factor = factor_registry.get("MA", window=20)

# 创建示例数据
data = pd.DataFrame({
    "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109] * 10
})

# 计算因子值
factor_values = factor.compute(data)
print(f"因子值:\n{factor_values.tail()}")
```

### 创建自定义因子

```python
from factors.base import TechnicalFactor
from factors.registry import factor_registry

@factor_registry.register("MY_FACTOR")
class MyFactor(TechnicalFactor):
    """我的自定义因子"""

    name = "MY_FACTOR"
    description = "示例因子"
    author = "Your Name"
    version = "1.0.0"
    params = {"window": 10}

    def compute(self, data):
        window = self.params.get("window", 10)
        return data["close"].pct_change(window)

# 使用自定义因子
factor = factor_registry.get("MY_FACTOR", window=5)
print(f"因子名称: {factor.name}")
print(f"因子描述: {factor.description}")
```

## 常见问题

### Q1: 提示"Python未找到"

**解决方案：**
1. 确保已安装Python 3.10+
2. 将Python添加到系统PATH
3. 或使用完整路径运行，如：`C:\Python311\python.exe run_tests.py`

### Q2: 提示缺少依赖包

**解决方案：**
```bash
pip install -r requirements.txt
```

### Q3: Tushare测试失败

**解决方案：**
1. 确保已在`.env`文件中配置了正确的Token
2. Token格式应该是一串字符，不要有引号或空格
3. 确认Token是否有效（访问 https://tushare.pro）

### Q4: AKShare测试失败

**解决方案：**
1. 检查网络连接
2. 安装或更新akshare：`pip install --upgrade akshare`
3. 某些数据可能暂时不可用，可以稍后重试

### Q5: 因子计算报错

**解决方案：**
1. 确保输入数据包含所需的列：open, high, low, close, volume, amount
2. 检查数据格式是否正确（DataFrame，包含trade_date列）
3. 查看错误信息，可能是参数设置不当

## 测试检查清单

完成以下检查确保系统正常：

- [ ] 配置管理系统能正常加载配置
- [ ] 交易日历工具能正确判断交易日
- [ ] 能列出所有已注册的因子
- [ ] 能成功计算至少3个不同的因子
- [ ] 能创建和使用自定义因子
- [ ] （可选）AKShare数据源能正常获取数据
- [ ] （可选）Tushare数据源能正常获取数据

## 下一步

测试通过后，你可以：

1. **开发自己的因子**
   - 参考`factors/library/`中的示例
   - 使用`@factor_registry.register()`装饰器注册

2. **获取真实数据**
   - 配置Tushare或AKShare
   - 使用数据源接口获取历史数据

3. **准备回测**
   - 等待回测系统实现
   - 准备测试你的因子策略

## 获取帮助

如果遇到问题：

1. 查看错误信息和堆栈跟踪
2. 检查依赖是否完整安装
3. 参考示例代码
4. 查看README.md文档

---

**祝测试顺利！** 🎉
