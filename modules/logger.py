#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志模块 - 提供统一的日志记录功能
支持独立日志文件和统一日志
"""

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """日志管理器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.loggers = {}
        self.log_dir = config.get('log_dir', '/mnt/sd/camera1/logs')
        self.separate_logs = config.get('separate_logs', {})
        self.log_level = getattr(logging, config.get('log_level', 'INFO'))
        
        # 确保日志目录存在
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化根日志器
        self._init_root_logger()
        
        # 初始化各模块日志器
        if self.separate_logs.get('screenshot'):
            self.get_logger('screenshot')
        if self.separate_logs.get('lowfps'):
            self.get_logger('lowfps')
        if self.separate_logs.get('synthesis'):
            self.get_logger('synthesis')
        if self.separate_logs.get('upload'):
            self.get_logger('upload')
        if self.separate_logs.get('statistics'):
            self.get_logger('statistics')
        if self.separate_logs.get('alerts'):
            self.get_logger('alerts')
    
    def _init_root_logger(self):
        """初始化根日志器"""
        root_logger = logging.getLogger('camera_monitor')
        root_logger.setLevel(self.log_level)
        
        # 清除已有的处理器
        root_logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 主日志文件处理器
        main_log_file = os.path.join(self.log_dir, 'main.log')
        main_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        main_handler.setFormatter(file_formatter)
        root_logger.addHandler(main_handler)
        
        self.loggers['main'] = root_logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(f'camera_monitor.{name}')
        logger.setLevel(self.log_level)
        logger.handlers.clear()
        
        # 文件处理器
        log_file = os.path.join(self.log_dir, f'{name}.log')
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        handler.setLevel(self.log_level)
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        self.loggers[name] = logger
        return logger
    
    def info(self, message: str, module: str = 'main'):
        """记录INFO级别日志"""
        self.get_logger(module).info(message)
    
    def warning(self, message: str, module: str = 'main'):
        """记录WARNING级别日志"""
        self.get_logger(module).warning(message)
    
    def error(self, message: str, module: str = 'main'):
        """记录ERROR级别日志"""
        self.get_logger(module).error(message)
    
    def debug(self, message: str, module: str = 'main'):
        """记录DEBUG级别日志"""
        self.get_logger(module).debug(message)


# 全局日志器实例
_logger = None


def init_logger(config: dict) -> Logger:
    """初始化日志系统"""
    global _logger
    _logger = Logger(config)
    return _logger


def get_logger(module: str = 'main') -> logging.Logger:
    """获取日志器"""
    global _logger
    if _logger is None:
        raise RuntimeError("日志系统未初始化，请先调用init_logger()")
    return _logger.get_logger(module)
