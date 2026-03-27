"""
测试因子系统
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_sample_data():
    """创建示例数据"""
    # 生成100天的模拟数据
    np.random.seed(42)
    n = 100

    dates = pd.date_range(start="2024-01-01", periods=n, freq="D")

    # 生成价格数据（随机游走）
    price = 100 + np.cumsum(np.random.randn(n) * 0.02)

    # 生成OHLC数据
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


def test_factor_registry():
    """测试因子注册表"""
    print("=" * 60)
    print("测试因子注册表")
    print("=" * 60)

    from factors.registry import factor_registry, list_factors

    # 测试1: 列出所有因子
    print("\n[测试1] 列出所有已注册因子...")
    all_factors = list_factors()
    print(f"  ✓ 已注册因子总数: {len(all_factors)}")
    print(f"  所有因子: {', '.join(all_factors)}")

    # 测试2: 按类别列出因子
    print("\n[测试2] 按类别列出因子...")
    factors_by_category = factor_registry.list_factors_by_category()
    for category, factors in factors_by_category.items():
        print(f"  {category}: {len(factors)}个 - {', '.join(factors)}")

    # 测试3: 获取因子信息
    print("\n[测试3] 获取因子信息...")
    test_factor = "MA"
    if factor_registry.exists(test_factor):
        info = factor_registry.get_factor_info(test_factor)
        print(f"  因子名称: {info['name']}")
        print(f"  描述: {info['description']}")
        print(f"  作者: {info['author']}")
        print(f"  版本: {info['version']}")
        print(f"  类别: {info['category']}")
        print(f"  参数: {info['params']}")
    else:
        print(f"  ✗ 因子 {test_factor} 不存在")


def test_factor_computation():
    """测试因子计算"""
    print("\n" + "=" * 60)
    print("测试因子计算")
    print("=" * 60)

    from factors import factor_registry

    # 创建示例数据
    print("\n[准备] 创建示例数据...")
    data = create_sample_data()
    print(f"  ✓ 生成 {len(data)} 天的示例数据")
    print(f"  数据列: {data.columns.tolist()}")
    print(f"  前5行数据:")
    print(data.head())

    # 测试多个因子
    test_factors = [
        ("MA", {"window": 20}),
        ("RETURN", {"period": 10}),
        ("VOLUME_RATIO", {"window": 5}),
        ("RSI", {"window": 14}),
    ]

    print("\n[测试] 计算因子值...")
    for factor_name, params in test_factors:
        try:
            # 获取因子实例
            factor = factor_registry.get(factor_name, **params)

            if factor is None:
                print(f"  ✗ 因子 {factor_name} 不存在")
                continue

            # 计算因子值
            factor_values = factor.compute(data)

            # 显示结果
            print(f"\n  因子: {factor_name}")
            print(f"  参数: {params}")
            print(f"  ✓ 计算成功")
            print(f"  有效数据点: {factor_values.notna().sum()}")
            print(f"  均值: {factor_values.mean():.4f}")
            print(f"  标准差: {factor_values.std():.4f}")
            print(f"  最小值: {factor_values.min():.4f}")
            print(f"  最大值: {factor_values.max():.4f}")
            print(f"  最新5个值:")
            print(f"  {factor_values.tail().to_string()}")

        except Exception as e:
            print(f"  ✗ 计算因子 {factor_name} 失败: {e}")


def test_factor_engine():
    """测试因子计算引擎"""
    print("\n" + "=" * 60)
    print("测试因子计算引擎")
    print("=" * 60)

    from factors.engine import FactorEngine

    # 创建示例数据
    print("\n[准备] 创建示例数据...")
    data = create_sample_data()
    print(f"  ✓ 生成 {len(data)} 天的示例数据")

    # 创建引擎
    engine = FactorEngine()

    # 测试单因子计算
    print("\n[测试1] 单因子计算...")
    try:
        factor_values = engine.compute_factor("MA", data, window=20)
        print(f"  ✓ 计算成功")
        print(f"  因子值统计:")
        print(f"    均值: {factor_values.mean():.4f}")
        print(f"  标准差: {factor_values.std():.4f}")
    except Exception as e:
        print(f"  ✗ 计算失败: {e}")

    # 测试批量因子计算
    print("\n[测试2] 批量因子计算...")
    try:
        factor_names = ["MA", "RETURN", "VOLUME_RATIO", "RSI"]
        results = engine.compute_factors_batch(factor_names, data)

        print(f"  ✓ 成功计算 {len(results)} 个因子")
        for name, values in results.items():
            print(f"    {name}: 均值={values.mean():.4f}, 标准差={values.std():.4f}")
    except Exception as e:
        print(f"  ✗ 批量计算失败: {e}")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "🔬" * 30)
    print("因子系统测试套件")
    print("🔬" * 30)

    try:
        # 测试因子注册表
        test_factor_registry()

        # 测试因子计算
        test_factor_computation()

        # 测试因子引擎
        test_factor_engine()

        print("\n" + "=" * 60)
        print("✅ 所有因子系统测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
