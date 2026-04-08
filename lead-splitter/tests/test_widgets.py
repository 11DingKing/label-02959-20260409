"""
Widgets 单元测试
测试自定义组件的功能
"""

import pytest
from unittest.mock import MagicMock

# 跳过 GUI 测试如果没有显示器
pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

import sys
if not QApplication.instance():
    app = QApplication(sys.argv)

from src.widgets import SplitPartWidget, StatCard


class TestSplitPartWidget:
    """测试 SplitPartWidget 组件"""
    
    @pytest.fixture
    def widget(self):
        """创建测试组件"""
        w = SplitPartWidget(index=0, max_count=1000)
        yield w
        w.deleteLater()
    
    def test_init(self, widget: SplitPartWidget):
        """测试初始化"""
        assert widget.index == 0
        assert widget.get_count() == 100  # 默认值
        assert widget.get_filename() == "分割文件_1"
    
    def test_get_set_count(self, widget: SplitPartWidget):
        """测试获取和设置数量"""
        widget.set_count(500)
        assert widget.get_count() == 500
    
    def test_get_set_filename(self, widget: SplitPartWidget):
        """测试获取和设置文件名"""
        widget.set_filename("custom_name")
        assert widget.get_filename() == "custom_name"
    
    def test_empty_filename_fallback(self, widget: SplitPartWidget):
        """测试空文件名回退到默认值"""
        widget.set_filename("")
        assert widget.get_filename() == "分割文件_1"
    
    def test_update_index(self, widget: SplitPartWidget):
        """测试更新索引"""
        widget.update_index(2)
        assert widget.index == 2
        # 默认文件名也应该更新
        assert "3" in widget.get_filename()
    
    def test_set_max_count(self, widget: SplitPartWidget):
        """测试设置最大数量"""
        widget.set_max_count(500)
        widget.set_count(600)  # 尝试设置超过最大值
        assert widget.get_count() <= 500
    
    def test_delete_signal(self, widget: SplitPartWidget):
        """测试删除信号"""
        callback = MagicMock()
        widget.delete_requested.connect(callback)
        
        widget.delete_btn.click()
        
        callback.assert_called_once_with(0)
    
    def test_count_changed_signal(self, widget: SplitPartWidget):
        """测试数量变化信号"""
        callback = MagicMock()
        widget.count_changed.connect(callback)
        
        widget.set_count(200)
        
        callback.assert_called()


class TestStatCard:
    """测试 StatCard 组件"""
    
    @pytest.fixture
    def card(self):
        """创建测试组件"""
        c = StatCard(title="测试标题", value="100", color="#409EFF")
        yield c
        c.deleteLater()
    
    def test_init(self, card: StatCard):
        """测试初始化"""
        assert card._title == "测试标题"
        assert card.value_label.text() == "100"
    
    def test_set_value(self, card: StatCard):
        """测试设置值"""
        card.set_value("200")
        assert card.value_label.text() == "200"
    
    def test_set_color(self, card: StatCard):
        """测试设置颜色"""
        card.set_color("#67C23A")
        # 颜色应该在样式表中
        assert "#67C23A" in card.value_label.styleSheet()


class TestSplitPartWidgetIntegration:
    """SplitPartWidget 集成测试"""
    
    def test_multiple_widgets(self):
        """测试多个组件"""
        widgets = []
        for i in range(5):
            w = SplitPartWidget(index=i, max_count=1000)
            w.set_count((i + 1) * 100)
            w.set_filename(f"file_{i + 1}")
            widgets.append(w)
        
        # 验证每个组件的状态
        for i, w in enumerate(widgets):
            assert w.index == i
            assert w.get_count() == (i + 1) * 100
            assert w.get_filename() == f"file_{i + 1}"
        
        # 清理
        for w in widgets:
            w.deleteLater()
    
    def test_widget_count_sum(self):
        """测试组件数量总和"""
        widgets = []
        counts = [30, 30, 40]
        
        for i, count in enumerate(counts):
            w = SplitPartWidget(index=i, max_count=1000)
            w.set_count(count)
            widgets.append(w)
        
        total = sum(w.get_count() for w in widgets)
        assert total == 100
        
        # 清理
        for w in widgets:
            w.deleteLater()
