"""
因子模块
提供因子计算的核心功能
"""

# 导入基类
from .base import (
    Factor,
    TechnicalFactor,
    MomentumFactor,
    VolumeFactor,
    FundamentalFactor,
    FactorCalculator,
    FactorValidator,
)

# 导入注册表
from .registry import (
    FactorRegistry,
    factor_registry,
    register_factor,
    get_factor,
    list_factors,
)

# 导入引擎
from .engine import FactorEngine

# 导入内置因子库
from .library import technical, momentum, volume, fundamental

# 自动注册所有内置因子
from .library.technical import MA, EMA, MACD, RSI, BOLL, ATR, KDJ, CCI, OBV
from .library.momentum import (
    Return,
    MOM,
    Acceleration,
    RSQ,
    MaxReturn,
    DownsideRisk,
    UpsidePotential,
    RateOfChange,
    WilliamsR,
)
from .library.volume import (
    VolumeRatio,
    VolumeMA,
    Turnover,
    VPrice,
    Volatility,
    NetFlow,
    VolumeTrend,
    PriceVolumeTrend,
    VolumeOscillator,
)
from .library.fundamental import (
    PE,
    PB,
    PS,
    MARKET_CAP,
    CIRCULATING_CAP,
    EP,
    BP,
    LogMarketCap,
)

__all__ = [
    # 基类
    "Factor",
    "TechnicalFactor",
    "MomentumFactor",
    "VolumeFactor",
    "FundamentalFactor",
    "FactorCalculator",
    "FactorValidator",
    # 注册表
    "FactorRegistry",
    "factor_registry",
    "register_factor",
    "get_factor",
    "list_factors",
    # 引擎
    "FactorEngine",
    # 内置因子
    "MA",
    "EMA",
    "MACD",
    "RSI",
    "BOLL",
    "ATR",
    "KDJ",
    "CCI",
    "OBV",
    "Return",
    "MOM",
    "Acceleration",
    "RSQ",
    "MaxReturn",
    "DownsideRisk",
    "UpsidePotential",
    "RateOfChange",
    "WilliamsR",
    "VolumeRatio",
    "VolumeMA",
    "Turnover",
    "VPrice",
    "Volatility",
    "NetFlow",
    "VolumeTrend",
    "PriceVolumeTrend",
    "VolumeOscillator",
    "PE",
    "PB",
    "PS",
    "MARKET_CAP",
    "CIRCULATING_CAP",
    "EP",
    "BP",
    "LogMarketCap",
]

# 注册内置因子
factor_registry.register_class(MA, "MA")
factor_registry.register_class(EMA, "EMA")
factor_registry.register_class(MACD, "MACD")
factor_registry.register_class(RSI, "RSI")
factor_registry.register_class(BOLL, "BOLL")
factor_registry.register_class(ATR, "ATR")
factor_registry.register_class(KDJ, "KDJ")
factor_registry.register_class(CCI, "CCI")
factor_registry.register_class(OBV, "OBV")
factor_registry.register_class(Return, "RETURN")
factor_registry.register_class(MOM, "MOM")
factor_registry.register_class(Acceleration, "ACCELERATION")
factor_registry.register_class(RSQ, "RSQ")
factor_registry.register_class(MaxReturn, "MAX_RETURN")
factor_registry.register_class(DownsideRisk, "DOWNSIDE_RISK")
factor_registry.register_class(UpsidePotential, "UPSIDE_POTENTIAL")
factor_registry.register_class(RateOfChange, "RATE_OF_CHANGE")
factor_registry.register_class(WilliamsR, "WILLIAMS_R")
factor_registry.register_class(VolumeRatio, "VOLUME_RATIO")
factor_registry.register_class(VolumeMA, "VOLUME_MA")
factor_registry.register_class(Turnover, "TURNOVER")
factor_registry.register_class(VPrice, "VPRICE")
factor_registry.register_class(Volatility, "VOLATILITY")
factor_registry.register_class(NetFlow, "NET_FLOW")
factor_registry.register_class(VolumeTrend, "VOLUME_TREND")
factor_registry.register_class(PriceVolumeTrend, "PRICE_VOLUME_TREND")
factor_registry.register_class(VolumeOscillator, "VOLUME_OSCILLATOR")
factor_registry.register_class(PE, "PE")
factor_registry.register_class(PB, "PB")
factor_registry.register_class(PS, "PS")
factor_registry.register_class(MARKET_CAP, "MARKET_CAP")
factor_registry.register_class(CIRCULATING_CAP, "CIRCULATING_CAP")
factor_registry.register_class(EP, "EP")
factor_registry.register_class(BP, "BP")
factor_registry.register_class(LogMarketCap, "LOG_MARKET_CAP")
