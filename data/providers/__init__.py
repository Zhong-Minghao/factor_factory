"""
数据源提供者模块
支持多种数据源：Tushare, AKShare, Wind等
"""

from .wind import WindSource

__all__ = [
    "TushareSource",
    "AKShareSource",
    "WindSource",
]
