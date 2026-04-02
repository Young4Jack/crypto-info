@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================================
echo         Crypto-info 数字货币价格监控系统
echo         一键安装脚本 v1.0.0
echo ============================================================
echo.

:: 检查Python
echo [INFO] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未检测到 Python
    echo [INFO] 请手动安装 Python 3.11+ : https://www.python.org/downloads/
    echo [INFO] 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

:: 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% 已安装

:: 设置工作目录
cd /d "%~dp0"

echo [INFO] 工作目录: %cd%
echo.

:: 配置向导
echo ============================================================
echo         安装配置
echo ============================================================
echo.

:: 读取当前配置
for /f "tokens=*" %%i in ('python -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))"') do set CURRENT_BACKEND=%%i
for /f "tokens=*" %%i in ('python -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))"') do set CURRENT_FRONTEND=%%i

echo 当前端口配置：
echo    后端 API 端口: %CURRENT_BACKEND%
echo    前端 Web 端口: %CURRENT_FRONTEND%
echo.

set /p MODIFY="是否修改端口配置? (y/n): "
if /i "%MODIFY%"=="y" (
    set /p NEW_BACKEND="后端 API 端口 [%CURRENT_BACKEND%]: "
    set /p NEW_FRONTEND="前端 Web 端口 [%CURRENT_FRONTEND%]: "
    
    if "%NEW_BACKEND%"=="" set NEW_BACKEND=%CURRENT_BACKEND%
    if "%NEW_FRONTEND%"=="" set NEW_FRONTEND=%CURRENT_FRONTEND%
    
    :: 更新配置文件
    python -c "import json; c=json.load(open('backend/config.json')); c['system_settings']['backend_port']=%NEW_BACKEND%; c['system_settings']['frontend_port']=%NEW_FRONTEND%; json.dump(c, open('backend/config.json','w'), indent=2)"
    
    echo.
    echo [SUCCESS] 端口配置已更新：
    echo    后端 API 端口: %NEW_BACKEND%
    echo    前端 Web 端口: %NEW_FRONTEND%
) else (
    echo [INFO] 使用默认端口配置
)
echo.

:: 安装后端依赖
echo [INFO] 正在安装后端依赖...
cd backend

:: 创建虚拟环境
if not exist "venv" (
    echo [INFO] 创建 Python 虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
echo [INFO] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 安装依赖
echo [INFO] 安装 Python 依赖...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q

:: 初始化数据库
echo [INFO] 初始化数据库...
if exist "alembic.ini" (
    alembic upgrade head 2>nul
)
python -m app.init_db

echo [SUCCESS] 后端安装完成

:: 返回项目根目录
cd ..

:: 安装到 Program Files
echo [INFO] 正在安装到 C:\Program Files\Crypto-info...
if not exist "C:\Program Files\Crypto-info" mkdir "C:\Program Files\Crypto-info"
xcopy /E /Y /Q * "C:\Program Files\Crypto-info\"

:: 创建启动脚本
echo [INFO] 创建启动脚本...

:: 创建 start.bat
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "C:\Program Files\Crypto-info"
    echo.
    echo echo 启动后端服务...
    echo start "Crypto-info Backend" /min cmd /c "cd backend ^&^& call venv\Scripts\activate.bat ^&^& python run.py"
    echo.
    echo timeout /t 3 /nobreak ^>nul
    echo.
    echo echo 启动代理服务...
    echo start "Crypto-info Proxy" /min cmd /c "cd scripts ^&^& python proxy.py"
    echo.
    echo timeout /t 3 /nobreak ^>nul
    echo.
    echo echo.
    echo echo ============================================================
    echo echo              Crypto-info 启动成功！
    echo echo ============================================================
    echo echo.
    echo echo 本地访问: http://localhost:5173
    echo echo API文档: http://localhost:8000/docs
    echo echo.
    echo echo 默认账户:
    echo echo   邮箱: admin@crypto.local
    echo echo   用户名: admin
    echo echo   密码: admin123
    echo echo ============================================================
    echo echo.
    echo pause
) > "C:\Program Files\Crypto-info\start.bat"

:: 创建 stop.bat
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo.
    echo 正在停止 Crypto-info 服务...
    echo.
    echo taskkill /f /im python.exe 2^>nul
    echo.
    echo 所有服务已停止
    echo pause
) > "C:\Program Files\Crypto-info\stop.bat"

:: 创建桌面快捷方式
echo [INFO] 创建桌面快捷方式...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([System.IO.Path]::Combine([System.Environment]::GetFolderPath('Desktop'), 'Crypto-info.lnk')); $s.TargetPath = 'C:\Program Files\Crypto-info\start.bat'; $s.IconLocation = 'shell32.dll,44'; $s.Save()"

:: 读取端口配置
for /f "tokens=*" %%i in ('python -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('backend_port', 8000))"') do set BACKEND_PORT=%%i
for /f "tokens=*" %%i in ('python -c "import json; print(json.load(open('backend/config.json'))['system_settings'].get('frontend_port', 5173))"') do set FRONTEND_PORT=%%i

:: 安装完成
echo.
echo ============================================================
echo              安装完成！
echo ============================================================
echo.
echo 启动方式:
echo   1. 双击桌面上的 "Crypto-info" 快捷方式
echo   2. 或运行: C:\Program Files\Crypto-info\start.bat
echo.
echo 停止方式:
echo   运行: C:\Program Files\Crypto-info\stop.bat
echo.
echo 访问地址:
echo   本地访问: http://localhost:%FRONTEND_PORT%
echo   API文档: http://localhost:%BACKEND_PORT%/docs
echo.
echo 默认账户:
echo   邮箱: admin@crypto.local
echo   用户名: admin
echo   密码: admin123
echo ============================================================
echo.

:: 询问是否立即启动
set /p START_NOW="是否立即启动服务? (y/n): "
if /i "%START_NOW%"=="y" (
    call "C:\Program Files\Crypto-info\start.bat"
) else (
    pause
)
