@echo off
setlocal enabledelayedexpansion

echo ���ڼ��Python����...
REM �޸��汾����������Python 3.12+�������ʽ
for /f "tokens=1,2 delims=. " %%a in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>^&1') do (
    set major=%%a
    set minor=%%b
)

REM ��֤Python�汾
if "!major!"=="" (
    echo �����޷���ȡPython�汾��Ϣ
    exit /b 1
)
if !major! lss 3 (
    echo ���󣺲�֧�ֵ�Python�汾��!major!.!minor!���谲װ3.6�����ϰ汾
    exit /b 1
)
if !major! equ 3 if !minor! lss 6 (
    echo ���󣺲�֧�ֵ�Python�汾��3.!minor!���谲װ3.6�����ϰ汾
    exit /b 1
)
echo ? ��ǰPython�汾��!major!.!minor!(����Ҫ��)

REM ��鲢��װPyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo PyInstallerδ��װ������ͨ��pip��װ...
    pip install "pyinstaller>=4.0"
    if %errorlevel% neq 0 (
        echo ����PyInstaller��װʧ��
        exit /b 1
    )
)

REM ����Python��̬�⣨�����޸��㣩
set PYTHON_LIB=
REM �ؼ��޸���ʹ�� python3!minor!.dll ��� python!minor!.dll
for /f "delims=" %%i in ('where python3!minor!.dll 2^>nul') do (
    set PYTHON_LIB=%%i
    goto :found_lib
)

:found_lib
if "!PYTHON_LIB!"=="" (
    echo ����δ�ҵ�python3!minor!.dll����ȷ�ϣ�
    echo  1. Python��װʱ��ѡ��"Add Python to PATH"
    echo  2. �Ѱ�װ��Ӧ�汾��Python������
    exit /b 1
)
echo ? �ҵ�Python��̬�⣺!PYTHON_LIB!

REM ������ԴĿ¼
set RESOURCES_ARG=
if exist "resources\" (
    echo ��⵽��ԴĿ¼����ӵ��������...
    set RESOURCES_ARG=--add-data "resources;resources"
)

REM �����������ؼ��Ż���
echo �������ô������...
set COMMAND=pyinstaller --onefile ^
    --add-binary "!PYTHON_LIB!;." ^
    !RESOURCES_ARG! ^
    --windowed ^
    --clean ^
    -n pybuild ^
    main.py

REM ִ�д��
echo ��ʼ��������%COMMAND%��...
%COMMAND%
if %errorlevel% neq 0 (
    echo ���󣺴�����̳������飺
    echo  1. ���ļ�main.py�Ƿ����
    echo  2. ��Դ·���Ƿ���ȷ
    exit /b 1
)

REM ��֤���
if exist "dist\pybuild.exe" (
    echo ? ����ɹ�����ִ���ļ�·����dist\pybuild.exe
) else (
    echo ? ���ʧ�ܣ�δ�ҵ���ִ���ļ�
    exit /b 1
)

endlocal