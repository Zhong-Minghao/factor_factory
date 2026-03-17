"""
AKShare数据源接口
"""
import time
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta

from ..base import DataSourceBase, DataSourceError


class AKShareSource(DataSourceBase):
    """
    AKShare数据源

    免费的开源财经数据接口
    文档: https://akshare.akfamily.xyz
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化AKShare数据源

        Args:
            config: 配置字典
        """
        super().__init__(config)

        self._last_request_time = 0
        self._min_interval = 0.5  # 请求间隔（秒）

    def connect(self) -> bool:
        """
        建立连接（AKShare不需要认证）

        Returns:
            是否连接成功
        """
        try:
            import akshare as ak

            # 测试连接
            ak.stock_zh_a_spot_em()

            self._connected = True
            return True

        except ImportError:
            raise ImportError("请安装akshare: pip install akshare")
        except Exception as e:
            raise DataSourceError(f"AKShare连接失败: {str(e)}")

    def disconnect(self):
        """断开连接"""
        self._connected = False

    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        # 同时检查状态标志和API对象
        return self._connected and self.api is not None

    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        self._last_request_time = time.time()

    def _standardize_code(self, code: str) -> str:
        """
        标准化股票代码格式

        Args:
            code: 股票代码

        Returns:
            标准化后的代码
        """
        code = code.strip().upper()

        # AKShare使用的格式：sh600000, sz000001
        # 我们需要转换为标准格式：600000.SH, 000001.SZ
        if not "." in code:
            # 如果已经是AKShare格式，转换
            if code.startswith("sh"):
                return code[2:] + ".SH"
            elif code.startswith("sz"):
                return code[2:] + ".SZ"
            else:
                # 如果是纯数字，根据规则添加后缀
                if code.startswith("6") or code.startswith("5"):
                    return code + ".SH"
                else:
                    return code + ".SZ"

        return code

    def _convert_to_akshare_format(self, code: str) -> str:
        """
        转换为AKShare格式的股票代码

        Args:
            code: 标准格式的股票代码 (如：000001.SZ)

        Returns:
            AKShare格式的代码 (如：sz000001)
        """
        code = code.split(".")[0]

        if code.startswith("6") or code.startswith("5"):
            return "sh" + code
        else:
            return "sz" + code

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        Returns:
            股票列表 DataFrame
        """
        import akshare as ak

        self._rate_limit()

        try:
            # 获取A股列表
            df = ak.stock_zh_a_spot_em()

            # 标准化列名
            df = df.rename(
                columns={
                    "代码": "ts_code",
                    "名称": "name",
                    "行业": "industry",
                }
            )

            # 标准化代码
            df["ts_code"] = df["ts_code"].apply(self._standardize_code)

            # 添加上市日期（默认为空，需要另外获取）
            df["list_date"] = ""

            # 选择需要的列
            columns = ["ts_code", "name", "industry", "list_date"]
            df = df[columns]

            return df

        except Exception as e:
            raise DataSourceError(f"获取股票列表失败: {str(e)}")

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
        import akshare as ak

        self._rate_limit()

        # 转换代码格式
        ak_code = self._convert_to_akshare_format(ts_code)

        try:
            # 获取历史数据
            df = ak.stock_zh_a_hist(
                symbol=ak_code, period="daily", adjust="qfq"
            )

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "trade_date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                }
            )

            # 选择需要的列
            columns = ["trade_date", "open", "high", "low", "close", "volume", "amount"]
            df = df[columns]

            # 标准化格式
            df = self.standardize_dataframe(df, date_column="trade_date")

            # 筛选日期范围
            if start_date:
                df = df[df["trade_date"] >= start_date]
            if end_date:
                df = df[df["trade_date"] <= end_date]

            return df

        except Exception as e:
            raise DataSourceError(f"获取 {ts_code} 数据失败: {str(e)}")

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
        import akshare as ak

        self._rate_limit()

        # 映射指数代码
        index_mapping = {
            "000300.SH": "000300",  # 沪深300
            "000001.SH": "000001",  # 上证指数
            "399001.SZ": "399001",  # 深证成指
            "399006.SZ": "399006",  # 创业板指
        }

        ak_code = index_mapping.get(index_code, index_code.split(".")[0])

        try:
            # 获取指数历史数据
            df = ak.stock_zh_index_daily(symbol=f"sh{ak_code}")

            # 标准化列名
            df = df.rename(
                columns={
                    "date": "trade_date",
                    "open": "open",
                    "high": "high",
                    "low": "low",
                    "close": "close",
                    "volume": "volume",
                    "amount": "amount",
                }
            )

            # 选择需要的列
            columns = ["trade_date", "open", "high", "low", "close", "volume", "amount"]
            df = df[columns]

            # 标准化格式
            df = self.standardize_dataframe(df, date_column="trade_date")

            # 筛选日期范围
            if start_date:
                df = df[df["trade_date"] >= start_date]
            if end_date:
                df = df[df["trade_date"] <= end_date]

            return df

        except Exception as e:
            raise DataSourceError(f"获取指数 {index_code} 数据失败: {str(e)}")

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
        import akshare as ak

        self._rate_limit()

        # 转换代码格式
        ak_code = self._convert_to_akshare_format(ts_code)

        try:
            # 获取个股资产负债表
            df = ak.stock_balance_sheet_by_yearly_em(symbol=ak_code)

            # AKShare的财务数据是按报告期的，需要转换为日线数据
            # 这里简化处理，返回空DataFrame
            # 实际使用中需要更复杂的处理逻辑

            return pd.DataFrame()

        except Exception as e:
            raise DataSourceError(f"获取 {ts_code} 财务数据失败: {str(e)}")
