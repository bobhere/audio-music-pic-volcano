import os
import json
import ffmpeg
import pandas as pd
from PIL import Image
from datetime import datetime
from .logger import Logger

class MaterialEngine:
    def __init__(self):
        self.logger = Logger()
        self.temp_dir = os.path.join(os.getcwd(), 'temp')
        self.init_temp_dir()

    def init_temp_dir(self):
        """初始化临时目录"""
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            self.logger.info('MaterialEngine', '创建临时目录')

    def process_audio(self, audio_path):
        """处理音频文件，获取音频信息"""
        try:
            probe = ffmpeg.probe(audio_path)
            audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
            
            info = {
                'duration': float(probe['format']['duration']),
                'bitrate': int(probe['format']['bit_rate']),
                'sample_rate': int(audio_info['sample_rate']),
                'channels': int(audio_info['channels']),
                'codec': audio_info['codec_name']
            }
            
            self.logger.info('MaterialEngine', f'音频文件处理完成: {os.path.basename(audio_path)}', info)
            return info
        except Exception as e:
            self.logger.error('MaterialEngine', f'音频文件处理失败: {str(e)}', {'file': audio_path})
            return None

    def process_image(self, image_path):
        """处理图片文件，获取图片信息"""
        try:
            with Image.open(image_path) as img:
                info = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size
                }
                
                # 如果是PNG格式，转换为JPG
                if img.format == 'PNG':
                    jpg_path = os.path.join(
                        self.temp_dir,
                        f"{os.path.splitext(os.path.basename(image_path))[0]}.jpg"
                    )
                    img.convert('RGB').save(jpg_path, 'JPEG', quality=95)
                    self.logger.info('MaterialEngine', f'PNG转换为JPG: {jpg_path}')
                
                self.logger.info('MaterialEngine', f'图片文件处理完成: {os.path.basename(image_path)}', info)
                return info
        except Exception as e:
            self.logger.error('MaterialEngine', f'图片文件处理失败: {str(e)}', {'file': image_path})
            return None

    def process_video(self, video_path):
        """处理视频文件，获取视频信息"""
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            audio_info = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
            
            info = {
                'duration': float(probe['format']['duration']),
                'width': int(video_info['width']),
                'height': int(video_info['height']),
                'fps': eval(video_info['r_frame_rate']),
                'video_codec': video_info['codec_name'],
                'audio_codec': audio_info['codec_name'],
                'bitrate': int(probe['format']['bit_rate'])
            }
            
            self.logger.info('MaterialEngine', f'视频文件处理完成: {os.path.basename(video_path)}', info)
            return info
        except Exception as e:
            self.logger.error('MaterialEngine', f'视频文件处理失败: {str(e)}', {'file': video_path})
            return None

    def process_excel(self, excel_path):
        """处理Excel文件，获取文案信息"""
        try:
            df = pd.read_excel(excel_path)
            info = {
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': df.columns.tolist()
            }
            
            self.logger.info('MaterialEngine', f'Excel文件处理完成: {os.path.basename(excel_path)}', info)
            return info
        except Exception as e:
            self.logger.error('MaterialEngine', f'Excel文件处理失败: {str(e)}', {'file': excel_path})
            return None

    def extract_audio(self, video_path, output_path=None):
        """从视频中提取音频"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir,
                    f"{os.path.splitext(os.path.basename(video_path))[0]}.mp3"
                )
            
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, output_path, acodec='libmp3lame', ac=2, ar='44100')
            ffmpeg.run(stream, overwrite_output=True)
            
            self.logger.info('MaterialEngine', f'音频提取完成: {output_path}')
            return output_path
        except Exception as e:
            self.logger.error('MaterialEngine', f'音频提取失败: {str(e)}', {'file': video_path})
            return None

    def resize_image(self, image_path, target_size, output_path=None):
        """调整图片大小"""
        try:
            if output_path is None:
                output_path = os.path.join(
                    self.temp_dir,
                    f"resized_{os.path.basename(image_path)}"
                )
            
            with Image.open(image_path) as img:
                resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                resized_img.save(output_path)
            
            self.logger.info('MaterialEngine', f'图片调整完成: {output_path}')
            return output_path
        except Exception as e:
            self.logger.error('MaterialEngine', f'图片调整失败: {str(e)}', {'file': image_path})
            return None

    def get_frame_count(self, video_path):
        """获取视频帧数"""
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            duration = float(probe['format']['duration'])
            fps = eval(video_info['r_frame_rate'])
            frame_count = int(duration * fps)
            
            self.logger.info('MaterialEngine', f'获取视频帧数: {frame_count}', {'file': video_path})
            return frame_count
        except Exception as e:
            self.logger.error('MaterialEngine', f'获取视频帧数失败: {str(e)}', {'file': video_path})
            return None

    def cleanup_temp(self):
        """清理临时文件"""
        try:
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            self.logger.info('MaterialEngine', '清理临时文件完成')
        except Exception as e:
            self.logger.error('MaterialEngine', f'清理临时文件失败: {str(e)}') 