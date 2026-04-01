"""
输出看板模块
生成交互式 HTML 因子看板和报告
"""

from .report import FactorReport, ComparisonReport, ICReport
from .dashboard import (
    create_dashboard,
    create_comparison_dashboard,
    create_ic_dashboard,
)

__all__ = [
    # 报告生成器
    "FactorReport",
    "ComparisonReport",
    "ICReport",
    # 快速生成函数
    "create_dashboard",
    "create_comparison_dashboard",
    "create_ic_dashboard",
]
