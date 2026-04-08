"""
自定义组件模块
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QPushButton, QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import (
    pyqtSignal, Qt, QPropertyAnimation, QEasingCurve,
    QTimer,
)
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtCore import QRectF

from .styles import COLORS


class SplitPartWidget(QFrame):
    """单个分割配置组件"""

    delete_requested = pyqtSignal(int)
    count_changed = pyqtSignal()

    def __init__(self, index: int, max_count: int = 999999, parent=None):
        super().__init__(parent)
        self.index = index
        self._max_count = max_count
        self._setup_ui()
        self._setup_effects()

    def _setup_ui(self):
        self.setFixedHeight(44)
        self.setStyleSheet("""
            SplitPartWidget {
                background-color: #F5F7FA;
                border: none;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(12)

        # 序号
        self.index_label = QLabel(f"第 {self.index + 1} 份")
        self.index_label.setFixedWidth(50)
        self.index_label.setStyleSheet("color: #409EFF; font-size: 13px; font-weight: 600; background: transparent;")
        layout.addWidget(self.index_label)

        # 数量输入
        count_lbl = QLabel("条数")
        count_lbl.setStyleSheet("color: #909399; font-size: 12px; background: transparent;")
        layout.addWidget(count_lbl)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, self._max_count)
        self.count_spin.setValue(100)
        self.count_spin.setFixedWidth(100)
        self.count_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DCDFE6; border-radius: 6px;
                padding: 4px 8px; font-size: 13px; color: #303133;
                background-color: #FFFFFF;
            }
            QSpinBox:focus { border-color: #409EFF; }
        """)
        self.count_spin.valueChanged.connect(self.count_changed.emit)
        layout.addWidget(self.count_spin)

        # 文件名输入
        name_lbl = QLabel("文件名")
        name_lbl.setStyleSheet("color: #909399; font-size: 12px; background: transparent;")
        layout.addWidget(name_lbl)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(f"分割文件_{self.index + 1}")
        self.name_edit.setText(f"分割文件_{self.index + 1}")
        self.name_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #DCDFE6; border-radius: 6px;
                padding: 4px 8px; font-size: 13px; color: #303133;
                background-color: #FFFFFF;
            }
            QLineEdit:focus { border-color: #409EFF; }
        """)
        layout.addWidget(self.name_edit, 1)

        # 删除按钮 — 红色文字
        self.delete_btn = QPushButton("删除")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #C0C4CC;
                border: none; font-size: 12px; min-width: 0;
                padding: 4px 8px;
            }
            QPushButton:hover { color: #F56C6C; }
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.index))
        layout.addWidget(self.delete_btn)

    def _setup_effects(self):
        pass  # No shadow for inline rows

    def update_index(self, new_index: int):
        self.index = new_index
        self.index_label.setText(f"第 {self.index + 1} 份")
        if self.name_edit.text().startswith("分割文件_"):
            self.name_edit.setText(f"分割文件_{self.index + 1}")
            self.name_edit.setPlaceholderText(f"分割文件_{self.index + 1}")

    def get_count(self) -> int:
        return self.count_spin.value()

    def set_count(self, count: int):
        self.count_spin.setValue(count)

    def get_filename(self) -> str:
        return self.name_edit.text().strip() or f"分割文件_{self.index + 1}"

    def set_filename(self, filename: str):
        self.name_edit.setText(filename)

    def set_max_count(self, max_count: int):
        self._max_count = max_count
        self.count_spin.setMaximum(max_count)


class StatCard(QFrame):
    """统计卡片组件"""

    def __init__(self, title: str, value: str = "0", color: str = "#409EFF", icon: str = "📊", parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value
        self._color = color
        self._icon = icon
        self._setup_ui()
        self._setup_effects()

    def _setup_ui(self):
        self.setMinimumHeight(60)
        self.setMinimumWidth(120)
        self._update_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        # 标题行
        top = QHBoxLayout()
        top.setSpacing(6)
        icon_lbl = QLabel(self._icon)
        icon_lbl.setStyleSheet("font-size: 15px; background: transparent;")
        top.addWidget(icon_lbl)
        title_lbl = QLabel(self._title)
        title_lbl.setStyleSheet("font-size: 13px; color: #606266; font-weight: 500; background: transparent;")
        top.addWidget(title_lbl)
        top.addStretch()
        layout.addLayout(top)

        # 数值
        self.value_label = QLabel(self._value)
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {self._color};
            background: transparent;
            line-height: 1.3;
        """)
        layout.addWidget(self.value_label)

    def _update_style(self):
        self.setStyleSheet(f"""
            StatCard {{
                background-color: #FFFFFF;
                border: none;
                border-radius: 10px;
                border-left: 4px solid {self._color};
            }}
        """)

    def _setup_effects(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)

    def set_value(self, value: str):
        self._value = value
        self.value_label.setText(value)

    def set_color(self, color: str):
        self._color = color
        self._update_style()
        self.value_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {self._color};
            background: transparent;
        """)


class AnimatedButton(QPushButton):
    """带悬停效果的按钮"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(6)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)


class LoadingSpinner(QWidget):
    """加载动画组件"""

    def __init__(self, parent=None, size: int = 40, color: str = "#409EFF"):
        super().__init__(parent)
        self._size = size
        self._color = color
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        self._timer.start(16)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self._size / 2, self._size / 2)
        painter.rotate(self._angle)

        pen_width = 3
        radius = (self._size - pen_width) / 2 - 2
        pen = QPen(QColor(self._color))
        pen.setWidth(pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        rect = QRectF(-radius, -radius, radius * 2, radius * 2)
        painter.drawArc(rect, 0, 270 * 16)
