"""
股票选择器模块
提供多种选股方式：Top N、分层、百分比
"""
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import warnings


class StockSelector:
    """
    股票选择器

    提供基于因子值的股票选择方法：
    - Top N: 选择因子值最高的 N 只股票
    - 分层: 按因子值分层，选择指定层
    - 百分比: 选择因子值最高的前 X% 股票
    """

    @staticmethod
    def select_top_n(
        factor_values: pd.Series,
        top_n: int,
        min_stocks: int = 5,
    ) -> List[str]:
        """
        选择因子值最高的 N 只股票

        Args:
            factor_values: 因子值 Series，index 为股票代码
            top_n: 选择的股票数量
            min_stocks: 最小股票数量（如果可用股票不足，至少返回 min_stocks）

        Returns:
            选中股票代码列表

        Example:
            >>> factor_values = pd.Series([1.2, 0.8, 1.5, 0.9], index=['A', 'B', 'C', 'D'])
            >>> StockSelector.select_top_n(factor_values, 2)
            ['C', 'A']  # 选择因子值最高的2只股票
        """
        # 去除 NaN
        valid_values = factor_values.dropna()

        if len(valid_values) == 0:
            warnings.warn("因子值全为空，返回空列表")
            return []

        # 如果可用股票不足 top_n，调整数量
        n = min(top_n, len(valid_values))
        n = max(n, min_stocks)  # 至少返回 min_stocks 只

        # 选择因子值最高的 N 只
        selected = valid_values.nlargest(n)

        return selected.index.tolist()

    @staticmethod
    def select_by_layer(
        factor_values: pd.Series,
        n_layers: int = 5,
        layer_id: int = 4,
    ) -> List[str]:
        """
        按因子值分层，选择指定层的股票

        Args:
            factor_values: 因子值 Series
            n_layers: 分层数量
            layer_id: 选择的层 ID（0 到 n_layers-1），默认为 4（最高层）

        Returns:
            选中股票代码列表

        Example:
            >>> factor_values = pd.Series([1.2, 0.8, 1.5, 0.9, 0.5, 1.0], index=['A', 'B', 'C', 'D', 'E', 'F'])
            >>> StockSelector.select_by_layer(factor_values, n_layers=3, layer_id=2)
            ['C', 'A']  # 第3层（因子值最高）
        """
        # 去除 NaN
        valid_values = factor_values.dropna()

        if len(valid_values) == 0:
            warnings.warn("因子值全为空，返回空列表")
            return []

        # 验证参数
        if n_layers < 2:
            raise ValueError(f"分层数量必须 >= 2，当前为 {n_layers}")
        if layer_id < 0 or layer_id >= n_layers:
            raise ValueError(f"层 ID 必须在 [0, {n_layers-1}] 范围内，当前为 {layer_id}")

        # 计算分位数边界
        quantiles = np.linspace(0, 1, n_layers + 1)

        # 获取当前层的上下界
        lower = valid_values.quantile(quantiles[layer_id])
        upper = valid_values.quantile(quantiles[layer_id + 1])

        # 选择该层的股票
        # 最后一层包含上界值，其他层不包含上界值（避免重复）
        if layer_id == n_layers - 1:
            mask = (valid_values >= lower) & (valid_values <= upper)
        else:
            mask = (valid_values >= lower) & (valid_values < upper)

        selected = valid_values[mask]

        return selected.index.tolist()

    @staticmethod
    def select_by_percentile(
        factor_values: pd.Series,
        percentile: float = 0.2,
        min_stocks: int = 5,
    ) -> List[str]:
        """
        选择因子值最高的前 X% 股票

        Args:
            factor_values: 因子值 Series
            percentile: 百分比（0-1），例如 0.2 表示前 20%
            min_stocks: 最小股票数量

        Returns:
            选中股票代码列表

        Example:
            >>> factor_values = pd.Series([1.2, 0.8, 1.5, 0.9, 0.5, 1.0, 0.7, 0.6, 1.1, 0.4],
            ...                          index=list('ABCDEFGHIJ'))
            >>> StockSelector.select_by_percentile(factor_values, 0.3)
            ['C', 'A', 'J']  # 前 30%（约3只股票）
        """
        # 验证参数
        if not 0 < percentile <= 1:
            raise ValueError(f"百分比必须在 (0, 1] 范围内，当前为 {percentile}")

        # 去除 NaN
        valid_values = factor_values.dropna()

        if len(valid_values) == 0:
            warnings.warn("因子值全为空，返回空列表")
            return []

        # 计算阈值（前 percentile%）
        threshold = valid_values.quantile(1 - percentile)

        # 选择因子值 >= 阈值的股票
        selected = valid_values[valid_values >= threshold]

        # 确保至少有 min_stocks 只股票
        if len(selected) < min_stocks and len(valid_values) >= min_stocks:
            selected = valid_values.nlargest(min_stocks)

        return selected.index.tolist()

    @staticmethod
    def select(
        factor_values: pd.Series,
        method: str = "top_n",
        params: Dict[str, Any] = None,
    ) -> List[str]:
        """
        统一的股票选择接口

        Args:
            factor_values: 因子值 Series
            method: 选择方式
                - "top_n": Top N 选择
                - "layer": 分层选择
                - "percentile": 百分比选择
            params: 选择参数
                - top_n: {"top_n": 10}
                - layer: {"n_layers": 5, "layer_id": 4}
                - percentile: {"percentile": 0.2}

        Returns:
            选中股票代码列表

        Example:
            >>> # Top N 选择
            >>> StockSelector.select(factor_values, "top_n", {"top_n": 10})
            >>> # 分层选择
            >>> StockSelector.select(factor_values, "layer", {"n_layers": 5, "layer_id": 4})
            >>> # 百分比选择
            >>> StockSelector.select(factor_values, "percentile", {"percentile": 0.2})
        """
        params = params or {}

        if method == "top_n":
            return StockSelector.select_top_n(
                factor_values,
                top_n=params.get("top_n", 10),
                min_stocks=params.get("min_stocks", 5),
            )
        elif method == "layer":
            return StockSelector.select_by_layer(
                factor_values,
                n_layers=params.get("n_layers", 5),
                layer_id=params.get("layer_id", 4),
            )
        elif method == "percentile":
            return StockSelector.select_by_percentile(
                factor_values,
                percentile=params.get("percentile", 0.2),
                min_stocks=params.get("min_stocks", 5),
            )
        else:
            raise ValueError(f"未知的选股方式: {method}，可选: top_n, layer, percentile")
