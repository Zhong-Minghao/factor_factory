"""
动量因子库
包含价格动量相关因子
"""
import pandas as pd
import numpy as np

from ..base import MomentumFactor
from ..registry import register_factor


@register_factor("RETURN")
class Return(MomentumFactor):
    """收益率因子"""

    name = "RETURN"
    description = "N日收益率"
    params = {"period": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算收益率"""
        period = self.params.get("period", 20)
        return data["close"].pct_change(period)


@register_factor("MOM")
class MOM(MomentumFactor):
    """动量因子"""

    name = "MOM"
    description = "N日动量（价格变化）"
    params = {"period": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算动量"""
        period = self.params.get("period", 20)
        return data["close"].diff(period)


@register_factor("ACCELERATION")
class Acceleration(MomentumFactor):
    """加速度因子"""

    name = "ACCELERATION"
    description = "价格加速度（二阶导数）"
    params = {"short_period": 5, "long_period": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算加速度"""
        short_period = self.params.get("short_period", 5)
        long_period = self.params.get("long_period", 20)

        # 计算短期和长期收益率
        short_return = data["close"].pct_change(short_period)
        long_return = data["close"].pct_change(long_period)

        # 加速度 = 短期收益率 - 长期收益率
        acceleration = short_return - long_return

        return acceleration


@register_factor("RSQ")
class RSQ(MomentumFactor):
    """R平方因子（趋势强度）"""

    name = "RSQ"
    description = "R平方，衡量价格趋势的强度"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算R平方"""
        window = self.params.get("window", 20)

        def calculate_r2(series):
            """计算R平方"""
            x = np.arange(len(series))
            y = series.values

            # 线性回归
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept

            # 计算R平方
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - y.mean()) ** 2)

            if ss_tot == 0:
                return 0

            r2 = 1 - (ss_res / ss_tot)
            return r2

        # 滚动计算R平方
        r2 = data["close"].rolling(window=window).apply(calculate_r2, raw=False)

        return r2


@register_factor("MAX_RETURN")
class MaxReturn(MomentumFactor):
    """最大收益率因子"""

    name = "MAX_RETURN"
    description = "N日内最大收益率"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算最大收益率"""
        window = self.params.get("window", 20)

        # 计算滚动最高价
        rolling_max = data["high"].rolling(window=window).max()

        # 计算最大收益率
        max_return = (rolling_max - data["close"]) / data["close"]

        return max_return


@register_factor("DOWNSIDE_RISK")
class DownsideRisk(MomentumFactor):
    """下行风险因子"""

    name = "DOWNSIDE_RISK"
    description = "下行波动率（只考虑下跌）"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算下行风险"""
        window = self.params.get("window", 20)

        # 计算收益率
        returns = data["close"].pct_change()

        # 只考虑负收益
        negative_returns = returns.where(returns < 0, 0)

        # 计算下行标准差
        downside_std = negative_returns.rolling(window=window).std()

        return downside_std


@register_factor("UPSIDE_POTENTIAL")
class UpsidePotential(MomentumFactor):
    """上行潜力因子"""

    name = "UPSIDE_POTENTIAL"
    description = "上行收益率（只考虑上涨）"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算上行潜力"""
        window = self.params.get("window", 20)

        # 计算收益率
        returns = data["close"].pct_change()

        # 只考虑正收益
        positive_returns = returns.where(returns > 0, 0)

        # 计算上行平均收益率
        upside_mean = positive_returns.rolling(window=window).mean()

        return upside_mean


@register_factor("RATE_OF_CHANGE")
class RateOfChange(MomentumFactor):
    """变化率因子"""

    name = "RATE_OF_CHANGE"
    description = "N日变化率（ROC）"
    params = {"period": 10}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算变化率"""
        period = self.params.get("period", 10)

        # ROC = (当前价格 - N日前价格) / N日前价格 * 100
        roc = (
            (data["close"] - data["close"].shift(period))
            / data["close"].shift(period)
            * 100
        )

        return roc


@register_factor("WILLIAMS_R")
class WilliamsR(MomentumFactor):
    """威廉指标因子"""

    name = "WILLIAMS_R"
    description = "威廉指标%R"
    params = {"window": 14}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算威廉指标"""
        window = self.params.get("window", 14)

        # 计算最高价和最低价
        high_n = data["high"].rolling(window=window).max()
        low_n = data["low"].rolling(window=window).min()

        # 计算威廉指标
        williams_r = (
            (high_n - data["close"]) / (high_n - low_n) * -100
        )

        return williams_r
