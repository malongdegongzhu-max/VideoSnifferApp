#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
下载管理器模块
"""

import os
import time
import requests
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from utils import format_size, format_speed


class DownloadManager:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks = {}  # {video_id: DownloadTask}
        self.download_dir = 'downloads'
        self.video_dir = os.path.join(self.download_dir, 'videos')
        self.cover_dir = os.path.join(self.download_dir, 'covers')
        
        # 创建目录
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.cover_dir, exist_ok=True)
    
    def download_video(self, video_id, url, filename, callback=None):
        """下载视频"""
        save_path = os.path.join(self.video_dir, filename)
        task = DownloadTask(video_id, url, save_path, callback)
        self.tasks[video_id] = task
        self.executor.submit(task.start)
        return task
    
    def download_cover(self, video_id, url, filename, callback=None):
        """下载封面"""
        save_path = os.path.join(self.cover_dir, filename)
        task = DownloadTask(video_id, url, save_path, callback)
        self.executor.submit(task.start)
        return task
    
    def get_task(self, video_id):
        """获取下载任务"""
        return self.tasks.get(video_id)
    
    def cancel_task(self, video_id):
        """取消下载任务"""
        task = self.tasks.get(video_id)
        if task:
            task.cancel()


class DownloadTask:
    def __init__(self, video_id, url, save_path, callback=None):
        self.video_id = video_id
        self.url = url
        self.save_path = save_path
        self.callback = callback
        
        self.status = 'pending'  # pending, downloading, completed, failed, cancelled
        self.progress = 0
        self.total_size = 0
        self.downloaded_size = 0
        self.speed = 0
        self.error = None
        self.cancelled = False
        
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始下载"""
        self.status = 'downloading'
        self.start_time = time.time()
        
        try:
            self._download()
            
            if not self.cancelled:
                self.status = 'completed'
                self.progress = 100
                self.end_time = time.time()
                print(f"✅ 下载完成: {os.path.basename(self.save_path)}")
            else:
                self.status = 'cancelled'
                print(f"⏹️ 下载取消: {os.path.basename(self.save_path)}")
            
        except Exception as e:
            self.status = 'failed'
            self.error = str(e)
            print(f"❌ 下载失败: {os.path.basename(self.save_path)} - {e}")
        
        finally:
            if self.callback:
                try:
                    self.callback(self)
                except:
                    pass
    
    def _download(self):
        """执行下载"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        # 支持断点续传
        downloaded = 0
        if os.path.exists(self.save_path):
            downloaded = os.path.getsize(self.save_path)
            headers['Range'] = f'bytes={downloaded}-'
        
        response = requests.get(self.url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        # 获取总大小
        if 'Content-Length' in response.headers:
            self.total_size = int(response.headers['Content-Length'])
            if downloaded > 0:
                self.total_size += downloaded
        
        # 下载文件
        mode = 'ab' if downloaded > 0 else 'wb'
        chunk_size = 1024 * 1024  # 1MB
        
        last_time = time.time()
        last_downloaded = downloaded
        
        with open(self.save_path, mode) as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if self.cancelled:
                    break
                
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    self.downloaded_size = downloaded
                    
                    # 更新进度
                    if self.total_size > 0:
                        self.progress = int(downloaded / self.total_size * 100)
                    
                    # 计算速度
                    current_time = time.time()
                    if current_time - last_time >= 1:
                        time_diff = current_time - last_time
                        size_diff = downloaded - last_downloaded
                        self.speed = size_diff / time_diff
                        last_time = current_time
                        last_downloaded = downloaded
    
    def cancel(self):
        """取消下载"""
        self.cancelled = True
    
    def get_info(self):
        """获取下载信息"""
        return {
            'video_id': self.video_id,
            'status': self.status,
            'progress': self.progress,
            'total_size': self.total_size,
            'downloaded_size': self.downloaded_size,
            'speed': self.speed,
            'speed_text': format_speed(self.speed),
            'size_text': format_size(self.total_size),
            'error': self.error
        }