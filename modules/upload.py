#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端上传模块
使用rclone将视频/截图上传到云端
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class CloudUploader:
    """云端上传器"""
    
    def __init__(self, config: dict, logger, alert_manager=None):
        self.config = config
        self.logger = logger
        self.alert_manager = alert_manager
        self.storage = config['storage']
        self.upload_config = config['cloud_upload']
        
        # 统计信息
        self.stats = {
            'total_uploads': 0,
            'failed_uploads': 0,
            'last_upload_time': None,
            'uploaded_files': []
        }
    
    def upload_file(self, local_path: str, remote_path: str = None) -> bool:
        """上传单个文件"""
        if not os.path.exists(local_path):
            self.logger.warning(f"文件不存在: {local_path}", module='upload')
            return False
        
        filename = os.path.basename(local_path)
        
        # 构建rclone命令
        rclone_config = self.upload_config.get('rclone_config', {})
        remote = rclone_config.get('remote', 'gdrive')
        
        if remote_path is None:
            remote_path = rclone_config.get('remote_path', '')
        
        remote_full_path = f"{remote}:{remote_path}/{filename}"
        
        cmd = [
            'rclone',
            'copyto',
            local_path,
            remote_full_path,
            '--update',
            '--verbose'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=600,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"上传成功: {filename}", module='upload')
                self.stats['total_uploads'] += 1
                self.stats['last_upload_time'] = datetime.now().isoformat()
                self.stats['uploaded_files'].append({
                    'filename': filename,
                    'local_path': local_path,
                    'upload_time': datetime.now().isoformat()
                })
                return True
            else:
                self.logger.error(f"上传失败: {filename}, {result.stderr[:200]}", module='upload')
                self.stats['failed_uploads'] += 1
                
                # 触发告警
                if self.alert_manager:
                    self.alert_manager.trigger_alert(
                        'upload_failed',
                        f"文件上传失败: {filename}"
                    )
                
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"上传超时: {filename}", module='upload')
            self.stats['failed_uploads'] += 1
            return False
        except Exception as e:
            self.logger.error(f"上传异常: {filename}, {str(e)}", module='upload')
            self.stats['failed_uploads'] += 1
            return False
    
    def upload_videos(self, date_str: str = None) -> Dict[str, bool]:
        """上传当天的视频文件"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        video_dir = self.storage['video_dir']
        results = {}
        
        # 查找当天视频
        for filename in os.listdir(video_dir):
            if filename.endswith('.mp4') and date_str in filename:
                filepath = os.path.join(video_dir, filename)
                results[filename] = self.upload_file(filepath)
        
        return results
    
    def upload_screenshots(self, date_str: str = None) -> Dict[str, bool]:
        """上传当天的截图文件"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        screenshot_dir = self.storage['screenshot_dir']
        results = {}
        
        # 查找当天截图
        for filename in os.listdir(screenshot_dir):
            if filename.endswith('.jpg') and date_str in filename:
                filepath = os.path.join(screenshot_dir, filename)
                results[filename] = self.upload_file(filepath)
        
        return results
    
    def upload_all(self) -> Dict[str, Dict[str, bool]]:
        """上传所有需要上传的文件"""
        self.logger.info("开始云端上传", module='upload')
        
        results = {}
        date_str = datetime.now().strftime('%Y%m%d')
        
        if self.upload_config.get('upload_videos', True):
            self.logger.info("上传视频文件", module='upload')
            results['videos'] = self.upload_videos(date_str)
        
        if self.upload_config.get('upload_screenshots', False):
            self.logger.info("上传截图文件", module='upload')
            results['screenshots'] = self.upload_screenshots(date_str)
        
        total = sum(len(r) for r in results.values())
        success = sum(sum(r.values()) for r in results.values())
        
        self.logger.info(
            f"云端上传完成: 成功{success}个, 失败{total-success}个",
            module='upload'
        )
        
        return results
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


def start_upload_service(config: dict, logger, alert_manager=None) -> CloudUploader:
    """创建云端上传器实例"""
    uploader = CloudUploader(config, logger, alert_manager)
    return uploader
