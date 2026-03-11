#!/usr/bin/env python3
"""
简单的 HTTP 服务器，用于本地预览 AI Article Writer 前端页面
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

# 切换到 web 目录
web_dir = Path(__file__).parent
os.chdir(web_dir)

PORT = 8080

Handler = http.server.SimpleHTTPRequestHandler

# 添加 MIME 类型支持
Handler.extensions_map.update({
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.html': 'text/html',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
})

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    url = f"http://localhost:{PORT}"
    print(f"\n🚀 AI Article Writer 前端服务已启动")
    print(f"📍 访问地址: {url}")
    print(f" 按 Ctrl+C 停止服务\n")

    # 自动打开浏览器
    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n 服务已停止")
