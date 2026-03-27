# 输出看板模块

## 概述

本模块负责生成交互式 HTML 因子看板和报告，提供专业的可视化分析工具。

## 功能特性

### 已实现 ✅

1. **HTML 因子看板**
   - 核心 KPI 卡片（6个关键指标）
   - 净值曲线图（策略 vs 基准）
   - 回撤分析图（水下图）
   - 收益率分布直方图
   - 月度收益热力图
   - 换手率分析图
   - 绩效摘要表格

2. **交互功能**
   - 缩放和平移
   - 悬停查看详细数据
   - 图例切换
   - 导出为图片

### 开发中 ⏳

3. **多因子对比看板**
   - 多因子性能对比雷达图
   - 并列绩效指标对比
   - 净值曲线对比

4. **IC 分析看板**
   - IC 分布直方图
   - IC 滚动分析
   - IC 衰减曲线
   - IR 统计

## 文件结构

```
output_dashboard/
├── __init__.py           # 模块入口
├── dashboard.py          # 快速生成看板的主入口
├── report.py             # HTML 报告生成器
└── README.md             # 本文件
```

## 快速开始

### 方式 1：使用快速生成函数

```python
from backtest import VectorBacktest
from output_dashboard import create_dashboard

# 1. 运行回测
backtest = VectorBacktest(
    factor_data=factor_df,
    price_data=price_df,
    select_method="top_n",
    select_params={"top_n": 10},
)
result = backtest.run()

# 2. 生成看板并自动打开
create_dashboard(
    result,
    output_path="reports/my_dashboard.html",
    title="MA20 因子分析",
    auto_open=True,  # 自动在浏览器中打开
)
```

### 方式 2：使用详细 API

```python
from output_dashboard import FactorReport

# 创建报告生成器
report = FactorReport(result)

# 生成 HTML 报告
report.generate_html_report(
    output_path="reports/detailed_report.html",
    title="详细因子回测报告",
)
```

### 方式 3：自定义图表

```python
from output_dashboard import FactorReport

report = FactorReport(result)

# 创建单个图表
kpi_fig = report.create_kpi_cards()
equity_fig = report.create_equity_curve()
drawdown_fig = report.create_drawdown_chart()

# 保存为独立 HTML
kpi_fig.write_html("kpi_cards.html")
equity_fig.write_html("equity_curve.html")
```

## 输出格式

### HTML 报告

生成的 HTML 报告包含：
- 完整的交互式图表
- 响应式设计（桌面、平板、移动）
- 独立的 HTML 文件（无需服务器）
- 可在浏览器中直接打开

### 文件位置

默认输出路径：`reports/factor_backtest_report.html`

可以自定义：
```python
create_dashboard(
    result,
    output_path="custom_path/my_report.html",  # 自定义路径
)
```

## 依赖项

### 必需
- Python >= 3.10
- pandas
- numpy
- plotly

### 安装

```bash
pip install plotly
```

## 技术栈

- **Plotly**：交互式图表
- **HTML + CSS**：报告模板
- **JavaScript**：前端交互（Plotly.js）

## 使用场景

1. **因子验证**
   - 回测后立即生成报告
   - 快速评估因子有效性

2. **团队分享**
   - 通过 HTML 文件分享结果
   - 在浏览器中查看

3. **报告归档**
   - 保存历史回测结果
   - 建立因子库

4. **客户演示**
   - 专业的可视化展示
   - 交互式探索

## 扩展开发

### 添加新图表

1. 在 `report.py` 中添加新方法：
```python
def create_custom_chart(self) -> go.Figure:
    # 创建图表
    fig = go.Figure()
    # ...
    return fig
```

2. 在 `generate_html_report()` 中调用：
```python
custom_fig = self.create_custom_chart()
custom_html = custom_fig.to_html(full_html=False, include_plotlyjs=False)
```

3. 添加到 HTML 模板

### 自定义样式

修改 `report.py` 中的 CSS 样式：
```python
html_template = f"""
<style>
    /* 自定义样式 */
    body {{
        background-color: #your-color;
        /* ... */
    }}
</style>
"""
```

## 最佳实践

1. **定期生成报告**：每次回测后都生成报告
2. **版本管理**：保存不同版本的报告进行对比
3. **团队协作**：通过 HTML 文件分享结果
4. **自动化**：集成到 CI/CD 流程

## 常见问题

### Q: 如何修改报告样式？
A: 修改 `report.py` 中的 CSS 样式部分。

### Q: 如何添加自定义图表？
A: 在 `FactorReport` 类中添加新方法。

### Q: 如何集成到 Web 应用？
A: 使用 Plotly Dash 框架。

### Q: 如何导出为 PDF？
A: 在浏览器中打开 HTML，使用"打印"功能保存为 PDF。

## 参考资料

- [Plotly Python 文档](https://plotly.com/python/)
- [因子可视化指南](../VISUALIZATION_GUIDE.md)
- [回测框架文档](../BACKTEST_GUIDE.md)
