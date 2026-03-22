"""
报告生成模块
生成因子分析报告（HTML格式）和图表
"""
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

try:
    import matplotlib.pyplot as plt
    import matplotlib
    from matplotlib.figure import Figure

    # 设置中文字体
    matplotlib.rcParams["font.sans-serif"] = ["SimHei"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    warnings.warn("matplotlib未安装，绘图功能将不可用。安装: pip install matplotlib")


class ReportGenerator:
    """
    报告生成器

    生成因子分析报告，包括：
    - IC/IR分析结果
    - 分层回测结果
    - 相关性分析结果
    - 各种图表
    """

    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.figures = []  # 保存图表，用于后续保存

    def _create_ic_plot(
        self,
        ic_series: pd.Series,
        title: str = "IC时序图",
    ) -> Optional["Figure"]:
        """
        创建IC时序图

        Args:
            ic_series: IC序列
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(12, 4))

        # 绘制IC序列
        ax.plot(ic_series.index, ic_series.values, label="IC", color="blue", alpha=0.7)

        # 绘制零线
        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8)

        # 绘制均值线
        mean_ic = ic_series.mean()
        ax.axhline(y=mean_ic, color="red", linestyle="--", linewidth=1, label=f"均值={mean_ic:.4f}")

        ax.set_title(title)
        ax.set_xlabel("日期")
        ax.set_ylabel("IC值")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def _create_ic_distribution_plot(
        self,
        ic_series: pd.Series,
        title: str = "IC分布图",
    ) -> Optional["Figure"]:
        """
        创建IC分布图

        Args:
            ic_series: IC序列
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # 直方图
        axes[0].hist(ic_series.dropna(), bins=30, edgecolor="black", alpha=0.7)
        axes[0].axvline(ic_series.mean(), color="red", linestyle="--", linewidth=2, label=f"均值={ic_series.mean():.4f}")
        axes[0].set_title("IC分布直方图")
        axes[0].set_xlabel("IC值")
        axes[0].set_ylabel("频数")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        # QQ图
        from scipy import stats

        stats.probplot(ic_series.dropna(), dist="norm", plot=axes[1])
        axes[1].set_title("IC Q-Q图（正态分布）")
        axes[1].grid(True, alpha=0.3)

        plt.suptitle(title, y=1.02)
        plt.tight_layout()

        return fig

    def _create_monthly_ic_boxplot(
        self,
        monthly_stats: pd.DataFrame,
        title: str = "月度IC箱线图",
    ) -> Optional["Figure"]:
        """
        创建月度IC箱线图

        Args:
            monthly_stats: 月度统计DataFrame
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        # TODO: 需要每日IC数据来绘制箱线图
        # 这里暂时用月度均值代替

        fig, ax = plt.subplots(figsize=(12, 4))

        ax.bar(monthly_stats.index, monthly_stats["mean"], alpha=0.7)
        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.8)
        ax.set_title(title)
        ax.set_xlabel("月份")
        ax.set_ylabel("IC均值")
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def _create_layer_returns_plot(
        self,
        layer_returns: pd.DataFrame,
        title: str = "各层累计收益率",
    ) -> Optional["Figure"]:
        """
        创建各层累计收益率图

        Args:
            layer_returns: 各层收益率DataFrame
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(12, 6))

        # 计算累计收益
        cumulative_returns = (1 + layer_returns).cumprod()

        # 绘制各层累计收益
        for column in cumulative_returns.columns:
            ax.plot(
                cumulative_returns.index,
                cumulative_returns[column],
                label=f"第{column + 1}层",
                alpha=0.8,
            )

        ax.set_title(title)
        ax.set_xlabel("日期")
        ax.set_ylabel("累计收益")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def _create_long_short_plot(
        self,
        long_short_return: pd.Series,
        title: str = "多空累计收益",
    ) -> Optional["Figure"]:
        """
        创建多空收益图

        Args:
            long_short_return: 多空收益Series
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(12, 4))

        # 计算累计收益
        cumulative = (1 + long_short_return).cumprod()

        ax.plot(cumulative.index, cumulative.values, label="多空收益", color="purple", linewidth=2)
        ax.axhline(y=1, color="black", linestyle="--", linewidth=0.8)

        ax.set_title(title)
        ax.set_xlabel("日期")
        ax.set_ylabel("累计收益")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        return fig

    def _create_correlation_heatmap(
        self,
        corr_matrix: pd.DataFrame,
        title: str = "因子相关性热力图",
    ) -> Optional["Figure"]:
        """
        创建相关性热力图

        Args:
            corr_matrix: 相关性矩阵
            title: 图表标题

        Returns:
            matplotlib Figure对象
        """
        if not MATPLOTLIB_AVAILABLE:
            return None

        fig, ax = plt.subplots(figsize=(10, 8))

        # 绘制热力图
        im = ax.imshow(corr_matrix.values, cmap="RdBu_r", vmin=-1, vmax=1)

        # 设置刻度
        ax.set_xticks(range(len(corr_matrix.columns)))
        ax.set_yticks(range(len(corr_matrix.index)))
        ax.set_xticklabels(corr_matrix.columns)
        ax.set_yticklabels(corr_matrix.index)

        # 旋转x轴标签
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # 添加数值标注
        for i in range(len(corr_matrix.index)):
            for j in range(len(corr_matrix.columns)):
                value = corr_matrix.values[i, j]
                text = ax.text(j, i, f"{value:.2f}", ha="center", va="center", color="black", fontsize=8)

        # 添加colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("相关系数", rotation=-90, va="bottom")

        ax.set_title(title)

        plt.tight_layout()

        return fig

    def generate_ic_report(
        self,
        ic_analysis: Dict,
        factor_name: str,
        save_path: Optional[str] = None,
    ) -> str:
        """
        生成IC/IR分析报告

        Args:
            ic_analysis: IC分析结果字典
            factor_name: 因子名称
            save_path: 保存路径，None表示自动生成

        Returns:
            HTML报告内容
        """
        html_content = []

        # 标题
        html_content.append(f"<h1>因子IC/IR分析报告</h1>")
        html_content.append(f"<h2>因子名称：{factor_name}</h2>")

        # 对每个周期的IC进行分析
        for period, results in ic_analysis.items():
            html_content.append(f"<h3>{period}日IC分析</h3>")

            # 统计指标
            stats = results["statistics"]

            html_content.append("<h4>IC统计指标</h4>")
            html_content.append("<table border='1' style='border-collapse: collapse;'>")
            html_content.append("<tr><th>指标</th><th>值</th></tr>")

            for key, value in stats.items():
                if key == "count":
                    html_content.append(f"<tr><td>样本数</td><td>{value}</td></tr>")
                elif key == "mean":
                    html_content.append(f"<tr><td>IC均值</td><td>{value:.4f}</td></tr>")
                elif key == "std":
                    html_content.append(f"<tr><td>IC标准差</td><td>{value:.4f}</td></tr>")
                elif key == "ir":
                    html_content.append(f"<tr><td>IR（信息比率）</td><td>{value:.4f}</td></tr>")
                elif key == "t_stat":
                    html_content.append(f"<tr><td>t统计量</td><td>{value:.4f}</td></tr>")
                elif key == "p_value":
                    html_content.append(f"<tr><td>p值</td><td>{value:.4f}</td></tr>")
                elif key == "positive_ratio":
                    html_content.append(f"<tr><td>正IC占比</td><td>{value:.2%}</td></tr>")
                elif key == "abs_mean":
                    html_content.append(f"<tr><td>IC绝对均值</td><td>{value:.4f}</td></tr>")

            html_content.append("</table>")

            # 生成图表
            daily_ic = results["daily_ic"]

            if not daily_ic.empty:
                # IC时序图
                fig = self._create_ic_plot(daily_ic, title=f"{period}日IC时序图")
                if fig:
                    self.figures.append(("ic_timeseries", fig))

                # IC分布图
                fig = self._create_ic_distribution_plot(daily_ic, title=f"{period}日IC分布")
                if fig:
                    self.figures.append(("ic_distribution", fig))

        # 生成HTML
        html = "\n".join(html_content)

        # 保存
        if save_path is None:
            save_path = self.output_dir / f"{factor_name}_ic_report.html"

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)

        return html

    def generate_layer_backtest_report(
        self,
        backtest_results: Dict,
        factor_name: str,
        save_path: Optional[str] = None,
    ) -> str:
        """
        生成分层回测报告

        Args:
            backtest_results: 回测结果字典
            factor_name: 因子名称
            save_path: 保存路径

        Returns:
            HTML报告内容
        """
        html_content = []

        # 标题
        html_content.append(f"<h1>因子分层回测报告</h1>")
        html_content.append(f"<h2>因子名称：{factor_name}</h2>")

        # 统计指标
        statistics = backtest_results["statistics"]

        html_content.append("<h3>各层统计指标</h3>")
        html_content.append("<table border='1' style='border-collapse: collapse;'>")
        html_content.append("<tr><th>层级</th><th>累计收益</th><th>年化收益</th><th>夏普比率</th><th>最大回撤</th></tr>")

        for layer_id, stats in statistics.items():
            if layer_id.startswith("layer_"):
                layer_num = int(layer_id.split("_")[1]) + 1
                html_content.append(
                    f"<tr><td>第{layer_num}层</td>"
                    f"<td>{stats['total_return']:.2%}</td>"
                    f"<td>{stats['annual_return']:.2%}</td>"
                    f"<td>{stats['sharpe']:.4f}</td>"
                    f"<td>{stats['max_drawdown']:.2%}</td></tr>"
                )

        html_content.append("</table>")

        # 多空收益
        if "long_short" in statistics:
            ls_stats = statistics["long_short"]
            html_content.append("<h3>多空收益</h3>")
            html_content.append("<table border='1' style='border-collapse: collapse;'>")
            html_content.append("<tr><th>指标</th><th>值</th></tr>")
            html_content.append(f"<tr><td>累计收益</td><td>{ls_stats['total_return']:.2%}</td></tr>")
            html_content.append(f"<tr><td>年化收益</td><td>{ls_stats['annual_return']:.2%}</td></tr>")
            html_content.append(f"<tr><td>夏普比率</td><td>{ls_stats['sharpe']:.4f}</td></tr>")
            html_content.append(f"<tr><td>最大回撤</td><td>{ls_stats['max_drawdown']:.2%}</td></tr>")
            html_content.append("</table>")

        # 生成图表
        layer_returns = backtest_results["layer_returns"]

        if not layer_returns.empty:
            fig = self._create_layer_returns_plot(layer_returns)
            if fig:
                self.figures.append(("layer_returns", fig))

        long_short_return = backtest_results["long_short_return"]

        if not long_short_return.empty:
            fig = self._create_long_short_plot(long_short_return)
            if fig:
                self.figures.append(("long_short", fig))

        # 生成HTML
        html = "\n".join(html_content)

        # 保存
        if save_path is None:
            save_path = self.output_dir / f"{factor_name}_backtest_report.html"

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)

        return html

    def save_figures(self, prefix: str = ""):
        """
        保存所有图表

        Args:
            prefix: 文件名前缀
        """
        if not MATPLOTLIB_AVAILABLE:
            warnings.warn("matplotlib未安装，无法保存图表")
            return

        for name, fig in self.figures:
            save_path = self.output_dir / f"{prefix}{name}.png"
            fig.savefig(save_path, dpi=150, bbox_inches="tight")
            plt.close(fig)

        self.figures.clear()

    def clear_figures(self):
        """清空图表"""
        self.figures.clear()


# 便捷函数
def generate_html_report(
    analysis_results: Dict,
    factor_name: str,
    output_dir: str = "reports",
) -> str:
    """
    快捷生成HTML报告

    Args:
        analysis_results: 分析结果字典
        factor_name: 因子名称
        output_dir: 输出目录

    Returns:
        HTML文件路径
    """
    generator = ReportGenerator(output_dir=output_dir)

    # 生成IC报告
    if "ic_analysis" in analysis_results:
        generator.generate_ic_report(analysis_results["ic_analysis"], factor_name)

    # 生成分层回测报告
    if "backtest" in analysis_results:
        generator.generate_layer_backtest_report(analysis_results["backtest"], factor_name)

    # 保存图表
    generator.save_figures(prefix=f"{factor_name}_")

    return str(generator.output_dir)
