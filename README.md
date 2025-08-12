# Pybuild is a project designed for creating C++ project structures.      

## How to install
1. `pip install Pyinstaller`
2. packge the code
    - Linux/macOS : 
    `pyinstaller --onefile -n pybuild main.py`

    - Windows :
    `pyinstaller --onefile -n pybuild main.py`

## `pybuild` Usage
pybuild [options] <project-name>

## Options

### `new <project-name>`
Create a new project

- `-e, --executable`: Create executable project (default)
- `-s, --static`: Create static library project
- `-d, --shared`: Create shared library project
- `-D, --dep <dependency>`: Add project dependency
- `-h, --help`: Display this help message
- `-p, --precompile-headers`: Create precompiled headers

### `build`
Build the project

- `-d, --debug`: Build using Debug mode
- `-r, --release`: Build using Release mode
- `-p, --prefix`: Specify installation directory
- `-c, --configure-only`: Configure without building
- `-b, --build-dir`: Set build directory
- `-C, --clean-cache`: Clean cmake cache before building         

### `init`
Create new project based on `CMake.json`

### `install <path>`
Install built files (uses default path if omitted)

### `uninstall`
Uninstall installed library

### `get <url>`
- `-d, --debug`: Build using Debug mode (dafault)
- `-r, --release`: Build using Release mode
- `-p, --prefix`: Specify installation directory

# Pybuild 是一个专为创建 C++ 项目结构而设计的项目。

## 如何安装
1. `pip install Pyinstaller`
2. 打包代码 
    - Linux/macOS : 
    `pyinstaller --onefile -n pybuild main.py`

    - Windows :
    `pyinstaller --onefile -n pybuild main.py`

## `pybuild` 用法

```
pybuild [选项] <项目名>
```

## 选项

### `new <项目名>`
创建新项目

- `-e, --executable`：创建可执行项目（默认）
- `-s, --static`：创建静态库项目
- `-d, --shared`：创建动态库项目
- `-D, --dep <依赖>`：添加项目依赖
- `-h, --help`：显示此帮助信息
- `-p, --precompile-headers`：创建预编译头文件


### `build`
构建项目

- `-d, --debug`：使用 Debug 模式构建
- `-r, --release`：使用 Release 模式构建
- `-p, --prefix`：指定安装目录
- `-c, --configure-only`：选择是否构建
- `-b, --build-dir`：设置构建目录
- `-C, --clean-cache`：构建前清理cmake缓存


### `init`
根据 `CMake.json` 创建新项目


### `install`
安装生成的文件


### `uninstall`
卸载安装的库


### `get <下载连接>`
- `-d, --debug`: 使用Debug模式构建(默认)
- `-r, --release`: 使用Release模式构建
- `-p, --prefix`: 指定安装目录
