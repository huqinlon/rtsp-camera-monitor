#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警推送模块
监控系统异常并推送到PushPlus
"""

import os
import requests
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        self.alert_config = config['alerts']
        
        # 告警状态
        self.alert_states = {}
        self.offline_cameras = {}
        
        # 告警历史
        self.alert_history = []
    
    def check_camera_status(self):
        """检查摄像头在线状态"""
        if not self.alert_config.get('alert_types', {}).get('camera_offline', False):
            return
    
        # TODO: 实现实际的摄像头状态检查
    
    def trigger_alert(self, alert_type: str, message: str):
        """触发告警"""
        alert_types = self.alert_config.get('alert_types', {})
        
        if not alert_types.get(alert_type, False):
            return
        
        # 检查是否重复告警（5分钟内不重复）
        if alert_type in self.alert_states:
            last_triggered = self.alert_states[alert_type].get('last_triggered')
            if last_triggered:
                time_diff = (datetime.now() - last_triggered).total_seconds()
                if time_diff < 300:
                    self.logger.debug(f"告警被忽略（5分钟内重复）: {alert_type}", module='alerts')
                    return
        
        # 记录告警
        self.alert_states[alert_type] = {
            'last_triggered': datetime.now(),
            'count': self.alert_states.get(alert_type, {}).get('count', 0) + 1
        }
        
        alert_record = {
            'type': alert_type,
            'message': message,
            'time': datetime.now().isoformat()
        }
        self.alert_history.append(alert_record)
        
        # 推送告警
        self.push_alert(alert_type, message)
    
    def push_alert(self, alert_type: str, message: str):
        """推送告警到PushPlus"""
        if not self.alert_config.get('push_to_pushplus', False):
            return
        
        token = self.alert_config.get('pushplus_token')
        
        if not token:
            self.logger.error("PushPlus token未配置", module='alerts')
            return
        
        # 告警标题
        titles = {
            'camera_offline': '🔴 摄像头离线',
            'rtsp_connect_failed': '🟡 RTSP连接失败',
            'storage_full': '🔴 存储空间不足',
            'screenshot_failed': '🟡 截图失败',
            'video_synthesis_failed': '🟡 视频合成失败',
            'upload_failed': '🟡 上传失败'
        }
        
        title = titles.get(alert_type, '⚠️ 告警通知')
        
        # 构建内容
        content = f"""{title}

⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 详情：{message}

🔧 建议：请检查相关服务或设备状态"""
        
        # PushPlus API
        url = 'http://www.pushplus.plus/send'
        
        data = {
            'token': token,
            'title': title,
            'content': content,
            'template': 'txt'
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    self.logger.info(f"告警推送成功: {alert_type}", module='alerts')
                else:
                    self.logger.error(f"告警推送失败: {result.get('msg')}", module='alerts')
            else:
                self.logger.error(f"告警推送失败: HTTP {response.status_code}", module='alerts')
                
        except Exception as e:
            self.logger.error(f"告警推送异常: {str(e)}", module='alerts')
    
    def start_monitoring(self):
        """启动告警监控"""
        if not self.alert_config.get('enabled', False):
            return
        
        interval = self.alert_config.get('check_interval_minutes', 5)
        
        self.logger.info(f"启动告警监控（检查间隔: {interval}分钟）", module='alerts')
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """获取告警历史"""
        return self.alert_history[-limit:]


def create_alert_manager(config: dict, logger) -> AlertManager:
    """创建告警管理器实例"""
    manager = AlertManager(config, logger)
    return manager
