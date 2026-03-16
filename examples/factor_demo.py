"""
因子计算演示
使用生成的测试数据计算各种因子
"""
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from factors.registry import factor_registry
from factors import FactorEngine


def demo_single_factor():
    """演示单因子计算"""
    print("=" * 60)
    print("演示1: 单因子计算")
    print("=" * 60)

    # 读取测试数据
    data = pd.read_csv("../data/test_single_stock.csv")
    print(f"\n✓ 读取数据: {len(data)} 行")
    print(f"  日期范围: {data['trade_date'].min()} 到 {data['trade_date'].max()}")

    # 计算移动平均线
    print("\n[1] 计算 MA20（20日移动平均）...")
    ma_factor = factor_registry.get("MA", window=20)
    ma_values = ma_factor.compute(data)

    print(f"  有效数据点: {ma_values.notna().sum()}")
    print(f"  最新5个值:")
    print(f"    {ma_values.tail().to_string()}")

    # 计算RSI
    print("\n[2] 计算 RSI（相对强弱指标，14日）...")
    rsi_factor = factor_registry.get("RSI", window=14)
    rsi_values = rsi_factor.compute(data)

    print(f"  有效数据点: {rsi_values.notna().sum()}")
    print(f"  最新RSI值: {rsi_values.iloc[-1]:.2f}")
    print(f"  RSI范围: {rsi_values.min():.2f} - {rsi_values.max():.2f}")

    # 计算MACD
    print("\n[3] 计算 MACD（指数平滑异同移动平均线）...")
    macd_factor = factor_registry.get("MACD")
    macd_values = macd_factor.compute(data)

    print(f"  有效数据点: {macd_values.notna().sum()}")
    print(f"  最新MACD值: {macd_values.iloc[-1]:.4f}")

    # 计算成交量比率
    print("\n[4] 计算成交量比率（5日）...")
    vr_factor = factor_registry.get("VOLUME_RATIO", window=5)
    vr_values = vr_factor.compute(data)

    print(f"  有效数据点: {vr_values.notna().sum()}")
    print(f"  最新量比: {vr_values.iloc[-1]:.2f}")


def demo_batch_factors():
    """演示批量因子计算"""
    print("\n" + "=" * 60)
    print("演示2: 批量因子计算")
    print("=" * 60)

    # 读取测试数据
    data = pd.read_csv("../data/test_single_stock.csv")

    # 创建因子引擎
    engine = FactorEngine()

    # 批量计算多个因子
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
    output_file = "../data/factor_results.csv"
    result_df.to_csv(output_file)
    print(f"✓ 结果已保存到: {output_file}")


def demo_multi_stock():
    """演示多股票因子计算"""
    print("\n" + "=" * 60)
    print("演示3: 多股票因子计算")
    print("=" * 60)

    # 读取多股票数据
    data = pd.read_csv("../data/test_multi_stock.csv")
    print(f"\n✓ 读取数据: {len(data)} 行")
    print(f"  股票数量: {data['symbol'].nunique()}")
    print(f"  股票列表: {data['symbol'].unique().tolist()}")

    # 计算每个股票的因子
    print(f"\n计算每只股票的 MA20...")

    results = []
    for symbol in data['symbol'].unique():
        stock_data = data[data['symbol'] == symbol].reset_index(drop=True)

        ma_factor = factor_registry.get("MA", window=20)
        ma_values = ma_factor.compute(stock_data)

        results.append({
            'symbol': symbol,
            'ma20_latest': ma_values.iloc[-1],
            'ma20_mean': ma_values.mean(),
            'valid_points': ma_values.notna().sum()
        })

    result_df = pd.DataFrame(results)
    print(f"\n结果:")
    print(result_df.to_string())


def demo_factor_statistics():
    """演示因子统计分析"""
    print("\n" + "=" * 60)
    print("演示4: 因子统计分析")
    print("=" * 60)

    # 读取测试数据
    data = pd.read_csv("../data/test_single_stock.csv")

    # 计算多个因子
    factors = {
        "MA5": factor_registry.get("MA", window=5),
        "MA20": factor_registry.get("MA", window=20),
        "RSI": factor_registry.get("RSI", window=14),
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


if __name__ == "__main__":
    print("\n" + "🧪" * 30)
    print("量化因子工厂 - 计算演示")
    print("🧪" * 30)

    try:
        # 运行各个演示
        demo_single_factor()
        demo_batch_factors()
        demo_multi_stock()
        demo_factor_statistics()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
