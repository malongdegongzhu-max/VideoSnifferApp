#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
打包脚本 - 使用PyInstaller
"""

import PyInstaller.__main__
import os

# 打包配置
PyInstaller.__main__.run([
    'main.py',                          # 主程序
    '--name=微信视频号嗅探器Pro',         # 应用名称
    '--windowed',                        # 窗口模式(不显示控制台)
    '--onefile',                         # 打包成单个exe
    '--icon=icon.ico',                   # 图标(可选)
    '--add-data=README.txt;.',          # 添加文件(可选)
    '--hidden-import=mitmproxy',        # 隐藏导入
    '--hidden-import=PyQt5',
    '--hidden-import=requests',
    '--clean',                           # 清理临时文件
])

print("\n✅ 打包完成!")
print("📦 输出目录: dist/微信视频号嗅探器Pro.exe")