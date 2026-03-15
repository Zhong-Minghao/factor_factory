"""
数据缓存模块
提供高效的数据缓存机制
"""
from pathlib import Path
from typing import Optional, Any, Dict
import pickle
import hashlib
import json
from datetime import datetime, timedelta
import pandas as pd

from config.settings import get_settings


class DataCache:
    """
    数据缓存类

    支持多种缓存策略：
    - 内存缓存：最快的访问速度
    - 磁盘缓存：持久化存储
    - TTL缓存：支持过期时间
    """

    def __init__(self):
        """初始化缓存"""
        self.settings = get_settings()
        self._memory_cache: Dict[str, tuple] = {}  # (data, expire_time)

        # 缓存目录
        self.cache_dir = self.settings.get_cache_path()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 默认缓存时间（天）
        self.default_ttl = self.settings.data.cache_days

    def _generate_key(self, *args, **kwargs) -> str:
        """
        生成缓存键

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            缓存键的MD5哈希值
        """
        # 将参数序列化为字符串
        key_parts = []

        for arg in args:
            if isinstance(arg, pd.DataFrame):
                # DataFrame特殊处理
                key_parts.append(arg.to_string())
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            if isinstance(v, pd.DataFrame):
                key_parts.append(f"{k}={v.to_string()}")
            else:
                key_parts.append(f"{k}={v}")

        key_string = "|".join(key_parts)

        # 生成MD5哈希
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_file_path(self, key: str) -> Path:
        """
        获取缓存文件路径

        Args:
            key: 缓存键

        Returns:
            缓存文件路径
        """
        return self.cache_dir / f"{key}.pkl"

    def get(self, key: str, default: Any = None) -> Any:
        """
        从内存缓存获取数据

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存的数据，如果不存在或已过期则返回默认值
        """
        if key in self._memory_cache:
            data, expire_time = self._memory_cache[key]

            # 检查是否过期
            if expire_time is None or datetime.now() < expire_time:
                return data
            else:
                # 删除过期的缓存
                del self._memory_cache[key]

        return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置内存缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果为None则使用默认配置
        """
        if ttl is None:
            # 使用默认天数转换为秒
            ttl = self.default_ttl * 24 * 3600

        expire_time = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None

        self._memory_cache[key] = (value, expire_time)

    def get_disk(self, key: str, default: Any = None) -> Any:
        """
        从磁盘缓存获取数据

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存的数据，如果不存在或已过期则返回默认值
        """
        cache_file = self._get_cache_file_path(key)

        if not cache_file.exists():
            return default

        try:
            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)

            # 检查是否过期
            expire_time = cache_data.get("expire_time")
            if expire_time is None or datetime.now() < expire_time:
                return cache_data["data"]
            else:
                # 删除过期的缓存
                cache_file.unlink()
                return default

        except Exception:
            return default

    def set_disk(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        设置磁盘缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        if ttl is None:
            ttl = self.default_ttl * 24 * 3600

        expire_time = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None

        cache_data = {"data": value, "expire_time": expire_time}

        cache_file = self._get_cache_file_path(key)

        try:
            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)
        except Exception:
            pass

    def get_cached(self, key: str, default: Any = None, use_disk: bool = True) -> Any:
        """
        获取缓存（优先从内存获取，再从磁盘获取）

        Args:
            key: 缓存键
            default: 默认值
            use_disk: 是否使用磁盘缓存

        Returns:
            缓存的数据
        """
        # 先从内存获取
        data = self.get(key)

        if data is not None:
            return data

        # 再从磁盘获取
        if use_disk:
            data = self.get_disk(key, default)

            # 如果从磁盘获取到了数据，放入内存缓存
            if data is not None and data is not default:
                self.set(key, data)

            return data

        return default

    def set_cached(self, key: str, value: Any, ttl: Optional[int] = None, use_disk: bool = True):
        """
        设置缓存（同时设置内存和磁盘缓存）

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            use_disk: 是否使用磁盘缓存
        """
        # 设置内存缓存
        self.set(key, value, ttl)

        # 设置磁盘缓存
        if use_disk:
            self.set_disk(key, value, ttl)

    def delete(self, key: str):
        """
        删除缓存

        Args:
            key: 缓存键
        """
        # 删除内存缓存
        if key in self._memory_cache:
            del self._memory_cache[key]

        # 删除磁盘缓存
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            cache_file.unlink()

    def clear(self):
        """清空所有缓存"""
        # 清空内存缓存
        self._memory_cache.clear()

        # 清空磁盘缓存
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception:
                pass

    def cache_call(
        self,
        ttl: Optional[int] = None,
        use_disk: bool = True,
        key_func: Optional[callable] = None,
    ):
        """
        缓存装饰器

        Args:
            ttl: 过期时间（秒）
            use_disk: 是否使用磁盘缓存
            key_func: 自定义缓存键生成函数

        Returns:
            装饰器函数
        """

        def decorator(func):
            def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_key(func.__name__, *args, **kwargs)

                # 尝试从缓存获取
                cached_result = self.get_cached(cache_key, use_disk=use_disk)

                if cached_result is not None:
                    return cached_result

                # 调用原函数
                result = func(*args, **kwargs)

                # 缓存结果
                self.set_cached(cache_key, result, ttl=ttl, use_disk=use_disk)

                return result

            return wrapper

        return decorator

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息

        Returns:
            缓存信息字典
        """
        # 内存缓存信息
        memory_cache_count = len(self._memory_cache)
        expired_count = sum(
            1
            for _, expire_time in self._memory_cache.values()
            if expire_time is not None and datetime.now() >= expire_time
        )

        # 磁盘缓存信息
        disk_cache_files = list(self.cache_dir.glob("*.pkl"))
        disk_cache_count = len(disk_cache_files)

        # 计算磁盘缓存大小
        disk_cache_size = sum(f.stat().st_size for f in disk_cache_files)

        return {
            "memory_cache_count": memory_cache_count,
            "memory_cache_expired": expired_count,
            "disk_cache_count": disk_cache_count,
            "disk_cache_size": disk_cache_size,
            "disk_cache_size_mb": disk_cache_size / (1024 * 1024),
        }


# 全局缓存实例
_cache: Optional[DataCache] = None


def get_cache() -> DataCache:
    """
    获取全局缓存实例（单例模式）

    Returns:
        DataCache实例
    """
    global _cache
    if _cache is None:
        _cache = DataCache()
    return _cache
