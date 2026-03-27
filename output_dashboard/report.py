"""
HTML 报告生成器
生成交互式 HTML 因子看板
"""
from typing import Optional, Dict, List
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    warnings.warn("Plotly 未安装，HTML 报告功能将不可用。请运行: pip install plotly")

from backtest.result import BacktestResult


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
