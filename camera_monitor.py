#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP-LINK 摄像头录像压缩系统 - 主程序
支持定时截图、低帧率录制、视频合成、云端上传、统计推送、告警推送、自动清理
"""

import os
import sys
import json
import signal
import time
import argparse
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.logger import init_logger, get_logger
from modules.screenshot import start_screenshot_service
from modules.lowfps import start_lowfps_service
from modules.synthesis import start_synthesis_service
from modules.upload import start_upload_service
from modules.statistics import start_statistics_service
from modules.alerts import create_alert_manager
from modules.cleanup import create_cleanup_manager


class CameraMonitor:
    """摄像头监控系统主类"""
    
    def __init__(self, config_path: str = None):
        # 默认配置路径
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        self.config_path = config_path
        self.config = None
        self.logger = None
        self.scheduler = None
        
        # 各模块实例
        self.screenshot_mgr = None
        self.lowfps_mgr = None
        self.synthesis_mgr = None
        self.upload_mgr = None
        self.stats_mgr = None
        self.alert_mgr = None
        self.cleanup_mgr = None
        
        # 运行状态
        self.running = False
        
        # PID文件
        self.pid_file = '/tmp/camera_monitor.pid'
    
    def write_pid_file(self):
        """写入PID文件"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except:
            pass
    
    def remove_pid_file(self):
        """删除PID文件"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
    
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"配置文件加载成功: {self.config_path}")
            return True
        except FileNotFoundError:
            print(f"配置文件不存在: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"配置文件格式错误: {e}")
            return False
        except Exception as e:
            print(f"配置文件加载异常: {e}")
            return False
    
    def create_directories(self):
        """创建必要的目录"""
        storage = self.config.get('storage', {})
        
        dirs = [
            storage.get('screenshot_dir', '/mnt/sd/camera1/screenshots'),
            storage.get('video_dir', '/mnt/sd/camera1/videos'),
            storage.get('lowfps_dir', '/mnt/sd/camera1/lowfps_videos'),
            storage.get('temp_dir', '/mnt/sd/camera1/temp'),
            storage.get('log_dir', '/mnt/sd/camera1/logs')
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"目录创建完成", module='main')
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            self.logger.info(f"收到信号 {signum}，正在停止服务...", module='main')
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def setup_scheduled_tasks(self):
        """设置定时任务"""
        self.scheduler = BackgroundScheduler()
        
        synthesis_config = self.config.get('video_synthesis', {})
        upload_config = self.config.get('cloud_upload', {})
        stats_config = self.config.get('statistics', {})
        cleanup_config = self.config.get('cleanup', {})
        
        # 视频合成 - 每天凌晨1点
        if synthesis_config.get('enabled', False):
            synthesis_time = synthesis_config.get('schedule', '01:00')
            hour, minute = map(int, synthesis_time.split(':'))
            self.scheduler.add_job(
                self.run_daily_synthesis,
                'cron',
                hour=hour,
                minute=minute,
                id='video_synthesis',
                name='视频合成'
            )
            self.logger.info(f"视频合成任务已设置: 每天 {synthesis_time}", module='main')
        
        # 云端上传 - 每天凌晨2点
        if upload_config.get('enabled', False):
            upload_time = upload_config.get('schedule', '02:00')
            hour, minute = map(int, upload_time.split(':'))
            self.scheduler.add_job(
                self.run_daily_upload,
                'cron',
                hour=hour,
                minute=minute,
                id='cloud_upload',
                name='云端上传'
            )
            self.logger.info(f"云端上传任务已设置: 每天 {upload_time}", module='main')
        
        # 自动清理 - 每天凌晨3点
        if cleanup_config.get('enabled', False):
            cleanup_time = cleanup_config.get('schedule', '03:00')
            hour, minute = map(int, cleanup_time.split(':'))
            self.scheduler.add_job(
                self.run_daily_cleanup,
                'cron',
                hour=hour,
                minute=minute,
                id='cleanup',
                name='自动清理'
            )
            self.logger.info(f"自动清理任务已设置: 每天 {cleanup_time}", module='main')
        
        # 统计推送 - 每天早上8点
        if stats_config.get('enabled', False):
            stats_time = stats_config.get('schedule', '08:00')
            hour, minute = map(int, stats_time.split(':'))
            self.scheduler.add_job(
                self.run_daily_statistics,
                'cron',
                hour=hour,
                minute=minute,
                id='statistics',
                name='统计推送'
            )
            self.logger.info(f"统计推送任务已设置: 每天 {stats_time}", module='main')
        
        self.scheduler.start()
    
    def run_daily_synthesis(self):
        """执行每日视频合成"""
        self.logger.info("开始执行每日视频合成任务", module='main')
        
        if self.synthesis_mgr:
            try:
                results = self.synthesis_mgr.synthesize_all()
                success = sum(results.values())
                total = len(results)
                self.logger.info(f"视频合成任务完成: 成功{success}/{total}", module='main')
            except Exception as e:
                self.logger.error(f"视频合成任务异常: {str(e)}", module='main')
                if self.alert_mgr:
                    self.alert_mgr.trigger_alert('video_synthesis_failed', f'每日视频合成任务异常: {str(e)}')
    
    def run_daily_upload(self):
        """执行每日云端上传"""
        self.logger.info("开始执行每日云端上传任务", module='main')
        
        if self.upload_mgr:
            try:
                results = self.upload_mgr.upload_all()
                total = sum(len(r) for r in results.values())
                success = sum(sum(r.values()) for r in results.values())
                self.logger.info(f"云端上传任务完成: 成功{success}/{total}", module='main')
            except Exception as e:
                self.logger.error(f"云端上传任务异常: {str(e)}", module='main')
                if self.alert_mgr:
                    self.alert_mgr.trigger_alert('upload_failed', f'每日云端上传任务异常: {str(e)}')
    
    def run_daily_cleanup(self):
        """执行每日自动清理"""
        self.logger.info("开始执行每日自动清理任务", module='main')
        
        if self.cleanup_mgr:
            try:
                results = self.cleanup_mgr.run_cleanup()
                
                total_deleted = 0
                total_freed = 0
                for key, result in results.items():
                    if isinstance(result, dict):
                        total_deleted += result.get('deleted', 0)
                        total_freed += result.get('freed_space', 0)
                
                self.logger.info(
                    f"自动清理任务完成: 删除 {total_deleted} 个文件，"
                    f"释放 {self.cleanup_mgr.format_size(total_freed)}",
                    module='main'
                )
            except Exception as e:
                self.logger.error(f"自动清理任务异常: {str(e)}", module='main')
                if self.alert_manager:
                    self.alert_mgr.trigger_alert('cleanup_failed', f'每日自动清理任务异常: {str(e)}')
    
    def run_daily_statistics(self):
        """执行每日统计推送"""
        self.logger.info("开始执行每日统计推送任务", module='main')
        
        if self.stats_mgr:
            try:
                self.stats_mgr.push_statistics()
                self.logger.info("统计推送任务完成", module='main')
            except Exception as e:
                self.logger.error(f"统计推送任务异常: {str(e)}", module='main')
    
    def start(self):
        """启动监控系统"""
        print("=" * 60)
        print("TP-LINK 摄像头录像压缩系统")
        print("=" * 60)
        
        # 加载配置
        if not self.load_config():
            print("配置加载失败，系统退出")
            sys.exit(1)
        
        # 初始化日志
        logging_config = self.config.get('logging', {})
        self.logger = init_logger(logging_config)
        
        self.logger.info("=" * 60, module='main')
        self.logger.info("TP-LINK 摄像头录像压缩系统启动", module='main')
        self.logger.info("=" * 60, module='main')
        
        # 写入PID文件
        self.write_pid_file()
        
        # 创建目录
        self.create_directories()
        
        # 设置信号处理
        self.setup_signal_handlers()
        
        # 初始化告警模块
        alert_config = self.config.get('alerts', {})
        if alert_config.get('enabled', False):
            self.alert_mgr = create_alert_manager(self.config, self.logger)
            self.alert_mgr.start_monitoring()
        
        # 初始化清理模块
        cleanup_config = self.config.get('cleanup', {})
        if cleanup_config.get('enabled', False):
            self.cleanup_mgr = create_cleanup_manager(self.config, self.logger, self.alert_mgr)
        
        # 启动截图模块
        screenshot_config = self.config.get('scheme1_screenshot', {})
        if screenshot_config.get('enabled', False):
            self.screenshot_mgr = start_screenshot_service(
                self.config, 
                self.logger, 
                self.alert_mgr
            )
        
        # 启动低帧率录制模块
        lowfps_config = self.config.get('scheme3_lowfps', {})
        if lowfps_config.get('enabled', False):
            self.lowfps_mgr = start_lowfps_service(
                self.config, 
                self.logger, 
                self.alert_mgr
            )
        
        # 初始化其他模块
        self.synthesis_mgr = start_synthesis_service(self.config, self.logger, self.alert_mgr)
        self.upload_mgr = start_upload_service(self.config, self.logger, self.alert_mgr)
        self.stats_mgr = start_statistics_service(
            self.config, 
            self.logger,
            self.screenshot_mgr,
            self.synthesis_mgr,
            self.upload_mgr
        )
        
        # 设置定时任务
        self.setup_scheduled_tasks()
        
        self.running = True
        self.logger.info("系统启动完成", module='main')
        
        # 保持运行
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """停止监控系统"""
        self.logger.info("正在停止监控系统...", module='main')
        
        self.running = False
        
        # 删除PID文件
        self.remove_pid_file()
        
        # 停止各模块
        if self.screenshot_mgr:
            self.screenshot_mgr.stop()
        
        if self.lowfps_mgr:
            self.lowfps_mgr.stop()
        
        # 停止定时任务
        if self.scheduler:
            self.scheduler.shutdown()
        
        self.logger.info("监控系统已停止", module='main')
        print("\n系统已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TP-LINK 摄像头录像压缩系统')
    parser.add_argument(
        '-c', '--config',
        default=None,
        help='配置文件路径'
    )
    
    args = parser.parse_args()
    
    # 创建并启动监控
    monitor = CameraMonitor(args.config)
    monitor.start()


if __name__ == '__main__':
    main()
