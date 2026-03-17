"""
Wind数据源使用示例

展示如何使用Wind数据源获取金融数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.providers import WindSource
from config.settings import get_settings


def wind_demo():
    """Wind数据源使用示例"""
    print("=" * 80)
    print("Wind数据源使用示例")
    print("=" * 80)

    # 获取配置
    settings = get_settings()

    # 检查Wind是否启用
    if not settings.data.wind_enabled:
        print("\n[!] Wind数据源未启用")
        print("\n如需使用Wind数据源，请：")
        print("  1. 确保已安装Wind终端")
        print("  2. 安装WindPy: pip install WindPy")
        print("  3. 在.env文件中设置 DATA_WIND_ENABLED=true")
        print("  4. （可选）设置 DATA_WIND_ACCOUNT 和 DATA_WIND_PASSWORD")
        return

    # 创建Wind数据源
    print("\n[步骤1] 创建Wind数据源连接...")
    source = WindSource()

    try:
        # 连接Wind
        print("  正在连接Wind...")
        if source.connect():
            print("  [OK] Wind连接成功")
        else:
            print("  [FAIL] Wind连接失败")
            return

        # 获取股票列表
        print("\n[步骤2] 获取股票列表...")
        stock_list = source.get_stock_list()
        print(f"  [OK] 获取到 {len(stock_list)} 只股票")
        print(f"  前5只股票:")
        print(stock_list.head())

        # 获取单只股票日线数据
        print("\n[步骤3] 获取单只股票日线数据...")
        ts_code = "000001.SZ"  # 平安银行
        print(f"  获取股票: {ts_code}")

        data = source.get_daily_data(
            ts_code=ts_code,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        if not data.empty:
            print(f"  [OK] 获取到 {len(data)} 条数据")
            print(f"  数据列: {data.columns.tolist()}")
            print(f"  最新5条数据:")
            print(data.tail())
        else:
            print("  [FAIL] 未获取到数据")

        # 批量获取多只股票数据
        print("\n[步骤4] 批量获取多只股票数据...")
        codes = ["000001.SZ", "000002.SZ", "600000.SH"]
        print(f"  获取股票: {codes}")

        batch_data = source.get_daily_data_batch(
            ts_codes=codes,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        print(f"  [OK] 成功获取 {len(batch_data)} 只股票的数据")
        for code, df in batch_data.items():
            print(f"    {code}: {len(df)} 条数据")

        # 获取指数数据
        print("\n[步骤5] 获取指数数据...")
        index_code = "000300.SH"  # 沪深300
        print(f"  获取指数: {index_code}")

        index_data = source.get_index_data(
            index_code=index_code,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        if not index_data.empty:
            print(f"  [OK] 获取到 {len(index_data)} 条指数数据")
            print(f"  最新5条数据:")
            print(index_data.tail())
        else:
            print("  [FAIL] 未获取到指数数据")

        # 获取财务数据
        print("\n[步骤6] 获取财务数据...")
        print(f"  获取股票: {ts_code}")

        financial_data = source.get_financial_data(
            ts_code=ts_code,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        if not financial_data.empty:
            print(f"  [OK] 获取到 {len(financial_data)} 条财务数据")
            print(f"  数据列: {financial_data.columns.tolist()}")
            print(f"  最新5条数据:")
            print(financial_data.tail())
        else:
            print("  [FAIL] 未获取到财务数据")

        # 获取资金流向数据
        print("\n[步骤7] 获取资金流向数据...")
        print(f"  获取股票: {ts_code}")

        fund_flow_data = source.get_fund_flow(
            ts_code=ts_code,
            start_date="2024-01-01",
            end_date="2024-03-15"
        )

        if not fund_flow_data.empty:
            print(f"  [OK] 获取到 {len(fund_flow_data)} 条资金流向数据")
            print(f"  数据列: {fund_flow_data.columns.tolist()}")
            print(f"  最新5条数据:")
            print(fund_flow_data.tail())
        else:
            print("  [FAIL] 未获取到资金流向数据")

        # 断开连接
        print("\n[步骤8] 断开连接...")
        source.disconnect()
        print("  [OK] 已断开连接")

    except ImportError as e:
        print(f"  [FAIL] 缺少依赖: {e}")
        print("  请运行: pip install WindPy")
    except Exception as e:
        print(f"  [FAIL] 执行失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 确保断开连接
        if source.is_connected():
            source.disconnect()

    print("\n" + "=" * 80)
    print("[SUCCESS] Wind数据源使用示例完成！")
    print("=" * 80)


if __name__ == "__main__":
    wind_demo()
