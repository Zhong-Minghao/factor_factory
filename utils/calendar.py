"""
交易日历工具
支持A股交易日历查询
"""
import pandas as pd
from datetime import datetime, date
from typing import List, Optional, Set
from pathlib import Path
import pickle

from config.settings import get_settings


class TradingCalendar:
    """
    A股交易日历

    使用缓存机制提高查询效率
    """

    def __init__(self):
        """初始化交易日历"""
        self.settings = get_settings()
        self._trading_days: Optional[Set[date]] = None
        self._load_from_cache()

    def _load_from_cache(self):
        """从缓存加载交易日历"""
        cache_path = self.settings.get_cache_path("trading_calendar.pkl")

        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    self._trading_days = pickle.load(f)
                return
            except Exception:
                pass

        # 如果缓存不存在或加载失败，初始化为空集合
        self._trading_days = set()

    def _save_to_cache(self):
        """保存交易日历到缓存"""
        cache_path = self.settings.get_cache_path("trading_calendar.pkl")

        try:
            with open(cache_path, "wb") as f:
                pickle.dump(self._trading_days, f)
        except Exception:
            pass

    def update_trading_days(self, start_date: str, end_date: str):
        """
        更新交易日历数据

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        """
        try:
            import akshare as ak

            # 获取交易日历
            df = ak.tool_trade_date_hist_sina()

            # 转换为日期类型
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date

            # 筛选日期范围
            start = pd.to_datetime(start_date).date()
            end = pd.to_datetime(end_date).date()

            # 过滤日期范围
            mask = (df["trade_date"] >= start) & (df["trade_date"] <= end)
            trading_days = set(df.loc[mask, "trade_date"])

            # 更新交易日历
            if self._trading_days is None:
                self._trading_days = set()
            self._trading_days.update(trading_days)

            # 保存到缓存
            self._save_to_cache()

        except ImportError:
            raise ImportError("请安装akshare: pip install akshare")
        except Exception as e:
            raise RuntimeError(f"更新交易日历失败: {str(e)}")

    def is_trading_day(self, date_obj: date) -> bool:
        """
        判断是否为交易日

        Args:
            date_obj: 日期对象

        Returns:
            是否为交易日
        """
        if self._trading_days is None or len(self._trading_days) == 0:
            # 如果没有交易日历数据，默认周一到周五为交易日（不含节假日）
            return date_obj.weekday() < 5

        return date_obj in self._trading_days

    def is_trading_day_str(self, date_str: str) -> bool:
        """
        判断是否为交易日（字符串版本）

        Args:
            date_str: 日期字符串 (YYYY-MM-DD)

        Returns:
            是否为交易日
        """
        date_obj = pd.to_datetime(date_str).date()
        return self.is_trading_day(date_obj)

    def get_trading_days(
        self, start_date: str, end_date: Optional[str] = None
    ) -> List[date]:
        """
        获取日期范围内的所有交易日

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天

        Returns:
            交易日的列表，按时间顺序排序
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        start = pd.to_datetime(start_date).date()
        end = pd.to_datetime(end_date).date()

        if self._trading_days is None or len(self._trading_days) == 0:
            # 如果没有交易日历数据，返回工作日（不含节假日）
            date_range = pd.date_range(start=start_date, end=end_date, freq="B")
            return [d.date() for d in date_range]

        # 过滤交易日
        trading_days = [
            d for d in self._trading_days if start <= d <= end
        ]

        return sorted(trading_days)

    def get_trading_days_str(
        self, start_date: str, end_date: Optional[str] = None
    ) -> List[str]:
        """
        获取日期范围内的所有交易日（字符串版本）

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)，默认为今天

        Returns:
            交易日的字符串列表，格式为YYYY-MM-DD
        """
        trading_days = self.get_trading_days(start_date, end_date)
        return [d.strftime("%Y-%m-%d") for d in trading_days]

    def get_previous_trading_day(self, date_obj: date) -> Optional[date]:
        """
        获取指定日期之前的最后一个交易日

        Args:
            date_obj: 日期对象

        Returns:
            前一个交易日，如果没有则返回None
        """
        # 向前查找最多30天
        for i in range(1, 31):
            prev_date = date_obj - pd.Timedelta(days=i)
            if self.is_trading_day(prev_date):
                return prev_date
        return None

    def get_next_trading_day(self, date_obj: date) -> Optional[date]:
        """
        获取指定日期之后的第一个交易日

        Args:
            date_obj: 日期对象

        Returns:
            后一个交易日，如果没有则返回None
        """
        # 向后查找最多30天
        for i in range(1, 31):
            next_date = date_obj + pd.Timedelta(days=i)
            if self.is_trading_day(next_date):
                return next_date
        return None

    def get_n_trading_days_later(self, date_obj: date, n: int) -> Optional[date]:
        """
        获取指定日期之后的第n个交易日

        Args:
            date_obj: 日期对象
            n: 向后数n个交易日

        Returns:
            第n个交易日的日期，如果没有则返回None
        """
        current = date_obj
        count = 0

        # 向后查找最多一年
        for _ in range(365):
            current = current + pd.Timedelta(days=1)
            if self.is_trading_day(current):
                count += 1
                if count >= n:
                    return current

        return None

    def get_trading_days_count(self, start_date: str, end_date: str) -> int:
        """
        计算日期范围内的交易日天数

        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            交易日天数
        """
        trading_days = self.get_trading_days(start_date, end_date)
        return len(trading_days)


# 全局交易日历实例
_calendar: Optional[TradingCalendar] = None


def get_calendar() -> TradingCalendar:
    """
    获取全局交易日历实例（单例模式）

    Returns:
        TradingCalendar实例
    """
    global _calendar
    if _calendar is None:
        _calendar = TradingCalendar()
    return _calendar


def is_trading_day(date_obj: date) -> bool:
    """
    判断是否为交易日（便捷函数）

    Args:
        date_obj: 日期对象

    Returns:
        是否为交易日
    """
    return get_calendar().is_trading_day(date_obj)


def get_trading_days(
    start_date: str, end_date: Optional[str] = None
) -> List[date]:
    """
    获取交易日列表（便捷函数）

    Args:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)，默认为今天

    Returns:
        交易日列表
    """
    return get_calendar().get_trading_days(start_date, end_date)
