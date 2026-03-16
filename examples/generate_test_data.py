"""
生成测试数据
用于演示和测试因子系统
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


def generate_stock_data(
    n_days: int = 250,
    start_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0005,
    symbol: str = "TEST001",
    start_date: Optional[str] = None
) -> pd.DataFrame:
    """
    生成模拟股票数据

    Args:
        n_days: 生成天数（默认250个交易日，约1年）
        start_price: 起始价格
        volatility: 波动率（标准差）
        trend: 趋势（每天的平均涨跌幅）
        symbol: 股票代码
        start_date: 开始日期（格式：YYYY-MM-DD）

    Returns:
        包含OHLCV数据的DataFrame
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=n_days * 2)).strftime("%Y-%m-%d")

    # 生成日期序列（只包含工作日）
    dates = pd.bdate_range(start=start_date, periods=n_days)

    # 生成价格数据（几何布朗运动）
    returns = np.random.normal(trend, volatility, n_days)
    prices = start_price * (1 + returns).cumprod()

    # 生成OHLC数据
    data = []
    for i, price in enumerate(prices):
        # 日内波动
        daily_volatility = price * volatility * 0.5

        high = price + abs(np.random.normal(0, daily_volatility))
        low = price - abs(np.random.normal(0, daily_volatility))
        open_price = low + (high - low) * np.random.random()
        close_price = price

        # 确保逻辑正确
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)

        # 生成成交量和成交额
        volume = np.random.randint(1000000, 50000000)  # 100万到5000万股
        amount = volume * close_price * (0.98 + 0.04 * np.random.random())  # 成交额

        data.append({
            'symbol': symbol,
            'trade_date': dates[i].strftime('%Y%m%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close_price, 2),
            'volume': int(volume),
            'amount': round(amount, 2)
        })

    df = pd.DataFrame(data)
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

    return df


def generate_multi_stock_data(
    symbols: list = None,
    n_days: int = 250,
    start_date: Optional[str] = None
) -> pd.DataFrame:
    """
    生成多只股票的数据

    Args:
        symbols: 股票代码列表
        n_days: 生成天数
        start_date: 开始日期

    Returns:
        包含多只股票数据的DataFrame
    """
    if symbols is None:
        symbols = ['STOCK001', 'STOCK002', 'STOCK003', 'STOCK004', 'STOCK005']

    all_data = []
    for symbol in symbols:
        # 每只股票有不同的特性
        start_price = np.random.uniform(50, 200)
        volatility = np.random.uniform(0.015, 0.03)
        trend = np.random.uniform(-0.001, 0.002)

        stock_data = generate_stock_data(
            n_days=n_days,
            start_price=start_price,
            volatility=volatility,
            trend=trend,
            symbol=symbol,
            start_date=start_date
        )
        all_data.append(stock_data)

    return pd.concat(all_data, ignore_index=True)


def save_test_data(df: pd.DataFrame, filename: str):
    """保存测试数据到文件"""
    filepath = f"data/{filename}"
    df.to_csv(filepath, index=False, encoding='utf-8')
    print(f"✓ 数据已保存到: {filepath}")
    print(f"  共 {len(df)} 行")
    print(f"  日期范围: {df['trade_date'].min()} 到 {df['trade_date'].max()}")


if __name__ == "__main__":
    print("=" * 60)
    print("生成测试数据")
    print("=" * 60)

    # 1. 生成单只股票数据
    print("\n[1] 生成单只股票数据（250个交易日）...")
    single_stock = generate_stock_data(
        n_days=250,
        start_price=100.0,
        volatility=0.02,
        symbol="TEST001"
    )
    save_test_data(single_stock, "test_single_stock.csv")

    # 2. 生成多只股票数据
    print("\n[2] 生成多只股票数据（5只股票，各250个交易日）...")
    multi_stock = generate_multi_stock_data(
        symbols=['STOCK001', 'STOCK002', 'STOCK003', 'STOCK004', 'STOCK005'],
        n_days=250
    )
    save_test_data(multi_stock, "test_multi_stock.csv")

    # 3. 显示数据样本
    print("\n[3] 数据样本:")
    print(single_stock.head(10))

    print("\n[4] 数据统计:")
    print(single_stock.describe())

    print("\n" + "=" * 60)
    print("✅ 测试数据生成完成！")
    print("=" * 60)
