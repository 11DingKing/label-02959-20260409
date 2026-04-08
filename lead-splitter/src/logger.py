"""
日志配置模块
统一管理应用日志
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerConfig:
    """日志配置类"""
    
    _initialized = False
    _log_dir: Optional[Path] = None
    
    @classmethod
    def setup(cls, log_dir: Optional[str] = None, level: int = logging.INFO):
        """
        配置日志系统
        
        Args:
            log_dir: 日志目录，默认为当前目录下的 logs 文件夹
            level: 日志级别
        """
        if cls._initialized:
            return
        
        # 设置日志目录
        if log_dir:
            cls._log_dir = Path(log_dir)
        else:
            cls._log_dir = Path.cwd() / "logs"
        
        cls._log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件名（按日期）
        log_file = cls._log_dir / f"lead_splitter_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 日志格式
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 文件记录更详细
        file_handler.setFormatter(formatter)
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        
        cls._initialized = True
        
        # 记录启动日志
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("日志系统初始化完成")
        logger.info(f"日志文件: {log_file}")
        logger.info("=" * 60)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            日志器实例
        """
        if not cls._initialized:
            cls.setup()
        return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    return LoggerConfig.get_logger(name)
