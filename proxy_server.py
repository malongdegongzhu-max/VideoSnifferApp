#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代理服务器模块 - 使用mitmproxy
"""

import asyncio
import threading
from mitmproxy import http
from mitmproxy.tools.main import mitmdump
from utils import is_video_url


class ProxyServer:
    def __init__(self, port=8888, callback=None):
        self.port = port
        self.callback = callback
        self.is_running = False
        self.thread = None
    
    def start(self):
        """启动代理服务器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_proxy, daemon=True)
        self.thread.start()
        print(f"✅ 代理服务器启动: 0.0.0.0:{self.port}")
    
    def stop(self):
        """停止代理服务器"""
        self.is_running = False
        print("⏹️ 代理服务器已停止")
    
    def _run_proxy(self):
        """运行代理（在独立线程中）"""
        try:
            # 创建addon实例
            addon = VideoSnifferAddon(self.callback)
            
            # 启动mitmdump
            asyncio.run(self._async_run(addon))
        except Exception as e:
            print(f"❌ 代理服务器错误: {e}")
            self.is_running = False
    
    async def _async_run(self, addon):
        """异步运行mitmdump"""
        from mitmproxy.tools.main import mitmdump
        
        # mitmdump 配置
        opts = [
            '--listen-host', '0.0.0.0',
            '--listen-port', str(self.port),
            '--ssl-insecure',  # 忽略SSL错误
            '--set', 'block_global=false',
            '-q'  # 安静模式
        ]
        
        # 运行mitmdump
        await mitmdump(opts, [addon])


class VideoSnifferAddon:
    """mitmproxy插件 - 嗅探视频URL"""
    
    def __init__(self, callback=None):
        self.callback = callback
    
    def request(self, flow: http.HTTPFlow):
        """处理HTTP请求"""
        url = flow.request.url
        
        # 检查是否是视频URL
        if is_video_url(url):
            print(f"✅ 捕获视频: {url}")
            
            # 提取请求头
            headers = {
                'Referer': flow.request.headers.get('Referer', ''),
                'User-Agent': flow.request.headers.get('User-Agent', ''),
                'Host': flow.request.headers.get('Host', '')
            }
            
            # 回调通知
            if self.callback:
                try:
                    self.callback(url, headers)
                except Exception as e:
                    print(f"回调错误: {e}")
    
    def response(self, flow: http.HTTPFlow):
        """处理HTTP响应（可用于获取文件大小等）"""
        pass