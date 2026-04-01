"""
多因子对比看板生成测试示例
演示如何使用 ComparisonReport 类和 create_comparison_dashboard() 函数
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_test_data(
    num_stocks: int = 100,
    num_days: int = 252,
    start_date: str = "2023-01-01",
    seed: int = 42,
) -> tuple:
    """创建测试数据"""
    np.random.seed(seed)
    dates = pd.date_range(start=start_date, periods=num_days, freq="D")
    stock_codes = [f"sz{str(i).zfill(6)}" for i in range(1, num_stocks + 1)]

    # 生成价格数据（随机游走）
    returns = np.random.randn(num_days, num_stocks) * 0.02
    price_data = pd.DataFrame(
        100 * np.cumprod(1 + returns, axis=0),
        index=dates,
        columns=stock_codes,
    )

    # 生成因子数据（3个不同的因子）
    factor_1 = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.5 + np.random.randn(num_stocks) * 0.3,
        index=dates,
        columns=stock_codes,
    )

    factor_2 = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.4 + np.sin(np.linspace(0, 10, num_stocks)) * 0.5,
        index=dates,
        columns=stock_codes,
    )

    factor_3 = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.6,
        index=dates,
        columns=stock_codes,
    )

    # 添加一些 NaN 值
    for factor in [factor_1, factor_2, factor_3]:
        nan_mask = np.random.random(factor.shape) < 0.05
        factor[nan_mask] = np.nan

    return (factor_1, factor_2, factor_3), price_data


def main():
    """生成多因子对比看板"""
    print("=" * 70)
    print("多因子对比看板生成测试")
    print("=" * 70)

    # 1. 创建测试数据
    print("\n[INFO] 创建测试数据...")
    (factor_1, factor_2, factor_3), price_data = create_test_data(
        num_stocks=100, num_days=252, start_date="2023-01-01"
    )

    # 2. 运行多个因子的回测
    print("\n[INFO] 运行多个因子的回测...")
    from backtest import VectorBacktest
    from output_dashboard import create_comparison_dashboard

    results = {}

    # 因子 1：MA20 风格
    print("  [1/3] 运行因子 1 回测...")
    backtest_1 = VectorBacktest(
        factor_data=factor_1,
        price_data=price_data,
        select_method="top_n",
        select_params={"top_n": 20},
        rebalance_freq="monthly",
    )
    results["因子1（MA20风格）"] = backtest_1.run()

    # 因子 2：RSI14 风格
    print("  [2/3] 运行因子 2 回测...")
    backtest_2 = VectorBacktest(
        factor_data=factor_2,
        price_data=price_data,
        select_method="top_n",
        select_params={"top_n": 20},
        rebalance_freq="monthly",
    )
    results["因子2（RSI14风格）"] = backtest_2.run()

    # 因子 3：MACD 风格
    print("  [3/3] 运行因子 3 回测...")
    backtest_3 = VectorBacktest(
        factor_data=factor_3,
        price_data=price_data,
        select_method="top_n",
        select_params={"top_n": 20},
        rebalance_freq="monthly",
    )
    results["因子3（MACD风格）"] = backtest_3.run()

    print(f"\n[INFO] 所有回测完成！")
    print(f"  - 因子1: 年化收益 {results['因子1（MA20风格）'].metrics['年化收益率'].iloc[0]:.2%}")
    print(f"  - 因子2: 年化收益 {results['因子2（RSI14风格）'].metrics['年化收益率'].iloc[0]:.2%}")
    print(f"  - 因子3: 年化收益 {results['因子3（MACD风格）'].metrics['年化收益率'].iloc[0]:.2%}")

    # 3. 生成多因子对比看板
    print("\n[INFO] 生成多因子对比看板...")
    output_path = "reports/comparison_dashboard.html"

    create_comparison_dashboard(
        results,
        output_path=output_path,
        title="多因子性能对比分析报告",
        auto_open=False,  # 设为 True 可自动打开浏览器
    )

    print(f"[SUCCESS] 多因子对比看板已生成！")
    print(f"[INFO] 报告路径: {Path.cwd() / output_path}")
    print(f"\n[TIP] 在浏览器中打开 {output_path} 查看交互式图表")

    # 4. 显示对比摘要
    print("\n" + "=" * 70)
    print("多因子对比摘要")
    print("=" * 70)

    for name, result in results.items():
        metrics = result.metrics.iloc[0]
        print(f"\n{name}:")
        print(f"  年化收益: {metrics['年化收益率']:.2%}")
        print(f"  夏普比率: {metrics['夏普比率']:.2f}")
        print(f"  最大回撤: {metrics['最大回撤']:.2%}")
        print(f"  卡尔玛比率: {metrics['卡尔玛比率']:.2f}")

    print("\n[TIP] 多因子对比看板包含以下内容：")
    print("  1. 性能对比雷达图（归一化的5维指标）")
    print("  2. 并列绩效指标对比表（高亮最优值）")
    print("  3. 净值曲线对比图（归一化）")
    print("  4. 回撤对比图（水下图）")
    print("  5. 月度收益热力图对比（多个子图）")

    print("\n[INFO] 所有图表都是交互式的，支持：")
    print("  - 缩放和平移")
    print("  - 悬停查看详细数据")
    print("  - 图例切换")
    print("  - 导出为图片")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 生成看板失败: {e}")
        import traceback

        traceback.print_exc()
