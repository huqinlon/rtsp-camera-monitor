#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本
随机生成10张测试图片，全流程测试视频合成功能
"""

import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.synthesis import VideoSynthesizer
from modules.logger import init_logger


def generate_test_image(camera_name: str, image_num: int, output_path: str):
    """生成一张测试图片"""
    # 创建图片
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), color=(
        random.randint(50, 200),
        random.randint(50, 200),
        random.randint(50, 200)
    ))
    
    draw = ImageDraw.Draw(img)
    
    # 绘制一些随机图形
    for _ in range(random.randint(5, 15)):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        if random.choice([True, False]):
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
        else:
            draw.ellipse([x1, y1, x2, y2], outline=color, width=3)
    
    # 添加文字信息
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
    except:
        # 如果找不到，使用默认字体
        font = ImageFont.load_default()
    
    # 绘制文字
    text_lines = [
        f"测试图片 - {camera_name}",
        f"第 {image_num} 张",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"随机数: {random.randint(1000, 9999)}"
    ]
    
    y_offset = 100
    for line in text_lines:
        draw.text((100, y_offset), line, font=font, fill=(255, 255, 255))
        y_offset += 80
    
    # 添加时间戳水印
    timestamp_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    draw.text((width - 500, height - 80), timestamp_text, font=font, fill=(255, 255, 255))
    
    # 保存图片
    img.save(output_path, 'JPEG', quality=95)
    print(f"生成测试图片: {output_path}")


def generate_test_screenshots(test_dir: str, camera_name: str = "测试摄像头", count: int = 10):
    """生成指定数量的测试图片"""
    Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n开始生成 {count} 张测试图片...")
    print(f"保存目录: {test_dir}")
    print("-" * 50)
    
    for i in range(1, count + 1):
        # 生成时间戳（每隔10分钟一张）
        minutes_offset = (i - 1) * 10
        timestamp = datetime.now().replace(
            hour=8, minute=0, second=0
        ) + datetime.timedelta(minutes=minutes_offset)
        
        filename = f"{camera_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(test_dir, filename)
        
        generate_test_image(camera_name, i, filepath)
    
    print("-" * 50)
    print(f"测试图片生成完成！共 {count} 张")
    
    # 列出生成的文件
    files = sorted(os.listdir(test_dir))
    print(f"\n生成的文件列表:")
    for f in files:
        filepath = os.path.join(test_dir, f)
        size = os.path.getsize(filepath) / 1024
        print(f"  - {f} ({size:.1f} KB)")
    
    return files


def test_video_synthesis(screenshot_dir: str, output_dir: str):
    """测试视频合成功能"""
    print("\n" + "=" * 50)
    print("开始测试视频合成功能")
    print("=" * 50)
    
    # 模拟配置
    config = {
        'storage': {
            'screenshot_dir': screenshot_dir,
            'video_dir': output_dir,
            'temp_dir': os.path.join(output_dir, 'temp')
        },
        'video_synthesis': {
            'output_fps': 2,
            'codec': 'libx264',
            'quality': 23
        }
    }
    
    # 创建日志
    logging_config = {
        'log_dir': os.path.join(output_dir, 'logs'),
        'log_level': 'INFO',
        'separate_logs': {}
    }
    logger = init_logger(logging_config)
    
    # 创建合成器
    synthesizer = VideoSynthesizer(config, logger, None)
    
    # 执行合成
    results = synthesizer.synthesize_all()
    
    print("\n合成结果:")
    for camera_name, success in results.items():
        status = "成功" if success else "失败"
        print(f"  - {camera_name}: {status}")
    
    # 检查输出文件
    if os.path.exists(output_dir):
        video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
        print(f"\n生成的视频文件:")
        for f in video_files:
            filepath = os.path.join(output_dir, f)
            size = os.path.getsize(filepath) / 1024 / 1024
            print(f"  - {f} ({size:.2f} MB)")
    
    return results


def test_statistics_module(screenshot_dir: str):
    """测试统计模块"""
    print("\n" + "=" * 50)
    print("开始测试统计模块")
    print("=" * 50)
    
    # 统计截图数量
    if os.path.exists(screenshot_dir):
        jpg_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.jpg')]
        total_size = sum(os.path.getsize(os.path.join(screenshot_dir, f)) for f in jpg_files)
        
        print(f"截图总数: {len(jpg_files)}")
        print(f"总大小: {total_size / 1024 / 1024:.2f} MB")
        
        # 按摄像头分组统计
        camera_stats = {}
        for f in jpg_files:
            camera_name = f.split('_')[0]
            if camera_name not in camera_stats:
                camera_stats[camera_name] = {'count': 0, 'size': 0}
            camera_stats[camera_name]['count'] += 1
            camera_stats[camera_name]['size'] += os.path.getsize(os.path.join(screenshot_dir, f))
        
        print("\n各摄像头统计:")
        for camera_name, stats in camera_stats.items():
            print(f"  - {camera_name}: {stats['count']}张, {stats['size']/1024:.1f} KB")
    
    print("\n统计模块测试完成!")


def cleanup_test_files(test_dir: str):
    """清理测试文件"""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"已清理测试目录: {test_dir}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("TP-LINK 摄像头录像压缩系统 - 全流程测试")
    print("=" * 60)
    
    # 测试配置
    test_base_dir = "/tmp/camera_test"
    screenshot_dir = os.path.join(test_base_dir, "screenshots")
    video_dir = os.path.join(test_base_dir, "videos")
    camera_name = "测试摄像头"
    
    # 确保目录存在
    Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
    Path(video_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: 生成测试图片
        print("\n[Step 1] 生成测试图片")
        test_files = generate_test_screenshots(screenshot_dir, camera_name, 10)
        
        # Step 2: 测试视频合成
        print("\n[Step 2] 测试视频合成")
        test_video_synthesis(screenshot_dir, video_dir)
        
        # Step 3: 测试统计模块
        print("\n[Step 3] 测试统计模块")
        test_statistics_module(screenshot_dir)
        
        # 总结
        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)
        print(f"\n测试数据保存在: {test_base_dir}")
        print(f"  - 截图目录: {screenshot_dir}")
        print(f"  - 视频目录: {video_dir}")
        print("\n如需清理测试数据，请运行:")
        print(f"  rm -rf {test_base_dir}")
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
