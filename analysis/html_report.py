"""
HTML报告生成器
生成因子库的HTML报告，展示所有因子的信息和统计
"""
from pathlib import Path
from typing import Optional
import pandas as pd
import json
from datetime import datetime

from storage.factor_store import FactorStore
from config.settings import get_settings


class FactorReportGenerator:
    """
    因子报告生成器

    生成HTML格式的因子库报告
    """

    def __init__(self, factor_store: Optional[FactorStore] = None):
        """
        初始化报告生成器

        Args:
            factor_store: FactorStore实例，如果为None则创建新实例
        """
        self.factor_store = factor_store or FactorStore()
        self.settings = get_settings()

    def generate_html_report(
        self,
        output_path: Optional[Path] = None,
        title: str = "因子库报告",
    ) -> str:
        """
        生成HTML报告

        Args:
            output_path: 输出文件路径
            title: 报告标题

        Returns:
            HTML文件路径
        """
        if output_path is None:
            output_path = self.settings.project_root / "examples" / "factor_report.html"

        output_path = Path(output_path)

        # 获取数据
        store_info = self.factor_store.get_storage_info()
        metadata_df = self.factor_store.export_metadata()

        # 生成HTML
        html_content = self._generate_html(
            title=title,
            store_info=store_info,
            metadata_df=metadata_df,
        )

        # 保存文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(output_path)

    def _generate_html(
        self,
        title: str,
        store_info: dict,
        metadata_df: pd.DataFrame,
    ) -> str:
        """
        生成HTML内容

        Args:
            title: 报告标题
            store_info: 存储信息
            metadata_df: 元数据DataFrame

        Returns:
            HTML字符串
        """
        # 生成各部分
        html_header = self._generate_header(title)
        html_summary = self._generate_summary_section(store_info, metadata_df)
        html_factors = self._generate_factors_table(metadata_df)
        html_footer = self._generate_footer()

        # 组合
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {self._generate_css()}
</head>
<body>
    {html_header}
    {html_summary}
    {html_factors}
    {html_footer}
</body>
</html>
"""
        return html

    def _generate_css(self) -> str:
        """生成CSS样式"""
        return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header .subtitle {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .section {
            padding: 30px 40px;
            border-bottom: 1px solid #eee;
        }

        .section:last-child {
            border-bottom: none;
        }

        .section-title {
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #667eea;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .summary-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .summary-card .label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .summary-card .value {
            font-size: 2em;
            font-weight: 700;
            color: #333;
        }

        .summary-card .unit {
            font-size: 0.6em;
            color: #999;
            margin-left: 5px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        table thead {
            background: #667eea;
            color: white;
        }

        table th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
        }

        table tbody tr {
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s;
        }

        table tbody tr:hover {
            background-color: #f8f9fa;
        }

        table td {
            padding: 15px;
            font-size: 0.95em;
        }

        .category-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .category-technical { background: #e3f2fd; color: #1976d2; }
        .category-momentum { background: #f3e5f5; color: #7b1fa2; }
        .category-volume { background: #e8f5e9; color: #388e3c; }
        .category-fundamental { background: #fff3e0; color: #f57c00; }
        .category-unknown { background: #f5f5f5; color: #666; }

        .params-tag {
            background: #eee;
            padding: 3px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #666;
        }

        .statistics-box {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #666;
            max-height: 100px;
            overflow-y: auto;
        }

        .footer {
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }

        .empty-state svg {
            width: 100px;
            height: 100px;
            margin-bottom: 20px;
            opacity: 0.3;
        }

        @media (max-width: 768px) {
            .container {
                border-radius: 0;
            }

            .section {
                padding: 20px;
            }

            table {
                font-size: 0.85em;
            }

            table th, table td {
                padding: 10px;
            }

            .summary-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
"""

    def _generate_header(self, title: str) -> str:
        """生成页面头部"""
        return f"""
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
"""

    def _generate_summary_section(
        self,
        store_info: dict,
        metadata_df: pd.DataFrame,
    ) -> str:
        """生成摘要部分"""
        # 统计各类别因子数量
        category_counts = {}
        if not metadata_df.empty:
            category_counts = metadata_df['category'].value_counts().to_dict()

        # 生成类别统计
        category_stats = ""
        if category_counts:
            category_stats = "<div style='margin-top: 15px;'>"
            for category, count in sorted(category_counts.items()):
                category_stats += f"<span class='category-badge category-{category}'>{category}: {count}</span> "
            category_stats += "</div>"

        return f"""
        <div class="section">
            <h2 class="section-title">📊 概览</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="label">因子总数</div>
                    <div class="value">{store_info['num_factors']}<span class="unit">个</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">存储文件大小</div>
                    <div class="value">{store_info['size_mb']:.2f}<span class="unit">MB</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">股票平均数量</div>
                    <div class="value">{self._get_avg_num_stocks(metadata_df):.0f}<span class="unit">只</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">数据平均天数</div>
                    <div class="value">{self._get_avg_num_records(metadata_df):.0f}<span class="unit">天</span></div>
                </div>
            </div>
            {category_stats}
        </div>
"""

    def _generate_factors_table(self, metadata_df: pd.DataFrame) -> str:
        """生成因子表格"""
        if metadata_df.empty:
            return """
        <div class="section">
            <h2 class="section-title">📋 因子列表</h2>
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                </svg>
                <p>暂无因子数据</p>
            </div>
        </div>
"""

        # 生成表格行
        rows = ""
        for _, row in metadata_df.iterrows():
            # 类别徽章
            category_badge = f"<span class='category-badge category-{row['category']}'>{row['category']}</span>"

            # 参数
            params_display = self._format_params(row.get('params'))

            # 统计信息
            statistics_display = self._format_statistics(row.get('statistics'))

            rows += f"""
            <tr>
                <td><strong>{row['factor_name']}</strong></td>
                <td>{category_badge}</td>
                <td>{params_display}</td>
                <td>{row['description']}</td>
                <td>{row['start_date']}<br>至 {row['end_date']}</td>
                <td>{row['num_stocks']}</td>
                <td>{row['num_records']}</td>
                <td>{statistics_display}</td>
            </tr>
"""

        return f"""
        <div class="section">
            <h2 class="section-title">📋 因子列表</h2>
            <table>
                <thead>
                    <tr>
                        <th>因子名称</th>
                        <th>类别</th>
                        <th>参数</th>
                        <th>描述</th>
                        <th>时间范围</th>
                        <th>股票数</th>
                        <th>记录数</th>
                        <th>统计信息</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
"""

    def _generate_footer(self) -> str:
        """生成页面底部"""
        # 获取版本号（如果存在）
        version = getattr(self.settings, 'app_version', '1.0.0')

        return f"""
        <div class="footer">
            <p>因子工厂 - Factor Factory v{version}</p>
            <p>存储路径: {self.factor_store.storage_path}</p>
        </div>
    </div>
"""

    def _format_params(self, params_str: str) -> str:
        """格式化参数显示"""
        if pd.isna(params_str) or not params_str:
            return "<span style='color: #999;'>默认参数</span>"

        try:
            params = json.loads(params_str)
            if not params:
                return "<span style='color: #999;'>默认参数</span>"

            items = [f"{k}={v}" for k, v in params.items()]
            return " ".join([f'<span class="params-tag">{item}</span>' for item in items])
        except:
            return f"<span class='params-tag'>{params_str}</span>"

    def _format_statistics(self, statistics_str: str) -> str:
        """格式化统计信息显示"""
        if pd.isna(statistics_str) or not statistics_str:
            return "<span style='color: #999;'>无</span>"

        try:
            stats = json.loads(statistics_str)
            items = [f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                    for k, v in stats.items()]
            return f"<div class='statistics-box'>{', '.join(items)}</div>"
        except:
            return f"<div class='statistics-box'>{statistics_str}</div>"

    def _get_avg_num_stocks(self, metadata_df: pd.DataFrame) -> float:
        """获取平均股票数量"""
        if metadata_df.empty or 'num_stocks' not in metadata_df.columns:
            return 0.0
        return metadata_df['num_stocks'].mean()

    def _get_avg_num_records(self, metadata_df: pd.DataFrame) -> float:
        """获取平均记录数量"""
        if metadata_df.empty or 'num_records' not in metadata_df.columns:
            return 0.0
        return metadata_df['num_records'].mean()


# 便捷函数
def generate_factor_report(
    output_path: Optional[Path] = None,
    title: str = "因子库报告",
) -> str:
    """
    生成因子库HTML报告

    Args:
        output_path: 输出文件路径
        title: 报告标题

    Returns:
        HTML文件路径
    """
    generator = FactorReportGenerator()
    return generator.generate_html_report(output_path=output_path, title=title)


if __name__ == "__main__":
    # 生成报告
    print("正在生成因子库报告...")

    report_path = generate_factor_report()

    print(f"✅ 报告已生成: {report_path}")
    print(f"请在浏览器中打开该文件查看报告")
