"""
因子分析完整测试示例
测试Phase 1（因子存储）和Phase 2（因子分析）的所有功能
"""
import sys
import io
from pathlib import Path
import pandas as pd
import numpy as np

# 设置UTF-8编码以支持Windows控制台显示emoji
# if sys.platform == 'win32':
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_test_data(
    num_stocks: int = 100,
    num_days: int = 300,  # 增加到300天以支持月度调仓
    start_date: str = "2024-01-01",
) -> tuple:
    """
    创建测试数据：因子值和价格数据

    Args:
        num_stocks: 股票数量
        num_days: 天数
        start_date: 开始日期

    Returns:
        (factor_data, price_data) 元组
    """
    # 生成日期序列（只用工作日）
    dates = pd.date_range(start=start_date, periods=num_days, freq="B")  # B = 工作日

    # 生成股票代码（使用下划线代替点号以避免HDF5警告）
    stock_codes = [f"{str(i).zfill(6)}_SZ" for i in range(1, num_stocks + 1)]

    # 生成价格数据（随机游走）
    np.random.seed(42)
    price = 100 + np.cumsum(np.random.randn(num_days, num_stocks) * 0.02, axis=0)

    price_data = pd.DataFrame(price, index=dates, columns=stock_codes)

    # 生成因子值（与未来收益率有一定相关性）
    # 计算未来收益率
    future_returns = price_data.pct_change(5).shift(-5)  # 5日收益率

    # 因子值 = 未来收益率 + 噪声
    noise = np.random.randn(num_days, num_stocks) * 0.01
    factor_values = future_returns.values + noise

    factor_data = pd.DataFrame(factor_values, index=dates, columns=stock_codes)

    # 添加NaN值
    nan_mask_factor = np.random.random((num_days, num_stocks)) < 0.02
    factor_data[nan_mask_factor] = np.nan

    nan_mask_price = np.random.random((num_days, num_stocks)) < 0.01
    price_data[nan_mask_price] = np.nan

    return factor_data, price_data


def test_phase1_factor_storage():
    """测试Phase 1：因子存储功能"""
    print("\n" + "=" * 70)
    print("Phase 1：因子存储功能测试")
    print("=" * 70)

    from factors.engine import FactorEngine
    from storage import FactorStore

    # 创建因子引擎
    print("\n🔧 创建因子引擎...")
    engine = FactorEngine()
    print(f"  ✓ 因子引擎创建成功")
    print(f"  存储路径: {engine.factor_store.storage_path}")

    # 创建测试数据
    print("\n📊 创建测试数据...")
    factor_data, price_data = create_test_data(num_stocks=50, num_days=300)
    print(f"  因子数据: {factor_data.shape}")
    print(f"  价格数据: {price_data.shape}")

    # 保存因子
    print("\n💾 保存因子...")
    engine.save_factor_values(
        factor_name="TEST_FACTOR",
        factor_values=factor_data,
        params={"version": "test"},
    )
    print("  ✓ 因子保存成功")

    # 加载因子
    print("\n📂 加载因子...")
    loaded_factor = engine.load_factor_values("TEST_FACTOR", params={"version": "test"})
    print(f"  ✓ 因子加载成功: {loaded_factor.shape}")

    # 查看存储信息
    print("\n💾 存储信息:")
    info = engine.factor_store.get_storage_info()
    print(f"  文件大小: {info['size_mb']:.2f} MB")
    print(f"  因子数量: {info['num_factors']}")

    # 列出所有因子
    print("\n📋 已保存的因子:")
    factors = engine.factor_store.list_factors()
    for factor in factors:
        print(f"  - {factor}")

    return factor_data, price_data


def test_phase2_preprocessing(factor_data: pd.DataFrame):
    """测试因子预处理"""
    print("\n" + "=" * 70)
    print("测试：因子预处理")
    print("=" * 70)

    from analysis import preprocess_factor, mad_outlier_treatment, zscore_standardization

    print("\n🔧 MAD去极值...")
    mad_data = mad_outlier_treatment(factor_data)
    print(f"  ✓ 去极值完成")
    print(f"  原始数据范围: [{factor_data.min().min():.4f}, {factor_data.max().max():.4f}]")
    print(f"  去极值后范围: [{mad_data.min().min():.4f}, {mad_data.max().max():.4f}]")

    print("\n📊 Z-score标准化...")
    zscore_data = zscore_standardization(mad_data)
    print(f"  ✓ 标准化完成")
    print(f"  均值: {zscore_data.mean().mean():.6f}")
    print(f"  标准差: {zscore_data.std().mean():.6f}")

    print("\n🔄 完整预处理流程...")
    processed_data = preprocess_factor(
        factor_data,
        outlier_method="mad",
        standardize=True,
    )
    print(f"  ✓ 预处理完成: {processed_data.shape}")

    return processed_data


def test_phase2_ic_ir(factor_data: pd.DataFrame, price_data: pd.DataFrame):
    """测试IC/IR分析"""
    print("\n" + "=" * 70)
    print("测试：IC/IR分析")
    print("=" * 70)

    from analysis import ICAnalyzer

    # 创建IC分析器
    print("\n🔧 创建IC分析器...")
    analyzer = ICAnalyzer(ic_type="rank", preprocess=False)
    print("  ✓ IC分析器创建成功")

    # 计算IC
    print("\n📊 计算IC...")
    ic_series = analyzer.compute_daily_ic(factor_data, price_data, period=5)
    print(f"  ✓ IC计算完成: {len(ic_series)}个数据点")

    # IC统计
    print("\n📈 IC统计指标:")
    ic_stats = analyzer.compute_ic_statistics(ic_series)

    stats_display = {
        "IC均值": f"{ic_stats['mean']:.4f}",
        "IC标准差": f"{ic_stats['std']:.4f}",
        "IR": f"{ic_stats['ir']:.4f}",
        "t统计量": f"{ic_stats['t_stat']:.4f}",
        "p值": f"{ic_stats['p_value']:.4f}",
        "正IC占比": f"{ic_stats['positive_ratio']:.2%}",
    }

    for key, value in stats_display.items():
        print(f"  {key}: {value}")

    # 完整分析
    print("\n🔍 完整IC分析（5日和20日）...")
    results = analyzer.analyze(factor_data, price_data, periods=[5, 20])

    for period, period_results in results.items():
        stats = period_results["statistics"]
        print(f"\n  {period}日IC:")
        print(f"    IC均值: {stats['mean']:.4f}")
        print(f"    IR: {stats['ir']:.4f}")

    return results


def test_phase2_layer_backtest(factor_data: pd.DataFrame, price_data: pd.DataFrame):
    """测试分层回测"""
    print("\n" + "=" * 70)
    print("测试：分层回测")
    print("=" * 70)

    from analysis import run_layer_backtest

    # 运行5层回测
    print("\n🏃 运行5层回测（月度调仓）...")
    results_5 = run_layer_backtest(
        factor_data=factor_data,
        price_data=price_data,
        n_layers=5,
        rebalance_freq="monthly",
    )
    print("  ✓ 5层回测完成")

    # 打印统计结果
    print("\n📊 5层回测统计:")
    statistics = results_5["statistics"]

    print("\n  各层表现:")
    for layer_id in range(5):
        key = f"layer_{layer_id}"
        if key in statistics:
            stats = statistics[key]
            print(f"    第{layer_id + 1}层:")
            print(f"      累计收益: {stats['total_return']:.2%}")
            print(f"      夏普比率: {stats['sharpe']:.4f}")
            print(f"      最大回撤: {stats['max_drawdown']:.2%}")

    # 多空收益
    if "long_short" in statistics:
        ls = statistics["long_short"]
        print(f"\n  多空收益:")
        print(f"    累计收益: {ls['total_return']:.2%}")
        print(f"    夏普比率: {ls['sharpe']:.4f}")

    # 运行10层回测
    print("\n🏃 运行10层回测（周度调仓）...")
    results_10 = run_layer_backtest(
        factor_data=factor_data,
        price_data=price_data,
        n_layers=10,
        rebalance_freq="weekly",
    )
    print("  ✓ 10层回测完成")

    return results_5, results_10


def test_phase2_correlation(factor_data: pd.DataFrame, price_data: pd.DataFrame):
    """测试相关性分析"""
    print("\n" + "=" * 70)
    print("测试：相关性分析")
    print("=" * 70)

    from analysis import CorrelationAnalyzer

    # 创建分析器
    print("\n🔧 创建相关性分析器...")
    analyzer = CorrelationAnalyzer()

    # 创建第二个因子（用于相关性分析）
    print("\n📊 创建测试因子...")
    np.random.seed(123)
    factor_data_2 = factor_data * 0.8 + np.random.randn(*factor_data.shape) * 0.01

    factor_dict = {"Factor1": factor_data, "Factor2": factor_data_2}

    # 计算相关性
    print("\n📈 计算因子间相关性...")
    corr_matrix = analyzer.compute_cross_sectional_correlation(factor_dict, method="spearman")
    print("  ✓ 相关性矩阵:")
    print(corr_matrix)

    # 计算VIF
    print("\n🔍 计算VIF（方差膨胀因子）...")
    try:
        vif = analyzer.compute_vif(factor_dict)
        print("  ✓ VIF值:")
        print(vif)
    except Exception as e:
        print(f"  ⚠ VIF计算失败（需要statsmodels）: {e}")

    # 多重共线性检验
    print("\n🧪 多重共线性检验...")
    test_result = analyzer.test_multicollinearity(factor_dict, threshold=10.0)

    if test_result["has_multicollinearity"]:
        print(f"  ⚠ 存在多重共线性")
        print(f"  高VIF因子: {test_result['high_vif_factors']}")
    else:
        print(f"  ✓ 不存在多重共线性")

    # PCA分析
    print("\n📊 PCA降维分析...")
    try:
        pca_result = analyzer.compute_pca(factor_dict, n_components=2)

        print("  ✓ PCA结果:")
        print(f"    解释方差比例: {pca_result['explained_variance_ratio']}")
        print(f"    累计解释方差: {pca_result['cumulative_variance_ratio']}")

        print("\n  因子载荷:")
        print(pca_result["factor_loadings"])
    except Exception as e:
        print(f"  ⚠ PCA计算失败（需要sklearn）: {e}")

    return corr_matrix


def test_phase2_reports(
    ic_analysis: dict,
    backtest_results: dict,
    factor_name: str = "TEST_FACTOR",
):
    """测试报告生成"""
    print("\n" + "=" * 70)
    print("测试：报告生成")
    print("=" * 70)

    from analysis import ReportGenerator

    # 创建报告生成器
    print("\n📝 创建报告生成器...")
    generator = ReportGenerator(output_dir="reports")
    print("  ✓ 报告生成器创建成功")

    # 生成IC报告
    print("\n📄 生成IC/IR报告...")
    generator.generate_ic_report(ic_analysis, factor_name)
    print("  ✓ IC报告已生成")

    # 生成分层回测报告
    print("\n📄 生成分层回测报告...")
    generator.generate_layer_backtest_report(backtest_results, factor_name)
    print("  ✓ 分层回测报告已生成")

    # 保存图表
    print("\n📊 保存图表...")
    try:
        generator.save_figures(prefix=f"{factor_name}_")
        print("  ✓ 图表已保存到 reports/ 目录")
    except Exception as e:
        print(f"  ⚠ 图表保存失败: {e}")
        print(f"    提示: 安装matplotlib以启用绘图功能")


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print("因子分析完整测试 - Phase 1 + Phase 2")
    print("🚀" * 35)

    try:
        # Phase 1: 因子存储
        factor_data, price_data = test_phase1_factor_storage()

        # Phase 2: 因子分析

        # 1. 预处理
        processed_data = test_phase2_preprocessing(factor_data)

        # 2. IC/IR分析
        ic_analysis = test_phase2_ic_ir(processed_data, price_data)

        # 3. 分层回测
        backtest_5, backtest_10 = test_phase2_layer_backtest(processed_data, price_data)

        # 4. 相关性分析
        corr_matrix = test_phase2_correlation(processed_data, price_data)

        # 5. 报告生成
        test_phase2_reports(ic_analysis, backtest_5, "TEST_FACTOR")

        print("\n" + "=" * 70)
        print("✅ 所有测试完成！")
        print("=" * 70)

        print("\n📁 生成的文件:")
        print("  - storage/factors.h5: 因子数据存储")
        print("  - reports/: 分析报告和图表")

        print("\n💡 提示:")
        print("  - 可以用pandas读取HDF5文件:")
        print("    df = pd.read_hdf('storage/factors.h5', '/factors/FACTOR_KEY')")
        print("  - 可以用HDFView软件查看HDF5文件")
        print("  - 报告中的图表需要matplotlib支持")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
