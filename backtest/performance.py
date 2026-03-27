"""
绩效计算器模块
计算回测的各种绩效指标
"""
from typing import Optional, Dict
import pandas as pd
import numpy as np
import warnings


class PerformanceCalculator:
    """
    绩效计算器

    计算策略的各种绩效指标：
    - 收益指标：年化收益率、累计收益率
    - 风险指标：波动率、最大回撤
    - 风险调整收益：夏普比率、索提诺比率
    - 交易统计：胜率、盈亏比
    """

    @staticmethod
    def calculate_metrics(
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        periods_per_year: int = 252,
        risk_free_rate: float = 0.03,
    ) -> pd.DataFrame:
        """
        计算绩效指标，返回 DataFrame

        Args:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列（可选）
            periods_per_year: 每年交易周期数（默认252天）
            risk_free_rate: 无风险收益率（默认3%）

        Returns:
            绩效指标 DataFrame，每行一个指标
        """
        returns = returns.dropna()

        if len(returns) == 0:
            warnings.warn("收益率序列为空，返回空指标")
            return pd.DataFrame()

        # 计算基础指标
        total_return = PerformanceCalculator.calculate_total_return(returns)
        annual_return = PerformanceCalculator.calculate_annual_return(
            returns, periods_per_year
        )
        volatility = PerformanceCalculator.calculate_volatility(
            returns, periods_per_year
        )
        max_drawdown = PerformanceCalculator.calculate_max_drawdown(returns)
        sharpe = PerformanceCalculator.calculate_sharpe_ratio(
            returns, risk_free_rate, periods_per_year
        )
        sortino = PerformanceCalculator.calculate_sortino_ratio(
            returns, risk_free_rate, periods_per_year
        )
        win_rate = PerformanceCalculator.calculate_win_rate(returns)
        calmar = PerformanceCalculator.calculate_calmar_ratio(
            returns, periods_per_year
        )

        # 构建指标字典
        metrics = {
            "累计收益率": [total_return],
            "年化收益率": [annual_return],
            "波动率": [volatility],
            "最大回撤": [max_drawdown],
            "夏普比率": [sharpe],
            "索提诺比率": [sortino],
            "卡尔玛比率": [calmar],
            "胜率": [win_rate],
        }

        # 如果有基准，计算相对指标
        if benchmark_returns is not None:
            benchmark_returns = benchmark_returns.dropna()

            # 对齐日期
            aligned_returns, aligned_benchmark = returns.align(
                benchmark_returns, join="inner"
            )

            if len(aligned_returns) > 0:
                excess_return = PerformanceCalculator.calculate_excess_return(
                    aligned_returns, aligned_benchmark, periods_per_year
                )
                information_ratio = (
                    PerformanceCalculator.calculate_information_ratio(
                        aligned_returns, aligned_benchmark
                    )
                )
                tracking_error = PerformanceCalculator.calculate_tracking_error(
                    aligned_returns, aligned_benchmark, periods_per_year
                )

                metrics.update(
                    {
                        "超额收益": [excess_return],
                        "信息比率": [information_ratio],
                        "跟踪误差": [tracking_error],
                    }
                )

        return pd.DataFrame(metrics, index=[0])

    @staticmethod
    def calculate_total_return(returns: pd.Series) -> float:
        """
        计算累计收益率

        Args:
            returns: 收益率序列

        Returns:
            累计收益率
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan
        return (1 + returns).prod() - 1

    @staticmethod
    def calculate_annual_return(
        returns: pd.Series,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算年化收益率

        Args:
            returns: 收益率序列
            periods_per_year: 每年交易周期数

        Returns:
            年化收益率
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan

        total_return = PerformanceCalculator.calculate_total_return(returns)
        n_periods = len(returns)

        return (1 + total_return) ** (periods_per_year / n_periods) - 1

    @staticmethod
    def calculate_volatility(
        returns: pd.Series,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算年化波动率

        Args:
            returns: 收益率序列
            periods_per_year: 每年交易周期数

        Returns:
            年化波动率
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan
        return returns.std() * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_max_drawdown(returns: pd.Series) -> float:
        """
        计算最大回撤

        Args:
            returns: 收益率序列

        Returns:
            最大回撤（负数）
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan

        # 计算累计净值
        cumulative = (1 + returns).cumprod()

        # 计算历史最高点
        running_max = cumulative.expanding().max()

        # 计算回撤
        drawdown = (cumulative - running_max) / running_max

        return drawdown.min()

    @staticmethod
    def calculate_sharpe_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.03,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险收益率（年化）
            periods_per_year: 每年交易周期数

        Returns:
            夏普比率
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan

        # 计算超额收益
        excess_returns = returns - risk_free_rate / periods_per_year

        # 计算夏普比率
        if excess_returns.std() == 0:
            return np.nan

        return (
            excess_returns.mean() * periods_per_year
            / (excess_returns.std() * np.sqrt(periods_per_year))
        )

    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series,
        risk_free_rate: float = 0.03,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算索提诺比率（只考虑下行风险）

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险收益率（年化）
            periods_per_year: 每年交易周期数

        Returns:
            索提诺比率
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan

        # 计算超额收益
        excess_returns = returns - risk_free_rate / periods_per_year

        # 计算下行风险（只考虑负收益）
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return np.nan

        downside_std = downside_returns.std() * np.sqrt(periods_per_year)

        if downside_std == 0:
            return np.nan

        return (
            excess_returns.mean() * periods_per_year / downside_std
        )

    @staticmethod
    def calculate_calmar_ratio(
        returns: pd.Series,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算卡尔玛比率（年化收益 / 最大回撤的绝对值）

        Args:
            returns: 收益率序列
            periods_per_year: 每年交易周期数

        Returns:
            卡尔玛比率
        """
        annual_return = PerformanceCalculator.calculate_annual_return(
            returns, periods_per_year
        )
        max_drawdown = PerformanceCalculator.calculate_max_drawdown(returns)

        if pd.isna(annual_return) or pd.isna(max_drawdown):
            return np.nan

        if max_drawdown == 0:
            return np.nan

        return annual_return / abs(max_drawdown)

    @staticmethod
    def calculate_win_rate(returns: pd.Series) -> float:
        """
        计算胜率（正收益占比）

        Args:
            returns: 收益率序列

        Returns:
            胜率（0-1）
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return np.nan
        return (returns > 0).mean()

    @staticmethod
    def calculate_excess_return(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算超额收益（策略收益 - 基准收益）

        Args:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列
            periods_per_year: 每年交易周期数

        Returns:
            年化超额收益
        """
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )

        if len(aligned_returns) == 0:
            return np.nan

        strategy_annual = PerformanceCalculator.calculate_annual_return(
            aligned_returns, periods_per_year
        )
        benchmark_annual = PerformanceCalculator.calculate_annual_return(
            aligned_benchmark, periods_per_year
        )

        return strategy_annual - benchmark_annual

    @staticmethod
    def calculate_information_ratio(
        returns: pd.Series,
    benchmark_returns: pd.Series,
    ) -> float:
        """
        计算信息比率（超额收益的均值 / 超额收益的标准差）

        Args:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列

        Returns:
            信息比率
        """
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )

        if len(aligned_returns) == 0:
            return np.nan

        excess_returns = aligned_returns - aligned_benchmark

        if excess_returns.std() == 0:
            return np.nan

        return excess_returns.mean() / excess_returns.std()

    @staticmethod
    def calculate_tracking_error(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        periods_per_year: int = 252,
    ) -> float:
        """
        计算跟踪误差（超额收益的标准差）

        Args:
            returns: 策略收益率序列
            benchmark_returns: 基准收益率序列
            periods_per_year: 每年交易周期数

        Returns:
            年化跟踪误差
        """
        aligned_returns, aligned_benchmark = returns.align(
            benchmark_returns, join="inner"
        )

        if len(aligned_returns) == 0:
            return np.nan

        excess_returns = aligned_returns - aligned_benchmark

        return excess_returns.std() * np.sqrt(periods_per_year)

    @staticmethod
    def calculate_equity_curve(returns: pd.Series, initial_capital: float = 1000000) -> pd.Series:
        """
        计算净值曲线

        Args:
            returns: 收益率序列
            initial_capital: 初始资金

        Returns:
            净值序列
        """
        returns = returns.dropna()
        if len(returns) == 0:
            return pd.Series(dtype=float)

        cumulative_returns = (1 + returns).cumprod()
        equity_curve = cumulative_returns * initial_capital

        return equity_curve
