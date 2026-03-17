# Wind数据源配置指南

## 概述

Wind（万得）是中国领先的金融数据服务提供商，提供全面的金融市场数据。本指南说明如何在因子工厂项目中配置和使用Wind数据源。

## 前置条件

使用Wind数据源前，需要满足以下条件：

1. **安装Wind终端**
   - 购买并安装Wind金融终端
   - 确保终端可以正常运行

2. **安装WindPy库**
   ```bash
   pip install WindPy
   ```

3. **Wind终端登录**
   - 启动Wind终端并完成登录
   - 确保终端保持运行状态

## 配置步骤

### 1. 环境变量配置

在项目根目录的 `.env` 文件中添加以下配置：

```bash
# 启用Wind数据源
DATA_WIND_ENABLED=true

# Wind账号（可选，默认使用终端登录账号）
DATA_WIND_ACCOUNT=your_account

# Wind密码（可选）
DATA_WIND_PASSWORD=your_password

# Wind服务器地址（默认本地）
DATA_WIND_SERVER=localhost
```

### 2. 配置文件设置

在 `config/config.yaml` 中确认以下配置：

```yaml
data:
  # 设置主要数据源为wind
  primary_provider: "wind"

  # Wind配置
  wind_enabled: true
  wind_account: null  # 可选
  wind_password: null  # 可选
  wind_server: "localhost"
```

### 3. 测试连接

运行测试脚本验证Wind连接：

```bash
# 运行完整的数据源测试
python tests/test_data_source.py

# 或运行Wind特定的示例
python examples/wind_demo.py
```

## 使用方法

### 基本使用

```python
from data.providers import WindSource

# 创建Wind数据源实例
source = WindSource()

# 连接Wind
if source.connect():
    print("Wind连接成功")

    # 获取股票列表
    stock_list = source.get_stock_list()

    # 获取日线数据
    data = source.get_daily_data(
        ts_code="000001.SZ",
        start_date="2024-01-01",
        end_date="2024-03-15"
    )

    # 断开连接
    source.disconnect()
```

### 上下文管理器

推荐使用上下文管理器自动管理连接：

```python
from data.providers import WindSource

with WindSource() as source:
    # 获取数据
    data = source.get_daily_data("000001.SZ", "2024-01-01", "2024-03-15")
    print(data)
```

### 批量获取数据

```python
from data.providers import WindSource

with WindSource() as source:
    # 批量获取多只股票数据
    codes = ["000001.SZ", "000002.SZ", "600000.SH"]
    batch_data = source.get_daily_data_batch(
        ts_codes=codes,
        start_date="2024-01-01",
        end_date="2024-03-15"
    )

    for code, df in batch_data.items():
        print(f"{code}: {len(df)} 条数据")
```

## 支持的数据接口

Wind数据源实现了以下接口：

### 1. 基础行情数据

- **get_stock_list()**: 获取股票列表
- **get_daily_data()**: 获取单只股票日线数据
- **get_daily_data_batch()**: 批量获取多只股票日线数据
- **get_index_data()**: 获取指数数据

### 2. 财务数据

- **get_financial_data()**: 获取财务指标数据
  - PE、PB、PS等估值指标
  - 总市值、流通市值

### 3. 补充数据

- **get_fund_flow()**: 获取资金流向数据
- **get_index_weight()**: 获取指数成分股权重
- **get_trade_calendar()**: 获取交易日历

## Wind数据格式说明

### 股票代码格式

Wind使用标准的股票代码格式：
- 深交所：`000001.SZ`
- 上交所：`600000.SH`

### 日期格式

输入日期格式：`YYYY-MM-DD` (如：`2024-01-01`)
Wind内部格式：`YYYYMMDD` (如：`20240101`)

### 返回数据格式

所有返回的DataFrame都经过标准化处理，包含以下列：
- `trade_date`: 交易日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `amount`: 成交额

## 常见问题

### 1. 连接失败

**问题**: 无法连接到Wind

**解决方案**:
- 确保Wind终端已启动并登录
- 检查WindPy是否正确安装
- 验证Wind服务器地址配置

### 2. 权限错误

**问题**: 提示无权限访问某些数据

**解决方案**:
- 检查Wind账号权限
- 联系Wind客服开通相应数据权限

### 3. 数据不存在

**问题**: 返回空数据

**解决方案**:
- 检查股票代码是否正确
- 确认日期范围内是否有交易日
- 验证该数据是否在订阅范围内

### 4. 频率限制

**问题**: 请求过于频繁导致失败

**解决方案**:
- Wind数据源已内置频率限制（默认0.05秒间隔）
- 可调整 `_min_interval` 参数修改请求间隔

## 性能优化建议

1. **批量获取**: 尽量使用批量接口获取多只股票数据
2. **本地缓存**: 启用缓存功能减少重复请求
3. **请求间隔**: 根据实际需求调整请求频率
4. **连接复用**: 使用上下文管理器保持连接，避免频繁连接/断开

## 与其他数据源对比

| 特性 | Wind | Tushare | AKShare |
|------|------|---------|---------|
| 数据质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 数据完整性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 成本 | 付费 | 免费付费 | 免费 |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 易用性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 参考资源

- Wind官网：https://www.wind.com.cn/
- WindPy文档：https://www.windquant.com/qntcloud/api
- Wind社区：https://www.windquant.com/

## 技术支持

如遇到问题，请：
1. 检查本文档的常见问题部分
2. 查看Wind官方文档
3. 在项目issue中提问
