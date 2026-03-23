"""
智能数据加载器
支持自动fallback、内存监控、批量加载等功能
"""
from typing import List, Dict, Optional, Union, Callable, Any
import pandas as pd
import numpy as np
from functools import lru_cache
from collections import OrderedDict
import warnings

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    warnings.warn("psutil未安装，内存监控功能将不可用。安装: pip install psutil")

from data.store import DataStore


class LRUCache:
    """
    LRU缓存实现
    """

    def __init__(self, capacity: int = 100):
        """
        初始化LRU缓存

        Args:
            capacity: 缓存容量
        """
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[pd.DataFrame]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在则返回None
        """
        if key not in self.cache:
            return None

        # 移动到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: pd.DataFrame):
        """
        放入缓存

        Args:
            key: 缓存键
            value: 数据
        """
        if key in self.cache:
            self.cache.move_to_end(key)

        self.cache[key] = value

        # 超过容量，删除最久未使用的
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def __len__(self) -> int:
        return len(self.cache)


class SmartDataLoader:
    """
    智能数据加载器

    策略：
    1. < 1000只股票：全量加载到内存
    2. 1000-3000只股票：按年份分批加载
    3. > 3000只股票：按需加载 + LRU缓存
    """

    # 内存阈值
    MEMORY_THRESHOLD_HIGH = 80  # 80%内存使用率
    MEMORY_THRESHOLD_MEDIUM = 60  # 60%内存使用率

    # 股票数量阈值
    STOCK_THRESHOLD_SMALL = 1000
    STOCK_THRESHOLD_MEDIUM = 3000

    def __init__(
        self,
        data_store: Optional[DataStore] = None,
        cache_size: int = 100,
        enable_cache: bool = True,
    ):
        """
        初始化智能数据加载器

        Args:
            data_store: 数据存储实例
            cache_size: 缓存大小（股票数量）
            enable_cache: 是否启用缓存
        """
        self.data_store = data_store or DataStore()
        self.enable_cache = enable_cache

        # LRU缓存
        self.cache = LRUCache(cache_size) if enable_cache else None

        # 内存监控
        self.psutil_available = PSUTIL_AVAILABLE

        # 加载策略（自动选择）
        self.loading_strategy = "auto"  # auto, all, batch, on_demand

    def _get_memory_usage(self) -> float:
        """
        获取当前内存使用率

        Returns:
            内存使用率（百分比）
        """
        if not self.psutil_available:
            return 0.0

        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0

    def _estimate_data_size(
        self, stock_list: List[str], start_date: str, end_date: str
    ) -> int:
        """
        估算数据大小（MB）

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            估算的数据大小（MB）
        """
        # 估算：每只股票每天约100字节（6列float64 + 开销）
        try:
            num_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1
            num_stocks = len(stock_list)

            # 估算字节数
            estimated_bytes = num_stocks * num_days * 100

            # 转换为MB
            return estimated_bytes / (1024 * 1024)
        except Exception:
            return 0

    def _determine_loading_strategy(
        self, stock_list: List[str], start_date: str, end_date: str
    ) -> str:
        """
        确定加载策略

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            加载策略：all, batch, on_demand
        """
        num_stocks = len(stock_list)
        memory_usage = self._get_memory_usage()
        estimated_size = self._estimate_data_size(stock_list, start_date, end_date)

        # 如果内存不足，使用保守策略
        if memory_usage > self.MEMORY_THRESHOLD_HIGH:
            return "on_demand"

        # 根据股票数量选择策略
        if num_stocks < self.STOCK_THRESHOLD_SMALL:
            return "all"
        elif num_stocks < self.STOCK_THRESHOLD_MEDIUM:
            return "batch"
        else:
            return "on_demand"

    def load_data(
        self,
        stock_list: List[str],
        start_date: str,
        end_date: str,
        strategy: Optional[str] = None,
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        加载股票数据（自动选择最优策略）

        Args:
            stock_list: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            strategy: 加载策略，None表示自动选择
                     - all: 全量加载
                     - batch: 分批加载
                     - on_demand: 按需加载

        Returns:
            如果策略是all，返回合并的DataFrame
            如果策略是batch或on_demand，返回字典 {stock_code: DataFrame}
        """
        if not stock_list:
            return {} if strategy in ["batch", "on_demand", None] else pd.DataFrame()

        # 确定策略
        if strategy is None:
            strategy = self.loading_strategy
            if strategy == "auto":
                strategy = self._determine_loading_strategy(stock_list, start_date, end_date)

        # 根据策略加载数据
        if strategy == "all":
            return self._load_all(stock_list, start_date, end_date)
        elif strategy == "batch":
            return self._load_batch_by_year(stock_list, start_date, end_date)
        elif strategy == "on_demand":
            return self._load_on_demand(stock_list, start_date, end_date)
        else:
            raise ValueError(f"未知策略: {strategy}")

    def _load_all(
        self, stock_list: List[str], start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        全量加载（适用于少量股票）

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            合并的DataFrame，columns为多级索引 (stock_code, field)
        """
        data_dict = {}

        for stock_code in stock_list:
            # 检查缓存
            cache_key = f"{stock_code}_{start_date}_{end_date}"
            if self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    data_dict[stock_code] = cached_data
                    continue

            # 加载数据
            df = self.data_store.load_daily_data(stock_code, start_date, end_date)

            if not df.empty:
                data_dict[stock_code] = df

                # 缓存
                if self.cache:
                    self.cache.put(cache_key, df)

        # 合并数据
        if not data_dict:
            return pd.DataFrame()

        # 使用多级索引合并
        result = pd.concat(data_dict, names=["ts_code", "index"], axis=1)

        return result

    def _load_batch_by_year(
        self, stock_list: List[str], start_date: str, end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        按年份分批加载（适用于中等数量股票）

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            字典 {stock_code: DataFrame}
        """
        result = {}

        # 按年份分组
        start_year = pd.to_datetime(start_date).year
        end_year = pd.to_datetime(end_date).year

        for stock_code in stock_list:
            stock_data = []

            for year in range(start_year, end_year + 1):
                year_start = f"{year}-01-01"
                year_end = f"{year}-12-31"

                # 调整日期范围
                if year == start_year:
                    year_start = start_date
                if year == end_year:
                    year_end = end_date

                # 加载数据
                df = self.data_store.load_daily_data(stock_code, year_start, year_end)

                if not df.empty:
                    stock_data.append(df)

            # 合并该股票的数据
            if stock_data:
                result[stock_code] = pd.concat(stock_data).sort_index()

        return result

    def _load_on_demand(
        self, stock_list: List[str], start_date: str, end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        按需加载（适用于大量股票）

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            字典 {stock_code: DataFrame}
        """
        result = {}

        for stock_code in stock_list:
            # 检查缓存
            cache_key = f"{stock_code}_{start_date}_{end_date}"
            if self.cache:
                cached_data = self.cache.get(cache_key)
                if cached_data is not None:
                    result[stock_code] = cached_data
                    continue

            # 加载数据
            df = self.data_store.load_daily_data(stock_code, start_date, end_date)

            if not df.empty:
                result[stock_code] = df

                # 缓存
                if self.cache:
                    self.cache.put(cache_key, df)

        return result

    def load_data_for_factors(
        self,
        stock_list: List[str],
        start_date: str,
        end_date: str,
        columns: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        为因子计算加载数据（只加载需要的列）

        Args:
            stock_list: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            columns: 需要的列（如：["open", "high", "low", "close", "volume"]）

        Returns:
            字典 {stock_code: DataFrame}
        """
        # 加载完整数据
        data_dict = self.load_data(stock_list, start_date, end_date)

        # 如果是DataFrame，转换为字典
        if isinstance(data_dict, pd.DataFrame):
            # 多级索引DataFrame转换为字典
            result = {}
            for stock_code in stock_list:
                if stock_code in data_dict.columns.get_level_values(0):
                    stock_data = data_dict[stock_code]

                    # 筛选列
                    if columns:
                        stock_data = stock_data[columns]

                    result[stock_code] = stock_data

            return result
        else:
            # 筛选列
            if columns:
                result = {}
                for stock_code, df in data_dict.items():
                    result[stock_code] = df[columns]
                return result
            else:
                return data_dict

    def clear_cache(self):
        """清空缓存"""
        if self.cache:
            self.cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息

        Returns:
            缓存信息字典
        """
        if not self.cache:
            return {"enabled": False, "size": 0, "capacity": 0}

        return {
            "enabled": True,
            "size": len(self.cache),
            "capacity": self.cache.capacity,
            "usage": f"{len(self.cache)}/{self.cache.capacity}",
        }

    def __repr__(self) -> str:
        """字符串表示"""
        cache_info = self.get_cache_info()
        memory_usage = self._get_memory_usage()

        return (
            f"SmartDataLoader("
            f"cache={cache_info['usage'] if cache_info['enabled'] else 'disabled'}, "
            f"memory={memory_usage:.1f}%)"
        )


# 便捷函数
def create_data_loader(
    data_store: Optional[DataStore] = None,
    cache_size: int = 100,
    enable_cache: bool = True,
) -> SmartDataLoader:
    """
    创建智能数据加载器

    Args:
        data_store: 数据存储实例
        cache_size: 缓存大小
        enable_cache: 是否启用缓存

    Returns:
        SmartDataLoader实例
    """
    return SmartDataLoader(
        data_store=data_store,
        cache_size=cache_size,
        enable_cache=enable_cache,
    )
