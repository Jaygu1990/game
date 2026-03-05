@echo off
REM 在TCG环境中安装服务器依赖

echo ======================================================================
echo 在TCG环境中安装服务器依赖
echo ======================================================================
echo.

REM 检查是否在TCG环境
python -c "import sys; env = 'tcg' if 'tcg' in sys.executable.lower() else 'base'; print(f'当前环境: {env}')" 2>nul

echo.
echo 安装依赖包...
python -m pip install -r server\requirements_server.txt

echo.
echo ======================================================================
echo 安装完成！
echo ======================================================================
echo.
echo 现在可以启动服务器：
echo   python server\server.py
echo.

pause
