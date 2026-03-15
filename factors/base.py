"""
因子基类模块
定义因子接口规范和基础实现
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime
import inspect


class Factor(ABC):
    """
    因子基类

    所有因子实现都需要继承这个基类，并实现其抽象方法
    """

    # 因子元数据（子类需要覆盖）
    name: str = ""  # 因子名称，唯一标识符
    description: str = ""  # 因子描述
    author: str = ""  # 作者
    version: str = "1.0.0"  # 版本号
    category: str = ""  # 因子类别：technical, momentum, volume, fundamental等
    dependencies: List[str] = []  # 依赖的其他因子

    # 计算参数
    params: Dict[str, Any] = {}  # 参数定义及其默认值

    def __init__(self, **params):
        """
        初始化因子

        Args:
            **params: 因子参数
        """
        # 验证参数
        self._validate_params(params)

        # 设置参数
        self.params.update(params)

    def _validate_params(self, params: Dict[str, Any]):
        """
        验证参数

        Args:
            params: 参数字典

        Raises:
            ValueError: 如果参数无效
        """
        # 检查是否有未知的参数
        for key in params:
            if key not in self.params:
                raise ValueError(
                    f"未知参数: {key}. 可用参数: {list(self.params.keys())}"
                )

    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """
        计算因子值

        Args:
            data: 输入数据，至少包含以下列：
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - amount: 成交额

        Returns:
            因子值Series，index为日期
        """
        pass

    def __call__(self, data: pd.DataFrame) -> pd.Series:
        """
        使因子可调用

        Args:
            data: 输入数据

        Returns:
            因子值Series
        """
        return self.compute(data)

    def get_info(self) -> Dict[str, Any]:
        """
        获取因子信息

        Returns:
            因子信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "category": self.category,
            "dependencies": self.dependencies,
            "params": self.params,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(name={self.name}, version={self.version})"


class TechnicalFactor(Factor):
    """
    技术指标因子基类

    适用于基于价格和成交量的技术指标
    """

    category = "technical"


class MomentumFactor(Factor):
    """
    动量因子基类

    适用于基于价格动量的因子
    """

    category = "momentum"


class VolumeFactor(Factor):
    """
    成交量因子基类

    适用于基于成交量的因子
    """

    category = "volume"


class FundamentalFactor(Factor):
    """
    基本面因子基类

    适用于基于财务数据的因子
    """

    category = "fundamental"


class FactorCalculator:
    """
    因子计算器

    提供常用的因子计算辅助函数
    """

    @staticmethod
    def sma(series: pd.Series, window: int) -> pd.Series:
        """
        简单移动平均

        Args:
            series: 价格序列
            window: 窗口大小

        Returns:
            移动平均序列
        """
        return series.rolling(window=window).mean()

    @staticmethod
    def ema(series: pd.Series, window: int) -> pd.Series:
        """
        指数移动平均

        Args:
            series: 价格序列
            window: 窗口大小

        Returns:
            指数移动平均序列
        """
        return series.ewm(span=window, adjust=False).mean()

    @staticmethod
    def std(series: pd.Series, window: int) -> pd.Series:
        """
        滚动标准差

        Args:
            series: 价格序列
            window: 窗口大小

        Returns:
            标准差序列
        """
        return series.rolling(window=window).std()

    @staticmethod
    def rank(series: pd.Series) -> pd.Series:
        """
        排序（百分位）

        Args:
            series: 数据序列

        Returns:
            排序后的序列（0-1之间）
        """
        return series.rank(pct=True)

    @staticmethod
    def zscore(series: pd.Series) -> pd.Series:
        """
        Z-score标准化

        Args:
            series: 数据序列

        Returns:
            标准化后的序列（均值0，标准差1）
        """
        return (series - series.mean()) / series.std()

    @staticmethod
    def delta(series: pd.Series, periods: int = 1) -> pd.Series:
        """
        差分

        Args:
            series: 数据序列
            periods: 周期

        Returns:
            差分序列
        """
        return series.diff(periods)

    @staticmethod
    def ts_rank(series: pd.Series, window: int) -> pd.Series:
        """
        时间序列排序

        Args:
            series: 数据序列
            window: 窗口大小

        Returns:
            滚动排序序列
        """
        return series.rolling(window=window).apply(
            lambda x: x.rank(pct=True).iloc[-1]
        )

    @staticmethod
    def ts_max(series: pd.Series, window: int) -> pd.Series:
        """
        时间序列最大值

        Args:
            series: 数据序列
            window: 窗口大小

        Returns:
            滚动最大值序列
        """
        return series.rolling(window=window).max()

    @staticmethod
    def ts_min(series: pd.Series, window: int) -> pd.Series:
        """
        时间序列最小值

        Args:
            series: 数据序列
            window: 窗口大小

        Returns:
            滚动最小值序列
        """
        return series.rolling(window=window).min()

    @staticmethod
    def ts_argmax(series: pd.Series, window: int) -> pd.Series:
        """
        时间序列最大值位置

        Args:
            series: 数据序列
            window: 窗口大小

        Returns:
            最大值位置序列
        """
        return series.rolling(window=window).apply(
            lambda x: x.argmax(), raw=False
        )

    @staticmethod
    def ts_argmin(series: pd.Series, window: int) -> pd.Series:
        """
        时间序列最小值位置

        Args:
            series: 数据序列
            window: 窗口大小

        Returns:
            最小值位置序列
        """
        return series.rolling(window=window).apply(
            lambda x: x.argmin(), raw=False
        )

    @staticmethod
    def correlation(s1: pd.Series, s2: pd.Series, window: int) -> pd.Series:
        """
        滚动相关系数

        Args:
            s1: 序列1
            s2: 序列2
            window: 窗口大小

        Returns:
            相关系数序列
        """
        return s1.rolling(window=window).corr(s2)

    @staticmethod
    def covariance(s1: pd.Series, s2: pd.Series, window: int) -> pd.Series:
        """
        滚动协方差

        Args:
            s1: 序列1
            s2: 序列2
            window: 窗口大小

        Returns:
            协方差序列
        """
        return s1.rolling(window=window).cov(s2)

    @staticmethod
    def decile(series: pd.Series) -> pd.Series:
        """
        十分位分组

        Args:
            series: 数据序列

        Returns:
            十分位分组序列（1-10）
        """
        return pd.qcut(series, q=10, labels=False, duplicates="drop") + 1


class FactorValidator:
    """
    因子验证器

    用于验证因子计算结果的有效性
    """

    @staticmethod
    def validate_factor_values(factor_values: pd.Series) -> Dict[str, Any]:
        """
        验证因子值

        Args:
            factor_values: 因子值序列

        Returns:
            验证结果字典
        """
        result = {
            "valid": True,
            "warnings": [],
            "errors": [],
        }

        # 检查是否为空
        if factor_values.empty:
            result["valid"] = False
            result["errors"].append("因子值为空")
            return result

        # 检查缺失值比例
        missing_ratio = factor_values.isna().sum() / len(factor_values)
        if missing_ratio > 0.5:
            result["valid"] = False
            result["errors"].append(f"缺失值比例过高: {missing_ratio:.2%}")
        elif missing_ratio > 0.1:
            result["warnings"].append(f"缺失值比例较高: {missing_ratio:.2%}")

        # 检查无穷值
        if np.isinf(factor_values).any():
            result["valid"] = False
            result["errors"].append("存在无穷值")

        # 检查是否为常数
        if factor_values.std() == 0:
            result["warnings"].append("因子值为常数")

        # 检查异常值
        q1 = factor_values.quantile(0.25)
        q3 = factor_values.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr

        outliers = (
            (factor_values < lower_bound) | (factor_values > upper_bound)
        ).sum()
        outlier_ratio = outliers / len(factor_values)

        if outlier_ratio > 0.05:
            result["warnings"].append(f"异常值比例较高: {outlier_ratio:.2%}")

        return result
