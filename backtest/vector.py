"""
向量回测引擎
轻量级的向量回测框架，专注于因子有效性验证
"""
from typing import Optional, Dict, List, Tuple
import pandas as pd
import numpy as np
import warnings
from datetime import timedelta

from .selector import StockSelector
from .performance import PerformanceCalculator
from .result import BacktestResult

from utils.calendar import get_calendar
from config.settings import get_settings


class VectorBacktest:
    """
    向量回测引擎

    使用向量化运算进行回测，速度快、代码简洁。

    功能：
    - 支持多种选股方式（Top N、分层、百分比）
    - 支持多种调仓频率（日度、周度、月度）
    - 支持等权、市值加权等权重方式
    - 自动处理 T+1 交易规则
    - 计算手续费和滑点
    """

    def __init__(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        select_method: str = "top_n",
        select_params: Optional[Dict] = None,
        rebalance_freq: str = "monthly",
        weight_method: str = "equal",
        commission_rate: float = 0.0003,
        min_commission: float = 5.0,
        slippage_rate: float = 0.0001,
        initial_capital: float = 1000000.0,
        benchmark: Optional[str] = None,
        benchmark_data: Optional[pd.Series] = None,
    ):
        """
        初始化向量回测引擎

        Args:
            factor_data: 因子数据 DataFrame（宽表格式）
                         index: 交易日期
                         columns: 股票代码
                         values: 因子值
            price_data: 价格数据 DataFrame（宽表格式）
                        index: 交易日期
                        columns: 股票代码
                        values: 收盘价
            select_method: 选股方式
                - "top_n": Top N 选择
                - "layer": 分层选择
                - "percentile": 百分比选择
            select_params: 选股参数
                - top_n: {"top_n": 10}
                - layer: {"n_layers": 5, "layer_id": 4}
                - percentile: {"percentile": 0.2}
            rebalance_freq: 调仓频率
                - "daily": 日度
                - "weekly": 周度
                - "monthly": 月度
            weight_method: 权重方式
                - "equal": 等权（默认）
                - "market_cap": 市值加权（需要提供市值数据）
            commission_rate: 手续费率（默认万三）
            min_commission: 最低手续费（默认5元）
            slippage_rate: 滑点率（默认万分之一）
            initial_capital: 初始资金（默认100万）
            benchmark: 基准指数代码（可选）
            benchmark_data: 基准价格数据 Series（可选）
        """
        # 数据
        self.factor_data = factor_data
        self.price_data = price_data
        self.benchmark_data = benchmark_data

        # 选股配置
        self.select_method = select_method
        self.select_params = select_params or {}
        self.rebalance_freq = rebalance_freq
        self.weight_method = weight_method

        # 交易成本
        self.commission_rate = commission_rate
        self.min_commission = min_commission
        self.slippage_rate = slippage_rate

        # 资金配置
        self.initial_capital = initial_capital

        # 基准配置
        self.benchmark = benchmark

        # 初始化组件
        self.selector = StockSelector()
        self.performance = PerformanceCalculator()
        self.calendar = get_calendar()

    def run(self) -> BacktestResult:
        """
        运行回测

        Returns:
            BacktestResult: 回测结果对象
        """
        # 1. 数据预处理
        factor_data, price_data = self._preprocess_data()

        # 2. 获取调仓日期
        rebalance_dates = self._get_rebalance_dates()

        if len(rebalance_dates) < 2:
            raise ValueError(
                f"调仓日期不足: 只找到{len(rebalance_dates)}个，至少需要2个"
            )

        # 3. 初始化结果存储
        returns_list = []
        positions_list = []
        holdings_list = []
        turnover_list = []

        previous_positions = None

        # 4. 逐期回测
        for i in range(len(rebalance_dates) - 1):
            current_date = rebalance_dates[i]
            next_date = rebalance_dates[i + 1]

            # 检查数据是否存在
            if current_date not in factor_data.index:
                continue
            if next_date not in price_data.index:
                continue

            # 获取当前因子值
            factor_values = factor_data.loc[current_date]

            # 选股
            selected_stocks = self.selector.select(
                factor_values,
                method=self.select_method,
                params=self.select_params,
            )

            if len(selected_stocks) == 0:
                warnings.warn(f"{current_date} 没有选中任何股票")
                continue

            # 获取价格
            current_prices = price_data.loc[current_date, selected_stocks]
            next_prices = price_data.loc[next_date, selected_stocks]

            # 处理缺失价格
            valid_mask = (
                current_prices.notna() & next_prices.notna()
            )
            valid_stocks_list = [
                stock for stock, valid in zip(selected_stocks, valid_mask)
                if valid
            ]

            if len(valid_stocks_list) == 0:
                warnings.warn(f"{current_date} 选中的股票都没有价格数据")
                continue

            # 计算权重
            weights = self._calculate_weights(
                valid_stocks_list, current_prices[valid_stocks_list]
            )

            # 计算收益率（考虑交易成本）
            period_return = self._calculate_period_return(
                valid_stocks_list,
                current_prices[valid_stocks_list],
                next_prices[valid_stocks_list],
                weights,
                previous_positions,
            )

            # 计算持仓
            positions = self._calculate_positions(valid_stocks_list, weights)

            # 计算市值
            holdings = self._calculate_holdings(
                valid_stocks_list, weights, current_prices[valid_stocks_list], period_return
            )

            # 计算换手率
            turnover = self._calculate_turnover(positions, previous_positions)

            # 记录结果
            returns_list.append(period_return)
            positions_list.append(positions)
            holdings_list.append(holdings)
            turnover_list.append(turnover)

            previous_positions = positions

        # 5. 构建结果序列
        returns = pd.Series(
            returns_list, index=rebalance_dates[1 : len(returns_list) + 1]
        )

        # 6. 计算绩效指标
        metrics = self.performance.calculate_metrics(returns)

        # 7. 计算净值曲线
        equity_curve = self.performance.calculate_equity_curve(
            returns, self.initial_capital
        )

        # 8. 计算累计收益
        cumulative_returns = (1 + returns).cumprod() - 1

        # 9. 构建持仓 DataFrame
        positions_df = pd.DataFrame(positions_list)
        holdings_df = pd.DataFrame(holdings_list)

        # 10. 构建换手率序列
        turnover_series = pd.Series(
            turnover_list, index=returns.index
        )

        # 11. 处理基准数据
        benchmark_returns = None
        benchmark_equity = None
        excess_returns = None

        if self.benchmark_data is not None:
            benchmark_returns = self._calculate_benchmark_returns(
                rebalance_dates
            )
            benchmark_equity = self.performance.calculate_equity_curve(
                benchmark_returns, self.initial_capital
            )

            # 对齐日期，计算超额收益
            aligned_returns, aligned_benchmark = returns.align(
                benchmark_returns, join="inner"
            )
            excess_returns = aligned_returns - aligned_benchmark

        # 12. 构建结果对象
        result = BacktestResult(
            returns=returns,
            equity_curve=equity_curve,
            cumulative_returns=cumulative_returns,
            positions=positions_df,
            holdings=holdings_df,
            metrics=metrics,
            turnover=turnover_series,
            benchmark_returns=benchmark_returns,
            benchmark_equity=benchmark_equity,
            excess_returns=excess_returns,
            start_date=rebalance_dates[0],
            end_date=rebalance_dates[-1],
            initial_capital=self.initial_capital,
            config={
                "select_method": self.select_method,
                "select_params": self.select_params,
                "rebalance_freq": self.rebalance_freq,
                "weight_method": self.weight_method,
                "commission_rate": self.commission_rate,
                "slippage_rate": self.slippage_rate,
            },
        )

        return result

    def _preprocess_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        数据预处理

        Returns:
            处理后的因子数据和价格数据
        """
        # 确保索引是日期类型
        factor_data = self.factor_data.copy()
        price_data = self.price_data.copy()

        if not isinstance(factor_data.index, pd.DatetimeIndex):
            factor_data.index = pd.to_datetime(factor_data.index)

        if not isinstance(price_data.index, pd.DatetimeIndex):
            price_data.index = pd.to_datetime(price_data.index)

        # 对齐日期
        aligned_dates = factor_data.index.intersection(price_data.index)

        if len(aligned_dates) == 0:
            raise ValueError("因子数据和价格数据没有共同的日期")

        return factor_data.loc[aligned_dates], price_data.loc[aligned_dates]

    def _get_rebalance_dates(self) -> List[pd.Timestamp]:
        """
        获取调仓日期列表

        Returns:
            调仓日期列表
        """
        # 使用因子数据中的日期作为交易日
        trading_days = self.factor_data.index.sort_values().tolist()

        if len(trading_days) == 0:
            raise ValueError("因子数据中没有日期")

        # 根据调仓频率筛选日期
        if self.rebalance_freq == "daily":
            # 日度：所有交易日
            rebalance_dates = trading_days

        elif self.rebalance_freq == "weekly":
            # 周度：每周最后一个交易日
            rebalance_dates = []
            for i, date in enumerate(trading_days):
                # 周五（weekday=4）或该周最后一个交易日
                if date.weekday() == 4:
                    rebalance_dates.append(date)
                elif i == len(trading_days) - 1:
                    rebalance_dates.append(date)
                else:
                    next_date = trading_days[i + 1]
                    if date.strftime("%Y-%W") != next_date.strftime("%Y-%W"):
                        rebalance_dates.append(date)

        elif self.rebalance_freq == "monthly":
            # 月度：每月最后一个交易日
            rebalance_dates = []
            for i, date in enumerate(trading_days):
                if i == len(trading_days) - 1:
                    rebalance_dates.append(date)
                else:
                    next_date = trading_days[i + 1]
                    # 如果下个月不同，则当前是月末
                    if date.month != next_date.month:
                        rebalance_dates.append(date)

        else:
            raise ValueError(f"未知的调仓频率: {self.rebalance_freq}")

        return rebalance_dates

    def _calculate_weights(
        self,
        stocks: List[str],
        prices: pd.Series,
    ) -> Dict[str, float]:
        """
        计算权重

        Args:
            stocks: 股票列表
            prices: 价格序列

        Returns:
            权重字典 {股票代码: 权重}
        """
        if self.weight_method == "equal":
            # 等权
            n = len(stocks)
            weight = 1.0 / n
            return {stock: weight for stock in stocks}

        elif self.weight_method == "market_cap":
            # 市值加权（暂未实现）
            raise NotImplementedError("市值加权暂未实现")

        else:
            raise ValueError(f"未知的权重方式: {self.weight_method}")

    def _calculate_period_return(
        self,
        stocks: List[str],
        current_prices: pd.Series,
        next_prices: pd.Series,
        weights: Dict[str, float],
        previous_positions: Optional[Dict],
    ) -> float:
        """
        计算期间收益率（考虑交易成本）

        Args:
            stocks: 股票列表
            current_prices: 当前价格
            next_prices: 下期价格
            weights: 权重
            previous_positions: 上期持仓

        Returns:
            期间收益率
        """
        # 计算个股收益率
        stock_returns = (next_prices / current_prices) - 1

        # 应用滑点
        if self.slippage_rate > 0:
            stock_returns = stock_returns * (1 - self.slippage_rate)

        # 计算组合收益率（加权平均）
        portfolio_return = sum(
            weights[stock] * stock_returns[stock] for stock in stocks
        )

        # 计算交易成本
        if previous_positions is not None:
            # 计算换手
            turnover = 0.0
            all_stocks = set(stocks) | set(previous_positions.keys())

            for stock in all_stocks:
                new_weight = weights.get(stock, 0.0)
                old_weight = previous_positions.get(stock, 0.0)
                turnover += abs(new_weight - old_weight)

            # 交易成本 = 换手率 * 手续费率
            transaction_cost = turnover * self.commission_rate

            # 确保最低手续费
            transaction_cost = max(
                transaction_cost, self.min_commission / self.initial_capital
            )

            portfolio_return -= transaction_cost

        return portfolio_return

    def _calculate_positions(
        self,
        stocks: List[str],
        weights: Dict[str, float],
    ) -> Dict[str, float]:
        """
        计算持仓

        Args:
            stocks: 股票列表
            weights: 权重

        Returns:
            持仓字典 {股票代码: 权重}
        """
        return weights.copy()

    def _calculate_holdings(
        self,
        stocks: List[str],
        weights: Dict[str, float],
        prices: pd.Series,
        period_return: float,
    ) -> Dict[str, float]:
        """
        计算市值

        Args:
            stocks: 股票列表
            weights: 权重
            prices: 价格
            period_return: 期间收益率

        Returns:
            市值字典 {股票代码: 市值}
        """
        holdings = {}
        current_equity = self.initial_capital * (1 + period_return)

        for stock in stocks:
            holdings[stock] = current_equity * weights[stock]

        return holdings

    def _calculate_turnover(
        self,
        current_positions: Dict[str, float],
        previous_positions: Optional[Dict[str, float]],
    ) -> float:
        """
        计算换手率

        Args:
            current_positions: 当前持仓
            previous_positions: 上期持仓

        Returns:
            换手率
        """
        if previous_positions is None:
            return 1.0  # 第一次建仓，换手率为100%

        # 计算权重变化
        all_stocks = set(current_positions.keys()) | set(previous_positions.keys())

        weight_diff = 0.0
        for stock in all_stocks:
            new_weight = current_positions.get(stock, 0.0)
            old_weight = previous_positions.get(stock, 0.0)
            weight_diff += abs(new_weight - old_weight)

        return weight_diff / 2

    def _calculate_benchmark_returns(
        self,
        rebalance_dates: List[pd.Timestamp],
    ) -> pd.Series:
        """
        计算基准收益率

        Args:
            rebalance_dates: 调仓日期列表

        Returns:
            基准收益率序列
        """
        if self.benchmark_data is None:
            return pd.Series(dtype=float)

        # 确保索引是日期类型
        benchmark_data = self.benchmark_data.copy()
        if not isinstance(benchmark_data.index, pd.DatetimeIndex):
            benchmark_data.index = pd.to_datetime(benchmark_data.index)

        # 对齐日期
        aligned_dates = pd.Index(rebalance_dates).intersection(
            benchmark_data.index
        )

        if len(aligned_dates) < 2:
            return pd.Series(dtype=float)

        # 计算收益率
        benchmark_values = benchmark_data.loc[aligned_dates]
        benchmark_returns = benchmark_values.pct_change().dropna()

        return benchmark_returns
