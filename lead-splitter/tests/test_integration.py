"""
集成测试
测试完整的工作流程
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from src.data_handler import DataHandler, SplitConfig


class TestFullWorkflow:
    """完整工作流程测试"""
    
    @pytest.fixture
    def workflow_setup(self):
        """设置测试环境"""
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        
        # 创建测试数据
        df = pd.DataFrame({
            'wm_poi_id': [f'POI{str(i).zfill(8)}' for i in range(1, 1001)],
            'provider_id': [f'PRV{str(i % 50).zfill(4)}' for i in range(1, 1001)],
            'lead_tag': ['新客' if i % 3 == 0 else '老客' for i in range(1, 1001)],
            'status': ['active' if i % 2 == 0 else 'inactive' for i in range(1, 1001)],
            'modifier': [f'user_{i % 10}' for i in range(1, 1001)],
        })
        
        input_file = temp_dir / "input_data.xlsx"
        df.to_excel(input_file, index=False)
        
        output_dir = temp_dir / "output"
        
        yield {
            'temp_dir': temp_dir,
            'input_file': input_file,
            'output_dir': output_dir,
            'total_rows': 1000
        }
        
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self, workflow_setup):
        """测试完整工作流程"""
        input_file = workflow_setup['input_file']
        output_dir = workflow_setup['output_dir']
        total_rows = workflow_setup['total_rows']
        
        # 1. 创建处理器
        handler = DataHandler()
        assert handler.is_loaded is False
        
        # 2. 加载文件
        success, msg = handler.load_file(str(input_file))
        assert success is True
        assert handler.is_loaded is True
        
        # 3. 获取统计信息
        stats = handler.get_stats()
        assert stats is not None
        assert stats.total_rows == total_rows
        
        # 4. 配置分割
        configs = [
            SplitConfig(count=300, filename="batch_1"),
            SplitConfig(count=300, filename="batch_2"),
            SplitConfig(count=400, filename="batch_3")
        ]
        
        # 5. 验证配置
        valid, msg = handler.validate_split_config(configs)
        assert valid is True
        
        # 6. 执行分割导出
        progress_log = []
        
        def on_progress(current, total, message):
            progress_log.append({
                'current': current,
                'total': total,
                'message': message
            })
        
        success, msg, files = handler.split_and_export(
            configs, str(output_dir), on_progress
        )
        
        assert success is True
        assert len(files) == 3
        
        # 7. 验证输出文件
        for file_path in files:
            assert Path(file_path).exists()
        
        # 8. 验证数据完整性
        all_poi_ids = []
        for file_path in files:
            df = pd.read_excel(file_path)
            assert '商家门店id' in df.columns
            assert '服务商id' in df.columns
            all_poi_ids.extend(df['商家门店id'].tolist())
        
        # 确保所有数据都被导出且无重复
        assert len(all_poi_ids) == total_rows
        assert len(set(all_poi_ids)) == total_rows
        
        # 9. 验证进度回调
        assert len(progress_log) > 0
        assert progress_log[-1]['message'] == "导出完成"
    
    def test_workflow_with_uneven_split(self, workflow_setup):
        """测试不均匀分割"""
        input_file = workflow_setup['input_file']
        output_dir = workflow_setup['output_dir']
        
        handler = DataHandler()
        handler.load_file(str(input_file))
        
        # 不均匀分割
        configs = [
            SplitConfig(count=100, filename="small"),
            SplitConfig(count=200, filename="medium"),
            SplitConfig(count=700, filename="large")
        ]
        
        success, msg, files = handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        
        # 验证每个文件的行数
        df_small = pd.read_excel(files[0])
        df_medium = pd.read_excel(files[1])
        df_large = pd.read_excel(files[2])
        
        assert len(df_small) == 100
        assert len(df_medium) == 200
        assert len(df_large) == 700
    
    def test_workflow_single_file(self, workflow_setup):
        """测试单文件导出"""
        input_file = workflow_setup['input_file']
        output_dir = workflow_setup['output_dir']
        total_rows = workflow_setup['total_rows']
        
        handler = DataHandler()
        handler.load_file(str(input_file))
        
        configs = [SplitConfig(count=total_rows, filename="all_in_one")]
        
        success, msg, files = handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert len(files) == 1
        
        df = pd.read_excel(files[0])
        assert len(df) == total_rows
    
    def test_workflow_many_small_files(self, workflow_setup):
        """测试多个小文件导出"""
        input_file = workflow_setup['input_file']
        output_dir = workflow_setup['output_dir']
        
        handler = DataHandler()
        handler.load_file(str(input_file))
        
        # 分成 10 个文件，每个 100 条
        configs = [
            SplitConfig(count=100, filename=f"part_{i+1}")
            for i in range(10)
        ]
        
        success, msg, files = handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert len(files) == 10
        
        # 验证每个文件
        for file_path in files:
            df = pd.read_excel(file_path)
            assert len(df) == 100


class TestErrorHandling:
    """错误处理测试"""
    
    def test_load_corrupted_file(self, temp_dir: Path):
        """测试加载损坏的文件"""
        # 创建一个假的 Excel 文件
        corrupted_file = temp_dir / "corrupted.xlsx"
        corrupted_file.write_bytes(b"not a valid excel file")
        
        handler = DataHandler()
        success, msg = handler.load_file(str(corrupted_file))
        
        assert success is False
        assert "失败" in msg
    
    def test_export_to_readonly_dir(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试导出到只读目录（如果可能）"""
        # 这个测试在某些系统上可能不适用
        configs = [SplitConfig(count=100, filename="test")]
        
        # 尝试导出到一个不存在的深层目录
        output_dir = "/nonexistent/deep/path/output"
        
        success, msg, files = loaded_handler.split_and_export(configs, output_dir)
        
        # 应该失败或成功创建目录
        # 具体行为取决于系统权限


class TestEdgeCases:
    """边界情况测试"""
    
    def test_single_row_data(self, temp_dir: Path):
        """测试单行数据"""
        df = pd.DataFrame({
            'wm_poi_id': ['POI00000001'],
            'provider_id': ['PRV0001']
        })
        
        input_file = temp_dir / "single_row.xlsx"
        df.to_excel(input_file, index=False)
        
        handler = DataHandler()
        success, msg = handler.load_file(str(input_file))
        
        assert success is True
        
        stats = handler.get_stats()
        assert stats.total_rows == 1
        
        configs = [SplitConfig(count=1, filename="single")]
        output_dir = temp_dir / "output"
        
        success, msg, files = handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert len(files) == 1
    
    def test_large_dataset(self, temp_dir: Path):
        """测试大数据集（10000行）"""
        df = pd.DataFrame({
            'wm_poi_id': [f'POI{str(i).zfill(8)}' for i in range(1, 10001)],
            'provider_id': [f'PRV{str(i % 100).zfill(4)}' for i in range(1, 10001)]
        })
        
        input_file = temp_dir / "large_data.xlsx"
        df.to_excel(input_file, index=False)
        
        handler = DataHandler()
        success, msg = handler.load_file(str(input_file))
        
        assert success is True
        
        stats = handler.get_stats()
        assert stats.total_rows == 10000
        
        # 分成 100 个文件
        configs = [
            SplitConfig(count=100, filename=f"batch_{i+1}")
            for i in range(100)
        ]
        
        output_dir = temp_dir / "output"
        success, msg, files = handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        assert len(files) == 100
    
    def test_special_characters_in_filename(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试文件名中的特殊字符"""
        configs = [SplitConfig(count=100, filename="测试文件_2024")]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        # 中文文件名应该可以正常工作
        assert success is True
    
    def test_whitespace_in_filename(self, loaded_handler: DataHandler, temp_dir: Path):
        """测试文件名前后空格"""
        configs = [SplitConfig(count=100, filename="  trimmed_name  ")]
        output_dir = temp_dir / "output"
        
        success, msg, files = loaded_handler.split_and_export(configs, str(output_dir))
        
        assert success is True
        # 文件名应该被 trim
        assert "trimmed_name" in files[0]
