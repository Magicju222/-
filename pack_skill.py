"""
Excel Cleaner Skill 打包脚本
将 Skill 打包成 ZIP 文件便于分发
"""

import zipfile
import os
from datetime import datetime


def pack_skill():
    """打包 Skill 为 ZIP 文件"""
    
    # Skill 文件列表
    skill_files = [
        'skills/excel-cleaner/SKILL.md',
        'skills/excel-cleaner/excel_cleaner.py',
        'skills/excel-cleaner/interactive.py',
        'skills/excel-cleaner/utils.py',
        'skills/excel-cleaner/requirements.txt',
        'skills/excel-cleaner/README.md',
        'skills/excel-cleaner/examples/__init__.py',
        'skills/excel-cleaner/examples/basic_usage.py',
        'skills/excel-cleaner/examples/batch_process.py',
    ]
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"excel-cleaner-skill_{timestamp}.zip"
    
    print(f"📦 开始打包 Skill...")
    print(f"   输出文件: {zip_filename}")
    print("-" * 60)
    
    # 创建 ZIP 文件
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_files:
            if os.path.exists(file_path):
                # 在 ZIP 中使用相对路径
                arcname = file_path.replace('skills/excel-cleaner/', '')
                zf.write(file_path, arcname)
                print(f"  ✓ {file_path}")
            else:
                print(f"  ⚠️ 文件不存在: {file_path}")
    
    # 获取文件大小
    file_size = os.path.getsize(zip_filename)
    size_mb = file_size / (1024 * 1024)
    
    print("-" * 60)
    print(f"✅ 打包完成!")
    print(f"   文件名: {zip_filename}")
    print(f"   大小: {size_mb:.2f} MB")
    print(f"   文件数: {len(skill_files)}")
    print("\n使用方式:")
    print(f"  1. 解压: unzip {zip_filename} -d my_project/")
    print(f"  2. 安装依赖: pip install -r requirements.txt")
    print(f"  3. 运行交互式清洗: python interactive.py")
    print("=" * 60)
    
    return zip_filename


def pack_skill_simple():
    """简单打包（不带时间戳）"""
    
    skill_files = [
        'skills/excel-cleaner/SKILL.md',
        'skills/excel-cleaner/excel_cleaner.py',
        'skills/excel-cleaner/interactive.py',
        'skills/excel-cleaner/utils.py',
        'skills/excel-cleaner/requirements.txt',
        'skills/excel-cleaner/README.md',
        'skills/excel-cleaner/examples/__init__.py',
        'skills/excel-cleaner/examples/basic_usage.py',
        'skills/excel-cleaner/examples/batch_process.py',
    ]
    
    zip_filename = "excel-cleaner-skill.zip"
    
    print(f"📦 打包 Skill: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in skill_files:
            if os.path.exists(file_path):
                arcname = file_path.replace('skills/excel-cleaner/', '')
                zf.write(file_path, arcname)
    
    file_size = os.path.getsize(zip_filename)
    print(f"✅ 完成! 大小: {file_size / 1024:.1f} KB")
    
    return zip_filename


if __name__ == "__main__":
    print("Excel Cleaner Skill - 打包工具")
    print("=" * 60)
    
    # 使用简单打包（固定文件名）
    pack_skill_simple()
    
    # 或者使用带时间戳的打包
    # pack_skill()
