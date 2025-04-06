import os
import json
from datetime import datetime

class ProjectManager:
    def __init__(self):
        self.projects_dir = 'projects'
        self.current_project = None
        self._ensure_projects_dir()

    def _ensure_projects_dir(self):
        """确保项目目录存在"""
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)

    def create_project(self, name):
        """创建新项目"""
        project_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        project = {
            'id': project_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'files': {
                'audio': [],
                'images': []
            }
        }

        # 创建项目目录
        project_dir = os.path.join(self.projects_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)

        # 保存项目配置
        project_file = os.path.join(project_dir, 'project.json')
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project, f, ensure_ascii=False, indent=2)

        self.current_project = project
        return project

    def list_projects(self):
        """列出所有项目"""
        projects = []
        for project_id in os.listdir(self.projects_dir):
            project_dir = os.path.join(self.projects_dir, project_id)
            if os.path.isdir(project_dir):
                project_file = os.path.join(project_dir, 'project.json')
                if os.path.exists(project_file):
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project = json.load(f)
                        projects.append(project)
        return projects

    def load_project(self, project_id):
        """加载项目"""
        project_dir = os.path.join(self.projects_dir, project_id)
        project_file = os.path.join(project_dir, 'project.json')
        if os.path.exists(project_file):
            with open(project_file, 'r', encoding='utf-8') as f:
                project = json.load(f)
                # 确保项目包含所有必要的文件类型
                if 'files' not in project:
                    project['files'] = {}
                if 'audio' not in project['files']:
                    project['files']['audio'] = []
                if 'images' not in project['files']:
                    project['files']['images'] = []
                self.current_project = project
                return project
        return None

    def delete_project(self, project_id):
        """删除项目"""
        project_dir = os.path.join(self.projects_dir, project_id)
        if os.path.exists(project_dir):
            import shutil
            shutil.rmtree(project_dir)
            if self.current_project and self.current_project['id'] == project_id:
                self.current_project = None
            return True
        return False

    def add_file(self, file_type, file_path):
        """添加文件到项目"""
        if not self.current_project:
            print("错误：没有当前项目")
            return False

        # 检查文件类型是否支持
        if file_type not in ['audio', 'images']:
            print(f"错误：不支持的文件类型 {file_type}")
            return False

        # 检查文件是否存在
        if not os.path.exists(file_path):
            print(f"错误：文件不存在 {file_path}")
            return False

        # 检查文件是否已经添加
        if file_path not in self.current_project['files'][file_type]:
            self.current_project['files'][file_type].append(file_path)
            self._save_project()
            print(f"成功：添加文件 {file_path} 到类型 {file_type}")
            return True
        else:
            print(f"提示：文件 {file_path} 已经存在于类型 {file_type}")
        return False

    def remove_file(self, file_path):
        """从项目中移除文件"""
        if not self.current_project:
            return False

        for file_type in self.current_project['files']:
            if file_path in self.current_project['files'][file_type]:
                self.current_project['files'][file_type].remove(file_path)
                self._save_project()
                return True
        return False

    def _save_project(self):
        """保存当前项目"""
        if not self.current_project:
            return False

        project_dir = os.path.join(self.projects_dir, self.current_project['id'])
        project_file = os.path.join(project_dir, 'project.json')
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_project, f, ensure_ascii=False, indent=2)
        return True 