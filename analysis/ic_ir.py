"""
IC/IR分析模块
计算因子的IC（Information Coefficient）和IR（Information Ratio）
"""
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy import stats
import warnings
from numba import jit

from .preprocessing import preprocess_factor
from utils.calendar import get_calendar


@jit(nopython=True)
def _pearson_correlation_numba(arr1: np.ndarray, arr2: np.ndarray) -> float:
    """
    Numba加速的Pearson相关系数计算

    Args:
        arr1: 数组1
        arr2: 数组2

    Returns:
        相关系数，如果无法计算返回nan
    """
    n = len(arr1)
    if n < 3:
        return np.nan

    # 计算均值
    mean1 = 0.0
    mean2 = 0.0
    for i in range(n):
        mean1 += arr1[i]
        mean2 += arr2[i]
    mean1 /= n
    mean2 /= n

    # 计算协方差和标准差
    cov = 0.0
    var1 = 0.0
    var2 = 0.0

    for i in range(n):
        diff1 = arr1[i] - mean1
        diff2 = arr2[i] - mean2
        cov += diff1 * diff2
        var1 += diff1 * diff1
        var2 += diff2 * diff2

    if var1 == 0.0 or var2 == 0.0:
        return np.nan

    return cov / np.sqrt(var1 * var2)


@jit(nopython=True)
def _spearman_correlation_numba(arr1: np.ndarray, arr2: np.ndarray) -> float:
    """
    Numba加速的Spearman秩相关系数计算

    Args:
        arr1: 数组1
        arr2: 数组2

    Returns:
        秩相关系数，如果无法计算返回nan
    """
    n = len(arr1)
    if n < 3:
        return np.nan

    # 计算秩（简单排序方法）
    rank1 = np.empty(n, dtype=np.float64)
    rank2 = np.empty(n, dtype=np.float64)

    # 对arr1排序并计算秩
    for i in range(n):
        rank1[i] = 0.0
        rank2[i] = 0.0
        for j in range(n):
            if arr1[j] < arr1[i]:
                rank1[i] += 1.0
            if arr2[j] < arr2[i]:
                rank2[i] += 1.0

    # 使用Pearson相关系数计算秩相关
    return _pearson_correlation_numba(rank1, rank2)


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
        计算单个时间点的IC（使用numba加速）

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

        # 转换为numpy数组以使用numba加速
        factor_arr = aligned["factor"].values.astype(np.float64)
        return_arr = aligned["return"].values.astype(np.float64)

        # 使用numba加速的相关系数计算
        if self.ic_type == "pearson":
            ic = _pearson_correlation_numba(factor_arr, return_arr)
        elif self.ic_type == "rank":
            ic = _spearman_correlation_numba(factor_arr, return_arr)
        else:
            raise ValueError(f"未知的IC类型: {self.ic_type}")

        return float(ic) if not np.isnan(ic) else None

    def _validate_input_format(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
    ) -> None:
        """
        验证输入数据格式，提供清晰的错误提示

        Args:
            factor_data: 因子数据
            price_data: 价格数据

        Raises:
            ValueError: 数据格式不符合要求，附带详细的修复建议
        """
        errors = []

        # 验证 factor_data
        if not isinstance(factor_data, pd.DataFrame):
            errors.append("factor_data 必须是 DataFrame 类型")
        elif factor_data.empty:
            errors.append("factor_data 不能为空")
        else:
            # 检查是否为长表格式（包含 OHLC 列）
            if 'close' in factor_data.columns and 'open' in factor_data.columns:
                errors.append(
                    "factor_data 是长表格式（包含 open/high/low/close 列），"
                    "需要宽表格式（index=日期, columns=股票代码）\n"
                    "参考 examples/test_factor_analysis.py 中的正确格式"
                )

        # 验证 price_data
        if not isinstance(price_data, pd.DataFrame):
            errors.append("price_data 必须是 DataFrame 类型")
        elif price_data.empty:
            errors.append("price_data 不能为空")
        else:
            # 检查是否为长表格式
            if 'close' in price_data.columns and 'open' in price_data.columns:
                errors.append(
                    "price_data 是长表格式（包含 open/high/low/close 列），"
                    "需要宽表格式（index=日期, columns=股票代码）\n\n"
                    "解决方案：\n"
                    "1. 使用 WindSource.get_daily_data_batch() 获取多只股票数据\n"
                    "2. 转换为宽表格式：\n"
                    "   ```python\n"
                    "   price_list = []\n"
                    "   for ts_code, df in price_dict.items():\n"
                    "       df['ts_code'] = ts_code\n"
                    "       price_list.append(df[['close', 'ts_code']])\n"
                    "   \n"
                    "   price_wide = pd.concat(price_list).pivot(\n"
                    "       index='trade_date',\n"
                    "       columns='ts_code',\n"
                    "       values='close'\n"
                    "   )\n"
                    "   ```\n"
                    "3. 参考 examples/test_numba_speedup.py:19-33"
                )
            elif price_data.shape[1] < 2:
                errors.append(
                    f"price_data 至少需要 2 列（多个股票），当前只有 {price_data.shape[1]} 列"
                )

        # 检查股票代码是否匹配
        if (isinstance(factor_data, pd.DataFrame) and
            isinstance(price_data, pd.DataFrame) and
            len(errors) == 0):  # 只在基本格式正确时检查

            factor_stocks = set(factor_data.columns)
            price_stocks = set(price_data.columns)
            common_stocks = factor_stocks.intersection(price_stocks)

            if len(common_stocks) < min(3, len(factor_stocks)):
                errors.append(
                    f"股票代码匹配不足：factor_data 有 {len(factor_stocks)} 只股票，"
                    f"price_data 有 {len(price_stocks)} 只股票，"
                    f"共同股票只有 {len(common_stocks)} 只\n"
                    f"factor_data 股票：{list(factor_stocks)[:5]}...\n"
                    f"price_data 股票：{list(price_stocks)[:5]}..."
                )

        # 如果有错误，抛出异常
        if errors:
            error_msg = "数据格式验证失败：\n\n" + "\n\n".join(f"❌ {e}" for e in errors)
            error_msg += "\n\n💡 提示：运行 python check_data_format.py 查看详细的数据格式诊断"
            raise ValueError(error_msg)

    def _compute_future_returns(
        self,
        price_data: pd.DataFrame,
        period: int
    ) -> pd.DataFrame:
        """
        计算未来收益率（简化版，不依赖交易日历）

        使用 pandas 的 shift 操作，性能更好且更可靠

        Args:
            price_data: 价格数据（宽表格式）
            period: 未来周期

        Returns:
            未来收益率 DataFrame（index=trade_date, columns=ts_code）

        Note:
            使用 shift(-period) 计算未来价格，最后 period 行会被丢弃
            这比使用交易日历查询更简单、更快速
        """
        # 直接使用 shift 计算未来价格
        future_prices = price_data.shift(-period)

        # 计算收益率: (future_price - current_price) / current_price
        future_returns = (future_prices - price_data) / price_data

        # 移除最后 period 行（没有未来收益率的数据）
        future_returns = future_returns.iloc[:-period]

        return future_returns

    def compute_daily_ic(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        period: int = 5,
    ) -> pd.Series:
        """
        计算单日IC序列（改进版）

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

        Raises:
            ValueError: 数据格式不符合要求（附带详细的修复建议）

        Example:
            >>> from analysis.ic_ir import ICAnalyzer
            >>> analyzer = ICAnalyzer(ic_type="rank")
            >>> ic_series = analyzer.compute_daily_ic(factor_data, price_data, period=5)
            >>> print(f"IC 均值: {ic_series.mean():.4f}")
        """
        # 步骤 1: 数据格式验证（新增）
        self._validate_input_format(factor_data, price_data)

        # 步骤 2: 数据对齐
        common_dates = factor_data.index.intersection(price_data.index)
        if len(common_dates) == 0:
            raise ValueError(
                f"因子数据和价格数据没有共同的日期\n"
                f"factor_data 日期范围: {factor_data.index.min()} ~ {factor_data.index.max()}\n"
                f"price_data 日期范围: {price_data.index.min()} ~ {price_data.index.max()}"
            )

        factor_data = factor_data.loc[common_dates]
        price_data = price_data.loc[common_dates]

        # 步骤 3: 预处理因子值
        if self.preprocess:
            factor_data = preprocess_factor(
                factor_data,
                outlier_method=self.outlier_method,
                standardize=True,
            )

        # 步骤 4: 计算未来收益率（简化版）
        future_returns = self._compute_future_returns(price_data, period)

        # 步骤 5: 对齐日期
        valid_dates = factor_data.index.intersection(future_returns.index)

        if len(valid_dates) == 0:
            warnings.warn(
                f"没有有效的日期可以计算 IC\n"
                f"factor_data 日期范围: {factor_data.index.min()} ~ {factor_data.index.max()}\n"
                f"future_returns 日期范围: {future_returns.index.min()} ~ {future_returns.index.max()}\n"
                f"提示：增加 price_data 的日期范围或减小 period 参数"
            )
            return pd.Series(dtype=float)

        factor_subset = factor_data.loc[valid_dates]
        returns_subset = future_returns.loc[valid_dates]

        # 步骤 6: Stack为长格式，准备批量计算
        factor_long = factor_subset.stack().rename("factor")
        returns_long = returns_subset.stack().rename("return")

        # 步骤 7: 合并
        combined = pd.DataFrame({"factor": factor_long, "return": returns_long})

        # 步骤 8: 按日期分组，使用numba加速计算IC
        def compute_ic_group(group):
            factor_arr = group["factor"].values.astype(np.float64)
            return_arr = group["return"].values.astype(np.float64)

            if self.ic_type == "pearson":
                ic = _pearson_correlation_numba(factor_arr, return_arr)
            else:  # rank
                ic = _spearman_correlation_numba(factor_arr, return_arr)

            return ic if not np.isnan(ic) else np.nan

        # 批量计算IC
        ic_series = combined.groupby(level=0).apply(compute_ic_group)

        # 过滤nan值
        ic_series = ic_series.dropna()

        return ic_series

    def _get_future_trading_dates(
        self,
        start_date: Union[pd.Timestamp, str],
        n_days: int,
    ) -> Optional[List[pd.Timestamp]]:
        """
        获取未来N个交易日

        Args:
            start_date: 开始日期（支持Timestamp或字符串）
            n_days: 交易日数量

        Returns:
            交易日列表，如果无法获取则返回None
        """
        try:
            # 确保start_date是Timestamp类型
            if not isinstance(start_date, pd.Timestamp):
                start_date = pd.Timestamp(start_date)

            # 获取交易日历
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = (start_date + pd.Timedelta(days=n_days * 2)).strftime("%Y-%m-%d")

            trading_days = self.calendar.get_trading_days(start_str, end_str)

            # 找到start_date之后的所有交易日
            # 将start_date转换为date对象进行比较
            start_date_obj = start_date.date()
            future_days = [d for d in trading_days if d > start_date_obj]

            if len(future_days) < n_days:
                return None

            # 返回Timestamp对象列表以保持一致性
            return [pd.Timestamp(d) for d in future_days[:n_days]]

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
