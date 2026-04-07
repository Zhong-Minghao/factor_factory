"""
检查数据格式脚本 - 帮助诊断 IC 计算问题
"""
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_data_format(factor_data, price_data):
    """检查数据格式是否正确"""

    print("=" * 70)
    print("数据格式检查")
    print("=" * 70)

    # 检查 factor_data
    print("\n[1] 因子数据 (factor_data):")
    print("-" * 70)
    print(f"  类型: {type(factor_data)}")
    print(f"  形状: {factor_data.shape}")
    print(f"  索引类型: {type(factor_data.index)}")
    print(f"  索引示例: {factor_data.index[:3].tolist()}")
    print(f"  列名示例: {factor_data.columns[:3].tolist()}")
    print(f"  数据示例:\n{factor_data.iloc[:3, :3]}")

    # 检查 price_data
    print("\n[2] 价格数据 (price_data):")
    print("-" * 70)
    print(f"  类型: {type(price_data)}")
    print(f"  形状: {price_data.shape}")

    if isinstance(price_data, pd.DataFrame):
        print(f"  索引类型: {type(price_data.index)}")
        print(f"  索引示例: {price_data.index[:3].tolist()}")
        print(f"  列名: {price_data.columns.tolist()}")
        print(f"  数据示例:\n{price_data.iloc[:3, :min(5, len(price_data.columns))]}")

    # 检查 price_data[['close']]
    if isinstance(price_data, pd.DataFrame) and 'close' in price_data.columns:
        print("\n[3] price_data[['close']]:")
        print("-" * 70)
        close_df = price_data[['close']]
        print(f"  类型: {type(close_df)}")
        print(f"  形状: {close_df.shape}")
        print(f"  索引示例: {close_df.index[:3].tolist()}")
        print(f"  列名: {close_df.columns.tolist()}")
        print(f"  数据示例:\n{close_df.iloc[:3, :]}")

    # 问题诊断
    print("\n" + "=" * 70)
    print("问题诊断")
    print("=" * 70)

    # 期望的格式
    print("\n[期望格式] compute_daily_ic 需要的格式:")
    print("-" * 70)
    print("  factor_data:")
    print("    - index: trade_date (交易日)")
    print("    - columns: ts_code (股票代码)")
    print("    - values: factor_value (因子值)")
    print("\n  price_data:")
    print("    - index: trade_date (交易日)")
    print("    - columns: ts_code (股票代码)")
    print("    - values: close_price (收盘价)")

    # 检查当前格式
    print("\n[当前格式] 您的数据格式:")
    print("-" * 70)

    if isinstance(price_data, pd.DataFrame):
        if 'close' in price_data.columns and 'open' in price_data.columns:
            print("  ❌ price_data 是长表格式 (列: open, high, low, close, ...)")
            print("     这是 WindSource.get_daily_data() 返回的原始格式")
            print("     需要转换为宽表格式 (列: 股票代码)")
            print("\n  解决方案:")
            print("    1. 如果只获取了一只股票的数据，需要获取多只股票")
            print("    2. 需要将长表转换为宽表 (pivot/unstack)")
        elif len(price_data.columns) > 10:
            print("  ✓ price_data 可能是宽表格式 (列数 > 10)")
            print(f"    列名示例: {price_data.columns[:3].tolist()}")

    # 检查索引是否对齐
    print("\n[索引对齐检查]")
    print("-" * 70)
    if isinstance(factor_data, pd.DataFrame) and isinstance(price_data, pd.DataFrame):
        factor_dates = set(factor_data.index)
        price_dates = set(price_data.index)

        common_dates = factor_dates.intersection(price_dates)
        print(f"  factor_data 日期范围: {factor_data.index.min()} ~ {factor_data.index.max()}")
        print(f"  price_data 日期范围: {price_data.index.min()} ~ {price_data.index.max()}")
        print(f"  共同日期数量: {len(common_dates)}")

        if len(common_dates) == 0:
            print("  ❌ 没有共同的日期！无法计算 IC")

    return True


# 示例：如何转换数据格式
def show_conversion_example():
    """展示如何转换数据格式"""
    print("\n" + "=" * 70)
    print("数据转换示例")
    print("=" * 70)

    print("\n[方案 1] 使用 WindSource 批量获取多只股票数据:")
    print("-" * 70)
    print("""
    from data.providers import WindSource

    wind = WindSource()
    wind.connect()

    # 方式 1: 批量获取多只股票
    price_dict = wind.get_daily_data_batch(
        ts_codes=['000001.SZ', '000002.SZ', '600000.SH'],
        start_date='2020-01-01',
        end_date='2024-12-31'
    )

    # 转换为宽表格式
    price_list = []
    for ts_code, df in price_dict.items():
        df['ts_code'] = ts_code
        price_list.append(df[['close', 'ts_code']])

    price_wide = pd.concat(price_list).pivot(
        index='trade_date',
        columns='ts_code',
        values='close'
    )
    """)

    print("\n[方案 2] 使用因子引擎自动处理:")
    print("-" * 70)
    print("""
    from data.providers import WindSource
    from factors.engine import FactorEngine

    wind = WindSource()
    wind.connect()

    # 获取多只股票数据
    price_dict = wind.get_daily_data_batch(
        ts_codes=['000001.SZ', '000002.SZ', '600000.SH'],
        start_date='2020-01-01',
        end_date='2024-12-31'
    )

    # 转换为宽表
    price_list = []
    for ts_code, df in price_dict.items():
        df['ts_code'] = ts_code
        price_list.append(df[['close', 'ts_code']])

    price_wide = pd.concat(price_list).pivot(
        index='trade_date',
        columns='ts_code',
        values='close'
    )

    # 计算因子
    engine = FactorEngine()
    factor_data = engine.compute_factor('EMA', price_wide)

    # 计算 IC
    from analysis.ic_ir import ICAnalyzer

    analyzer = ICAnalyzer()
    ic_series = analyzer.compute_daily_ic(factor_data, price_wide, period=5)
    """)


def show_fix_suggestions(factor_data=None, price_data=None):
    """显示修复建议"""
    print("\n" + "=" * 70)
    print("修复建议")
    print("=" * 70)

    if factor_data is None or price_data is None:
        print("\n提示：传入 factor_data 和 price_data 参数以获取针对性的修复建议")
        return

    # 检查 price_data 格式
    if isinstance(price_data, pd.DataFrame):
        if 'close' in price_data.columns and 'open' in price_data.columns:
            print("\n[问题] price_data 是长表格式")
            print("[解决方案] 转换为宽表格式：")
            print("""
# 步骤 1: 批量获取多只股票数据
price_dict = wind.get_daily_data_batch(
    ts_codes=['000001.SZ', '000002.SZ', '600000.SH'],
    start_date='2020-01-01',
    end_date='2024-12-31'
)

# 步骤 2: 转换为宽表
price_list = []
for ts_code, df in price_dict.items():
    df['ts_code'] = ts_code
    price_list.append(df[['close', 'ts_code']])

price_wide = pd.concat(price_list).pivot(
    index='trade_date',
    columns='ts_code',
    values='close'
)

# 步骤 3: 使用宽表格式计算 IC
ic_series = analyzer.compute_daily_ic(factor_data, price_wide, period=5)
""")

    # 检查股票代码匹配
    if isinstance(factor_data, pd.DataFrame) and isinstance(price_data, pd.DataFrame):
        # 检查是否为宽表格式
        factor_is_long = 'close' in factor_data.columns and 'open' in factor_data.columns
        price_is_long = 'close' in price_data.columns and 'open' in price_data.columns

        if not factor_is_long and not price_is_long:
            factor_stocks = set(factor_data.columns)
            price_stocks = set(price_data.columns)
            common_stocks = factor_stocks.intersection(price_stocks)

            if len(common_stocks) < len(factor_stocks) or len(common_stocks) < len(price_stocks):
                print(f"\n[问题] 股票代码不匹配")
                print(f"  factor_data 股票数: {len(factor_stocks)}")
                print(f"  price_data 股票数: {len(price_stocks)}")
                print(f"  共同股票数: {len(common_stocks)}")
                print("\n[解决方案] 使用共同股票：")
                print("""
# 找到共同股票
common_stocks = set(factor_data.columns).intersection(set(price_data.columns))

# 只使用共同股票
factor_data = factor_data[list(common_stocks)]
price_data = price_data[list(common_stocks)]

# 重新计算 IC
ic_series = analyzer.compute_daily_ic(factor_data, price_data, period=5)
""")

    # 检查日期范围
    if isinstance(factor_data, pd.DataFrame) and isinstance(price_data, pd.DataFrame):
        factor_dates = factor_data.index
        price_dates = price_data.index

        common_dates = factor_dates.intersection(price_dates)

        if len(common_dates) == 0:
            print(f"\n[问题] 没有共同的日期")
            print(f"  factor_data 日期范围: {factor_dates.min()} ~ {factor_dates.max()}")
            print(f"  price_data 日期范围: {price_dates.min()} ~ {price_dates.max()}")
            print("\n[解决方案] 对齐日期范围：")
            print("""
# 确保日期格式一致
factor_data.index = pd.to_datetime(factor_data.index)
price_data.index = pd.to_datetime(price_data.index)

# 对齐日期范围
start_date = max(factor_data.index.min(), price_data.index.min())
end_date = min(factor_data.index.max(), price_data.index.max())

factor_data = factor_data.loc[start_date:end_date]
price_data = price_data.loc[start_date:end_date]
""")
        elif len(common_dates) < min(len(factor_dates), len(price_dates)) * 0.9:
            print(f"\n[警告] 日期范围部分重叠")
            print(f"  factor_data 日期数: {len(factor_dates)}")
            print(f"  price_data 日期数: {len(price_dates)}")
            print(f"  共同日期数: {len(common_dates)}")
            print("\n[建议] 检查数据源的日期范围是否一致")

    print("\n" + "=" * 70)
    print("💡 更多帮助：")
    print("  - 运行 python check_data_format.py 查看数据格式")
    print("  - 查看 docs/IC_USAGE_GUIDE.md 了解详细使用指南")
    print("  - 参考 examples/test_factor_analysis.py 查看完整示例")
    print("=" * 70)


if __name__ == "__main__":
    # 读取您的数据
    print("请在您的代码中调用 check_data_format() 函数")
    print("或者直接运行此脚本并传入您的数据\n")

    show_conversion_example()
