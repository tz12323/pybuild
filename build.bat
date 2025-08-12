@echo off
setlocal enabledelayedexpansion

echo 正在检测Python环境...
REM 修复版本解析：兼容Python 3.12+的输出格式
for /f "tokens=1,2 delims=. " %%a in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>^&1') do (
    set major=%%a
    set minor=%%b
)

REM 验证Python版本
if "!major!"=="" (
    echo 错误：无法获取Python版本信息
    exit /b 1
)
if !major! lss 3 (
    echo 错误：不支持的Python版本：!major!.!minor!，需安装3.6及以上版本
    exit /b 1
)
if !major! equ 3 if !minor! lss 6 (
    echo 错误：不支持的Python版本：3.!minor!，需安装3.6及以上版本
    exit /b 1
)
echo ? 当前Python版本：!major!.!minor!(符合要求)

REM 检查并安装PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstaller未安装，正在通过pip安装...
    pip install "pyinstaller>=4.0"
    if %errorlevel% neq 0 (
        echo 错误：PyInstaller安装失败
        exit /b 1
    )
)

REM 查找Python动态库（核心修复点）
set PYTHON_LIB=
REM 关键修复：使用 python3!minor!.dll 替代 python!minor!.dll
for /f "delims=" %%i in ('where python3!minor!.dll 2^>nul') do (
    set PYTHON_LIB=%%i
    goto :found_lib
)

:found_lib
if "!PYTHON_LIB!"=="" (
    echo 错误：未找到python3!minor!.dll，请确认：
    echo  1. Python安装时勾选了"Add Python to PATH"
    echo  2. 已安装对应版本的Python开发库
    exit /b 1
)
echo ? 找到Python动态库：!PYTHON_LIB!

REM 处理资源目录
set RESOURCES_ARG=
if exist "resources\" (
    echo 检测到资源目录，添加到打包参数...
    set RESOURCES_ARG=--add-data "resources;resources"
)

REM 构建打包命令（关键优化）
echo 正在配置打包参数...
set COMMAND=pyinstaller --onefile ^
    --add-binary "!PYTHON_LIB!;." ^
    !RESOURCES_ARG! ^
    --windowed ^
    --clean ^
    -n pybuild ^
    main.py

REM 执行打包
echo 开始打包（命令：%COMMAND%）...
%COMMAND%
if %errorlevel% neq 0 (
    echo 错误：打包过程出错，请检查：
    echo  1. 主文件main.py是否存在
    echo  2. 资源路径是否正确
    exit /b 1
)

REM 验证结果
if exist "dist\pybuild.exe" (
    echo ? 打包成功！可执行文件路径：dist\pybuild.exe
) else (
    echo ? 打包失败，未找到可执行文件
    exit /b 1
)

endlocal