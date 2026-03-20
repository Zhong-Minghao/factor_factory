"""
配置管理模块
支持从配置文件、环境变量加载配置
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


@dataclass
class DataConfig:
    """数据配置"""
    # 数据目录
    data_dir: str = "data"
    cache_dir: str = "cache"

    # 数据源配置
    primary_provider: str = "tushare"  # 默认数据源

    # Tushare配置
    tushare_token: Optional[str] = None
    tushare_pro_api: str = "http://api.tushare.pro"

    # AKShare配置
    akshare_enabled: bool = True

    # Baostock配置
    baostock_enabled: bool = True

    # Wind配置
    wind_enabled: bool = False  # 默认关闭，需要Wind终端
    wind_account: Optional[str] = None  # Wind账号（可选）
    wind_password: Optional[str] = None  # Wind密码（可选）
    wind_server: str = "localhost"  # Wind服务器地址

    # 缓存配置
    enable_cache: bool = True
    cache_days: int = 7  # 缓存天数

    # 数据更新配置
    auto_update: bool = False
    update_time: str = "18:00"  # 自动更新时间

    # 存储格式
    storage_format: str = "hdf5"  # hdf5 or parquet


@dataclass
class FactorConfig:
    """因子配置"""
    # 因子目录
    factor_dir: str = "factors"

    # 计算配置
    parallel: bool = True  # 是否并行计算
    n_workers: int = -1    # 工作进程数，-1表示使用所有CPU核心

    # 因子存储
    factor_db_path: str = "storage/factors.h5"

    # 因子版本控制
    enable_versioning: bool = True


@dataclass
class BacktestConfig:
    """回测配置"""
    # 初始资金
    initial_capital: float = 1000000.0

    # 手续费配置
    commission_rate: float = 0.0003  # 万分之三
    min_commission: float = 5.0      # 最低手续费5元

    # 滑点配置
    slippage_rate: float = 0.0001    # 万分之一

    # A股交易规则
    t_plus_one: bool = True  # T+1交易

    # 报告配置
    report_dir: str = "reports"

    # 基准指数
    benchmark: str = "000300.SH"  # 沪深300


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "factor_factory.log"
    rotation: str = "500 MB"
    retention: str = "7 days"


@dataclass
class Settings:
    """全局配置类"""

    # 项目根目录
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)

    # 子配置
    data: DataConfig = field(default_factory=DataConfig)
    factor: FactorConfig = field(default_factory=FactorConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    log: LogConfig = field(default_factory=LogConfig)

    def __post_init__(self):
        """初始化后处理"""
        # 确保路径是绝对路径
        if not isinstance(self.project_root, Path):
            self.project_root = Path(self.project_root)

    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "Settings":
        """
        从YAML配置文件加载配置

        Args:
            config_path: 配置文件路径，默认为config/config.yaml

        Returns:
            Settings实例
        """
        if config_path is None:
            config_path = cls.get_default_config_path()

        config_file = Path(config_path)

        if not config_file.exists():
            # 如果配置文件不存在，返回默认配置
            return cls()

        # 读取YAML文件
        with open(config_file, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}

        # 递归更新配置
        return cls.from_dict(config_dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Settings":
        """
        从字典创建配置实例

        Args:
            config_dict: 配置字典

        Returns:
            Settings实例
        """
        settings = cls()

        # 更新data配置
        if "data" in config_dict:
            for key, value in config_dict["data"].items():
                # 优先使用环境变量
                env_key = f"DATA_{key.upper()}"
                if env_key in os.environ:
                    value = os.environ[env_key]
                setattr(settings.data, key, value)

        # 更新factor配置
        if "factor" in config_dict:
            for key, value in config_dict["factor"].items():
                env_key = f"FACTOR_{key.upper()}"
                if env_key in os.environ:
                    value = os.environ[env_key]
                setattr(settings.factor, key, value)

        # 更新backtest配置
        if "backtest" in config_dict:
            for key, value in config_dict["backtest"].items():
                env_key = f"BACKTEST_{key.upper()}"
                if env_key in os.environ:
                    value = os.environ[env_key]
                setattr(settings.backtest, key, value)

        # 更新log配置
        if "log" in config_dict:
            for key, value in config_dict["log"].items():
                setattr(settings.log, key, value)

        return settings

    @staticmethod
    def get_default_config_path() -> str:
        """获取默认配置文件路径"""
        return str(Path(__file__).parent / "config.yaml")

    def get_data_path(self, *paths: str) -> Path:
        """获取数据目录下的文件路径"""
        return (self.project_root / self.data.data_dir).joinpath(*paths)

    def get_cache_path(self, *paths: str) -> Path:
        """获取缓存目录下的文件路径"""
        cache_dir = self.project_root / self.data.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir.joinpath(*paths)

    def get_factor_db_path(self) -> Path:
        """获取因子数据库路径"""
        return self.project_root / self.factor.factor_db_path

    def get_report_path(self, *paths: str) -> Path:
        """获取报告目录下的文件路径"""
        report_dir = self.project_root / self.backtest.report_dir
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir.joinpath(*paths)

    def get_log_path(self, *paths: str) -> Path:
        """获取日志目录下的文件路径"""
        log_dir = self.project_root / self.log.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir.joinpath(*paths)


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取全局配置实例（单例模式）

    Returns:
        Settings实例
    """
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml()
    return _settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """
    重新加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        Settings实例
    """
    global _settings
    _settings = Settings.from_yaml(config_path)
    return _settings
