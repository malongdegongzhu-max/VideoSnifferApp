#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GUI界面模块
"""

import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox, QFileDialog, QGroupBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
from utils import format_size, format_speed


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 自定义信号
    video_captured = pyqtSignal(dict)
    download_progress = pyqtSignal(int, dict)
    
    def __init__(self, db, download_manager, proxy_server):
        super().__init__()
        self.db = db
        self.download_manager = download_manager
        self.proxy_server = proxy_server
        
        self.init_ui()
        self.setup_timer()
        
        # 连接信号
        self.video_captured.connect(self.on_video_captured)
        self.download_progress.connect(self.on_download_progress)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle('微信视频号嗅探器 Pro')
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 顶部状态栏
        layout.addWidget(self.create_status_panel())
        
        # 控制按钮
        layout.addWidget(self.create_control_panel())
        
        # 视频列表
        layout.addWidget(self.create_video_table())
        
        # 底部日志
        layout.addWidget(self.create_log_panel())
    
    def create_status_panel(self):
        """创建状态面板"""
        group = QGroupBox("系统状态")
        layout = QHBoxLayout()
        
        # 代理状态
        self.proxy_status = QLabel("🟢 代理运行中")
        self.proxy_status.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.proxy_status)
        
        layout.addStretch()
        
        # 统计信息
        self.stats_label = QLabel("已捕获: 0 | 已下载: 0")
        self.stats_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.stats_label)
        
        group.setLayout(layout)
        return group
    
    def create_control_panel(self):
        """创建控制面板"""
        group = QGroupBox("操作控制")
        layout = QHBoxLayout()
        
        # 刷新按钮
        btn_refresh = QPushButton("🔄 刷新列表")
        btn_refresh.clicked.connect(self.refresh_table)
        layout.addWidget(btn_refresh)
        
        # 批量下载
        btn_download_all = QPushButton("📥 下载全部")
        btn_download_all.clicked.connect(self.download_all)
        layout.addWidget(btn_download_all)
        
        # 打开下载目录
        btn_open_folder = QPushButton("📁 打开下载目录")
        btn_open_folder.clicked.connect(self.open_download_folder)
        layout.addWidget(btn_open_folder)
        
        # 清空列表
        btn_clear = QPushButton("🗑️ 清空列表")
        btn_clear.clicked.connect(self.clear_list)
        layout.addWidget(btn_clear)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def create_video_table(self):
        """创建视频表格"""
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'ID', '文件名', '域名', '捕获时间', '状态', '进度', '操作'
        ])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(5, 150)
        
        # 设置样式
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        return self.table
    
    def create_log_panel(self):
        """创建日志面板"""
        group = QGroupBox("运行日志")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group
    
    def setup_timer(self):
        """设置定时器"""
        # 每2秒刷新一次
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_table)
        self.refresh_timer.start(2000)
    
    def refresh_table(self):
        """刷新表格"""
        videos = self.db.get_all()
        self.table.setRowCount(len(videos))
        
        for row, video in enumerate(videos):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(str(video['id'])))
            
            # 文件名
            self.table.setItem(row, 1, QTableWidgetItem(video['filename']))
            
            # 域名
            self.table.setItem(row, 2, QTableWidgetItem(video['domain']))
            
            # 捕获时间
            from datetime import datetime
            capture_time = datetime.fromisoformat(video['capture_time'])
            time_str = capture_time.strftime('%Y-%m-%d %H:%M:%S')
            self.table.setItem(row, 3, QTableWidgetItem(time_str))
            
            # 状态
            task = self.download_manager.get_task(video['id'])
            if task:
                status = task.status
                if status == 'downloading':
                    status_text = '⬇️ 下载中'
                elif status == 'completed':
                    status_text = '✅ 已完成'
                elif status == 'failed':
                    status_text = '❌ 失败'
                else:
                    status_text = '⏸️ 等待中'
            elif video.get('downloaded'):
                status_text = '✅ 已完成'
            else:
                status_text = '📭 未下载'
            
            self.table.setItem(row, 4, QTableWidgetItem(status_text))
            
            # 进度条
            progress_widget = QWidget()
            progress_layout = QVBoxLayout(progress_widget)
            progress_layout.setContentsMargins(5, 5, 5, 5)
            
            progress_bar = QProgressBar()
            if task and task.status == 'downloading':
                progress_bar.setValue(task.progress)
                progress_bar.setFormat(f"{task.progress}% - {format_speed(task.speed)}")
            elif video.get('downloaded'):
                progress_bar.setValue(100)
                progress_bar.setFormat("100%")
            else:
                progress_bar.setValue(0)
                progress_bar.setFormat("0%")
            
            progress_layout.addWidget(progress_bar)
            self.table.setCellWidget(row, 5, progress_widget)
            
            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            # 下载按钮
            btn_download = QPushButton("⬇️ 下载")
            btn_download.clicked.connect(lambda checked, v=video: self.download_video(v))
            if task and task.status == 'downloading':
                btn_download.setEnabled(False)
            btn_layout.addWidget(btn_download)
            
            # 复制链接
            btn_copy = QPushButton("📋")
            btn_copy.clicked.connect(lambda checked, v=video: self.copy_url(v))
            btn_layout.addWidget(btn_copy)
            
            self.table.setCellWidget(row, 6, btn_widget)
        
        # 更新统计
        self.update_stats()
    
    def update_stats(self):
        """更新统计信息"""
        total = self.db.get_count()
        downloaded = self.db.get_downloaded_count()
        self.stats_label.setText(f"已捕获: {total} | 已下载: {downloaded}")
    
    def download_video(self, video):
        """下载视频"""
        def on_complete(task):
            if task.status == 'completed':
                self.db.update_video(video['id'], {
                    'downloaded': True,
                    'download_path': task.save_path,
                    'file_size': task.total_size
                })
                self.add_log(f"✅ 下载完成: {video['filename']}")
        
        self.download_manager.download_video(
            video['id'],
            video['url'],
            video['filename'],
            callback=on_complete
        )
        
        self.add_log(f"⬇️ 开始下载: {video['filename']}")
    
    def download_all(self):
        """下载全部"""
        videos = self.db.get_all()
        undownloaded = [v for v in videos if not v.get('downloaded')]
        
        if not undownloaded:
            QMessageBox.information(self, "提示", "没有未下载的视频")
            return
        
        reply = QMessageBox.question(
            self, '确认',
            f"确定下载 {len(undownloaded)} 个视频吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for video in undownloaded:
                self.download_video(video)
    
    def copy_url(self, video):
        """复制链接"""
        clipboard = QApplication.clipboard()
        clipboard.setText(video['url'])
        self.add_log(f"📋 已复制链接: {video['filename']}")
    
    def open_download_folder(self):
        """打开下载目录"""
        path = os.path.abspath(self.download_manager.video_dir)
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    
    def clear_list(self):
        """清空列表"""
        reply = QMessageBox.question(
            self, '确认',
            "确定清空所有记录吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.clear()
            self.refresh_table()
            self.add_log("🗑️ 已清空列表")
    
    def add_log(self, message):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f"[{timestamp}] {message}")
        
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_video_captured(self, video):
        """视频捕获回调"""
        self.add_log(f"✅ 捕获视频: {video['filename']}")
        self.refresh_table()
    
    def on_download_progress(self, video_id, progress):
        """下载进度回调"""
        pass
    
    def closeEvent(self, event):
        """关闭事件"""
        self.proxy_server.stop()
        event.accept()