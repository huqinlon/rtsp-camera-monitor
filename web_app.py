#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP-LINK 摄像头录像压缩系统 - Web管理界面
提供配置文件管理、系统状态监控、日志查看等功能
"""

import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用
app = Flask(__name__)
app.secret_key = os.environ.get('WEB_SECRET_KEY', 'change-this-secret-key-in-production')
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

# 全局配置
CONFIG_PATH = os.environ.get('CONFIG_PATH', '/app/config.json')
BASE_DIR = os.environ.get('DATA_BASE_DIR', '/app/data')
SCREENSHOT_DIR = os.path.join(BASE_DIR, 'screenshots')
VIDEO_DIR = os.path.join(BASE_DIR, 'videos')
LOG_DIR = os.path.join(BASE_DIR, 'logs')


# =============================================================================
# 辅助函数
# =============================================================================

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"加载配置失败: {e}")
        return {}


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存配置失败: {e}")
        return False


def get_process_status():
    """获取进程状态"""
    pid_file = '/tmp/camera_monitor.pid'
    status = {
        'running': False,
        'pid': None,
        'memory_mb': 0,
        'cpu_percent': 0,
        'uptime': None
    }
    
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            try:
                import psutil
                process = psutil.Process(pid)
                status['running'] = True
                status['pid'] = pid
                status['memory_mb'] = process.memory_info().rss / 1024 / 1024
                status['cpu_percent'] = process.cpu_percent(interval=0.1)
                
                # 计算运行时间
                create_time = datetime.fromtimestamp(process.create_time())
                uptime_delta = datetime.now() - create_time
                hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                status['uptime'] = f"{hours}小时{minutes}分钟{seconds}秒"
                
            except (ImportError, psutil.NoSuchProcess):
                pass
    except:
        pass
    
    return status


def get_storage_info():
    """获取存储信息"""
    def get_dir_size(path):
        total = 0
        count = 0
        try:
            if os.path.exists(path):
                for dirpath, dirnames, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total += os.path.getsize(fp)
                            count += 1
        except:
            pass
        return total, count
    
    screenshot_size, screenshot_count = get_dir_size(SCREENSHOT_DIR)
    video_size, video_count = get_dir_size(VIDEO_DIR)
    
    # 获取磁盘可用空间
    try:
        stat = os.statvfs(BASE_DIR)
        free_gb = stat.f_bavail * stat.f_frsize / (1024 ** 3)
        total_gb = stat.f_blocks * stat.f_frsize / (1024 ** 3)
        used_percent = (total_gb - free_gb) / total_gb * 100
    except:
        free_gb = 0
        total_gb = 0
        used_percent = 0
    
    return {
        'screenshot': {
            'size': format_size(screenshot_size),
            'size_bytes': screenshot_size,
            'count': screenshot_count
        },
        'video': {
            'size': format_size(video_size),
            'size_bytes': video_size,
            'count': video_count
        },
        'disk': {
            'free_gb': round(free_gb, 2),
            'total_gb': round(total_gb, 2),
            'used_percent': round(used_percent, 1)
        }
    }


def format_size(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def get_today_stats():
    """获取今日统计"""
    today = datetime.now().strftime('%Y%m%d')
    
    screenshot_count = 0
    video_count = 0
    
    try:
        if os.path.exists(SCREENSHOT_DIR):
            for f in os.listdir(SCREENSHOT_DIR):
                if today in f and f.endswith('.jpg'):
                    screenshot_count += 1
    except:
        pass
    
    try:
        if os.path.exists(VIDEO_DIR):
            for f in os.listdir(VIDEO_DIR):
                if today in f and f.endswith('.mp4'):
                    video_count += 1
    except:
        pass
    
    return {
        'screenshot_count': screenshot_count,
        'video_count': video_count
    }


def get_recent_logs(lines=100):
    """获取最近的日志"""
    logs = []
    main_log = os.path.join(LOG_DIR, 'main.log')
    
    try:
        if os.path.exists(main_log):
            with open(main_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                logs = all_lines[-lines:] if len(all_lines) > lines else all_lines
    except:
        pass
    
    return logs


def restart_service():
    """重启服务"""
    try:
        # 停止现有进程
        pid_file = '/tmp/camera_monitor.pid'
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 9)
            except:
                pass
            os.remove(pid_file)
        
        # 启动新进程
        script_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen(
            [sys.executable, os.path.join(script_dir, 'camera_monitor.py')],
            cwd=script_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception as e:
        print(f"重启服务失败: {e}")
        return False


# =============================================================================
# 路由定义
# =============================================================================

@app.route('/')
def index():
    """首页/仪表盘"""
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    config = load_config()
    process_status = get_process_status()
    storage_info = get_storage_info()
    today_stats = get_today_stats()
    recent_logs = get_recent_logs(50)
    
    return render_template(
        'dashboard.html',
        config=config,
        process_status=process_status,
        storage_info=storage_info,
        today_stats=today_stats,
        recent_logs=recent_logs
    )


@app.route('/config')
def config_page():
    """配置管理页面"""
    config = load_config()
    return render_template('config.html', config=config)


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """配置API"""
    if request.method == 'GET':
        config = load_config()
        return jsonify(config)
    
    elif request.method == 'POST':
        data = request.get_json()
        if save_config(data):
            return jsonify({'success': True, 'message': '配置保存成功'})
        else:
            return jsonify({'success': False, 'message': '配置保存失败'})


@app.route('/logs')
def logs_page():
    """日志查看页面"""
    return render_template('logs.html')


@app.route('/api/logs')
def api_logs():
    """日志API"""
    lines = request.args.get('lines', 200, type=int)
    logs = get_recent_logs(lines)
    return jsonify({'logs': logs})


@app.route('/api/service/restart', methods=['POST'])
def api_restart():
    """重启服务API"""
    if restart_service():
        return jsonify({'success': True, 'message': '服务重启成功'})
    else:
        return jsonify({'success': False, 'message': '服务重启失败'})


@app.route('/api/status')
def api_status():
    """状态API"""
    process_status = get_process_status()
    storage_info = get_storage_info()
    today_stats = get_today_stats()
    
    return jsonify({
        'process': process_status,
        'storage': storage_info,
        'today': today_stats,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    """手动清理API"""
    try:
        from modules.cleanup import create_cleanup_manager
        config = load_config()
        logger = type('Logger', (), {
            'info': lambda self, msg, module=None: print(f"[INFO] {msg}"),
            'warning': lambda self, msg, module=None: print(f"[WARN] {msg}"),
            'error': lambda self, msg, module=None: print(f"[ERROR] {msg}")
        })()
        
        cleanup_mgr = create_cleanup_manager(config, logger, None)
        results = cleanup_mgr.run_cleanup()
        
        total_deleted = sum(r.get('deleted', 0) for r in results.values() if isinstance(r, dict))
        total_freed = sum(r.get('freed_space', 0) for r in results.values() if isinstance(r, dict))
        
        return jsonify({
            'success': True,
            'message': f'清理完成，删除 {total_deleted} 个文件，释放 {format_size(total_freed)}'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'})


@app.route('/api/synthesis', methods=['POST'])
def api_synthesis():
    """手动合成视频API"""
    try:
        from modules.synthesis import start_synthesis_service
        config = load_config()
        logger = type('Logger', (), {
            'info': lambda self, msg, module=None: print(f"[INFO] {msg}"),
            'warning': lambda self, msg, module=None: print(f"[WARN] {msg}"),
            'error': lambda self, msg, module=None: print(f"[ERROR] {msg}")
        })()
        
        synthesis_mgr = start_synthesis_service(config, logger, None)
        results = synthesis_mgr.synthesize_all()
        
        success = sum(results.values())
        total = len(results)
        
        return jsonify({
            'success': True,
            'message': f'视频合成完成，成功 {success}/{total} 个'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'合成失败: {str(e)}'})


# =============================================================================
# 启动应用
# =============================================================================

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """运行Web服务器"""
    # 确保目录存在
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='TP-LINK 摄像头监控系统 - Web管理界面')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=5000, help='监听端口')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("TP-LINK 摄像头监控系统 - Web管理界面")
    print("=" * 60)
    print(f"访问地址: http://{args.host}:{args.port}")
    print("=" * 60)
    
    run_web_server(args.host, args.port, args.debug)
