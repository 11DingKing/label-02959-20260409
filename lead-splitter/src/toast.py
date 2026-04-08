"""
Toast 通知组件
在应用窗口内部显示消息提示（覆盖在 centralWidget 之上）
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint, QEvent
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QFont, QPen
from PyQt6.QtCore import QRectF

from .logger import get_logger

logger = get_logger(__name__)


class Toast(QWidget):
    """Toast 通知 — 挂载到目标 widget 上，始终浮在内容之上"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    TYPE_CONFIG = {
        SUCCESS: {"bg": "#FFFFFF", "border": "#67C23A", "text": "#529B2E", "icon": "✓"},
        ERROR:   {"bg": "#FFFFFF", "border": "#F56C6C", "text": "#C45656", "icon": "✕"},
        WARNING: {"bg": "#FFFFFF", "border": "#E6A23C", "text": "#B88230", "icon": "!"},
        INFO:    {"bg": "#FFFFFF", "border": "#409EFF", "text": "#337ECC", "icon": "i"},
    }

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        # 不参与父布局，手动定位
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFixedHeight(48)
        self._bg_color = "#F4F4F5"
        self._border_color = "#909399"
        self._opacity_val = 0.0
        self._setup_ui()
        self._setup_animation()
        self.hide()
        # 监听父 widget 的 resize 事件，保持居中
        parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        """父 widget resize 时重新居中"""
        if obj == self.parent() and event.type() == QEvent.Type.Resize and self.isVisible():
            self._center_in_parent()
        return False

    def _center_in_parent(self):
        if self.parent():
            pw = self.parent().width()
            px = (pw - self.width()) // 2
            self.move(px, self.y())

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(22, 22)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        self.icon_label.setFont(f)
        layout.addWidget(self.icon_label)

        self.message_label = QLabel()
        self.message_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        layout.addWidget(self.message_label)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

    def _setup_animation(self):
        self.fade_in = QPropertyAnimation(self, b"opacity")
        self.fade_in.setDuration(250)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_out = QPropertyAnimation(self, b"opacity")
        self.fade_out.setDuration(300)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out.finished.connect(self.hide)

        self.slide_anim = QPropertyAnimation(self, b"pos")
        self.slide_anim.setDuration(250)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._start_fade_out)

    def _start_fade_out(self):
        self.fade_out.start()

    def _get_opacity(self):
        return self._opacity_val

    def _set_opacity(self, v):
        self._opacity_val = v
        self.opacity_effect.setOpacity(v)

    opacity = pyqtProperty(float, _get_opacity, _set_opacity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # 阴影（偏移 2px 向下，模糊用半透明矩形模拟）
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(1.0, 2.0, w - 2.0, h - 1.0, 8.0, 8.0)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 25))

        # 白色背景
        bg_path = QPainterPath()
        bg_path.addRoundedRect(0.0, 0.0, w, h, 8.0, 8.0)
        painter.fillPath(bg_path, QColor(self._bg_color))

        # 边框
        painter.setPen(QPen(QColor(0, 0, 0, 15), 1.0))
        painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1.0, h - 1.0), 8.0, 8.0)

        # 左侧色条（加粗到 5px）
        bar = QPainterPath()
        bar.addRoundedRect(0.0, 0.0, 5.0, h, 2.5, 2.5)
        painter.fillPath(bar, QColor(self._border_color))

    def show_message(self, message: str, toast_type: str = INFO, duration: int = 3000):
        # 停止之前的动画
        self.fade_in.stop()
        self.fade_out.stop()
        self.slide_anim.stop()
        self.hide_timer.stop()

        config = self.TYPE_CONFIG.get(toast_type, self.TYPE_CONFIG[self.INFO])
        self._bg_color = config["bg"]
        self._border_color = config["border"]

        self.icon_label.setText(config["icon"])
        self.icon_label.setStyleSheet(f"color: {config['text']}; background: transparent; font-weight: 700;")
        self.message_label.setText(message)
        self.message_label.setStyleSheet(f"color: {config['text']}; font-size: 14px; font-weight: 500; background: transparent;")

        self.adjustSize()
        w = max(240, self.message_label.sizeHint().width() + 70)
        self.setFixedWidth(w)

        if self.parent():
            pw = self.parent().width()
            px = (pw - w) // 2
            start_pos = QPoint(px, -self.height())
            end_pos = QPoint(px, 12)
            self.move(start_pos)
            self.slide_anim.setStartValue(start_pos)
            self.slide_anim.setEndValue(end_pos)

        self._opacity_val = 0.0
        self.opacity_effect.setOpacity(0.0)
        self.show()
        self.raise_()
        self.fade_in.start()
        self.slide_anim.start()
        self.hide_timer.start(duration)

        logger.debug(f"Toast 显示: [{toast_type}] {message}")


class ToastManager:
    """Toast 管理器 — 单例，绑定到指定 widget"""

    _instance = None
    _toast = None
    _host = None

    @classmethod
    def get_instance(cls, host_widget: QWidget = None):
        if cls._instance is None:
            cls._instance = cls()
        if host_widget and host_widget != cls._host:
            cls._host = host_widget
            cls._toast = Toast(host_widget)
        return cls._instance

    def success(self, message: str, duration: int = 3000):
        if self._toast:
            self._toast.show_message(message, Toast.SUCCESS, duration)

    def error(self, message: str, duration: int = 4000):
        if self._toast:
            self._toast.show_message(message, Toast.ERROR, duration)

    def warning(self, message: str, duration: int = 3500):
        if self._toast:
            self._toast.show_message(message, Toast.WARNING, duration)

    def info(self, message: str, duration: int = 3000):
        if self._toast:
            self._toast.show_message(message, Toast.INFO, duration)
