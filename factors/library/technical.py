"""
技术指标因子库
包含常用的技术分析因子
"""
from typing import Optional
import pandas as pd
import numpy as np

from ..base import TechnicalFactor, FactorCalculator
from ..registry import register_factor


class MA(TechnicalFactor):
    """移动平均线因子"""

    name = "MA"
    description = "简单移动平均线"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"window": 20}  # 默认20日均线

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算移动平均线"""
        window = self.params.get("window", 20)
        calculator = FactorCalculator()
        return calculator.sma(data["close"], window)


@register_factor("EMA")
class EMA(TechnicalFactor):
    """指数移动平均线因子"""

    name = "EMA"
    description = "指数移动平均线"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算指数移动平均线"""
        window = self.params.get("window", 20)
        calculator = FactorCalculator()
        return calculator.ema(data["close"], window)


@register_factor("MACD")
class MACD(TechnicalFactor):
    """MACD因子"""

    name = "MACD"
    description = "指数平滑异同移动平均线"
    author = "Factor Factory"
    version = "1.0.0"
    params = {
        "fast": 12,
        "slow": 26,
        "signal": 9,
    }

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算MACD"""
        fast = self.params.get("fast", 12)
        slow = self.params.get("slow", 26)
        signal = self.params.get("signal", 9)

        calculator = FactorCalculator()

        # 计算快速和慢速EMA
        ema_fast = calculator.ema(data["close"], fast)
        ema_slow = calculator.ema(data["close"], slow)

        # DIF线
        dif = ema_fast - ema_slow

        # DEA线（信号线）
        dea = calculator.ema(dif, signal)

        # MACD柱
        macd = (dif - dea) * 2

        return macd


@register_factor("RSI")
class RSI(TechnicalFactor):
    """相对强弱指标因子"""

    name = "RSI"
    description = "相对强弱指标"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"window": 14}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算RSI"""
        window = self.params.get("window", 14)

        # 计算价格变化
        delta = data["close"].diff()

        # 分离上涨和下跌
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)

        # 计算平均涨跌幅
        avg_gains = gains.rolling(window=window).mean()
        avg_losses = losses.rolling(window=window).mean()

        # 计算RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi


@register_factor("BOLL")
class BOLL(TechnicalFactor):
    """布林带因子"""

    name = "BOLL"
    description = "布林带"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"window": 20, "num_std": 2}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算布林带宽度"""
        window = self.params.get("window", 20)
        num_std = self.params.get("num_std", 2)

        calculator = FactorCalculator()

        # 计算中轨（移动平均）
        middle = calculator.sma(data["close"], window)

        # 计算标准差
        std = calculator.std(data["close"], window)

        # 计算上下轨
        upper = middle + num_std * std
        lower = middle - num_std * std

        # 返回布林带宽度
        boll_width = (upper - lower) / middle

        return boll_width


@register_factor("ATR")
class ATR(TechnicalFactor):
    """平均真实波幅因子"""

    name = "ATR"
    description = "平均真实波幅"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"window": 14}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算ATR"""
        window = self.params.get("window", 14)

        # 计算真实波幅
        high_low = data["high"] - data["low"]
        high_close = np.abs(data["high"] - data["close"].shift())
        low_close = np.abs(data["low"] - data["close"].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # 计算平均真实波幅
        atr = tr.rolling(window=window).mean()

        return atr


@register_factor("KDJ")
class KDJ(TechnicalFactor):
    """KDJ指标因子"""

    name = "KDJ"
    description = "随机指标KDJ"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"n": 9, "m1": 3, "m2": 3}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算KDJ的J值"""
        n = self.params.get("n", 9)
        m1 = self.params.get("m1", 3)
        m2 = self.params.get("m2", 3)

        # 计算RSV
        low_n = data["low"].rolling(window=n).min()
        high_n = data["high"].rolling(window=n).max()
        rsv = (data["close"] - low_n) / (high_n - low_n) * 100

        # 计算K值
        k = rsv.ewm(com=m1 - 1, adjust=False).mean()

        # 计算D值
        d = k.ewm(com=m2 - 1, adjust=False).mean()

        # 计算J值
        j = 3 * k - 2 * d

        return j


@register_factor("CCI")
class CCI(TechnicalFactor):
    """顺势指标因子"""

    name = "CCI"
    description = "顺势指标"
    author = "Factor Factory"
    version = "1.0.0"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算CCI"""
        window = self.params.get("window", 20)

        # 计算典型价格
        tp = (data["high"] + data["low"] + data["close"]) / 3

        # 计算移动平均
        ma_tp = tp.rolling(window=window).mean()

        # 计算平均绝对偏差
        mad = tp.rolling(window=window).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        # 计算CCI
        cci = (tp - ma_tp) / (0.015 * mad)

        return cci


@register_factor("OBV")
class OBV(TechnicalFactor):
    """能量潮因子"""

    name = "OBV"
    description = "能量潮"
    author = "Factor Factory"
    version = "1.0.0"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算OBV"""
        # 计算价格变化方向
        price_change = data["close"].diff()

        # 确定成交量方向
        volume_direction = np.where(price_change > 0, 1, np.where(price_change < 0, -1, 0))

        # 计算OBV
        obv = (volume_direction * data["volume"]).cumsum()

        return obv
