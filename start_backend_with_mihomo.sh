#!/bin/bash

echo "正在启动后端服务..."

# 1. 设置代理环境变量
export http_proxy=http://127.0.0.1:17890
export https_proxy=http://127.0.0.1:17890
export HTTP_PROXY=http://127.0.0.1:17890
export HTTPS_PROXY=http://127.0.0.1:17890

echo "✓ 代理已启用"

# 2. 后台启动 uvicorn
# uvicorn app:app --host 0.0.0.0 --port 8007 &
# 2. 后台启动 uvicorn (使用 nohup 保证后台运行，日志输出到 logs.txt)
nohup uvicorn app:app --host 0.0.0.0 --port 8007 > logs.txt 2>&1 &
UVICORN_PID=$!

echo "✓ 后端服务启动中 (PID: $UVICORN_PID)..."

# 3. 等待服务启动（检查健康检查端点）
for i in {1..30}; do
    sleep 1
    if curl -s http://127.0.0.1:8007/health > /dev/null 2>&1; then
        echo "✓ 后端服务已就绪"
        break
    fi
    echo "等待服务启动... ($i/30)"
done

# 4. 取消代理环境变量
unset http_proxy
unset https_proxy
unset HTTP_PROXY
unset HTTPS_PROXY

echo "✓ 代理已取消"
echo ""
echo "========================================="
echo "后端服务运行在: http://0.0.0.0:8007"
echo "进程 PID: $UVICORN_PID"
echo ""
echo "查看日志: tail -f logs.txt"
echo "停止服务: kill $UVICORN_PID"
echo "========================================="

# 保存 PID 到文件，方便后续停止
echo $UVICORN_PID > /home/ght/aim-develop/AIM-develop/.backend.pid

# 将uvicorn的输出重定向到前台，这样可以看到日志
# wait $UVICORN_PID
echo "服务已在后台运行，您可以安全关闭此终端。"
# wait $UVICORN_PID  <-- 删除或注释掉这行，不再等待进程结束

