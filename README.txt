视频生成工具使用说明【语音音乐图片生成4.6测试成功】
================

Mac版本
-------
1. 进入 mac 文件夹
2. 双击"视频生成工具"图标即可运行

Windows版本
----------
1. 确保已安装Python 3.10或更高版本（可从 https://www.python.org/downloads/ 下载）
2. 进入 windows 文件夹
3. 双击运行 setup.bat
4. 等待安装完成
5. 安装完成后，在 dist 目录下找到"视频生成工具.exe"
6. 双击运行即可使用

使用方法
-------
1. 点击"新建项目"创建一个项目
2. 添加一个或多个音频文件（支持mp3、wav、aac格式）
3. 添加一张或多张图片（支持jpg、jpeg、png格式）
4. 可选：添加背景音乐文件，并调整音量
   - 如果背景音乐长度不足，会自动循环播放直到与主音频长度一致
   - 可以通过滑块调整背景音乐的音量（0%-100%）
5. 点击"生成视频"按钮
6. 选择输出目录
7. 程序会根据图片和音频的数量自动选择处理模式：
   - 一个音频 + 多张图片：为每张图片生成对应的视频，视频文件名与图片文件名相同
   - 一张图片 + 多个音频：为每个音频生成对应的视频，视频文件名与音频文件名相同
   - 一个音频 + 一张图片：生成一个视频，文件名与图片文件名相同
8. 所有生成的视频会保存在一个新建的文件夹中（文件夹名包含时间戳）

注意事项
-------
1. 生成的视频分辨率为1080p（1920x1080）
2. 视频帧率为30fps
3. 视频时长与音频文件时长相同
4. 建议使用清晰度较高的图片
5. 生成过程中请勿关闭程序 
