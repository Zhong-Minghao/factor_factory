"""
分层回测模块
对因子进行分层分组，回测各层收益表现
"""
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
import warnings

from .preprocessing import preprocess_factor
from utils.calendar import get_calendar


class LayerBacktest:
    """
    分层回测器

    将股票按因子值分层，回测各层收益表现

    功能：
    - 分层：等权分组（分位数法）
    - 调仓：月度/周度
    - 收益：计算各层收益率
    - 换手：计算换手率（权重差法）
    - 绩效：Sharpe、MDD等指标
    """

    def __init__(
        self,
        n_layers: int = 5,
        rebalance_freq: str = "monthly",
        preprocess: bool = True,
        outlier_method: str = "mad",
    ):
        """
        初始化分层回测器

        Args:
            n_layers: 分层数量，默认5
            rebalance_freq: 调仓频率
                           - 'monthly': 月度（默认）
                           - 'weekly': 周度
            preprocess: 是否预处理因子值
            outlier_method: 去极值方法
        """
        self.n_layers = n_layers
        self.rebalance_freq = rebalance_freq
        self.preprocess = preprocess
        self.outlier_method = outlier_method

        self.calendar = get_calendar()

    def _get_rebalance_dates(
        self,
        start_date: str,
        end_date: str,
    ) -> List[pd.Timestamp]:
        """
        获取调仓日期列表

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            调仓日期列表
        """
        # 获取交易日历
        trading_days = self.calendar.get_trading_days(start_date, end_date)

        # 确保交易日历已更新
        if len(trading_days) == 0:
            self.calendar.update_trading_days(start_date, end_date)
            trading_days = self.calendar.get_trading_days(start_date, end_date)

        if self.rebalance_freq == "monthly":
            # 月度调仓：每月最后一个交易日
            rebalance_dates = []
            for i, date in enumerate(trading_days):
                # 检查是否是月末
                if i == len(trading_days) - 1:
                    rebalance_dates.append(pd.Timestamp(date))
                else:
                    next_date = trading_days[i + 1]
                    # 如果下个月不同，则当前是月末
                    if date.month != next_date.month:
                        rebalance_dates.append(pd.Timestamp(date))

        elif self.rebalance_freq == "weekly":
            # 周度调仓：每周最后一个交易日（周五）
            rebalance_dates = []
            for i, date in enumerate(trading_days):
                # 周五（weekday=4）
                if date.weekday() == 4:
                    rebalance_dates.append(pd.Timestamp(date))

                # 或者最后一个交易日
                if i == len(trading_days) - 1:
                    if date not in rebalance_dates:
                        rebalance_dates.append(pd.Timestamp(date))
                else:
                    next_date = trading_days[i + 1]
                    # 如果下周不同，则当前是周末
                    if date.strftime("%Y-%W") != next_date.strftime("%Y-%W"):
                        if date not in rebalance_dates:
                            rebalance_dates.append(pd.Timestamp(date))

        else:
            raise ValueError(f"未知的调仓频率: {self.rebalance_freq}")

        return rebalance_dates

    def _assign_layers(
        self,
        factor_values: pd.Series,
    ) -> pd.Series:
        """
        分层：将股票按因子值分配到不同层

        Args:
            factor_values: 因子值Series（截面）

        Returns:
            分层结果Series，index为股票代码，values为层级（0到n_layers-1）
        """
        # 去除NaN
        valid_values = factor_values.dropna()

        if len(valid_values) == 0:
            return pd.Series(dtype=int)

        # 计算分位数
        quantiles = np.linspace(0, 1, self.n_layers + 1)

        # 分层
        layers = pd.Series(0, index=valid_values.index)

        for i in range(self.n_layers):
            lower = valid_values.quantile(quantiles[i])
            upper = valid_values.quantile(quantiles[i + 1])

            # 处理边界情况
            if i == self.n_layers - 1:
                # 最后一层包含上界值
                mask = (valid_values >= lower) & (valid_values <= upper)
            else:
                # 其他层不包含上界值
                mask = (valid_values >= lower) & (valid_values < upper)

            layers[mask] = i

        return layers

    def _compute_layer_returns(
        self,
        layer_stocks: Dict[int, List[str]],
        current_prices: pd.Series,
        next_prices: pd.Series,
    ) -> Dict[int, float]:
        """
        计算各层收益率

        Args:
            layer_stocks: 各层的股票列表字典
                         {layer_id: [stock_codes]}
            current_prices: 当前价格Series
            next_prices: 下期价格Series

        Returns:
            各层收益率字典
        """
        layer_returns = {}

        for layer_id, stocks in layer_stocks.items():
            if not stocks:
                layer_returns[layer_id] = 0.0
                continue

            # 计算等权收益率
            returns = []
            for stock in stocks:
                if stock in current_prices.index and stock in next_prices.index:
                    if current_prices[stock] != 0:
                        ret = (next_prices[stock] - current_prices[stock]) / current_prices[stock]
                        returns.append(ret)

            if returns:
                layer_returns[layer_id] = np.mean(returns)
            else:
                layer_returns[layer_id] = 0.0

        return layer_returns

    def _compute_turnover(
        self,
        current_weights: Dict[int, Dict[str, float]],
        previous_weights: Dict[int, Dict[str, float]],
    ) -> Dict[int, float]:
        """
        计算换手率（权重差法）

        Args:
            current_weights: 当前期权重 {layer_id: {stock_code: weight}}
            previous_weights: 上期权重 {layer_id: {stock_code: weight}}

        Returns:
            各层换手率字典

        Note:
            公式：turnover = Σ |weight_new - weight_old| / 2
        """
        turnover = {}

        for layer_id in current_weights.keys():
            current = current_weights[layer_id]
            previous = previous_weights.get(layer_id, {})

            # 计算权重变化
            all_stocks = set(current.keys()) | set(previous.keys())

            weight_diff = 0.0
            for stock in all_stocks:
                w_new = current.get(stock, 0.0)
                w_old = previous.get(stock, 0.0)
                weight_diff += abs(w_new - w_old)

            turnover[layer_id] = weight_diff / 2

        return turnover

    def run_backtest(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Union[pd.DataFrame, Dict]]:
        """
        运行分层回测

        Args:
            factor_data: 因子值DataFrame（宽表格式）
            price_data: 价格数据DataFrame（宽表格式）
            start_date: 回测开始日期
            end_date: 回测结束日期

        Returns:
            回测结果字典
                {
                    'layer_returns': 各层收益率序列,
                    'long_short_return': 多空收益序列,
                    'turnover': 换手率序列,
                    'rebalance_dates': 调仓日期列表,
                    'statistics': 各层统计指标,
                }
        """
        # 预处理因子值
        if self.preprocess:
            factor_data = preprocess_factor(
                factor_data,
                outlier_method=self.outlier_method,
                standardize=True,
            )

        # 确定日期范围
        if start_date is None:
            start_date = factor_data.index.min().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = factor_data.index.max().strftime("%Y-%m-%d")

        # 获取调仓日期
        rebalance_dates = self._get_rebalance_dates(start_date, end_date)

        if len(rebalance_dates) < 2:
            raise ValueError(f"调仓日期不足: 只找到{len(rebalance_dates)}个，日期范围: {start_date} 到 {end_date}")

        # 初始化结果
        layer_returns_list = []
        long_short_returns = []
        turnover_list = []

        previous_weights = {}

        # 逐期回测
        for i in range(len(rebalance_dates) - 1):
            current_date = rebalance_dates[i]
            next_date = rebalance_dates[i + 1]

            # 检查数据是否存在
            if current_date not in factor_data.index or next_date not in factor_data.index:
                continue

            if current_date not in price_data.index or next_date not in price_data.index:
                continue

            # 获取因子值和价格
            factor_values = factor_data.loc[current_date]
            current_prices = price_data.loc[current_date]
            next_prices = price_data.loc[next_date]

            # 分层
            layers = self._assign_layers(factor_values)

            # 构建各层股票列表
            layer_stocks = {}
            current_weights = {}

            for layer_id in range(self.n_layers):
                stocks = layers[layers == layer_id].index.tolist()
                layer_stocks[layer_id] = stocks

                # 等权权重
                n_stocks = len(stocks)
                if n_stocks > 0:
                    weight = 1.0 / n_stocks
                    current_weights[layer_id] = {stock: weight for stock in stocks}
                else:
                    current_weights[layer_id] = {}

            # 计算各层收益率
            layer_ret = self._compute_layer_returns(
                layer_stocks,
                current_prices,
                next_prices,
            )

            layer_returns_list.append(layer_ret)

            # 计算多空收益（最高层 - 最低层）
            long_return = layer_ret[self.n_layers - 1]
            short_return = layer_ret[0]
            long_short_returns.append(long_return - short_return)

            # 计算换手率
            if previous_weights:
                turnover = self._compute_turnover(current_weights, previous_weights)
                turnover_list.append(turnover)

            previous_weights = current_weights

        # 转换为DataFrame
        layer_returns_df = pd.DataFrame(
            layer_returns_list,
            index=rebalance_dates[1 : len(layer_returns_list) + 1],
        )

        long_short_series = pd.Series(
            long_short_returns,
            index=rebalance_dates[1 : len(long_short_returns) + 1],
        )

        turnover_df = pd.DataFrame(turnover_list, index=rebalance_dates[1 : len(turnover_list) + 1])

        # 计算统计指标
        statistics = self._compute_statistics(layer_returns_df, long_short_series)

        return {
            "layer_returns": layer_returns_df,
            "long_short_return": long_short_series,
            "turnover": turnover_df,
            "rebalance_dates": rebalance_dates,
            "statistics": statistics,
        }

    def _compute_statistics(
        self,
        layer_returns: pd.DataFrame,
        long_short_return: pd.Series,
    ) -> Dict[str, Dict]:
        """
        计算统计指标

        Args:
            layer_returns: 各层收益率DataFrame
            long_short_return: 多空收益Series

        Returns:
            统计指标字典
        """
        statistics = {}

        # 各层统计
        for layer_id in range(self.n_layers):
            if layer_id not in layer_returns.columns:
                continue

            returns = layer_returns[layer_id].dropna()

            if len(returns) == 0:
                statistics[f"layer_{layer_id}"] = {
                    "total_return": np.nan,
                    "annual_return": np.nan,
                    "sharpe": np.nan,
                    "max_drawdown": np.nan,
                }
                continue

            # 累计收益
            total_return = (1 + returns).prod() - 1

            # 年化收益（假设252个交易日）
            n_periods = len(returns)
            if self.rebalance_freq == "monthly":
                periods_per_year = 12
            elif self.rebalance_freq == "weekly":
                periods_per_year = 52
            else:
                periods_per_year = 252

            annual_return = (1 + total_return) ** (periods_per_year / n_periods) - 1

            # 夏普比率
            sharpe = returns.mean() / returns.std() * np.sqrt(periods_per_year) if returns.std() != 0 else np.nan

            # 最大回撤
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            statistics[f"layer_{layer_id}"] = {
                "total_return": total_return,
                "annual_return": annual_return,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
            }

        # 多空收益统计
        ls_returns = long_short_return.dropna()
        if len(ls_returns) > 0:
            ls_total = (1 + ls_returns).prod() - 1
            ls_annual = (1 + ls_total) ** (periods_per_year / len(ls_returns)) - 1
            ls_sharpe = (
                ls_returns.mean() / ls_returns.std() * np.sqrt(periods_per_year)
                if ls_returns.std() != 0
                else np.nan
            )

            ls_cumulative = (1 + ls_returns).cumprod()
            ls_running_max = ls_cumulative.expanding().max()
            ls_drawdown = (ls_cumulative - ls_running_max) / ls_running_max
            ls_mdd = ls_drawdown.min()

            statistics["long_short"] = {
                "total_return": ls_total,
                "annual_return": ls_annual,
                "sharpe": ls_sharpe,
                "max_drawdown": ls_mdd,
            }

        return statistics


# 便捷函数
def run_layer_backtest(
    factor_data: pd.DataFrame,
    price_data: pd.DataFrame,
    n_layers: int = 5,
    rebalance_freq: str = "monthly",
) -> Dict:
    """
    快捷运行分层回测

    Args:
        factor_data: 因子值DataFrame
        price_data: 价格数据DataFrame
        n_layers: 分层数
        rebalance_freq: 调仓频率

    Returns:
        回测结果字典
    """
    backtest = LayerBacktest(n_layers=n_layers, rebalance_freq=rebalance_freq)
    return backtest.run_backtest(factor_data, price_data)
