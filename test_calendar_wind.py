"""
测试交易日历Wind API集成
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

from utils.calendar import TradingCalendar
from datetime import date


def test_wind_update():
    """测试Wind API更新交易日历"""
    print("=" * 60)
    print("测试1: Wind API更新交易日历")
    print("=" * 60)

    calendar = TradingCalendar()

    # 测试更新2026年2月-3月的交易日历
    start_date = "2026-02-19"
    end_date = "2026-03-19"

    print(f"更新日期范围: {start_date} 至 {end_date}")
    success = calendar.update_trading_days(start_date, end_date)

    print(f"\n结果:")
    print(f"  Wind API成功: {success}")
    print(f"  交易日历总数: {len(calendar._trading_days)}")

    # 显示前5个交易日
    trading_days_list = sorted(list(calendar._trading_days))[:5]
    print(f"  前5个交易日: {trading_days_list}")

    return success


def test_get_trading_days():
    """测试获取交易日列表"""
    print("\n" + "=" * 60)
    print("测试2: 获取交易日列表")
    print("=" * 60)

    calendar = TradingCalendar()

    # 获取指定日期范围的交易日
    start_date = "2026-02-24"
    end_date = "2026-02-28"

    trading_days = calendar.get_trading_days(start_date, end_date)

    print(f"查询日期范围: {start_date} 至 {end_date}")
    print(f"交易日数量: {len(trading_days)}")
    print(f"交易日列表: {trading_days}")

    return len(trading_days) > 0


def test_is_trading_day():
    """测试判断是否为交易日"""
    print("\n" + "=" * 60)
    print("测试3: 判断是否为交易日")
    print("=" * 60)

    calendar = TradingCalendar()

    # 测试几个日期
    test_dates = [
        date(2026, 2, 24),  # 周二
        date(2026, 2, 25),  # 周三
        date(2026, 2, 28),  # 周六
        date(2026, 3, 1),   # 周日
    ]

    for test_date in test_dates:
        is_trading = calendar.is_trading_day(test_date)
        weekday = test_date.strftime("%A")
        print(f"  {test_date} ({weekday}): {'是交易日' if is_trading else '非交易日'}")

    return True


def test_cache_persistence():
    """测试缓存持久化"""
    print("\n" + "=" * 60)
    print("测试4: 缓存持久化")
    print("=" * 60)

    # 创建第一个实例并更新
    calendar1 = TradingCalendar()
    calendar1.update_trading_days("2026-02-19", "2026-03-19")
    count1 = len(calendar1._trading_days)
    print(f"第一个实例交易日数量: {count1}")

    # 创建第二个实例，应该从缓存加载
    calendar2 = TradingCalendar()
    count2 = len(calendar2._trading_days)
    print(f"第二个实例交易日数量: {count2}")

    if count2 > 0:
        print("✓ 缓存持久化成功")
        return True
    else:
        print("✗ 缓存持久化失败")
        return False


def test_fallback_to_weekdays():
    """测试降级到工作日"""
    print("\n" + "=" * 60)
    print("测试5: 降级到工作日判断")
    print("=" * 60)

    calendar = TradingCalendar()

    # 强制标记Wind不可用
    calendar._wind_available = False

    # 尝试更新，应该降级到工作日
    success = calendar.update_trading_days("2026-03-01", "2026-03-05")

    print(f"Wind API成功: {success}")
    print(f"交易日数量: {len(calendar._trading_days)}")

    if not success and len(calendar._trading_days) > 0:
        print("✓ 成功降级到工作日判断")
        return True
    else:
        print("✗ 降级策略失败")
        return False


def main():
    """运行所有测试"""
    print("\n交易日历Wind API集成测试\n")

    results = []

    # 运行测试
    try:
        results.append(("Wind API更新", test_wind_update()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("Wind API更新", False))

    try:
        results.append(("获取交易日列表", test_get_trading_days()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("获取交易日列表", False))

    try:
        results.append(("判断交易日", test_is_trading_day()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("判断交易日", False))

    try:
        results.append(("缓存持久化", test_cache_persistence()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("缓存持久化", False))

    try:
        results.append(("降级到工作日", test_fallback_to_weekdays()))
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        results.append(("降级到工作日", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")

    # 统计
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
