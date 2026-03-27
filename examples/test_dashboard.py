"""
HTML 因子看板生成测试示例
演示如何使用 output_dashboard 模块生成交互式 HTML 因子看板
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
) -> tuple:
    """创建测试数据"""
    dates = pd.date_range(start=start_date, periods=num_days, freq="D")
    stock_codes = [f"sz{str(i).zfill(6)}" for i in range(1, num_stocks + 1)]

    np.random.seed(42)

    # 生成价格数据
    price_data = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.02 + 1,
        index=dates,
        columns=stock_codes,
    )
    price_data = 100 * price_data.cumprod()

    # 生成因子数据
    factor_data = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.5 + 1,
        index=dates,
        columns=stock_codes,
    )

    # 添加 NaN 值
    nan_mask_factor = np.random.random((num_days, num_stocks)) < 0.05
    nan_mask_price = np.random.random((num_days, num_stocks)) < 0.02

    factor_data[nan_mask_factor] = np.nan
    price_data[nan_mask_price] = np.nan

    return factor_data, price_data


def main():
    """生成 HTML 因子看板"""
    print("=" * 70)
    print("HTML 因子看板生成测试")
    print("=" * 70)

    # 1. 创建测试数据
    print("\n[INFO] 创建测试数据...")
    factor_data, price_data = create_test_data(
        num_stocks=50, num_days=252, start_date="2023-01-01"
    )

    # 2. 运行回测
    print("\n[INFO] 运行回测...")
    from backtest import VectorBacktest
    from output_dashboard import create_dashboard

    backtest = VectorBacktest(
        factor_data=factor_data,
        price_data=price_data,
        select_method="top_n",
        select_params={"top_n": 10},
        rebalance_freq="monthly",
    )

    result = backtest.run()

    print(f"[INFO] 回测完成：年化收益 {result.metrics['年化收益率'].iloc[0]:.2%}")

    # 3. 生成 HTML 因子看板（使用新的模块）
    print("\n[INFO] 生成 HTML 因子看板...")
    output_path = "reports/factor_dashboard.html"

    create_dashboard(
        result,
        output_path=output_path,
        title="因子回测报告 - MA20 因子",
        auto_open=False,  # 设为 True 可自动打开浏览器
    )

    print(f"[SUCCESS] HTML 因子看板已生成！")
    print(f"[INFO] 报告路径: {Path.cwd() / output_path}")
    print(f"\n[TIP] 在浏览器中打开 {output_path} 查看交互式图表")

    # 4. 显示报告摘要
    print("\n" + "=" * 70)
    print("报告内容预览")
    print("=" * 70)
    print(result.summary())

    print("\n[TIP] 因子看板包含以下内容：")
    print("  1. 核心 KPI 卡片（6个关键指标）")
    print("  2. 净值曲线图（策略 vs 基准）")
    print("  3. 回撤分析图（水下图）")
    print("  4. 收益率分布直方图")
    print("  5. 月度收益热力图")
    print("  6. 换手率分析图")
    print("  7. 绩效摘要表格")

    print("\n[INFO] 所有图表都是交互式的，支持：")
    print("  - 缩放和平移")
    print("  - 悬停查看详细数据")
    print("  - 图例切换")
    print("  - 导出为图片")

    print("\n[INFO] 新的 output_dashboard 模块结构：")
    print("  output_dashboard/")
    print("  ├── __init__.py           # 模块入口")
    print("  ├── dashboard.py          # 快速生成函数")
    print("  ├── report.py             # HTML 报告生成器")
    print("  └── README.md             # 详细文档")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 生成看板失败: {e}")
        import traceback

        traceback.print_exc()
