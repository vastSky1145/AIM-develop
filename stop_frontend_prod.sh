#!/bin/bash
PID_FILE="/home/ght/aim-develop/AIM-develop/.frontend.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "正在停止前端服务 (PID: $PID)..."
    kill $PID
    rm "$PID_FILE"
    echo "✓ 前端服务已停止"
else
    echo "未找到 PID 文件，尝试查找 serve 进程..."
    pkill -f "serve -s dist"
fi
