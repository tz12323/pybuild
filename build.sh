#!/bin/bash

OS=$(uname -s)
ARCH=$(uname -m)
echo "检测到操作系统：$OS $ARCH"

function die() { echo "$@" >&2; exit 1; }
function is_installed() { command -v "$1" >/dev/null 2>&1; }

echo "检测Python版本..."
if ! is_installed python3; then
    die "未找到Python3,请先安装Python 3.6及以上版本"
fi

PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
PY_VERSION="$PY_MAJOR.$PY_MINOR"

if [[ $PY_MAJOR -lt 3 || ($PY_MAJOR -eq 3 && $PY_MINOR -lt 6) ]]; then
    die "不支持的Python版本:$PY_VERSION,需安装3.6及以上版本"
fi
echo "当前Python版本:$PY_VERSION(符合要求)"


echo "检查并安装PyInstaller..."
if ! is_installed pyinstaller; then
    echo "PyInstaller未安装,正在通过pip安装..."
    if ! is_installed pip3; then
        case $OS in
            Linux)
                sudo apt-get update && sudo apt-get install -y python3-pip 
                ;;
            Darwin)
                brew install python3-pip 
                ;;
            WindowsNT)
                die "未找到pip3,请确保Python安装时勾选了'Add Python to PATH'"
                ;;
        esac
    fi
    pip3 install "pyinstaller>=4.0" 
fi


find_python_lib() {
    local pattern
    local search_paths  # 存储搜索路径，方便调试
    case $OS in
        Linux)
            # 关键修正：添加64位系统常见的库目录（如x86_64-linux-gnu）
            search_paths=(
                /usr/lib 
                /usr/lib64 
                /lib 
                /usr/local/lib 
                /usr/lib/x86_64-linux-gnu  # 你的动态库实际存放目录
                /lib/x86_64-linux-gnu
            )
            pattern="libpython3.${PY_MINOR}.so*"
            # 修正find命令语法（补全反斜杠，确保参数正确）
            PYTHON_LIB=$(find "${search_paths[@]}" \
                -name "$pattern" \
                -not -name "*d.so" \
                2>/dev/null | head -n1)
            ;;
        Darwin)
            pattern="libpython3.${PY_MINOR}.dylib"
            PYTHON_LIB=$(find \
                /Library/Frameworks/Python.framework/Versions/*/lib \
                /usr/local/Cellar/python*/3.${PY_MINOR}*/lib \
                -name "$pattern" \
                2>/dev/null | head -n1)
            ;;
        WindowsNT)
            pattern="python3${PY_MINOR}.dll"
            PYTHON_LIB=$(where "$pattern" 2>/dev/null | head -n1)
            ;;
    esac

    # 优化错误提示：显示搜索过的路径，方便排查
    if [[ -z "$PYTHON_LIB" || ! -f "$PYTHON_LIB" ]]; then
        if [[ $OS == "Linux" ]]; then
            die "未找到Python $PY_VERSION 动态库(模式：$pattern)。搜索路径：${search_paths[*]}\n请确认安装了python3.${PY_MINOR}-dev（如sudo apt install python3.8-dev）"
        else
            die "未找到Python $PY_VERSION 动态库(模式：$pattern),请确认Python安装完整"
        fi
    fi
    echo "找到Python动态库:$PYTHON_LIB"
}

find_python_lib


RESOURCES_ARG=""
if [[ -d "resources" ]]; then
    echo "检测到资源目录，添加到打包参数..."
    case $OS in
        Linux|Darwin) SEP=":" ;; 
        WindowsNT) SEP=";" ;;    
    esac
    RESOURCES_ARG="--add-data \"resources${SEP}resources\""
fi


case $OS in
    Linux)
        COMMAND="pyinstaller --onefile \
            --add-binary \"$PYTHON_LIB:$SEP.\" \
            $RESOURCES_ARG \
            -n pybuild main.py"
        ;;
    Darwin)
        COMMAND="pyinstaller --onefile \
            --add-binary \"$PYTHON_LIB:$SEP.\" \
            $RESOURCES_ARG \
            --noconsole \
            -n pybuild main.py"
        ;;
    WindowsNT)
        COMMAND="pyinstaller --onefile \
            --add-binary \"$PYTHON_LIB:$SEP.\" \
            $RESOURCES_ARG \
            --windowed \
            -n pybuild main.py"
        ;;
esac


# 执行打包
echo "开始打包，命令：$COMMAND"
eval "$COMMAND" || die "打包过程出错，请检查日志"


echo "验证打包结果..."
case $OS in
    Linux|Darwin)
        EXE_PATH="dist/pybuild"
        ;;
    WindowsNT)
        EXE_PATH="dist/pybuild.exe"
        ;;
esac

if [[ -f "$EXE_PATH" ]]; then
    echo "✅ 打包成功！可执行文件路径：$EXE_PATH"
else
    die "❌ 打包失败，未找到可执行文件(预期路径：$EXE_PATH)"
fi