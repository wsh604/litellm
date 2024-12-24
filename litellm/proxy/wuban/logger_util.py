import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

class WubanLogger:
    _instance = None
    _logger = None
    _file_logging = False
    _console_logging = True
    _log_level = logging.DEBUG
    _logger_name = 'wuban'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WubanLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        if self._logger is not None:
            return self._logger

        # 获取根日志记录器并重置其处理器
        root_logger = logging.getLogger()
        root_logger.handlers = []
        
        # 创建 wuban logger
        logger = logging.getLogger(self._logger_name)
        # 重要：设置 propagate 为 False
        logger.propagate = False
        # 清除现有处理器
        logger.handlers = []
        logger.setLevel(self._log_level)

        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )

        # 如果启用文件日志
        if self._file_logging:
            # 创建日志目录（使用绝对路径）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # 生成日志文件名（包含日期）
            log_file = os.path.join(log_dir, f"wuban_{datetime.now().strftime('%Y%m%d')}.log")
            
            try:
                # 创建 RotatingFileHandler
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(self._log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                logger.debug(f"File logging enabled. Writing to: {log_file}")
            except Exception as e:
                print(f"Error setting up file handler: {str(e)}")

        # 如果启用控制台日志
        if self._console_logging:
            try:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(self._log_level)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
                logger.debug("Console logging enabled")
            except Exception as e:
                print(f"Error setting up console handler: {str(e)}")

        self._logger = logger
        return logger

    @classmethod
    def get_logger(cls):
        """获取logger实例"""
        if cls._instance is None:
            cls._instance = WubanLogger()
        return cls._instance._logger

    @classmethod
    def reset_logger(cls):
        """重置logger实例"""
        cls._instance = None
        return cls.get_logger()

    @classmethod
    def set_log_level(cls, level):
        """设置日志级别"""
        cls._log_level = level
        if cls._instance and cls._instance._logger:
            cls._instance._logger.setLevel(level)
            for handler in cls._instance._logger.handlers:
                handler.setLevel(level)

    @classmethod
    def enable_file_logging(cls):
        """启用文件日志"""
        cls._file_logging = True
        if cls._instance is not None:
            cls._instance = None  # 重置实例以重新配置logger
    
    @classmethod
    def disable_file_logging(cls):
        """禁用文件日志"""
        cls._file_logging = False
        if cls._instance is not None:
            cls._instance = None  # 重置实例以重新配置logger

    @classmethod
    def enable_console_logging(cls):
        """启用控制台日志"""
        cls._console_logging = True
        if cls._instance is not None:
            cls._instance = None  # 重置实例以重新配置logger
    
    @classmethod
    def disable_console_logging(cls):
        """禁用控制台日志"""
        cls._console_logging = False
        if cls._instance is not None:
            cls._instance = None  # 重置实例以重新配置logger

    @classmethod
    def set_logging_config(cls, file_logging: bool = True, console_logging: bool = True):
        """设置日志配置"""
        cls._file_logging = file_logging
        cls._console_logging = console_logging
        if cls._instance is not None:
            cls._instance = None  # 重置实例以重新配置logger