"""
因子预处理模块
提供去极值、标准化、中性化等预处理功能
"""
from typing import Optional, Union, List
import pandas as pd
import numpy as np
from scipy import stats


def mad_outlier_treatment(
    factor_values: pd.DataFrame,
    n: float = 3.0,
) -> pd.DataFrame:
    """
    MAD法去极值（Median Absolute Deviation）

    使用中位数绝对偏差方法处理异常值
    这是量化圈最常用的去极值方法

    Args:
        factor_values: 因子值DataFrame（宽表格式）
                      index: trade_date
                      columns: ts_code
                      values: factor_value
        n: MAD倍数，默认3.0

    Returns:
        去极值后的因子值DataFrame

    Note:
        公式：
        1. 计算中位数：median = factor_values.median()
        2. 计算MAD：mad = median(|factor_values - median|)
        3. 定义上限：upper = median + n * mad * 1.4826
        4. 定义下限：lower = median - n * mad * 1.4826
        5. 超过上限的值设为上限，低于下限的值设为下限

        其中1.4826是正态分布MAD到标准差的转换系数
    """
    result = factor_values.copy()

    # 对每个日期（每一行）分别处理
    for date in result.index:
        row_data = result.loc[date]

        # 计算中位数
        median = row_data.median()

        # 计算MAD
        mad = np.median(np.abs(row_data - median))

        # 计算上下限
        upper = median + n * mad * 1.4826
        lower = median - n * mad * 1.4826

        # 去极值
        result.loc[date, :] = row_data.clip(lower=lower, upper=upper)

    return result


def sigma_outlier_treatment(
    factor_values: pd.DataFrame,
    n: float = 3.0,
) -> pd.DataFrame:
    """
    3-sigma法去极值

    Args:
        factor_values: 因子值DataFrame（宽表格式）
        n: 标准差倍数，默认3.0

    Returns:
        去极值后的因子值DataFrame

    Note:
        公式：
        1. 计算均值：mean = factor_values.mean()
        2. 计算标准差：std = factor_values.std()
        3. 定义上限：upper = mean + n * std
        4. 定义下限：lower = mean - n * std
        5. 超过上限的值设为上限，低于下限的值设为下限
    """
    result = factor_values.copy()

    # 对每个日期分别处理
    for date in result.index:
        row_data = result.loc[date]

        # 计算均值和标准差
        mean = row_data.mean()
        std = row_data.std()

        # 计算上下限
        upper = mean + n * std
        lower = mean - n * std

        # 去极值
        result.loc[date, :] = row_data.clip(lower=lower, upper=upper)

    return result


def quantile_outlier_treatment(
    factor_values: pd.DataFrame,
    lower_quantile: float = 0.01,
    upper_quantile: float = 0.99,
) -> pd.DataFrame:
    """
    百分位法去极值

    Args:
        factor_values: 因子值DataFrame（宽表格式）
        lower_quantile: 下分位数，默认0.01
        upper_quantile: 上分位数，默认0.99

    Returns:
        去极值后的因子值DataFrame
    """
    result = factor_values.copy()

    # 对每个日期分别处理
    for date in result.index:
        row_data = result.loc[date]

        # 计算分位数
        lower = row_data.quantile(lower_quantile)
        upper = row_data.quantile(upper_quantile)

        # 去极值
        result.loc[date, :] = row_data.clip(lower=lower, upper=upper)

    return result


def zscore_standardization(
    factor_values: pd.DataFrame,
) -> pd.DataFrame:
    """
    Z-score标准化

    将因子值标准化为均值为0，标准差为1的分布

    Args:
        factor_values: 因子值DataFrame（宽表格式）

    Returns:
        标准化后的因子值DataFrame

    Note:
        公式：z = (x - μ) / σ
        其中μ为均值，σ为标准差
    """
    result = factor_values.copy()

    # 对每个日期分别处理（截面标准化）
    for date in result.index:
        row_data = result.loc[date]

        # 计算均值和标准差
        mean = row_data.mean()
        std = row_data.std()

        # 避免除以0
        if std == 0 or pd.isna(std):
            result.loc[date, :] = 0
        else:
            result.loc[date, :] = (row_data - mean) / std

    return result


def rank_standardization(
    factor_values: pd.DataFrame,
) -> pd.DataFrame:
    """
    排序标准化（Rank标准化）

    将因子值转换为其在截面中的排名，然后标准化

    Args:
        factor_values: 因子值DataFrame（宽表格式）

    Returns:
        排序标准化后的因子值DataFrame

    Note:
        排序标准化对异常值更稳健
    """
    result = factor_values.copy()

    # 对每个日期分别处理
    for date in result.index:
        row_data = result.loc[date]

        # 计算排名（百分比）
        rank = row_data.rank(pct=True)

        # 标准化
        result.loc[date, :] = (rank - rank.mean()) / rank.std()

    return result


def neutralize(
    factor_values: pd.DataFrame,
    industry_df: Optional[pd.DataFrame] = None,
    market_cap_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    因子中性化

    对行业、市值等因子进行正交化处理

    Args:
        factor_values: 因子值DataFrame（宽表格式）
        industry_df: 行业分类DataFrame（宽表格式）
                      如果提供，进行行业中性化
        market_cap_df: 市值DataFrame（宽表格式，取对数）
                       如果提供，进行市值中性化

    Returns:
        中性化后的因子值DataFrame

    Note:
        TODO: 完整实现中性化功能
        当前版本为简单实现，仅返回标准化后的值

        完整实现需要：
        1. 对行业哑变量回归取残差（行业中性化）
        2. 对ln(市值)回归取残差（市值中性化）
        3. 对行业+市值联合回归取残差
    """
    result = factor_values.copy()

    # TODO: 实现完整的中性化
    # 目前先做简单的Z-score标准化
    result = zscore_standardization(result)

    return result


def preprocess_factor(
    factor_values: pd.DataFrame,
    outlier_method: str = "mad",
    standardize: bool = True,
    neutralize: bool = False,
    industry_df: Optional[pd.DataFrame] = None,
    market_cap_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    完整的因子预处理流程

    Args:
        factor_values: 因子值DataFrame（宽表格式）
        outlier_method: 去极值方法
                        - 'mad': MAD法（默认）
                        - 'sigma': 3-sigma法
                        - 'quantile': 百分位法
                        - 'none': 不去极值
        standardize: 是否标准化（Z-score）
        neutralize: 是否中性化
        industry_df: 行业分类DataFrame（用于中性化）
        market_cap_df: 市值DataFrame（用于中性化）

    Returns:
        预处理后的因子值DataFrame
    """
    result = factor_values.copy()

    # 1. 去极值
    if outlier_method != "none":
        if outlier_method == "mad":
            result = mad_outlier_treatment(result)
        elif outlier_method == "sigma":
            result = sigma_outlier_treatment(result)
        elif outlier_method == "quantile":
            result = quantile_outlier_treatment(result)
        else:
            raise ValueError(f"未知的去极值方法: {outlier_method}")

    # 2. 标准化
    if standardize:
        result = zscore_standardization(result)

    # 3. 中性化
    if neutralize:
        result = neutralize(
            result,
            industry_df=industry_df,
            market_cap_df=market_cap_df,
        )

    return result


def winsorize_factor(
    factor_values: pd.Series,
    limits: tuple = (0.01, 0.99),
) -> pd.Series:
    """
    对单列因子值进行缩尾处理（类似scipy.stats.winsorize）

    Args:
        factor_values: 因子值Series
        limits: 缩尾的上下限（分位数）

    Returns:
        缩尾后的因子值Series
    """
    from scipy.stats import mstats

    # 移除NaN
    valid_mask = ~pd.isna(factor_values)
    valid_values = factor_values[valid_mask].values

    # 缩尾处理
    winsorized = mstats.winsorize(valid_values, limits=limits)

    # 返回Series
    result = factor_values.copy()
    result[valid_mask] = winsorized

    return result


def fill_missing_values(
    factor_values: pd.DataFrame,
    method: str = "drop",
) -> pd.DataFrame:
    """
    处理缺失值

    Args:
        factor_values: 因子值DataFrame（宽表格式）
        method: 处理方法
                - 'drop': 删除包含NaN的行/列
                - 'zero': 用0填充
                - 'median': 用中位数填充
                - 'mean': 用均值填充
                - 'ffill': 前向填充

    Returns:
        处理后的因子值DataFrame
    """
    result = factor_values.copy()

    if method == "drop":
        # 删除全为NaN的列，然后删除包含NaN的行
        result = result.dropna(axis=1, how="all")
        result = result.dropna(axis=0, how="any")
    elif method == "zero":
        result = result.fillna(0)
    elif method == "median":
        # 对每列用中位数填充
        result = result.fillna(result.median())
    elif method == "mean":
        # 对每列用均值填充
        result = result.fillna(result.mean())
    elif method == "ffill":
        # 前向填充
        result = result.fillna(method="ffill")
    else:
        raise ValueError(f"未知的缺失值处理方法: {method}")

    return result
