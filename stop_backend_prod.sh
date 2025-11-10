#!/bin/bash

PID_FILE="/home/ght/aim-develop/AIM-develop/.backend.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "正在停止后端服务 (PID: $PID)..."
        kill $PID
        sleep 2
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止..."
            kill -9 $PID
        fi
        echo "✓ 后端服务已停止"
        rm "$PID_FILE"
    else
        echo "后端服务未运行"
        rm "$PID_FILE"
    fi
else
    echo "未找到 PID 文件，尝试查找进程..."
    pkill -f "uvicorn app:app"
    echo "✓ 已尝试停止所有 uvicorn 进程"
fi

