"""
IC 计算验证测试
测试改进后的数据格式验证和错误提示
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.ic_ir import ICAnalyzer


class TestLongFormatValidation:
    """测试长表格式的验证"""

    def test_validate_long_format_price_data(self):
        """测试长表格式 price_data 的验证"""
        analyzer = ICAnalyzer()

        # 创建长表格式数据
        dates = pd.date_range('2024-01-01', periods=10)
        price_data = pd.DataFrame({
            'open': np.random.randn(10),
            'high': np.random.randn(10),
            'low': np.random.randn(10),
            'close': np.random.randn(10),
        }, index=dates)

        factor_data = pd.DataFrame(
            np.random.randn(10, 3),
            index=dates,
            columns=['000001.SZ', '000002.SZ', '600000.SH']
        )

        # 应该抛出 ValueError，并包含解决方案
        with pytest.raises(ValueError) as exc_info:
            analyzer.compute_daily_ic(factor_data, price_data, period=5)

        error_msg = str(exc_info.value)
        assert "长表格式" in error_msg
        assert "解决方案" in error_msg
        assert "pivot" in error_msg

    def test_validate_long_format_factor_data(self):
        """测试长表格式 factor_data 的验证"""
        analyzer = ICAnalyzer()

        # 创建长表格式数据
        dates = pd.date_range('2024-01-01', periods=10)
        factor_data = pd.DataFrame({
            'open': np.random.randn(10),
            'close': np.random.randn(10),
        }, index=dates)

        codes = ['000001.SZ', '000002.SZ', '600000.SH']
        price_data = pd.DataFrame(
            100 + np.random.randn(10, 3),
            index=dates,
            columns=codes
        )

        # 应该抛出 ValueError
        with pytest.raises(ValueError) as exc_info:
            analyzer.compute_daily_ic(factor_data, price_data, period=5)

        error_msg = str(exc_info.value)
        assert "factor_data 是长表格式" in error_msg


class TestStockCodeMismatch:
    """测试股票代码不匹配的验证"""

    def test_validate_mismatched_stocks(self):
        """测试股票代码不匹配的验证"""
        analyzer = ICAnalyzer()

        dates = pd.date_range('2024-01-01', periods=10)

        # 创建股票代码不匹配的数据
        factor_data = pd.DataFrame(
            np.random.randn(10, 3),
            index=dates,
            columns=['000001.SZ', '000002.SZ', '000003.SZ']
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(10, 3),
            index=dates,
            columns=['600000.SH', '600001.SH', '600002.SH']
        )

        # 应该抛出 ValueError
        with pytest.raises(ValueError) as exc_info:
            analyzer.compute_daily_ic(factor_data, price_data, period=5)

        error_msg = str(exc_info.value)
        assert "股票代码匹配不足" in error_msg

    def test_validate_single_column(self):
        """测试只有一列数据的验证"""
        analyzer = ICAnalyzer()

        dates = pd.date_range('2024-01-01', periods=10)
        codes = ['000001.SZ']

        factor_data = pd.DataFrame(
            np.random.randn(10, 1),
            index=dates,
            columns=codes
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(10, 1),
            index=dates,
            columns=codes
        )

        # 应该抛出 ValueError（至少需要 2 列或 3 个共同股票）
        with pytest.raises(ValueError) as exc_info:
            analyzer.compute_daily_ic(factor_data, price_data, period=5)

        error_msg = str(exc_info.value)
        assert "股票代码匹配不足" in error_msg


class TestDateRangeMismatch:
    """测试日期范围不匹配的验证"""

    def test_validate_no_common_dates(self):
        """测试没有共同日期的验证"""
        analyzer = ICAnalyzer()

        codes = ['000001.SZ', '000002.SZ', '600000.SH']

        # 创建没有共同日期的数据
        factor_dates = pd.date_range('2024-01-01', periods=10)
        price_dates = pd.date_range('2024-02-01', periods=10)

        factor_data = pd.DataFrame(
            np.random.randn(10, 3),
            index=factor_dates,
            columns=codes
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(10, 3),
            index=price_dates,
            columns=codes
        )

        # 应该抛出 ValueError
        with pytest.raises(ValueError) as exc_info:
            analyzer.compute_daily_ic(factor_data, price_data, period=5)

        error_msg = str(exc_info.value)
        assert "没有共同的日期" in error_msg

    def test_validate_partial_date_overlap(self):
        """测试部分日期重叠的情况"""
        analyzer = ICAnalyzer()

        codes = ['000001.SZ', '000002.SZ', '600000.SH']

        # 创建部分重叠的日期
        factor_dates = pd.date_range('2024-01-01', periods=20)
        price_dates = pd.date_range('2024-01-10', periods=20)

        factor_data = pd.DataFrame(
            np.random.randn(20, 3),
            index=factor_dates,
            columns=codes
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(20, 3),
            index=price_dates,
            columns=codes
        )

        # 应该成功计算（使用重叠的日期）
        ic_series = analyzer.compute_daily_ic(factor_data, price_data, period=5)

        # 验证结果
        assert isinstance(ic_series, pd.Series)
        # 由于 period=5，有效日期应该更少
        assert len(ic_series) < 10  # 粗略估计


class TestFutureReturnsCalculation:
    """测试简化的收益率计算"""

    def test_compute_future_returns(self):
        """测试简化的收益率计算"""
        analyzer = ICAnalyzer()

        dates = pd.date_range('2024-01-01', periods=10)
        codes = ['000001.SZ', '000002.SZ', '600000.SH']

        price_data = pd.DataFrame(
            100 + np.random.randn(10, 3),
            index=dates,
            columns=codes
        )

        future_returns = analyzer._compute_future_returns(price_data, period=5)

        # 验证形状
        assert future_returns.shape == (5, 3)  # 10 - 5 = 5

        # 验证没有 NaN（最后 5 行被丢弃）
        assert not future_returns.isna().any().any()

    def test_compute_future_returns_period_1(self):
        """测试 period=1 的收益率计算"""
        analyzer = ICAnalyzer()

        dates = pd.date_range('2024-01-01', periods=10)
        codes = ['000001.SZ', '000002.SZ']

        price_data = pd.DataFrame(
            100 + np.random.randn(10, 2),
            index=dates,
            columns=codes
        )

        future_returns = analyzer._compute_future_returns(price_data, period=1)

        # 验证形状
        assert future_returns.shape == (9, 2)  # 10 - 1 = 9

    def test_compute_future_returns_large_period(self):
        """测试较大 period 的收益率计算"""
        analyzer = ICAnalyzer()

        dates = pd.date_range('2024-01-01', periods=20)
        codes = ['000001.SZ', '000002.SZ']

        price_data = pd.DataFrame(
            100 + np.random.randn(20, 2),
            index=dates,
            columns=codes
        )

        future_returns = analyzer._compute_future_returns(price_data, period=15)

        # 验证形状
        assert future_returns.shape == (5, 2)  # 20 - 15 = 5


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_wide_format_still_works(self):
        """测试宽表格式的向后兼容性"""
        # 使用旧 API 应该仍然有效
        dates = pd.date_range('2024-01-01', periods=100)
        codes = [f'{str(i).zfill(6)}.SZ' for i in range(1, 51)]

        factor_data = pd.DataFrame(
            np.random.randn(100, 50),
            index=dates,
            columns=codes
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(100, 50),
            index=dates,
            columns=codes
        )

        # 旧方式
        analyzer = ICAnalyzer(ic_type="rank")
        ic_series = analyzer.compute_daily_ic(factor_data, price_data, period=5)

        # 验证
        assert len(ic_series) > 0
        assert isinstance(ic_series, pd.Series)

    def test_different_ic_types(self):
        """测试不同的 IC 类型"""
        dates = pd.date_range('2024-01-01', periods=50)
        codes = ['000001.SZ', '000002.SZ', '600000.SH', '600001.SH', '600002.SH']

        factor_data = pd.DataFrame(
            np.random.randn(50, 5),
            index=dates,
            columns=codes
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(50, 5),
            index=dates,
            columns=codes
        )

        # 测试 rank IC
        analyzer_rank = ICAnalyzer(ic_type="rank", preprocess=False)
        ic_rank = analyzer_rank.compute_daily_ic(factor_data, price_data, period=5)

        assert len(ic_rank) > 0

        # 测试 pearson IC
        analyzer_pearson = ICAnalyzer(ic_type="pearson", preprocess=False)
        ic_pearson = analyzer_pearson.compute_daily_ic(factor_data, price_data, period=5)

        assert len(ic_pearson) > 0

    def test_preprocess_parameter(self):
        """测试 preprocess 参数"""
        dates = pd.date_range('2024-01-01', periods=50)
        codes = ['000001.SZ', '000002.SZ', '600000.SH']

        factor_data = pd.DataFrame(
            np.random.randn(50, 3),
            index=dates,
            columns=codes
        )

        price_data = pd.DataFrame(
            100 + np.random.randn(50, 3),
            index=dates,
            columns=codes
        )

        # 测试 preprocess=True
        analyzer_with_preprocess = ICAnalyzer(preprocess=True)
        ic_with = analyzer_with_preprocess.compute_daily_ic(factor_data, price_data, period=5)

        assert len(ic_with) > 0

        # 测试 preprocess=False
        analyzer_without_preprocess = ICAnalyzer(preprocess=False)
        ic_without = analyzer_without_preprocess.compute_daily_ic(factor_data, price_data, period=5)

        assert len(ic_without) > 0


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_dataframe(self):
        """测试空 DataFrame"""
        analyzer = ICAnalyzer()

        empty_df = pd.DataFrame()

        dates = pd.date_range('2024-01-01', periods=10)
        codes = ['000001.SZ', '000002.SZ']
        valid_df = pd.DataFrame(
            np.random.randn(10, 2),
            index=dates,
            columns=codes
        )

        # factor_data 为空
        with pytest.raises(ValueError, match="factor_data 不能为空"):
            analyzer.compute_daily_ic(empty_df, valid_df, period=5)

        # price_data 为空
        with pytest.raises(ValueError, match="price_data 不能为空"):
            analyzer.compute_daily_ic(valid_df, empty_df, period=5)

    def test_non_dataframe_input(self):
        """测试非 DataFrame 输入"""
        analyzer = ICAnalyzer()

        dates = pd.date_range('2024-01-01', periods=10)
        codes = ['000001.SZ', '000002.SZ']
        valid_df = pd.DataFrame(
            np.random.randn(10, 2),
            index=dates,
            columns=codes
        )

        # factor_data 不是 DataFrame
        with pytest.raises(ValueError, match="factor_data 必须是 DataFrame 类型"):
            analyzer.compute_daily_ic(None, valid_df, period=5)

        # price_data 不是 DataFrame
        with pytest.raises(ValueError, match="price_data 必须是 DataFrame 类型"):
            analyzer.compute_daily_ic(valid_df, "not a dataframe", period=5)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
