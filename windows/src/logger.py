import os
import json
from datetime import datetime

class Logger:
    def __init__(self):
        self.log_dir = os.path.join(os.getcwd(), 'logs')
        self.log_file = os.path.join(self.log_dir, f'app-{datetime.now().strftime("%Y-%m-%d")}.log')
        self.callback = None
        self.init_log_dir()

    def init_log_dir(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)

    def set_callback(self, callback):
        self.callback = callback

    def log(self, level, module, message, data=None):
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'module': module,
            'message': message,
            'data': data
        }

        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        # 控制台输出
        print(f'[{timestamp}] [{level}] [{module}] {message}', data if data else '')

        # 回调通知
        if self.callback:
            self.callback(level, module, message, data)

    def info(self, module, message, data=None):
        self.log('INFO', module, message, data)

    def warn(self, module, message, data=None):
        self.log('WARN', module, message, data)

    def error(self, module, message, data=None):
        self.log('ERROR', module, message, data) 