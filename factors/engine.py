"""
因子计算引擎模块
负责因子的高效计算和管理
"""
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import warnings

from .base import Factor, FactorValidator
from .registry import factor_registry
from config.settings import get_settings
from data.store import DataStore


class FactorEngine:
    """
    因子计算引擎

    提供高效的因子计算功能：
    - 自动解析因子依赖
    - 并行计算优化
    - 结果缓存
    - 批量计算
    """

    def __init__(self, storage: Optional[DataStore] = None):
        """
        初始化因子引擎

        Args:
            storage: 数据存储实例
        """
        self.settings = get_settings()
        self.storage = storage or DataStore()
        self.validator = FactorValidator()

        # 计算配置
        self.parallel = self.settings.factor.parallel
        self.n_workers = self.settings.factor.n_workers

    def compute_factor(
        self,
        factor_name: str,
        data: pd.DataFrame,
        **params
    ) -> pd.Series:
        """
        计算单个因子

        Args:
            factor_name: 因子名称
            data: 输入数据
            **params: 因子参数

        Returns:
            因子值Series
        """
        # 获取因子实例
        factor = factor_registry.get(factor_name, **params)

        if factor is None:
            raise ValueError(f"因子不存在: {factor_name}")

        # 计算因子值
        try:
            factor_values = factor.compute(data)

            # 验证因子值
            validation_result = self.validator.validate_factor_values(factor_values)

            if not validation_result["valid"]:
                errors = ", ".join(validation_result["errors"])
                raise ValueError(f"因子值验证失败: {errors}")

            # 输出警告
            for warning in validation_result["warnings"]:
                warnings.warn(f"因子 {factor_name} 警告: {warning}")

            return factor_values

        except Exception as e:
            raise RuntimeError(f"计算因子 {factor_name} 失败: {str(e)}")

    def compute_factors_batch(
        self,
        factor_names: List[str],
        data: pd.DataFrame,
        parallel: Optional[bool] = None,
    ) -> Dict[str, pd.Series]:
        """
        批量计算多个因子

        Args:
            factor_names: 因子名称列表
            data: 输入数据
            parallel: 是否并行计算

        Returns:
            字典，key为因子名称，value为因子值Series
        """
        parallel = parallel if parallel is not None else self.parallel

        result = {}

        if parallel and len(factor_names) > 1:
            # 并行计算
            result = self._compute_parallel(factor_names, data)
        else:
            # 串行计算
            for factor_name in factor_names:
                try:
                    factor_values = self.compute_factor(factor_name, data)
                    result[factor_name] = factor_values
                except Exception as e:
                    warnings.warn(f"计算因子 {factor_name} 失败: {str(e)}")
                    continue

        return result

    def _compute_parallel(
        self, factor_names: List[str], data: pd.DataFrame
    ) -> Dict[str, pd.Series]:
        """
        并行计算因子

        Args:
            factor_names: 因子名称列表
            data: 输入数据

        Returns:
            字典，key为因子名称，value为因子值Series
        """
        result = {}

        # 确定工作进程数
        n_workers = self.n_workers if self.n_workers > 0 else None

        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # 提交任务
            futures = {
                executor.submit(
                    self._compute_factor_worker,
                    factor_name,
                    data
                ): factor_name
                for factor_name in factor_names
            }

            # 收集结果
            for future in as_completed(futures):
                factor_name = futures[future]
                try:
                    factor_values = future.result()
                    result[factor_name] = factor_values
                except Exception as e:
                    warnings.warn(f"并行计算因子 {factor_name} 失败: {str(e)}")
                    continue

        return result

    @staticmethod
    def _compute_factor_worker(factor_name: str, data: pd.DataFrame) -> pd.Series:
        """
        工作进程函数（用于并行计算）

        Args:
            factor_name: 因子名称
            data: 输入数据

        Returns:
            因子值Series
        """
        # 重新导入因子模块（因为是在新进程中）
        from factors.registry import factor_registry

        # 获取因子实例
        factor = factor_registry.get(factor_name)

        if factor is None:
            raise ValueError(f"因子不存在: {factor_name}")

        # 计算因子值
        return factor.compute(data)

    def compute_factor_for_stocks(
        self,
        factor_name: str,
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **params
    ) -> pd.DataFrame:
        """
        为多只股票计算因子值

        Args:
            factor_name: 因子名称
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            **params: 因子参数

        Returns:
            DataFrame，index为日期，columns为股票代码
        """
        # 获取因子实例
        factor = factor_registry.get(factor_name, **params)

        if factor is None:
            raise ValueError(f"因子不存在: {factor_name}")

        result = {}

        for stock_code in stock_codes:
            try:
                # 加载股票数据
                data = self.storage.load_daily_data(
                    stock_code, start_date, end_date
                )

                if data.empty:
                    warnings.warn(f"股票 {stock_code} 数据为空")
                    continue

                # 计算因子值
                factor_values = factor.compute(data)

                # 存储结果
                result[stock_code] = factor_values

            except Exception as e:
                warnings.warn(f"为股票 {stock_code} 计算因子失败: {str(e)}")
                continue

        # 转换为DataFrame
        df = pd.DataFrame(result)

        return df

    def compute_cross_sectional(
        self,
        factor_name: str,
        date: str,
        stock_codes: List[str],
        lookback_days: int = 252,
        **params
    ) -> pd.Series:
        """
        计算截面因子值（某一时点所有股票的因子值）

        Args:
            factor_name: 因子名称
            date: 目标日期
            stock_codes: 股票代码列表
            lookback_days: 向前回溯天数（用于计算因子所需的历史数据）
            **params: 因子参数

        Returns:
            Series，index为股票代码，values为因子值
        """
        # 计算开始日期
        end_date = pd.to_datetime(date)
        start_date = end_date - pd.Timedelta(days=lookback_days)

        result = {}

        for stock_code in stock_codes:
            try:
                # 加载股票数据
                data = self.storage.load_daily_data(
                    stock_code,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=date,
                )

                if data.empty or data.iloc[-1]["trade_date"] != end_date:
                    continue

                # 计算因子值
                factor_values = self.compute_factor(factor_name, data, **params)

                # 获取最后一天的因子值
                last_value = factor_values.iloc[-1]

                result[stock_code] = last_value

            except Exception as e:
                warnings.warn(f"为股票 {stock_code} 计算截面因子失败: {str(e)}")
                continue

        # 转换为Series
        series = pd.Series(result)

        return series

    def save_factor_values(
        self,
        factor_name: str,
        factor_values: pd.DataFrame,
        date: Optional[str] = None,
    ):
        """
        保存因子值

        Args:
            factor_name: 因子名称
            factor_values: 因子值DataFrame
            date: 日期（可选）
        """
        # TODO: 实现因子值保存到数据库
        # 这个功能将在storage模块中实现
        pass

    def load_factor_values(
        self,
        factor_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        加载因子值

        Args:
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            因子值DataFrame
        """
        # TODO: 实现从数据库加载因子值
        # 这个功能将在storage模块中实现
        return pd.DataFrame()

    def get_dependency_order(self, factor_names: List[str]) -> List[str]:
        """
        获取因子计算顺序（考虑依赖关系）

        Args:
            factor_names: 因子名称列表

        Returns:
            排序后的因子名称列表
        """
        # TODO: 实现拓扑排序，考虑因子依赖关系
        # 简单版本直接返回原列表
        return factor_names

    def validate_factor_dependencies(self, factor_name: str) -> bool:
        """
        验证因子的依赖关系

        Args:
            factor_name: 因子名称

        Returns:
            是否所有依赖都存在
        """
        factor = factor_registry.get_class(factor_name)

        if factor is None:
            return False

        # 检查所有依赖是否存在
        for dep in factor.dependencies:
            if not factor_registry.exists(dep):
                return False

        return True
