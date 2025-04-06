import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QPushButton, QFileDialog, QTextEdit, QHBoxLayout,
                           QInputDialog, QMessageBox, QListWidget, QListWidgetItem,
                           QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                           QProgressBar, QGroupBox, QComboBox, QSlider)
from PyQt5.QtCore import Qt, QMimeData, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from core.project_manager import ProjectManager
from core.video_core import VideoCore
from datetime import datetime

class VideoGeneratorThread(QThread):
    """视频生成线程"""
    progress = pyqtSignal(int, int, int)  # 当前图片索引，总图片数，当前进度
    finished = pyqtSignal(bool, str)
    log = pyqtSignal(str)  # 添加日志信号
    
    def __init__(self, audio_paths, image_paths, output_dir, bg_music_path=None, bg_music_volume=0.3):
        super().__init__()
        self.audio_paths = audio_paths if isinstance(audio_paths, list) else [audio_paths]
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.bg_music_path = bg_music_path
        self.bg_music_volume = bg_music_volume
        self.video_core = VideoCore()
        
        # 重定向 print 输出
        self.old_print = print
        def new_print(*args, **kwargs):
            message = ' '.join(map(str, args))
            self.log.emit(message)
            self.old_print(*args, **kwargs)
        import builtins
        builtins.print = new_print

    def run(self):
        try:
            success = self.video_core.generate_video_from_images(
                self.audio_paths,
                self.image_paths,
                self.output_dir,
                progress_callback=lambda current, total, progress: self.progress.emit(current, total, progress),
                bg_music_path=self.bg_music_path,
                bg_music_volume=self.bg_music_volume
            )
            self.finished.emit(success, self.output_dir)
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            # 恢复原始的 print 函数
            import builtins
            builtins.print = self.old_print

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.video_core = VideoCore()
        self.generator_thread = None
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 初始化界面
        self.init_ui(central_widget)
        
        # 设置窗口属性
        self.setWindowTitle('视频生成工具')
        self.setGeometry(100, 100, 1000, 800)  # 增加窗口大小
        
        # 初始化项目列表
        self.refresh_project_list()

    def init_ui(self, central_widget):
        """初始化界面"""
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 上半部分布局（原有内容）
        upper_layout = QVBoxLayout()
        
        # 项目管理区域
        project_group = QGroupBox("项目管理")
        project_layout = QHBoxLayout()
        
        self.project_list = QComboBox()
        self.project_list.currentIndexChanged.connect(self.on_project_changed)
        project_layout.addWidget(self.project_list)
        
        create_project_btn = QPushButton("新建项目")
        create_project_btn.clicked.connect(self.create_project)
        project_layout.addWidget(create_project_btn)
        
        delete_project_btn = QPushButton("删除项目")
        delete_project_btn.clicked.connect(self.delete_project)
        project_layout.addWidget(delete_project_btn)
        
        project_group.setLayout(project_layout)
        upper_layout.addWidget(project_group)
        
        # 素材管理区域
        material_group = QGroupBox("素材管理")
        material_layout = QVBoxLayout()
        
        # 音频文件
        audio_layout = QHBoxLayout()
        audio_label = QLabel("音频文件:")
        audio_layout.addWidget(audio_label)
        
        self.audio_list = QListWidget()
        audio_layout.addWidget(self.audio_list)
        
        audio_btn_layout = QVBoxLayout()
        add_audio_btn = QPushButton("添加音频")
        add_audio_btn.clicked.connect(lambda: self.add_file('audio'))
        audio_btn_layout.addWidget(add_audio_btn)
        
        delete_audio_btn = QPushButton("删除音频")
        delete_audio_btn.clicked.connect(lambda: self.delete_file('audio'))
        audio_btn_layout.addWidget(delete_audio_btn)
        
        audio_layout.addLayout(audio_btn_layout)
        material_layout.addLayout(audio_layout)
        
        # 图片文件
        image_layout = QHBoxLayout()
        image_label = QLabel("图片文件:")
        image_layout.addWidget(image_label)
        
        self.image_list = QListWidget()
        image_layout.addWidget(self.image_list)
        
        image_btn_layout = QVBoxLayout()
        add_image_btn = QPushButton("添加图片")
        add_image_btn.clicked.connect(lambda: self.add_file('images'))
        image_btn_layout.addWidget(add_image_btn)
        
        delete_image_btn = QPushButton("删除图片")
        delete_image_btn.clicked.connect(lambda: self.delete_file('images'))
        image_btn_layout.addWidget(delete_image_btn)
        
        image_layout.addLayout(image_btn_layout)
        material_layout.addLayout(image_layout)
        
        # 背景音乐文件
        bg_music_layout = QHBoxLayout()
        bg_music_label = QLabel("背景音乐:")
        bg_music_layout.addWidget(bg_music_label)
        
        self.bg_music_list = QListWidget()
        bg_music_layout.addWidget(self.bg_music_list)
        
        bg_music_btn_layout = QVBoxLayout()
        add_bg_music_btn = QPushButton("添加背景音乐")
        add_bg_music_btn.clicked.connect(lambda: self.add_file('background_music'))
        bg_music_btn_layout.addWidget(add_bg_music_btn)
        
        delete_bg_music_btn = QPushButton("删除背景音乐")
        delete_bg_music_btn.clicked.connect(lambda: self.delete_file('background_music'))
        bg_music_btn_layout.addWidget(delete_bg_music_btn)
        
        bg_music_layout.addLayout(bg_music_btn_layout)
        material_layout.addLayout(bg_music_layout)
        
        # 背景音乐音量控制
        volume_layout = QHBoxLayout()
        volume_label = QLabel("背景音乐音量:")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(30)  # 默认音量30%
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_value_label = QLabel("30%")
        volume_layout.addWidget(self.volume_value_label)
        
        material_layout.addLayout(volume_layout)
        
        material_group.setLayout(material_layout)
        upper_layout.addWidget(material_group)
        
        # 生成控制区域
        control_group = QGroupBox("生成控制")
        control_layout = QVBoxLayout()
        
        self.generate_btn = QPushButton("生成视频")
        self.generate_btn.clicked.connect(self.start_generation)
        control_layout.addWidget(self.generate_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        control_group.setLayout(control_layout)
        upper_layout.addWidget(control_group)
        
        main_layout.addLayout(upper_layout)
        
        # 添加日志显示区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)  # 设置最小高度
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

    def on_project_changed(self, index):
        """项目选择改变时的处理"""
        if index >= 0:
            project_id = self.project_list.currentData()
            self.project_manager.load_project(project_id)
            self.update_file_lists()
            self.update_volume_slider()

    def update_file_lists(self):
        """更新文件列表"""
        if not self.project_manager.current_project:
            self.audio_list.clear()
            self.image_list.clear()
            self.bg_music_list.clear()
            return

        project = self.project_manager.current_project
        files = project['files']

        # 更新音频列表
        self.audio_list.clear()
        for file_path in files.get('audio', []):
            self.audio_list.addItem(os.path.basename(file_path))

        # 更新图片列表
        self.image_list.clear()
        for file_path in files.get('images', []):
            self.image_list.addItem(os.path.basename(file_path))
            
        # 更新背景音乐列表
        self.bg_music_list.clear()
        for file_path in files.get('background_music', []):
            self.bg_music_list.addItem(os.path.basename(file_path))
            
    def update_volume_slider(self):
        """根据项目设置更新音量滑块"""
        if self.project_manager.current_project:
            volume = self.project_manager.get_setting('bg_music_volume', 0.3)
            # 将0-1的音量值转换为0-100的滑块值
            slider_value = int(volume * 100)
            self.volume_slider.setValue(slider_value)
            self.volume_value_label.setText(f"{slider_value}%")

    def on_volume_changed(self, value):
        """音量滑块值改变的处理"""
        self.volume_value_label.setText(f"{value}%")
        # 将0-100的滑块值转换为0-1的音量值
        volume = value / 100.0
        # 保存到项目设置
        self.project_manager.update_setting('bg_music_volume', volume)

    def handle_files(self, files, file_type):
        """处理文件"""
        if not self.project_manager.current_project:
            QMessageBox.warning(self, '警告', '请先选择或创建一个项目')
            return

        success_count = 0
        error_count = 0
        error_messages = []

        for file_path in files:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                error_msg = f'文件不存在: {os.path.basename(file_path)}'
                error_messages.append(error_msg)
                error_count += 1
                continue

            # 检查文件大小
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
            if file_size > 500:  # 限制文件大小为500MB
                error_msg = f'文件过大: {os.path.basename(file_path)} ({file_size:.2f}MB)\n最大支持500MB'
                error_messages.append(error_msg)
                error_count += 1
                continue

            # 添加文件到项目
            if file_path.lower().endswith(('.mp3', '.wav', '.aac')):
                if self.project_manager.add_file(file_type, file_path):
                    success_count += 1
                else:
                    error_msg = f'添加{file_type}文件失败: {os.path.basename(file_path)}'
                    error_messages.append(error_msg)
                    error_count += 1
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                if file_type == 'images':
                    if self.project_manager.add_file(file_type, file_path):
                        success_count += 1
                    else:
                        error_msg = f'添加{file_type}文件失败: {os.path.basename(file_path)}'
                        error_messages.append(error_msg)
                        error_count += 1
                else:
                    error_msg = f'不支持的文件类型: {os.path.basename(file_path)}'
                    error_messages.append(error_msg)
                    error_count += 1
            else:
                error_msg = f'不支持的文件类型: {os.path.basename(file_path)}'
                error_messages.append(error_msg)
                error_count += 1

        # 更新文件列表
        self.update_file_lists()

        # 显示结果
        if error_count > 0:
            QMessageBox.warning(self, '警告', '\n'.join(error_messages))
        if success_count > 0:
            QMessageBox.information(self, '成功', f'成功添加 {success_count} 个文件')

    def refresh_project_list(self):
        """刷新项目列表"""
        current_text = self.project_list.currentText()
        self.project_list.clear()
        
        for project in self.project_manager.list_projects():
            self.project_list.addItem(project['name'], project['id'])
            
        # 恢复之前选中的项目
        index = self.project_list.findText(current_text)
        if index >= 0:
            self.project_list.setCurrentIndex(index)
            
        # 更新文件列表
        self.update_file_lists()
        # 更新音量滑块
        self.update_volume_slider()

    def create_project(self):
        """创建新项目"""
        name, ok = QInputDialog.getText(self, '新建项目', '请输入项目名称:')
        if ok and name:
            project = self.project_manager.create_project(name)
            self.refresh_project_list()
            self.project_list.setCurrentText(name)
            self.update_file_lists()

    def delete_project(self):
        """删除项目"""
        selected = self.project_list.currentText()
        if selected:
            reply = QMessageBox.question(
                self,
                '确认删除',
                f'确定要删除项目 "{selected}" 吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                project_id = self.project_list.currentData()
                self.project_manager.delete_project(project_id)
                self.refresh_project_list()
                self.update_file_lists()

    def add_file(self, file_type):
        """添加文件"""
        filter_str = ""
        if file_type == 'audio' or file_type == 'background_music':
            filter_str = "音频文件 (*.mp3 *.wav *.aac)"
        elif file_type == 'images':
            filter_str = "图片文件 (*.jpg *.jpeg *.png)"
            
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            filter_str
        )
        if files:
            self.handle_files(files, file_type)

    def delete_file(self, file_type):
        """删除文件"""
        if file_type == 'audio':
            selected = self.audio_list
        elif file_type == 'images':
            selected = self.image_list
        elif file_type == 'background_music':
            selected = self.bg_music_list
        else:
            return
            
        if selected.selectedIndexes():
            # 获取当前项目下对应类型的文件列表
            if self.project_manager.current_project:
                file_paths = self.project_manager.current_project['files'].get(file_type, [])
                if selected.currentRow() < len(file_paths):
                    # 从项目中移除文件
                    self.project_manager.remove_file(file_paths[selected.currentRow()])
                    # 更新UI
                    selected.takeItem(selected.currentRow())

    def add_log(self, message):
        """添加日志"""
        self.log_text.append(message)
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_generation(self):
        """开始生成视频"""
        if not self.project_manager.current_project:
            QMessageBox.warning(self, '警告', '请先选择或创建一个项目')
            return

        project = self.project_manager.current_project
        audio_files = project['files'].get('audio', [])
        image_files = project['files'].get('images', [])
        bg_music_files = project['files'].get('background_music', [])

        # 检查是否有必要的文件
        if not audio_files:
            QMessageBox.warning(self, '警告', '请先添加音频文件')
            return

        if not image_files:
            QMessageBox.warning(self, '警告', '请先添加图片文件')
            return

        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(self, '选择输出目录', os.path.expanduser('~'))
        if not output_dir:
            return

        # 清空日志
        self.log_text.clear()
            
        # 更新UI状态
        self.generate_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        
        # 添加日志
        self.add_log("开始生成视频...")
        
        # 记录开始时间
        start_time = datetime.now()
        self.add_log(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 输出音频和图片数量信息
        self.add_log(f"音频文件数量: {len(audio_files)}")
        self.add_log(f"图片文件数量: {len(image_files)}")
        
        # 获取背景音乐路径（如果有）
        bg_music_path = None
        if bg_music_files:
            bg_music_path = bg_music_files[0]
            self.add_log(f"使用背景音乐: {os.path.basename(bg_music_path)}")
            
        # 获取背景音乐音量
        bg_music_volume = self.project_manager.get_setting('bg_music_volume', 0.3)
        self.add_log(f"背景音乐音量: {int(bg_music_volume * 100)}%")
        
        # 检查图片和音频数量关系
        if len(image_files) == 1 and len(audio_files) > 1:
            self.add_log("检测到单图片多音频模式: 将为每个音频生成对应视频，视频名称为音频文件名")
        elif len(audio_files) == 1 and len(image_files) > 1:
            self.add_log("检测到单音频多图片模式: 将为每张图片生成对应视频，视频名称为图片文件名")
        elif len(audio_files) == 1 and len(image_files) == 1:
            self.add_log("检测到单音频单图片模式: 将生成一个视频")
        else:
            self.add_log("注意: 音频和图片数量不匹配，将使用第一个音频文件")
            
        # 创建并启动线程
        self.generator_thread = VideoGeneratorThread(
            audio_files, 
            image_files, 
            output_dir,
            bg_music_path,
            bg_music_volume
        )
        self.generator_thread.progress.connect(self.update_generation_progress)
        self.generator_thread.finished.connect(self.on_generation_finished)
        self.generator_thread.log.connect(self.add_log)
        self.generator_thread.start()

    def update_generation_progress(self, current_index, total_images, progress):
        """更新生成进度"""
        # 计算总体进度
        total_progress = int((current_index * 100 + progress) / total_images)
        self.progress_bar.setValue(total_progress)
        # 更新进度条文字
        self.progress_bar.setFormat(f'处理第 {current_index + 1}/{total_images} 个视频: {progress}%')

    def on_generation_finished(self, success, message):
        """视频生成完成处理"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, '完成', f'视频生成完成！\n输出目录：{message}')
        else:
            QMessageBox.critical(self, '错误', f'生成视频时发生错误：{message}')
        
        # 清理临时文件
        self.video_core.cleanup_temp()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 