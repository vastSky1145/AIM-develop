#!/bin/bash
cd /home/ght/aim-develop/AIM-develop/AIM-web

echo "🚀 启动前端生产服务"

npm run build
#nohup serve -s dist -l 5173 > /home/ght/aim-develop/AIM-develop/logs/front.log 2>&1 &
# 添加 --host 0.0.0.0 让前端监听所有网络接口
nohup serve -s dist -l 5173 --host 0.0.0.0 > /home/ght/aim-develop/AIM-develop/logs/front.log 2>&1 &


FRONT_PID=$!
echo $FRONT_PID > /home/ght/aim-develop/AIM-develop/.frontend.pid

echo "✓ 前端生产服务已启动 (PID: $FRONT_PID)"
echo "访问地址: http://192.168.1.96:5173"
