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
            "category": self.category,
            "dependencies": self.dependencies,
            "params": self.params,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(name={self.name})"


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
