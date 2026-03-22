"""
因子存储模块
使用HDF5格式存储因子值
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import pandas as pd
import warnings
from datetime import datetime

from config.settings import get_settings
from .metadata import FactorMetadata, FactorMetadataManager


class FactorStore:
    """
    因子存储类

    使用HDF5格式存储因子值，支持高效的读写操作

    数据格式：
    - 宽表格式：index=trade_date, columns=ts_code, values=factor_value
    - 每个因子存储为独立的dataset
    - 元数据存储在dataset的attrs中
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        初始化因子存储

        Args:
            storage_path: 存储文件路径，默认为storage/factors.h5
        """
        self.settings = get_settings()

        # 存储路径
        if storage_path is None:
            storage_path = self.settings.project_root / "storage" / "factors.h5"

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 元数据管理器
        self.metadata_manager = FactorMetadataManager()

        # 加载已有元数据
        self._load_existing_metadata()

    def _get_hdf5_path(self) -> Path:
        """
        获取HDF5文件路径

        Returns:
            HDF5文件路径
        """
        return self.storage_path

    def _load_existing_metadata(self):
        """加载已有的因子元数据"""
        if not self.storage_path.exists():
            return

        try:
            with pd.HDFStore(self.storage_path, mode="r") as store:
                # 遍历所有因子
                for key in store.keys():
                    if key.startswith("/factors/"):
                        # 读取元数据
                        try:
                            factor_data = store[key]
                            metadata = self._extract_metadata_from_attrs(store, key)
                            if metadata:
                                self.metadata_manager.add_metadata(metadata)
                        except Exception as e:
                            warnings.warn(f"加载因子元数据失败 {key}: {e}")
                            continue
        except Exception as e:
            warnings.warn(f"加载因子元数据失败: {e}")

    def _extract_metadata_from_attrs(self, store, key: str) -> Optional[FactorMetadata]:
        """
        从HDF5 attrs中提取元数据

        Args:
            store: HDFStore对象
            key: 数据集键

        Returns:
            因子元数据，如果不存在则返回None
        """
        try:
            # 获取数据
            factor_data = store[key]

            # 获取attrs
            storer = store.get_storer(key)

            # 检查是否有元数据
            if hasattr(storer, "attrs"):
                attrs = storer.attrs

                # 如果有完整的元数据，直接使用
                if "factor_name" in attrs:
                    metadata_dict = {}
                    for field in FactorMetadata.__dataclass_fields__:
                        if field in attrs:
                            metadata_dict[field] = attrs[field]

                    return FactorMetadata.from_dict(metadata_dict)

            # 如果没有元数据，从key推断
            factor_key = key.replace("/factors/", "")
            return self._create_metadata_from_key(factor_key, factor_data)

        except Exception as e:
            warnings.warn(f"提取元数据失败 {key}: {e}")
            return None

    def _create_metadata_from_key(self, factor_key: str, factor_data: pd.DataFrame) -> FactorMetadata:
        """
        从因子键和数据推断元数据

        Args:
            factor_key: 因子键（如：MA_20, RSI_14）
            factor_data: 因子数据

        Returns:
            因子元数据
        """
        # 解析因子名称和参数
        parts = factor_key.split("_")

        if len(parts) >= 2:
            factor_name = parts[0]
            # 尝试解析参数
            try:
                window = int(parts[1])
                params = {"window": window}
            except ValueError:
                params = {}
        else:
            factor_name = factor_key
            params = {}

        # 创建元数据
        metadata = FactorMetadata(
            factor_name=factor_name,
            category="unknown",  # 未知类别
            description=f"Factor {factor_key}",
            author="unknown",
            version="1.0.0",
            params=params,
        )

        # 更新统计信息
        metadata.update_statistics(factor_data)

        return metadata

    def save_factor(
        self,
        factor_name: str,
        factor_data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None,
        metadata: Optional[FactorMetadata] = None,
        overwrite: bool = True,
    ):
        """
        保存因子值

        Args:
            factor_name: 因子名称（如：MA, RSI）
            factor_data: 因子值DataFrame（宽表格式）
                        index: trade_date
                        columns: ts_code
                        values: factor_value
            params: 因子参数（如：{"window": 20}）
            metadata: 因子元数据，如果为None则自动创建
            overwrite: 是否覆盖已有数据
        """
        # 验证数据格式
        if not isinstance(factor_data, pd.DataFrame):
            raise ValueError("factor_data必须是DataFrame")

        if factor_data.empty:
            raise ValueError("factor_data不能为空")

        # 构造因子键
        if params:
            params_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
            factor_key = f"{factor_name}_{params_str}"
        else:
            factor_key = factor_name

        # 创建或更新元数据
        if metadata is None:
            metadata = FactorMetadata(
                factor_name=factor_name,
                category="custom",  # 默认类别
                description=f"Factor {factor_key}",
                author="user",
                version="1.0.0",
                params=params or {},
            )

        # 更新元数据的统计信息和时间
        metadata.update_statistics(factor_data)
        metadata.updated_at = datetime.now().isoformat()

        # 保存到HDF5
        hdf5_path = self._get_hdf5_path()
        dataset_key = f"/factors/{factor_key}"

        with pd.HDFStore(hdf5_path, mode="a") as store:
            if dataset_key in store and not overwrite:
                raise ValueError(f"因子 {factor_key} 已存在，设置 overwrite=True 来覆盖")

            # 保存数据
            store.put(
                dataset_key,
                factor_data,
                format="table",  # 使用表格格式以支持查询
                data_columns=True,  # 允许列索引
            )

            # 保存元数据到attrs
            storer = store.get_storer(dataset_key)
            for key, value in metadata.to_dict().items():
                storer.attrs[key] = value

        # 更新内存中的元数据
        self.metadata_manager.add_metadata(metadata)

    def load_factor(
        self,
        factor_name: str,
        params: Optional[Dict[str, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        stock_codes: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        加载因子值

        Args:
            factor_name: 因子名称
            params: 因子参数
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            stock_codes: 股票代码列表，如果为None则返回所有股票

        Returns:
            因子值DataFrame（宽表格式）
        """
        # 构造因子键
        if params:
            params_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
            factor_key = f"{factor_name}_{params_str}"
        else:
            factor_key = factor_name

        # 检查文件是否存在
        hdf5_path = self._get_hdf5_path()
        if not hdf5_path.exists():
            warnings.warn(f"因子数据库不存在: {hdf5_path}")
            return pd.DataFrame()

        dataset_key = f"/factors/{factor_key}"

        try:
            with pd.HDFStore(hdf5_path, mode="r") as store:
                if dataset_key not in store:
                    warnings.warn(f"因子不存在: {factor_key}")
                    return pd.DataFrame()

                # 读取数据
                df = store[dataset_key]

                # 筛选日期范围
                if start_date:
                    df = df[df.index >= start_date]
                if end_date:
                    df = df[df.index <= end_date]

                # 筛选股票
                if stock_codes:
                    # 确保所有股票代码都存在
                    available_codes = [code for code in stock_codes if code in df.columns]
                    missing_codes = set(stock_codes) - set(available_codes)

                    if missing_codes:
                        warnings.warn(f"以下股票代码不存在: {missing_codes}")

                    df = df[available_codes]

                return df

        except Exception as e:
            warnings.warn(f"加载因子失败 {factor_key}: {e}")
            return pd.DataFrame()

    def list_factors(
        self, category: Optional[str] = None, pattern: Optional[str] = None
    ) -> List[str]:
        """
        列出所有因子

        Args:
            category: 因子类别筛选
            pattern: 因子名称模式（如：MA*）

        Returns:
            因子键列表
        """
        factors = self.metadata_manager.list_factors()

        # 筛选类别
        if category:
            factors = [
                f
                for f in factors
                if self.metadata_manager.get_metadata(f)
                and self.metadata_manager.get_metadata(f).category == category
            ]

        # 筛选模式
        if pattern:
            import fnmatch

            factors = [f for f in factors if fnmatch.fnmatch(f, pattern)]

        return sorted(factors)

    def get_factor_metadata(self, factor_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[FactorMetadata]:
        """
        获取因子元数据

        Args:
            factor_name: 因子名称
            params: 因子参数

        Returns:
            因子元数据，如果不存在则返回None
        """
        return self.metadata_manager.get_metadata(factor_name, params)

    def delete_factor(self, factor_name: str, params: Optional[Dict[str, Any]] = None):
        """
        删除因子

        Args:
            factor_name: 因子名称
            params: 因子参数
        """
        # 构造因子键
        if params:
            params_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
            factor_key = f"{factor_name}_{params_str}"
        else:
            factor_key = factor_name

        hdf5_path = self._get_hdf5_path()
        dataset_key = f"/factors/{factor_key}"

        if not hdf5_path.exists():
            warnings.warn(f"因子数据库不存在: {hdf5_path}")
            return

        with pd.HDFStore(hdf5_path, mode="a") as store:
            if dataset_key in store:
                store.remove(dataset_key)
                # 从内存中移除元数据
                if factor_key in self.metadata_manager._metadata:
                    del self.metadata_manager._metadata[factor_key]
            else:
                warnings.warn(f"因子不存在: {factor_key}")

    def export_metadata(self) -> pd.DataFrame:
        """
        导出所有因子元数据

        Returns:
            元数据DataFrame
        """
        return self.metadata_manager.export_all_to_dataframe()

    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储信息

        Returns:
            存储信息字典
        """
        hdf5_path = self._get_hdf5_path()

        info = {
            "storage_path": str(hdf5_path),
            "exists": hdf5_path.exists(),
            "size_mb": 0,
            "num_factors": 0,
            "factors": [],
        }

        if hdf5_path.exists():
            # 文件大小
            info["size_mb"] = hdf5_path.stat().st_size / (1024 * 1024)

            # 因子列表
            try:
                with pd.HDFStore(hdf5_path, mode="r") as store:
                    keys = store.keys()
                    factor_keys = [k.replace("/factors/", "") for k in keys if k.startswith("/factors/")]
                    info["num_factors"] = len(factor_keys)
                    info["factors"] = factor_keys
            except Exception as e:
                warnings.warn(f"读取存储信息失败: {e}")

        return info

    def __repr__(self) -> str:
        """字符串表示"""
        info = self.get_storage_info()
        return f"FactorStore(factors={info['num_factors']}, size={info['size_mb']:.2f}MB)"
