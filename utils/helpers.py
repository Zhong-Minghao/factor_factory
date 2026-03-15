"""
辅助工具函数
提供通用的辅助功能
"""
import pandas as pd
import numpy as np
from typing import Union, List, Tuple
from pathlib import Path


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def standardize_code(code: str) -> str:
    """
    标准化股票代码格式

    Args:
        code: 股票代码（如：000001.SZ, 600000.SH, 000001, 600000）

    Returns:
        标准化后的股票代码（如：000001.SZ, 600000.SH）
    """
    code = code.strip().upper()

    # 如果已经包含后缀，直接返回
    if "." in code:
        return code

    # 根据代码规则添加后缀
    if code.startswith("6") or code.startswith("5"):
        # 上海证券交易所
        return f"{code}.SH"
    elif code.startswith("0") or code.startswith("3") or code.startswith("8"):
        # 深圳证券交易所
        return f"{code}.SZ"
    else:
        return code


def remove_suffix(code: str) -> str:
    """
    移除股票代码后缀

    Args:
        code: 股票代码（如：000001.SZ）

    Returns:
        不含后缀的股票代码（如：000001）
    """
    return code.split(".")[0]


def parse_date(date_input: Union[str, pd.Timestamp, np.datetime64]) -> str:
    """
    解析并标准化日期格式为YYYY-MM-DD

    Args:
        date_input: 日期输入

    Returns:
        标准化的日期字符串
    """
    if isinstance(date_input, str):
        return date_input
    elif isinstance(date_input, pd.Timestamp):
        return date_input.strftime("%Y-%m-%d")
    elif isinstance(date_input, np.datetime64):
        return pd.Timestamp(date_input).strftime("%Y-%m-%d")
    else:
        raise ValueError(f"不支持的日期类型: {type(date_input)}")


def calculate_return(prices: pd.Series, periods: int = 1) -> pd.Series:
    """
    计算收益率

    Args:
        prices: 价格序列
        periods: 周期

    Returns:
        收益率序列
    """
    return prices.pct_change(periods)


def calculate_log_return(prices: pd.Series, periods: int = 1) -> pd.Series:
    """
    计算对数收益率

    Args:
        prices: 价格序列
        periods: 周期

    Returns:
        对数收益率序列
    """
    return np.log(prices / prices.shift(periods))


def calculate_volatility(
    returns: pd.Series, window: int = 20, annualize: bool = True
) -> pd.Series:
    """
    计算滚动波动率

    Args:
        returns: 收益率序列
        window: 窗口大小
        annualize: 是否年化

    Returns:
        波动率序列
    """
    vol = returns.rolling(window=window).std()

    if annualize:
        # 假设一年有252个交易日
        vol = vol * np.sqrt(252)

    return vol


def calculate_sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0, annualize: bool = True
) -> float:
    """
    计算夏普比率

    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率
        annualize: 是否年化

    Returns:
        夏普比率
    """
    if returns.std() == 0:
        return 0.0

    sharpe = (returns.mean() - risk_free_rate) / returns.std()

    if annualize:
        # 假设一年有252个交易日
        sharpe = sharpe * np.sqrt(252)

    return sharpe


def calculate_max_drawdown(prices: pd.Series) -> Tuple[float, pd.Timestamp]:
    """
    计算最大回撤

    Args:
        prices: 价格或净值序列

    Returns:
        (最大回撤, 回撤日期)
    """
    # 计算累计收益
    cum_returns = (1 + prices.pct_change()).cumprod()

    # 计算滚动最大值
    rolling_max = cum_returns.expanding().max()

    # 计算回撤
    drawdown = (cum_returns - rolling_max) / rolling_max

    # 找到最大回撤
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin()

    return max_dd, max_dd_date


def winsorize(
    series: pd.Series, limits: Tuple[float, float] = (0.01, 0.99)
) -> pd.Series:
    """
    去极值处理

    Args:
        series: 数据序列
        limits: 分位数上下限

    Returns:
        去极值后的序列
    """
    lower, upper = np.quantile(series, limits)

    # 将超出范围的值替换为边界值
    series = series.clip(lower=lower, upper=upper)

    return series


def standardize(series: pd.Series) -> pd.Series:
    """
    标准化处理

    Args:
        series: 数据序列

    Returns:
        标准化后的序列（均值0，标准差1）
    """
    return (series - series.mean()) / series.std()


def neutralize(
    factor: pd.DataFrame, industry: pd.DataFrame, market_cap: pd.DataFrame
) -> pd.DataFrame:
    """
    行业和市值中性化处理

    Args:
        factor: 因子值 DataFrame，index为日期，columns为股票代码
        industry: 行业分类 DataFrame，index为日期，columns为股票代码
        market_cap: 市值 DataFrame，index为日期，columns为股票代码

    Returns:
        中性化后的因子值
    """
    from sklearn.linear_model import LinearRegression

    result = factor.copy()

    for date in factor.index:
        factor_values = factor.loc[date].dropna()
        industry_values = industry.loc[date][factor_values.index]
        market_cap_values = market_cap.loc[date][factor_values.index]

        # 构造特征矩阵
        X = pd.get_dummies(industry_values)
        X["log_cap"] = np.log(market_cap_values)

        # 线性回归
        model = LinearRegression()
        model.fit(X, factor_values)

        # 残差作为中性化后的因子值
        residual = factor_values - model.predict(X)
        result.loc[date, residual.index] = residual

    return result


def resample_to_month(df: pd.DataFrame, method: str = "last") -> pd.DataFrame:
    """
    将数据重采样到月度频率

    Args:
        df: DataFrame，index为日期
        method: 重采样方法 ('last', 'first', 'mean')

    Returns:
        月度数据
    """
    if method == "last":
        return df.resample("M").last()
    elif method == "first":
        return df.resample("M").first()
    elif method == "mean":
        return df.resample("M").mean()
    else:
        raise ValueError(f"不支持的重采样方法: {method}")


def align_dataframes(
    dfs: List[pd.DataFrame], join: str = "inner"
) -> List[pd.DataFrame]:
    """
    对齐多个DataFrame的索引和列

    Args:
        dfs: DataFrame列表
        join: 连接方式 ('inner', 'outer', 'left', 'right')

    Returns:
        对齐后的DataFrame列表
    """
    if not dfs:
        return []

    # 对齐索引
    index = dfs[0].index
    for df in dfs[1:]:
        if join == "inner":
            index = index.intersection(df.index)
        elif join == "outer":
            index = index.union(df.index)
        elif join == "left":
            pass
        elif join == "right":
            index = df.index

    # 对齐列
    columns = dfs[0].columns
    for df in dfs[1:]:
        if join == "inner":
            columns = columns.intersection(df.columns)
        elif join == "outer":
            columns = columns.union(df.columns)
        elif join == "left":
            pass
        elif join == "right":
            columns = df.columns

    # 对齐所有DataFrame
    aligned_dfs = []
    for df in dfs:
        aligned_df = df.reindex(index=index, columns=columns)
        aligned_dfs.append(aligned_df)

    return aligned_dfs


def format_number(num: float, precision: int = 2) -> str:
    """
    格式化数字显示

    Args:
        num: 数字
        precision: 小数位数

    Returns:
        格式化后的字符串
    """
    if abs(num) >= 1e8:
        return f"{num/1e8:.{precision}f}亿"
    elif abs(num) >= 1e4:
        return f"{num/1e4:.{precision}f}万"
    else:
        return f"{num:.{precision}f}"


def format_percent(num: float, precision: int = 2) -> str:
    """
    格式化百分比显示

    Args:
        num: 数字（小数形式，如0.05表示5%）
        precision: 小数位数

    Returns:
        格式化后的字符串
    """
    return f"{num * 100:.{precision}f}%"
