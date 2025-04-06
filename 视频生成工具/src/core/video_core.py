import os
import ffmpeg
from PIL import Image
import time
from datetime import datetime
import shutil

class VideoCore:
    def __init__(self):
        self.temp_dir = 'temp'
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def generate_video_from_images(self, audio_path, image_paths, output_dir, 
                                  progress_callback=None, bg_music_path=None, 
                                  bg_music_volume=0.3):
        """从图片和音频生成视频
        Args:
            audio_path: 音频文件路径
            image_paths: 图片文件路径列表
            output_dir: 输出目录
            progress_callback: 进度回调函数，参数为(当前处理的图片索引, 总图片数, 当前图片的处理进度)
            bg_music_path: 背景音乐文件路径
            bg_music_volume: 背景音乐音量（0.0-1.0）
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
                return self._process_one_audio_multiple_images(audio_paths[0], image_paths, output_folder, 
                                                              progress_callback, bg_music_path, bg_music_volume)
            # 如果是多个音频一张图片的情况
            elif len(audio_paths) > 1 and len(image_paths) == 1:
                return self._process_multiple_audios_one_image(audio_paths, image_paths[0], output_folder, 
                                                              progress_callback, bg_music_path, bg_music_volume)
            # 正常的一对一情况
            else:
                return self._process_one_audio_multiple_images(audio_paths[0], image_paths, output_folder, 
                                                              progress_callback, bg_music_path, bg_music_volume)
                
        except Exception as e:
            print(f"生成视频时发生错误: {str(e)}")
            return False
            
    def _prepare_background_music(self, bg_music_path, target_duration, volume=0.3):
        """准备背景音乐（循环播放至指定长度）
        Args:
            bg_music_path: 背景音乐文件路径
            target_duration: 目标时长（秒）
            volume: 背景音乐音量（0.0-1.0）
        Returns:
            str: 处理后的背景音乐文件路径
        """
        if not bg_music_path or not os.path.exists(bg_music_path):
            print("背景音乐文件不存在，跳过背景音乐处理")
            return None
            
        try:
            # 获取背景音乐时长
            probe = ffmpeg.probe(bg_music_path)
            bg_duration = float(probe['format']['duration'])
            print(f"背景音乐时长: {bg_duration}秒")
            print(f"目标时长: {target_duration}秒")
            
            # 如果背景音乐时长不足，需要循环
            if bg_duration < target_duration:
                print("背景音乐时长不足，进行循环处理")
                # 计算需要循环的次数
                loops = int(target_duration / bg_duration) + 1
                print(f"需要循环 {loops} 次")
                
                # 创建临时文件路径
                temp_file = os.path.join(self.temp_dir, f"looped_bg_{int(time.time())}.mp3")
                
                # 创建循环背景音乐的滤镜
                filter_complex = f"[0:a]aloop=loop={loops-1}:size=2e+09[out]"
                
                # 执行循环处理
                stream = ffmpeg.input(bg_music_path)
                stream = ffmpeg.filter_(stream, "aloop", loop=loops-1, size="2e+09")
                stream = ffmpeg.output(stream, temp_file, t=target_duration, acodec='libmp3lame')
                
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                # 调整音量
                volume_file = os.path.join(self.temp_dir, f"volume_bg_{int(time.time())}.mp3")
                stream = ffmpeg.input(temp_file)
                stream = ffmpeg.filter_(stream, "volume", volume=volume)
                stream = ffmpeg.output(stream, volume_file, acodec='libmp3lame')
                
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                print(f"背景音乐循环处理完成: {volume_file}")
                return volume_file
            else:
                # 只需要截取并调整音量
                print("背景音乐时长足够，只需截取并调整音量")
                temp_file = os.path.join(self.temp_dir, f"volume_bg_{int(time.time())}.mp3")
                
                stream = ffmpeg.input(bg_music_path)
                stream = ffmpeg.filter_(stream, "volume", volume=volume)
                stream = ffmpeg.output(stream, temp_file, t=target_duration, acodec='libmp3lame')
                
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                print(f"背景音乐处理完成: {temp_file}")
                return temp_file
                
        except Exception as e:
            print(f"处理背景音乐时发生错误: {str(e)}")
            return None
            
    def _process_one_audio_multiple_images(self, audio_path, image_paths, output_folder, 
                                          progress_callback=None, bg_music_path=None, 
                                          bg_music_volume=0.3):
        """处理一个音频多张图片的情况"""
        try:
            # 获取音频时长
            probe = ffmpeg.probe(audio_path)
            duration = float(probe['format']['duration'])
            print(f"音频时长: {duration}秒")
            
            # 准备背景音乐（如果有）
            bg_music_temp = None
            if bg_music_path:
                print(f"检测到背景音乐: {bg_music_path}")
                bg_music_temp = self._prepare_background_music(bg_music_path, duration, bg_music_volume)
            
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
                
                # 如果有背景音乐，则混合音频
                if bg_music_temp:
                    print(f"混合背景音乐: {bg_music_temp}")
                    
                    main_audio = ffmpeg.input(audio_path).audio
                    bg_audio = ffmpeg.input(bg_music_temp).audio
                    
                    # 混合背景音乐和主音频
                    mixed_audio = ffmpeg.filter([main_audio, bg_audio], 'amix', 
                                             inputs=2, dropout_transition=0, normalize=0)
                    
                    # 输出到文件
                    stream = ffmpeg.output(
                        stream.video,
                        mixed_audio,
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        video_bitrate='2000k',
                        audio_bitrate='192k',
                        r=30,
                        pix_fmt='yuv420p',
                        preset='ultrafast',
                        threads='auto',
                        shortest=None,
                        movflags='+faststart'
                    )
                else:
                    # 没有背景音乐，只使用原始音频
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
            
    def _process_multiple_audios_one_image(self, audio_paths, image_path, output_folder, 
                                          progress_callback=None, bg_music_path=None, 
                                          bg_music_volume=0.3):
        """处理多个音频一张图片的情况"""
        try:
            total_audios = len(audio_paths)
            
            # 处理每个音频
            for index, audio_path in enumerate(audio_paths):
                # 获取音频时长
                probe = ffmpeg.probe(audio_path)
                duration = float(probe['format']['duration'])
                
                # 准备背景音乐（如果有）
                bg_music_temp = None
                if bg_music_path:
                    print(f"检测到背景音乐: {bg_music_path}")
                    bg_music_temp = self._prepare_background_music(bg_music_path, duration, bg_music_volume)
                
                # 获取音频文件名（不含扩展名）作为输出视频名
                audio_name = os.path.splitext(os.path.basename(audio_path))[0]
                output_path = os.path.join(output_folder, f'{audio_name}.mp4')
                
                print(f"正在处理第 {index + 1}/{total_audios} 个视频: {audio_name}")
                print(f"使用图片: {image_path}")
                print(f"使用音频: {audio_path}")
                print(f"音频时长: {duration}秒")
                
                # 生成视频
                stream = ffmpeg.input(image_path, loop=1, t=duration)
                
                # 如果有背景音乐，则混合音频
                if bg_music_temp:
                    print(f"混合背景音乐: {bg_music_temp}")
                    
                    main_audio = ffmpeg.input(audio_path).audio
                    bg_audio = ffmpeg.input(bg_music_temp).audio
                    
                    # 混合背景音乐和主音频
                    mixed_audio = ffmpeg.filter([main_audio, bg_audio], 'amix', 
                                             inputs=2, dropout_transition=0, normalize=0)
                    
                    # 输出到文件
                    stream = ffmpeg.output(
                        stream.video,
                        mixed_audio,
                        output_path,
                        vcodec='libx264',
                        acodec='aac',
                        video_bitrate='2000k',
                        audio_bitrate='192k',
                        r=30,
                        pix_fmt='yuv420p',
                        preset='ultrafast',
                        threads='auto',
                        shortest=None,
                        movflags='+faststart'
                    )
                else:
                    # 没有背景音乐，只使用原始音频
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