import os
import ffmpeg
from PIL import Image
import time
from datetime import datetime

class VideoCore:
    def __init__(self):
        self.temp_dir = 'temp'
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def generate_video_from_images(self, audio_path, image_paths, output_dir, progress_callback=None):
        """从图片和音频生成视频
        Args:
            audio_path: 音频文件路径
            image_paths: 图片文件路径列表
            output_dir: 输出目录
            progress_callback: 进度回调函数，参数为(当前处理的图片索引, 总图片数, 当前图片的处理进度)
        Returns:
            bool: 是否成功
        """
        try:
            # 创建输出目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_folder = os.path.join(output_dir, f'output_{timestamp}')
            os.makedirs(output_folder, exist_ok=True)
            
            # 判断是一对多（一个音频多张图片）还是多对一（多个音频一张图片）
            audio_paths = [audio_path] if isinstance(audio_path, str) else audio_path
            
            # 如果是一个音频多张图片的情况
            if len(audio_paths) == 1 and len(image_paths) > 1:
                return self._process_one_audio_multiple_images(audio_paths[0], image_paths, output_folder, progress_callback)
            # 如果是多个音频一张图片的情况
            elif len(audio_paths) > 1 and len(image_paths) == 1:
                return self._process_multiple_audios_one_image(audio_paths, image_paths[0], output_folder, progress_callback)
            # 正常的一对一情况
            else:
                return self._process_one_audio_multiple_images(audio_paths[0], image_paths, output_folder, progress_callback)
                
        except Exception as e:
            print(f"生成视频时发生错误: {str(e)}")
            return False
            
    def _process_one_audio_multiple_images(self, audio_path, image_paths, output_folder, progress_callback=None):
        """处理一个音频多张图片的情况"""
        try:
            # 获取音频时长
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])
            print(f"音频时长: {duration}秒")
            
            total_images = len(image_paths)
            
            # 处理每张图片
            for index, image_path in enumerate(image_paths):
                # 获取图片文件名（不含扩展名）作为输出视频名
                image_name = os.path.splitext(os.path.basename(image_path))[0]
                output_path = os.path.join(output_folder, f'{image_name}.mp4')
                
                print(f"正在处理第 {index + 1}/{total_images} 个视频: {image_name}")
                print(f"使用图片: {image_path}")
                
                # 生成视频
                stream = ffmpeg.input(image_path, loop=1, t=duration)
                audio = ffmpeg.input(audio_path)
                
                stream = ffmpeg.output(
                    stream,
                    audio,
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    video_bitrate='2000k',
                    audio_bitrate='128k',
                    r=30,
                    pix_fmt='yuv420p',
                    preset='ultrafast',
                    threads='auto',
                    shortest=None,
                    movflags='+faststart'
                )
                
                print(f"开始生成视频: {image_name}.mp4")
                process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True)
                
                # 监控进度
                start_time = time.time()
                while process.poll() is None:
                    elapsed = time.time() - start_time
                    progress = min(100, int((elapsed / duration) * 100))
                    if progress_callback:
                        # 回调参数：当前图片索引，总图片数，当前图片处理进度
                        progress_callback(index, total_images, progress)
                    time.sleep(0.1)
                
                # 获取输出
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print(f"处理 {image_name} 时发生错误: {stderr.decode() if stderr else '未知错误'}")
                    continue
                    
                print(f"视频 {image_name}.mp4 生成完成")
            
            print(f"所有视频生成完成，输出目录: {output_folder}")
            return True
            
        except ffmpeg.Error as e:
            print(f"FFmpeg错误: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"生成视频时发生错误: {str(e)}")
            return False
            
    def _process_multiple_audios_one_image(self, audio_paths, image_path, output_folder, progress_callback=None):
        """处理多个音频一张图片的情况"""
        try:
            total_audios = len(audio_paths)
            
            # 处理每个音频
            for index, audio_path in enumerate(audio_paths):
                # 获取音频时长
                probe = ffmpeg.probe(audio_path)
                duration = float(probe['format']['duration'])
                
                # 获取音频文件名（不含扩展名）作为输出视频名
                audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                output_path = os.path.join(output_folder, f'{audio_name}.mp4')
                
                print(f"正在处理第 {index + 1}/{total_audios} 个视频: {audio_name}")
                print(f"使用图片: {image_path}")
                print(f"使用音频: {audio_path}")
                print(f"音频时长: {duration}秒")
                
                # 生成视频
                stream = ffmpeg.input(image_path, loop=1, t=duration)
                audio = ffmpeg.input(audio_path)
                
                stream = ffmpeg.output(
                    stream,
                    audio,
                    output_path,
                    vcodec='libx264',
                    acodec='aac',
                    video_bitrate='2000k',
                    audio_bitrate='128k',
                    r=30,
                    pix_fmt='yuv420p',
                    preset='ultrafast',
                    threads='auto',
                    shortest=None,
                    movflags='+faststart'
                )
                
                print(f"开始生成视频: {audio_name}.mp4")
                process = ffmpeg.run_async(stream, pipe_stdout=True, pipe_stderr=True)
                
                # 监控进度
                start_time = time.time()
                while process.poll() is None:
                    elapsed = time.time() - start_time
                    progress = min(100, int((elapsed / duration) * 100))
                    if progress_callback:
                        # 回调参数：当前音频索引，总音频数，当前音频处理进度
                        progress_callback(index, total_audios, progress)
                    time.sleep(0.1)
                
                # 获取输出
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print(f"处理 {audio_name} 时发生错误: {stderr.decode() if stderr else '未知错误'}")
                    continue
                    
                print(f"视频 {audio_name}.mp4 生成完成")
            
            print(f"所有视频生成完成，输出目录: {output_folder}")
            return True
            
        except ffmpeg.Error as e:
            print(f"FFmpeg错误: {e.stderr.decode() if e.stderr else str(e)}")
            return False
        except Exception as e:
            print(f"生成视频时发生错误: {str(e)}")
            return False

    def _resize_image(self, image_path):
        """调整图片大小"""
        try:
            # 打开图片
            img = Image.open(image_path)
            
            # 计算新的尺寸，保持宽高比
            target_width = 1920
            target_height = 1080
            
            # 计算缩放比例
            width_ratio = target_width / img.width
            height_ratio = target_height / img.height
            ratio = min(width_ratio, height_ratio)
            
            new_width = int(img.width * ratio)
            new_height = int(img.height * ratio)
            
            # 调整大小
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 创建新的背景图片
            background = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            
            # 计算居中位置
            x = (target_width - new_width) // 2
            y = (target_height - new_height) // 2
            
            # 将调整后的图片粘贴到背景上
            background.paste(img, (x, y))
            
            # 保存调整后的图片
            output_path = os.path.join(self.temp_dir, os.path.basename(image_path))
            if not output_path.lower().endswith('.jpg'):
                output_path = os.path.splitext(output_path)[0] + '.jpg'
            
            background.save(output_path, 'JPEG', quality=95)
            print(f"图片调整完成: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"调整图片大小时发生错误: {str(e)}")
            return image_path

    def cleanup_temp(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    file_path = os.path.join(self.temp_dir, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"删除临时文件失败: {str(e)}")
        except Exception as e:
            print(f"清理临时目录失败: {str(e)}") 