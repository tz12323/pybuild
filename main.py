import os
import sys
import json
import shutil
import platform
import subprocess
import stat
import re

# 平台定义
PLATFORM_WINDOWS = platform.system() == "Windows"
PLATFORM_MACOS = platform.system() == "Darwin"
PLATFORM_LINUX = platform.system() == "Linux"
CMAKE_SOURCE_DIR = "{CMAKE_SOURCE_DIR}"
# 路径和文件扩展名定义
if PLATFORM_WINDOWS:
    PATH_SEP = '\\'
    EXE_EXT = ".exe"
    STATIC_LIB_EXT = ".lib"
    SHARED_LIB_EXT = ".dll"
elif PLATFORM_MACOS:
    PATH_SEP = '/'
    EXE_EXT = ""
    STATIC_LIB_EXT = ".a"
    SHARED_LIB_EXT = ".dylib"
else:  # Linux
    PATH_SEP = '/'
    EXE_EXT = ""
    STATIC_LIB_EXT = ".a"
    SHARED_LIB_EXT = ".so"

MAX_PATH_LEN = 1024
BUFFER_SIZE = 1024
MAX_DEPS = 20  # 最大依赖数

def print_platform_info():
    """显示平台信息"""
    print("运行平台: ", end="")
    if PLATFORM_WINDOWS:
        print("Windows\n")
    elif PLATFORM_MACOS:
        print("macOS\n")
    elif PLATFORM_LINUX:
        print("Linux\n")
    else:
        print("未知平台\n")

def print_usage(program_name):
    """输出使用帮助信息"""
    print_platform_info()
    print(f"用法: {program_name} [选项] <项目名>")
    print("选项:")
    print("  new <项目名>               创建新项目")
    print("    -e, --executable         创建可执行项目（默认）")
    print("    -s, --static             创建静态库项目")
    print("    -d, --shared             创建动态库项目")
    print("    -D, --dep <依赖>         添加项目依赖")
    print("    -h, --help               显示此帮助信息")
    print("    -p, --precompile-headers 创建预编译头文件")
    print("  build                      构建项目")
    print("    -d, --debug              使用Debug模式构建")
    print("    -r, --release            使用Release模式构建")
    print("    -p, --prefix             指定安装目录")
    print("    -c, --configure-only     选择是否构建")
    print("    -b, --build-dir          设置构建目录")
    print("    -C, --clean-cache        构建前清理cmake缓存")
    print("  init                       根据CMake.json创建新项目")
    print("  install <path>             安装生成的文件,如果不设置path则选择默认路径")
    print("  uninstall                  卸载安装的库")
    print("  get <下载链接>             使用git安装第三方库")
    print("    -d, --debug              使用Debug模式构建 (默认)")
    print("    -r, --release            使用Release模式构建")
    print("    -p, --prefix             指定安装目录")
    print("示例:")
    print(f"  {program_name} new myapp -e -D fmt -D sdl2")
    print(f"  {program_name} new mylib -s -D boost")
    print("注意 : 使用get功能需要预先安装git\n\n")

    print(f"Usage: {program_name} [options] <project-name>")
    print("Options:")
    print("  new <project-name>             Create new project")
    print("    -e, --executable             Create executable project (default)")
    print("    -s, --static                 Create static library project")
    print("    -d, --shared                 Create shared library project")
    print("    -D, --dep <dependency>       Add project dependency")
    print("    -h, --help                   Display this help message")
    print("    -p, --precompile-headers     Create precompiled headers")
    print("  build                          Build project")
    print("    -d, --debug                  Build using Debug mode")
    print("    -r, --release                Build using Release mode")
    print("    -p, --prefix                 Specify installation directory")
    print("    -c, --configure-only         Configure without building")
    print("    -b, --build-dir              Set build directory")
    print("    -C, --clean-cache            Clean cmake cache before building")
    print("  init                           Create new project based on CMake.json")
    print("  install <path>                 Install built files (uses default path if omitted)")
    print("  uninstall                      Uninstall installed library")
    print("  get <urls>                     use git to install third party library")
    print("    -d, --debug                  Build using Debug mode (dafault)")
    print("    -r, --release                Build using Release mode")
    print("    -p, --prefix                 Specify installation directory")
    print("Examples:")
    print(f"  {program_name} new myapp -e -D fmt -D sdl2")
    print(f"  {program_name} new mylib -s -D boost")
    print("Note: To use the get function, you need to install git in advance.")
    if PLATFORM_WINDOWS:
        print("\n注意: Windows平台需要预先安装CMake和编译器")
        print("      推荐使用MinGW")
    elif PLATFORM_MACOS:
        print("\n注意: macOS平台需要安装Xcode命令行工具:")
        print("      xcode-select --install")
    else:
        print("\n注意: Linux平台需要安装build-essential和cmake:")
        print("      sudo apt-get install build-essential cmake")

def create_precompile_headers(add_precompile_headers) -> bool:
    """创建预编译头文件"""
    if not add_precompile_headers:
        return True
    
    # 保存当前工作目录
    cwd = os.getcwd()
    
    try:
        # 确保include目录存在
        os.makedirs("include", exist_ok=True)
        
        with open("include/pch.h", "w", encoding="utf-8") as f:
            print("创建预编译头文件pch.h")
            f.write("#ifndef PCH_H\n")
            f.write("#define PCH_H\n\n")
            f.write("#include <string>\n")
            f.write("#include <iostream>\n")
            f.write("#include <vector>\n")
            f.write("#include <map>\n")
            f.write("#include <array>\n")
            f.write("#include <algorithm>\n")
            f.write("#include <functional>\n")
            f.write("#include <future>\n")
            f.write("#include <mutex>\n")
            f.write("#include <thread>\n\n")
            f.write("#endif\n")
        
        return True
    except Exception as e:
        print(f"打开pch.h失败: {e}")
        return False
    finally:
        # 切换回原目录
        os.chdir(cwd)

def create_cmake_json(project_name, project_type, deps, num_deps, add_precompile_headers, include_dir) -> bool:
    """创建CMake.json配置文件"""
    try:
        config = {
            "project": {
                "name": project_name,
                "type": project_type,
                "version": "1.0.0",
                "precompile_headers": add_precompile_headers
            },
            "dependencies": {},
            "include_dir":[]
        }
        
        # 添加依赖项
        for i in range(num_deps):
            config["dependencies"][deps[i]] = "latest"
        for i in include_dir:
            config["include_dir"].append(i)
        
        with open("CMake.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"创建CMake.json失败: {e}")
        return False

def trim_string(s):
    """去除字符串首尾的空白字符和引号"""
    if not s:
        return s
    # 去除前面的空白和引号
    start = 0
    while start < len(s) and (s[start].isspace() or s[start] in ['"', "'"]):
        start += 1
    
    # 去除后面的空白和引号
    end = len(s) - 1
    while end >= start and (s[end].isspace() or s[end] in ['"', "'"]):
        end -= 1
    
    return s[start:end+1] if end >= start else ""

def parse_cmake_json(project_name:list, project_type:list, deps:list, num_deps:list, add_precompile_headers:list, include_dir:list):
    """解析CMake.json配置文件"""
    try:
        with open("CMake.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 解析项目信息
        if "project" in config:
            project_info = config["project"]
            if "name" in project_info:
                project_name[0] = project_info["name"]
            if "type" in project_info:
                project_type[0] = project_info["type"]
            if "precompile_headers" in project_info:
                add_precompile_headers[0] = project_info["precompile_headers"]
        
        # 解析依赖项
        num_deps[0] = 0
        if "dependencies" in config:
            for dep in config["dependencies"]:
                if num_deps[0] < MAX_DEPS:
                    deps.append(dep)
                    num_deps[0] += 1
                else:
                    print(f"警告: 已达到最大依赖项数量({MAX_DEPS})，忽略依赖项: {dep}")
        if "include_dir" in config:
            for inc in config["include_dir"]:
                include_dir.append(inc)
        
        return len(project_name[0]) > 0  # 返回是否成功解析了项目名称
    except Exception as e:
        print(f"解析CMake.json失败: {e}")
        return False

def create_cmakelists(project_name, project_type, deps, num_deps, add_precompile_headers, include_dir:list):
    """创建CMakeLists.txt文件"""
    try:
        with open("CMakeLists.txt", "w", encoding="utf-8") as f:
            f.write("cmake_minimum_required(VERSION 3.16)\n")
            f.write(f"project({project_name} LANGUAGES CXX)\n\n")
            f.write("set(CMAKE_CXX_STANDARD 11)\n")
            f.write("set(CMAKE_CXX_STANDARD_REQUIRED ON)\n")
            f.write("set(CMAKE_EXPORT_COMPILE_COMMANDS ON)\n\n")
            
            if PLATFORM_WINDOWS:
                if num_deps > 0:
                    f.write("# Windows平台依赖设置\n")
                    for i in range(num_deps):
                        f.write(f"find_package({deps[i]} REQUIRED)\n")
                    f.write("\n")
            else:
                # 添加PkgConfig支持
                if num_deps > 0:
                    f.write("# 启用pkg-config\n")
                    f.write("find_package(PkgConfig REQUIRED)\n")
                
                # 处理依赖项
                for i in range(num_deps):
                    f.write(f"pkg_check_modules({deps[i]} REQUIRED {deps[i]})\n")
                
                if num_deps > 0:
                    f.write("\n# 设置包含目录\n")
                    f.write("include_directories(${PKG_CONFIG_INCLUDE_DIRS})\n")
                    f.write("link_directories(${PKG_CONFIG_LIBRARY_DIRS})\n")
                    f.write("add_definitions(${PKG_CONFIG_CFLAGS_OTHER})\n\n")
                elif project_type != "library":
                    f.write(f"target_include_directories(${project_name} PRIVATE ${CMAKE_SOURCE_DIR}/include)\n\n")
            
            if project_type == "executable":
                f.write(
                    f"""set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)  # 可执行文件
                    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/static)  # 静态库
                    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/shared)  # 共享库\n""")
                f.write(f"add_executable({project_name}\n")
                f.write("    src/main.cpp\n")
                f.write(")\n")
                f.write(f"target_include_directories({project_name} PRIVATE ${CMAKE_SOURCE_DIR}/include)\n")

                # 安装规则（跨平台）
                f.write("\n# 安装规则\n")
                f.write(f"install(TARGETS {project_name}\n")
                f.write("    RUNTIME DESTINATION bin\n")
                f.write(")\n")
            elif project_type == "static":
                f.write(
                    f"""set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)  # 可执行文件
                    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/static)  # 静态库
                    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/shared)  # 共享库\n""")
                f.write(f"add_library({project_name} STATIC\n")
                f.write(f"    src/{project_name}.cpp\n")
                f.write(")\n")
                f.write(f"target_include_directories({project_name} PRIVATE ${CMAKE_SOURCE_DIR}/include)\n")

                # 安装规则（跨平台）
                f.write("\n# 安装规则\n")
                f.write(f"install(TARGETS {project_name}\n")
                f.write("    ARCHIVE DESTINATION lib\n")
                f.write(")\n")
                f.write(f"install(FILES include/{project_name}.h DESTINATION include)\n")
            elif project_type == "shared":
                f.write(
                    f"""set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)  # 可执行文件
                    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/static)  # 静态库
                    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/shared)  # 共享库\n""")
                f.write(f"add_library({project_name} SHARED\n")
                f.write(f"    src/{project_name}.cpp\n")
                f.write(")\n")
                f.write(f"target_include_directories({project_name} PRIVATE ${CMAKE_SOURCE_DIR}/include)\n")
                
                # 安装规则（跨平台）
                f.write("\n# 安装规则\n")
                f.write(f"install(TARGETS {project_name}\n")
                f.write("    LIBRARY DESTINATION lib\n")
                f.write(")\n")
                f.write(f"install(FILES include/{project_name}.h DESTINATION include)\n")
            else:
                print("未设置项目类型,自动选择为:executable")
                f.write(
                    f"""set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)  # 可执行文件
                    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/static)  # 静态库
                    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/lib/shared)  # 共享库\n""")
                f.write(f"add_executable({project_name}\n")
                f.write("    src/main.cpp\n")
                f.write(")\n")
                f.write(f"target_include_directories({project_name} PRIVATE ${CMAKE_SOURCE_DIR}/include)\n")

                # 安装规则（跨平台）
                f.write("\n# 安装规则\n")
                f.write(f"install(TARGETS {project_name}\n")
                f.write("    RUNTIME DESTINATION bin\n")
                f.write(")\n")
            
            if add_precompile_headers:
                f.write("set(PRECOMPILED_HEADER ${CMAKE_SOURCE_DIR}/include/pch.h)\n")
                f.write("if(MSVC)\n")
                f.write(f"\tset_target_properties({project_name} PROPERTIES\n")
                f.write("\t\tCOMPILE_FLAGS \"/Yu\\\"${PRECOMPILED_HEADER}\\\"\"\n")
                f.write("\t)\n")
                f.write("\tset_source_files_properties(${PRECOMPILED_HEADER} PROPERTIES\n")
                f.write("\t\tCOMPILE_FLAGS \"/Yc\"${PRECOMPILED_HEADER}\"\"\n")
                f.write("\t)\n")
                f.write("elseif(CMAKE_CXX_COMPILER_ID MATCHES \"GNU|Clang\")\n")
                f.write("\tset(PCH_OUTPUT \"${CMAKE_BINARY_DIR}/pch.h.gch\")\n")
                f.write("\tadd_custom_command(\n")
                f.write("\t\tOUTPUT ${PCH_OUTPUT}\n")
                f.write("\t\tCOMMAND ${CMAKE_CXX_COMPILER}\n")
                f.write("\t\t\t\t${CMAKE_CXX_FLAGS}\n")
                f.write("\t\t\t\t-x c++-header\n")
                f.write("\t\t\t\t-o ${PCH_OUTPUT}\n")
                f.write("\t\t\t\t-I ${CMAKE_SOURCE_DIR}/include\n")
                f.write("\t\t\t\t${PRECOMPILED_HEADER}\n")
                f.write("\t\tDEPENDS ${PRECOMPILED_HEADER}\n")
                f.write("\t)\n")
                f.write("\tadd_custom_target(pch_target DEPENDS ${PCH_OUTPUT})\n")
                f.write(f"\tadd_dependencies({project_name} pch_target)\n")
                f.write(f"\ttarget_compile_options({project_name} PRIVATE\n")
                f.write("\t\t-include ${PRECOMPILED_HEADER}\n")
                f.write("\t)\n")
                f.write("endif()\n")
            
            if len(include_dir)>0:
                f.write(f"target_include_directories({project_name} PUBLIC \n")
                for inc in include_dir:
                    f.write(f"    \"${CMAKE_SOURCE_DIR}/{inc}\"\n")
                f.write(")\n")
            if PLATFORM_WINDOWS:
                if num_deps > 0:
                    f.write(f"\n# Windows平台链接依赖库\n")
                    f.write(f"target_include_directories({project_name} PUBLIC \n")
                    for i in range(num_deps):
                        f.write(f"    ${{{deps[i]}_INCLUDE_DIRS}}\n")
                    f.write(")\n")
                    
                    f.write(f"target_link_libraries({project_name} PUBLIC \n")
                    for i in range(num_deps):
                        f.write(f"    ${{{deps[i]}_LIBRARIES}}\n")
                    f.write(")\n")
            else:
                # 链接依赖库
                if num_deps > 0:
                    f.write("\n# 链接依赖库\n")
                    f.write(f"target_link_libraries({project_name} PUBLIC \n")
                    for i in range(num_deps):
                        f.write(f"    ${{{deps[i]}_LIBRARIES}}\n")
                    f.write(")\n")
        
        return True
    except Exception as e:
        print(f"创建CMakeLists.txt失败: {e}")
        return False

def create_main_cpp_file(add_precompile_headers):
    """创建初始的main.cpp文件"""
    try:
        with open("src/main.cpp", "w", encoding="utf-8") as f:
            if add_precompile_headers:
                f.write("#include \"pch.h\"\n")
            f.write("#include <iostream>\n\n")
            f.write("int main() {\n")
            f.write("    std::cout << \"Hello, World!\" << std::endl;\n")
            f.write("    return 0;\n")
            f.write("}\n")
        return True
    except Exception as e:
        print(f"创建main.cpp失败: {e}")
        return False

def create_library_files(project_name, add_precompile_headers):
    """创建库源文件和头文件"""
    try:
        # 创建源文件
        with open(f"src/{project_name}.cpp", "w", encoding="utf-8") as f:
            if add_precompile_headers:
                f.write(f"#include \"pch.h\"\n")
            f.write(f"#include \"{project_name}.h\"\n\n")
            f.write(f"int {project_name}_function() {{\n")
            f.write("    return 0;\n")
            f.write("}\n")
        
        # 创建头文件
        # 防止头文件重复包含的保护宏
        guard = project_name.upper().replace("-", "_").replace(".", "_") + "_H"
        
        with open(f"include/{project_name}.h", "w", encoding="utf-8") as f:
            f.write(f"#ifndef {guard}\n")
            f.write(f"#define {guard}\n\n")
            f.write(f"int {project_name}_function();\n\n")
            f.write(f"#endif // {guard}\n")
        
        return True
    except Exception as e:
        print(f"创建库文件失败: {e}")
        return False

def create_new_project(args):
    """创建新项目"""
    project_name = "my_project"
    project_type = "executable"
    deps_from_cli = []
    project_name_set = False
    add_precompile_headers = False
    include_dir = []
    
    # 解析命令行参数
    i = 2  # args[0]是程序名，args[1]是"new"
    while i < len(args):
        arg = args[i]
        if arg == "-e" or arg == "--executable":
            project_type = "executable"
            i += 1
        elif arg == "-s" or arg == "--static":
            project_type = "static"
            i += 1
        elif arg == "-d" or arg == "--shared":
            project_type = "shared"
            i += 1
        elif arg == "-p" or arg == "--precompile-headers":
            add_precompile_headers = True
            i += 1
        elif arg == "-i" or arg == "--include-dir":
            if i+1 >= len(args):
                print("未设置include路径")
                break
            while i < len(args):
                if args[i+1][0] == '-':
                    print("未设置include路径")
                    break
                i+=1
                include_dir.append(args[i])
        elif arg == "-h" or arg == "--help":
            print_usage(args[0])
            return 0
        elif (arg == "-D" or arg == "--dep") and i + 1 < len(args):
            # 获取依赖项名称
            i += 1
            if len(deps_from_cli) < MAX_DEPS:
                deps_from_cli.append(args[i])
            else:
                print(f"警告: 已达到最大依赖项数量({MAX_DEPS})，忽略依赖项: {args[i]}")
            i += 1
        elif not project_name_set and not arg.startswith("-"):
            project_name = arg
            project_name_set = True
            i += 1
        else:
            i += 1
    
    if not project_name_set and len(args) > 2 and not args[2].startswith("-"):
        project_name = args[2]
        project_name_set = True
    
    if not project_name_set:
        print(f"未设置项目名称,使用默认名称{project_name}")
    
    print(f"项目名称为 : {project_name}")
    print(f"项目类型为 : {project_name} ({'可执行文件' if project_type == 'executable' else '静态库' if project_type == 'static' else '动态库'})")
    
    # 显示命令行添加的依赖项
    if deps_from_cli:
        print("命令行添加的依赖项: " + " ".join(deps_from_cli))
    
    # 创建项目目录
    try:
        os.makedirs(project_name, exist_ok=True)
        os.chdir(project_name)
        
        # 创建子目录
        os.makedirs("src", exist_ok=True)
        os.makedirs("include", exist_ok=True)
        os.makedirs("build", exist_ok=True)
        
        # 创建CMake.json文件（包含命令行依赖项）
        if not create_cmake_json(project_name, project_type, deps_from_cli, len(deps_from_cli), add_precompile_headers, include_dir):
            return 1
        
        # 解析CMake.json获取依赖项
        deps = []
        num_deps = [0]
        parsed_project_name = [project_name]
        parsed_project_type = [project_type]
        parsed_precompile = [add_precompile_headers]
        include_dir.clear()
        
        if parse_cmake_json(parsed_project_name, parsed_project_type, deps, num_deps, parsed_precompile, include_dir):
            project_name = parsed_project_name[0]
            project_type = parsed_project_type[0]
            add_precompile_headers = parsed_precompile[0]
            
            if num_deps[0] > 0:
                print("检测到依赖项: " + " ".join(deps[:num_deps[0]]))
        else:
            print("警告 : 未能完全解析CMake.json,使用默认配置")
        
        # 创建CMakeLists.txt文件
        if not create_cmakelists(project_name, project_type, deps, num_deps[0], add_precompile_headers, include_dir):
            return 1
        
        # 创建源文件
        if project_type == "executable":
            if not create_main_cpp_file(add_precompile_headers):
                return 1
        else:
            if not create_library_files(project_name, add_precompile_headers):
                return 1
        
        # 创建预编译头文件
        if add_precompile_headers:
            if not create_precompile_headers(add_precompile_headers):
                return 1
        
        # 输出成功信息
        print("\n项目创建成功! 结构如下:")
        print(f"{project_name}{PATH_SEP}")
        print("├── CMakeLists.txt")
        print("├── CMake.json")
        print(f"├── build{PATH_SEP}")
        print(f"├── include{PATH_SEP}")
        if project_type in ["static", "shared"]:
            print(f"│   └── {project_name}.h")
        print(f"└── src{PATH_SEP}")
        
        if project_type == "executable":
            print("    └── main.cpp")
        else:
            print(f"    └── {project_name}.cpp")
        
        print("\n构建指南:")
        print(f"  cd {project_name}")
        print("  cd build")
        
        if project_type == "executable":
            print("  cmake ..")
            print("  cmake --build .")
            print(f"  .{PATH_SEP}{project_name}{EXE_EXT}")
        elif project_type == "static":
            print("  cmake ..")
            print("  cmake --build .")
            print(f"  # 静态库文件: build{PATH_SEP}lib{PATH_SEP}static{PATH_SEP}{project_name}{STATIC_LIB_EXT}")
        else:  # shared
            print("  cmake ..")
            print("  cmake --build .")
            if PLATFORM_WINDOWS:
                print(f"  # 动态库文件: build{PATH_SEP}bin{PATH_SEP}{project_name}{SHARED_LIB_EXT}")
            else:
                print(f"  # 动态库文件: build{PATH_SEP}lib{PATH_SEP}shared{PATH_SEP}{project_name}{SHARED_LIB_EXT}")
        
        if num_deps[0] > 0:
            print("\n注意 : 本项目的依赖项需要通过系统包管理器安装")
            if PLATFORM_WINDOWS:
                print("      请使用 vcpkg 安装依赖项")
            elif PLATFORM_MACOS:
                print("      请使用 Homebrew 安装依赖项")
            else:
                print("      请使用 apt-get/yum 安装依赖项")
            print("使用本应用的get功能,从github等支持git的平台上面下载安装")
        
        return 0
    except Exception as e:
        print(f"创建项目失败: {e}")
        return 1
    finally:
        # 回到原始目录
        os.chdir("..")

def init_project(args):
    """根据CMake.json初始化项目"""
    project_name = ["my_project"]
    project_type = ["executable"]
    deps = []
    num_deps = [0]
    add_precompile_headers = [False]
    include_dir = []
    
    # 尝试从CMake.json获取项目名称
    if parse_cmake_json(project_name, project_type, deps, num_deps, add_precompile_headers, include_dir):
        print(f"从CMake.json获取项目名称: {project_name[0]}")
        print(f"从CMake.json获取项目类型: {project_type[0]}")
        if num_deps[0] > 0:
            print("检测到依赖项: " + " ".join(deps))
        if len(include_dir) > 0:
            print("检测到包含目录: " + " ".join(include_dir))
    else:
        print("无法打开CMake.json或解析失败")
        return 1
    
    print(f"\n在当前目录初始化项目: {project_name[0]} ({'可执行文件' if project_type[0] == 'executable' else '静态库' if project_type[0] == 'static' else '动态库'})")
    
    try:
        # 创建必要的子目录
        os.makedirs("src", exist_ok=True)
        os.makedirs("include", exist_ok=True)
        os.makedirs("build", exist_ok=True)
        
        # 创建CMakeLists.txt文件
        if not create_cmakelists(project_name[0], project_type[0], deps, num_deps[0], add_precompile_headers[0], include_dir):
            return 1
        
        # 创建源文件（如果不存在）
        if project_type[0] == "executable":
            if not os.path.exists("src/main.cpp"):
                if not create_main_cpp_file(add_precompile_headers[0]):
                    return 1
        else:
            src_file = f"src/{project_name[0]}.cpp"
            if not os.path.exists(src_file):
                if not create_library_files(project_name[0], add_precompile_headers[0]):
                    return 1
        
        # 创建预编译头文件
        if add_precompile_headers[0]:
            if not create_precompile_headers(add_precompile_headers[0]):
                return 1
        
        # 确保CMake.json存在
        if not os.path.exists("CMake.json"):
            create_cmake_json(project_name[0], project_type[0], deps, num_deps[0], add_precompile_headers[0], include_dir)
            print("  CMake.json (已创建)")
        else:
            print("  CMake.json (已更新)")
        
        # 输出成功信息
        print("\n项目初始化成功!")
        print("已创建/更新以下文件:")
        print("  CMakeLists.txt")
        
        if project_type[0] in ["static", "shared"]:
            print(f"  include/{project_name[0]}.h")
            print(f"  src/{project_name[0]}.cpp")
        else:
            print("  src/main.cpp")
        
        if num_deps[0] > 0:
            print("\n注意 : 本项目的依赖项需要通过系统包管理器安装")
            if PLATFORM_WINDOWS:
                print("      请使用 vcpkg 安装依赖项")
            elif PLATFORM_MACOS:
                print("      请使用 Homebrew 安装依赖项")
            else:
                print("      请使用 apt-get/yum 安装依赖项")
        
        return 0
    except Exception as e:
        print(f"初始化项目失败: {e}")
        return 1

def execute_command(command):
    """执行命令并检查状态"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e.stderr}")
        return False
    except Exception as e:
        print(f"命令执行错误: {e}")
        return False

def clean_project_cache():
    """清理项目缓存"""
    original_dir = os.getcwd()
    
    try:
        # 检查build目录是否存在
        if not os.path.exists("build"):
            print("build目录不存在,无需清理")
            os.makedirs("build", exist_ok=True)
            return 0
        
        # 进入build目录
        os.chdir("build")
        
        # 清理操作
        if PLATFORM_WINDOWS:
            # Windows: 返回上级目录后删除整个build
            os.chdir("..")
            if os.path.exists("build"):
                # 确保所有文件可写
                def make_writable(path):
                    for root, dirs, files in os.walk(path):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), stat.S_IWRITE)
                        for f in files:
                            os.chmod(os.path.join(root, f), stat.S_IWRITE)
                
                make_writable("build")
                shutil.rmtree("build", ignore_errors=True)
            
            os.makedirs("build", exist_ok=True)
        else:
            # POSIX: 使用更可靠的递归删除命令
            execute_command("find . -delete 2>/dev/null || { rm -rf ./* && rm -rf .[!.]*; }")
        
        print("CMake缓存清理成功")
        return 0
    except Exception as e:
        print(f"清理缓存失败: {e}")
        return 1
    finally:
        # 返回原始目录
        os.chdir(original_dir)

def build_project(args):
    """构建项目"""
    cmake_build_type = "Debug"
    make_install_prefix = ""
    build_dir = "build"
    additional_flags = ""
    configure_only = False
    clean_cache = False
    
    # 设置默认安装路径
    if PLATFORM_WINDOWS:
        make_install_prefix = ".\\install"  # Windows默认安装路径
    else:
        make_install_prefix = "/usr/local"
    
    # 解析命令行参数
    i = 2  # args[0]是程序名，args[1]是"build"
    while i < len(args):
        arg = args[i]
        if arg == "-d" or arg == "--debug":
            cmake_build_type = "Debug"
            i += 1
        elif arg == "-r" or arg == "--release":
            cmake_build_type = "Release"
            i += 1
        elif arg == "-p" or arg == "--prefix":
            if i + 1 < len(args) and not args[i+1].startswith("-"):
                i += 1
                make_install_prefix = args[i]
            else:
                print("错误：未指定安装目录,使用默认安装目录")
                if PLATFORM_WINDOWS:
                    make_install_prefix = ".\\install"
                else:
                    make_install_prefix = "/usr/local"
            i += 1
        elif arg == "-c" or arg == "--configure-only":
            configure_only = True
            i += 1
        elif arg == "-b" or arg == "--build-dir":
            if i + 1 < len(args) and not args[i+1].startswith("-"):
                i += 1
                build_dir = args[i]
            else:
                print("错误：未指定构建目录")
                return 1
            i += 1
        elif arg == "-C" or arg == "--clean-cache":
            clean_cache = True
            i += 1
        else:
            # 收集额外的CMake参数
            if additional_flags:
                additional_flags += " "
            additional_flags += arg
            i += 1
    
    print(f"构建模式: {cmake_build_type} | 安装路径: {make_install_prefix}")
    
    if clean_cache:
        print("清理缓存")
        if clean_project_cache() != 0:
            print("清理缓存失败")
            return 1
    
    # 处理构建目录
    try:
        os.makedirs(build_dir, exist_ok=True)
    except Exception as e:
        print(f"创建构建目录失败: {build_dir} - {e}")
        return 1
    
    # 保存当前目录
    cwd = os.getcwd()
    
    try:
        # 进入构建目录
        os.chdir(build_dir)
        
        need_configure = True
        
        # 检查是否存在CMake缓存文件
        if os.path.exists("CMakeCache.txt"):
            # 尝试获取缓存的构建类型
            try:
                with open("CMakeCache.txt", "r", encoding="utf-8") as f:
                    existing_type = ""
                    for line in f:
                        if line.startswith("CMAKE_BUILD_TYPE:STRING"):
                            parts = line.split("=")
                            if len(parts) > 1:
                                existing_type = parts[1].strip()
                                break
                
                if existing_type == cmake_build_type:
                    need_configure = False
                    print("检测到现有的CMake缓存(构建类型相同),跳过配置阶段")
                else:
                    print(f"构建类型从 {existing_type} 变为 {cmake_build_type},需要重新配置")
                    need_configure = True
            except Exception as e:
                print(f"读取CMake缓存失败: {e}")
                need_configure = True
        else:
            print("未找到CMake缓存,需要进行配置")
        
        # 配置阶段
        if need_configure:
            # 构建配置命令
            if PLATFORM_WINDOWS:
                # Windows路径处理
                escaped_prefix = make_install_prefix.replace("\\", "\\\\")
                cmake_command = f'cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE={cmake_build_type} -DCMAKE_INSTALL_PREFIX="{escaped_prefix}" -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ {additional_flags}'
            else:
                cmake_command = f'cmake .. -DCMAKE_BUILD_TYPE={cmake_build_type} -DCMAKE_INSTALL_PREFIX="{make_install_prefix}" -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ {additional_flags}'
            
            print(f"配置CMake: {cmake_command}")
            if not execute_command(cmake_command):
                print("CMake配置失败")
                return 1
        
        # 构建阶段
        if not configure_only:
            if PLATFORM_WINDOWS:
                build_tool = "cmake --build ."
            else:
                # 尝试获取核心数
                try:
                    import multiprocessing
                    core_count = multiprocessing.cpu_count()
                    build_tool = f"cmake --build . --parallel {core_count}"
                except:
                    build_tool = "cmake --build ."
            
            print(f"构建中: {build_tool}")
            if not execute_command(build_tool):
                print("构建失败")
                return 1
        
        print(f"\n构建{'配置' if configure_only else ''}成功!")
        return 0
    except Exception as e:
        print(f"构建项目失败: {e}")
        return 1
    finally:
        # 返回原始目录
        os.chdir(cwd)

def install_project(args):
    """安装项目"""
    install_path = ""
    set_path = False
    
    if len(args) > 2:
        install_path = args[2]
        set_path = True
    
    try:
        # 进入build目录
        os.chdir("build")
        
        # 构建安装命令
        if set_path:
            if PLATFORM_WINDOWS:
                command = f'cmake --install . --prefix "{install_path}"'
            else:
                command = f'sudo cmake --install . --prefix "{install_path}"'
        else:
            if PLATFORM_WINDOWS:
                command = "cmake --install ."
            else:
                command = "sudo cmake --install ."
        
        return 0 if execute_command(command) else 1
    except Exception as e:
        print(f"安装项目失败: {e}")
        return 1
    finally:
        # 返回原始目录
        os.chdir("..")

def uninstall():
    """卸载项目"""
    try:
        if not os.path.exists("build/install_manifest.txt"):
            print("未找到安装清单文件: build/install_manifest.txt")
            return 1
        
        with open("build/install_manifest.txt", "r", encoding="utf-8") as f:
            files = [line.strip() for line in f if line.strip()]
        
        success_count = 0
        fail_count = 0
        
        for file_path in files:
            try:
                if PLATFORM_WINDOWS:
                    # Windows路径处理
                    file_path = file_path.replace("/", "\\")
                    # 确保文件可写
                    if os.path.exists(file_path):
                        os.chmod(file_path, stat.S_IWRITE)
                        os.remove(file_path)
                        success_count += 1
                    else:
                        fail_count += 1
                else:
                    # Linux/macOS
                    result = subprocess.run(f"sudo rm -f {file_path}", shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        success_count += 1
                    else:
                        print(f"删除失败 {file_path}: {result.stderr}")
                        fail_count += 1
            except Exception as e:
                print(f"处理 {file_path} 失败: {e}")
                fail_count += 1
        
        print(f"卸载完成：已删除 {success_count} 个文件, {fail_count} 个文件失败")
        return 0 if fail_count == 0 else 1
    except Exception as e:
        print(f"卸载失败: {e}")
        return 1

def get_lib_name(url):
        # 从URL中提取库名（去掉.git后缀）
        match = re.search(r'/([^/]+?)(\.git)?$', url)
        if match:
            return match.group(1)
        return "unknown_lib"

def get_third_party_library(args):
    build_type = "-d"
    set_install_place = False
    install_place = ""
    url = []    
    lib_success = []
    lib_fail = []
    i = 2
    while i <len(args):
        if args[i] == "-r" or args[i] == "--release":
            build_type = "-r"
            i+=1
        elif args[i] == "-d" or args[i] == "--debug":
            build_type = "-d"
            i+=1
        elif args[i] == "-p" or args[i] == "--prefic":
            if i+1>=len(args):
                print("未指定下载位置!!! 参数无效")
                break
            set_install_place = True
            i+=1
            install_place = args[i]
            i+=1
        else:
            url.append(args[i])
            i+=1

    cmd = ['','',build_type]
    if set_install_place:
        cmd.append('-p')
        cmd.append(install_place)
    for third_party_library in url:
        try:
            lib_name = get_lib_name(third_party_library)
            result = subprocess.run(["git", "clone", third_party_library])
            if result.returncode == 0:
                os.chdir(lib_name)
                build_project(cmd)
                os.chdir('..')
                lib_success.append(lib_name)
            else:
                print(f"下载失败 {lib_name}: {result.stderr}")
                lib_fail.append(lib_name)
        except Exception as e:
            print(f"下载失败 {lib_name} 失败: {e}")
            lib_fail.append(lib_name)
    print(f"下载完成：已下载 {lib_success} 个文件, {lib_fail} 个文件失败")
    return 0 if len(lib_fail) == 0 else 1

def main():
    """主函数"""
    # 设置控制台编码为UTF-8
    if PLATFORM_WINDOWS:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
            kernel32.SetConsoleCP(65001)
        except:
            pass
    
    print_platform_info()
    
    if len(sys.argv) == 1:
        print("提示: 使用 -h 查看帮助")
        print_usage(sys.argv[0])
        return 0
    
    command = sys.argv[1]
    
    # 构建项目
    if command == "build":
        print("开始构建...")
        return build_project(sys.argv)
    
    # 根据解析的CMake.json初始化项目
    elif command == "init":
        return init_project(sys.argv)
    
    # 清除cmake构建
    elif command == "clean":
        return clean_project_cache()
    
    # 创建新的项目
    elif command == "new":
        return create_new_project(sys.argv)
    
    # 安装项目
    elif command == "install":
        return install_project(sys.argv)
    
    # 卸载安装的项目
    elif command == "uninstall":
        return uninstall()
    
    elif command == "get":
        return get_third_party_library(sys.argv)
    
    # 输出帮助消息
    elif command == "-h" or command == "--help":
        print_usage(sys.argv[0])
        return 0
    
    else:
        print(f"无效参数: {command}")
        print_usage(sys.argv[0])
        return 1

if __name__ == "__main__":
    import time
    start = time.time()
    res = main()
    end = time.time()
    print(f"耗时 : {end-start}s")
    sys.exit(res)