"""
IC/IR分析模块
计算因子的IC（Information Coefficient）和IR（Information Ratio）
"""
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy import stats
import warnings

from .preprocessing import preprocess_factor
from utils.calendar import get_calendar


class ICAnalyzer:
    """
    IC分析器

    计算因子的IC和IR统计指标

    IC定义：因子值与未来收益率的相关系数
    IR定义：IC均值 / IC标准差

    支持的IC类型：
    - Pearson IC：普通相关系数
    - Rank IC：Spearman秩相关系数（更稳健）
    """

    def __init__(
        self,
        ic_type: str = "rank",
        preprocess: bool = True,
        outlier_method: str = "mad",
    ):
        """
        初始化IC分析器

        Args:
            ic_type: IC类型
                    - 'pearson': Pearson相关系数
                    - 'rank': Spearman秩相关系数（默认）
            preprocess: 是否预处理因子值
            outlier_method: 去极值方法
        """
        self.ic_type = ic_type
        self.preprocess = preprocess
        self.outlier_method = outlier_method

        self.calendar = get_calendar()

    def _compute_single_ic(
        self,
        factor_values: pd.Series,
        future_returns: pd.Series,
    ) -> Optional[float]:
        """
        计算单个时间点的IC

        Args:
            factor_values: 因子值Series（截面）
            future_returns: 未来收益率Series（截面）

        Returns:
            IC值，如果无法计算则返回None
        """
        # 对齐数据
        aligned = pd.DataFrame({"factor": factor_values, "return": future_returns}).dropna()

        if len(aligned) < 3:  # 至少需要3个样本
            return None

        # 计算相关系数
        if self.ic_type == "pearson":
            ic, _ = stats.pearsonr(aligned["factor"], aligned["return"])
        elif self.ic_type == "rank":
            ic, _ = stats.spearmanr(aligned["factor"], aligned["return"])
        else:
            raise ValueError(f"未知的IC类型: {self.ic_type}")

        return ic

    def compute_daily_ic(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        period: int = 5,
    ) -> pd.Series:
        """
        计算单日IC序列

        Args:
            factor_data: 因子值DataFrame（宽表格式）
                        index: trade_date
                        columns: ts_code
                        values: factor_value
            price_data: 价格数据DataFrame（宽表格式）
                       index: trade_date
                       columns: ts_code
                       values: close_price
            period: 未来收益率周期（交易日数），默认5

        Returns:
            IC序列Series，index为日期
        """
        # 预处理因子值
        if self.preprocess:
            factor_data = preprocess_factor(
                factor_data,
                outlier_method=self.outlier_method,
                standardize=True,
            )

        ic_series = []

        # 对每个日期计算IC
        for i, date in enumerate(factor_data.index):
            # 计算未来收益率需要的交易日
            future_dates = self._get_future_trading_dates(date, period)

            if future_dates is None or len(future_dates) < period:
                # 没有足够的未来数据
                continue

            future_date = future_dates[-1]

            # 计算未来收益率
            if date not in price_data.index or future_date not in price_data.index:
                continue

            start_price = price_data.loc[date]
            end_price = price_data.loc[future_date]

            # 计算收益率
            future_returns = (end_price - start_price) / start_price

            # 获取因子值
            factor_values = factor_data.loc[date]

            # 计算IC
            ic = self._compute_single_ic(factor_values, future_returns)

            if ic is not None:
                ic_series.append({"date": date, "ic": ic})

        if not ic_series:
            return pd.Series(dtype=float)

        # 转换为Series
        result = pd.DataFrame(ic_series).set_index("date")["ic"]

        return result

    def _get_future_trading_dates(
        self,
        start_date: pd.Timestamp,
        n_days: int,
    ) -> Optional[List[pd.Timestamp]]:
        """
        获取未来N个交易日

        Args:
            start_date: 开始日期
            n_days: 交易日数量

        Returns:
            交易日列表，如果无法获取则返回None
        """
        try:
            # 获取交易日历
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = (start_date + pd.Timedelta(days=n_days * 2)).strftime("%Y-%m-%d")

            trading_days = self.calendar.get_trading_days(start_str, end_str)

            # 找到start_date之后的所有交易日
            future_days = [d for d in trading_days if d > start_date]

            if len(future_days) < n_days:
                return None

            return future_days[:n_days]

        except Exception as e:
            warnings.warn(f"获取交易日失败: {e}")
            return None

    def compute_rolling_ic(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        period: int = 5,
        roll_period: Optional[int] = None,
    ) -> pd.Series:
        """
        计算滚动IC序列

        Args:
            factor_data: 因子值DataFrame
            price_data: 价格数据DataFrame
            period: 未来收益率周期
            roll_period: 滚动周期（天数），None表示每个交易日都计算

        Returns:
            滚动IC序列
        """
        # 先计算每日IC
        daily_ic = self.compute_daily_ic(factor_data, price_data, period)

        if daily_ic.empty:
            return pd.Series(dtype=float)

        # 按滚动周期采样
        if roll_period is not None:
            # 每roll_period天计算一次
            sampled_ic = daily_ic.iloc[::roll_period]
        else:
            sampled_ic = daily_ic

        return sampled_ic

    def compute_ic_statistics(
        self,
        ic_series: pd.Series,
    ) -> Dict[str, float]:
        """
        计算IC统计指标

        Args:
            ic_series: IC序列

        Returns:
            统计指标字典
                - mean: IC均值
                - std: IC标准差
                - ir: 信息比率（IC均值/IC标准差）
                - t_stat: t统计量
                - p_value: p值
                - positive_ratio: 正IC占比
                - abs_mean: 绝对值均值
        """
        if ic_series.empty or len(ic_series) < 2:
            return {
                "mean": np.nan,
                "std": np.nan,
                "ir": np.nan,
                "t_stat": np.nan,
                "p_value": np.nan,
                "positive_ratio": np.nan,
                "abs_mean": np.nan,
            }

        # 基本统计
        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        ic_len = len(ic_series)

        # IR（信息比率）
        ir = ic_mean / ic_std if ic_std != 0 else np.nan

        # t统计量和p值
        # H0: IC均值 = 0
        # t = mean / (std / sqrt(n))
        t_stat = ic_mean / (ic_std / np.sqrt(ic_len)) if ic_std != 0 else np.nan
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=ic_len - 1)) if not np.isnan(t_stat) else np.nan

        # 正IC占比
        positive_ratio = (ic_series > 0).sum() / ic_len

        # 绝对值均值
        abs_mean = ic_series.abs().mean()

        return {
            "mean": ic_mean,
            "std": ic_std,
            "ir": ir,
            "t_stat": t_stat,
            "p_value": p_value,
            "positive_ratio": positive_ratio,
            "abs_mean": abs_mean,
            "count": ic_len,
        }

    def analyze(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        periods: List[int] = [5, 20],
    ) -> Dict[int, Dict[str, Union[pd.Series, Dict[str, float]]]]:
        """
        完整的IC分析

        Args:
            factor_data: 因子值DataFrame
            price_data: 价格数据DataFrame
            periods: 要分析的收益率周期列表

        Returns:
            分析结果字典
                {
                    period: {
                        'daily_ic': IC序列,
                        'rolling_ic': 滚动IC序列,
                        'statistics': IC统计指标
                    }
                }
        """
        results = {}

        for period in periods:
            # 计算每日IC
            daily_ic = self.compute_daily_ic(factor_data, price_data, period)

            # 计算滚动IC（每周/每月采样）
            if period == 5:
                roll_period = 5  # 每周
            elif period == 20:
                roll_period = 20  # 每月
            else:
                roll_period = None

            rolling_ic = self.compute_rolling_ic(
                factor_data,
                price_data,
                period,
                roll_period=roll_period,
            )

            # 计算统计指标
            statistics = self.compute_ic_statistics(daily_ic)

            results[period] = {
                "daily_ic": daily_ic,
                "rolling_ic": rolling_ic,
                "statistics": statistics,
            }

        return results

    def get_monthly_ic(
        self,
        ic_series: pd.Series,
    ) -> pd.DataFrame:
        """
        计算月度IC统计

        Args:
            ic_series: IC序列

        Returns:
            月度IC统计DataFrame
                index: 月份
                columns: mean, std, t_stat, ir
        """
        if ic_series.empty:
            return pd.DataFrame()

        # 按月分组
        monthly = ic_series.to_frame("ic")
        monthly["year_month"] = monthly.index.strftime("%Y-%m")

        # 计算月度统计
        monthly_stats = monthly.groupby("year_month")["ic"].agg(
            [
                ("mean", "mean"),
                ("std", "std"),
                ("count", "count"),
            ]
        )

        # 计算IR和t统计量
        monthly_stats["ir"] = monthly_stats["mean"] / monthly_stats["std"]
        monthly_stats["t_stat"] = (
            monthly_stats["mean"] / (monthly_stats["std"] / np.sqrt(monthly_stats["count"]))
        )

        return monthly_stats


# 便捷函数
def compute_ic(
    factor_data: pd.DataFrame,
    price_data: pd.DataFrame,
    period: int = 5,
    ic_type: str = "rank",
) -> pd.Series:
    """
    快捷计算IC序列

    Args:
        factor_data: 因子值DataFrame
        price_data: 价格数据DataFrame
        period: 收益率周期
        ic_type: IC类型

    Returns:
        IC序列
    """
    analyzer = ICAnalyzer(ic_type=ic_type)
    return analyzer.compute_daily_ic(factor_data, price_data, period)


def compute_ic_statistics(
    ic_series: pd.Series,
) -> Dict[str, float]:
    """
    快捷计算IC统计指标

    Args:
        ic_series: IC序列

    Returns:
        统计指标字典
    """
    analyzer = ICAnalyzer()
    return analyzer.compute_ic_statistics(ic_series)
