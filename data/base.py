"""
数据源基类
定义统一的数据源接口
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime


class DataSourceBase(ABC):
    """
    数据源基类

    所有数据源实现都需要继承这个基类，并实现其抽象方法
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据源

        Args:
            config: 数据源配置
        """
        self.config = config or {}
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        建立数据源连接

        Returns:
            是否连接成功
        """
        pass

    @abstractmethod
    def disconnect(self):
        """断开数据源连接"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        pass

    @abstractmethod
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        Returns:
            股票列表 DataFrame，包含列：
            - ts_code: 股票代码（如：000001.SZ）
            - name: 股票名称
            - industry: 行业
            - list_date: 上市日期
        """
        pass

    @abstractmethod
    def get_daily_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取日线行情数据

        Args:
            ts_code: 股票代码（如：000001.SZ）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            日线行情 DataFrame，包含列：
            - trade_date: 交易日期
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
        """
        pass

    @abstractmethod
    def get_daily_data_batch(
        self,
        ts_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票的日线行情数据

        Args:
            ts_codes: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            字典，key为股票代码，value为对应的DataFrame
        """
        pass

    @abstractmethod
    def get_index_data(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取指数行情数据

        Args:
            index_code: 指数代码（如：000300.SH）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            指数行情 DataFrame，包含列：
            - trade_date: 交易日期
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量
            - amount: 成交额
        """
        pass

    @abstractmethod
    def get_financial_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取财务数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            财务数据 DataFrame，包含列：
            - ann_date: 公告日期
            - end_date: 报告期
            - pe: 市盈率
            - pb: 市净率
            - ps: 市销率
            - total_mv: 总市值
            - circ_mv: 流通市值
        """
        pass

    def validate_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        验证并标准化日期格式

        Args:
            date_str: 日期字符串

        Returns:
            标准化后的日期字符串，如果输入为None则返回None
        """
        if date_str is None:
            return None

        try:
            # 尝试解析日期
            dt = pd.to_datetime(date_str)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            raise ValueError(f"无效的日期格式: {date_str}")

    def standardize_dataframe(
        self, df: pd.DataFrame, date_column: str = "trade_date"
    ) -> pd.DataFrame:
        """
        标准化DataFrame格式

        Args:
            df: 原始DataFrame
            date_column: 日期列名

        Returns:
            标准化后的DataFrame
        """
        if df.empty:
            return df

        # 确保日期列是datetime类型
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column])

            # 按日期排序
            df = df.sort_values(date_column)

            # 去重（保留最后一条）
            df = df.drop_duplicates(subset=[date_column], keep="last")

        return df

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class DataSourceError(Exception):
    """数据源异常"""

    pass


class DataSourceConnectionError(DataSourceError):
    """数据源连接异常"""

    pass


class DataSourceNotFoundError(DataSourceError):
    """数据未找到异常"""

    pass


class DataSourceValidationError(DataSourceError):
    """数据验证异常"""

    pass
