#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主程序入口
"""

import sys
import socket
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from video_database import VideoDatabase
from download_manager import DownloadManager
from proxy_server import ProxyServer
from gui_window import MainWindow


def get_local_ip():
    """获取本机IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def main():
    print("=" * 60)
    print("🎯 微信视频号嗅探器 Pro")
    print("=" * 60)
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 显示启动画面
    splash = QSplashScreen()
    splash.showMessage(
        "正在启动...",
        Qt.AlignCenter | Qt.AlignBottom,
        Qt.white
    )
    splash.show()
    app.processEvents()
    
    try:
        # 初始化数据库
        splash.showMessage("初始化数据库...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        db = VideoDatabase()
        
        # 初始化下载管理器
        splash.showMessage("初始化下载管理器...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        download_manager = DownloadManager(max_workers=3)
        
        # 初始化代理服务器
        splash.showMessage("启动代理服务器...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        
        def on_video_captured(url, headers):
            """视频捕获回调"""
            video = db.add_video(url, headers)
            if video and hasattr(window, 'video_captured'):
                window.video_captured.emit(video)
        
        proxy_server = ProxyServer(port=8888, callback=on_video_captured)
        proxy_server.start()
        
        # 创建主窗口
        splash.showMessage("加载界面...", Qt.AlignCenter | Qt.AlignBottom, Qt.white)
        window = MainWindow(db, download_manager, proxy_server)
        
        # 显示使用说明
        local_ip = get_local_ip()
        window.add_log("=" * 40)
        window.add_log("🎯 微信视频号嗅探器 Pro 已启动")
        window.add_log("=" * 40)
        window.add_log(f"📡 代理服务器: {local_ip}:8888")
        window.add_log("📱 手机设置步骤:")
        window.add_log("   1. WiFi设置 → 代理 → 手动")
        window.add_log(f"   2. 服务器: {local_ip}")
        window.add_log("   3. 端口: 8888")
        window.add_log("   4. 安装证书: http://mitm.it")
        window.add_log("=" * 40)
        window.add_log("✅ 准备就绪，等待捕获视频...")
        
        # 关闭启动画面
        splash.finish(window)
        
        # 显示主窗口
        window.show()
        
        # 运行应用
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "错误", f"启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()