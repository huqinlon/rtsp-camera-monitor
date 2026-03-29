#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动清理模块
自动清理过期的截图、视频、日志文件
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List


class CleanupManager:
    """自动清理管理器"""
    
    def __init__(self, config: dict, logger, alert_manager=None):
        self.config = config
        self.logger = logger
        self.alert_manager = alert_manager
        self.storage = config['storage']
        self.cleanup_config = config.get('cleanup', {})
        
        # 统计信息
        self.stats = {
            'total_deleted': 0,
            'total_freed_space': 0,
            'last_cleanup_time': None,
            'cleanup_details': []
        }
    
    def get_file_age_days(self, filepath: str) -> float:
        """获取文件年龄（天）"""
        try:
            mtime = os.path.getmtime(filepath)
            file_date = datetime.fromtimestamp(mtime)
            age = (datetime.now() - file_date).total_seconds() / 86400
            return age
        except:
            return 0
    
    def get_dir_size(self, path: str) -> int:
        """获取目录大小（字节）"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except:
            pass
        return total
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def cleanup_directory(self, dir_path: str, max_age_days: int, file_pattern: str = "*") -> Dict:
        """清理指定目录下的过期文件"""
        result = {
            'dir': dir_path,
            'scanned': 0,
            'deleted': 0,
            'failed': 0,
            'freed_space': 0,
            'errors': []
        }
        
        if not os.path.exists(dir_path):
            self.logger.warning(f"清理目录不存在: {dir_path}", module='cleanup')
            return result
        
        try:
            for filename in os.listdir(dir_path):
                filepath = os.path.join(dir_path, filename)
                
                # 跳过目录
                if os.path.isdir(filepath):
                    continue
                
                # 检查文件模式
                if file_pattern != "*":
                    if not filename.endswith(file_pattern.replace("*", "")):
                        continue
                
                result['scanned'] += 1
                
                # 检查文件年龄
                age = self.get_file_age_days(filepath)
                
                if age > max_age_days:
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        result['deleted'] += 1
                        result['freed_space'] += file_size
                    except Exception as e:
                        result['failed'] += 1
                        result['errors'].append(f"{filename}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"清理目录失败: {dir_path}, {str(e)}", module='cleanup')
            result['errors'].append(str(e))
        
        return result
    
    def check_disk_space(self) -> Dict:
        """检查磁盘空间"""
        screenshot_dir = self.storage.get('screenshot_dir', '/mnt/sd/camera1/screenshots')
        video_dir = self.storage.get('video_dir', '/mnt/sd/camera1/videos')
        
        # 获取根分区或挂载点的可用空间
        try:
            stat = os.statvfs(screenshot_dir)
            free_gb = stat.f_bavail * stat.f_frsize / (1024 ** 3)
        except:
            free_gb = 0
        
        return {
            'free_space_gb': free_gb,
            'screenshot_size': self.get_dir_size(screenshot_dir),
            'video_size': self.get_dir_size(video_dir)
        }
    
    def force_cleanup_on_low_space(self) -> bool:
        """当磁盘空间不足时强制清理"""
        min_free = self.cleanup_config.get('min_free_space_gb', 10)
        
        disk_info = self.check_disk_space()
        free_gb = disk_info['free_space_gb']
        
        if free_gb < min_free:
            self.logger.warning(
                f"磁盘空间不足: 剩余 {free_gb:.1f}GB < 最小 {min_free}GB，尝试强制清理",
                module='cleanup'
            )
            
            # 强制清理所有7天前的文件
            self.cleanup_directory(
                self.storage['screenshot_dir'],
                7,
                '.jpg'
            )
            
            self.cleanup_directory(
                self.storage['video_dir'],
                7,
                '.mp4'
            )
            
            self.cleanup_directory(
                self.storage.get('lowfps_dir', '/mnt/sd/camera1/lowfps_videos'),
                3,
                '.mp4'
            )
            
            # 再次检查
            disk_info = self.check_disk_space()
            new_free = disk_info['free_space_gb']
            
            self.logger.info(f"强制清理后磁盘剩余: {new_free:.1f}GB", module='cleanup')
            
            # 触发告警
            if self.alert_manager and free_gb < min_free:
                self.alert_manager.trigger_alert(
                    'storage_full',
                    f"磁盘空间不足，剩余 {free_gb:.1f}GB，已尝试强制清理"
                )
            
            return True
        
        return False
    
    def run_cleanup(self) -> Dict:
        """执行清理任务"""
        self.logger.info("开始执行自动清理任务", module='cleanup')
        
        cleanup_config = self.cleanup_config
        screenshot_days = cleanup_config.get('screenshot_days', 7)
        video_days = cleanup_config.get('video_days', 30)
        lowfps_days = cleanup_config.get('lowfps_days', 7)
        log_days = cleanup_config.get('log_days', 30)
        
        results = {}
        
        # 1. 清理过期截图
        self.logger.info(f"清理{screenshot_days}天前的截图", module='cleanup')
        results['screenshots'] = self.cleanup_directory(
            self.storage['screenshot_dir'],
            screenshot_days,
            '.jpg'
        )
        
        # 2. 清理过期视频
        self.logger.info(f"清理{video_days}天前的视频", module='cleanup')
        results['videos'] = self.cleanup_directory(
            self.storage['video_dir'],
            video_days,
            '.mp4'
        )
        
        # 3. 清理低帧率视频
        lowfps_dir = self.storage.get('lowfps_dir', '/mnt/sd/camera1/lowfps_videos')
        if os.path.exists(lowfps_dir):
            self.logger.info(f"清理{lowfps_days}天前的低帧率视频", module='cleanup')
            results['lowfps'] = self.cleanup_directory(
                lowfps_dir,
                lowfps_days,
                '.mp4'
            )
        
        # 4. 清理过期日志
        log_dir = self.config.get('logging', {}).get('log_dir', '/mnt/sd/camera1/logs')
        if os.path.exists(log_dir):
            self.logger.info(f"清理{log_days}天前的日志", module='cleanup')
            results['logs'] = self.cleanup_directory(
                log_dir,
                log_days,
                '.log'
            )
        
        # 5. 清理临时目录
        temp_dir = self.storage.get('temp_dir', '/mnt/sd/camera1/temp')
        if os.path.exists(temp_dir):
            self.logger.info("清理临时目录", module='cleanup')
            results['temp'] = self.cleanup_directory(temp_dir, 1, '*')
        
        # 6. 检查磁盘空间
        disk_info = self.check_disk_space()
        
        # 统计结果
        total_deleted = 0
        total_freed = 0
        
        for key, result in results.items():
            if isinstance(result, dict):
                total_deleted += result.get('deleted', 0)
                total_freed += result.get('freed_space', 0)
        
        self.stats['total_deleted'] += total_deleted
        self.stats['total_freed_space'] += total_freed
        self.stats['last_cleanup_time'] = datetime.now().isoformat()
        self.stats['cleanup_details'] = results
        
        self.logger.info(
            f"清理完成: 删除 {total_deleted} 个文件，释放 {self.format_size(total_freed)}，"
            f"剩余磁盘空间 {disk_info['free_space_gb']:.1f}GB",
            module='cleanup'
        )
        
        # 如果空间仍然不足，触发告警
        if disk_info['free_space_gb'] < cleanup_config.get('min_free_space_gb', 10):
            if self.alert_manager:
                self.alert_manager.trigger_alert(
                    'storage_full',
                    f"磁盘空间不足: 剩余 {disk_info['free_space_gb']:.1f}GB"
                )
        
        return results
    
    def get_stats(self) -> dict:
        """获取清理统计信息"""
        disk_info = self.check_disk_space()
        stats = self.stats.copy()
        stats['disk_info'] = disk_info
        return stats


def create_cleanup_manager(config: dict, logger, alert_manager=None) -> CleanupManager:
    """创建清理管理器实例"""
    return CleanupManager(config, logger, alert_manager)
