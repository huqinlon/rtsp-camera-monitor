#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时截图模块 - 方案一
从RTSP流定时截图，支持分时段不同间隔（秒）
"""

import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ScreenshotCapture:
    """定时截图捕获器"""
    
    def __init__(self, config: dict, logger, alert_manager=None):
        self.config = config
        self.logger = logger
        self.alert_manager = alert_manager
        self.cameras = config['camera']['cameras']
        self.storage = config['storage']
        self.scheme_config = config['scheme1_screenshot']
        
        # 确保目录存在
        Path(self.storage['screenshot_dir']).mkdir(parents=True, exist_ok=True)
        
        # 运行状态
        self.running = False
        self.threads = []
        self.current_intervals = {}
        
        # 统计信息
        self.stats = {
            'total_screenshots': 0,
            'failed_screenshots': 0,
            'last_screenshot_time': {}
        }
    
    def format_interval(self, seconds: int) -> str:
        """格式化时间间隔为可读字符串"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            if secs == 0:
                return f"{minutes}分钟"
            return f"{minutes}分{secs}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes == 0:
                return f"{hours}小时"
            return f"{hours}小时{minutes}分钟"
    
    def get_current_interval(self, camera_name: str) -> int:
        """获取当前时间段的截图间隔（秒）"""
        if not self.scheme_config.get('enabled', False):
            return 0
        
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_time_str = f"{current_hour:02d}:{current_minute:02d}"
        
        intervals = self.scheme_config.get('intervals', [])
        
        for interval_config in intervals:
            start = interval_config['start']
            end = interval_config['end']
            interval_seconds = interval_config.get('interval_seconds', 300)  # 默认5分钟
            
            # 处理跨天情况（如22:00-06:00）
            if start > end:
                if current_time_str >= start or current_time_str < end:
                    self.logger.info(
                        f"[{camera_name}] 当前时间段: {start}-{end}, 间隔: {self.format_interval(interval_seconds)}",
                        module='screenshot'
                    )
                    return interval_seconds
            else:
                if start <= current_time_str < end:
                    self.logger.info(
                        f"[{camera_name}] 当前时间段: {start}-{end}, 间隔: {self.format_interval(interval_seconds)}",
                        module='screenshot'
                    )
                    return interval_seconds
        
        # 默认10分钟（600秒）
        return 600
    
    def capture_frame(self, camera: dict) -> bool:
        """从RTSP流截取一帧"""
        camera_name = camera['name']
        rtsp_url = camera['rtsp_url']
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{camera_name}_{timestamp}.jpg"
        filepath = os.path.join(self.storage['screenshot_dir'], filename)
        
        # FFmpeg截图命令
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-vframes', '1',
            '-q:v', '2',
            '-y',
            filepath
        ]
        
        try:
            # 设置超时
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=10,
                text=True
            )
            
            if result.returncode == 0 and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.logger.info(
                    f"[{camera_name}] 截图成功: {filename} ({file_size} bytes)",
                    module='screenshot'
                )
                self.stats['total_screenshots'] += 1
                self.stats['last_screenshot_time'][camera_name] = datetime.now().isoformat()
                return True
            else:
                self.logger.error(
                    f"[{camera_name}] 截图失败: {result.stderr[:200]}",
                    module='screenshot'
                )
                self.stats['failed_screenshots'] += 1
                
                # 触发告警
                if self.alert_manager:
                    self.alert_manager.trigger_alert(
                        'screenshot_failed',
                        f"摄像头 {camera_name} 截图失败"
                    )
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"[{camera_name}] 截图超时", module='screenshot')
            self.stats['failed_screenshots'] += 1
            return False
        except Exception as e:
            self.logger.error(f"[{camera_name}] 截图异常: {str(e)}", module='screenshot')
            self.stats['failed_screenshots'] += 1
            return False
    
    def capture_worker(self, camera: dict, stop_event: threading.Event):
        """截图工作线程"""
        camera_name = camera['name']
        
        # 首次截图
        self.capture_frame(camera)
        
        while not stop_event.is_set():
            # 获取当前间隔（秒）
            interval = self.get_current_interval(camera_name)
            
            if interval == 0:
                # 功能未启用，暂停1分钟
                time.sleep(60)
                continue
            
            # 等待指定秒数，每秒检查一次是否需要停止
            for _ in range(interval):
                if stop_event.is_set():
                    break
                time.sleep(1)
            
            if not stop_event.is_set():
                self.capture_frame(camera)
    
    def start(self):
        """启动截图服务"""
        if not self.scheme_config.get('enabled', False):
            self.logger.info("方案一截图功能未启用", module='screenshot')
            return
        
        self.running = True
        self.logger.info("启动定时截图服务", module='screenshot')
        
        # 打印配置的时间段信息
        intervals = self.scheme_config.get('intervals', [])
        for interval_config in intervals:
            interval_seconds = interval_config.get('interval_seconds', 300)
            self.logger.info(
                f"  时间段 {interval_config['start']}-{interval_config['end']}: "
                f"间隔 {self.format_interval(interval_seconds)}",
                module='screenshot'
            )
        
        for camera in self.cameras:
            if not camera.get('enabled', True):
                continue
            
            stop_event = threading.Event()
            thread = threading.Thread(
                target=self.capture_worker,
                args=(camera, stop_event),
                daemon=True
            )
            thread.start()
            self.threads.append((stop_event, thread))
            self.logger.info(f"摄像头 {camera['name']} 截图线程已启动", module='screenshot')
    
    def stop(self):
        """停止截图服务"""
        self.running = False
        self.logger.info("停止定时截图服务", module='screenshot')
        
        for stop_event, thread in self.threads:
            stop_event.set()
        
        # 等待线程结束
        for stop_event, thread in self.threads:
            thread.join(timeout=5)
        
        self.threads.clear()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


def start_screenshot_service(config: dict, logger, alert_manager=None) -> ScreenshotCapture:
    """启动截图服务"""
    capture = ScreenshotCapture(config, logger, alert_manager)
    capture.start()
    return capture
