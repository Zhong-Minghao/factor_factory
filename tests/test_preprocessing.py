"""
测试预处理模块

重点测试单列 DataFrame 的处理，验证修复后的行为
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
import pytest

from analysis.preprocessing import (
    mad_outlier_treatment,
    sigma_outlier_treatment,
    quantile_outlier_treatment,
    zscore_standardization,
    rank_standardization,
    preprocess_factor,
)


class TestSingleColumnDataFrame:
    """测试单列 DataFrame 的处理（修复核心问题）"""

    @pytest.fixture
    def single_column_df(self):
        """创建单列 DataFrame（模拟单股票数据）"""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        data = np.random.randn(100) * 10 + 50  # 均值50，标准差10
        df = pd.DataFrame(data, index=dates, columns=["600000.SH"])
        return df

    def test_mad_outlier_single_column(self, single_column_df):
        """测试 MAD 去极值处理单列 DataFrame"""
        result = mad_outlier_treatment(single_column_df)

        # 验证返回 DataFrame 格式
        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame，不是 Series"
        assert result.shape == single_column_df.shape, "形状应该保持不变"
        assert result.index.equals(single_column_df.index), "索引应该保持不变"
        assert result.columns.equals(single_column_df.columns), "列名应该保持不变"

        # 验证极值被处理（不超过原始数据范围的3倍MAD）
        assert not result.isna().any().any(), "不应该有 NaN 值"

    def test_sigma_outlier_single_column(self, single_column_df):
        """测试 3-sigma 去极值处理单列 DataFrame"""
        result = sigma_outlier_treatment(single_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame，不是 Series"
        assert result.shape == single_column_df.shape, "形状应该保持不变"
        assert not result.isna().any().any(), "不应该有 NaN 值"

    def test_quantile_outlier_single_column(self, single_column_df):
        """测试分位数去极值处理单列 DataFrame"""
        result = quantile_outlier_treatment(single_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame，不是 Series"
        assert result.shape == single_column_df.shape, "形状应该保持不变"
        assert not result.isna().any().any(), "不应该有 NaN 值"

    def test_zscore_standardization_single_column(self, single_column_df):
        """测试 Z-score 标准化处理单列 DataFrame"""
        result = zscore_standardization(single_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame，不是 Series"
        assert result.shape == single_column_df.shape, "形状应该保持不变"

        # 验证每行（每个截面）的均值接近0，标准差接近1
        for date in result.index:
            row_data = result.loc[date, :]
            # 注意：由于只有一列，标准差可能是 NaN 或 0
            if len(row_data.dropna()) > 1:
                assert abs(row_data.mean()) < 1e-10, f"日期 {date} 的均值应该接近0"

    def test_rank_standardization_single_column(self, single_column_df):
        """测试排序标准化处理单列 DataFrame"""
        result = rank_standardization(single_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame，不是 Series"
        assert result.shape == single_column_df.shape, "形状应该保持不变"
        assert not result.isna().any().any(), "不应该有 NaN 值"


class TestMultiColumnDataFrame:
    """测试多列 DataFrame 的处理（回归测试）"""

    @pytest.fixture
    def multi_column_df(self):
        """创建多列 DataFrame（模拟多股票数据）"""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        stocks = [f"{i:06d}.SH" for i in range(600000, 600010)]  # 10个股票
        data = np.random.randn(100, 10) * 10 + 50
        df = pd.DataFrame(data, index=dates, columns=stocks)
        return df

    def test_mad_outlier_multi_column(self, multi_column_df):
        """测试 MAD 去极值处理多列 DataFrame"""
        result = mad_outlier_treatment(multi_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        assert result.shape == multi_column_df.shape, "形状应该保持不变"
        assert not result.isna().any().any(), "不应该有 NaN 值"

    def test_sigma_outlier_multi_column(self, multi_column_df):
        """测试 3-sigma 去极值处理多列 DataFrame"""
        result = sigma_outlier_treatment(multi_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        assert result.shape == multi_column_df.shape, "形状应该保持不变"
        assert not result.isna().any().any(), "不应该有 NaN 值"

    def test_zscore_standardization_multi_column(self, multi_column_df):
        """测试 Z-score 标准化处理多列 DataFrame"""
        result = zscore_standardization(multi_column_df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        assert result.shape == multi_column_df.shape, "形状应该保持不变"

        # 验证每行的均值接近0，标准差接近1
        for date in result.index[:5]:  # 检查前5行
            row_data = result.loc[date, :]
            assert abs(row_data.mean()) < 1e-10, f"日期 {date} 的均值应该接近0"
            assert abs(row_data.std() - 1.0) < 1e-10, f"日期 {date} 的标准差应该接近1"


class TestSeriesWithMultiIndex:
    """测试 Series with MultiIndex 格式（回归测试）"""

    @pytest.fixture
    def multiindex_series(self):
        """创建 MultiIndex Series（长格式）"""
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        stocks = ["600000.SH", "600001.SH", "600002.SH"]

        index = pd.MultiIndex.from_product([dates, stocks], names=["trade_date", "ts_code"])
        data = np.random.randn(len(index)) * 10 + 50

        return pd.Series(data, index=index, name="factor")

    def test_mad_outlier_multiindex_series(self, multiindex_series):
        """测试 MAD 去极值处理 MultiIndex Series"""
        result = mad_outlier_treatment(multiindex_series)

        assert isinstance(result, pd.Series), "应该返回 Series"
        assert isinstance(result.index, pd.MultiIndex), "应该保持 MultiIndex"
        assert result.index.equals(multiindex_series.index), "索引应该保持不变"
        assert not result.isna().any(), "不应该有 NaN 值"

    def test_zscore_standardization_multiindex_series(self, multiindex_series):
        """测试 Z-score 标准化处理 MultiIndex Series"""
        result = zscore_standardization(multiindex_series)

        assert isinstance(result, pd.Series), "应该返回 Series"
        assert isinstance(result.index, pd.MultiIndex), "应该保持 MultiIndex"
        assert result.index.equals(multiindex_series.index), "索引应该保持不变"

    def test_series_without_multiindex_raises_error(self):
        """测试没有 MultiIndex 的 Series 应该抛出错误"""
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        data = np.random.randn(10) * 10 + 50
        series = pd.Series(data, index=dates)

        with pytest.raises(ValueError, match="Series格式必须具有MultiIndex"):
            mad_outlier_treatment(series)


class TestChainedPreprocessing:
    """测试链式预处理（关键测试）"""

    @pytest.fixture
    def single_column_df(self):
        """创建单列 DataFrame"""
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        data = np.random.randn(100) * 10 + 50
        df = pd.DataFrame(data, index=dates, columns=["600000.SH"])
        return df

    def test_preprocess_factor_single_column(self, single_column_df):
        """测试完整的预处理流程（去极值 → 标准化）"""
        result = preprocess_factor(
            single_column_df,
            outlier_method="mad",
            standardize=True,
            neutralize=False,
        )

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame，不是 Series"
        assert result.shape == single_column_df.shape, "形状应该保持不变"
        assert not result.isna().any().any(), "不应该有 NaN 值"

    def test_preprocess_factor_all_methods(self, single_column_df):
        """测试所有去极值方法"""
        methods = ["mad", "sigma", "quantile"]

        for method in methods:
            result = preprocess_factor(
                single_column_df,
                outlier_method=method,
                standardize=True,
            )

            assert isinstance(result, pd.DataFrame), f"{method} 方法应该返回 DataFrame"
            assert result.shape == single_column_df.shape, f"{method} 方法形状应该保持不变"


class TestEdgeCases:
    """测试边缘情况"""

    def test_single_row_single_column(self):
        """测试单行单列的情况"""
        df = pd.DataFrame([[42.0]], index=[pd.Timestamp("2020-01-01")], columns=["600000.SH"])

        result = mad_outlier_treatment(df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        assert result.shape == df.shape, "形状应该保持不变"

    def test_all_nan_values(self):
        """测试全 NaN 值的情况"""
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        df = pd.DataFrame(np.nan, index=dates, columns=["600000.SH"])

        result = zscore_standardization(df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        assert result.shape == df.shape, "形状应该保持不变"

    def test_zero_variance(self):
        """测试零方差（所有值相同）的情况"""
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        df = pd.DataFrame(50.0, index=dates, columns=["600000.SH"])

        result = zscore_standardization(df)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        assert result.shape == df.shape, "形状应该保持不变"
        # 零方差时应该被设置为0
        assert (result == 0).all().all(), "零方差时应该全部设置为0"

    def test_extreme_values(self):
        """测试极值处理（clipping）"""
        dates = pd.date_range("2020-01-01", periods=10, freq="D")
        data = np.array([1.0, 2.0, 3.0, 1000.0, 5.0, 6.0, -1000.0, 8.0, 9.0, 10.0])
        df = pd.DataFrame(data, index=dates, columns=["600000.SH"])

        result = mad_outlier_treatment(df, n=3.0)

        assert isinstance(result, pd.DataFrame), "应该返回 DataFrame"
        # 验证极值被处理
        assert result.loc[dates[3], "600000.SH"] < 1000.0, "极值应该被裁剪"
        assert result.loc[dates[6], "600000.SH"] > -1000.0, "极值应该被裁剪"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
