#!/usr/bin/env python3
"""
GitHub大文件自动检测和处理工具
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def find_large_files(directory=".", size_limit=100*1024*1024):
    """查找大于指定大小的文件"""
    large_files = []
    
    for root, dirs, files in os.walk(directory):
        # 跳过.git目录和备份目录
        dirs[:] = [d for d in dirs if d not in ['.git', 'large_files_backup', '__pycache__', '.vscode']]
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path)
                if file_size > size_limit:
                    large_files.append((file_path, file_size))
            except OSError:
                continue
    
    return large_files

def init_git_lfs():
    """初始化Git LFS"""
    try:
        subprocess.run(['git', 'lfs', 'version'], check=True, capture_output=True)
        subprocess.run(['git', 'lfs', 'install'], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 请先安装Git LFS")
        print("访问 https://git-lfs.github.io/ 下载安装")
        return False

def add_to_git_lfs(file_path):
    """添加文件到Git LFS跟踪"""
    try:
        subprocess.run(['git', 'lfs', 'track', file_path], check=True)
        print(f"已添加到Git LFS: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"添加到Git LFS失败: {file_path}, 错误: {e}")
        return False

def compress_image(file_path):
    """尝试压缩图片文件"""
    try:
        from PIL import Image
        
        with Image.open(file_path) as img:
            # 保存原始文件
            backup_path = file_path + ".original"
            shutil.copy2(file_path, backup_path)
            
            # 压缩保存
            if img.format == 'PNG':
                img.save(file_path, 'PNG', optimize=True)
            else:
                img.save(file_path, 'JPEG', quality=85, optimize=True)
            
            new_size = os.path.getsize(file_path)
            if new_size < 100*1024*1024:  # 如果压缩后小于100MB
                os.remove(backup_path)
                return True, new_size
            else:
                # 恢复原文件
                shutil.move(backup_path, file_path)
                return False, new_size
                
    except ImportError:
        print("提示: 安装Pillow库可以自动压缩图片: pip install Pillow")
        return False, 0
    except Exception as e:
        print(f"压缩图片失败: {e}")
        return False, 0

def process_large_files():
    """主要处理函数"""
    print("🔍 正在扫描项目中的大文件...")
    
    # 查找大文件
    large_files = find_large_files()
    
    if not large_files:
        print("✅ 未发现大于100MB的文件，项目可以直接上传到GitHub")
        return
    
    print(f"\n📋 发现 {len(large_files)} 个大文件:")
    for file_path, size in large_files:
        print(f"  📁 {file_path} ({format_size(size)})")
    
    # 初始化Git LFS
    if not init_git_lfs():
        return
    
    # 创建备份目录
    backup_dir = Path("large_files_backup")
    backup_dir.mkdir(exist_ok=True)
    
    processed_files = []
    
    for file_path, size in large_files:
        print(f"\n🔧 处理文件: {file_path}")
        
        # 备份原文件
        backup_file = backup_dir / Path(file_path).name
        try:
            shutil.copy2(file_path, backup_file)
            print(f"  💾 已备份到: {backup_file}")
        except Exception as e:
            print(f"  ⚠️ 备份失败: {e}")
        
        # 根据文件扩展名决定处理方式
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            print("  🖼️ 图片文件，尝试压缩...")
            compressed, new_size = compress_image(file_path)
            if compressed:
                print(f"  ✅ 压缩成功: {format_size(size)} → {format_size(new_size)}")
                continue
            else:
                print("  ➡️ 压缩失败或效果不佳，添加到Git LFS")
        
        # 添加到Git LFS
        if file_ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
            pattern = f"*{file_ext}"
            print(f"  📦 压缩文件，添加模式到Git LFS: {pattern}")
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            pattern = f"*{file_ext}"
            print(f"  🎥 视频文件，添加模式到Git LFS: {pattern}")
        elif file_ext in ['.exe', '.dll', '.so', '.dylib']:
            pattern = f"*{file_ext}"
            print(f"  ⚙️ 二进制文件，添加模式到Git LFS: {pattern}")
        else:
            pattern = file_path
            print(f"  📄 添加单个文件到Git LFS: {pattern}")
        
        add_to_git_lfs(pattern)
        processed_files.append(file_path)
    
    # 更新.gitignore
    gitignore_path = Path(".gitignore")
    gitignore_content = ""
    if gitignore_path.exists():
        gitignore_content = gitignore_path.read_text()
    
    if "large_files_backup/" not in gitignore_content:
        with open(".gitignore", "a") as f:
            f.write("\n# 大文件备份目录\nlarge_files_backup/\n")
    
    print(f"\n🎉 处理完成! 共处理了 {len(processed_files)} 个文件")
    print("\n📝 接下来的步骤:")
    print("  1. git add .gitattributes")
    print("  2. git add .")
    print("  3. git commit -m 'Add large files with Git LFS'")
    print("  4. git push origin main")
    print(f"\n💡 备份文件保存在: {backup_dir}")
    print("   如果上传成功，可以删除此目录")

if __name__ == "__main__":
    try:
        process_large_files()
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        sys.exit(1)