import os
import platform
from pathlib import Path

class CodexCore:
    @staticmethod
    def set_codex_home(path: str):
        """设置 CODEX_HOME 环境变量"""
        path_obj = Path(path).expanduser().resolve()
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
        
        # 在当前进程中设置环境变量
        os.environ["CODEX_HOME"] = str(path_obj)
        print(f"Codex Home set to: {path_obj}")

    @staticmethod
    def create_symlink(source: str, target: str):
        """创建跨平台的符号链接"""
        source_path = Path(source).expanduser().resolve()
        target_path = Path(target).expanduser().resolve()
        
        if target_path.exists() or target_path.is_symlink():
            if target_path.is_symlink():
                target_path.unlink()
            else:
                import shutil
                shutil.rmtree(target_path)
        
        target_path.symlink_to(source_path, target_is_directory=source_path.is_dir())
        print(f"Created symlink: {target_path} -> {source_path}")
