"""
DataHandler 单元测试
测试数据处理模块的所有功能
"""

import pytest
import pandas as pd
from pathlib import Path

from src.data_handler import DataHandler, SplitConfig, DataStats, SplitMode


class TestDataHandlerInit:
    """测试 DataHandler 初始化"""
    
    def test_init(self, data_handler: DataHandler):
        """测试初始化状态"""
        assert data_handler is not None
        assert data_handler.is_loaded is False
        assert data_handler.dataframe is None
    
    def test_supported_formats(self, data_handler: DataHandler):
        """测试支持的文件格式"""
        assert '.xlsx' in data_handler.SUPPORTED_FORMATS
        assert '.xls' in data_handler.SUPPORTED_FORMATS
        assert '.csv' in data_handler.SUPPORTED_FORMATS


class TestLoadFile:
    """测试文件加载功能"""
    
    def test_load_excel_success(self, data_handler: DataHandler, sample_excel_file: Path):
        """测试成功加载 Excel 文件"""
        success, msg = data_handler.load_file(str(sample_excel_file))
        
        assert success is True
        assert "成功加载" in msg
        assert "100" in msg
        assert data_handler.is_loaded is True
        assert data_handler.dataframe is not None
        assert len(data_handler.dataframe) == 100
    
    def test_load_csv_success(self, data_handler: DataHandler, sample_csv_file: Path):
        """测试成功加载 CSV 文件"""
        success, msg = data_handler.load_file(str(sample_csv_file))
        
        assert success is True
        assert data_handler.is_loaded is True
        assert len(data_handler.dataframe) == 100
    
    def test_load_csv_gbk_success(self, data_handler: DataHandler, sample_csv_file_gbk: Path):
        """测试成功加载 GBK 编码的 CSV 文件"""
        success, msg = data_handler.load_file(str(sample_csv_file_gbk))
        
        assert success is True
        assert data_handler.is_loaded is True
    
    def test_load_nonexistent_file(self, data_handler: DataHandler):
        """测试加载不存在的文件"""
        success, msg = data_handler.load_file("/nonexistent/path/file.xlsx")
        
        assert success is False
        assert "不存在" in msg
        assert data_handler.is_loaded is False
    
    def test_load_unsupported_format(self, data_handler: DataHandler, temp_dir: Path):
        """测试加载不支持的文件格式"""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("test content")
        
        success, msg = data_handler.load_file(str(txt_file))
        
        assert success is False
        assert "不支持" in msg
    
    def test_load_missing_required_column(self, data_handler: DataHandler, invalid_excel_file: Path):
        """测试加载缺少必需列的文件"""
        success, msg = data_handler.load_file(str(invalid_excel_file))
        
        assert success is False
        assert "wm_poi_id" in msg


class TestGetStats:
    """测试统计功能"""
    
    def test_get_stats_not_loaded(self, data_handler: DataHandler):
        """测试未加载数据时获取统计"""
        stats = data_handler.get_stats()
        assert stats is None
    
    def test_get_stats_success(self, loaded_handler: DataHandler):
        """测试成功获取统计信息"""
        stats = loaded_handler.get_stats()
        
        assert stats is not None
        assert isinstance(stats, DataStats)
        assert stats.total_rows == 100
        assert stats.wm_poi_id_count == 100  # 每个 POI ID 都是唯一的
        assert 'wm_poi_id' in stats.columns
        assert 'provider_id' in stats.columns


class TestGetPreview:
    """测试预览功能"""
    
    def test_get_preview_not_loaded(self, data_handler: DataHandler):
        """测试未加载数据时获取预览"""
        preview = data_handler.get_preview()
        assert preview is None
    
    def test_get_preview_default(self, loaded_handler: DataHandler):
        """测试默认预览行数"""
        preview = loaded_handler.get_preview()
        
        assert preview is not None
        assert len(preview) == 10
    
    def test_get_preview_custom_rows(self, loaded_handler: DataHandler):
        """测试自定义预览行数"""
        preview = loaded_handler.get_preview(rows=5)
        
        assert preview is not None
        assert len(preview) == 5


class TestValidateSplitConfig:
    """测试配置验证功能"""
    
    def test_validate_not_loaded(self, data_handler: DataHandler):
        """测试未加载数据时验证"""
        configs = [SplitConfig(count=50, filename="test")]
        valid, msg = data_handler.validate_split_config(configs)
        
        assert valid is False
        assert "导入" in msg
    
    def test_validate_empty_configs(self, loaded_handler: DataHandler):
        """测试空配置"""
        valid, msg = loaded_handler.validate_split_config([])
        
        assert valid is False
        assert "至少" in msg
    
    def test_validate_empty_filename(self, loaded_handler: DataHandler):
        """测试空文件名"""
        configs = [SplitConfig(count=100, filename="")]
        valid, msg = loaded_handler.validate_split_config(configs)
        
        assert valid is False
        assert "文件名" in msg
    
    def test_validate_duplicate_filename(self, loaded_handler: DataHandler):
        """测试重复文件名"""
        configs = [
            SplitConfig(count=50, filename="same_name"),
            SplitConfig(count=50, filename="same_name")
        ]
        valid, msg = loaded_handler.validate_split_config(configs)
        
        assert valid is False
        assert "重复" in msg
    
    def test_validate_count_mismatch(self, loaded_handler: DataHandler):
        """测试数量不匹配"""
        configs = [
            SplitConfig(count=30, filename="file1"),
            SplitConfig(count=30, filename="file2")
        ]
        valid, msg = loaded_handler.validate_split_config(configs)
        
        assert valid is False
        assert "不匹配" in msg
    
    def test_validate_zero_count(self, loaded_handler: DataHandler):
        """测试零数量"""
        configs = [
            SplitConfig(count=0, filename="file1"),
            SplitConfig(count=100, filename="file2")
        ]
        valid, msg = loaded_handler.validate_split_config(configs)
        
        assert valid is False
        assert "大于 0" in msg
    
    def test_validate_success(self, loaded_handler: DataHandler):
        """测试验证成功"""
        configs = [
            SplitConfig(count=30, filename="file1"),
            SplitConfig(count=30, filename="file2"),
            SplitConfig(count=40, filename="file3")
        ]
        valid, msg = loaded_handler.validate_split_config(configs)
        
        assert valid is True
        assert "通过" in msg


class TestSplitAndExport:
    """测试分割导出功能"""
    
    def test_export_single_file(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试导出单个文件"""
        configs = [SplitConfig(count=100, filename="all_data")]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert len(files) == 1
        assert Path(files[0]).exists()
        
        # 验证导出内容
        df = pd.read_excel(files[0])
        assert len(df) == 100
        assert '商家门店id' in df.columns
        assert '服务商id' in df.columns
        # 服务商id 应该为空（Excel 读取后可能是 NaN 或空字符串）
        assert pd.isna(df['服务商id'].iloc[0]) or df['服务商id'].iloc[0] == ''
    
    def test_export_multiple_files(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试导出多个文件"""
        configs = [
            SplitConfig(count=30, filename="part1"),
            SplitConfig(count=30, filename="part2"),
            SplitConfig(count=40, filename="part3")
        ]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert len(files) == 3
        
        # 验证每个文件的行数
        df1 = pd.read_excel(files[0])
        df2 = pd.read_excel(files[1])
        df3 = pd.read_excel(files[2])
        
        assert len(df1) == 30
        assert len(df2) == 30
        assert len(df3) == 40
    
    def test_export_with_progress_callback(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试带进度回调的导出"""
        configs = [
            SplitConfig(count=50, filename="part1"),
            SplitConfig(count=50, filename="part2")
        ]
        output_dir = temp_dir / "output"
        
        progress_calls = []
        
        def progress_callback(current, total, message):
            progress_calls.append((current, total, message))
        
        success, msg, files = loaded_handler.split_and_export(
            configs, str(output_dir), progress_callback
        )
        
        assert success is True
        assert len(progress_calls) >= 2  # 至少有开始和结束的回调
    
    def test_export_auto_add_extension(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试自动添加扩展名"""
        configs = [SplitConfig(count=100, filename="no_extension")]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert files[0].endswith('.xlsx')
    
    def test_export_preserve_extension(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试保留已有扩展名"""
        configs = [SplitConfig(count=100, filename="with_extension.xlsx")]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert files[0].endswith('.xlsx')
        assert not files[0].endswith('.xlsx.xlsx')
    
    def test_export_data_order_preserved(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试数据顺序保持"""
        configs = [
            SplitConfig(count=50, filename="first_half"),
            SplitConfig(count=50, filename="second_half")
        ]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        df1 = pd.read_excel(files[0])
        df2 = pd.read_excel(files[1])
        
        # 第一个文件应该包含 POI00000001 到 POI00000050
        assert df1['商家门店id'].iloc[0] == 'POI00000001'
        assert df1['商家门店id'].iloc[-1] == 'POI00000050'
        
        # 第二个文件应该包含 POI00000051 到 POI00000100
        assert df2['商家门店id'].iloc[0] == 'POI00000051'
        assert df2['商家门店id'].iloc[-1] == 'POI00000100'


class TestClear:
    """测试清除功能"""
    
    def test_clear(self, loaded_handler: DataHandler):
        """测试清除数据"""
        assert loaded_handler.is_loaded is True
        
        loaded_handler.clear()
        
        assert loaded_handler.is_loaded is False
        assert loaded_handler.dataframe is None


class TestValidateColumns:
    """测试字段校验功能"""

    def test_validate_columns_not_loaded(self, data_handler: DataHandler):
        """测试未加载数据时校验"""
        result = data_handler.validate_columns()
        assert result["present"] == []
        assert result["missing"] == []

    def test_validate_columns_all_present(self, loaded_handler: DataHandler):
        """测试所有业务字段都存在"""
        result = loaded_handler.validate_columns()
        present_cols = [p["column"] for p in result["present"]]
        assert "wm_poi_id" in present_cols
        assert "provider_id" in present_cols
        assert "lead_tag" in present_cols
        assert "status" in present_cols
        assert "modifier" in present_cols
        assert len(result["warnings"]) == 0

    def test_validate_columns_missing_fields(self, data_handler: DataHandler, temp_dir: Path):
        """测试缺少部分字段时产生警告"""
        df = pd.DataFrame({
            'wm_poi_id': ['POI001', 'POI002'],
            'other_col': ['a', 'b'],
        })
        file_path = temp_dir / "partial.xlsx"
        df.to_excel(file_path, index=False)
        data_handler.load_file(str(file_path))

        result = data_handler.validate_columns()
        missing_cols = [m["column"] for m in result["missing"]]
        assert "provider_id" in missing_cols
        assert "lead_tag" in missing_cols
        assert len(result["warnings"]) > 0

    def test_validate_columns_date_detection(self, loaded_handler: DataHandler):
        """测试日期字段检测"""
        result = loaded_handler.validate_columns()
        # conftest 的 sample_dataframe 包含 ctime 列
        assert result["date_column"] == "ctime"


class TestDeepAnalysis:
    """测试深度分析功能"""

    def test_stats_has_analysis(self, loaded_handler: DataHandler):
        """测试统计信息包含深度分析"""
        stats = loaded_handler.get_stats()
        assert stats is not None
        assert stats.analysis is not None
        assert "provider_id_empty" in stats.analysis
        assert "status_distribution" in stats.analysis
        assert "date_range" in stats.analysis

    def test_provider_id_empty_count(self, loaded_handler: DataHandler):
        """测试服务商ID空值统计"""
        stats = loaded_handler.get_stats()
        # conftest 中每 5 条有 1 条 provider_id 为空
        assert stats.analysis["provider_id_empty"] == 20

    def test_status_distribution(self, loaded_handler: DataHandler):
        """测试状态分布"""
        stats = loaded_handler.get_stats()
        dist = stats.analysis["status_distribution"]
        assert isinstance(dist, dict)
        assert "待联系" in dist
        assert "已联系" in dist
        assert "已流失" in dist
        assert sum(dist.values()) == 100

    def test_date_range_unix_timestamp(self, loaded_handler: DataHandler):
        """测试 Unix 时间戳日期范围识别"""
        stats = loaded_handler.get_stats()
        date_range = stats.analysis["date_range"]
        assert date_range is not None
        assert date_range["column"] == "ctime"
        # 应该识别为近一年内的日期，不是 1970
        assert "1970" not in date_range["earliest"]
        assert date_range["count"] == 100

    def test_to_dict(self, loaded_handler: DataHandler):
        """测试 DataStats.to_dict()"""
        stats = loaded_handler.get_stats()
        d = stats.to_dict()
        assert "total_rows" in d
        assert "wm_poi_id_count" in d
        assert "columns" in d
        assert "analysis" in d
        assert d["total_rows"] == 100

    def test_no_date_column(self, data_handler: DataHandler, temp_dir: Path):
        """测试无日期列时的分析"""
        df = pd.DataFrame({
            'wm_poi_id': ['POI001', 'POI002'],
            'provider_id': ['PRV001', ''],
        })
        file_path = temp_dir / "no_date.xlsx"
        df.to_excel(file_path, index=False)
        data_handler.load_file(str(file_path))

        stats = data_handler.get_stats()
        assert stats.analysis["date_range"] is None
        assert stats.analysis["provider_id_empty"] == 1


class TestNewFeatures:
    """测试新功能"""

    def test_validate_split_config_with_mode_partial(self, loaded_handler: DataHandler):
        """测试部分导出模式"""
        # 配置总数小于数据总数
        configs = [
            SplitConfig(count=30, filename="part1"),
            SplitConfig(count=30, filename="part2")
        ]
        
        # 使用精确分配模式应该失败
        valid, msg = loaded_handler.validate_split_config(configs)
        assert valid is False
        assert "不匹配" in msg
        
        # 使用部分导出模式应该成功
        valid, msg, calculated_configs = loaded_handler.validate_split_config_with_mode(
            configs, SplitMode.PARTIAL
        )
        assert valid is True
        assert len(calculated_configs) == 3  # 2个配置 + 1个未分配
        assert calculated_configs[2].filename == "未分配"
        assert calculated_configs[2].count == 40  # 100 - 30 - 30 = 40

    def test_validate_split_config_with_mode_ratio(self, loaded_handler: DataHandler):
        """测试按比例分配模式"""
        configs = [
            SplitConfig(count=0, filename="part1", ratio=0.3),
            SplitConfig(count=0, filename="part2", ratio=0.3),
            SplitConfig(count=0, filename="part3", ratio=0.4)
        ]
        
        valid, msg, calculated_configs = loaded_handler.validate_split_config_with_mode(
            configs, SplitMode.RATIO
        )
        assert valid is True
        assert len(calculated_configs) == 3
        assert calculated_configs[0].count == 30  # 100 * 0.3
        assert calculated_configs[1].count == 30  # 100 * 0.3
        assert calculated_configs[2].count == 40  # 100 * 0.4

    def test_validate_split_config_with_mode_ratio_remainder(self, loaded_handler: DataHandler):
        """测试按比例分配模式的余数处理"""
        # 100条数据，按 0.33, 0.33, 0.34 分配
        configs = [
            SplitConfig(count=0, filename="part1", ratio=0.33),
            SplitConfig(count=0, filename="part2", ratio=0.33),
            SplitConfig(count=0, filename="part3", ratio=0.34)
        ]
        
        valid, msg, calculated_configs = loaded_handler.validate_split_config_with_mode(
            configs, SplitMode.RATIO
        )
        assert valid is True
        # 总数应该等于100
        total = sum(c.count for c in calculated_configs)
        assert total == 100
        # 最后一组应该包含余数
        assert calculated_configs[2].count >= calculated_configs[0].count

    def test_split_and_export_preserve_all_columns(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试保留所有原始字段的导出"""
        configs = [SplitConfig(count=100, filename="all_data")]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(
            configs, str(output_dir), preserve_all_columns=True
        )
        
        assert success is True
        assert len(files) == 1
        
        # 验证导出内容
        df = pd.read_excel(files[0])
        # 应该包含所有原始字段
        assert 'wm_poi_id' in df.columns
        assert 'provider_id' in df.columns
        assert 'lead_tag' in df.columns
        assert 'status' in df.columns
        assert 'modifier' in df.columns
        assert 'ctime' in df.columns
        # 应该包含分配组列
        assert '分配组' in df.columns
        assert df['分配组'].iloc[0] == 'all_data'

    def test_split_and_export_partial_mode(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试部分导出模式"""
        configs = [
            SplitConfig(count=30, filename="part1"),
            SplitConfig(count=30, filename="part2")
        ]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(
            configs, str(output_dir), mode=SplitMode.PARTIAL
        )
        
        assert success is True
        assert len(files) == 3  # 2个配置 + 1个未分配
        
        # 验证每个文件的行数
        df1 = pd.read_excel(files[0])
        df2 = pd.read_excel(files[1])
        df3 = pd.read_excel(files[2])
        
        assert len(df1) == 30
        assert len(df2) == 30
        assert len(df3) == 40  # 未分配的

    def test_split_and_export_ratio_mode(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试按比例分配模式"""
        configs = [
            SplitConfig(count=0, filename="part1", ratio=0.3),
            SplitConfig(count=0, filename="part2", ratio=0.3),
            SplitConfig(count=0, filename="part3", ratio=0.4)
        ]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(
            configs, str(output_dir), mode=SplitMode.RATIO
        )
        
        assert success is True
        assert len(files) == 3
        
        # 验证每个文件的行数
        df1 = pd.read_excel(files[0])
        df2 = pd.read_excel(files[1])
        df3 = pd.read_excel(files[2])
        
        assert len(df1) == 30
        assert len(df2) == 30
        assert len(df3) == 40

    def test_get_export_preview(self, loaded_handler: DataHandler):
        """测试导出预览功能"""
        configs = [
            SplitConfig(count=30, filename="part1"),
            SplitConfig(count=30, filename="part2"),
            SplitConfig(count=40, filename="part3")
        ]
        
        success, msg, preview = loaded_handler.get_export_preview(configs)
        
        assert success is True
        assert preview is not None
        assert preview.total_rows == 100
        assert len(preview.columns) > 0
        assert len(preview.groups) == 3
        
        # 验证每组信息
        assert preview.groups[0]["filename"] == "part1"
        assert preview.groups[0]["count"] == 30
        assert len(preview.groups[0]["sample_data"]) <= 3  # 最多3条预览
        
        assert preview.groups[1]["filename"] == "part2"
        assert preview.groups[1]["count"] == 30
        
        assert preview.groups[2]["filename"] == "part3"
        assert preview.groups[2]["count"] == 40

    def test_get_export_preview_partial_mode(self, loaded_handler: DataHandler):
        """测试部分导出模式的预览"""
        configs = [
            SplitConfig(count=30, filename="part1"),
            SplitConfig(count=30, filename="part2")
        ]
        
        success, msg, preview = loaded_handler.get_export_preview(
            configs, mode=SplitMode.PARTIAL
        )
        
        assert success is True
        assert len(preview.groups) == 3  # 2个配置 + 1个未分配
        assert preview.groups[2]["filename"] == "未分配"
        assert preview.groups[2]["count"] == 40

    def test_millisecond_timestamp_detection(self, data_handler: DataHandler, temp_dir: Path):
        """测试毫秒级时间戳识别"""
        # 创建包含毫秒级时间戳的数据
        current_ms = int(pd.Timestamp.now().timestamp() * 1000)
        df = pd.DataFrame({
            'wm_poi_id': ['POI001', 'POI002', 'POI003'],
            'ctime': [current_ms, current_ms + 1000, current_ms + 2000]  # 毫秒级时间戳
        })
        file_path = temp_dir / "ms_timestamp.xlsx"
        df.to_excel(file_path, index=False)
        data_handler.load_file(str(file_path))
        
        stats = data_handler.get_stats()
        assert stats.analysis["date_range"] is not None
        # 应该识别为近期日期，不是1970年
        assert "1970" not in stats.analysis["date_range"]["earliest"]

    def test_microsecond_timestamp_detection(self, data_handler: DataHandler, temp_dir: Path):
        """测试微秒级时间戳识别"""
        # 创建包含微秒级时间戳的数据
        current_us = int(pd.Timestamp.now().timestamp() * 1000000)
        df = pd.DataFrame({
            'wm_poi_id': ['POI001', 'POI002', 'POI003'],
            'ctime': [current_us, current_us + 1000000, current_us + 2000000]  # 微秒级时间戳
        })
        file_path = temp_dir / "us_timestamp.xlsx"
        df.to_excel(file_path, index=False)
        data_handler.load_file(str(file_path))
        
        stats = data_handler.get_stats()
        assert stats.analysis["date_range"] is not None
        # 应该识别为近期日期，不是1970年
        assert "1970" not in stats.analysis["date_range"]["earliest"]

    def test_timestamp_constants(self):
        """测试时间戳常量定义"""
        from src.data_handler import (
            TIMESTAMP_MIN_SECONDS,
            TIMESTAMP_MAX_SECONDS,
            TIMESTAMP_MILLISECONDS_THRESHOLD,
            TIMESTAMP_MICROSECONDS_THRESHOLD
        )
        
        # 验证常量值
        assert TIMESTAMP_MIN_SECONDS == 946684800  # 2000-01-01
        assert TIMESTAMP_MAX_SECONDS == 4102444800  # 2100-01-01
        assert TIMESTAMP_MILLISECONDS_THRESHOLD == 10**12
        assert TIMESTAMP_MICROSECONDS_THRESHOLD == 10**15

    def test_split_mode_enum(self):
        """测试分割模式枚举"""
        from src.data_handler import SplitMode
        
        assert SplitMode.EXACT.value == "精确分配"
        assert SplitMode.PARTIAL.value == "部分导出"
        assert SplitMode.RATIO.value == "按比例分配"

    def test_export_preview_dataclass(self):
        """测试导出预览数据类"""
        from src.data_handler import ExportPreview
        
        preview = ExportPreview(
            total_rows=100,
            columns=['col1', 'col2'],
            groups=[{"filename": "test", "count": 10, "sample_data": []}],
            sample_data=[{"col1": "value1"}]
        )
        
        assert preview.total_rows == 100
        assert len(preview.columns) == 2
        assert len(preview.groups) == 1
        assert len(preview.sample_data) == 1

    def test_validate_split_config_with_mode_invalid_ratio(self, loaded_handler: DataHandler):
        """测试按比例分配模式的无效比例"""
        # 比例为0
        configs = [
            SplitConfig(count=0, filename="part1", ratio=0.0),
            SplitConfig(count=0, filename="part2", ratio=1.0)
        ]
        
        valid, msg, _ = loaded_handler.validate_split_config_with_mode(
            configs, SplitMode.RATIO
        )
        assert valid is False
        assert "比例" in msg
        
        # 比例大于1
        configs2 = [
            SplitConfig(count=0, filename="part1", ratio=0.5),
            SplitConfig(count=0, filename="part2", ratio=1.5)
        ]
        
        valid2, msg2, _ = loaded_handler.validate_split_config_with_mode(
            configs2, SplitMode.RATIO
        )
        assert valid2 is False
        assert "比例" in msg2

    def test_validate_split_config_with_mode_partial_exceed(self, loaded_handler: DataHandler):
        """测试部分导出模式配置总数超过数据总数"""
        configs = [
            SplitConfig(count=60, filename="part1"),
            SplitConfig(count=50, filename="part2")  # 总数110 > 100
        ]
        
        valid, msg, _ = loaded_handler.validate_split_config_with_mode(
            configs, SplitMode.PARTIAL
        )
        assert valid is False
        assert "不能大于" in msg
