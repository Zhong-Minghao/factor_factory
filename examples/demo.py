"""
量化因子工厂 - 综合示例
展示如何使用因子工厂进行因子研发、数据获取和因子计算
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# 第一部分：配置与基础设施
# =============================================================================

def example_1_config():
    """示例1: 配置管理"""
    print("\n" + "=" * 70)
    print("示例1: 配置管理")
    print("=" * 70)

    from config.settings import get_settings

    settings = get_settings()

    print("\n📋 当前配置:")
    print(f"  项目根目录: {settings.project_root}")
    print(f"  数据目录: {settings.get_data_path()}")
    print(f"  缓存目录: {settings.get_cache_path()}")
    print(f"  主要数据源: {settings.data.primary_provider}")
    print(f"  存储格式: {settings.data.storage_format}")
    print(f"  回测初始资金: ¥{settings.backtest.initial_capital:,.0f}")
    print(f"  Wind数据源启用: {settings.data.wind_enabled}")


def example_2_calendar():
    """示例2: 交易日历"""
    print("\n" + "=" * 70)
    print("示例2: 交易日历")
    print("=" * 70)

    from utils.calendar import get_calendar

    calendar = get_calendar()

    # 先更新交易日历（会自动使用配置的数据源，优先Wind API）
    print("\n🔄 更新交易日历...")
    success = calendar.update_trading_days("2024-01-01", "2024-01-31")
    if success:
        print("  ✓ 成功从Wind API更新交易日历")
    else:
        print("  ⚠ Wind不可用，使用工作日作为交易日（不含节假日）")

    # 获取交易日
    trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
    print(f"\n📅 2024年1月的交易日 (共{len(trading_days)}天):")
    print("  " + ", ".join([d.strftime("%m-%d") for d in trading_days[:10]]) + "...")


# =============================================================================
# 第二部分：因子注册表
# =============================================================================

def example_3_factor_registry():
    """示例3: 因子注册表"""
    print("\n" + "=" * 70)
    print("示例3: 因子注册表")
    print("=" * 70)

    from factors.registry import factor_registry

    # 查看已注册因子
    print(f"\n📊 总共有 {factor_registry.count()} 个已注册因子")

    # 按类别列出因子
    factors_by_category = factor_registry.list_factors_by_category()
    print("\n📋 已注册因子 (按类别):")
    for category, factors in factors_by_category.items():
        print(f"\n  {category.upper()} ({len(factors)}个):")
        print(f"    {', '.join(factors)}")

    # 查看因子详情
    print("\n📝 因子详情 - MA (移动平均线):")
    info = factor_registry.get_factor_info("MA")
    if info:
        print(f"  名称: {info['name']}")
        print(f"  描述: {info['description']}")
        print(f"  参数: {info['params']}")

    # 检查因子是否存在
    print(f"\n🔍 检查因子是否存在:")
    print(f"  'MA' 是否存在: {factor_registry.exists('MA')}")
    print(f"  'MY_CUSTOM_FACTOR' 是否存在: {factor_registry.exists('MY_CUSTOM_FACTOR')}")


def example_4_register_custom_factor():
    """示例4: 注册自定义因子"""
    print("\n" + "=" * 70)
    print("示例4: 注册自定义因子")
    print("=" * 70)

    from factors.base import TechnicalFactor
    from factors.registry import factor_registry

    print(f"\n当前注册因子数量: {factor_registry.count()}")

    # 方法1: 使用装饰器注册（推荐）
    print("\n🔧 方法1: 使用装饰器注册因子")

    @factor_registry.register("CUSTOM_RSI")
    class CustomRSI(TechnicalFactor):
        """自定义RSI指标"""

        name = "CUSTOM_RSI"
        description = "相对强弱指标-增强版"
        author = "用户"
        version = "1.0.0"
        category = "technical"
        params = {"window": 14, "threshold": 70}

        def compute(self, data):
            """计算RSI"""
            window = self.params.get("window", 14)
            delta = data["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

    print(f"  ✓ 因子 'CUSTOM_RSI' 注册成功")
    print(f"  当前注册因子数量: {factor_registry.count()}")

    # 方法2: 定义均线交叉因子
    print("\n🔧 方法2: 定义自定义因子 - 均线交叉")

    @factor_registry.register("CUSTOM_MA_CROSS")
    class CustomMACross(TechnicalFactor):
        """自定义因子：均线交叉"""

        name = "CUSTOM_MA_CROSS"
        description = "短期均线与长期均线的交叉"
        author = "用户"
        version = "1.0.0"
        params = {"short_window": 5, "long_window": 20}

        def compute(self, data):
            """计算均线交叉"""
            short_window = self.params.get("short_window", 5)
            long_window = self.params.get("long_window", 20)

            # 计算短期和长期均线
            short_ma = data["close"].rolling(window=short_window).mean()
            long_ma = data["close"].rolling(window=long_window).mean()

            # 返回短期均线与长期均线的比率
            return short_ma / long_ma

    print(f"  ✓ 因子 'CUSTOM_MA_CROSS' 注册成功")

    # 验证新注册的因子
    print("\n✅ 验证新注册的因子:")
    print(f"  'CUSTOM_RSI' 是否存在: {factor_registry.exists('CUSTOM_RSI')}")
    print(f"  'CUSTOM_MA_CROSS' 是否存在: {factor_registry.exists('CUSTOM_MA_CROSS')}")


# =============================================================================
# 第三部分：因子计算
# =============================================================================

def create_sample_data(n=100):
    """创建示例数据"""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=n, freq="D")
    price = 100 + np.cumsum(np.random.randn(n) * 0.02)

    data = pd.DataFrame({
        "trade_date": dates,
        "open": price * (1 + np.random.randn(n) * 0.005),
        "high": price * (1 + abs(np.random.randn(n)) * 0.01),
        "low": price * (1 - abs(np.random.randn(n)) * 0.01),
        "close": price,
        "volume": np.random.randint(1000000, 10000000, n),
        "amount": price * np.random.randint(1000000, 10000000, n),
    })
    return data


def example_5_single_factor():
    """示例5: 单因子计算"""
    print("\n" + "=" * 70)
    print("示例5: 单因子计算")
    print("=" * 70)

    from factors.registry import factor_registry

    # 创建示例数据
    print("\n📈 创建示例数据...")
    data = create_sample_data()
    print(f"  生成 {len(data)} 天的数据")
    print(f"  价格范围: ¥{data['close'].min():.2f} - ¥{data['close'].max():.2f}")

    # 计算多个因子
    factors_to_compute = [
        ("MA", {"window": 20}, "20日移动平均线"),
        ("RETURN", {"period": 10}, "10日收益率"),
        ("RSI", {"window": 14}, "相对强弱指标"),
        ("MACD", {}, "MACD指标"),
        ("VOLUME_RATIO", {"window": 5}, "量比"),
    ]

    print("\n🧮 计算因子:")
    for factor_name, params, description in factors_to_compute:
        try:
            factor = factor_registry.get(factor_name, **params)
            values = factor.compute(data)

            print(f"\n  {factor_name} - {description}")
            print(f"    参数: {params}")
            print(f"    统计: 均值={values.mean():.4f}, 标准差={values.std():.4f}")
            print(f"    范围: [{values.min():.4f}, {values.max():.4f}]")
            print(f"    最新值: {values.iloc[-1]:.4f}")

        except Exception as e:
            print(f"\n  {factor_name}: 计算失败 - {e}")


def example_6_batch_factors():
    """示例6: 批量因子计算"""
    print("\n" + "=" * 70)
    print("示例6: 批量因子计算")
    print("=" * 70)

    from factors.registry import factor_registry

    # 创建示例数据
    print("\n📈 创建示例数据...")
    data = create_sample_data()
    print(f"  生成 {len(data)} 天的数据")

    # 批量计算多个因子
    # 如需使用因子引擎的批量计算功能，可以创建 FactorEngine 实例
    # engine = FactorEngine()
    factors_to_compute = [
        ("MA", {"window": 5}),
        ("MA", {"window": 20}),
        ("RSI", {"window": 14}),
        ("MACD", {}),
        ("VOLUME_RATIO", {"window": 5}),
        ("RETURN", {"period": 10}),
    ]

    print(f"\n✓ 准备计算 {len(factors_to_compute)} 个因子...")

    results = {}
    for factor_name, params in factors_to_compute:
        print(f"\n  计算 {factor_name} (参数: {params})...")
        factor = factor_registry.get(factor_name, **params)
        values = factor.compute(data)
        results[f"{factor_name}_{str(params)}"] = values

        print(f"    ✓ 有效数据点: {values.notna().sum()}")
        print(f"    最新值: {values.iloc[-1]:.4f}")

    # 组合结果
    result_df = pd.DataFrame(results)
    print(f"\n✓ 计算完成！结果维度: {result_df.shape}")

    # 保存结果
    output_file = project_root / "data" / "factor_results.csv"
    output_file.parent.mkdir(exist_ok=True)
    result_df.to_csv(output_file)
    print(f"✓ 结果已保存到: {output_file}")


def example_7_custom_factor_compute():
    """示例7: 使用自定义因子计算"""
    print("\n" + "=" * 70)
    print("示例7: 使用自定义因子计算")
    print("=" * 70)

    from factors.registry import factor_registry

    # 创建示例数据
    print("\n📈 创建示例数据...")
    data = create_sample_data()

    # 计算自定义因子
    print("\n🧮 计算自定义因子...")

    # 自定义RSI
    custom_rsi = factor_registry.get("CUSTOM_RSI", window=14)
    if custom_rsi:
        rsi_values = custom_rsi.compute(data)
        print(f"\n  CUSTOM_RSI(14) - 自定义RSI")
        print(f"    最新值: {rsi_values.iloc[-1]:.2f}")
        print(f"    均值: {rsi_values.mean():.2f}")

    # 均线交叉因子
    ma_cross = factor_registry.get("CUSTOM_MA_CROSS", short_window=5, long_window=20)
    if ma_cross:
        cross_values = ma_cross.compute(data)
        print(f"\n  CUSTOM_MA_CROSS(5,20) - 均线交叉")
        print(f"    最新值: {cross_values.iloc[-1]:.4f}")
        print(f"    释义:")
        print(f"      值 > 1: 短期均线上穿长期均线 (看涨)")
        print(f"      值 < 1: 短期均线下穿长期均线 (看跌)")


def example_8_factor_statistics():
    """示例8: 因子统计分析"""
    print("\n" + "=" * 70)
    print("示例8: 因子统计分析")
    print("=" * 70)

    from factors.registry import factor_registry

    # 创建示例数据
    print("\n📈 创建示例数据...")
    data = create_sample_data()

    # 计算多个因子
    factors = {
        "MA5": factor_registry.get("MA", window=5),
        "MA20": factor_registry.get("MA", window=20),
        "RSI": factor_registry.get("RSI", window=14),
        "RETURN": factor_registry.get("RETURN", period=10),
    }

    results = {}
    for name, factor in factors.items():
        values = factor.compute(data)
        results[name] = values

    result_df = pd.DataFrame(results)

    print(f"\n因子统计摘要:")
    print(f"\n{result_df.describe()}")

    print(f"\n缺失值统计:")
    print(result_df.isna().sum())

    # 计算因子相关性
    print(f"\n因子相关性:")
    print(result_df.corr())


# =============================================================================
# 第四部分：数据源使用
# =============================================================================

def example_9_wind_source():
    """示例9: Wind数据源使用（需要Wind环境）"""
    print("\n" + "=" * 70)
    print("示例9: Wind数据源使用（需要Wind环境）")
    print("=" * 70)

    from config.settings import get_settings
    from data.providers import WindSource

    settings = get_settings()

    # 检查Wind是否启用
    if not settings.data.wind_enabled:
        print("\n[!] Wind数据源未启用")
        print("\n如需使用Wind数据源，请：")
        print("  1. 确保已安装Wind终端")
        print("  2. 安装WindPy: pip install WindPy")
        print("  3. 在.env文件中设置 DATA_WIND_ENABLED=true")
        print("  4. （可选）设置 DATA_WIND_ACCOUNT 和 DATA_WIND_PASSWORD")
        return

    # 创建Wind数据源
    print("\n[步骤1] 创建Wind数据源连接...")
    source = WindSource()

    try:
        # 连接Wind
        print("  正在连接Wind...")
        if source.connect():
            print("  [OK] Wind连接成功")
        else:
            print("  [FAIL] Wind连接失败")
            return

        # 获取股票列表
        print("\n[步骤2] 获取股票列表...")
        stock_list = source.get_stock_list()
        print(f"  [OK] 获取到 {len(stock_list)} 只股票")
        print(f"  前5只股票:")
        print(stock_list.head())

        # 获取单只股票日线数据
        print("\n[步骤3] 获取单只股票日线数据...")
        ts_code = "sz000001"  # 平安银行（使用 internal_id 格式）
        print(f"  获取股票: {ts_code}")

        data = source.get_daily_data(
            ts_code=ts_code,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        if not data.empty:
            print(f"  [OK] 获取到 {len(data)} 条数据")
            print(f"  数据列: {data.columns.tolist()}")
            print(f"  最新5条数据:")
            print(data.tail())
        else:
            print("  [FAIL] 未获取到数据")

        # 批量获取多只股票数据
        print("\n[步骤4] 批量获取多只股票数据...")
        codes = ["sz000001", "sz000002", "sh600000"]  # 使用 internal_id 格式
        print(f"  获取股票: {codes}")

        batch_data = source.get_daily_data_batch(
            ts_codes=codes,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        print(f"  [OK] 成功获取 {len(batch_data)} 只股票的数据")
        for code, df in batch_data.items():
            print(f"    {code}: {len(df)} 条数据")

        # 断开连接
        print("\n[步骤5] 断开连接...")
        source.disconnect()
        print("  [OK] 已断开连接")

    except ImportError as e:
        print(f"  [FAIL] 缺少依赖: {e}")
        print("  请运行: pip install WindPy")
    except Exception as e:
        print(f"  [FAIL] 执行失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 确保断开连接
        if source.is_connected():
            source.disconnect()


def example_11_wind_calendar_api():
    """示例11: Wind交易日历API测试（需要Wind环境）"""
    print("\n" + "=" * 70)
    print("示例11: Wind交易日历API测试（需要Wind环境）")
    print("=" * 70)

    try:
        from data.providers import WindSource

        with WindSource() as wind:
            print("\n1. 测试w.tdays() API（获取交易日）")
            start_date = "2024-02-19"
            end_date = "2024-03-19"

            # 转换为Wind格式
            wind_start = start_date.replace("-", "")
            wind_end = end_date.replace("-", "")

            print(f"   日期范围: {start_date} 至 {end_date}")
            print(f"   Wind格式: {wind_start} 至 {wind_end}")

            # 调用w.tdays
            result = wind.api.tdays(wind_start, wind_end)

            print(f"\n   返回结果:")
            print(f"   ErrorCode: {result.ErrorCode}")
            print(f"   Times: {result.Times}")

            if result.ErrorCode == 0 and result.Times:
                print(f"\n   ✓ 成功获取 {len(result.Times)} 个交易日")
                print(f"   前5个: {result.Times[:5]}")
                print(f"   数据类型: {type(result.Times[0])}")
            else:
                print(f"\n   ✗ API返回错误或无数据")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        print("  提示: 请确保已安装WindPy并连接Wind终端")


# =============================================================================
# 主函数
# =============================================================================

def main():
    """运行所有示例"""
    print("\n" + "🚀" * 35)
    print("量化因子工厂 - 综合示例")
    print("🚀" * 35)

    try:
        # 第一部分：配置与基础设施
        print("\n" + "📦" * 35)
        print("第一部分：配置与基础设施")
        print("📦" * 35)
        example_1_config()
        example_2_calendar()

        # 第二部分：因子注册表
        print("\n" + "📊" * 35)
        print("第二部分：因子注册表")
        print("📊" * 35)
        example_3_factor_registry()
        example_4_register_custom_factor()

        # 第三部分：因子计算
        print("\n" + "🧮" * 35)
        print("第三部分：因子计算")
        print("🧮" * 35)
        example_5_single_factor()
        example_6_batch_factors()
        example_7_custom_factor_compute()
        example_8_factor_statistics()

        # 第四部分：数据源使用（需要特定环境，可选运行）
        print("\n" + "📡" * 35)
        print("第四部分：数据源使用（可选）")
        print("📡" * 35)
        print("\n提示: 以下示例需要特定环境（Wind/AKShare）")
        print("如需运行，请取消相应注释\n")

        # 取消以下注释以运行数据源示例
        example_9_wind_source()        # 需要Wind环境
        # example_10_akshare_source()    # 需要网络连接
        example_11_wind_calendar_api() # 需要Wind环境

        print("\n" + "=" * 70)
        print("✅ 基础示例运行完成！")
        print("=" * 70)

        print("\n💡 提示:")
        print("  - 你可以修改这些示例来探索更多功能")
        print("  - 查看factors/目录了解因子实现")
        print("  - 查看data/providers/目录了解数据源实现")
        print("  - 阅读文档了解详细的API说明")

        print("\n🔧 常用API总结:")
        print("  因子注册表:")
        print("    - factor_registry.list_factors()")
        print("    - factor_registry.get_factor_info('因子名')")
        print("    - factor = factor_registry.get('因子名', 参数...)")
        print("  交易日历:")
        print("    - calendar = get_calendar()")
        print("    - trading_days = calendar.get_trading_days(开始, 结束)")
        print("  数据源:")
        print("    - source = WindSource() / AKShareSource()")
        print("    - data = source.get_daily_data(代码, 开始, 结束)")

    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


# def example_10_akshare_source():
#     """示例10: AKShare数据源使用（需要网络连接）"""
#     print("\n" + "=" * 70)
#     print("示例10: AKShare数据源使用（需要网络连接）")
#     print("=" * 70)

#     try:
#         from data.providers.akshare import AKShareSource

#         print("\n📡 连接AKShare数据源...")
#         source = AKShareSource()

#         if source.connect():
#             print("  ✓ 连接成功")

#             # 获取股票列表
#             print("\n📋 获取股票列表...")
#             stock_list = source.get_stock_list()
#             print(f"  获取到 {len(stock_list)} 只股票")
#             print(f"  前10只: {stock_list.head(10)['ts_code'].tolist()}")

#             # 获取单只股票数据
#             print("\n📈 获取股票数据...")
#             ts_code = "sz000001"  # 使用 internal_id 格式
#             print(f"  正在获取 {ts_code} 的数据...")

#             data = source.get_daily_data(
#                 ts_code=ts_code,
#                 start_date="2024-01-01",
#                 end_date="2024-03-15"
#             )

#             if not data.empty:
#                 print(f"  ✓ 获取到 {len(data)} 条数据")
#                 print(f"  日期范围: {data['trade_date'].min()} 到 {data['trade_date'].max()}")
#                 print(f"  价格范围: ¥{data['close'].min():.2f} - ¥{data['close'].max():.2f}")
#                 print(f"\n  最新5条数据:")
#                 print(data[['trade_date', 'open', 'high', 'low', 'close', 'volume']].tail().to_string())
#             else:
#                 print("  ✗ 未获取到数据")

#             source.disconnect()
#         else:
#             print("  ✗ 连接失败")

#     except ImportError as e:
#         print(f"  ✗ 缺少依赖: {e}")
#         print("  请运行: pip install akshare")
#     except Exception as e:
#         print(f"  ✗ 操作失败: {e}")