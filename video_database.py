#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频数据库模块
"""

import json
import os
from datetime import datetime
from threading import Lock
from utils import extract_filename, extract_cover_url


class VideoDatabase:
    def __init__(self, db_path='videos.json'):
        self.db_path = db_path
        self.videos = []
        self.lock = Lock()
        self.load()
    
    def load(self):
        """加载数据库"""
        with self.lock:
            if os.path.exists(self.db_path):
                try:
                    with open(self.db_path, 'r', encoding='utf-8') as f:
                        self.videos = json.load(f)
                except Exception as e:
                    print(f"加载数据库失败: {e}")
                    self.videos = []
    
    def save(self):
        """保存数据库"""
        with self.lock:
            try:
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.videos, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"保存数据库失败: {e}")
    
    def add_video(self, url, headers=None):
        """添加视频"""
        with self.lock:
            # 检查是否已存在
            if any(v['url'] == url for v in self.videos):
                return None
            
            video_id = len(self.videos) + 1
            filename = extract_filename(url)
            cover_url = extract_cover_url(url)
            
            video = {
                'id': video_id,
                'url': url,
                'filename': filename,
                'cover_url': cover_url,
                'capture_time': datetime.now().isoformat(),
                'domain': self._extract_domain(url),
                'referer': headers.get('Referer', '') if headers else '',
                'user_agent': headers.get('User-Agent', '') if headers else '',
                'downloaded': False,
                'cover_downloaded': False,
                'download_path': None,
                'file_size': 0
            }
            
            self.videos.append(video)
            self.save()
            return video
    
    def update_video(self, video_id, updates):
        """更新视频信息"""
        with self.lock:
            for video in self.videos:
                if video['id'] == video_id:
                    video.update(updates)
                    self.save()
                    return True
            return False
    
    def get_all(self):
        """获取所有视频"""
        with self.lock:
            return sorted(self.videos, key=lambda x: x['capture_time'], reverse=True)
    
    def get_by_id(self, video_id):
        """根据ID获取视频"""
        with self.lock:
            return next((v for v in self.videos if v['id'] == video_id), None)
    
    def clear(self):
        """清空数据库"""
        with self.lock:
            self.videos = []
            self.save()
    
    def get_count(self):
        """获取视频数量"""
        with self.lock:
            return len(self.videos)
    
    def get_downloaded_count(self):
        """获取已下载数量"""
        with self.lock:
            return sum(1 for v in self.videos if v.get('downloaded'))
    
    @staticmethod
    def _extract_domain(url):
        """提取域名"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).hostname
        except:
            return 'unknown'