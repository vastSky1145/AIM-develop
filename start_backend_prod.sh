#!/bin/bash

echo "正在启动后端服务..."

# 1. 设置代理环境变量
# export http_proxy=http://127.0.0.1:7890
# export https_proxy=http://127.0.0.1:7890
# export HTTP_PROXY=http://127.0.0.1:7890
# export HTTPS_PROXY=http://127.0.0.1:7890
export HF_ENDPOINT=https://hf-mirror.com
export HUGGINGFACE_HUB_BASE_URL=https://hf-mirror.com

echo "✓ 代理已启用"

# 2. 后台启动 gunicorn(生产模式)
GUNICORN_CMD="gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000"
nohup $GUNICORN_CMD > /home/ght/aim-develop/AIM-develop/logs/backend.log 2>&1 &
GUNICORN_PID=$!

echo "✓ 后端服务启动中 (PID: $GUNICORN_PID)..."

# 3. 等待服务启动（检查健康检查端点）
for i in {1..30}; do
    sleep 1
    if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "✓ 后端服务已就绪"
        break
    fi
    echo "等待服务启动... ($i/30)"
done

# 4. 取消代理环境变量
# unset http_proxy
# unset https_proxy
# unset HTTP_PROXY
# unset HTTPS_PROXY

echo "✓ 代理已取消"
echo ""
echo "========================================="
echo "后端服务运行在: http://0.0.0.0:8000"
echo "进程 PID: $GUNICORN_PID"
echo ""
echo "查看日志: tail -f logs.txt"
echo "停止服务: kill $GUNICORN_PID"
echo "========================================="

# 保存 PID 到文件，方便后续停止
echo $GUNICORN_PID > /home/ght/aim-develop/AIM-develop/.backend.pid

# 将uvicorn的输出重定向到前台，这样可以看到日志
wait $GUNICORN_PID

