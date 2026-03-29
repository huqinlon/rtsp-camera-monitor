#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低帧率录制模块 - 方案三
在特定时间段进行极低帧率录制
"""

import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class LowFPSRecorder:
    """低帧率录像录制器"""
    
    def __init__(self, config: dict, logger, alert_manager=None):
        self.config = config
        self.logger = logger
        self.alert_manager = alert_manager
        self.cameras = config['camera']['cameras']
        self.storage = config['storage']
        self.scheme_config = config['scheme3_lowfps']
        
        # 确保目录存在
        Path(self.storage['lowfps_dir']).mkdir(parents=True, exist_ok=True)
        
        # 运行状态
        self.running = False
        self.recording_processes = {}
        self.threads = []
        
        # 统计信息
        self.stats = {
            'total_recording_time': 0,
            'recordings': []
        }
    
    def is_recording_time(self, camera_name: str) -> tuple:
        """检查当前是否在录制时间段内"""
        if not self.scheme_config.get('enabled', False):
            return False, None
        
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_time_str = f"{current_hour:02d}:{current_minute:02d}"
        
        periods = self.scheme_config.get('periods', [])
        
        for period in periods:
            start = period['start']
            end = period['end']
            
            # 处理跨天情况
            if start > end:
                if current_time_str >= start or current_time_str < end:
                    self.logger.info(
                        f"[{camera_name}] 当前在录制时间段内: {start}-{end}",
                        module='lowfps'
                    )
                    return True, period['name']
            else:
                if start <= current_time_str < end:
                    self.logger.info(
                        f"[{camera_name}] 当前在录制时间段内: {start}-{end}",
                        module='lowfps'
                    )
                    return True, period['name']
        
        return False, None
    
    def start_recording(self, camera: dict, period_name: str):
        """开始录制"""
        camera_name = camera['name']
        rtsp_url = camera['rtsp_url']
        frame_rate = self.scheme_config.get('frame_rate', 1)
        
        # 如果已经在录制，跳过
        if camera_name in self.recording_processes:
            return
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{camera_name}_{period_name}_{timestamp}.mp4"
        filepath = os.path.join(self.storage['lowfps_dir'], filename)
        
        # FFmpeg低帧率录制命令
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-r', str(frame_rate),
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-y',
            filepath
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.recording_processes[camera_name] = process
            
            self.logger.info(
                f"[{camera_name}] 开始低帧率录制: {filename} ({frame_rate}fps)",
                module='lowfps'
            )
            
            self.stats['recordings'].append({
                'camera': camera_name,
                'filename': filename,
                'start_time': datetime.now().isoformat(),
                'period': period_name
            })
            
        except Exception as e:
            self.logger.error(
                f"[{camera_name}] 启动录制失败: {str(e)}",
                module='lowfps'
            )
    
    def stop_recording(self, camera_name: str):
        """停止录制"""
        if camera_name not in self.recording_processes:
            return
        
        try:
            process = self.recording_processes[camera_name]
            process.terminate()
            
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            self.logger.info(
                f"[{camera_name}] 停止低帧率录制",
                module='lowfps'
            )
            
            # 更新统计
            for recording in self.stats['recordings']:
                if recording['camera'] == camera_name and 'end_time' not in recording:
                    recording['end_time'] = datetime.now().isoformat()
            
            del self.recording_processes[camera_name]
            
        except Exception as e:
            self.logger.error(
                f"[{camera_name}] 停止录制失败: {str(e)}",
                module='lowfps'
            )
    
    def recording_worker(self, camera: dict, stop_event: threading.Event):
        """录制监控工作线程"""
        camera_name = camera['name']
        
        while not stop_event.is_set():
            is_recording, period_name = self.is_recording_time(camera_name)
            
            if is_recording:
                if camera_name not in self.recording_processes:
                    self.start_recording(camera, period_name)
            else:
                if camera_name in self.recording_processes:
                    self.stop_recording(camera_name)
            
            # 每分钟检查一次
            for _ in range(6):
                if stop_event.is_set():
                    break
                time.sleep(10)
    
    def start(self):
        """启动低帧率录制服务"""
        if not self.scheme_config.get('enabled', False):
            self.logger.info("方案三低帧率录制功能未启用", module='lowfps')
            return
        
        self.running = True
        self.logger.info("启动低帧率录制服务", module='lowfps')
        
        for camera in self.cameras:
            if not camera.get('enabled', True):
                continue
            
            stop_event = threading.Event()
            thread = threading.Thread(
                target=self.recording_worker,
                args=(camera, stop_event),
                daemon=True
            )
            thread.start()
            self.threads.append((stop_event, thread))
            self.logger.info(f"摄像头 {camera['name']} 录制监控线程已启动", module='lowfps')
    
    def stop(self):
        """停止低帧率录制服务"""
        self.running = False
        self.logger.info("停止低帧率录制服务", module='lowfps')
        
        # 停止所有录制
        for camera_name in list(self.recording_processes.keys()):
            self.stop_recording(camera_name)
        
        # 停止所有线程
        for stop_event, thread in self.threads:
            stop_event.set()
        
        for stop_event, thread in self.threads:
            thread.join(timeout=5)
        
        self.threads.clear()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy()


def start_lowfps_service(config: dict, logger, alert_manager=None) -> LowFPSRecorder:
    """启动低帧率录制服务"""
    recorder = LowFPSRecorder(config, logger, alert_manager)
    recorder.start()
    return recorder
