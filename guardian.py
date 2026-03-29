#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程守护脚本
用于在非systemd环境下监控和自动重启主程序
支持自动检测进程状态、内存使用、资源限制等
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import argparse
from datetime import datetime
from pathlib import Path


class ProcessGuardian:
    """进程守护器"""
    
    def __init__(self, config_path: str = None):
        # 默认配置路径
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'config.json'
            )
        
        self.config_path = config_path
        self.config = self.load_config()
        
        # 守护配置
        guardian_config = self.config.get('guardian', {})
        self.enabled = guardian_config.get('enabled', True)
        self.check_interval = guardian_config.get('check_interval_minutes', 5) * 60
        self.auto_restart = guardian_config.get('auto_restart', True)
        self.max_memory_mb = guardian_config.get('max_memory_mb', 500)
        self.restart_on_error = guardian_config.get('restart_on_error', True)
        
        # 进程信息
        self.process_name = 'camera_monitor.py'
        self.process = None
        self.pid_file = '/tmp/camera_monitor.pid'
        self.last_restart_time = None
        self.restart_count = 0
        self.max_restart_per_hour = 5
        
        # 日志
        self.log_dir = os.environ.get('LOG_DIR', '/app/data/logs')
        self.log_file = os.path.join(self.log_dir, 'guardian.log')
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"配置文件加载失败: {e}")
            return {}
    
    def log(self, message: str, level: str = "INFO"):
        """写入日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except:
            pass
        
        # 同时输出到控制台
        print(log_message.strip())
    
    def get_process_pid(self) -> int:
        """获取主进程PID"""
        # 检查PID文件
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                return pid
            except:
                pass
        
        # 通过进程名查找
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and self.process_name in ' '.join(cmdline):
                    return proc.info['pid']
            except:
                continue
        
        return None
    
    def is_process_running(self) -> bool:
        """检查进程是否在运行"""
        pid = self.get_process_pid()
        
        if pid is None:
            return False
        
        try:
            process = psutil.Process(pid)
            
            # 检查进程状态
            if process.status() in [psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED]:
                return False
            
            # 检查进程是否是对应的脚本
            cmdline = process.cmdline()
            if not cmdline:
                return False
            
            if self.process_name not in ' '.join(cmdline):
                return False
            
            return True
            
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            self.log(f"检查进程状态异常: {e}", "ERROR")
            return False
    
    def get_process_info(self) -> dict:
        """获取进程信息"""
        pid = self.get_process_pid()
        
        if pid is None:
            return None
        
        try:
            process = psutil.Process(pid)
            
            return {
                'pid': pid,
                'status': process.status(),
                'cpu_percent': process.cpu_percent(interval=1),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'create_time': datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                'cmdline': ' '.join(process.cmdline())
            }
            
        except psutil.NoSuchProcess:
            return None
        except Exception as e:
            self.log(f"获取进程信息异常: {e}", "ERROR")
            return None
    
    def check_and_restart(self) -> bool:
        """检查并重启进程"""
        # 检查进程是否在运行
        if not self.is_process_running():
            self.log("主进程未运行，准备启动...", "WARN")
            return self.start_process()
        
        # 检查进程资源使用
        process_info = self.get_process_info()
        
        if process_info:
            # 检查内存使用
            if process_info['memory_mb'] > self.max_memory_mb:
                self.log(
                    f"内存使用过高: {process_info['memory_mb']:.1f}MB > {self.max_memory_mb}MB，"
                    f"正在重启进程...",
                    "WARN"
                )
                self.stop_process()
                time.sleep(2)
                return self.start_process()
            
            # 检查进程状态
            if process_info['status'] in [psutil.STATUS_ZOMBIE, psutil.STATUS_STOPPED]:
                self.log(f"进程状态异常: {process_info['status']}，正在重启...", "WARN")
                self.stop_process()
                time.sleep(2)
                return self.start_process()
            
            self.log(
                f"进程运行正常: PID={process_info['pid']}, "
                f"内存={process_info['memory_mb']:.1f}MB, "
                f"CPU={process_info['cpu_percent']:.1f}%, "
                f"线程={process_info['num_threads']}",
                "INFO"
            )
        
        return True
    
    def start_process(self) -> bool:
        """启动主进程"""
        # 检查重启频率
        if self.last_restart_time:
            time_since_restart = (datetime.now() - self.last_restart_time).total_seconds()
            if time_since_restart < 3600:  # 1小时内
                if self.restart_count >= self.max_restart_per_hour:
                    self.log(
                        f"1小时内重启次数已达到 {self.restart_count} 次，停止重启",
                        "ERROR"
                    )
                    return False
            else:
                self.restart_count = 0
        
        try:
            # 获取脚本路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, 'camera_monitor.py')
            
            # 启动进程
            self.log(f"正在启动主进程: {script_path}", "INFO")
            
            process = subprocess.Popen(
                [sys.executable, script_path],
                cwd=script_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # 写入PID文件
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
            
            self.last_restart_time = datetime.now()
            self.restart_count += 1
            
            self.log(
                f"主进程启动成功: PID={process.pid}, "
                f"重启次数={self.restart_count}",
                "INFO"
            )
            
            return True
            
        except Exception as e:
            self.log(f"启动主进程失败: {e}", "ERROR")
            return False
    
    def stop_process(self) -> bool:
        """停止主进程"""
        pid = self.get_process_pid()
        
        if pid is None:
            self.log("进程未运行，无需停止", "INFO")
            return True
        
        try:
            # 发送SIGTERM信号
            self.log(f"正在停止进程: PID={pid}", "INFO")
            
            try:
                process = psutil.Process(pid)
                process.terminate()
                
                # 等待进程退出
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # 强制杀死
                    process.kill()
                    self.log("进程已强制杀死", "WARN")
            
            except psutil.NoSuchProcess:
                pass
            
            # 删除PID文件
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
            
            self.log(f"进程已停止: PID={pid}", "INFO")
            return True
            
        except Exception as e:
            self.log(f"停止进程失败: {e}", "ERROR")
            return False
    
    def run(self):
        """运行守护进程"""
        if not self.enabled:
            self.log("守护进程未启用", "INFO")
            return
        
        self.log("=" * 50, "INFO")
        self.log("进程守护器启动", "INFO")
        self.log(f"检查间隔: {self.check_interval}秒", "INFO")
        self.log(f"最大内存: {self.max_memory_mb}MB", "INFO")
        self.log(f"自动重启: {self.auto_restart}", "INFO")
        self.log("=" * 50, "INFO")
        
        # 首次检查
        if not self.is_process_running():
            self.log("主进程未运行，正在启动...", "WARN")
            self.start_process()
        
        # 主循环
        try:
            while True:
                time.sleep(self.check_interval)
                
                if not self.check_and_restart():
                    self.log("进程检查失败", "ERROR")
        
        except KeyboardInterrupt:
            self.log("收到中断信号，守护进程退出", "INFO")
        except Exception as e:
            self.log(f"守护进程异常: {e}", "ERROR")
            sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TP-LINK 摄像头监控进程守护器')
    parser.add_argument(
        '-c', '--config',
        default=None,
        help='配置文件路径'
    )
    parser.add_argument(
        '-s', '--start',
        action='store_true',
        help='启动主进程'
    )
    parser.add_argument(
        '-k', '--stop',
        action='store_true',
        help='停止主进程'
    )
    parser.add_argument(
        '-r', '--restart',
        action='store_true',
        help='重启主进程'
    )
    parser.add_argument(
        '-t', '--status',
        action='store_true',
        help='查看进程状态'
    )
    
    args = parser.parse_args()
    
    guardian = ProcessGuardian(args.config)
    
    if args.status:
        # 查看状态
        if guardian.is_process_running():
            info = guardian.get_process_info()
            if info:
                print(f"\n进程状态: 运行中")
                print(f"  PID: {info['pid']}")
                print(f"  状态: {info['status']}")
                print(f"  内存: {info['memory_mb']:.1f}MB")
                print(f"  CPU: {info['cpu_percent']:.1f}%")
                print(f"  线程: {info['num_threads']}")
                print(f"  启动时间: {info['create_time']}")
            else:
                print("进程状态: 运行中（无法获取详细信息）")
        else:
            print("进程状态: 未运行")
        return
    
    if args.start:
        # 启动
        if guardian.is_process_running():
            print("进程已在运行")
        else:
            guardian.start_process()
        return
    
    if args.stop:
        # 停止
        guardian.stop_process()
        return
    
    if args.restart:
        # 重启
        guardian.stop_process()
        time.sleep(2)
        guardian.start_process()
        return
    
    # 默认启动守护进程
    guardian.run()


if __name__ == '__main__':
    import json
    main()
