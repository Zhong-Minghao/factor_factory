"""
HTML 报告生成器
生成交互式 HTML 因子看板
"""
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from datetime import datetime

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("Plotly 未安装，HTML 报告功能将不可用。请运行: pip install plotly")

from backtest.result import BacktestResult
from analysis.ic_ir import ICAnalyzer


class FactorReport:
    """
    因子看板报告生成器

    生成交互式 HTML 报告，包含：
    - 核心指标 KPI 卡片
    - 净值曲线和收益分析
    - 风险分析图表
    - 因子有效性分析
    - 持仓分析
    """

    def __init__(self, result: BacktestResult):
        """
        初始化报告生成器

        Args:
            result: 回测结果对象
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError(
                "需要安装 Plotly 库。请运行: pip install plotly"
            )

        self.result = result
        self.figures = {}

    def create_kpi_cards(self) -> go.Figure:
        """
        创建核心指标 KPI 卡片

        Returns:
            Plotly Figure
        """
        metrics = self.result.metrics.iloc[0]

        # 定义 KPI 指标
        kpi_data = [
            {
                "title": "累计收益率",
                "value": f"{metrics['累计收益率']:.2%}",
                "color": "green" if metrics['累计收益率'] > 0 else "red",
            },
            {
                "title": "年化收益率",
                "value": f"{metrics['年化收益率']:.2%}",
                "color": "green" if metrics['年化收益率'] > 0 else "red",
            },
            {
                "title": "夏普比率",
                "value": f"{metrics['夏普比率']:.2f}",
                "color": "blue",
            },
            {
                "title": "最大回撤",
                "value": f"{metrics['最大回撤']:.2%}",
                "color": "red",
            },
            {
                "title": "卡尔玛比率",
                "value": f"{metrics['卡尔玛比率']:.2f}",
                "color": "blue",
            },
            {
                "title": "胜率",
                "value": f"{metrics['胜率']:.2%}",
                "color": "green" if metrics['胜率'] > 0.5 else "orange",
            },
        ]

        # 创建简单的柱状图作为 KPI 卡片
        fig = go.Figure()

        # 为每个 KPI 创建一个条形图
        for i, kpi in enumerate(kpi_data):
            fig.add_trace(
                go.Bar(
                    x=[kpi["title"]],
                    y=[0],  # 隐藏柱子
                    text=[kpi["value"]],
                    textposition="outside",
                    marker=dict(color=kpi["color"]),
                    showlegend=False,
                )
            )

        # 更新布局
        fig.update_layout(
            title="核心指标",
            xaxis=dict(showgrid=False, showticklabels=True),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=200,
            margin=dict(l=20, r=20, t=40, b=20),
        )

        return fig

    def create_equity_curve(self) -> go.Figure:
        """
        创建净值曲线图

        Returns:
            Plotly Figure
        """
        fig = go.Figure()

        # 策略净值
        fig.add_trace(
            go.Scatter(
                x=self.result.equity_curve.index,
                y=self.result.equity_curve.values,
                mode="lines",
                name="策略净值",
                line=dict(color="#2E86DE", width=2),
            )
        )

        # 基准净值（如果有）
        if self.result.benchmark_equity is not None:
            fig.add_trace(
                go.Scatter(
                    x=self.result.benchmark_equity.index,
                    y=self.result.benchmark_equity.values,
                    mode="lines",
                    name="基准净值",
                    line=dict(color="#95A5A6", width=2, dash="dash"),
                )
            )

        # 添加零线
        fig.add_hline(
            y=self.result.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="初始资金",
        )

        # 更新布局
        fig.update_layout(
            title="净值曲线",
            xaxis_title="日期",
            yaxis_title="净值（元）",
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )

        return fig

    def create_drawdown_chart(self) -> go.Figure:
        """
        创建回撤图（水下图）

        Returns:
            Plotly Figure
        """
        # 计算回撤
        cumulative = (1 + self.result.returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        fig = go.Figure()

        # 回撤填充区域
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown.values * 100,  # 转为百分比
                mode="lines",
                name="回撤",
                fill="tozeroy",
                line=dict(color="#E74C3C", width=1),
                fillcolor="rgba(231, 76, 60, 0.3)",
            )
        )

        # 更新布局
        fig.update_layout(
            title="回撤分析",
            xaxis_title="日期",
            yaxis_title="回撤（%）",
            hovermode="x unified",
            template="plotly_white",
            height=300,
        )

        return fig

    def create_returns_distribution(self) -> go.Figure:
        """
        创建收益率分布直方图

        Returns:
            Plotly Figure
        """
        fig = go.Figure()

        # 收益率直方图
        fig.add_trace(
            go.Histogram(
                x=self.result.returns.values * 100,  # 转为百分比
                nbinsx=30,
                name="收益率分布",
                marker=dict(color="#3498DB", line=dict(color="white", width=1)),
            )
        )

        # 添加均值线
        mean_return = self.result.returns.mean() * 100
        fig.add_vline(
            x=mean_return,
            line_dash="dash",
            line_color="red",
            annotation_text=f"均值: {mean_return:.2f}%",
        )

        # 更新布局
        fig.update_layout(
            title="收益率分布",
            xaxis_title="收益率（%）",
            yaxis_title="频数",
            template="plotly_white",
            height=300,
            showlegend=False,
        )

        return fig

    def create_monthly_returns_heatmap(self) -> go.Figure:
        """
        创建月度收益热力图

        Returns:
            Plotly Figure
        """
        # 计算月度收益
        returns = self.result.returns.copy()
        returns.index = pd.to_datetime(returns.index)

        # 按年月分组
        monthly_returns = returns.groupby(
            [returns.index.year, returns.index.month]
        ).sum()

        # 转为 DataFrame
        monthly_df = monthly_returns.unstack()

        # 只为实际存在的月份设置列名
        month_names = {
            1: "1月",
            2: "2月",
            3: "3月",
            4: "4月",
            5: "5月",
            6: "6月",
            7: "7月",
            8: "8月",
            9: "9月",
            10: "10月",
            11: "11月",
            12: "12月",
        }
        monthly_df.columns = [month_names.get(col, f"{col}月") for col in monthly_df.columns]

        # 转为百分比
        monthly_df = monthly_df * 100

        # 创建热力图
        # 使用 applymap 的替代方案
        text_values = monthly_df.map(lambda x: f"{x:.2f}%" if pd.notna(x) else "")

        fig = go.Figure(
            data=go.Heatmap(
                z=monthly_df.values,
                x=monthly_df.columns,
                y=monthly_df.index,
                colorscale="RdYlGn",
                text=text_values.values,
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="收益率（%）"),
            )
        )

        # 更新布局
        fig.update_layout(
            title="月度收益热力图",
            xaxis_title="月份",
            yaxis_title="年份",
            template="plotly_white",
            height=400,
        )

        return fig

    def create_turnover_chart(self) -> go.Figure:
        """
        创建换手率图

        Returns:
            Plotly Figure
        """
        fig = go.Figure()

        # 换手率柱状图
        fig.add_trace(
            go.Bar(
                x=self.result.turnover.index,
                y=self.result.turnover.values * 100,  # 转为百分比
                name="换手率",
                marker=dict(color="#9B59B6"),
            )
        )

        # 添加平均线
        avg_turnover = self.result.turnover.mean() * 100
        fig.add_hline(
            y=avg_turnover,
            line_dash="dash",
            line_color="red",
            annotation_text=f"平均: {avg_turnover:.2f}%",
        )

        # 更新布局
        fig.update_layout(
            title="换手率分析",
            xaxis_title="日期",
            yaxis_title="换手率（%）",
            template="plotly_white",
            height=300,
            showlegend=False,
        )

        return fig

    def create_performance_summary(self) -> str:
        """
        创建绩效摘要表格（HTML）

        Returns:
            HTML 表格字符串
        """
        metrics = self.result.metrics.iloc[0]

        # 定义指标显示配置
        metric_configs = [
            {"name": "回测期间", "value": self.result.summary()["回测期间"], "format": "text"},
            {"name": "初始资金", "value": self.result.summary()["初始资金"], "format": "text"},
            {"name": "最终资金", "value": self.result.summary()["最终资金"], "format": "text"},
            {"name": "累计收益率", "value": metrics["累计收益率"], "format": "percent"},
            {"name": "年化收益率", "value": metrics["年化收益率"], "format": "percent"},
            {"name": "波动率", "value": metrics["波动率"], "format": "percent"},
            {"name": "夏普比率", "value": metrics["夏普比率"], "format": "number"},
            {"name": "索提诺比率", "value": metrics["索提诺比率"], "format": "number"},
            {"name": "卡尔玛比率", "value": metrics["卡尔玛比率"], "format": "number"},
            {"name": "最大回撤", "value": metrics["最大回撤"], "format": "percent"},
            {"name": "胜率", "value": metrics["胜率"], "format": "percent"},
        ]

        # 添加相对指标（如果有）
        if "超额收益" in self.result.metrics.columns:
            metric_configs.append(
                {"name": "超额收益", "value": metrics["超额收益"], "format": "percent"}
            )
        if "信息比率" in self.result.metrics.columns:
            metric_configs.append(
                {"name": "信息比率", "value": metrics["信息比率"], "format": "number"}
            )

        # 生成 HTML 表格
        html_rows = []
        for config in metric_configs:
            if config["format"] == "percent":
                value_str = f"{config['value']:.2%}"
            elif config["format"] == "number":
                value_str = f"{config['value']:.2f}"
            else:
                value_str = str(config["value"])

            html_rows.append(
                f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>{config['name']}</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{value_str}</td>
                </tr>
                """
            )

        html_table = f"""
        <table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif;">
            {''.join(html_rows)}
        </table>
        """

        return html_table

    def generate_html_report(
        self,
        output_path: Optional[str] = None,
        title: str = "因子回测报告",
    ) -> str:
        """
        生成完整的 HTML 报告

        Args:
            output_path: 输出文件路径（可选）
            title: 报告标题

        Returns:
            HTML 字符串
        """
        # 创建所有图表
        kpi_fig = self.create_kpi_cards()
        equity_fig = self.create_equity_curve()
        drawdown_fig = self.create_drawdown_chart()
        returns_dist_fig = self.create_returns_distribution()
        monthly_heatmap_fig = self.create_monthly_returns_heatmap()
        turnover_fig = self.create_turnover_chart()
        summary_table = self.create_performance_summary()

        # 转换图表为 HTML
        kpi_html = kpi_fig.to_html(full_html=False, include_plotlyjs=False)
        equity_html = equity_fig.to_html(full_html=False, include_plotlyjs=False)
        drawdown_html = drawdown_fig.to_html(full_html=False, include_plotlyjs=False)
        returns_dist_html = returns_dist_fig.to_html(
            full_html=False, include_plotlyjs=False
        )
        monthly_html = monthly_heatmap_fig.to_html(
            full_html=False, include_plotlyjs=False
        )
        turnover_html = turnover_fig.to_html(full_html=False, include_plotlyjs=False)

        # 构建 HTML 报告
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 32px;
                }}
                h2 {{
                    color: #34495e;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-top: 40px;
                    font-size: 24px;
                }}
                .chart {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #fafafa;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                .summary {{
                    background-color: #ecf0f1;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 30px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #bdc3c7;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>

                <h2>核心指标</h2>
                <div class="chart">
                    {kpi_html}
                </div>

                <h2>绩效摘要</h2>
                <div class="summary">
                    {summary_table}
                </div>

                <h2>净值曲线</h2>
                <div class="chart">
                    {equity_html}
                </div>

                <h2>风险分析</h2>
                <div class="chart">
                    {drawdown_html}
                </div>

                <h2>收益率分布</h2>
                <div class="chart">
                    {returns_dist_html}
                </div>

                <h2>月度收益热力图</h2>
                <div class="chart">
                    {monthly_html}
                </div>

                <h2>换手率分析</h2>
                <div class="chart">
                    {turnover_html}
                </div>

                <div class="footer">
                    <p>生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>因子工厂 - 量化因子回测框架</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 保存到文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_template)
            print(f"HTML 报告已保存到: {output_path}")

        return html_template


class ComparisonReport:
    """
    多因子对比报告生成器

    生成多个因子的对比分析报告，包括：
    - 性能对比雷达图
    - 并列绩效指标表
    - 净值曲线对比
    - 回撤对比
    - 月度收益热力图对比
    """

    def __init__(self, results: dict):
        """
        初始化对比报告生成器

        Args:
            results: {因子名: BacktestResult} 字典
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("需要安装 Plotly 库。请运行: pip install plotly")

        if len(results) < 2:
            raise ValueError("至少需要2个因子进行对比")

        self.results = results
        self.factor_names = list(results.keys())

        # 预计算数据
        self._precompute_data()

    def _precompute_data(self):
        """预计算数据，优化性能"""
        # 对齐所有因子的日期范围
        self._align_results()

        # 提取关键指标
        self.metrics_data = self._extract_metrics()

    def _align_results(self):
        """对齐多个因子的回测结果到公共日期范围"""
        # 找到公共日期范围
        all_returns = [result.returns for result in self.results.values()]
        common_index = all_returns[0].index

        for returns in all_returns[1:]:
            common_index = common_index.intersection(returns.index)

        # 裁剪到公共范围（存储在原始结果中，不修改原始对象）
        self.aligned_returns = {}
        self.aligned_equity = {}

        for name, result in self.results.items():
            self.aligned_returns[name] = result.returns.loc[common_index]
            self.aligned_equity[name] = result.equity_curve.loc[common_index]

    def _extract_metrics(self) -> dict:
        """提取关键指标用于雷达图"""
        metrics = {}

        for name, result in self.results.items():
            result_metrics = result.metrics.iloc[0]
            metrics[name] = {
                '年化收益率': result_metrics['年化收益率'],
                '夏普比率': result_metrics['夏普比率'],
                '最大回撤': -result_metrics['最大回撤'],  # 取负，方向一致
                '卡尔玛比率': result_metrics['卡尔玛比率'],
                '胜率': result_metrics['胜率'],
            }

        return metrics

    def create_performance_radar(self) -> go.Figure:
        """
        创建多因子性能对比雷达图

        Returns:
            Plotly Figure 对象
        """
        # 1. 转换为 DataFrame
        df = pd.DataFrame(self.metrics_data).T

        # 2. 归一化处理（Min-Max 归一化到 [0, 1]）
        normalized_df = (df - df.min()) / (df.max() - df.min())
        normalized_df = normalized_df.fillna(0.5)  # 处理所有值相同的情况

        # 3. 创建雷达图
        fig = go.Figure()

        categories = normalized_df.columns.tolist()

        for factor_name in normalized_df.index:
            values = normalized_df.loc[factor_name].values

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=factor_name,
                opacity=0.7,
            ))

        # 4. 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    showticklabels=False,  # 隐藏刻度标签
                )),
            showlegend=True,
            title="多因子性能对比雷达图",
            height=500,
            template="plotly_white",
        )

        return fig


class ComparisonReport:
    """
    多因子对比报告生成器

    生成多个因子的对比分析报告，包括：
    - 性能对比雷达图
    - 并列绩效指标表
    - 净值曲线对比
    - 回撤对比
    - 月度收益热力图对比
    """

    def __init__(self, results: Dict[str, BacktestResult]):
        """
        初始化对比报告生成器

        Args:
            results: {因子名: BacktestResult} 字典
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("需要安装 Plotly 库。请运行: pip install plotly")

        if len(results) < 2:
            raise ValueError("至少需要2个因子进行对比")

        self.results = results
        self.factor_names = list(results.keys())

        # 预计算数据
        self._precompute_data()

    def _precompute_data(self):
        """预计算数据，优化性能"""
        # 对齐所有因子的日期范围
        self._align_results()

        # 提取关键指标
        self.metrics_data = self._extract_metrics()

        # 计算回撤数据
        self._compute_drawdowns()

        # 计算月度收益
        self._compute_monthly_returns()

    def _align_results(self):
        """对齐多个因子的回测结果到公共日期范围"""
        # 找到公共日期范围
        all_returns = [result.returns for result in self.results.values()]
        common_index = all_returns[0].index

        for returns in all_returns[1:]:
            common_index = common_index.intersection(returns.index)

        # 裁剪到公共范围
        self.aligned_returns = {}
        self.aligned_equity = {}

        for name, result in self.results.items():
            self.aligned_returns[name] = result.returns.loc[common_index]
            # 归一化净值曲线
            initial_value = result.equity_curve.iloc[0]
            self.aligned_equity[name] = result.equity_curve.loc[common_index] / initial_value

    def _extract_metrics(self) -> Dict:
        """提取关键指标用于雷达图"""
        metrics = {}

        for name, result in self.results.items():
            result_metrics = result.metrics.iloc[0]
            metrics[name] = {
                '年化收益率': result_metrics['年化收益率'],
                '夏普比率': result_metrics['夏普比率'],
                '最大回撤': -result_metrics['最大回撤'],  # 取负，方向一致
                '卡尔玛比率': result_metrics['卡尔玛比率'],
                '胜率': result_metrics['胜率'],
            }

        return metrics

    def _compute_drawdowns(self):
        """计算每个因子的回撤序列"""
        self.drawdowns = {}

        for name, equity in self.aligned_equity.items():
            cumulative = (equity / equity.iloc[0])
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            self.drawdowns[name] = drawdown

    def _compute_monthly_returns(self):
        """计算每个因子的月度收益"""
        self.monthly_returns = {}

        for name, returns in self.aligned_returns.items():
            returns_index = returns.copy()
            returns_index.index = pd.to_datetime(returns_index.index)

            # 按年月分组计算月度收益
            monthly = returns_index.groupby(
                [returns_index.index.year, returns_index.index.month]
            ).sum()

            monthly_df = monthly.unstack() * 100
            self.monthly_returns[name] = monthly_df

    def create_performance_radar(self) -> go.Figure:
        """
        创建多因子性能对比雷达图

        Returns:
            Plotly Figure 对象
        """
        # 1. 转换为 DataFrame
        df = pd.DataFrame(self.metrics_data).T

        # 2. 归一化处理（Min-Max 归一化到 [0, 1]）
        normalized_df = (df - df.min()) / (df.max() - df.min())
        normalized_df = normalized_df.fillna(0.5)

        # 3. 创建雷达图
        fig = go.Figure()

        categories = normalized_df.columns.tolist()

        for factor_name in normalized_df.index:
            values = normalized_df.loc[factor_name].values

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=factor_name,
                opacity=0.7,
            ))

        # 4. 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    showticklabels=False,
                )),
            showlegend=True,
            title="多因子性能对比雷达图（归一化）",
            height=500,
            template="plotly_white",
        )

        return fig

    def create_comparison_table(self) -> str:
        """
        创建并列绩效指标对比表（HTML）

        Returns:
            HTML 表格字符串
        """
        # 定义指标格式化函数
        def format_metric(value, metric_type):
            """格式化指标值"""
            if pd.isna(value):
                return "N/A"

            if metric_type == "percent":
                return f"{value * 100:.2f}%"
            elif metric_type == "number":
                return f"{value:.2f}"
            elif metric_type == "ratio":
                return f"{value:.4f}"
            else:
                return str(value)

        # 定义要显示的指标
        metrics_display = [
            ("回测期间", "period", "text"),
            ("累计收益率", "累计收益率", "percent"),
            ("年化收益率", "年化收益率", "percent"),
            ("波动率", "波动率", "percent"),
            ("夏普比率", "夏普比率", "ratio"),
            ("索提诺比率", "索提诺比率", "ratio"),
            ("最大回撤", "最大回撤", "percent"),
            ("卡尔玛比率", "卡尔玛比率", "ratio"),
            ("胜率", "胜率", "percent"),
        ]

        # 构建表格数据
        table_data = {}

        for display_name, metric_key, metric_type in metrics_display:
            row_values = []
            best_value = None

            # 收集所有值，找到最优值
            values = []
            for name in self.factor_names:
                if metric_key == "period":
                    # 特殊处理：回测期间
                    result = self.results[name]
                    start = result.start_date.strftime("%Y-%m-%d")
                    end = result.end_date.strftime("%Y-%m-%d")
                    value = f"{start}<br>至 {end}"
                    values.append((name, value))
                else:
                    result = self.results[name]
                    value = result.metrics.iloc[0].get(metric_key, np.nan)
                    values.append((name, value))

                    # 确定最优值（不同指标有不同标准）
                    if best_value is None:
                        if metric_key in ["最大回撤"]:
                            best_value = value  # 越小越好
                        else:
                            best_value = value  # 越大越好
                    else:
                        if metric_key in ["最大回撤"]:
                            if value < best_value:
                                best_value = value
                        else:
                            if value > best_value:
                                best_value = value

            # 格式化所有值
            for name, value in values:
                if metric_key == "period":
                    formatted_value = value
                else:
                    formatted_value = format_metric(value, metric_type)

                # 检查是否是最优值
                is_best = False
                if metric_key != "period" and not pd.isna(value):
                    if metric_key in ["最大回撤"]:
                        is_best = (value == best_value)
                    else:
                        is_best = (value == best_value)

                row_values.append((formatted_value, is_best))

            table_data[display_name] = row_values

        # 生成 HTML 表格
        html_rows = []

        # 标题行
        header_row = "<tr><th>指标</th>"
        for name in self.factor_names:
            header_row += f"<th>{name}</th>"
        header_row += "</tr>"
        html_rows.append(header_row)

        # 数据行
        for display_name, values in table_data.items():
            row = f"<tr><td><strong>{display_name}</strong></td>"

            for formatted_value, is_best in values:
                if is_best:
                    row += f'<td class="best-value">{formatted_value}</td>'
                else:
                    row += f"<td>{formatted_value}</td>"

            row += "</tr>"
            html_rows.append(row)

        # 添加样式
        style = """
        <style>
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }
        .comparison-table th {
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: bold;
        }
        .comparison-table td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: center;
        }
        .comparison-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .comparison-table tr:hover {
            background-color: #f5f5f5;
        }
        .best-value {
            background-color: #d5f4e6 !important;
            font-weight: bold;
            color: #27ae60;
        }
        </style>
        """

        table_html = f"""
        {style}
        <table class="comparison-table">
            {''.join(html_rows)}
        </table>
        """

        return table_html

    def create_equity_comparison(self) -> go.Figure:
        """
        创建多因子净值曲线对比图

        Returns:
            Plotly Figure 对象
        """
        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for idx, (name, equity) in enumerate(self.aligned_equity.items()):
            color = colors[idx % len(colors)]

            fig.add_trace(go.Scatter(
                x=equity.index,
                y=equity.values,
                mode='lines',
                name=name,
                line=dict(color=color, width=2),
                hovertemplate=f'{name}<br>日期: %{{x}}<br>净值: %{{y:.2f}}<extra></extra>',
            ))

        fig.update_layout(
            title="多因子净值曲线对比（归一化）",
            xaxis_title="日期",
            yaxis_title="净值（归一化）",
            hovermode='x unified',
            template="plotly_white",
            height=500,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        return fig

    def create_drawdown_comparison(self) -> go.Figure:
        """
        创建多因子回撤对比图

        Returns:
            Plotly Figure 对象
        """
        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for idx, (name, drawdown) in enumerate(self.drawdowns.items()):
            color = colors[idx % len(colors)]

            fig.add_trace(go.Scatter(
                x=drawdown.index,
                y=drawdown.values * 100,  # 转换为百分比
                mode='lines',
                name=name,
                line=dict(color=color, width=1.5),
                fill='tozeroy',
                fillcolor=color,  # 使用原色，Plotly 会自动处理透明度
                opacity=0.3,  # 设置透明度
                hovertemplate=f'{name}<br>日期: %{{x}}<br>回撤: %{{y:.2f}}%<extra></extra>',
            ))

        fig.update_layout(
            title="多因子回撤对比",
            xaxis_title="日期",
            yaxis_title="回撤（%）",
            hovermode='x unified',
            template="plotly_white",
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        return fig

    def create_monthly_heatmap_comparison(self) -> go.Figure:
        """
        创建多因子月度收益热力图对比

        Returns:
            Plotly Figure 对象（子图）
        """
        num_factors = len(self.factor_names)

        # 计算子图布局（2列）
        rows = (num_factors + 1) // 2
        cols = 2

        # 创建子图
        subplot_titles = [f"{name} 月度收益" for name in self.factor_names]
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.15,
            horizontal_spacing=0.1,
        )

        # 找到全局最小最大值，统一颜色刻度
        all_values = []
        for monthly_df in self.monthly_returns.values():
            all_values.extend(monthly_df.values.flatten())

        vmin = min(all_values) if all_values else -10
        vmax = max(all_values) if all_values else 10

        # 为每个因子创建热力图
        for idx, name in enumerate(self.factor_names):
            row = (idx // cols) + 1
            col = (idx % cols) + 1

            monthly_df = self.monthly_returns[name]

            # 创建热力图
            heatmap = go.Heatmap(
                z=monthly_df.values,
                x=list(monthly_df.columns),
                y=list(monthly_df.index),
                colorscale="RdYlGn",
                zmid=0,
                zmin=vmin,
                zmax=vmax,
                colorbar=dict(
                    title="收益率（%）",
                    x=1.02 if col == cols else None,
                ),
                text=[[f"{val:.1f}%" for val in row] for row in monthly_df.values],
                texttemplate="%{text}",
                textfont={"size": 10},
            )

            fig.add_trace(heatmap, row=row, col=col)

        # 更新布局
        fig.update_layout(
            title="多因子月度收益热力图对比",
            height=350 * rows,
            showlegend=False,
            template="plotly_white",
        )

        # 更新坐标轴标签
        fig.update_xaxes(title_text="月份")
        fig.update_yaxes(title_text="年份")

        return fig

    def generate_html_report(
        self,
        output_path: Optional[str] = None,
        title: str = "多因子对比报告",
    ) -> str:
        """
        生成完整的 HTML 报告

        Args:
            output_path: 输出文件路径
            title: 报告标题

        Returns:
            HTML 字符串
        """
        # 生成所有图表
        radar_fig = self.create_performance_radar()
        equity_fig = self.create_equity_comparison()
        drawdown_fig = self.create_drawdown_comparison()
        heatmap_fig = self.create_monthly_heatmap_comparison()

        # 转换为 HTML
        radar_html = radar_fig.to_html(full_html=False, include_plotlyjs=False)
        equity_html = equity_fig.to_html(full_html=False, include_plotlyjs=False)
        drawdown_html = drawdown_fig.to_html(full_html=False, include_plotlyjs=False)
        heatmap_html = heatmap_fig.to_html(full_html=False, include_plotlyjs=False)

        # 生成对比表格
        table_html = self.create_comparison_table()

        # 生成 HTML 模板
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>
                body {{
                    font-family: Arial, "Microsoft YaHei", sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    text-align: center;
                    color: #7f8c8d;
                    margin-bottom: 40px;
                    font-size: 14px;
                }}
                h2 {{
                    color: #34495e;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-top: 40px;
                }}
                .chart {{
                    margin: 30px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 60px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                    color: #95a5a6;
                    font-size: 12px;
                }}
                .comparison-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .comparison-table th {{
                    background-color: #3498db;
                    color: white;
                    padding: 12px;
                    text-align: center;
                    font-weight: bold;
                }}
                .comparison-table td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                    text-align: center;
                }}
                .comparison-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .comparison-table tr:hover {{
                    background-color: #f5f5f5;
                }}
                .best-value {{
                    background-color: #d5f4e6 !important;
                    font-weight: bold;
                    color: #27ae60;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <p class="subtitle">
                    对比因子：{', '.join(self.factor_names)} |
                    生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>

                <h2>性能对比雷达图（归一化）</h2>
                <div class="chart">
                    {radar_html}
                </div>

                <h2>绩效指标对比</h2>
                <div class="summary">
                    {table_html}
                </div>

                <h2>净值曲线对比（归一化）</h2>
                <div class="chart">
                    {equity_html}
                </div>

                <h2>回撤对比</h2>
                <div class="chart">
                    {drawdown_html}
                </div>

                <h2>月度收益热力图对比</h2>
                <div class="chart">
                    {heatmap_html}
                </div>

                <div class="footer">
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>因子工厂 - 量化因子回测框架</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 保存到文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_template)
            print(f"HTML 报告已保存到: {output_path}")

        return html_template


class ICReport:
    """
    IC 分析报告生成器

    生成因子的 IC/IR 分析报告，包括：
    - IC 分布直方图
    - IC 时序图
    - IC 滚动分析
    - IC 衰减曲线
    - IR 统计摘要
    - 月度 IC 热力图
    """

    def __init__(
        self,
        factor_data: pd.DataFrame,
        price_data: pd.DataFrame,
        period: int = 5,
        max_periods: int = 10,
        ic_type: str = "rank",
    ):
        """
        初始化 IC 分析报告生成器

        Args:
            factor_data: 因子数据 DataFrame（宽表格式）
            price_data: 价格数据 DataFrame（宽表格式）
            period: 基础收益率周期（默认5日）
            max_periods: IC 衰减分析的最大周期
            ic_type: IC 类型（'rank' 或 'pearson'）
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("需要安装 Plotly 库。请运行: pip install plotly")

        self.factor_data = factor_data
        self.price_data = price_data
        self.period = period
        self.max_periods = max_periods
        self.ic_type = ic_type

        # 创建 IC 分析器（复用现有类）
        self.ic_analyzer = ICAnalyzer(ic_type=ic_type)

        # 预计算 IC 数据
        self._compute_ic_data()

    def _compute_ic_data(self):
        """预计算 IC 数据，避免重复计算"""
        print("[INFO] 正在计算 IC 数据...")

        # 计算基础周期的 IC 序列
        self.ic_series = self.ic_analyzer.compute_daily_ic(
            self.factor_data,
            self.price_data,
            period=self.period,
        )

        # 计算 IC 衰减数据
        self.ic_decay_data = self._compute_ic_decay()

        # 计算 IC 统计指标
        self.ic_statistics = self.ic_analyzer.compute_ic_statistics(self.ic_series)

        # 计算滚动 IC 数据
        self._compute_rolling_ic()

        # 计算月度 IC 数据
        self._compute_monthly_ic()

        print(f"[INFO] IC 数据计算完成，共 {len(self.ic_series)} 个数据点")

    def _compute_ic_decay(self) -> pd.DataFrame:
        """计算 IC 衰减数据"""
        print(f"[INFO] 正在计算 IC 衰减（1-{self.max_periods} 期）...")

        decay_results = []

        for p in range(1, self.max_periods + 1):
            ic_series = self.ic_analyzer.compute_daily_ic(
                self.factor_data,
                self.price_data,
                period=p,
            )

            if not ic_series.empty:
                stats = self.ic_analyzer.compute_ic_statistics(ic_series)
                decay_results.append({
                    'period': p,
                    'ic_mean': stats['mean'],
                    'ic_std': stats['std'],
                    'ir': stats['ir'],
                    't_stat': stats['t_stat'],
                })

        # 如果没有结果，返回空 DataFrame
        if not decay_results:
            print("[WARNING] IC 衰减计算失败，返回空 DataFrame")
            return pd.DataFrame(columns=['period', 'ic_mean', 'ic_std', 'ir', 't_stat']).set_index('period')

        return pd.DataFrame(decay_results).set_index('period')

    def _compute_rolling_ic(self, window: int = 20):
        """计算滚动 IC 数据"""
        if len(self.ic_series) < window:
            window = max(5, len(self.ic_series) // 10)

        self.rolling_window = window
        self.rolling_ic_mean = self.ic_series.rolling(window=window).mean()
        self.rolling_ic_std = self.ic_series.rolling(window=window).std()
        self.rolling_ir = self.rolling_ic_mean / self.rolling_ic_std

    def _compute_monthly_ic(self):
        """计算月度 IC 统计"""
        if self.ic_series.empty:
            self.monthly_ic = None
            return

        ic_index = self.ic_series.copy()
        ic_index.index = pd.to_datetime(ic_index.index)

        # 按年月分组计算 IC 均值和 IR
        monthly_stats = ic_index.groupby(
            [ic_index.index.year, ic_index.index.month]
        ).agg(['mean', 'std'])

        monthly_stats.columns = monthly_stats.columns.droplevel(0)
        monthly_stats['ir'] = monthly_stats['mean'] / monthly_stats['std']

        self.monthly_ic = monthly_stats

    def create_ic_distribution(self) -> go.Figure:
        """
        创建 IC 分布直方图

        Returns:
            Plotly Figure 对象
        """
        # 检查数据是否为空
        if self.ic_series.empty or len(self.ic_series) == 0:
            fig = go.Figure()
            fig.update_layout(
                title=f"IC 分布直方图（{self.ic_type} IC）- 无数据",
                template="plotly_white",
                height=400,
            )
            return fig

        fig = go.Figure()

        # 添加直方图
        fig.add_trace(go.Histogram(
            x=self.ic_series.values,
            nbinsx=50,
            name='IC 分布',
            marker_color='skyblue',
            opacity=0.7,
        ))

        # 添加均值线
        ic_mean = self.ic_statistics['mean']
        if not pd.isna(ic_mean):
            fig.add_vline(
                x=ic_mean,
                line_dash="dash",
                line_color="red",
                annotation_text=f"均值: {ic_mean:.4f}",
                annotation_position="top right",
            )

        fig.update_layout(
            title=f"IC 分布直方图（{self.ic_type} IC）",
            xaxis_title="IC 值",
            yaxis_title="频数",
            template="plotly_white",
            height=400,
            showlegend=False,
        )

        # 添加统计信息注释
        stats_text = (
            f"均值: {ic_mean:.4f}<br>"
            f"标准差: {self.ic_statistics['std']:.4f}<br>"
            f"IR: {self.ic_statistics['ir']:.4f}<br>"
            f"样本数: {len(self.ic_series)}"
        )

        fig.add_annotation(
            text=stats_text,
            xref="paper", yref="paper",
            x=0.98, y=0.98,
            xanchor="right", yanchor="top",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#ccc",
            borderwidth=1,
        )

        return fig

    def create_ic_timeseries(self) -> go.Figure:
        """
        创建 IC 时序图

        Returns:
            Plotly Figure 对象
        """
        # 检查数据是否为空
        if self.ic_series.empty or len(self.ic_series) == 0:
            fig = go.Figure()
            fig.update_layout(
                title=f"IC 时序图（{self.ic_type} IC, {self.period}日周期）- 无数据",
                template="plotly_white",
                height=400,
            )
            return fig

        fig = go.Figure()

        # IC 序列
        fig.add_trace(go.Scatter(
            x=self.ic_series.index,
            y=self.ic_series.values,
            mode='lines+markers',
            name='IC 值',
            line=dict(color='blue', width=1),
            marker=dict(size=4),
            hovertemplate='日期: %{x}<br>IC: %{y:.4f}<extra></extra>',
        ))

        # 零线
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            annotation_text="零线",
        )

        # 均值线
        ic_mean = self.ic_statistics['mean']
        if not pd.isna(ic_mean):
            fig.add_hline(
                y=ic_mean,
                line_dash="dash",
                line_color="red",
                annotation_text=f"均值: {ic_mean:.4f}",
            )

        # ±1 标准差带
        ic_std = self.ic_statistics['std']
        if not pd.isna(ic_std):
            upper_bound = ic_mean + ic_std
            lower_bound = ic_mean - ic_std

            fig.add_trace(go.Scatter(
                x=self.ic_series.index,
                y=upper_bound,
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
            ))

            fig.add_trace(go.Scatter(
                x=self.ic_series.index,
                y=lower_bound,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(0,100,80,0.1)',
                name='±1 标准差',
                showlegend=False,
                hoverinfo='skip',
            ))

        fig.update_layout(
            title=f"IC 时序图（{self.ic_type} IC, {self.period}日周期）",
            xaxis_title="日期",
            yaxis_title="IC 值",
            template="plotly_white",
            height=400,
            hovermode='x unified',
        )

        return fig

    def create_rolling_ic_analysis(self) -> go.Figure:
        """
        创建 IC 滚动分析图

        Returns:
            Plotly Figure 对象（双子图）
        """
        # 检查数据是否为空
        if self.ic_series.empty or len(self.ic_series) == 0:
            fig = go.Figure()
            fig.update_layout(
                title=f"IC 滚动分析（{self.rolling_window}日窗口）- 无数据",
                template="plotly_white",
                height=600,
            )
            return fig

        # 创建双子图
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('滚动 IC 均值', '滚动 IR'),
            vertical_spacing=0.15,
        )

        # 子图1：滚动 IC 均值
        fig.add_trace(go.Scatter(
            x=self.rolling_ic_mean.index,
            y=self.rolling_ic_mean.values,
            mode='lines',
            name=f'滚动 IC 均值（{self.rolling_window}日）',
            line=dict(color='blue', width=2),
        ), row=1, col=1)

        ic_mean = self.ic_statistics['mean']
        if not pd.isna(ic_mean):
            fig.add_hline(
                y=ic_mean,
                line_dash="dash",
                line_color="red",
                annotation_text="总体均值",
                row=1, col=1,
            )

        # 子图2：滚动 IR
        fig.add_trace(go.Scatter(
            x=self.rolling_ir.index,
            y=self.rolling_ir.values,
            mode='lines',
            name=f'滚动 IR（{self.rolling_window}日）',
            line=dict(color='green', width=2),
        ), row=2, col=1)

        ic_ir = self.ic_statistics['ir']
        if not pd.isna(ic_ir):
            fig.add_hline(
                y=ic_ir,
                line_dash="dash",
                line_color="red",
                annotation_text="总体 IR",
                row=2, col=1,
            )

        # IR = 0.5 参考线
        fig.add_hline(
            y=0.5,
            line_dash="dot",
            line_color="orange",
            annotation_text="IR=0.5（良好）",
            row=2, col=1,
        )

        fig.update_layout(
            title=f"IC 滚动分析（{self.rolling_window}日窗口）",
            template="plotly_white",
            height=600,
            hovermode='x unified',
            showlegend=True,
        )

        fig.update_xaxes(title_text="日期")
        fig.update_yaxes(title_text="IC 均值", row=1, col=1)
        fig.update_yaxes(title_text="IR", row=2, col=1)

        return fig

    def create_ic_decay_curve(self) -> go.Figure:
        """
        创建 IC 衰减曲线

        Returns:
            Plotly Figure 对象
        """
        fig = go.Figure()

        # 检查数据是否为空
        if self.ic_decay_data.empty:
            fig.update_layout(
                title=f"IC 衰减曲线（{self.ic_type} IC, 1-{self.max_periods}期）- 无数据",
                template="plotly_white",
                height=500,
            )
            return fig

        periods = self.ic_decay_data.index.tolist()
        ic_means = self.ic_decay_data['ic_mean'].values

        # 确定颜色（正 IC 用绿色，负 IC 用红色）
        colors = ['green' if v > 0 else 'red' for v in ic_means]

        # 添加柱状图
        fig.add_trace(go.Bar(
            x=periods,
            y=ic_means,
            name='IC 均值',
            marker_color=colors,
            text=[f'{v:.4f}' for v in ic_means],
            textposition='outside',
            hovertemplate='周期: %{x}日<br>IC 均值: %{y:.4f}<extra></extra>',
        ))

        # 添加衰减趋势线
        fig.add_trace(go.Scatter(
            x=periods,
            y=ic_means,
            mode='lines+markers',
            name='衰减趋势',
            line=dict(color='blue', width=2, dash='dot'),
            marker=dict(size=8),
        ))

        # 零线
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
        )

        fig.update_layout(
            title=f"IC 衰减曲线（{self.ic_type} IC, 1-{self.max_periods}期）",
            xaxis_title="预测周期（日）",
            yaxis_title="IC 均值",
            template="plotly_white",
            height=500,
            showlegend=True,
        )

        return fig

    def create_ir_summary_table(self) -> str:
        """
        创建 IR 统计摘要表（HTML）

        Returns:
            HTML 表格字符串
        """
        stats = self.ic_statistics

        # 计算额外的统计指标
        positive_ratio = (self.ic_series > 0).mean() if len(self.ic_series) > 0 else 0
        abs_mean = self.ic_series.abs().mean() if len(self.ic_series) > 0 else 0

        # 定义指标
        metrics = [
            ("IC 均值", f"{stats['mean']:.4f}"),
            ("IC 标准差", f"{stats['std']:.4f}"),
            ("IR（信息比率）", f"{stats['ir']:.4f}"),
            ("t 统计量", f"{stats['t_stat']:.4f}"),
            ("p 值", f"{stats['p_value']:.4f}"),
            ("正 IC 占比", f"{positive_ratio * 100:.2f}%"),
            ("IC 绝对值均值", f"{abs_mean:.4f}"),
            ("样本数", f"{len(self.ic_series)}"),
        ]

        # 添加解释性注释
        explanations = {
            "IC 均值": "IC 平均值，越大越好",
            "IR（信息比率）": "IC 均值 / IC 标准差，> 0.5 为良好",
            "t 统计量": "IC 显著性检验，|t| > 1.96 显著",
            "p 值": "显著性概率，< 0.05 显著",
            "正 IC 占比": "IC > 0 的比例，理想值 > 50%",
        }

        # 生成 HTML 表格
        html_rows = []

        for metric_name, value in metrics:
            explanation = explanations.get(metric_name, "")
            row = f"""
            <tr>
                <td><strong>{metric_name}</strong></td>
                <td>{value}</td>
                <td style="color: #7f8c8d; font-size: 12px;">{explanation}</td>
            </tr>
            """
            html_rows.append(row)

        # 添加样式
        style = """
        <style>
        .ir-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }
        .ir-table th {
            background-color: #27ae60;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }
        .ir-table td {
            border: 1px solid #ddd;
            padding: 10px;
        }
        .ir-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .ir-table tr:hover {
            background-color: #f5f5f5;
        }
        </style>
        """

        table_html = f"""
        {style}
        <table class="ir-table">
            <thead>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                    <th>解释</th>
                </tr>
            </thead>
            <tbody>
                {''.join(html_rows)}
            </tbody>
        </table>
        """

        return table_html

    def create_monthly_ic_heatmap(self) -> go.Figure:
        """
        创建月度 IC 统计热力图

        Returns:
            Plotly Figure 对象
        """
        if self.monthly_ic is None or self.monthly_ic.empty:
            # 如果没有足够的月度数据，返回空白图表
            fig = go.Figure()
            fig.update_layout(
                title="月度 IC 统计（数据不足）",
                template="plotly_white",
                height=400,
            )
            return fig

        # 提取年月
        monthly_df = self.monthly_ic['mean'].unstack() * 100  # 转换为百分比

        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=monthly_df.values,
            x=list(monthly_df.columns),
            y=list(monthly_df.index),
            colorscale="RdYlGn",
            zmid=0,
            text=[[f"{val:.2f}%" for val in row] for row in monthly_df.values],
            texttemplate="%{text}",
            textfont={"size": 11},
            colorbar=dict(title="IC 均值（%）"),
        ))

        fig.update_layout(
            title=f"月度 IC 统计热力图（{self.ic_type} IC）",
            xaxis_title="月份",
            yaxis_title="年份",
            template="plotly_white",
            height=500,
        )

        return fig

    def generate_html_report(
        self,
        output_path: Optional[str] = None,
        title: str = "IC 分析报告",
    ) -> str:
        """
        生成完整的 HTML 报告

        Args:
            output_path: 输出文件路径
            title: 报告标题

        Returns:
            HTML 字符串
        """
        # 生成所有图表
        dist_fig = self.create_ic_distribution()
        timeseries_fig = self.create_ic_timeseries()
        rolling_fig = self.create_rolling_ic_analysis()
        decay_fig = self.create_ic_decay_curve()
        monthly_fig = self.create_monthly_ic_heatmap()

        # 转换为 HTML
        dist_html = dist_fig.to_html(full_html=False, include_plotlyjs=False)
        timeseries_html = timeseries_fig.to_html(full_html=False, include_plotlyjs=False)
        rolling_html = rolling_fig.to_html(full_html=False, include_plotlyjs=False)
        decay_html = decay_fig.to_html(full_html=False, include_plotlyjs=False)
        monthly_html = monthly_fig.to_html(full_html=False, include_plotlyjs=False)

        # 生成 IR 统计摘要表
        ir_table_html = self.create_ir_summary_table()

        # 生成 HTML 模板
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>
                body {{
                    font-family: Arial, "Microsoft YaHei", sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    text-align: center;
                    color: #7f8c8d;
                    margin-bottom: 40px;
                    font-size: 14px;
                }}
                h2 {{
                    color: #34495e;
                    border-bottom: 2px solid #27ae60;
                    padding-bottom: 10px;
                    margin-top: 40px;
                }}
                .chart {{
                    margin: 30px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 60px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                    color: #95a5a6;
                    font-size: 12px;
                }}
                .ir-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .ir-table th {{
                    background-color: #27ae60;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }}
                .ir-table td {{
                    border: 1px solid #ddd;
                    padding: 10px;
                }}
                .ir-table tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .ir-table tr:hover {{
                    background-color: #f5f5f5;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <p class="subtitle">
                    IC 类型：{self.ic_type} |
                    基础周期：{self.period}日 |
                    衰减分析：1-{self.max_periods}期 |
                    生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>

                <h2>IC/IR 统计摘要</h2>
                <div class="summary">
                    {ir_table_html}
                </div>

                <h2>IC 分布分析</h2>
                <div class="chart">
                    {dist_html}
                </div>

                <h2>IC 时序分析</h2>
                <div class="chart">
                    {timeseries_html}
                </div>

                <h2>IC 滚动分析（{self.rolling_window}日窗口）</h2>
                <div class="chart">
                    {rolling_html}
                </div>

                <h2>IC 衰减曲线</h2>
                <div class="chart">
                    {decay_html}
                </div>

                <h2>月度 IC 统计</h2>
                <div class="chart">
                    {monthly_html}
                </div>

                <div class="footer">
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>因子工厂 - 量化因子回测框架</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 保存到文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_template)
            print(f"HTML 报告已保存到: {output_path}")

        return html_template
