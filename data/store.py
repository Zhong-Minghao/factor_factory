"""
数据存储模块
支持HDF5和Parquet格式存储时序数据
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import h5py
from datetime import datetime

from config.settings import get_settings


class DataStore:
    """
    数据存储类

    支持多种存储格式：
    - HDF5: 适合时序数据，支持压缩和快速查询
    - Parquet: 适合列式存储和分析
    """

    def __init__(self, storage_format: Optional[str] = None):
        """
        初始化数据存储

        Args:
            storage_format: 存储格式 ('hdf5' 或 'parquet')
        """
        self.settings = get_settings()
        self.storage_format = storage_format or self.settings.data.storage_format

        # 数据目录
        self.data_dir = self.settings.get_data_path()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_hdf5_path(self) -> Path:
        """获取HDF5文件路径"""
        return self.data_dir / "market_data.h5"

    def _get_parquet_path(self, data_type: str) -> Path:
        """
        获取Parquet文件路径

        Args:
            data_type: 数据类型 (daily, index, financial等)

        Returns:
            Parquet文件路径
        """
        return self.data_dir / f"{data_type}.parquet"

    def save_daily_data(
        self, ts_code: str, data: pd.DataFrame, format: Optional[str] = None
    ):
        """
        保存日线数据

        Args:
            ts_code: 股票代码
            data: 日线数据
            format: 存储格式 (hdf5或parquet)，默认使用配置的格式
        """
        format = format or self.storage_format

        if format == "hdf5":
            self._save_hdf5(f"daily/{ts_code}", data)
        elif format == "parquet":
            self._save_parquet("daily", ts_code, data)
        else:
            raise ValueError(f"不支持的存储格式: {format}")

    def load_daily_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        format: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        加载日线数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            format: 存储格式

        Returns:
            日线数据 DataFrame
        """
        format = format or self.storage_format

        if format == "hdf5":
            df = self._load_hdf5(f"daily/{ts_code}")
        elif format == "parquet":
            df = self._load_parquet("daily", ts_code)
        else:
            raise ValueError(f"不支持的存储格式: {format}")

        # 筛选日期范围
        if not df.empty:
            if start_date:
                df = df[df["trade_date"] >= start_date]
            if end_date:
                df = df[df["trade_date"] <= end_date]

        return df

    def save_index_data(self, index_code: str, data: pd.DataFrame):
        """
        保存指数数据

        Args:
            index_code: 指数代码
            data: 指数数据
        """
        if self.storage_format == "hdf5":
            self._save_hdf5(f"index/{index_code}", data)
        else:
            self._save_parquet("index", index_code, data)

    def load_index_data(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        加载指数数据

        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            指数数据 DataFrame
        """
        if self.storage_format == "hdf5":
            df = self._load_hdf5(f"index/{index_code}")
        else:
            df = self._load_parquet("index", index_code)

        # 筛选日期范围
        if not df.empty:
            if start_date:
                df = df[df["trade_date"] >= start_date]
            if end_date:
                df = df[df["trade_date"] <= end_date]

        return df

    def _save_hdf5(self, key: str, data: pd.DataFrame):
        """
        保存数据到HDF5文件

        Args:
            key: 数据键
            data: 数据 DataFrame
        """
        hdf5_path = self._get_hdf5_path()

        # 将trade_date转换为字符串（HDF5不支持datetime类型）
        if "trade_date" in data.columns:
            data = data.copy()
            data["trade_date"] = data["trade_date"].dt.strftime("%Y-%m-%d")

        # 保存到HDF5
        with pd.HDFStore(hdf5_path, mode="a") as store:
            store.put(key, data, format="table")

    def _load_hdf5(self, key: str) -> pd.DataFrame:
        """
        从HDF5文件加载数据

        Args:
            key: 数据键

        Returns:
            数据 DataFrame
        """
        hdf5_path = self._get_hdf5_path()

        if not hdf5_path.exists():
            return pd.DataFrame()

        try:
            with pd.HDFStore(hdf5_path, mode="r") as store:
                if key in store:
                    df = store[key]
                    # 转换trade_date回datetime类型
                    if "trade_date" in df.columns:
                        df["trade_date"] = pd.to_datetime(df["trade_date"])
                    return df
                else:
                    return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def _save_parquet(self, data_type: str, code: str, data: pd.DataFrame):
        """
        保存数据到Parquet文件

        Args:
            data_type: 数据类型
            code: 股票/指数代码
            data: 数据 DataFrame
        """
        parquet_path = self._get_parquet_path(data_type)

        # 添加代码列
        data = data.copy()
        data["ts_code"] = code

        # 转换trade_date为字符串
        if "trade_date" in data.columns:
            data["trade_date"] = data["trade_date"].dt.strftime("%Y-%m-%d")

        # 读取现有数据或创建新数据
        if parquet_path.exists():
            existing_df = pd.read_parquet(parquet_path)
            # 移除该代码的旧数据
            existing_df = existing_df[existing_df["ts_code"] != code]
            # 合并新旧数据
            df = pd.concat([existing_df, data], ignore_index=True)
        else:
            df = data

        # 保存到Parquet
        df.to_parquet(parquet_path, index=False)

    def _load_parquet(self, data_type: str, code: str) -> pd.DataFrame:
        """
        从Parquet文件加载数据

        Args:
            data_type: 数据类型
            code: 股票/指数代码

        Returns:
            数据 DataFrame
        """
        parquet_path = self._get_parquet_path(data_type)

        if not parquet_path.exists():
            return pd.DataFrame()

        try:
            # 读取所有数据
            df = pd.read_parquet(parquet_path)

            # 筛选指定代码
            df = df[df["ts_code"] == code]

            # 移除ts_code列
            if "ts_code" in df.columns:
                df = df.drop(columns=["ts_code"])

            # 转换trade_date回datetime类型
            if "trade_date" in df.columns:
                df["trade_date"] = pd.to_datetime(df["trade_date"])

            return df

        except Exception:
            return pd.DataFrame()

    def get_available_codes(self, data_type: str = "daily") -> List[str]:
        """
        获取可用的股票/指数代码列表

        Args:
            data_type: 数据类型

        Returns:
            代码列表
        """
        if self.storage_format == "hdf5":
            return self._get_hdf5_keys(data_type)
        else:
            return self._get_parquet_codes(data_type)

    def _get_hdf5_keys(self, prefix: str) -> List[str]:
        """
        获取HDF5文件中指定前缀的所有键

        Args:
            prefix: 键前缀

        Returns:
            键列表
        """
        hdf5_path = self._get_hdf5_path()

        if not hdf5_path.exists():
            return []

        try:
            with pd.HDFStore(hdf5_path, mode="r") as store:
                keys = store.keys()
                # 筛选指定前缀的键，并去除前缀
                codes = [
                    k.replace(f"/{prefix}/", "").replace("/", "")
                    for k in keys
                    if k.startswith(f"/{prefix}/")
                ]
                return codes
        except Exception:
            return []

    def _get_parquet_codes(self, data_type: str) -> List[str]:
        """
        获取Parquet文件中所有代码

        Args:
            data_type: 数据类型

        Returns:
            代码列表
        """
        parquet_path = self._get_parquet_path(data_type)

        if not parquet_path.exists():
            return []

        try:
            df = pd.read_parquet(parquet_path)
            if "ts_code" in df.columns:
                return df["ts_code"].unique().tolist()
            return []
        except Exception:
            return []

    def clear_data(self, data_type: Optional[str] = None):
        """
        清除数据

        Args:
            data_type: 数据类型，如果为None则清除所有数据
        """
        if self.storage_format == "hdf5":
            hdf5_path = self._get_hdf5_path()
            if hdf5_path.exists():
                if data_type:
                    # 只清除指定类型的数据
                    keys = self._get_hdf5_keys(data_type)
                    with pd.HDFStore(hdf5_path, mode="a") as store:
                        for key in keys:
                            full_key = f"/{data_type}/{key}"
                            if full_key in store:
                                store.remove(full_key)
                else:
                    # 清除所有数据
                    hdf5_path.unlink()
        else:
            if data_type:
                parquet_path = self._get_parquet_path(data_type)
                if parquet_path.exists():
                    parquet_path.unlink()
            else:
                # 清除所有parquet文件
                for file in self.data_dir.glob("*.parquet"):
                    file.unlink()

    def get_data_size(self) -> Dict[str, Any]:
        """
        获取数据存储大小信息

        Returns:
            字典，包含各文件的大小信息
        """
        size_info = {}

        for data_type in ["daily", "index", "financial"]:
            if self.storage_format == "hdf5":
                hdf5_path = self._get_hdf5_path()
                if hdf5_path.exists():
                    size = hdf5_path.stat().st_size
                    size_info[f"{data_type}_hdf5"] = size
            else:
                parquet_path = self._get_parquet_path(data_type)
                if parquet_path.exists():
                    size = parquet_path.stat().st_size
                    size_info[f"{data_type}_parquet"] = size

        return size_info
