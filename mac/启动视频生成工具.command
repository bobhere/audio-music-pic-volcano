#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 导航到项目目录
cd "$PROJECT_DIR/windows/src"

# 打印启动信息
echo "正在启动视频生成工具..."
echo "当前工作目录: $(pwd)"

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请确保已安装Python3"
    echo "可以从 https://www.python.org/downloads/ 下载并安装"
    echo "按任意键退出..."
    read -n 1
    exit 1
fi

# 检查所需的Python包
echo "检查所需的Python包..."
REQUIRED_PACKAGES=("PyQt5" "ffmpeg-python" "Pillow")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    python3 -c "import $package" 2>/dev/null || MISSING_PACKAGES+=("$package")
done

# 如果有缺失的包，尝试安装
if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "发现缺失的Python包: ${MISSING_PACKAGES[*]}"
    echo "正在尝试安装..."
    
    for package in "${MISSING_PACKAGES[@]}"; do
        echo "安装 $package..."
        python3 -m pip install $package
        
        # 检查安装是否成功
        if [ $? -ne 0 ]; then
            echo "错误: 安装 $package 失败"
            echo "请手动运行: python3 -m pip install $package"
            echo "按任意键退出..."
            read -n 1
            exit 1
        fi
    done
    
    echo "所有缺失的包已成功安装"
fi

# 创建必要的目录
mkdir -p temp
mkdir -p projects

echo "启动视频生成工具..."
# 运行程序
python3 main.py

# 如果程序异常退出，保持终端窗口打开
if [ $? -ne 0 ]; then
    echo "程序异常退出，退出代码: $?"
    echo "按任意键关闭窗口..."
    read -n 1
fi 