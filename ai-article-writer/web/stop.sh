#!/bin/bash

# AI Article Writer - 停止脚本

echo "🛑 Stopping AI Article Writer services..."

# 读取PID并终止进程
if [ -f /tmp/ai_writer_api.pid ]; then
    API_PID=$(cat /tmp/ai_writer_api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        kill $API_PID 2>/dev/null
        echo "   ✅ API Server stopped (PID: $API_PID)"
    fi
    rm -f /tmp/ai_writer_api.pid
fi

if [ -f /tmp/ai_writer_frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/ai_writer_frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   ✅ Frontend Server stopped (PID: $FRONTEND_PID)"
    fi
    rm -f /tmp/ai_writer_frontend.pid
fi

# 确保清理所有相关进程
pkill -f "api_server.py" 2>/dev/null
pkill -f "server.py" 2>/dev/null
pkill -f "task_processor.py" 2>/dev/null
echo "   ✅ Task Processor stopped"

echo "✅ All services stopped"
