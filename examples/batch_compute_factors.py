"""
批量计算因子脚本
使用Wind数据源下载真实股票数据，计算所有已注册因子并保存到因子库
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from factors.registry import factor_registry
from factors.engine import FactorEngine
from storage.factor_store import FactorStore
from config.settings import get_settings
from data.providers import WindSource


# ============================================================================
# 配置参数
# ============================================================================

# 时间范围
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

# 股票池（这里提供一个默认的股票池，你可以修改）
# 主流指数成分股
DEFAULT_STOCK_POOL = [
    # 上证50部分
    "600000.SH", "600036.SH", "600519.SH", "600887.SH",
    "601318.SH", "601398.SH", "601857.SH", "601939.SH",
    "601988.SH", "603259.SH",
    # 深证100部分
    "000001.SZ", "000002.SZ", "000063.SZ", "000333.SZ",
    "000338.SZ", "000651.SZ", "000725.SZ", "000858.SZ",
    "002415.SZ", "300015.SZ", "300059.SZ", "300750.SZ",
]

# 或者从Wind获取全部A股
USE_ALL_STOCKS = False  # 如果为True，则下载全部A股（较慢）
MAX_STOCKS = 100  # 如果USE_ALL_STOCKS=True，限制股票数量

# 因子计算配置
COMPUTE_CONFIG = {
    "use_cache": True,  # 使用缓存
    "skip_existing": True,  # 跳过已存在的因子
    "validate": True,  # 验证因子值
}


# ============================================================================
# 辅助函数
# ============================================================================

def get_stock_list_from_wind(wind_source):
    """
    从Wind获取股票列表

    Args:
        wind_source: WindSource实例

    Returns:
        股票代码列表
    """
    print("\n📋 获取股票列表...")

    try:
        stock_list = wind_source.get_stock_list()
        print(f"  ✓ 获取到 {len(stock_list)} 只股票")

        # 过滤掉ST股票和退市股票
        stock_list = stock_list[~stock_list['ts_code'].str.contains('ST')]
        stock_list = stock_list[~stock_list['ts_code'].str.contains('^\*ST')]

        print(f"  ✓ 过滤后剩余 {len(stock_list)} 只股票")

        return stock_list['ts_code'].tolist()

    except Exception as e:
        print(f"  ✗ 获取股票列表失败: {e}")
        return DEFAULT_STOCK_POOL


def download_stock_data(wind_source, stock_list, start_date, end_date):
    """
    下载股票历史数据

    Args:
        wind_source: WindSource实例
        stock_list: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        字典 {stock_code: DataFrame}
    """
    print(f"\n📥 下载股票数据...")
    print(f"  时间范围: {start_date} 至 {end_date}")
    print(f"  股票数量: {len(stock_list)}")

    data_dict = {}
    success_count = 0
    fail_count = 0

    for i, stock_code in enumerate(stock_list):
        try:
            print(f"  正在下载 {stock_code} ({i+1}/{len(stock_list)})...", end=" ")

            data = wind_source.get_daily_data(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date,
            )

            if not data.empty:
                data_dict[stock_code] = data
                success_count += 1
                print(f"✓ {len(data)} 条数据")
            else:
                fail_count += 1
                print("✗ 无数据")

        except Exception as e:
            fail_count += 1
            print(f"✗ 失败: {e}")

    print(f"\n  ✓ 成功: {success_count} 只, ✗ 失败: {fail_count} 只")

    return data_dict


def compute_single_factor(
    engine,
    factor_name,
    data_dict,
    factor_params=None,
):
    """
    计算单个因子

    Args:
        engine: FactorEngine实例
        factor_name: 因子名称
        data_dict: 股票数据字典
        factor_params: 因子参数

    Returns:
        因子值DataFrame（宽表格式），如果失败返回None
    """
    try:
        print(f"  🧮 计算因子 {factor_name}...", end=" ")

        # 对每只股票计算因子
        factor_values_dict = {}

        for stock_code, stock_data in data_dict.items():
            try:
                # 计算因子值
                if factor_params:
                    factor_value = engine.compute_factor(factor_name, stock_data, **factor_params)
                else:
                    factor_value = engine.compute_factor(factor_name, stock_data)

                factor_values_dict[stock_code] = factor_value

            except Exception as e:
                # 该股票计算失败，跳过
                continue

        # 转换为宽表格式
        if factor_values_dict:
            # 找到最长的日期序列
            max_length = max(len(v) for v in factor_values_dict.values())

            # 构建DataFrame
            df_data = {}
            for stock_code, factor_value in factor_values_dict.items():
                # 对齐日期索引
                if len(factor_value) < max_length:
                    # 填充NaN
                    padding = max_length - len(factor_value)
                    factor_value = pd.concat([
                        pd.Series([np.nan] * padding),
                        factor_value
                    ], ignore_index=True)

                df_data[stock_code] = factor_value.values

            # 使用第一只股票的日期作为索引
            first_stock = list(factor_values_dict.values())[0]
            if hasattr(first_stock, 'index'):
                index = first_stock.index
                # 如果索引不是日期，需要从stock_data中获取
                if not isinstance(index, pd.DatetimeIndex):
                    # 使用第一只股票的日期
                    first_stock_data = list(data_dict.values())[0]
                    index = first_stock_data.index[:len(first_stock)]
            else:
                # 使用第一只股票的日期
                first_stock_data = list(data_dict.values())[0]
                index = first_stock_data.index[:max_length]

            factor_df = pd.DataFrame(df_data, index=index)
            factor_df.index.name = 'trade_date'

            print(f"✓ {factor_df.shape}")
            return factor_df
        else:
            print("✗ 无数据")
            return None

    except Exception as e:
        print(f"✗ 失败: {e}")
        return None


def batch_compute_factors():
    """
    批量计算所有已注册因子
    """
    print("\n" + "=" * 80)
    print("批量因子计算系统")
    print("=" * 80)

    # 初始化
    settings = get_settings()
    engine = FactorEngine()
    factor_store = FactorStore()

    # 显示配置
    print("\n⚙️  配置信息:")
    print(f"  时间范围: {START_DATE} 至 {END_DATE}")
    print(f"  数据源: Wind")
    print(f"  因子库: {factor_store.storage_path}")

    # 检查Wind是否可用
    print("\n🔍 检查Wind数据源...")
    if not settings.data.wind_enabled:
        print("  ✗ Wind数据源未启用")
        print("  请在.env文件中设置 DATA_WIND_ENABLED=true")
        return

    # 连接Wind
    print("\n📡 连接Wind数据源...")
    wind_source = WindSource()

    try:
        if not wind_source.connect():
            print("  ✗ Wind连接失败")
            return
        print("  ✓ Wind连接成功")
    except Exception as e:
        print(f"  ✗ Wind连接失败: {e}")
        return

    try:
        # 获取股票列表
        if USE_ALL_STOCKS:
            stock_list = get_stock_list_from_wind(wind_source)
            if MAX_STOCKS and len(stock_list) > MAX_STOCKS:
                stock_list = stock_list[:MAX_STOCKS]
        else:
            stock_list = DEFAULT_STOCK_POOL

        print(f"\n📊 股票池: {len(stock_list)} 只股票")

        # 下载股票数据
        data_dict = download_stock_data(
            wind_source,
            stock_list,
            START_DATE,
            END_DATE,
        )

        if not data_dict:
            print("\n✗ 没有下载到任何股票数据")
            return

        # 获取所有已注册因子
        print("\n📋 获取已注册因子...")
        all_factors = factor_registry.list_factors()
        print(f"  ✓ 共有 {len(all_factors)} 个已注册因子")

        # 按类别分组
        factors_by_category = factor_registry.list_factors_by_category()

        # 批量计算因子
        print("\n" + "=" * 80)
        print("开始批量计算因子")
        print("=" * 80)

        results = {
            "success": [],
            "failed": [],
            "skipped": [],
        }

        for category, factors in factors_by_category.items():
            print(f"\n📁 类别: {category.upper()} ({len(factors)}个因子)")

            for factor_name in factors:
                print(f"\n  [{category.upper()}] {factor_name}")

                # 获取因子信息
                factor_info = factor_registry.get_factor_info(factor_name)
                if not factor_info:
                    print(f"    ⚠️  无法获取因子信息")
                    continue

                # 获取默认参数
                default_params = factor_info.get('params', {})

                # 检查是否已存在
                if COMPUTE_CONFIG["skip_existing"]:
                    existing_factors = factor_store.list_factors()
                    factor_key = factor_name
                    if default_params:
                        params_str = "_".join(f"{k}_{v}" for k, v in sorted(default_params.items()))
                        factor_key = f"{factor_name}_{params_str}"

                    if factor_key in existing_factors:
                        print(f"    ⏭️  因子已存在，跳过")
                        results["skipped"].append(factor_name)
                        continue

                # 计算因子
                factor_df = compute_single_factor(
                    engine,
                    factor_name,
                    data_dict,
                    default_params,
                )

                if factor_df is not None:
                    try:
                        # 保存因子
                        engine.save_factor_values(
                            factor_name=factor_name,
                            factor_values=factor_df,
                            params=default_params if default_params else None,
                        )
                        print(f"    💾 已保存到因子库")
                        results["success"].append(factor_name)
                    except Exception as e:
                        print(f"    ✗ 保存失败: {e}")
                        results["failed"].append(factor_name)
                else:
                    results["failed"].append(factor_name)

        # 生成统计报告
        print("\n" + "=" * 80)
        print("计算完成统计")
        print("=" * 80)

        print(f"\n✓ 成功: {len(results['success'])} 个")
        if results['success']:
            for factor in results['success']:
                print(f"  - {factor}")

        print(f"\n✗ 失败: {len(results['failed'])} 个")
        if results['failed']:
            for factor in results['failed']:
                print(f"  - {factor}")

        print(f"\n⏭️  跳过: {len(results['skipped'])} 个")
        if results['skipped']:
            for factor in results['skipped']:
                print(f"  - {factor}")

        # 显示因子库信息
        print("\n" + "=" * 80)
        print("因子库信息")
        print("=" * 80)

        store_info = factor_store.get_storage_info()
        print(f"\n存储文件: {store_info['storage_path']}")
        print(f"文件大小: {store_info['size_mb']:.2f} MB")
        print(f"因子总数: {store_info['num_factors']}")

        # 导出元数据
        print("\n📄 导出因子元数据...")
        metadata_df = factor_store.export_metadata()

        if not metadata_df.empty:
            output_file = settings.project_root / "examples" / "factors_metadata.xlsx"
            metadata_df.to_excel(output_file, index=False)
            print(f"  ✓ 元数据已导出到: {output_file}")

        print("\n" + "=" * 80)
        print("✅ 批量计算完成！")
        print("=" * 80)

        print("\n💡 下一步:")
        print("  1. 查看因子元数据: examples/factors_metadata.xlsx")
        print("  2. 使用 analysis/ 模块进行因子分析")
        print("  3. 生成HTML报告: python examples/generate_factor_report.py")

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 断开Wind连接
        print("\n🔌 断开Wind连接...")
        wind_source.disconnect()
        print("  ✓ 已断开")


if __name__ == "__main__":
    batch_compute_factors()
