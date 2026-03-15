"""
量化因子工厂安装脚本
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="factor-factory",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="个人量化研究用因子工厂系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/factor-factory",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "h5py>=3.8.0",
        "pyarrow>=12.0.0",
        "duckdb>=0.8.0",
        "tushare>=1.2.73",
        "akshare>=1.9.0",
        "baostock>=0.8.8",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "statsmodels>=0.14.0",
        "plotly>=5.14.0",
        "matplotlib>=3.7.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "jupyter": [
            "jupyter>=1.0.0",
            "ipykernel>=6.25.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "factor-cli=cli.main:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
