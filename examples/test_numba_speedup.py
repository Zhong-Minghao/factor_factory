"""
测试numba加速的IC计算性能
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
import time
from analysis.ic_ir import ICAnalyzer


def generate_test_data():
    from data.providers import WindSource
    wind_source = WindSource()
    wind_source.connect()
    price_data = wind_source.get_daily_data(
            ts_code=["600000.SH"],
            start_date="2020-01-01",
            end_date="2024-12-31",
        )    

    # 因子
    from factors.engine import FactorEngine
    engine = FactorEngine()
    factor_data = engine.compute_factor('EMA', price_data)

    return factor_data, price_data


def benchmark_ic_computation(factor_data, price_data):
    """基准测试IC计算"""
    print("=" * 60)
    print("IC计算性能测试")
    print("=" * 60)
    print(f"数据规模: {len(factor_data)} 个交易日")
    print()

    # 测试不同配置
    configs = [
        ("Rank IC", "rank"),
        ("Pearson IC", "pearson"),
    ]

    for name, ic_type in configs:
        print(f"\n{name}:")
        print("-" * 60)

        analyzer = ICAnalyzer(ic_type=ic_type, preprocess=True)

        # 预热（首次运行会编译numba函数）
        print("预热中（首次运行会编译numba函数）...")
        small_factor = factor_data.iloc[:10]
        small_price = price_data.iloc[:20]
        _ = analyzer.compute_daily_ic(small_factor, small_price, period=5)

        # 正式测试
        print("计算中...")
        start_time = time.time()

        ic_result = analyzer.compute_daily_ic(factor_data, price_data[[ 'close' ]], period=5)

        elapsed = time.time() - start_time

        # 输出结果
        print(f"耗时: {elapsed:.2f} 秒")
        print(f"有效IC数量: {len(ic_result)}")
        if len(ic_result) > 0:
            print(f"IC均值: {ic_result.mean():.4f}")
            print(f"IC标准差: {ic_result.std():.4f}")
            print(f"IC IR: {ic_result.mean() / ic_result.std():.4f}")


if __name__ == "__main__":
    # 生成测试数据
    print("生成测试数据...")
    factor_data, price_data = generate_test_data()

    # 运行性能测试
    benchmark_ic_computation(factor_data, price_data)

    print("\n" + "=" * 60)
    print("性能提示:")
    print("  - 首次运行会编译numba函数，之后会非常快")
    print("  - numba加速主要在相关系数计算中")
    print("  - 向量化操作避免了大部分Python循环")
    print("=" * 60)
