"""
UI 样式定义模块
高级视觉设计 - 参考 Element Plus / Ant Design 风格
优化可读性和对比度
"""

# 颜色常量
COLORS = {
    # 主色调
    'primary': '#409EFF',
    'primary_light': '#66B1FF',
    'primary_lighter': '#A0CFFF',
    'primary_dark': '#337ECC',

    # 功能色
    'success': '#67C23A',
    'success_light': '#85CE61',
    'success_lighter': '#E1F3D8',

    'warning': '#E6A23C',
    'warning_light': '#EBB563',
    'warning_lighter': '#FAECD8',

    'danger': '#F56C6C',
    'danger_light': '#F78989',
    'danger_lighter': '#FDE2E2',

    'info': '#909399',
    'info_light': '#A6A9AD',
    'info_lighter': '#E9E9EB',

    # 中性色
    'text_primary': '#303133',
    'text_regular': '#606266',
    'text_secondary': '#909399',
    'text_placeholder': '#C0C4CC',

    # 边框色
    'border_base': '#DCDFE6',
    'border_light': '#E4E7ED',
    'border_lighter': '#EBEEF5',
    'border_extra_light': '#F2F6FC',

    # 背景色
    'background': '#F0F2F5',
    'background_light': '#FAFAFA',
    'card': '#FFFFFF',

    # 阴影
    'shadow': 'rgba(0, 0, 0, 0.08)',
    'shadow_light': 'rgba(0, 0, 0, 0.04)',
}

# 全局样式表
GLOBAL_STYLESHEET = """
/* ==================== 基础样式 ==================== */
QMainWindow {
    background-color: #F0F2F5;
}

QWidget {
    font-family: "PingFang SC", "SF Pro Display", "Helvetica Neue", "Microsoft YaHei", Arial, sans-serif;
    font-size: 14px;
    color: #303133;
}

/* ==================== 卡片样式 ==================== */
QFrame#card {
    background-color: #FFFFFF;
    border: none;
    border-radius: 10px;
}

/* ==================== 标签样式 ==================== */
QLabel#title {
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    padding: 8px 0;
}

QLabel#subtitle {
    font-size: 14px;
    font-weight: 500;
    color: #606266;
}

QLabel#hint {
    font-size: 12px;
    color: #909399;
}

/* ==================== 按钮样式 ==================== */
QPushButton {
    background-color: #409EFF;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #66B1FF;
}

QPushButton:pressed {
    background-color: #337ECC;
}

QPushButton:disabled {
    background-color: #A0CFFF;
    color: rgba(255, 255, 255, 0.7);
}

/* ==================== 输入框样式 ==================== */
QLineEdit, QSpinBox {
    border: 1px solid #DCDFE6;
    border-radius: 6px;
    padding: 8px 12px;
    background-color: #FFFFFF;
    font-size: 14px;
    color: #303133;
    selection-background-color: #409EFF;
    selection-color: white;
}

QLineEdit:hover, QSpinBox:hover {
    border-color: #C0C4CC;
}

QLineEdit:focus, QSpinBox:focus {
    border-color: #409EFF;
}

QLineEdit:disabled, QSpinBox:disabled {
    background-color: #F5F7FA;
    color: #C0C4CC;
    border-color: #E4E7ED;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 0; height: 0; border: none;
}

QSpinBox::up-arrow, QSpinBox::down-arrow {
    width: 0; height: 0;
}

/* ==================== 进度条样式 ==================== */
QProgressBar {
    border: none;
    border-radius: 10px;
    background-color: #EBEEF5;
    text-align: center;
    font-size: 12px;
    font-weight: 600;
    color: #606266;
    height: 22px;
}

QProgressBar::chunk {
    background-color: #409EFF;
    border-radius: 10px;
}

/* ==================== 表格样式 ==================== */
QTableWidget {
    border: none;
    border-radius: 6px;
    background-color: #FFFFFF;
    gridline-color: #EBEEF5;
    alternate-background-color: #FAFBFC;
    font-size: 13px;
    color: #303133;
}

QTableWidget::item {
    padding: 8px 10px;
    border-bottom: 1px solid #EBEEF5;
}

QTableWidget::item:selected {
    background-color: #ECF5FF;
    color: #409EFF;
}

QHeaderView::section {
    background-color: #F5F7FA;
    border: none;
    border-bottom: 1px solid #EBEEF5;
    padding: 10px 8px;
    font-weight: 600;
    font-size: 13px;
    color: #606266;
}

/* ==================== 滚动区域 ==================== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 4px 2px;
}

QScrollBar::handle:vertical {
    background-color: #C0C4CC;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #909399;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    border-radius: 4px;
    margin: 2px 4px;
}

QScrollBar::handle:horizontal {
    background-color: #C0C4CC;
    border-radius: 4px;
    min-width: 40px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #909399;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* ==================== 分组框 ==================== */
QGroupBox {
    font-weight: 600;
    font-size: 15px;
    border: none;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 14px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 10px;
    color: #303133;
    background-color: #FFFFFF;
}

/* ==================== 消息框 ==================== */
QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QLabel {
    color: #606266;
    font-size: 14px;
}

QMessageBox QPushButton {
    min-width: 80px;
    padding: 8px 16px;
}

/* ==================== 工具提示 ==================== */
QToolTip {
    background-color: #303133;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ==================== 分割器 ==================== */
QSplitter::handle {
    background-color: #E4E7ED;
}

QSplitter::handle:hover {
    background-color: #DCDFE6;
}

QSplitter::handle:vertical {
    height: 6px;
    margin: 2px 0;
}
"""

# 动画持续时间
ANIMATION_DURATION = {
    'fast': 150,
    'normal': 300,
    'slow': 500,
}
