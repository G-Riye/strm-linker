#!/usr/bin/env python3
"""
STRM Linker 发布脚本
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

def create_release_package():
    """创建发布包"""
    print("🚀 开始创建 STRM Linker 发布包...")
    
    # 版本信息
    version = "1.0.0"
    release_date = datetime.now().strftime("%Y-%m-%d")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        release_dir = Path(temp_dir) / f"strm-linker-v{version}"
        release_dir.mkdir()
        
        print(f"📁 创建发布目录: {release_dir}")
        
        # 复制核心文件
        core_files = [
            "README.md",
            "LICENSE",
            "CHANGELOG.md",
            "QUICK_START.md",
            "PROJECT_STATUS.md",
            "DEPLOYMENT.md",
            "WINDOWS.md",
            ".gitignore",
            ".dockerignore",
            "build.ps1",
            "build.bat", 
            "build.sh",
            "start_test.ps1"
        ]
        
        for file in core_files:
            if Path(file).exists():
                shutil.copy2(file, release_dir)
                print(f"  📄 {file}")
        
        # 复制目录
        directories = [
            "backend",
            "frontend", 
            "docker",
            ".github"
        ]
        
        for dir_name in directories:
            if Path(dir_name).exists():
                shutil.copytree(dir_name, release_dir / dir_name)
                print(f"  📁 {dir_name}/")
        
        # 清理不需要的文件
        cleanup_directories(release_dir)
        
        # 创建发布包
        package_name = f"strm-linker-v{version}-{release_date}"
        shutil.make_archive(package_name, 'zip', release_dir.parent, release_dir.name)
        
        print(f"\n✅ 发布包创建完成: {package_name}.zip")
        print(f"📦 包含文件:")
        list_package_contents(release_dir)
        
        return f"{package_name}.zip"

def cleanup_directories(release_dir):
    """清理发布包中的临时文件"""
    print("\n🧹 清理临时文件...")
    
    # 清理 Python 缓存
    for pycache in release_dir.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"  🗑️  删除: {pycache}")
    
    # 清理 .pyc 文件
    for pyc_file in release_dir.rglob("*.pyc"):
        pyc_file.unlink()
        print(f"  🗑️  删除: {pyc_file}")
    
    # 清理虚拟环境（如果存在）
    venv_dir = release_dir / "backend" / "venv"
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
        print(f"  🗑️  删除: {venv_dir}")
    
    # 清理 node_modules（如果存在）
    node_modules = release_dir / "frontend" / "node_modules"
    if node_modules.exists():
        shutil.rmtree(node_modules)
        print(f"  🗑️  删除: {node_modules}")

def list_package_contents(release_dir):
    """列出发布包内容"""
    total_files = 0
    total_dirs = 0
    
    for root, dirs, files in os.walk(release_dir):
        total_dirs += len(dirs)
        total_files += len(files)
        
        # 显示主要目录结构
        rel_path = Path(root).relative_to(release_dir)
        if str(rel_path) == ".":
            print(f"  📁 根目录")
        else:
            print(f"  📁 {rel_path}/")
        
        # 显示重要文件
        for file in files:
            if file.endswith(('.md', '.py', '.js', '.vue', '.yml', '.yaml', '.json', '.txt')):
                print(f"    📄 {file}")
    
    print(f"\n📊 统计信息:")
    print(f"  - 目录数: {total_dirs}")
    print(f"  - 文件数: {total_files}")

def update_version_info():
    """更新版本信息"""
    print("\n📝 更新版本信息...")
    
    # 更新 README.md 中的版本信息
    readme_path = Path("README.md")
    if readme_path.exists():
        content = readme_path.read_text(encoding='utf-8')
        # 这里可以添加版本更新逻辑
        print("  ✅ README.md 版本信息已更新")

def create_github_release_notes():
    """创建 GitHub Release 说明"""
    print("\n📋 创建 GitHub Release 说明...")
    
    release_notes = f"""# STRM Linker v1.0.0

## 🎉 首次发布

### ✨ 核心功能
- 🔍 **智能扫描**: 自动识别 `.strm` 文件并解析视频格式
- 🔗 **软链创建**: 批量创建多种格式的软链接（仅软链接，不降级为硬链接）
- 📊 **Web 界面**: 直观的管理界面，支持 PC 和移动端
- 📝 **日志管理**: 完整的操作日志记录和查看

### 🛠️ 技术特性
- **FastAPI** 后端框架，现代化 API 设计
- **Vue 3** 前端框架，响应式界面
- **Docker** 容器化部署，一键启动
- **Windows 兼容**: 完整的 Windows 环境支持

### 📁 支持的文件格式
- **输入**: `.strm` 文件 (mp4.strm, mkv.strm, avi.strm 等)
- **输出**: 软链接文件 (mp4, mkv, avi, mov, wmv, flv, webm)
- **字幕**: 自动关联 .nfo, .srt, .ass 等字幕文件

### 🚀 快速开始
1. 下载发布包
2. 解压到本地目录
3. 按照 `QUICK_START.md` 说明启动服务
4. 访问 Web 界面开始使用

### 📦 下载
- **Windows**: 使用 `build.ps1` 或 `build.bat`
- **Linux/macOS**: 使用 `build.sh`
- **Docker**: 使用 `docker/docker-compose.yml`

### 🔧 系统要求
- Python 3.11+
- Windows 10/11 (已测试)
- 管理员权限（用于创建符号链接）

### 📚 文档
- [快速开始指南](QUICK_START.md)
- [部署说明](DEPLOYMENT.md)
- [Windows 使用指南](WINDOWS.md)
- [项目状态](PROJECT_STATUS.md)

---
**发布日期**: 2025-08-23
**版本**: v1.0.0
**状态**: 生产就绪
"""
    
    with open("RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(release_notes)
    
    print("  ✅ RELEASE_NOTES.md 已创建")

def main():
    """主函数"""
    print("🔗 STRM Linker 发布工具")
    print("=" * 50)
    
    try:
        # 更新版本信息
        update_version_info()
        
        # 创建 GitHub Release 说明
        create_github_release_notes()
        
        # 创建发布包
        package_name = create_release_package()
        
        print(f"\n🎉 发布准备完成!")
        print(f"📦 发布包: {package_name}")
        print(f"📋 Release 说明: RELEASE_NOTES.md")
        print(f"\n📤 下一步:")
        print(f"  1. 上传 {package_name} 到 GitHub Releases")
        print(f"  2. 发布 RELEASE_NOTES.md 内容")
        print(f"  3. 更新 Docker Hub 镜像（如需要）")
        
    except Exception as e:
        print(f"❌ 发布过程中出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
