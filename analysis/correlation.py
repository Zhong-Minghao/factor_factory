"""
因子相关性分析模块
分析因子间的相关性、多重共线性、PCA聚类等
"""
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings


class CorrelationAnalyzer:
    """
    因子相关性分析器

    分析因子间的相关性结构

    功能：
    - 截面相关性（因子间相关）
    - 时间序列相关性（因子自相关）
    - 滚动窗口相关性
    - VIF（方差膨胀因子）
    - 多重共线性检验
    - PCA降维和聚类
    """

    def __init__(self):
        """初始化相关性分析器"""
        pass

    def compute_cross_sectional_correlation(
        self,
        factor_dict: Dict[str, pd.DataFrame],
        method: str = "spearman",
    ) -> pd.DataFrame:
        """
        计算因子间的截面相关性

        Args:
            factor_dict: 因子字典
                         {
                             'factor_name_1': factor_df_1,
                             'factor_name_2': factor_df_2,
                             ...
                         }
                         其中每个factor_df是宽表格式（index=trade_date, columns=ts_code）
            method: 相关性方法
                    - 'pearson': Pearson相关系数
                    - 'spearman': Spearman秩相关系数（默认）
                    - 'kendall': Kendall秩相关系数

        Returns:
            相关性矩阵DataFrame
                index: 因子名称
                columns: 因子名称
                values: 相关系数
        """
        # 对齐所有因子的日期和股票
        common_index = None
        common_columns = None

        for factor_data in factor_dict.values():
            if common_index is None:
                common_index = factor_data.index
                common_columns = factor_data.columns
            else:
                common_index = common_index.intersection(factor_data.index)
                common_columns = common_columns.intersection(factor_data.columns)

        if common_index.empty or common_columns.empty:
            raise ValueError("因子没有共同的日期或股票")

        # 展平因子值（将截面数据展平）
        flattened_factors = {}

        for factor_name, factor_data in factor_dict.items():
            # 筛选共同日期和股票
            aligned_data = factor_data.loc[common_index, common_columns]

            # 展平
            flattened = aligned_data.values.flatten()

            # 去除NaN
            flattened = flattened[~pd.isna(flattened)]

            flattened_factors[factor_name] = flattened

        # 计算相关性矩阵
        factor_names = list(flattened_factors.keys())
        n_factors = len(factor_names)

        corr_matrix = pd.DataFrame(np.eye(n_factors), index=factor_names, columns=factor_names)

        for i, factor_i in enumerate(factor_names):
            for j, factor_j in enumerate(factor_names):
                if i < j:
                    # 计算相关系数
                    if method == "pearson":
                        corr, _ = stats.pearsonr(flattened_factors[factor_i], flattened_factors[factor_j])
                    elif method == "spearman":
                        corr, _ = stats.spearmanr(flattened_factors[factor_i], flattened_factors[factor_j])
                    elif method == "kendall":
                        corr, _ = stats.kendalltau(flattened_factors[factor_i], flattened_factors[factor_j])
                    else:
                        raise ValueError(f"未知的相关性方法: {method}")

                    corr_matrix.loc[factor_i, factor_j] = corr
                    corr_matrix.loc[factor_j, factor_i] = corr

        return corr_matrix

    def compute_autocorrelation(
        self,
        factor_data: pd.DataFrame,
        nlags: int = 5,
    ) -> pd.Series:
        """
        计算因子的时间序列自相关性

        Args:
            factor_data: 因子值DataFrame（宽表格式）
            nlags: 滞后期数

        Returns:
            自相关系数Series
                index: lag (0, 1, 2, ..., nlags)
                values: 自相关系数
        """
        # 计算所有股票的平均因子值（时间序列）
        mean_factor = factor_data.mean(axis=1)

        # 计算自相关系数
        autocorr = []

        for lag in range(nlags + 1):
            if lag == 0:
                corr = 1.0
            else:
                # 计算滞后相关
                series = mean_factor[lag:]
                lagged = mean_factor[:-lag]

                # 对齐
                aligned = pd.DataFrame({"current": series, "lagged": lagged}).dropna()

                if len(aligned) < 2:
                    corr = np.nan
                else:
                    corr, _ = stats.pearsonr(aligned["current"], aligned["lagged"])

            autocorr.append(corr)

        return pd.Series(autocorr, index=range(nlags + 1))

    def compute_rolling_correlation(
        self,
        factor_dict: Dict[str, pd.DataFrame],
        window: int = 60,
        method: str = "spearman",
    ) -> pd.DataFrame:
        """
        计算滚动窗口相关性

        Args:
            factor_dict: 因子字典
            window: 窗口大小（天数）
            method: 相关性方法

        Returns:
            滚动相关性DataFrame
                index: 日期
                columns: (factor1, factor2) 对
                values: 相关系数
        """
        # 获取共同日期
        common_index = None
        for factor_data in factor_dict.values():
            if common_index is None:
                common_index = factor_data.index
            else:
                common_index = common_index.intersection(factor_data.index)

        if len(common_index) < window:
            raise ValueError(f"数据不足，需要至少{window}天的数据")

        # 计算滚动相关性
        factor_names = list(factor_dict.keys())

        # 只计算因子对（不重复）
        factor_pairs = []
        for i, factor_i in enumerate(factor_names):
            for j, factor_j in enumerate(factor_names):
                if i < j:
                    factor_pairs.append((factor_i, factor_j))

        rolling_corr = pd.DataFrame(index=common_index[window - 1 :], columns=[f"{p[0]}_{p[1]}" for p in factor_pairs])

        for i in range(window - 1, len(common_index)):
            current_date = common_index[i]
            window_start = common_index[i - window + 1]
            window_end = current_date

            # 提取窗口数据
            window_data = {}
            for factor_name, factor_data in factor_dict.items():
                window_data[factor_name] = factor_data.loc[window_start:window_end]

            # 计算相关性
            corr_matrix = self.compute_cross_sectional_correlation(window_data, method=method)

            # 提取因子对的相关系数
            for pair in factor_pairs:
                factor_i, factor_j = pair
                corr_value = corr_matrix.loc[factor_i, factor_j]
                rolling_corr.loc[current_date, f"{factor_i}_{factor_j}"] = corr_value

        return rolling_corr

    def compute_vif(
        self,
        factor_dict: Dict[str, pd.DataFrame],
    ) -> pd.Series:
        """
        计算VIF（方差膨胀因子）

        VIF用于检测多重共线性
        VIF > 10 表示存在严重的多重共线性

        Args:
            factor_dict: 因子字典

        Returns:
            VIF值Series
                index: 因子名称
                values: VIF值

        Note:
            VIF计算公式：
            VIF_i = 1 / (1 - R_i^2)

            其中R_i^2是因子i对其他因子回归的R方
        """
        # 获取共同日期和股票
        common_index = None
        common_columns = None

        for factor_data in factor_dict.values():
            if common_index is None:
                common_index = factor_data.index
                common_columns = factor_data.columns
            else:
                common_index = common_index.intersection(factor_data.index)
                common_columns = common_columns.intersection(factor_data.columns)

        # 构建回归矩阵
        n_samples = len(common_index) * len(common_columns)
        n_factors = len(factor_dict)

        # 创建矩阵
        X = np.zeros((n_samples, n_factors))

        for j, (factor_name, factor_data) in enumerate(factor_dict.items()):
            aligned_data = factor_data.loc[common_index, common_columns]
            X[:, j] = aligned_data.values.flatten()

        # 移除NaN
        valid_mask = ~pd.isna(X).any(axis=1)
        X = X[valid_mask]

        # 计算VIF
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        vif_values = []

        for j in range(n_factors):
            try:
                vif = variance_inflation_factor(X, j)
                vif_values.append(vif)
            except Exception as e:
                warnings.warn(f"计算因子{j}的VIF失败: {e}")
                vif_values.append(np.nan)

        vif_series = pd.Series(vif_values, index=list(factor_dict.keys()))

        return vif_series

    def test_multicollinearity(
        self,
        factor_dict: Dict[str, pd.DataFrame],
        threshold: float = 10.0,
    ) -> Dict[str, Union[bool, List[str], pd.Series]]:
        """
        多重共线性检验

        Args:
            factor_dict: 因子字典
            threshold: VIF阈值，默认10

        Returns:
            检验结果字典
                {
                    'has_multicollinearity': 是否存在多重共线性,
                    'high_vif_factors': VIF超过阈值的因子列表,
                    'vif_values': 所有因子的VIF值,
                }
        """
        # 计算VIF
        vif_series = self.compute_vif(factor_dict)

        # 找出高VIF的因子
        high_vif_factors = vif_series[vif_series > threshold].index.tolist()

        # 判断是否存在多重共线性
        has_multicollinearity = len(high_vif_factors) > 0

        return {
            "has_multicollinearity": has_multicollinearity,
            "high_vif_factors": high_vif_factors,
            "vif_values": vif_series,
        }

    def compute_pca(
        self,
        factor_dict: Dict[str, pd.DataFrame],
        n_components: Optional[int] = None,
    ) -> Dict[str, Union[np.ndarray, PCA, pd.DataFrame]]:
        """
        PCA降维分析

        Args:
            factor_dict: 因子字典
            n_components: 主成分数量，None表示自动选择

        Returns:
            PCA分析结果
                {
                    'components': 主成分,
                    'explained_variance': 解释方差,
                    'explained_variance_ratio': 解释方差比例,
                    'cumulative_variance_ratio': 累计解释方差比例,
                    'factor_loadings': 因子载荷,
                    'pca_model': PCA模型对象,
                }
        """
        # 获取共同日期和股票
        common_index = None
        common_columns = None

        for factor_data in factor_dict.values():
            if common_index is None:
                common_index = factor_data.index
                common_columns = factor_data.columns
            else:
                common_index = common_index.intersection(factor_data.index)
                common_columns = common_columns.intersection(factor_data.columns)

        # 构建矩阵
        n_samples = len(common_index) * len(common_columns)
        n_factors = len(factor_dict)

        X = np.zeros((n_samples, n_factors))

        for j, (factor_name, factor_data) in enumerate(factor_dict.items()):
            aligned_data = factor_data.loc[common_index, common_columns]
            X[:, j] = aligned_data.values.flatten()

        # 移除NaN
        valid_mask = ~pd.isna(X).any(axis=1)
        X = X[valid_mask]

        # 标准化
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # PCA
        if n_components is None:
            n_components = min(n_factors, X_scaled.shape[0])

        pca = PCA(n_components=n_components)
        components = pca.fit_transform(X_scaled)

        # 因子载荷（主成分与原始因子的相关系数）
        factor_loadings = pd.DataFrame(
            pca.components_.T,
            index=list(factor_dict.keys()),
            columns=[f"PC{i + 1}" for i in range(n_components)],
        )

        # 累计解释方差
        cumulative_variance_ratio = np.cumsum(pca.explained_variance_ratio_)

        return {
            "components": components,
            "explained_variance": pca.explained_variance_,
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "cumulative_variance_ratio": cumulative_variance_ratio,
            "factor_loadings": factor_loadings,
            "pca_model": pca,
        }


# 便捷函数
def compute_factor_correlation(
    factor_dict: Dict[str, pd.DataFrame],
    method: str = "spearman",
) -> pd.DataFrame:
    """
    快捷计算因子相关性

    Args:
        factor_dict: 因子字典
        method: 相关性方法

    Returns:
        相关性矩阵
    """
    analyzer = CorrelationAnalyzer()
    return analyzer.compute_cross_sectional_correlation(factor_dict, method=method)


def compute_vif(
    factor_dict: Dict[str, pd.DataFrame],
) -> pd.Series:
    """
    快捷计算VIF

    Args:
        factor_dict: 因子字典

    Returns:
        VIF值Series
    """
    analyzer = CorrelationAnalyzer()
    return analyzer.compute_vif(factor_dict)
