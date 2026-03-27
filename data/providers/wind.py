"""
Wind数据源接口
"""
import time
from typing import Optional, List, Dict, Any
import pandas as pd
from datetime import datetime
from functools import wraps

from ..base import DataSourceBase, DataSourceError, DataSourceConnectionError
from config.settings import get_settings


def require_connection(func):
    """
    装饰器：确保Wind连接已建立

    如果未连接，抛出 DataSourceError 异常
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.is_connected():
            raise DataSourceError("未连接到Wind，请先调用connect()")
        return func(self, *args, **kwargs)
    return wrapper


class WindSource(DataSourceBase):
    """
    Wind数据源

    需要安装WindPy并配置Wind终端
    官网: https://www.wind.com.cn/
    WindPy文档: https://www.windquant.com/qntcloud/api

    使用前需要：
    1. 安装Wind终端
    2. 安装WindPy: pip install WindPy
    3. 确保Wind终端已登录
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Wind数据源

        Args:
            config: 配置字典，可选字段：
                - account: Wind账号（可选，默认使用终端登录账号）
                - password: Wind密码（可选）
                - server: Wind服务器地址（可选）
        """
        super().__init__(config)

        self.account = self.config.get("account")
        self.password = self.config.get("password")
        self.server = self.config.get("server", "localhost")  # 默认本地服务器

        self.api = None
        self._last_request_time = 0
        self._min_interval = 0.05  # 请求间隔（秒）

        # 注意：基类已经定义了 self._connected，这里不需要重复定义

        # Wind错误码映射
        self._error_codes = {
            -40520007: "无权限",
            -40521009: "数据不存在",
            -40520001: "参数错误",
            -40521001: "连接失败",
        }

    def connect(self) -> bool:
        """
        建立Wind连接

        Returns:
            是否连接成功
        """
        try:
            from WindPy import w

            self.api = w

            # 启动Wind接口
            start_result = self.api.start()

            if start_result.ErrorCode != 0:
                error_msg = self._get_error_message(start_result.ErrorCode)
                raise DataSourceConnectionError(
                    f"Wind连接失败: {error_msg} (错误码: {start_result.ErrorCode})"
                )

            # 测试连接 - 获取一个简单的数据
            # Wind API 需要 external_id 格式
            from factor_factory.utils.helpers import to_external_id
            test_code = to_external_id("sz000001")
            test_data = self.api.wsd(test_code, "close", "2024-01-02", "2024-01-02")

            if test_data.ErrorCode != 0:
                raise DataSourceConnectionError("Wind连接测试失败")

            # 连接成功，设置状态
            self._connected = True
            return True

        except ImportError:
            raise ImportError("请安装WindPy: pip install WindPy")
        except Exception as e:
            raise DataSourceConnectionError(f"Wind连接失败: {str(e)}")

    def disconnect(self):
        """断开Wind连接"""
        if self.api is not None:
            try:
                self.api.stop()
            except Exception:
                pass

        self.api = None
        self._connected = False  # 清除连接状态

    def is_connected(self) -> bool:
        """
        检查是否已连接

        Returns:
            是否已连接
        """
        # 同时检查状态标志和API对象
        return self._connected and self.api is not None

    def _get_error_message(self, error_code: int) -> str:
        """
        获取Wind错误信息

        Args:
            error_code: 错误码

        Returns:
            错误信息
        """
        return self._error_codes.get(error_code, f"未知错误 (错误码: {error_code})")

    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time

        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)

        self._last_request_time = time.time()

    def _check_error(self, result) -> None:
        """
        检查Wind API返回结果

        Args:
            result: Wind API返回结果

        Raises:
            DataSourceError: 如果返回错误
        """
        if result.ErrorCode != 0:
            error_msg = self._get_error_message(result.ErrorCode)
            raise DataSourceError(f"Wind API错误: {error_msg}")

    @require_connection
    def get_stock_list(self) -> pd.DataFrame:
        """
        获取股票列表

        Returns:
            股票列表 DataFrame
        """
        self._rate_limit()

        try:
            # 使用wset获取全部A股列表
            # sectorconstituent: 获取板块成分股
            # sectorid=a001010100000000: 全部A股板块代码
            result = self.api.wset("sectorconstituent", "date=2024-03-15;sectorid=a001010100000000")

            self._check_error(result)

            # Wind返回的数据格式：
            # Data[0]: 时间戳
            # Data[1]: 股票代码
            # Data[2]: 股票名称
            if result.Data is None or len(result.Data) < 2:
                return pd.DataFrame()

            # 提取数据
            # Data[1] 是股票代码，Data[2] 是股票名称
            codes = result.Data[1] if len(result.Data) > 1 else []
            names = result.Data[2] if len(result.Data) > 2 else []

            # 构造DataFrame
            df = pd.DataFrame({
                "ts_code": codes,
                "name": names,
            })

            # 添加默认字段
            df["industry"] = ""
            df["list_date"] = ""

            return df

        except Exception as e:
            raise DataSourceError(f"获取股票列表失败: {str(e)}")

    @require_connection
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
            日线行情 DataFrame
        """
        # 验证日期
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        self._rate_limit()

        try:
            # 转换日期格式为Wind格式 (YYYYMMDD)
            wind_start = start_date.replace("-", "") if start_date else ""
            wind_end = end_date.replace("-", "") if end_date else ""

            # 调用WSD获取日线数据
            # open, high, low, close, volume, amt
            result = self.api.wsd(
                ts_code,
                "open,high,low,close,volume,amt",
                wind_start,
                wind_end,
                "Fill=Previous"
            )

            self._check_error(result)

            if result.Data is None or len(result.Data) == 0:
                return pd.DataFrame()

            # 构造DataFrame
            df = pd.DataFrame({
                "trade_date": pd.to_datetime(result.Times, errors="coerce"),
                "open": result.Data[0] if len(result.Data) > 0 else [],
                "high": result.Data[1] if len(result.Data) > 1 else [],
                "low": result.Data[2] if len(result.Data) > 2 else [],
                "close": result.Data[3] if len(result.Data) > 3 else [],
                "volume": result.Data[4] if len(result.Data) > 4 else [],
                "amount": result.Data[5] if len(result.Data) > 5 else [],
            })

            # 标准化格式
            df = self.standardize_dataframe(df, date_column="trade_date")

            # 转换日期为字符串格式
            df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")

            return df

        except Exception as e:
            raise DataSourceError(f"获取 {ts_code} 数据失败: {str(e)}")

    @require_connection
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
        result = {}

        # Wind支持批量获取，将代码用逗号连接
        # 但为了避免一次请求过多，分批处理
        batch_size = 50  # 每批50只股票

        for i in range(0, len(ts_codes), batch_size):
            batch_codes = ts_codes[i:i + batch_size]

            try:
                # 验证日期
                start_date_validated = self.validate_date(start_date)
                end_date_validated = self.validate_date(end_date)

                self._rate_limit()

                # 转换日期格式
                wind_start = start_date_validated.replace("-", "") if start_date_validated else ""
                wind_end = end_date_validated.replace("-", "") if end_date_validated else ""

                # 批量获取数据
                codes_str = ",".join(batch_codes)
                wind_result = self.api.wsd(
                    codes_str,
                    "open,high,low,close,volume,amt",
                    wind_start,
                    wind_end,
                    "Fill=Previous"
                )

                self._check_error(wind_result)

                # Wind批量返回的数据是一个二维数组，需要按股票代码分割
                # 这里简化处理，逐个获取
                for ts_code in batch_codes:
                    try:
                        df = self.get_daily_data(ts_code, start_date, end_date)
                        if not df.empty:
                            result[ts_code] = df
                    except Exception as e:
                        print(f"获取 {ts_code} 数据失败: {str(e)}")
                        continue

            except Exception as e:
                print(f"批量获取数据失败: {str(e)}")
                # 如果批量失败，尝试逐个获取
                for ts_code in batch_codes:
                    try:
                        df = self.get_daily_data(ts_code, start_date, end_date)
                        if not df.empty:
                            result[ts_code] = df
                    except Exception as inner_e:
                        print(f"获取 {ts_code} 数据失败: {str(inner_e)}")
                        continue

        return result

    @require_connection
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
            指数行情 DataFrame
        """
        # 验证日期
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        self._rate_limit()

        try:
            # 转换日期格式
            wind_start = start_date.replace("-", "") if start_date else ""
            wind_end = end_date.replace("-", "") if end_date else ""

            # 获取指数数据
            result = self.api.wsd(
                index_code,
                "open,high,low,close,volume,amt",
                wind_start,
                wind_end,
                "Fill=Previous"
            )

            self._check_error(result)

            if result.Data is None or len(result.Data) == 0:
                return pd.DataFrame()

            # 构造DataFrame
            df = pd.DataFrame({
                "trade_date": pd.to_datetime(result.Times, errors="coerce"),
                "open": result.Data[0] if len(result.Data) > 0 else [],
                "high": result.Data[1] if len(result.Data) > 1 else [],
                "low": result.Data[2] if len(result.Data) > 2 else [],
                "close": result.Data[3] if len(result.Data) > 3 else [],
                "volume": result.Data[4] if len(result.Data) > 4 else [],
                "amount": result.Data[5] if len(result.Data) > 5 else [],
            })

            # 标准化格式
            df = self.standardize_dataframe(df, date_column="trade_date")

            # 转换日期为字符串格式
            df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")

            return df

        except Exception as e:
            raise DataSourceError(f"获取指数 {index_code} 数据失败: {str(e)}")

    @require_connection
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
            财务数据 DataFrame
        """
        # 验证日期
        start_date = self.validate_date(start_date)
        end_date = self.validate_date(end_date)

        self._rate_limit()

        try:
            # 转换日期格式
            wind_start = start_date.replace("-", "") if start_date else ""
            wind_end = end_date.replace("-", "") if end_date else ""

            # 获取财务数据
            # 使用小写字段名：pe_ttm, pb, ps
            # 注意：total_mv 和 circula_mv 需要特殊权限，暂时不获取
            result = self.api.wsd(
                ts_code,
                "pe_ttm,pb,ps",
                wind_start,
                wind_end,
                "Fill=Previous"
            )

            self._check_error(result)

            if result.Data is None or len(result.Data) == 0:
                return pd.DataFrame()

            # 构造DataFrame
            df = pd.DataFrame({
                "trade_date": pd.to_datetime(result.Times, errors="coerce"),
                "pe_ttm": result.Data[0] if len(result.Data) > 0 else [],
                "pb": result.Data[1] if len(result.Data) > 1 else [],
                "ps_ttm": result.Data[2] if len(result.Data) > 2 else [],
            })

            # 标准化格式
            df = self.standardize_dataframe(df, date_column="trade_date")

            # 添加额外的列（与Tushare保持一致）
            df["pe"] = df["pe_ttm"]
            df["ps"] = df["ps_ttm"]
            df["total_mv"] = None  # Wind需要特殊权限
            df["circ_mv"] = None   # Wind需要特殊权限

            # 重新排列列顺序
            columns = ["trade_date", "pe", "pe_ttm", "pb", "ps", "ps_ttm", "total_mv", "circ_mv"]
            df = df[columns]

            # 转换日期为字符串格式
            df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")

            return df

        except Exception as e:
            raise DataSourceError(f"获取 {ts_code} 财务数据失败: {str(e)}")

    @require_connection
    def get_index_weight(self, index_code: str, trade_date: str) -> pd.DataFrame:
        """
        获取指数成分股权重

        Args:
            index_code: 指数代码
            trade_date: 交易日期 (YYYY-MM-DD)

        Returns:
            权重数据 DataFrame
        """
        self._rate_limit()

        try:
            # 转换日期格式
            wind_date = trade_date.replace("-", "")

            # 获取指数成分股
            result = self.api.wsd(
                index_code,
                "index_weight",
                wind_date,
                wind_date
            )

            self._check_error(result)

            if result.Data is None or len(result.Data) == 0:
                return pd.DataFrame()

            # Wind返回的数据格式需要解析
            # 这里简化处理，返回基本信息
            df = pd.DataFrame({
                "index_code": [index_code],
                "con_code": [""],
                "weight": [0],
                "trade_date": [trade_date],
            })

            return df

        except Exception as e:
            raise DataSourceError(f"获取指数 {index_code} 权重失败: {str(e)}")

    @require_connection
    def get_trade_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        exchange: str = "SSE"
    ) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            exchange: 交易所代码 (SSE=上交所, SZSE=深交所)

        Returns:
            交易日历 DataFrame
        """
        self._rate_limit()

        try:
            # 转换日期格式
            wind_start = start_date.replace("-", "") if start_date else ""
            wind_end = end_date.replace("-", "") if end_date else ""

            # 获取交易日历
            # 使用WSD获取交易所的交易日历
            result = self.api.wsd(
                f"{exchange}.TRADINGDAY",
                "trade_days",
                wind_start,
                wind_end
            )

            self._check_error(result)

            if result.Data is None or len(result.Data) == 0:
                return pd.DataFrame()

            # 构造DataFrame
            df = pd.DataFrame({
                "exchange": [exchange] * len(result.Times),
                "cal_date": pd.to_datetime(result.Times, errors="coerce").strftime("%Y-%m-%d"),
                "is_open": [1] * len(result.Times),  # Wind返回的都是交易日
            })

            return df

        except Exception as e:
            raise DataSourceError(f"获取交易日历失败: {str(e)}")

    @require_connection
    def get_fund_flow(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取资金流向数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            资金流向 DataFrame，包含列：
            - trade_date: 交易日期
            - net_inflow: 净流入
            - main_inflow: 主力净流入
            - retail_inflow: 散户净流入

        Note:
            Wind资金流向数据需要特殊权限，如果没有权限会返回空DataFrame
        """
        self._rate_limit()

        try:
            # 转换日期格式
            wind_start = start_date.replace("-", "") if start_date else ""
            wind_end = end_date.replace("-", "") if end_date else ""

            # 获取资金流向数据
            result = self.api.wsd(
                ts_code,
                "mf_net_amt,mf_main_amt,mf_retail_amt",
                wind_start,
                wind_end,
                "Fill=Previous"
            )

            self._check_error(result)

            if result.Data is None or len(result.Data) == 0:
                return pd.DataFrame()

            # 构造DataFrame
            df = pd.DataFrame({
                "trade_date": pd.to_datetime(result.Times, errors="coerce"),
                "net_inflow": result.Data[0] if len(result.Data) > 0 else [],
                "main_inflow": result.Data[1] if len(result.Data) > 1 else [],
                "retail_inflow": result.Data[2] if len(result.Data) > 2 else [],
            })

            # 标准化格式
            df = self.standardize_dataframe(df, date_column="trade_date")

            # 转换日期为字符串格式
            df["trade_date"] = df["trade_date"].dt.strftime("%Y-%m-%d")

            return df

        except DataSourceError as e:
            # 如果是权限错误，返回空DataFrame而不是抛出异常
            if "-40522007" in str(e) or "-40520007" in str(e):
                print(f"  [!] 资金流向数据需要特殊权限，跳过")
                return pd.DataFrame()
            raise
        except Exception as e:
            raise DataSourceError(f"获取 {ts_code} 资金流向失败: {str(e)}")

    @require_connection
    def get_trading_days_tdays(
        self,
        start_date: str,
        end_date: str,
        weekdays_only: bool = False
    ) -> List:
        """
        使用w.tdays获取交易日历

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            weekdays_only: 是否仅返回工作日（不含节假日）

        Returns:
            交易日期列表 (datetime.date对象)

        Example:
            # 获取交易日
            dates = wind.get_trading_days_tdays("2026-02-19", "2026-03-19")

            # 获取工作日
            dates = wind.get_trading_days_tdays("2026-02-20", "2026-03-20", weekdays_only=True)
        """
        self._rate_limit()

        try:
            # 转换日期格式为Wind格式
            wind_start = start_date.replace("-", "")
            wind_end = end_date.replace("-", "")

            # 调用w.tdays
            if weekdays_only:
                result = self.api.tdays(wind_start, wind_end, "Days=Weekdays")
            else:
                result = self.api.tdays(wind_start, wind_end)

            self._check_error(result)

            # WindPy已经将Times转换为datetime.date对象列表
            # 直接返回即可
            if result.Times:
                return list(result.Times)
            else:
                return []

        except Exception as e:
            raise DataSourceError(f"获取交易日历失败: {str(e)}")
