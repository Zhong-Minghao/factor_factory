"""
回测模块
提供轻量级的向量回测框架，专注于因子有效性验证
"""

# 核心回测引擎
from .vector import VectorBacktest

# 股票选择器
from .selector import StockSelector

# 绩效计算器
from .performance import PerformanceCalculator

# 回测结果数据类
from .result import BacktestResult

__all__ = [
    # 核心引擎
    "VectorBacktest",
    # 辅助类
    "StockSelector",
    "PerformanceCalculator",
    "BacktestResult",
]
