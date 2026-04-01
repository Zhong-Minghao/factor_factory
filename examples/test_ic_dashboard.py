"""
IC 分析看板生成测试示例
演示如何使用 ICReport 类和 create_ic_dashboard() 函数
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
):
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

    # 生成因子数据
    # 创建一个有一定预测能力的因子
    # 因子值与未来收益率有微弱的相关性
    factor_signal = np.random.randn(num_stocks) * 0.5
    factor_data = pd.DataFrame(
        np.random.randn(num_days, num_stocks) * 0.3 + factor_signal,
        index=dates,
        columns=stock_codes,
    )

    # 添加一些 NaN 值
    nan_mask = np.random.random(factor_data.shape) < 0.05
    factor_data[nan_mask] = np.nan

    return factor_data, price_data


def main():
    """生成 IC 分析看板"""
    print("=" * 70)
    print("IC 分析看板生成测试")
    print("=" * 70)

    # 1. 创建测试数据
    print("\n[INFO] 创建测试数据...")
    factor_data, price_data = create_test_data(
        num_stocks=100, num_days=252, start_date="2023-01-01"
    )

    print(f"  - 因子数据形状: {factor_data.shape}")
    print(f"  - 价格数据形状: {price_data.shape}")
    print(f"  - 时间范围: {factor_data.index[0]} 至 {factor_data.index[-1]}")

    # 2. 生成 IC 分析看板
    print("\n[INFO] 生成 IC 分析看板...")
    print("[INFO] 正在计算 IC 数据...")
    print("  [1/5] 计算基础 IC 序列...")
    print("  [2/5] 计算 IC 衰减数据...")
    print("  [3/5] 计算 IC 统计指标...")
    print("  [4/5] 计算滚动 IC 分析...")
    print("  [5/5] 计算月度 IC 统计...")

    from output_dashboard import create_ic_dashboard

    output_path = "reports/ic_dashboard.html"

    create_ic_dashboard(
        factor_data=factor_data,
        price_data=price_data,
        output_path=output_path,
        title="因子 IC 分析报告",
        period=5,  # 5日收益率
        max_periods=10,  # 分析 1-10 期的 IC 衰减
        ic_type="rank",  # 使用 Rank IC（Spearman 相关系数）
        auto_open=False,  # 设为 True 可自动打开浏览器
    )

    print(f"\n[SUCCESS] IC 分析看板已生成！")
    print(f"[INFO] 报告路径: {Path.cwd() / output_path}")
    print(f"\n[TIP] 在浏览器中打开 {output_path} 查看交互式图表")

    # 3. 显示 IC 统计摘要
    print("\n" + "=" * 70)
    print("IC 分析摘要")
    print("=" * 70)

    # 使用 ICAnalyzer 计算一些基本统计
    from analysis.ic_ir import ICAnalyzer

    analyzer = ICAnalyzer(ic_type="rank")
    ic_series = analyzer.compute_daily_ic(factor_data, price_data, period=5)
    ic_stats = analyzer.compute_ic_statistics(ic_series)

    print(f"\nIC 均值: {ic_stats['mean']:.4f}")
    print(f"IC 标准差: {ic_stats['std']:.4f}")
    print(f"IR（信息比率）: {ic_stats['ir']:.4f}")
    print(f"t 统计量: {ic_stats['t_stat']:.4f}")
    print(f"p 值: {ic_stats['p_value']:.4f}")
    print(f"正 IC 占比: {(ic_series > 0).mean() * 100:.2f}%")
    print(f"样本数: {len(ic_series)}")

    # 评估因子质量
    print("\n[INFO] 因子质量评估:")
    if abs(ic_stats['mean']) >= 0.05:
        print("  [OK] IC 均值 >= 0.05：因子预测能力优秀")
    elif abs(ic_stats['mean']) >= 0.03:
        print("  [WARN] IC 均值 >= 0.03：因子预测能力良好")
    else:
        print("  [FAIL] IC 均值 < 0.03：因子预测能力较弱")

    if ic_stats['ir'] >= 0.5:
        print("  [OK] IR >= 0.5：因子稳定性优秀")
    elif ic_stats['ir'] >= 0.3:
        print("  [WARN] IR >= 0.3：因子稳定性良好")
    else:
        print("  [FAIL] IR < 0.3：因子稳定性较差")

    if ic_stats['p_value'] < 0.05:
        print("  [OK] p < 0.05：IC 统计显著")
    else:
        print("  [FAIL] p >= 0.05：IC 统计不显著")

    print("\n[TIP] IC 分析看板包含以下内容：")
    print("  1. IC/IR 统计摘要表（带解释）")
    print("  2. IC 分布直方图（显示均值线和统计信息）")
    print("  3. IC 时序图（带零线、均值线、标准差带）")
    print("  4. IC 滚动分析（滚动 IC 均值和滚动 IR）")
    print("  5. IC 衰减曲线（1-10 期的 IC 变化）")
    print("  6. 月度 IC 统计热力图")

    print("\n[INFO] 所有图表都是交互式的，支持：")
    print("  - 缩放和平移")
    print("  - 悬停查看详细数据")
    print("  - 图例切换")
    print("  - 导出为图片")

    print("\n[INFO] IC 分析的关键概念：")
    print("  - IC（Information Coefficient）：因子值与未来收益率的相关系数")
    print("  - IR（Information Ratio）：IC 均值 / IC 标准差，衡量稳定性")
    print("  - Rank IC：使用 Spearman 秩相关系数，更稳健")
    print("  - IC 衰减：因子预测能力随时间的变化")
    print("  - 正 IC 占比：IC > 0 的比例，理想值 > 50%")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 生成看板失败: {e}")
        import traceback

        traceback.print_exc()
