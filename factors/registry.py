"""
因子注册表模块
管理所有因子的注册和发现
"""
from typing import Dict, List, Optional, Type, Any
import inspect

from .base import Factor


class FactorRegistry:
    """
    因子注册表

    管理所有已注册的因子，支持因子的注册、查询和发现
    """

    def __init__(self):
        """初始化注册表"""
        self._factors: Dict[str, Type[Factor]] = {}

    def register(self, name: Optional[str] = None) -> callable:
        """
        因子注册装饰器

        Args:
            name: 因子名称，如果为None则使用Factor类的name属性

        Returns:
            装饰器函数

        Examples:
            @factor_registry.register("MY_FACTOR")
            class MyFactor(Factor):
                pass
        """
        def decorator(factor_class: Type[Factor]) -> Type[Factor]:
            # 验证是否是Factor的子类
            if not issubclass(factor_class, Factor):
                raise TypeError(f"{factor_class.__name__} 必须继承自 Factor")

            # 获取因子名称
            factor_name = name or factor_class.name

            if not factor_name:
                raise ValueError(f"因子 {factor_class.__name__} 缺少name属性")

            # 注册因子
            self._factors[factor_name] = factor_class

            return factor_class

        return decorator

    def register_class(self, factor_class: Type[Factor], name: Optional[str] = None):
        """
        直接注册因子类

        Args:
            factor_class: 因子类
            name: 因子名称，如果为None则使用Factor类的name属性
        """
        # 验证是否是Factor的子类
        if not issubclass(factor_class, Factor):
            raise TypeError(f"{factor_class.__name__} 必须继承自 Factor")

        # 获取因子名称
        factor_name = name or factor_class.name

        if not factor_name:
            raise ValueError(f"因子 {factor_class.__name__} 缺少name属性")

        # 注册因子
        self._factors[factor_name] = factor_class

    def unregister(self, name: str):
        """
        注销因子

        Args:
            name: 因子名称
        """
        if name in self._factors:
            del self._factors[name]

    def get(self, name: str, **params) -> Optional[Factor]:
        """
        获取因子实例

        Args:
            name: 因子名称
            **params: 因子参数

        Returns:
            因子实例，如果不存在则返回None
        """
        factor_class = self._factors.get(name)

        if factor_class is None:
            return None

        return factor_class(**params)

    def get_class(self, name: str) -> Optional[Type[Factor]]:
        """
        获取因子类

        Args:
            name: 因子名称

        Returns:
            因子类，如果不存在则返回None
        """
        return self._factors.get(name)

    def list_factors(
        self, category: Optional[str] = None
    ) -> List[str]:
        """
        列出所有已注册的因子

        Args:
            category: 因子类别，如果为None则列出所有因子

        Returns:
            因子名称列表
        """
        if category is None:
            return list(self._factors.keys())

        # 筛选指定类别的因子
        factors = []
        for name, factor_class in self._factors.items():
            if factor_class.category == category:
                factors.append(name)

        return factors

    def list_factors_by_category(self) -> Dict[str, List[str]]:
        """
        按类别列出因子

        Returns:
            字典，key为类别，value为该类别的因子列表
        """
        result = {}

        for name, factor_class in self._factors.items():
            category = factor_class.category or "other"

            if category not in result:
                result[category] = []

            result[category].append(name)

        return result

    def get_factor_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取因子信息

        Args:
            name: 因子名称

        Returns:
            因子信息字典，如果因子不存在则返回None
        """
        factor_class = self._factors.get(name)

        if factor_class is None:
            return None

        # 创建一个临时实例来获取信息
        try:
            instance = factor_class()
            return instance.get_info()
        except Exception:
            # 如果实例化失败，返回类级别的信息
            return {
                "name": factor_class.name,
                "description": factor_class.description,
                "author": factor_class.author,
                "version": factor_class.version,
                "category": factor_class.category,
                "dependencies": factor_class.dependencies,
                "params": factor_class.params,
            }

    def get_all_factor_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有因子的信息

        Returns:
            字典，key为因子名称，value为因子信息字典
        """
        result = {}

        for name in self._factors:
            info = self.get_factor_info(name)
            if info:
                result[name] = info

        return result

    def exists(self, name: str) -> bool:
        """
        检查因子是否存在

        Args:
            name: 因子名称

        Returns:
            是否存在
        """
        return name in self._factors

    def count(self) -> int:
        """
        获取已注册因子的数量

        Returns:
            因子数量
        """
        return len(self._factors)

    def clear(self):
        """清空所有已注册的因子"""
        self._factors.clear()

    def __contains__(self, name: str) -> bool:
        """支持 'in' 操作符"""
        return name in self._factors

    def __len__(self) -> int:
        """支持 len() 操作"""
        return len(self._factors)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"FactorRegistry(factors={len(self._factors)})"


# 全局因子注册表实例
factor_registry = FactorRegistry()


def register_factor(name: Optional[str] = None) -> callable:
    """
    因子注册装饰器（便捷函数）

    Args:
        name: 因子名称

    Returns:
        装饰器函数

    Examples:
        @register_factor("MY_FACTOR")
        class MyFactor(Factor):
            pass
    """
    return factor_registry.register(name)


def get_factor(name: str, **params) -> Optional[Factor]:
    """
    获取因子实例（便捷函数）

    Args:
        name: 因子名称
        **params: 因子参数

    Returns:
        因子实例
    """
    return factor_registry.get(name, **params)


def list_factors(category: Optional[str] = None) -> List[str]:
    """
    列出所有因子（便捷函数）

    Args:
        category: 因子类别

    Returns:
        因子名称列表
    """
    return factor_registry.list_factors(category)
