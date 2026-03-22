"""
分析模块
提供因子分析工具：IC/IR分析、分层回测、相关性分析等
"""
from .preprocessing import (
    mad_outlier_treatment,
    sigma_outlier_treatment,
    quantile_outlier_treatment,
    zscore_standardization,
    rank_standardization,
    neutralize,
    preprocess_factor,
    fill_missing_values,
)
from .ic_ir import ICAnalyzer, compute_ic, compute_ic_statistics
from .layer_backtest import LayerBacktest, run_layer_backtest
from .correlation import CorrelationAnalyzer, compute_factor_correlation, compute_vif
from .report import ReportGenerator, generate_html_report

__all__ = [
    # 预处理
    "mad_outlier_treatment",
    "sigma_outlier_treatment",
    "quantile_outlier_treatment",
    "zscore_standardization",
    "rank_standardization",
    "neutralize",
    "preprocess_factor",
    "fill_missing_values",

    # IC/IR分析
    "ICAnalyzer",
    "compute_ic",
    "compute_ic_statistics",

    # 分层回测
    "LayerBacktest",
    "run_layer_backtest",

    # 相关性分析
    "CorrelationAnalyzer",
    "compute_factor_correlation",
    "compute_vif",

    # 报告生成
    "ReportGenerator",
    "generate_html_report",
]
