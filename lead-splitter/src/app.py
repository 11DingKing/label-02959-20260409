"""
应用入口模块
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from .logger import LoggerConfig, get_logger
from .main_window import MainWindow

LoggerConfig.setup()
logger = get_logger(__name__)


def main():
    """应用主入口"""
    logger.info("启动线索池数据分割工具")

    app = QApplication(sys.argv)
    app.setApplicationName("线索池数据分割工具")
    app.setApplicationVersion("1.0.0")

    font = QFont()
    font.setFamily("PingFang SC")
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
