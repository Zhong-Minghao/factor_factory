"""
因子看板生成器
快速生成交互式 HTML 因子看板
"""
from typing import Optional
from pathlib import Path
import pandas as pd

from .report import FactorReport


def create_dashboard(
    result,
    output_path: Optional[str] = None,
    title: str = "因子回测报告",
    auto_open: bool = False,
) -> str:
    """
    快速生成因子看板 HTML 报告

    Args:
        result: BacktestResult 对象
        output_path: 输出文件路径（可选）
        title: 报告标题
        auto_open: 是否自动在浏览器中打开

    Returns:
        HTML 字符串

    Example:
        >>> from backtest import VectorBacktest
        >>> from output_dashboard import create_dashboard
        >>>
        >>> # 运行回测
        >>> backtest = VectorBacktest(factor_data, price_data)
        >>> result = backtest.run()
        >>>
        >>> # 生成看板
        >>> create_dashboard(
        ...     result,
        ...     output_path="reports/my_dashboard.html",
        ...     title="MA20 因子分析",
        ...     auto_open=True,
        ... )
    """
    # 创建报告生成器
    report = FactorReport(result)

    # 生成 HTML
    html_content = report.generate_html_report(
        output_path=output_path,
        title=title,
    )

    # 自动打开（如果需要）
    if auto_open and output_path:
        import webbrowser
        import os

        file_path = Path(output_path).resolve()
        file_url = f"file:///{file_path.as_posix()}"
        webbrowser.open(file_url)

    return html_content


def create_comparison_dashboard(
    results: dict,
    output_path: Optional[str] = None,
    title: str = "多因子对比报告",
) -> str:
    """
    创建多因子对比看板

    Args:
        results: {因子名: BacktestResult} 字典
        output_path: 输出文件路径
        title: 报告标题

    Returns:
        HTML 字符串

    Example:
        >>> results = {
        ...     "MA20": result1,
        ...     "RSI14": result2,
        ...     "MACD": result3,
        ... }
        >>> create_comparison_dashboard(results)
    """
    # TODO: 实现多因子对比看板
    raise NotImplementedError("多因子对比看板功能开发中")


def create_ic_dashboard(
    factor_data: pd.DataFrame,
    return_data: pd.DataFrame,
    output_path: Optional[str] = None,
    title: str = "IC 分析报告",
) -> str:
    """
    创建 IC 分析看板

    Args:
        factor_data: 因子数据
        return_data: 收益率数据
        output_path: 输出文件路径
        title: 报告标题

    Returns:
        HTML 字符串

    Example:
        >>> create_ic_dashboard(
        ...     factor_data=ma_factor,
        ...     return_data=forward_returns,
        ... )
    """
    # TODO: 实现 IC 分析看板
    raise NotImplementedError("IC 分析看板功能开发中")
