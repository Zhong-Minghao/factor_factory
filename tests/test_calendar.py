"""
测试交易日历工具
"""
import sys
from pathlib import Path
from datetime import date

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.calendar import TradingCalendar, get_calendar, is_trading_day


def test_calendar():
    """测试交易日历"""
    print("=" * 60)
    print("测试交易日历工具")
    print("=" * 60)

    calendar = get_calendar()

    # 测试1: 基本交易日判断
    print("\n[测试1] 基本交易日判断...")
    test_dates = [
        date(2024, 3, 15),  # 周五
        date(2024, 3, 16),  # 周六
        date(2024, 3, 17),  # 周日
    ]

    for test_date in test_dates:
        is_trading = is_trading_day(test_date)
        weekday = test_date.strftime("%A")
        status = "交易日" if is_trading else "非交易日"
        print(f"  {test_date} ({weekday}): {status}")

    # 测试2: 字符串日期判断
    print("\n[测试2] 字符串日期判断...")
    date_str = "2024-03-15"
    is_trading = calendar.is_trading_day_str(date_str)
    print(f"  {date_str}: {'交易日' if is_trading else '非交易日'}")

    # 测试3: 获取交易日列表
    print("\n[测试3] 获取交易日列表...")
    trading_days = calendar.get_trading_days("2024-03-01", "2024-03-15")
    print(f"  2024-03-01 到 2024-03-15 期间的交易日数量: {len(trading_days)}")
    print(f"  前5个交易日: {[d.strftime('%Y-%m-%d') for d in trading_days[:5]]}")

    # 测试4: 获取下一个交易日
    print("\n[测试4] 获取下一个交易日...")
    test_date = date(2024, 3, 15)  # 周五
    next_trading = calendar.get_next_trading_day(test_date)
    if next_trading:
        print(f"  {test_date} 之后的下一个交易日: {next_trading}")
    else:
        print(f"  未找到 {test_date} 之后的交易日")

    # 测试5: 获取前一个交易日
    print("\n[测试5] 获取前一个交易日...")
    prev_trading = calendar.get_previous_trading_day(test_date)
    if prev_trading:
        print(f"  {test_date} 之前的前一个交易日: {prev_trading}")
    else:
        print(f"  未找到 {test_date} 之前的交易日")

    # 测试6: 获取N个交易日后的日期
    print("\n[测试6] 获取N个交易日后的日期...")
    start_date = date(2024, 3, 1)
    n = 10
    nth_trading = calendar.get_n_trading_days_later(start_date, n)
    if nth_trading:
        print(f"  {start_date} 之后第{n}个交易日: {nth_trading}")

    # 测试7: 计算交易日数量
    print("\n[测试7] 计算交易日数量...")
    start = "2024-03-01"
    end = "2024-03-31"
    count = calendar.get_trading_days_count(start, end)
    print(f"  {start} 到 {end} 的交易日数量: {count}天")

    print("\n" + "=" * 60)
    print("✅ 交易日历工具测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    test_calendar()
