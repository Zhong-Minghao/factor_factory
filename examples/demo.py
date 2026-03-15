"""
量化因子工厂 - 综合示例
展示如何使用因子工厂进行因子研发
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


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
    print(f"  因子并行计算: {settings.factor.parallel}")
    print(f"  回测初始资金: ¥{settings.backtest.initial_capital:,.0f}")


def example_2_calendar():
    """示例2: 交易日历"""
    print("\n" + "=" * 70)
    print("示例2: 交易日历")
    print("=" * 70)

    from utils.calendar import get_calendar

    calendar = get_calendar()

    # 获取交易日
    trading_days = calendar.get_trading_days("2024-01-01", "2024-01-31")
    print(f"\n📅 2024年1月的交易日 (共{len(trading_days)}天):")
    print("  " + ", ".join([d.strftime("%m-%d") for d in trading_days[:10]]) + "...")


def example_3_factor_registry():
    """示例3: 因子注册表"""
    print("\n" + "=" * 70)
    print("示例3: 因子注册表")
    print("=" * 70)

    from factors.registry import factor_registry

    # 按类别列出因子
    factors_by_category = factor_registry.list_factors_by_category()

    print("\n📊 已注册因子 (按类别):")
    for category, factors in factors_by_category.items():
        print(f"\n  {category.upper()} ({len(factors)}个):")
        print(f"    {', '.join(factors)}")

    # 查看因子详情
    print("\n📝 因子详情 - MA (移动平均线):")
    info = factor_registry.get_factor_info("MA")
    if info:
        print(f"  名称: {info['name']}")
        print(f"  描述: {info['description']}")
        print(f"  作者: {info['author']}")
        print(f"  版本: {info['version']}")
        print(f"  参数: {info['params']}")


def example_4_compute_factor():
    """示例4: 计算因子"""
    print("\n" + "=" * 70)
    print("示例4: 计算因子")
    print("=" * 70)

    from factors.registry import factor_registry

    # 创建示例数据
    print("\n📈 创建示例数据...")
    np.random.seed(42)
    n = 100
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

    print(f"  生成 {len(data)} 天的数据")
    print(f"  价格范围: ¥{data['close'].min():.2f} - ¥{data['close'].max():.2f}")

    # 计算多个因子
    factors_to_compute = [
        ("MA", {"window": 20}, "20日移动平均线"),
        ("RETURN", {"period": 10}, "10日收益率"),
        ("RSI", {"window": 14}, "相对强弱指标"),
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


def example_5_custom_factor():
    """示例5: 自定义因子"""
    print("\n" + "=" * 70)
    print("示例5: 创建自定义因子")
    print("=" * 70)

    from factors.base import TechnicalFactor
    from factors.registry import factor_registry

    # 定义自定义因子
    print("\n🔧 定义自定义因子...")

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

    print("  ✓ 自定义因子已注册")

    # 使用自定义因子
    print("\n🧮 使用自定义因子...")

    # 创建示例数据
    np.random.seed(42)
    n = 100
    dates = pd.date_range(start="2024-01-01", periods=n, freq="D")
    price = 100 + np.cumsum(np.random.randn(n) * 0.02)

    data = pd.DataFrame({
        "trade_date": dates,
        "close": price,
    })

    # 计算自定义因子
    factor = factor_registry.get("CUSTOM_MA_CROSS", short_window=5, long_window=20)
    values = factor.compute(data)

    print(f"\n  因子名称: {factor.name}")
    print(f"  因子描述: {factor.description}")
    print(f"  统计: 均值={values.mean():.4f}, 标准差={values.std():.4f}")
    print(f"  最新值: {values.iloc[-1]:.4f}")
    print(f"\n  释义:")
    print(f"    值 > 1: 短期均线上穿长期均线 (看涨)")
    print(f"    值 < 1: 短期均线下穿长期均线 (看跌)")


def example_6_data_source():
    """示例6: 数据源使用"""
    print("\n" + "=" * 70)
    print("示例6: 数据源使用 (需要网络连接)")
    print("=" * 70)

    try:
        from data.providers.akshare import AKShareSource

        print("\n📡 连接AKShare数据源...")
        source = AKShareSource()

        if source.connect():
            print("  ✓ 连接成功")

            # 获取股票列表
            print("\n📋 获取股票列表...")
            stock_list = source.get_stock_list()
            print(f"  获取到 {len(stock_list)} 只股票")
            print(f"  前10只: {stock_list.head(10)['ts_code'].tolist()}")

            # 获取单只股票数据
            print("\n📈 获取股票数据...")
            ts_code = "000001.SZ"
            print(f"  正在获取 {ts_code} 的数据...")

            data = source.get_daily_data(
                ts_code=ts_code,
                start_date="2024-01-01",
                end_date="2024-03-15"
            )

            if not data.empty:
                print(f"  ✓ 获取到 {len(data)} 条数据")
                print(f"  日期范围: {data['trade_date'].min()} 到 {data['trade_date'].max()}")
                print(f"  价格范围: ¥{data['close'].min():.2f} - ¥{data['close'].max():.2f}")
                print(f"\n  最新5条数据:")
                print(data[['trade_date', 'open', 'high', 'low', 'close', 'volume']].tail().to_string())
            else:
                print("  ✗ 未获取到数据")

            source.disconnect()
        else:
            print("  ✗ 连接失败")

    except ImportError as e:
        print(f"  ✗ 缺少依赖: {e}")
        print("  请运行: pip install akshare")
    except Exception as e:
        print(f"  ✗ 操作失败: {e}")


def main():
    """运行所有示例"""
    print("\n" + "🚀" * 35)
    print("量化因子工厂 - 综合示例")
    print("🚀" * 35)

    try:
        # 运行各个示例
        example_1_config()
        example_2_calendar()
        example_3_factor_registry()
        example_4_compute_factor()
        example_5_custom_factor()

        # 数据源示例需要网络，注释掉默认运行
        # example_6_data_source()

        print("\n" + "=" * 70)
        print("✅ 所有示例运行完成！")
        print("=" * 70)

        print("\n💡 提示:")
        print("  - 你可以修改这些示例来探索更多功能")
        print("  - 查看examples/目录获取更多示例代码")
        print("  - 阅读文档了解详细的API说明")

    except Exception as e:
        print(f"\n❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
