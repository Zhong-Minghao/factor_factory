"""
输出看板模块
生成交互式 HTML 因子看板和报告
"""

from .report import FactorReport
from .dashboard import create_dashboard

__all__ = [
    "FactorReport",
    "create_dashboard",
]
