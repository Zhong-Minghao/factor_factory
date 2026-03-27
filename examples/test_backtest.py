"""
向量回测框架测试示例
演示如何使用 VectorBacktest 进行因子回测
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_test_data(
    num_stocks: int = 50,
    num_days: int = 252,
    start_date: str = "2023-01-01",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    创建测试数据（因子数据和价格数据）

    Args:
        num_stocks: 股票数量
        num_days: 交易天数
        start_date: 开始日期

    Returns:
        (factor_data, price_data) 元组
    """
    # 生成日期序列
    dates = pd.date_range(start=start_date, periods=num_days, freq="D")

    # 生成股票代码
    stock_codes = [f"sz{str(i).zfill(6)}" for i in range(1, num_stocks + 1)]

    # 设置随机种子（可复现）
    np.random.seed(42)

    # 生成随机价格数据（几何布朗运动）
    price_data = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.02 + 1,
        index=dates,
        columns=stock_codes,
    )

    # 累计收益转价格
    price_data = 100 * price_data.cumprod()

    # 生成因子数据（与未来收益相关，模拟有效因子）
    factor_data = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.5 + 1,
        index=dates,
        columns=stock_codes,
    )

    # 添加一些 NaN 值（模拟真实情况）
    nan_mask_factor = np.random.random((num_days, num_stocks)) < 0.05
    nan_mask_price = np.random.random((num_days, num_stocks)) < 0.02

    factor_data[nan_mask_factor] = np.nan
    price_data[nan_mask_price] = np.nan

    return factor_data, price_data


def test_top_n_backtest():
    """测试 Top N 回测"""
    print("\n" + "=" * 70)
    print("测试1：Top N 回测")
    print("=" * 70)

    from backtest import VectorBacktest

    # 创建测试数据
    print("\n[INFO] 创建测试数据...")
    factor_data, price_data = create_test_data(
        num_stocks=50, num_days=252, start_date="2023-01-01"
    )
    print(f"  因子数据: {factor_data.shape}")
    print(f"  价格数据: {price_data.shape}")

    # 运行回测
    print("\n[INFO] 运行 Top N 回测...")
    backtest = VectorBacktest(
        factor_data=factor_data,
        price_data=price_data,
        select_method="top_n",
        select_params={"top_n": 10},
        rebalance_freq="monthly",
        weight_method="equal",
        commission_rate=0.0003,
        slippage_rate=0.0001,
        initial_capital=1000000.0,
    )

    result = backtest.run()

    # 输出结果
    print("\n[INFO] 回测结果:")
    print(result.summary())

    print("\n[INFO] 绩效指标:")
    print(result.metrics)

    print("\n[INFO] 收益率统计:")
    print(f"  平均收益率: {result.returns.mean():.4f}")
    print(f"  标准差: {result.returns.std():.4f}")
    print(f"  最佳交易: {result.get_best_trade()}")
    print(f"  最差交易: {result.get_worst_trade()}")

    print("\n[INFO] 换手率:")
    print(f"  平均换手率: {result.turnover.mean():.2%}")
    print(f"  最大换手率: {result.turnover.max():.2%}")

    return result


def test_layer_backtest():
    """测试分层回测"""
    print("\n" + "=" * 70)
    print("测试2：分层回测")
    print("=" * 70)

    from backtest import VectorBacktest

    # 创建测试数据
    print("\n[INFO] 创建测试数据...")
    factor_data, price_data = create_test_data(
        num_stocks=50, num_days=252, start_date="2023-01-01"
    )

    # 运行回测（选择第5层，即因子值最高的一层）
    print("\n[INFO] 运行分层回测（第5层）...")
    backtest = VectorBacktest(
        factor_data=factor_data,
        price_data=price_data,
        select_method="layer",
        select_params={"n_layers": 5, "layer_id": 4},  # 第5层
        rebalance_freq="monthly",
    )

    result = backtest.run()

    # 输出结果
    print("\n[INFO] 回测结果:")
    print(result.summary())

    print("\n[INFO] 绩效指标:")
    print(result.metrics)

    return result


def test_percentile_backtest():
    """测试百分比回测"""
    print("\n" + "=" * 70)
    print("测试3：百分比回测")
    print("=" * 70)

    from backtest import VectorBacktest

    # 创建测试数据
    print("\n[INFO] 创建测试数据...")
    factor_data, price_data = create_test_data(
        num_stocks=50, num_days=252, start_date="2023-01-01"
    )

    # 运行回测（选择前20%的股票）
    print("\n[INFO] 运行百分比回测（前20%）...")
    backtest = VectorBacktest(
        factor_data=factor_data,
        price_data=price_data,
        select_method="percentile",
        select_params={"percentile": 0.2},  # 前20%
        rebalance_freq="weekly",
    )

    result = backtest.run()

    # 输出结果
    print("\n[INFO] 回测结果:")
    print(result.summary())

    print("\n[INFO] 绩效指标:")
    print(result.metrics)

    return result


def test_with_benchmark():
    """测试带基准的回测"""
    print("\n" + "=" * 70)
    print("测试4：带基准的回测")
    print("=" * 70)

    from backtest import VectorBacktest

    # 创建测试数据
    print("\n[INFO] 创建测试数据...")
    factor_data, price_data = create_test_data(
        num_stocks=50, num_days=252, start_date="2023-01-01"
    )

    # 创建基准数据（模拟指数）
    dates = price_data.index
    benchmark_data = pd.Series(
        100 * np.cumprod(1 + np.random.randn(len(dates)) * 0.01),
        index=dates,
    )

    # 运行回测
    print("\n[INFO] 运行带基准的回测...")
    backtest = VectorBacktest(
        factor_data=factor_data,
        price_data=price_data,
        benchmark_data=benchmark_data,
        select_method="top_n",
        select_params={"top_n": 10},
        rebalance_freq="monthly",
    )

    result = backtest.run()

    # 输出结果
    print("\n[INFO] 回测结果:")
    print(result.summary())

    print("\n[INFO] 绩效指标:")
    print(result.metrics)

    # 显示相对指标
    if result.excess_returns is not None:
        print("\n[INFO] 超额收益统计:")
        print(f"  平均超额收益: {result.excess_returns.mean():.4f}")
        print(f"  累计超额收益: {result.excess_returns.sum():.4f}")

    return result


def test_export_results():
    """测试结果导出"""
    print("\n" + "=" * 70)
    print("测试5：结果导出")
    print("=" * 70)

    from backtest import VectorBacktest

    # 创建测试数据并运行回测
    factor_data, price_data = create_test_data()
    backtest = VectorBacktest(
        factor_data=factor_data,
        price_data=price_data,
        select_method="top_n",
        select_params={"top_n": 10},
    )

    result = backtest.run()

    # 导出所有结果
    print("\n[INFO] 导出所有结果为 DataFrame...")
    results_dict = result.to_dataframe()

    print("\n[INFO] 导出的结果:")
    for key, df in results_dict.items():
        print(f"  - {key}: {df.shape}")

    # 保存到文件（可选）
    # with pd.ExcelWriter('backtest_results.xlsx') as writer:
    #     for key, df in results_dict.items():
    #         df.to_excel(writer, sheet_name=key)
    # print("\n[INFO] 结果已保存到 backtest_results.xlsx")


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("向量回测框架测试")
    print("=" * 70)

    try:
        # 测试1：Top N 回测
        test_top_n_backtest()

        # 测试2：分层回测
        test_layer_backtest()

        # 测试3：百分比回测
        test_percentile_backtest()

        # 测试4：带基准的回测
        test_with_benchmark()

        # 测试5：结果导出
        test_export_results()

        print("\n" + "=" * 70)
        print("[SUCCESS] 所有测试完成！")
        print("=" * 70)

        print("\n[TIP] 提示:")
        print("  - 向量回测框架已成功实现")
        print("  - 支持 Top N、分层、百分比三种选股方式")
        print("  - 支持日度、周度、月度三种调仓频率")
        print("  - 所有结果都是 DataFrame 格式，便于分析")

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
