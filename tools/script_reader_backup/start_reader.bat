@echo off
chcp 65001 >nul
echo 正在启动《笑谈历史》智能审稿工作台...
cd /d "%~dp0\..\.."
start python tools\script_reader\server.py
timeout /t 1 >nul
start http://localhost:8520
echo 启动成功！已在浏览器打开: http://localhost:8520
