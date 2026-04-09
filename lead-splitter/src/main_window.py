"""
主窗口模块
本地单进程 GUI - 直接调用 DataHandler 处理数据
"""

from pathlib import Path
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog,
    QProgressBar, QScrollArea, QFrame, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGraphicsDropShadowEffect, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from .styles import GLOBAL_STYLESHEET, COLORS
from .data_handler import DataHandler, SplitConfig
from .widgets import SplitPartWidget, StatCard, AnimatedButton, LoadingSpinner
from .toast import ToastManager
from .logger import get_logger

logger = get_logger(__name__)


class ExportWorker(QThread):
    """导出工作线程"""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str, list)

    def __init__(self, handler: DataHandler, configs: List[SplitConfig], save_dir: str):
        super().__init__()
        self.handler = handler
        self.configs = configs
        self.save_dir = save_dir

    def run(self):
        # 使用 Qt 信号槽机制连接进度信号
        # DataHandler 的 progress 信号直接连接到 ExportWorker 的 progress 信号
        # 这样可以确保信号在正确的线程中处理
        try:
            # 连接 DataHandler 的 progress 信号到本线程的 progress 信号
            self.handler.progress.connect(self.progress.emit)
        except Exception:
            # 如果信号连接失败（比如在非 Qt 环境下），忽略错误
            pass

        # 调用 split_and_export，不需要传递回调函数
        # DataHandler 会通过信号槽机制发射进度信号
        success, msg, files = self.handler.split_and_export(
            self.configs, self.save_dir
        )
        
        # 断开信号连接（可选，但良好的实践）
        try:
            self.handler.progress.disconnect(self.progress.emit)
        except Exception:
            pass
            
        self.finished.emit(success, msg, files)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.handler = DataHandler()
        self.split_widgets: List[SplitPartWidget] = []
        self._export_worker = None
        self._total_rows = 0

        self._setup_ui()
        self._connect_signals()
        self._setup_toast()
        logger.info("主窗口初始化完成")

    def _setup_toast(self):
        self.toast = ToastManager.get_instance(self._central)

    def _setup_ui(self):
        self.setWindowTitle("线索池数据分割工具")
        self.setMinimumSize(960, 680)
        self.resize(1060, 760)
        self.setStyleSheet(GLOBAL_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        self._central = central

        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F0F2F5; border: none; }")
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background-color: #F0F2F5;")
        scroll.setWidget(content)

        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        main_layout.addWidget(self._create_header())
        main_layout.addWidget(self._create_import_card())
        main_layout.addWidget(self._create_stats_row())
        main_layout.addWidget(self._create_preview_card())
        main_layout.addWidget(self._create_split_card())
        main_layout.addWidget(self._create_action_card())

    # ==================== 头部 ====================

    def _create_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 4)

        left = QVBoxLayout()
        left.setSpacing(2)
        title = QLabel("线索池数据分割工具")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #303133; background: transparent;")
        left.addWidget(title)
        sub = QLabel("快速分割线索数据，支持自定义份数和文件命名")
        sub.setStyleSheet("font-size: 13px; color: #909399; background: transparent;")
        left.addWidget(sub)
        layout.addLayout(left)
        layout.addStretch()

        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #C0C4CC; font-size: 11px; background: transparent;")
        layout.addWidget(ver)
        return header

    # ==================== 导入卡片 ====================

    def _create_import_card(self) -> QFrame:
        card = self._make_card()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        icon = QLabel("📁")
        icon.setStyleSheet("font-size: 24px; background: transparent;")
        layout.addWidget(icon)

        info = QVBoxLayout()
        info.setSpacing(2)
        self.file_title_label = QLabel("选择数据文件")
        self.file_title_label.setStyleSheet("font-size: 15px; font-weight: 600; color: #303133; background: transparent;")
        info.addWidget(self.file_title_label)
        self.file_path_label = QLabel("支持 Excel (.xlsx, .xls) 和 CSV 格式")
        self.file_path_label.setStyleSheet("font-size: 13px; color: #909399; background: transparent;")
        info.addWidget(self.file_path_label)
        layout.addLayout(info, 1)

        self.import_btn = AnimatedButton("选择文件")
        self.import_btn.setMinimumWidth(100)
        self.import_btn.setStyleSheet("""
            QPushButton { background-color: #409EFF; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-size: 14px; font-weight: 500; }
            QPushButton:hover { background-color: #66B1FF; }
            QPushButton:pressed { background-color: #337ECC; }
        """)
        layout.addWidget(self.import_btn)

        self.clear_btn = AnimatedButton("清除")
        self.clear_btn.setEnabled(False)
        self.clear_btn.setStyleSheet("""
            QPushButton { background: #FFFFFF; color: #606266; border: 1px solid #DCDFE6; border-radius: 6px; padding: 10px 20px; font-size: 14px; }
            QPushButton:hover { color: #409EFF; border-color: #409EFF; background-color: #ECF5FF; }
            QPushButton:disabled { color: #C0C4CC; background: #F5F7FA; border-color: #E4E7ED; }
        """)
        layout.addWidget(self.clear_btn)
        return card

    # ==================== 统计卡片行 ====================

    def _create_stats_row(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 第一行：核心统计
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.total_card = StatCard("总数据行数", "0", COLORS['primary'], "📋")
        row1.addWidget(self.total_card)
        self.poi_card = StatCard("唯一门店数", "0", COLORS['success'], "🏪")
        row1.addWidget(self.poi_card)
        self.config_card = StatCard("已配置数量", "0", COLORS['warning'], "⚙️")
        row1.addWidget(self.config_card)
        self.diff_card = StatCard("剩余差额", "0", COLORS['info'], "📊")
        row1.addWidget(self.diff_card)
        layout.addLayout(row1)

        # 第二行：深度分析（导入后显示）
        self.analysis_row = QWidget()
        self.analysis_row.setStyleSheet("background: transparent;")
        self.analysis_row.hide()
        row2 = QHBoxLayout(self.analysis_row)
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(12)
        self.provider_card = StatCard("服务商ID为空", "-", COLORS['danger'], "🔍")
        row2.addWidget(self.provider_card)
        self.status_card = StatCard("状态分布", "-", COLORS['primary'], "📈")
        row2.addWidget(self.status_card)
        self.date_card = StatCard("时间范围", "-", COLORS['success'], "📅")
        row2.addWidget(self.date_card)
        self.field_card = StatCard("字段完整度", "-", COLORS['info'], "✅")
        row2.addWidget(self.field_card)
        layout.addWidget(self.analysis_row)

        return w

    # ==================== 数据预览卡片 ====================

    def _create_preview_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("数据预览")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #303133; background: transparent;")
        layout.addWidget(title)

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.preview_table.setShowGrid(False)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setMinimumHeight(120)
        self.preview_table.setMaximumHeight(220)
        self.preview_table.hide()
        layout.addWidget(self.preview_table)

        self.empty_label = QLabel("导入文件后在此预览数据")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #C0C4CC; font-size: 13px; padding: 20px 0; background: transparent;")
        layout.addWidget(self.empty_label)
        return card

    # ==================== 分割配置卡片 ====================

    def _create_split_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        title = QLabel("分割配置")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #303133; background: transparent;")
        toolbar.addWidget(title)

        toolbar.addSpacing(12)

        lbl = QLabel("份数")
        lbl.setStyleSheet("color: #606266; font-size: 13px; background: transparent;")
        toolbar.addWidget(lbl)

        self.part_count_spin = QSpinBox()
        self.part_count_spin.setRange(1, 100)
        self.part_count_spin.setValue(1)
        self.part_count_spin.setFixedWidth(60)
        self.part_count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.part_count_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.part_count_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #DCDFE6; border-radius: 6px;
                padding: 5px 8px; background: white; font-size: 14px; font-weight: 600; color: #303133;
            }
            QSpinBox:focus { border-color: #409EFF; }
        """)
        toolbar.addWidget(self.part_count_spin)

        self.apply_count_btn = QPushButton("应用")
        self.apply_count_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_count_btn.setStyleSheet("""
            QPushButton { background-color: #409EFF; color: white; border: none; border-radius: 6px; padding: 6px 16px; font-size: 13px; font-weight: 500; min-width: 0; }
            QPushButton:hover { background-color: #66B1FF; }
        """)
        toolbar.addWidget(self.apply_count_btn)

        self.avg_btn = QPushButton("平均分配")
        self.avg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.avg_btn.setEnabled(False)
        self.avg_btn.setStyleSheet("""
            QPushButton { background: #F5F7FA; color: #303133; border: none; border-radius: 6px; padding: 6px 16px; font-size: 13px; min-width: 0; }
            QPushButton:hover { color: #67C23A; background-color: #F0F9EB; }
            QPushButton:disabled { color: #C0C4CC; background: #F5F7FA; }
        """)
        toolbar.addWidget(self.avg_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #F0F2F5;")
        layout.addWidget(line)

        self.split_container = QWidget()
        self.split_container.setStyleSheet("background: transparent;")
        self.split_layout = QVBoxLayout(self.split_container)
        self.split_layout.setContentsMargins(0, 0, 0, 0)
        self.split_layout.setSpacing(8)

        self.split_empty_label = QLabel("设置份数后点击「应用」生成配置")
        self.split_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.split_empty_label.setStyleSheet("color: #C0C4CC; font-size: 13px; padding: 16px 0; background: transparent;")
        self.split_layout.addWidget(self.split_empty_label)

        layout.addWidget(self.split_container)
        return card

    # ==================== 操作卡片 ====================

    def _create_action_card(self) -> QFrame:
        card = self._make_card()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(14)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 11px; background-color: #F0F2F5; text-align: center; font-size: 12px; font-weight: 600; color: #FFFFFF; }
            QProgressBar::chunk { background-color: #409EFF; border-radius: 11px; }
        """)
        layout.addWidget(self.progress_bar, 1)

        self.progress_label = QLabel("就绪")
        self.progress_label.setStyleSheet("color: #606266; font-size: 13px; background: transparent;")
        self.progress_label.setFixedWidth(90)
        layout.addWidget(self.progress_label)

        self.loading_spinner = LoadingSpinner(self, size=22, color="#67C23A")
        self.loading_spinner.hide()
        layout.addWidget(self.loading_spinner)

        self.export_btn = AnimatedButton("开始分割导出")
        self.export_btn.setEnabled(False)
        self.export_btn.setMinimumWidth(140)
        self.export_btn.setFixedHeight(40)
        self.export_btn.setStyleSheet("""
            QPushButton { background-color: #67C23A; color: white; font-size: 14px; font-weight: 600; border: none; border-radius: 8px; padding: 0 24px; }
            QPushButton:hover { background-color: #85CE61; }
            QPushButton:pressed { background-color: #529B2E; }
            QPushButton:disabled { background-color: #B3E19D; color: rgba(255,255,255,0.8); }
        """)
        layout.addWidget(self.export_btn)
        return card

    # ==================== 工具方法 ====================

    def _make_card(self) -> QFrame:
        """创建白色圆角卡片"""
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #FFFFFF; border: none; border-radius: 10px; }")
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)
        return card

    def _connect_signals(self):
        self.import_btn.clicked.connect(self._on_import_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.apply_count_btn.clicked.connect(self._on_apply_count)
        self.avg_btn.clicked.connect(self._on_avg_distribute)
        self.export_btn.clicked.connect(self._on_export_clicked)

    # ==================== 事件处理 ====================

    def _on_import_clicked(self):
        logger.info("用户点击导入按钮")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "",
            "Excel 文件 (*.xlsx *.xls);;CSV 文件 (*.csv);;所有文件 (*.*)"
        )
        if not file_path:
            return

        self.import_btn.setEnabled(False)
        self.import_btn.setText("加载中...")
        QApplication.processEvents()

        success, msg = self.handler.load_file(file_path)

        self.import_btn.setEnabled(True)
        self.import_btn.setText("选择文件")

        if success:
            filename = Path(file_path).name
            self.file_title_label.setText(f"✅ {filename}")
            self.file_path_label.setText(file_path)
            self.file_path_label.setStyleSheet("font-size: 13px; color: #67C23A; background: transparent;")
            self.clear_btn.setEnabled(True)
            self.avg_btn.setEnabled(True)

            stats = self.handler.get_stats()
            if stats:
                self._total_rows = stats.total_rows
                self._apply_stats(stats)

            preview = self.handler.get_preview()
            if preview is not None:
                self._apply_preview(preview)

            # 字段校验警告
            col_check = self.handler.validate_columns()
            warnings = col_check.get("warnings", [])
            if warnings:
                self.toast.warning(f"字段提示: {'; '.join(warnings)}")
            else:
                self.toast.success(f"成功加载 {self._total_rows} 条数据，字段完整")
        else:
            self.toast.error(f"加载失败: {msg}")

    def _on_clear_clicked(self):
        logger.info("用户点击清除按钮")
        self.handler.clear()
        self._total_rows = 0
        self.file_title_label.setText("选择数据文件")
        self.file_path_label.setText("支持 Excel (.xlsx, .xls) 和 CSV 格式")
        self.file_path_label.setStyleSheet("font-size: 13px; color: #909399; background: transparent;")
        self.clear_btn.setEnabled(False)
        self.avg_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.total_card.set_value("0")
        self.poi_card.set_value("0")
        self.config_card.set_value("0")
        self.diff_card.set_value("0")
        self.diff_card.set_color(COLORS['info'])
        self.analysis_row.hide()
        self.preview_table.clear()
        self.preview_table.setRowCount(0)
        self.preview_table.setColumnCount(0)
        self.preview_table.hide()
        self.empty_label.show()
        self._clear_split_widgets()
        self.progress_bar.setValue(0)
        self.progress_label.setText("就绪")
        self.toast.info("数据已清除")

    def _on_apply_count(self):
        count = self.part_count_spin.value()
        self._create_split_widgets(count)
        self._update_config_stats()
        self.toast.success(f"已创建 {count} 个分割配置")

    def _on_avg_distribute(self):
        if self._total_rows == 0:
            self.toast.warning("请先导入数据文件")
            return
        count = len(self.split_widgets)
        if count == 0:
            self.toast.warning("请先设置分割份数并点击应用")
            return
        avg = self._total_rows // count
        remainder = self._total_rows % count
        for i, w in enumerate(self.split_widgets):
            w.set_count(avg + 1 if i < remainder else avg)
        self._update_config_stats()
        self.toast.success("已平均分配数据")

    def _on_export_clicked(self):
        logger.info("用户点击导出按钮")
        configs = [SplitConfig(count=w.get_count(), filename=w.get_filename()) for w in self.split_widgets]
        valid, msg = self.handler.validate_split_config(configs)
        if not valid:
            self.toast.warning(msg)
            return
        save_dir = QFileDialog.getExistingDirectory(self, "选择本地保存目录", "")
        if not save_dir:
            return
        self.export_btn.setEnabled(False)
        self.export_btn.setText("导出中...")
        self.import_btn.setEnabled(False)
        self.loading_spinner.start()
        self._export_worker = ExportWorker(self.handler, configs, save_dir)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.start()

    def _on_export_progress(self, current, total, message):
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))
        self.progress_label.setText(message)

    def _on_export_finished(self, success, message, files):
        self.export_btn.setEnabled(True)
        self.export_btn.setText("开始分割导出")
        self.import_btn.setEnabled(True)
        self.loading_spinner.stop()
        if success:
            self.progress_bar.setValue(100)
            self.progress_label.setText("✅ 完成")
            self.toast.success(message)
            QTimer.singleShot(500, lambda: self._show_export_result(files))
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("❌ 失败")
            self.toast.error(message)

    def _show_export_result(self, files):
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTextEdit
        dlg = QDialog(self)
        dlg.setWindowTitle("导出成功")
        dlg.setFixedSize(420, 300)
        dlg.setStyleSheet("QDialog { background: #FFFFFF; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel(f"✅ 成功导出 {len(files)} 个文件")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #303133;")
        layout.addWidget(title)

        file_list = QTextEdit()
        file_list.setReadOnly(True)
        file_list.setStyleSheet("""
            QTextEdit {
                background-color: #F5F7FA; border: 1px solid #EBEEF5;
                border-radius: 6px; padding: 10px; font-size: 13px; color: #606266;
            }
        """)
        file_list.setPlainText("\n".join([f"• {Path(f).name}" for f in files]))
        layout.addWidget(file_list)

        btn_box = QDialogButtonBox()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton { background-color: #409EFF; color: white; border: none;
            border-radius: 6px; padding: 8px 24px; font-size: 14px; font-weight: 500; }
            QPushButton:hover { background-color: #66B1FF; }
        """)
        ok_btn.clicked.connect(dlg.accept)
        btn_box.addButton(ok_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(btn_box)

        dlg.exec()

    # ==================== 数据展示 ====================

    def _apply_stats(self, stats):
        self.total_card.set_value(f"{stats.total_rows:,}")
        self.poi_card.set_value(f"{stats.wm_poi_id_count:,}")
        self._update_config_stats()

        # 深度分析
        analysis = stats.analysis or {}
        if analysis:
            self.analysis_row.show()

            # 服务商ID空值
            provider_empty = analysis.get("provider_id_empty")
            if provider_empty is not None:
                self.provider_card.set_value(f"{provider_empty:,}")
                if provider_empty > 0:
                    self.provider_card.set_color(COLORS['danger'])
                else:
                    self.provider_card.set_color(COLORS['success'])
            else:
                self.provider_card.set_value("无此列")

            # 状态分布（显示最多的状态及数量）
            status_dist = analysis.get("status_distribution")
            if status_dist:
                top_status = max(status_dist, key=status_dist.get)
                self.status_card.set_value(f"{top_status}: {status_dist[top_status]}")
            else:
                self.status_card.set_value("无此列")

            # 时间范围（两行显示，字号缩小）
            date_range = analysis.get("date_range")
            if date_range:
                earliest = date_range["earliest"][:10]
                latest = date_range["latest"][:10]
                self.date_card.set_value(f"{earliest} ~\n{latest}")
                self.date_card.value_label.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: 600;
                    color: {COLORS['success']};
                    background: transparent;
                    line-height: 1.4;
                """)
            else:
                self.date_card.set_value("无日期列")

            # 字段完整度
            col_check = self.handler.validate_columns()
            present_count = len(col_check.get("present", []))
            expected = len(col_check.get("present", [])) + len(col_check.get("missing", []))
            self.field_card.set_value(f"{present_count}/{expected}")
        else:
            self.analysis_row.hide()

    def _apply_preview(self, preview_df):
        if preview_df is None or preview_df.empty:
            return
        self.empty_label.hide()
        self.preview_table.show()
        columns = list(preview_df.columns)
        self.preview_table.setRowCount(len(preview_df))
        self.preview_table.setColumnCount(len(columns))
        self.preview_table.setHorizontalHeaderLabels(columns)
        for i, (_, row) in enumerate(preview_df.iterrows()):
            for j, col in enumerate(columns):
                item = QTableWidgetItem(str(row[col]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.preview_table.setItem(i, j, item)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _update_config_stats(self):
        total_config = sum(w.get_count() for w in self.split_widgets)
        self.config_card.set_value(f"{total_config:,}")
        if self._total_rows > 0:
            diff = self._total_rows - total_config
            self.diff_card.set_value(f"{diff:,}")
            if diff == 0:
                self.diff_card.set_color(COLORS['success'])
                self.export_btn.setEnabled(True)
            elif diff > 0:
                self.diff_card.set_color(COLORS['warning'])
                self.export_btn.setEnabled(False)
            else:
                self.diff_card.set_color(COLORS['danger'])
                self.export_btn.setEnabled(False)
        else:
            self.diff_card.set_value("0")
            self.diff_card.set_color(COLORS['info'])
            self.export_btn.setEnabled(False)

    def _create_split_widgets(self, count):
        self._clear_split_widgets()
        self.split_empty_label.hide()
        max_count = self._total_rows if self._total_rows > 0 else 999999
        for i in range(count):
            w = SplitPartWidget(i, max_count)
            w.delete_requested.connect(self._on_delete_part)
            w.count_changed.connect(self._update_config_stats)
            self.split_layout.addWidget(w)
            self.split_widgets.append(w)

    def _clear_split_widgets(self):
        for w in self.split_widgets:
            w.deleteLater()
        self.split_widgets.clear()
        self.split_empty_label.show()

    def _on_delete_part(self, index):
        if len(self.split_widgets) <= 1:
            self.toast.warning("至少需要保留一份配置")
            return
        w = self.split_widgets.pop(index)
        w.deleteLater()
        for i, w in enumerate(self.split_widgets):
            w.update_index(i)
        self.part_count_spin.setValue(len(self.split_widgets))
        self._update_config_stats()
        self.toast.info("已删除分割配置")
