#!/bin/bash

echo "启动AI论文辅助系统API服务器..."
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python"
    exit 1
fi

# 检查依赖是否安装
echo "检查依赖..."
python3 -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖..."
    pip3 install -r requirements_fastapi.txt
fi

# 启动服务器
echo ""
echo "启动服务器..."
echo "API文档地址: http://localhost:8000/docs"
echo ""
python3 app.py

