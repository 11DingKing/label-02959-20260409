"""
Pytest 配置和共享 fixtures
"""

import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from typing import Generator
from datetime import datetime, timedelta
import random

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_handler import DataHandler, SplitConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """创建示例数据框（含全部业务字段）"""
    return pd.DataFrame({
        'wm_poi_id': [f'POI{str(i).zfill(8)}' for i in range(1, 101)],
        'provider_id': [f'PRV{str(i % 10).zfill(4)}' if i % 5 != 0 else '' for i in range(1, 101)],
        'lead_tag': ['新客' if i % 2 == 0 else '老客' for i in range(1, 101)],
        'status': ['待联系' if i % 3 == 0 else '已联系' if i % 3 == 1 else '已流失' for i in range(1, 101)],
        'modifier': [f'user_{i % 5}' for i in range(1, 101)],
        'ctime': [int((datetime.now() - timedelta(days=random.randint(1, 365))).timestamp()) for _ in range(100)],
    })


@pytest.fixture
def sample_excel_file(temp_dir: Path, sample_dataframe: pd.DataFrame) -> Path:
    """创建示例 Excel 文件"""
    file_path = temp_dir / "test_data.xlsx"
    sample_dataframe.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_csv_file(temp_dir: Path, sample_dataframe: pd.DataFrame) -> Path:
    """创建示例 CSV 文件"""
    file_path = temp_dir / "test_data.csv"
    sample_dataframe.to_csv(file_path, index=False, encoding='utf-8')
    return file_path


@pytest.fixture
def sample_csv_file_gbk(temp_dir: Path, sample_dataframe: pd.DataFrame) -> Path:
    """创建 GBK 编码的 CSV 文件"""
    file_path = temp_dir / "test_data_gbk.csv"
    sample_dataframe.to_csv(file_path, index=False, encoding='gbk')
    return file_path


@pytest.fixture
def invalid_excel_file(temp_dir: Path) -> Path:
    """创建缺少必需列的 Excel 文件"""
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['a', 'b', 'c']
    })
    file_path = temp_dir / "invalid_data.xlsx"
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def data_handler() -> DataHandler:
    """创建 DataHandler 实例"""
    return DataHandler()


@pytest.fixture
def loaded_handler(data_handler: DataHandler, sample_excel_file: Path) -> DataHandler:
    """创建已加载数据的 DataHandler"""
    data_handler.load_file(str(sample_excel_file))
    return data_handler
