"""
快速运行所有测试
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_1_config():
    """测试配置管理"""
    print("\n" + "=" * 70)
    print("📋 测试1: 配置管理系统")
    print("=" * 70)

    try:
        from tests.test_config import test_config
        test_config()
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_calendar():
    """测试交易日历"""
    print("\n" + "=" * 70)
    print("📅 测试2: 交易日历工具")
    print("=" * 70)

    try:
        from tests.test_calendar import test_calendar
        test_calendar()
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_factors():
    """测试因子系统"""
    print("\n" + "=" * 70)
    print("🧮 测试3: 因子系统")
    print("=" * 70)

    try:
        from tests.test_factors import run_all_tests
        run_all_tests()
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_data_source():
    """测试数据源（可选）"""
    print("\n" + "=" * 70)
    print("📊 测试4: 数据源接口 (需要网络连接)")
    print("=" * 70)

    # 询问是否运行
    response = input("\n是否测试数据源? (需要网络连接) [y/N]: ").strip().lower()

    if response != 'y':
        print("跳过数据源测试")
        return True

    try:
        from tests.test_data_source import test_data_source
        test_data_source()
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "🧪" * 35)
    print("量化因子工厂 - 测试套件")
    print("🧪" * 35)

    results = {
        "配置管理系统": False,
        "交易日历工具": False,
        "因子系统": False,
        "数据源接口": False,
    }

    # 运行测试
    results["配置管理系统"] = test_1_config()
    results["交易日历工具"] = test_2_calendar()
    results["因子系统"] = test_3_factors()
    results["数据源接口"] = test_4_data_source()

    # 总结
    print("\n" + "=" * 70)
    print("📊 测试结果总结")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息")


if __name__ == "__main__":
    main()
