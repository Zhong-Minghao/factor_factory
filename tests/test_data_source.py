"""
测试数据源接口
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_data_source():
    """测试数据源"""
    print("=" * 60)
    print("测试数据源接口")
    print("=" * 60)

    # 测试AKShare（免费，无需token）
    print("\n[测试1] 测试AKShare数据源...")
    try:
        from data.providers.akshare import AKShareSource

        source = AKShareSource()

        # 连接
        print("  正在连接AKShare...")
        if source.connect():
            print("  ✓ AKShare连接成功")

            # 获取股票列表
            print("\n  获取股票列表...")
            stock_list = source.get_stock_list()
            print(f"  ✓ 获取到 {len(stock_list)} 只股票")
            print(f"  前5只股票: {stock_list.head()['ts_code'].tolist()}")

            # 获取单只股票数据
            print("\n  获取单只股票日线数据...")
            ts_code = "000001.SZ"  # 平安银行
            data = source.get_daily_data(
                ts_code=ts_code,
                start_date="2024-01-01",
                end_date="2024-03-15"
            )

            if not data.empty:
                print(f"  ✓ 获取到 {len(data)} 条数据")
                print(f"  数据列: {data.columns.tolist()}")
                print(f"  最新5条数据:")
                print(data.tail())
            else:
                print("  ✗ 未获取到数据")

            # 断开连接
            source.disconnect()
            print("\n  ✓ 测试完成")

        else:
            print("  ✗ AKShare连接失败")

    except ImportError as e:
        print(f"  ✗ 缺少依赖: {e}")
        print("  请运行: pip install akshare")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    # 测试Tushare（需要token）
    print("\n[测试2] 测试Tushare数据源...")
    print("  注意: 需要在.env文件中配置TUSHARE_TOKEN")

    try:
        from data.providers.tushare import TushareSource
        from config.settings import get_settings

        settings = get_settings()

        if settings.data.tushare_token:
            print("  检测到Tushare Token，正在测试...")

            source = TushareSource()

            # 连接
            print("  正在连接Tushare...")
            if source.connect():
                print("  ✓ Tushare连接成功")

                # 获取股票列表
                print("\n  获取股票列表...")
                stock_list = source.get_stock_list()
                print(f"  ✓ 获取到 {len(stock_list)} 只股票")

                # 获取单只股票数据
                print("\n  获取单只股票日线数据...")
                ts_code = "000001.SZ"
                data = source.get_daily_data(
                    ts_code=ts_code,
                    start_date="2024-01-01",
                    end_date="2024-03-15"
                )

                if not data.empty:
                    print(f"  ✓ 获取到 {len(data)} 条数据")
                    print(f"  最新5条数据:")
                    print(data.tail())
                else:
                    print("  ✗ 未获取到数据")

                # 断开连接
                source.disconnect()
                print("\n  ✓ Tushare测试完成")

            else:
                print("  ✗ Tushare连接失败")
        else:
            print("  ⚠ 未配置Tushare Token，跳过测试")
            print("  如需使用Tushare，请:")
            print("  1. 访问 https://tushare.pro/register 获取token")
            print("  2. 在.env文件中设置 TUSHARE_TOKEN=your_token")

    except ImportError as e:
        print(f"  ✗ 缺少依赖: {e}")
        print("  请运行: pip install tushare")
    except Exception as e:
        print(f"  ✗ 测试失败: {e}")

    print("\n" + "=" * 60)
    print("✅ 数据源接口测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_data_source()
