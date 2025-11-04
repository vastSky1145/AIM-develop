@echo off
echo 启动AI论文辅助系统API服务器...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements_fastapi.txt
)

REM 启动服务器
echo.
echo 启动服务器...
echo API文档地址: http://localhost:8000/docs
echo.
python app.py

pause

