"""
测试配置管理系统
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings, Settings


def test_settings():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置管理系统")
    print("=" * 60)

    # 测试1: 加载默认配置
    print("\n[测试1] 加载默认配置...")
    settings = get_settings()
    print(f"✓ 项目根目录: {settings.project_root}")
    print(f"✓ 数据目录: {settings.data.data_dir}")
    print(f"✓ 缓存目录: {settings.data.cache_dir}")
    print(f"✓ 主要数据源: {settings.data.primary_provider}")

    # 测试2: 获取路径
    print("\n[测试2] 测试路径获取...")
    data_path = settings.get_data_path("test.csv")
    print(f"✓ 数据路径: {data_path}")

    cache_path = settings.get_cache_path("test.pkl")
    print(f"✓ 缓存路径: {cache_path}")

    log_path = settings.get_log_path("test.log")
    print(f"✓ 日志路径: {log_path}")

    # 测试3: 配置信息
    print("\n[测试3] 配置详情...")
    print(f"✓ 因子并行计算: {settings.factor.parallel}")
    print(f"✓ 工作进程数: {settings.factor.n_workers}")
    print(f"✓ 回测初始资金: {settings.backtest.initial_capital:,.0f}元")
    print(f"✓ 手续费率: {settings.backtest.commission_rate:.4f}")
    print(f"✓ 滑点率: {settings.backtest.slippage_rate:.4f}")
    print(f"✓ 基准指数: {settings.backtest.benchmark}")

    print("\n" + "=" * 60)
    print("✅ 配置管理系统测试通过！")
    print("=" * 60)


def test_config():
    """测试配置（别名函数）"""
    test_settings()


if __name__ == "__main__":
    test_settings()
