"""
因子存储功能测试示例
测试FactorStore和FactorEngine的集成
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_test_factor_data(
    num_stocks: int = 100,
    num_days: int = 252,
    start_date: str = "2024-01-01",
) -> pd.DataFrame:
    """
    创建测试用的因子数据（宽表格式）

    Args:
        num_stocks: 股票数量
        num_days: 天数
        start_date: 开始日期

    Returns:
        因子值DataFrame（宽表格式）
    """
    # 生成日期序列
    dates = pd.date_range(start=start_date, periods=num_days, freq="D")

    # 生成股票代码
    stock_codes = [f"{str(i).zfill(6)}.SZ" for i in range(1, num_stocks + 1)]
 
    # 生成随机因子值
    np.random.seed(42)
    factor_values = np.random.randn(num_days, num_stocks) * 0.1

    # 创建DataFrame
    df = pd.DataFrame(
        factor_values,
        index=dates,
        columns=stock_codes,
    )

    # 添加一些NaN值（模拟真实情况）
    nan_mask = np.random.random((num_days, num_stocks)) < 0.05
    df[nan_mask] = np.nan

    return df


def test_factor_store():
    """测试因子存储功能"""
    print("\n" + "=" * 70)
    print("测试1：FactorStore基本功能")
    print("=" * 70)

    from storage import FactorStore

    # 创建FactorStore
    store = FactorStore()
    print(f"\n✓ FactorStore初始化成功")
    print(f"  存储路径: {store.storage_path}")
    print(f"  存储信息: {store}")

    # 创建测试数据
    print("\n📊 创建测试因子数据...")
    factor_data = create_test_factor_data(num_stocks=50, num_days=100)
    print(f"  数据形状: {factor_data.shape}")
    print(f"  日期范围: {factor_data.index.min()} 到 {factor_data.index.max()}")
    print(f"  缺失值比例: {factor_data.isna().sum().sum() / factor_data.size:.2%}")

    # 保存因子
    print("\n💾 保存因子...")
    store.save_factor(
        factor_name="MA",
        factor_data=factor_data,
        params={"window": 20},
    )
    print("  ✓ 因子 MA_20 保存成功")

    # 再保存一个因子
    factor_data_2 = create_test_factor_data(num_stocks=30, num_days=80)
    store.save_factor(
        factor_name="RSI",
        factor_data=factor_data_2,
        params={"window": 14},
    )
    print("  ✓ 因子 RSI_14 保存成功")

    # 列出因子
    print("\n📋 已保存的因子:")
    factors = store.list_factors()
    for factor in factors:
        metadata = store.get_factor_metadata(factor)
        print(f"  - {factor}")
        print(f"    元数据: {metadata}")

    # 加载因子
    print("\n📂 加载因子 MA_20...")
    loaded_data = store.load_factor("MA", params={"window": 20})
    print(f"  ✓ 加载成功")
    print(f"  数据形状: {loaded_data.shape}")
    print(f"  前5行×前5列:")
    print(loaded_data.iloc[:5, :5])

    # 导出元数据
    print("\n📄 导出所有因子元数据...")
    metadata_df = store.export_metadata()
    print(f"  ✓ 导出成功")
    print(f"\n{metadata_df}")

    # 存储信息
    print("\n💡 存储信息:")
    info = store.get_storage_info()
    print(f"  文件路径: {info['storage_path']}")
    print(f"  文件大小: {info['size_mb']:.2f} MB")
    print(f"  因子数量: {info['num_factors']}")


def test_factor_engine_integration():
    """测试FactorEngine与FactorStore的集成"""
    print("\n" + "=" * 70)
    print("测试2：FactorEngine集成FactorStore")
    print("=" * 70)

    from factors.engine import FactorEngine
    from storage import FactorStore

    # 创建FactorEngine（会自动创建FactorStore）
    print("\n🔧 创建FactorEngine...")
    engine = FactorEngine()
    print("  ✓ FactorEngine创建成功")
    print(f"  因子存储: {engine.factor_store}")

    # 创建测试因子数据
    print("\n📊 创建测试因子数据...")
    factor_data = create_test_factor_data(num_stocks=50, num_days=100)

    # 保存因子值
    print("\n💾 保存因子值...")
    engine.save_factor_values(
        factor_name="MACD",
        factor_values=factor_data,
        params={"fast": 12, "slow": 26, "signal": 9},
    )
    print("  ✓ 因子 MACD_12_26_9 保存成功")

    # 加载因子值
    print("\n📂 加载因子值...")
    loaded_data = engine.load_factor_values(
        factor_name="MACD",
        params={"fast": 12, "slow": 26, "signal": 9},
    )
    print(f"  ✓ 加载成功")
    print(f"  数据形状: {loaded_data.shape}")

    # 筛选日期
    print("\n📅 筛选日期范围加载...")
    filtered_data = engine.load_factor_values(
        factor_name="MACD",
        params={"fast": 12, "slow": 26, "signal": 9},
        start_date="2024-01-15",
        end_date="2024-02-15",
    )
    print(f"  ✓ 筛选后数据形状: {filtered_data.shape}")
    print(f"  日期范围: {filtered_data.index.min()} 到 {filtered_data.index.max()}")

    # 筛选股票
    print("\n📈 筛选股票代码...")
    stock_codes = ["000001.SZ", "000002.SZ", "000003.SZ"]
    filtered_data = engine.load_factor_values(
        factor_name="MACD",
        params={"fast": 12, "slow": 26, "signal": 9},
        stock_codes=stock_codes,
    )
    print(f"  ✓ 筛选后数据形状: {filtered_data.shape}")
    print(f"  股票代码: {list(filtered_data.columns)}")


def test_metadata():
    """测试元数据管理"""
    print("\n" + "=" * 70)
    print("测试3：因子元数据管理")
    print("=" * 70)

    from storage import FactorMetadata, FactorMetadataManager
    import pandas as pd

    # 创建元数据
    print("\n📝 创建因子元数据...")
    metadata = FactorMetadata(
        factor_name="TEST_FACTOR",
        category="technical",
        description="测试因子",
        author="Test User",
        version="1.0.0",
        params={"window": 20, "threshold": 0.5},
    )
    print(f"  ✓ 元数据创建成功")
    print(f"  因子键: {metadata.get_factor_key()}")

    # 创建测试数据
    factor_data = create_test_factor_data(num_stocks=20, num_days=50)

    # 更新统计信息
    print("\n📊 更新统计信息...")
    metadata.update_statistics(factor_data)
    print(f"  ✓ 统计信息已更新")
    print(f"  股票数量: {metadata.num_stocks}")
    print(f"  记录数量: {metadata.num_records}")
    print(f"  统计量: {metadata.statistics}")

    # 转换为字典和JSON
    print("\n🔄 转换格式...")
    metadata_dict = metadata.to_dict()
    print(f"  ✓ 字典: {list(metadata_dict.keys())}")

    metadata_json = metadata.to_json()
    print(f"  ✓ JSON长度: {len(metadata_json)} 字符")

    # 使用管理器
    print("\n📦 使用元数据管理器...")
    manager = FactorMetadataManager()
    manager.add_metadata(metadata)
    print(f"  ✓ 添加元数据成功")
    print(f"  管理器: {manager}")

    # 导出为DataFrame
    print("\n📄 导出为DataFrame...")
    metadata_df = manager.export_all_to_dataframe()
    print(f"  ✓ 导出成功")
    print(f"\n{metadata_df}")


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 35)
    print("因子存储功能测试")
    print("🚀" * 35)

    try:
        # 测试1：FactorStore基本功能
        test_factor_store()

        # 测试2：FactorEngine集成
        test_factor_engine_integration()

        # 测试3：元数据管理
        test_metadata()

        print("\n" + "=" * 70)
        print("✅ 所有测试完成！")
        print("=" * 70)

        print("\n💡 提示:")
        print("  - 因子数据保存在: storage/factors.h5")
        print("  - 可以用HDFView或pandas直接查看")
        print("  - 测试数据可以删除，重新运行测试会覆盖")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
