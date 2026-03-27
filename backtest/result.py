"""
回测结果数据类
封装回测的所有结果
"""
from typing import Optional, Dict
from dataclasses import dataclass, field
import pandas as pd
import numpy as np


@dataclass
class BacktestResult:
    """
    回测结果数据类

    封装回测的所有结果，包括收益、持仓、绩效指标等
    """

    # 收益相关
    returns: pd.Series  # 收益率序列
    equity_curve: pd.Series  # 净值曲线
    cumulative_returns: pd.Series  # 累计收益率序列

    # 持仓相关
    positions: pd.DataFrame  # 持仓明细（每只股票的持仓情况）
    holdings: pd.DataFrame  # 组合市值（每只股票的市值）

    # 绩效指标
    metrics: pd.DataFrame  # 绩效指标 DataFrame

    # 交易相关
    turnover: pd.Series  # 换手率序列

    # 对比基准（可选）
    benchmark_returns: Optional[pd.Series] = None  # 基准收益率序列
    benchmark_equity: Optional[pd.Series] = None  # 基准净值曲线
    excess_returns: Optional[pd.Series] = None  # 超额收益序列

    # 元数据
    start_date: Optional[pd.Timestamp] = None  # 回测开始日期
    end_date: Optional[pd.Timestamp] = None  # 回测结束日期
    initial_capital: float = 1000000.0  # 初始资金
    final_capital: float = 0.0  # 最终资金

    # 配置信息（可选）
    config: Dict = field(default_factory=dict)  # 回测配置参数

    def __post_init__(self):
        """初始化后处理"""
        if self.final_capital == 0.0 and len(self.equity_curve) > 0:
            self.final_capital = self.equity_curve.iloc[-1]

        if self.start_date is None and len(self.returns) > 0:
            self.start_date = self.returns.index[0]

        if self.end_date is None and len(self.returns) > 0:
            self.end_date = self.returns.index[-1]

    def to_dataframe(self) -> Dict[str, pd.DataFrame]:
        """
        导出所有结果为 DataFrame 字典

        Returns:
            包含所有结果的 DataFrame 字典
        """
        result = {
            "returns": self.returns.to_frame("returns"),
            "equity_curve": self.equity_curve.to_frame("equity"),
            "cumulative_returns": self.cumulative_returns.to_frame("cumulative_returns"),
            "metrics": self.metrics,
            "positions": self.positions,
            "holdings": self.holdings,
            "turnover": self.turnover.to_frame("turnover"),
        }

        # 可选的基准数据
        if self.benchmark_returns is not None:
            result["benchmark_returns"] = self.benchmark_returns.to_frame(
                "benchmark_returns"
            )
        if self.benchmark_equity is not None:
            result["benchmark_equity"] = self.benchmark_equity.to_frame(
                "benchmark_equity"
            )
        if self.excess_returns is not None:
            result["excess_returns"] = self.excess_returns.to_frame("excess_returns")

        return result

    def summary(self) -> pd.Series:
        """
        获取回测摘要

        Returns:
            摘要信息 Series
        """
        summary_data = {
            "回测期间": f"{self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}",
            "初始资金": f"{self.initial_capital:,.0f}",
            "最终资金": f"{self.final_capital:,.0f}",
            "累计收益": f"{self.metrics['累计收益率'].iloc[0]:.2%}",
            "年化收益": f"{self.metrics['年化收益率'].iloc[0]:.2%}",
            "夏普比率": f"{self.metrics['夏普比率'].iloc[0]:.2f}",
            "最大回撤": f"{self.metrics['最大回撤'].iloc[0]:.2%}",
            "胜率": f"{self.metrics['胜率'].iloc[0]:.2%}",
        }

        # 如果有基准，添加相对指标
        if "超额收益" in self.metrics.columns:
            summary_data["超额收益"] = (
                f"{self.metrics['超额收益'].iloc[0]:.2%}"
            )
        if "信息比率" in self.metrics.columns:
            summary_data["信息比率"] = (
                f"{self.metrics['信息比率'].iloc[0]:.2f}"
            )

        return pd.Series(summary_data)

    def get_best_trade(self) -> Dict:
        """
        获取最佳交易

        Returns:
            最佳交易信息字典
        """
        if len(self.returns) == 0:
            return {}

        max_return = self.returns.max()
        max_date = self.returns.idxmax()

        return {"date": max_date, "return": max_return}

    def get_worst_trade(self) -> Dict:
        """
        获取最差交易

        Returns:
            最差交易信息字典
        """
        if len(self.returns) == 0:
            return {}

        min_return = self.returns.min()
        min_date = self.returns.idxmin()

        return {"date": min_date, "return": min_return}

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"BacktestResult("
            f"期间={self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}, "
            f"年化收益={self.metrics['年化收益率'].iloc[0]:.2%}, "
            f"夏普={self.metrics['夏普比率'].iloc[0]:.2f}, "
            f"最大回撤={self.metrics['最大回撤'].iloc[0]:.2%})"
        )
