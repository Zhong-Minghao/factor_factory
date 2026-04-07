"""
因子元数据管理模块
管理因子的元数据信息
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import pandas as pd


@dataclass
class FactorMetadata:
    """
    因子元数据类

    存储因子的描述性信息，包括参数、统计数据等
    """

    # 基本信息
    factor_name: str  # 因子名称
    category: str  # 因子类别（technical/momentum/volume/fundamental）
    description: str  # 因子描述

    # 参数信息
    params: Dict[str, Any] = field(default_factory=dict)  # 因子参数

    # 数据信息
    start_date: Optional[str] = None  # 数据开始日期
    end_date: Optional[str] = None  # 数据结束日期
    num_stocks: int = 0  # 股票数量
    num_records: int = 0  # 记录数量

    # 统计信息
    statistics: Dict[str, float] = field(default_factory=dict)  # 统计信息

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            字典形式的元数据
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactorMetadata":
        """
        从字典创建元数据

        Args:
            data: 元数据字典

        Returns:
            FactorMetadata实例
        """
        # 移除已废弃的字段（兼容旧数据）
        data = {k: v for k, v in data.items() if k not in ['author', 'version', 'created_at', 'updated_at']}
        return cls(**data)

    def to_json(self) -> str:
        """
        转换为JSON字符串

        Returns:
            JSON字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "FactorMetadata":
        """
        从JSON字符串创建元数据

        Args:
            json_str: JSON字符串

        Returns:
            FactorMetadata实例
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def update_statistics(self, factor_data: pd.DataFrame):
        """
        更新统计信息

        Args:
            factor_data: 因子值DataFrame（宽表格式）
        """
        # 基本统计
        self.num_records = len(factor_data)
        self.num_stocks = len(factor_data.columns)

        if not factor_data.empty:
            # 日期范围（确保索引是DatetimeIndex）
            min_idx = factor_data.index.min()
            max_idx = factor_data.index.max()

            # 尝试将索引转换为DatetimeIndex（如果还不是的话）
            if not isinstance(factor_data.index, pd.DatetimeIndex):
                try:
                    factor_data.index = pd.to_datetime(factor_data.index)
                    min_idx = factor_data.index.min()
                    max_idx = factor_data.index.max()
                except Exception:
                    # 转换失败，使用原值
                    pass

            # 格式化日期
            if isinstance(min_idx, pd.Timestamp):
                self.start_date = min_idx.strftime("%Y-%m-%d")
                self.end_date = max_idx.strftime("%Y-%m-%d")
            elif hasattr(min_idx, 'strftime'):
                # 其他可格式化的对象
                self.start_date = min_idx.strftime("%Y-%m-%d")
                self.end_date = max_idx.strftime("%Y-%m-%d")
            else:
                # 整数或其他类型，直接转换为字符串
                self.start_date = str(min_idx)
                self.end_date = str(max_idx)

            # 统计量（计算所有股票的统计）
            values = factor_data.values.flatten()
            # 过滤NaN值
            values = values[~pd.isna(values)]

            if len(values) > 0:
                self.statistics = {
                    "mean": float(pd.Series(values).mean()),
                    "std": float(pd.Series(values).std()),
                    "min": float(pd.Series(values).min()),
                    "max": float(pd.Series(values).max()),
                    "median": float(pd.Series(values).median()),
                    "nan_ratio": float(pd.isna(factor_data.values).sum() / factor_data.size),
                }

    def get_factor_key(self) -> str:
        """
        获取因子的唯一标识键

        Returns:
            因子键（如：MA_20, RSI_14）
        """
        if self.params:
            # 将参数转换为字符串
            params_str = "_".join(f"{k}_{v}" for k, v in sorted(self.params.items()))
            return f"{self.factor_name}_{params_str}"
        else:
            return self.factor_name

    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"FactorMetadata(name={self.factor_name}, "
            f"category={self.category}, "
            f"stocks={self.num_stocks}, "
            f"records={self.num_records})"
        )


class FactorMetadataManager:
    """
    因子元数据管理器

    管理所有因子的元数据，支持批量导出
    """

    def __init__(self):
        """初始化元数据管理器"""
        self._metadata: Dict[str, FactorMetadata] = {}

    def add_metadata(self, metadata: FactorMetadata):
        """
        添加因子元数据

        Args:
            metadata: 因子元数据
        """
        key = metadata.get_factor_key()
        self._metadata[key] = metadata

    def get_metadata(self, factor_name: str, params: Optional[Dict[str, Any]] = None) -> Optional[FactorMetadata]:
        """
        获取因子元数据

        Args:
            factor_name: 因子名称
            params: 因子参数

        Returns:
            因子元数据，如果不存在则返回None
        """
        # 构造因子键
        if params:
            params_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()))
            key = f"{factor_name}_{params_str}"
        else:
            key = factor_name

        return self._metadata.get(key)

    def list_factors(self) -> List[str]:
        """
        列出所有因子键

        Returns:
            因子键列表
        """
        return list(self._metadata.keys())

    def export_all_to_dataframe(self) -> pd.DataFrame:
        """
        导出所有因子元数据为DataFrame

        Returns:
            元数据DataFrame，每行是一个因子
        """
        if not self._metadata:
            return pd.DataFrame()

        # 转换为列表
        metadata_list = []
        for metadata in self._metadata.values():
            data = metadata.to_dict()

            # 将params字典转换为JSON字符串
            if "params" in data and isinstance(data["params"], dict):
                data["params"] = json.dumps(data["params"], ensure_ascii=False)

            # 将statistics字典转换为JSON字符串
            if "statistics" in data and isinstance(data["statistics"], dict):
                data["statistics"] = json.dumps(data["statistics"], ensure_ascii=False)

            metadata_list.append(data)

        # 创建DataFrame
        df = pd.DataFrame(metadata_list)

        # 排序：按类别和因子名称
        if not df.empty:
            df = df.sort_values(["category", "factor_name"]).reset_index(drop=True)

        return df

    def export_all_to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        导出所有因子元数据为字典

        Returns:
            元数据字典，key为因子键，value为元数据字典
        """
        result = {}
        for key, metadata in self._metadata.items():
            result[key] = metadata.to_dict()
        return result

    def clear(self):
        """清空所有元数据"""
        self._metadata.clear()

    def __len__(self) -> int:
        """支持len()操作"""
        return len(self._metadata)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"FactorMetadataManager(factors={len(self._metadata)})"
