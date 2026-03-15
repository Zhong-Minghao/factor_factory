"""
Tushare数据源接口
"""
import time
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime

from ..base import DataSourceBase, DataSourceError, DataSourceConnectionError
from config.settings import get_settings


class TushareSource(DataSourceBase):
    """
    Tushare数据源

    需要配置Tushare Token
    获取Token: https://tushare.pro/register
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Tushare数据源

        Args:
            config: 配置字典，应包含token字段
        """
        super().__init__(config)

        # 获取token
        self.token = self.config.get("token") or get_settings().data.tushare_token

        if not self.token:
            raise ValueError(
                "Tushare Token未配置，请在.env文件中设置TUSHARE_TOKEN"
            )

        self.api = None
        self._last_request_time = 0
        self._min_interval = 0.1  # 请求间隔（秒），避免频率限制

    def connect(self) -> bool:
        """
        建立Tushare连接

        Returns:
            是否连接成功
        """
        try:
            import tushare as ts

            self.api = ts.pro_api(self.token)
            self._connected = True

            # 测试连接
            self.get_stock_list()

            return True

        except ImportError:
            raise ImportError("请安装tushare: pip install tushare")
        except Exception as e:
            raise DataSourceConnectionError(f"Tushare连接失败: {str(e)}")

    def disconnect(self):
        """断开连接"""
        self.api = None
        self._connected = False

    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        return self._connected and self.api is not None

    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        self._last_request_time = time.time()

    def _api_call(self, api_name: str, **kwargs) -> pd.DataFrame:
        """
        调用Tushare API

        Args:
            api_name: API名称
            **kwargs: API参数

        Returns:
            返回的数据DataFrame
        """
        if not self.is_connected():
            raise DataSourceError("未连接到Tushare，请先调用connect()")

        self._rate_limit()

        try:
            # 获取API方法
            api_method = getattr(self.api, api_name)

            # 调用API
            df = api_method(**kwargs)

            return df

        except Exception as e:
            raise DataSourceError(f"Tushare API调用失败 ({api_name}): {str(e)}")

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        Returns:
            股票列表 DataFrame
        """
        df = self._api_call("stock_basic", exchange="", list_status="L")

        # 标准化列名
        df = df.rename(
            columns={
                "ts_code": "ts_code",
                "name": "name",
                "industry": "industry",
                "list_date": "list_date",
            }
        )

        # 选择需要的列
        columns = ["ts_code", "name", "industry", "list_date"]
        df = df[columns]

        return df

    def get_daily_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取日线行情数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            日线行情 DataFrame
        """
        # 验证日期
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        # 调用API
        df = self._api_call(
            "daily",
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return df

        # 标准化列名
        df = df.rename(
            columns={
                "trade_date": "trade_date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount",
            }
        )

        # 选择需要的列
        columns = ["trade_date", "open", "high", "low", "close", "volume", "amount"]
        df = df[columns]

        # 标准化格式
        df = self.standardize_dataframe(df, date_column="trade_date")

        return df

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
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            字典，key为股票代码，value为对应的DataFrame
        """
        result = {}

        for ts_code in ts_codes:
            try:
                df = self.get_daily_data(ts_code, start_date, end_date)
                if not df.empty:
                    result[ts_code] = df
            except Exception as e:
                print(f"获取 {ts_code} 数据失败: {str(e)}")
                continue

        return result

    def get_index_data(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取指数行情数据

        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            指数行情 DataFrame
        """
        # 验证日期
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        # 调用API
        df = self._api_call(
            "index_daily",
            ts_code=index_code,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return df

        # 标准化列名
        df = df.rename(
            columns={
                "trade_date": "trade_date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "volume",
                "amount": "amount",
            }
        )

        # 选择需要的列
        columns = ["trade_date", "open", "high", "low", "close", "volume", "amount"]
        df = df[columns]

        # 标准化格式
        df = self.standardize_dataframe(df, date_column="trade_date")

        return df

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
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            财务数据 DataFrame
        """
        # 验证日期
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        # 调用API获取每日基本面数据
        df = self._api_call(
            "daily_basic",
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return df

        # 标准化列名
        df = df.rename(
            columns={
                "trade_date": "trade_date",
                "pe": "pe",
                "pe_ttm": "pe_ttm",
                "pb": "pb",
                "ps": "ps",
                "ps_ttm": "ps_ttm",
                "total_mv": "total_mv",
                "circ_mv": "circ_mv",
            }
        )

        # 选择需要的列
        columns = [
            "trade_date",
            "pe",
            "pe_ttm",
            "pb",
            "ps",
            "ps_ttm",
            "total_mv",
            "circ_mv",
        ]
        df = df[columns]

        # 标准化格式
        df = self.standardize_dataframe(df, date_column="trade_date")

        return df

    def get_index_weight(self, index_code: str, trade_date: str) -> pd.DataFrame:
        """
        获取指数成分股权重

        Args:
            index_code: 指数代码
            trade_date: 交易日期

        Returns:
            权重数据 DataFrame，包含列：
            - index_code: 指数代码
            - con_code: 成分股代码
            - weight: 权重
            - trade_date: 交易日期
        """
        df = self._api_call("index_weight", index_code=index_code, trade_date=trade_date)
        return df

    def get_trade_calendar(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            交易日历 DataFrame，包含列：
            - exchange: 交易所
            - cal_date: 日历日期
            - is_open: 是否开市
        """
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        df = self._api_call("trade_cal", start_date=start_date, end_date=end_date)
        return df
