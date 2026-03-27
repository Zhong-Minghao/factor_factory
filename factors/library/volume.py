"""
成交量因子库
包含成交量相关因子
"""
import pandas as pd
import numpy as np

from ..base import VolumeFactor
from ..registry import register_factor


@register_factor("VOLUME_RATIO")
class VolumeRatio(VolumeFactor):
    """量比因子"""

    name = "VOLUME_RATIO"
    description = "量比（当前成交量/过去N日平均成交量）"
    params = {"window": 5}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算量比"""
        window = self.params.get("window", 5)

        # 计算平均成交量
        avg_volume = data["volume"].rolling(window=window).mean()

        # 量比
        volume_ratio = data["volume"] / avg_volume

        return volume_ratio


@register_factor("VOLUME_MA")
class VolumeMA(VolumeFactor):
    """成交量均线因子"""

    name = "VOLUME_MA"
    description = "成交量移动平均"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算成交量均线"""
        window = self.params.get("window", 20)

        # 成交量移动平均
        volume_ma = data["volume"].rolling(window=window).mean()

        # 标准化（当前成交量/均线）
        volume_ma_ratio = data["volume"] / volume_ma

        return volume_ma_ratio


@register_factor("TURNOVER")
class Turnover(VolumeFactor):
    """换手率因子"""

    name = "TURNOVER"
    description = "换手率（需要流通股本数据）"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算换手率（简化版本：使用成交额代替）"""
        # 如果有换手率列，直接使用
        if "turnover" in data.columns:
            return data["turnover"]

        # 否则使用成交额作为代理
        # 计算成交额的移动平均
        amount_ma = data["amount"].rolling(window=20).mean()

        # 换手率代理指标
        turnover_proxy = data["amount"] / amount_ma

        return turnover_proxy


@register_factor("VPRICE")
class VPrice(VolumeFactor):
    """量价配合因子"""

    name = "VPRICE"
    description = "量价配合度（价格上涨时的成交量占比）"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算量价配合度"""
        window = self.params.get("window", 20)

        # 计算价格变化
        price_change = data["close"].diff()

        # 判断是否上涨
        is_up = price_change > 0

        # 上涨日的成交量
        up_volume = data["volume"].where(is_up, 0)

        # 计算上涨日成交量占比
        total_volume = data["volume"].rolling(window=window).sum()
        up_volume_sum = up_volume.rolling(window=window).sum()

        vprice = up_volume_sum / total_volume

        return vprice


@register_factor("VOLATILITY")
class Volatility(VolumeFactor):
    """成交量波动率因子"""

    name = "VOLATILITY"
    description = "成交量波动率"
    params = {"window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算成交量波动率"""
        window = self.params.get("window", 20)

        # 计算成交量变化率
        volume_change = data["volume"].pct_change()

        # 计算滚动标准差
        volume_std = volume_change.rolling(window=window).std()

        return volume_std


@register_factor("NET_FLOW")
class NetFlow(VolumeFactor):
    """资金净流入因子"""

    name = "NET_FLOW"
    description = "资金净流入（基于价格变化和成交量的代理指标）"
    params = {"window": 5}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算资金净流入"""
        window = self.params.get("window", 5)

        # 计算价格变化
        price_change = data["close"].pct_change()

        # 判断涨跌
        direction = np.sign(price_change)

        # 资金流向 = 成交额 * 涨跌方向
        money_flow = data["amount"] * direction

        # 累计净流入
        net_flow = money_flow.rolling(window=window).sum()

        # 标准化（除以成交额）
        total_amount = data["amount"].rolling(window=window).sum()
        net_flow_ratio = net_flow / total_amount

        return net_flow_ratio


@register_factor("VOLUME_TREND")
class VolumeTrend(VolumeFactor):
    """成交量趋势因子"""

    name = "VOLUME_TREND"
    description = "成交量变化趋势"
    params = {"short_window": 5, "long_window": 20}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算成交量趋势"""
        short_window = self.params.get("short_window", 5)
        long_window = self.params.get("long_window", 20)

        # 计算短期和长期成交量均线
        short_ma = data["volume"].rolling(window=short_window).mean()
        long_ma = data["volume"].rolling(window=long_window).mean()

        # 成交量趋势
        volume_trend = short_ma / long_ma

        return volume_trend


@register_factor("PRICE_VOLUME_TREND")
class PriceVolumeTrend(VolumeFactor):
    """价量趋势因子"""

    name = "PRICE_VOLUME_TREND"
    description = "价量趋势（PVT）"
    params = {}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算价量趋势"""
        # 计算价格变化率
        price_change = data["close"].pct_change()

        # PVT = 前一日PVT + 成交额 * 价格变化率
        pvt = (price_change * data["amount"]).cumsum()

        return pvt


@register_factor("VOLUME_OSCILLATOR")
class VolumeOscillator(VolumeFactor):
    """成交量震荡因子"""

    name = "VOLUME_OSCILLATOR"
    description = "成交量震荡指标"
    params = {"fast_window": 5, "slow_window": 10}

    def compute(self, data: pd.DataFrame) -> pd.Series:
        """计算成交量震荡指标"""
        fast_window = self.params.get("fast_window", 5)
        slow_window = self.params.get("slow_window", 10)

        # 计算快慢均线
        fast_ma = data["volume"].rolling(window=fast_window).mean()
        slow_ma = data["volume"].rolling(window=slow_window).mean()

        # 震荡指标
        oscillator = (fast_ma - slow_ma) / slow_ma * 100

        return oscillator
