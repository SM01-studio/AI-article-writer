#!/bin/bash
# AI Article Writer - 本地开发环境启动脚本

echo "🚀 启动 AI Article Writer 本地环境..."

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 启动后端 API（后台运行）
echo "📡 启动后端 API (端口 5000)..."
python3 api_server.py &
API_PID=$!

# 等待后端启动
sleep 2

# 启动前端服务器
echo "🌐 启动前端服务器 (端口 8080)..."
echo ""
echo "✅ 本地环境已启动！"
echo "   前端: http://localhost:8080"
echo "   后端: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 捕获退出信号，关闭后端进程
trap "kill $API_PID 2>/dev/null; echo '服务已停止'; exit 0" INT TERM

# 启动前端服务器（前台运行）
python3 -m http.server 8080
