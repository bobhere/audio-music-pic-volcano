@echo off
echo 正在安装必要的组件...

:: 检查 Python 是否已安装
python --version 2>NUL
if errorlevel 1 (
    echo Python未安装！请先安装Python 3.10或更高版本。
    echo 您可以从 https://www.python.org/downloads/ 下载Python。
    pause
    exit
)

:: 安装必要的包
echo 正在安装必要的Python包...
pip install PyQt5
pip install ffmpeg-python
pip install Pillow
pip install pyinstaller

:: 创建源代码目录
mkdir src 2>NUL

:: 复制源代码
echo 正在复制源代码...
copy ..\src\*.py src\

:: 打包程序
echo 正在打包程序...
pyinstaller --windowed --onefile --name "视频生成工具" src\main.py

echo 安装完成！
echo 您可以在 dist 目录下找到 视频生成工具.exe
pause 