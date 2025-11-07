#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块
"""

import re
import hashlib
from datetime import datetime
from urllib.parse import urlparse, unquote


def format_size(size):
    """格式化文件大小"""
    if size == 0:
        return '未知'
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def format_speed(speed):
    """格式化速度"""
    if speed == 0:
        return '0 B/s'
    return f"{format_size(speed)}/s"


def extract_filename(url):
    """从URL提取文件名"""
    try:
        # 尝试从URL路径提取
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        # 匹配视频文件
        match = re.search(r'/([^/]+\.(?:mp4|m4v|m3u8|ts))(?:\?|$)', path)
        if match:
            return sanitize_filename(match.group(1))
        
        # 使用时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"video_{timestamp}_{url_hash}.mp4"
        
    except Exception as e:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"video_{timestamp}.mp4"


def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    # Windows 非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, '_', filename)
    
    # 限制长度
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:190] + ('.' + ext if ext else '')
    
    return filename


def is_video_url(url):
    """判断是否是视频URL"""
    # 域名特征
    weixin_domains = [
        'channels.weixin.qq.com',
        'finder.video.qq.com',
        'findermp.video.qq.com',
        'wxsnsdy.tc.qq.com',
        'wxsnsdythumb.tc.qq.com',
        'v.qq.com'
    ]
    
    # URL特征
    video_patterns = [
        r'\.mp4(\?.*)?$',
        r'\.m4v(\?.*)?$',
        r'\.m3u8(\?.*)?$',
        r'/findersnsvideo/',
        r'/findermp/',
        r'video_id=',
        r'media_id='
    ]
    
    # 检查域名
    try:
        domain = urlparse(url).hostname
        if any(d in domain for d in weixin_domains):
            # 检查URL模式
            if any(re.search(p, url, re.IGNORECASE) for p in video_patterns):
                # 排除缩略图
                if not any(x in url.lower() for x in ['thumb', 'cover', 'avatar']):
                    return True
    except:
        pass
    
    return False


def extract_cover_url(video_url):
    """尝试从视频URL提取封面URL"""
    cover_patterns = [
        # 替换路径
        lambda u: u.replace('/findersnsvideo/', '/findersnscover/'),
        lambda u: u.replace('/video/', '/cover/'),
        # 替换扩展名
        lambda u: re.sub(r'\.mp4(\?|$)', r'_thumb.jpg\1', u),
        lambda u: re.sub(r'\.mp4(\?|$)', r'.jpg\1', u),
    ]
    
    for pattern in cover_patterns:
        try:
            cover_url = pattern(video_url)
            if cover_url != video_url:
                return cover_url
        except:
            continue
    
    return None


def format_time(seconds):
    """格式化时间"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}小时{minutes}分"