#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频合成模块
将截图合成为浓缩视频
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import glob


class VideoSynthesizer:
    """视频合成器"""
    
    def __init__(self, config: dict, logger, alert_manager=None):
        self.config = config
        self.logger = logger
        self.alert_manager = alert_manager
        self.storage = config['storage']
        self.synthesis_config = config['video_synthesis']
        
        # 确保目录存在
        Path(self.storage['video_dir']).mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.stats = {
            'total_videos': 0,
            'failed_videos': 0,
            'last_synthesis_time': None
        }
    
    def get_screenshots_for_date(self, target_date: str = None) -> Dict[str, List[str]]:
        """获取指定日期的截图文件，按摄像头分组"""
        if target_date is None:
            target_date = datetime.now().strftime('%Y%m%d')
        
        screenshot_dir = self.storage['screenshot_dir']
        screenshots_by_camera = {}
        
        # 查找当天所有截图
        pattern = os.path.join(screenshot_dir, f"*_{target_date}_*.jpg")
        files = glob.glob(pattern)
        
        # 按摄像头分组
        for filepath in files:
            filename = os.path.basename(filepath)
            parts = filename.split('_')
            if len(parts) >= 2:
                camera_name = parts[0]
                if camera_name not in screenshots_by_camera:
                    screenshots_by_camera[camera_name] = []
                screenshots_by_camera[camera_name].append(filepath)
        
        # 排序
        for camera_name in screenshots_by_camera:
            screenshots_by_camera[camera_name].sort()
        
        return screenshots_by_camera
    
    def synthesize_video(self, camera_name: str, screenshots: List[str]) -> bool:
        """将截图合成为视频"""
        if not screenshots:
            self.logger.warning(f"[{camera_name}] 没有截图文件", module='synthesis')
            return False
        
        # 生成输出文件名
        target_date = datetime.now().strftime('%Y%m%d')
        output_filename = f"{camera_name}_摘要_{target_date}.mp4"
        output_filepath = os.path.join(self.storage['video_dir'], output_filename)
        
        # 创建临时目录存放符号链接（保持顺序）
        temp_dir = os.path.join(self.storage['temp_dir'], 'synthesis', camera_name)
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建符号链接
        for i, src_file in enumerate(screenshots):
            link_file = os.path.join(temp_dir, f"{i:04d}.jpg")
            if os.path.exists(link_file):
                os.remove(link_file)
            os.symlink(src_file, link_file)
        
        # FFmpeg合成命令
        input_pattern = os.path.join(temp_dir, '%04d.jpg')
        
        output_fps = self.synthesis_config.get('output_fps', 2)
        codec = self.synthesis_config.get('codec', 'libx264')
        quality = self.synthesis_config.get('quality', 23)
        
        cmd = [
            'ffmpeg',
            '-framerate', str(output_fps),
            '-i', input_pattern,
            '-c:v', codec,
            '-crf', str(quality),
            '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p',
            '-y',
            output_filepath
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300,
                text=True
            )
            
            if result.returncode == 0 and os.path.exists(output_filepath):
                file_size = os.path.getsize(output_filepath)
                duration = len(screenshots) / output_fps
                
                self.logger.info(
                    f"[{camera_name}] 视频合成成功: {output_filename} "
                    f"({len(screenshots)}帧, {duration:.1f}秒, {file_size/1024/1024:.1f}MB)",
                    module='synthesis'
                )
                
                self.stats['total_videos'] += 1
                self.stats['last_synthesis_time'] = datetime.now().isoformat()
                
                # 清理临时文件
                try:
                    for f in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, f))
                except:
                    pass
                
                return True
            else:
                self.logger.error(
                    f"[{camera_name}] 视频合成失败: {result.stderr[:200]}",
                    module='synthesis'
                )
                self.stats['failed_videos'] += 1
                
                # 触发告警
                if self.alert_manager:
                    self.alert_manager.trigger_alert(
                        'video_synthesis_failed',
                        f"摄像头 {camera_name} 视频合成失败"
                    )
                
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"[{camera_name}] 视频合成超时", module='synthesis')
            self.stats['failed_videos'] += 1
            return False
        except Exception as e:
            self.logger.error(f"[{camera_name}] 视频合成异常: {str(e)}", module='synthesis')
            self.stats['failed_videos'] += 1
            return False
    
    def synthesize_all(self) -> Dict[str, bool]:
        """合成所有摄像头的视频"""
        self.logger.info("开始每日视频合成", module='synthesis')
        
        screenshots_by_camera = self.get_screenshots_for_date()
        
        results = {}
        for camera_name, screenshots in screenshots_by_camera.items():
            results[camera_name] = self.synthesize_video(camera_name, screenshots)
        
        self.logger.info(f"视频合成完成: 成功{sum(results.values())}个, 失败{len(results)-sum(results.values())}个", module='synthesis')
        
        return results
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


def start_synthesis_service(config: dict, logger, alert_manager=None) -> VideoSynthesizer:
    """创建视频合成器实例"""
    synthesizer = VideoSynthesizer(config, logger, alert_manager)
    return synthesizer
