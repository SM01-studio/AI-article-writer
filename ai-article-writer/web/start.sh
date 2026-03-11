#!/bin/bash

# AI Article Writer - 启动脚本
# 同时启动后端API服务和前端静态服务器

echo "========================================"
echo "🚀 AI Article Writer - Starting Services"
echo "========================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查是否安装了依赖
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed"
    exit 1
fi

# 安装Python依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask dependencies..."
    pip3 install flask flask-cors
fi

# 启动后端API服务 (后台运行)
echo ""
echo "🔧 Starting Backend API Server on port 5000..."
python3 api_server.py &
API_PID=$!
echo "   API PID: $API_PID"

# 等待API服务启动
sleep 2

# 检查API服务是否正常运行
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "   ✅ API Server is running"
else
    echo "   ⚠️ API Server might not be running properly"
fi

# 启动任务处理器 (后台运行)
echo ""
echo "🤖 Starting Task Processor..."
python3 task_processor.py &
TASK_PID=$!
echo "   Task Processor PID: $TASK_PID"

# 启动前端静态服务器 (后台运行)
echo ""
echo "🌐 Starting Frontend Server on port 8080..."
python3 server.py &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# 等待前端服务启动
sleep 1

echo ""
echo "========================================"
echo "✅ All services started!"
echo "========================================"
echo ""
echo "📍 Frontend:  http://localhost:8080"
echo "📍 API:       http://localhost:5000"
echo "📍 Health:    http://localhost:5000/api/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# 保存PID到文件
echo "$API_PID" > /tmp/ai_writer_api.pid
echo "$FRONTEND_PID" > /tmp/ai_writer_frontend.pid

# 捕获退出信号
trap "echo ''; echo '🛑 Stopping services...'; kill $API_PID $FRONTEND_PID 2>/dev/null; rm -f /tmp/ai_writer_*.pid; echo '✅ Services stopped'; exit 0" SIGINT SIGTERM

# 等待任意子进程结束
wait
