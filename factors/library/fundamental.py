"""
基本面因子库
包含财务数据相关因子
"""
import pandas as pd
import numpy as np

from ..base import FundamentalFactor
from ..registry import register_factor


@register_factor("PE")
class PE(FundamentalFactor):
    """市盈率因子"""

    name = "PE"
    description = "市盈率（TTM）"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算市盈率"""
        # 如果数据中包含pe_ttm列，直接使用
        if "pe_ttm" in data.columns:
            return data["pe_ttm"]

        # 如果包含pe列，使用pe
        if "pe" in data.columns:
            return data["pe"]

        # 否则返回空Series
        return pd.Series(index=data.index, dtype=float)


@register_factor("PB")
class PB(FundamentalFactor):
    """市净率因子"""

    name = "PB"
    description = "市净率"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算市净率"""
        if "pb" in data.columns:
            return data["pb"]

        return pd.Series(index=data.index, dtype=float)


@register_factor("PS")
class PS(FundamentalFactor):
    """市销率因子"""

    name = "PS"
    description = "市销率（TTM）"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算市销率"""
        if "ps_ttm" in data.columns:
            return data["ps_ttm"]

        if "ps" in data.columns:
            return data["ps"]

        return pd.Series(index=data.index, dtype=float)


@register_factor("MARKET_CAP")
class MarketCap(FundamentalFactor):
    """总市值因子"""

    name = "MARKET_CAP"
    description = "总市值"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算总市值"""
        if "total_mv" in data.columns:
            return data["total_mv"]

        return pd.Series(index=data.index, dtype=float)


@register_factor("CIRCULATING_CAP")
class CirculatingCap(FundamentalFactor):
    """流通市值因子"""

    name = "CIRCULATING_CAP"
    description = "流通市值"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算流通市值"""
        if "circ_mv" in data.columns:
            return data["circ_mv"]

        return pd.Series(index=data.index, dtype=float)


@register_factor("EP")
class EP(FundamentalFactor):
    """盈利收益率因子"""

    name = "EP"
    description = "盈利收益率（EP = 1/PE）"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算盈利收益率"""
        pe_factor = PE()

        pe = pe_factor.compute(data)

        # EP = 1/PE
        ep = 1 / pe

        return ep


@register_factor("BP")
class BP(FundamentalFactor):
    """账面市值比因子"""

    name = "BP"
    description = "账面市值比（BP = 1/PB）"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算账面市值比"""
        pb_factor = PB()

        pb = pb_factor.compute(data)

        # BP = 1/PB
        bp = 1 / pb

        return bp


@register_factor("LOG_MARKET_CAP")
class LogMarketCap(FundamentalFactor):
    """对数市值因子"""

    name = "LOG_MARKET_CAP"
    description = "总市值的自然对数"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算对数市值"""
        mc_factor = MarketCap()

        market_cap = mc_factor.compute(data)

        # 对数市值
        log_mc = np.log(market_cap)

        return log_mc
