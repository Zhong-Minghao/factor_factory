"""
调试Wind API
"""
import sys
import os
from pathlib import Path

# 设置UTF-8编码输出
if os.name == 'nt':  # Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.providers import WindSource


def test_wind_tdays():
    """测试Wind w.tdays API"""
    print("=" * 60)
    print("测试Wind w.tdays API")
    print("=" * 60)

    try:
        with WindSource() as wind:
            print("\n1. 测试w.tdays() API（获取交易日）")
            start_date = "2026-02-19"
            end_date = "2026-03-19"

            # 转换为Wind格式
            wind_start = start_date.replace("-", "")
            wind_end = end_date.replace("-", "")

            print(f"   日期范围: {start_date} 至 {end_date}")
            print(f"   Wind格式: {wind_start} 至 {wind_end}")

            # 调用w.tdays
            result = wind.api.tdays(wind_start, wind_end)

            print(f"\n   返回结果:")
            print(f"   ErrorCode: {result.ErrorCode}")
            print(f"   Times: {result.Times}")

            if result.ErrorCode == 0 and result.Times:
                print(f"\n   ✓ 成功获取 {len(result.Times)} 个交易日")
                print(f"   前5个: {result.Times[:5]}")

                # 测试转换
                from datetime import date
                trading_days = []
                for timestamp in result.Times[:5]:
                    year = timestamp // 10000
                    month = (timestamp % 10000) // 100
                    day = timestamp % 100
                    trading_days.append(date(year, month, day))
                print(f"   转换后: {trading_days}")
            else:
                print(f"\n   ✗ API返回错误或无数据")

            print("\n2. 测试w.tdays() + Days=Weekdays（获取工作日）")
            result2 = wind.api.tdays(wind_start, wind_end, "Days=Weekdays")

            print(f"   ErrorCode: {result2.ErrorCode}")
            print(f"   Times数量: {len(result2.Times) if result2.Times else 0}")

            if result2.ErrorCode == 0 and result2.Times:
                print(f"   ✓ 成功获取 {len(result2.Times)} 个工作日")
                print(f"   前5个: {result2.Times[:5]}")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


def test_wind_get_trading_days_tdays():
    """测试WindSource.get_trading_days_tdays()方法"""
    print("\n" + "=" * 60)
    print("测试WindSource.get_trading_days_tdays()方法")
    print("=" * 60)

    try:
        with WindSource() as wind:
            print("\n调用get_trading_days_tdays()...")
            trading_days = wind.get_trading_days_tdays("2026-02-19", "2026-03-19")

            print(f"返回类型: {type(trading_days)}")
            print(f"返回长度: {len(trading_days)}")

            if trading_days:
                print(f"✓ 成功获取 {len(trading_days)} 个交易日")
                print(f"前5个: {trading_days[:5]}")
            else:
                print(f"✗ 返回空列表")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    test_wind_tdays()
    test_wind_get_trading_days_tdays()


if __name__ == "__main__":
    main()
