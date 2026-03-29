#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计推送模块
将系统统计信息推送到Memos
"""

import os
import requests
from datetime import datetime
from typing import Dict, List


class StatisticsManager:
    """统计信息管理器"""
    
    def __init__(self, config: dict, logger, screenshot_mgr=None, synthesis_mgr=None, upload_mgr=None):
        self.config = config
        self.logger = logger
        self.stats_config = config['statistics']
        self.storage = config['storage']
        
        # 关联的模块
        self.screenshot_mgr = screenshot_mgr
        self.synthesis_mgr = synthesis_mgr
        self.upload_mgr = upload_mgr
    
    def get_storage_info(self) -> Dict:
        """获取存储信息"""
        def get_dir_size(path):
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
        
        screenshot_size = get_dir_size(self.storage['screenshot_dir'])
        video_size = get_dir_size(self.storage['video_dir'])
        
        return {
            'screenshot_size': screenshot_size,
            'video_size': video_size,
            'total_size': screenshot_size + video_size,
            'screenshot_count': len([f for f in os.listdir(self.storage['screenshot_dir']) if f.endswith('.jpg')]) if os.path.exists(self.storage['screenshot_dir']) else 0,
            'video_count': len([f for f in os.listdir(self.storage['video_dir']) if f.endswith('.mp4')]) if os.path.exists(self.storage['video_dir']) else 0
        }
    
    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def generate_report(self) -> str:
        """生成统计报告"""
        # 获取各模块统计
        screenshot_stats = self.screenshot_mgr.get_stats() if self.screenshot_mgr else {}
        synthesis_stats = self.synthesis_mgr.get_stats() if self.synthesis_mgr else {}
        upload_stats = self.upload_mgr.get_stats() if self.upload_mgr else {}
        
        # 获取存储信息
        storage_info = self.get_storage_info()
        
        # 获取摄像头信息
        cameras = self.config.get('camera', {}).get('cameras', [])
        
        # 生成报告
        report = f"""📊 监控系统统计报告 - {datetime.now().strftime('%Y-%m-%d')}

🏠 摄像头状态
- 总数：{len(cameras)}
- 启用：{sum(1 for c in cameras if c.get('enabled', True))}

📸 截图统计
- 今日截图：{screenshot_stats.get('total_screenshots', 0)}张
- 截图失败：{screenshot_stats.get('failed_screenshots', 0)}次

🎬 视频合成
- 合成视频：{synthesis_stats.get('total_videos', 0)}个
- 合成失败：{synthesis_stats.get('failed_videos', 0)}次

☁️ 云端上传
- 上传成功：{upload_stats.get('total_uploads', 0)}个
- 上传失败：{upload_stats.get('failed_uploads', 0)}次

💾 存储使用
- 截图目录：{self.format_size(storage_info['screenshot_size'])} ({storage_info['screenshot_count']}个文件)
- 视频目录：{self.format_size(storage_info['video_size'])} ({storage_info['video_count']}个文件)
- 总计：{self.format_size(storage_info['total_size'])}

⏰ 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

#监控 #统计"""
        
        return report
    
    def push_to_memos(self, content: str) -> bool:
        """推送到Memos"""
        memos_config = self.stats_config
        
        if not memos_config.get('push_to_memos', False):
            return False
        
        api_url = memos_config.get('memos_api_url')
        token = memos_config.get('memos_token')
        visibility = memos_config.get('visibility', 'PUBLIC')
        tags = memos_config.get('tags', [])
        
        if not api_url or not token:
            self.logger.error("Memos配置不完整", module='statistics')
            return False
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'content': content,
            'visibility': visibility
        }
        
        if tags:
            data['tags'] = tags
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info("统计报告已推送到Memos", module='statistics')
                return True
            else:
                self.logger.error(f"Memos推送失败: {response.status_code} {response.text[:200]}", module='statistics')
                return False
                
        except Exception as e:
            self.logger.error(f"Memos推送异常: {str(e)}", module='statistics')
            return False
    
    def push_statistics(self) -> bool:
        """推送统计信息"""
        self.logger.info("开始生成并推送统计报告", module='statistics')
        
        report = self.generate_report()
        self.logger.info(f"统计报告内容:\n{report}", module='statistics')
        
        success = self.push_to_memos(report)
        
        if success:
            self.logger.info("统计推送成功", module='statistics')
        else:
            self.logger.error("统计推送失败", module='statistics')
        
        return success


def start_statistics_service(config: dict, logger, screenshot_mgr=None, synthesis_mgr=None, upload_mgr=None) -> StatisticsManager:
    """创建统计管理器实例"""
    manager = StatisticsManager(config, logger, screenshot_mgr, synthesis_mgr, upload_mgr)
    return manager
