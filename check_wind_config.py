"""
检查Wind配置状态
"""
import sys
import os
from pathlib import Path

# 设置UTF-8编码输出
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings


def main():
    print("=" * 60)
    print("Wind配置检查")
    print("=" * 60)

    settings = get_settings()

    print(f"\nWind启用状态: {settings.data.wind_enabled}")

    if settings.data.wind_enabled:
        print("✓ Wind已启用")
        print("\n交易日历将优先使用Wind API获取数据")
        print("如果Wind不可用，将自动降级到工作日判断")
    else:
        print("✗ Wind未启用")
        print("\n要启用Wind，请修改 config/config.yaml:")
        print("  data:")
        print("    wind_enabled: true")
        print("\n或设置环境变量:")
        print("  export WIND_ENABLED=true")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
