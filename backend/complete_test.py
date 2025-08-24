#!/usr/bin/env python3
"""
完整的 STRM 软链接生成测试脚本
演示所有功能和使用方法
"""

import os
import tempfile
import shutil
from pathlib import Path
from services.scanner import StrmScanner

def create_complete_test_environment(test_dir: Path):
    """创建完整的测试环境"""
    print("📁 创建测试环境...")
    
    # 确保目录存在
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建 STRM 文件
    strm_files = [
        "绝命毒师.S01E01.(mp4).strm",
        "绝命毒师.S01E02.(mkv).strm", 
        "权力的游戏.S01E01.(mp4).strm",
        "权力的游戏.S01E02.(mkv).strm"
    ]
    
    for filename in strm_files:
        file_path = test_dir / filename
        file_path.write_text("http://example.com/stream")
        print(f"  ✅ 创建 STRM 文件: {filename}")
    
    # 创建元数据文件
    metadata_files = [
        # NFO 文件
        ("绝命毒师.S01E01.nfo", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>绝命毒师 S01E01</title>
    <year>2008</year>
    <season>1</season>
    <episode>1</episode>
</episodedetails>"""),
        
        ("绝命毒师.S01E01.srt", """1
00:00:01,000 --> 00:00:05,000
绝命毒师 第一季 第一集

2
00:00:05,000 --> 00:00:10,000
欢迎观看"""),
        
        ("绝命毒师.S01E01.ass", """[Script Info]
Title: 绝命毒师 S01E01
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:05.00,Default,,0,0,0,,绝命毒师 第一季 第一集"""),
        
        ("绝命毒师.S01E01.jpg", "fake poster image data"),
        ("绝命毒师.S01E01.fanart.jpg", "fake fanart image data"),
        ("绝命毒师.S01E01.json", """{
    "title": "绝命毒师 S01E01",
    "year": 2008,
    "season": 1,
    "episode": 1,
    "rating": 9.5
}"""),
        
        # 第二个文件的元数据
        ("绝命毒师.S01E02.nfo", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>绝命毒师 S01E02</title>
    <year>2008</year>
    <season>1</season>
    <episode>2</episode>
</episodedetails>"""),
        
        ("权力的游戏.S01E01.nfo", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>权力的游戏 S01E01</title>
    <year>2011</year>
    <season>1</season>
    <episode>1</episode>
</episodedetails>"""),
        
        ("权力的游戏.S01E02.nfo", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>权力的游戏 S01E02</title>
    <year>2011</year>
    <season>1</season>
    <episode>2</episode>
</episodedetails>""")
    ]
    
    for filename, content in metadata_files:
        file_path = test_dir / filename
        file_path.write_text(content)
        print(f"  ✅ 创建元数据文件: {filename}")

def show_directory_structure(directory: Path, title: str):
    """显示目录结构"""
    print(f"\n📋 {title}:")
    print("-" * 50)
    
    files = sorted(directory.glob("*"))
    if not files:
        print("  (空目录)")
        return
    
    for file_path in files:
        if file_path.is_file():
            file_type = "🔗 软链接" if file_path.is_symlink() else "📄 文件"
            print(f"  {file_type} {file_path.name}")

def run_complete_test():
    """运行完整测试"""
    print("🚀 STRM 软链接生成器 - 完整功能测试")
    print("=" * 60)
    
    # 创建临时测试目录
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir) / "media_library"
        create_complete_test_environment(test_dir)
        
        print(f"\n📁 测试目录: {test_dir}")
        
        # 显示初始状态
        show_directory_structure(test_dir, "初始文件结构")
        
        # 初始化扫描器
        scanner = StrmScanner()
        
        # 显示支持的扩展名
        print(f"\n📝 支持的扩展名:")
        print(f"  视频格式: {', '.join(sorted(scanner.video_extensions))}")
        print(f"  元数据格式: {', '.join(sorted(scanner.metadata_extensions))}")
        
        # 预览模式测试
        print(f"\n🔍 预览模式测试...")
        preview_result = scanner.scan_directory(
            directory=str(test_dir),
            recursive=True,
            dry_run=True
        )
        
        print(f"✅ 预览结果:")
        print(f"  - 找到 STRM 文件: {preview_result['total_files']} 个")
        print(f"  - 将创建软链接: {preview_result['created_links']} 个")
        print(f"  - 错误数量: {len(preview_result['errors'])} 个")
        
        # 显示预览详情
        print(f"\n📋 预览详情:")
        for detail in preview_result['details']:
            file_info = detail['result']
            print(f"  📄 {detail['file']}:")
            print(f"     基础名称: {file_info['base_name']}")
            print(f"     视频格式: {file_info['video_extension']}")
            print(f"     将创建链接: {file_info['links_created']} 个")
            if file_info['created_links']:
                for link in file_info['created_links']:
                    print(f"       🔗 {Path(link).name}")
        
        # 实际创建软链接
        print(f"\n🔗 实际创建软链接...")
        actual_result = scanner.scan_directory(
            directory=str(test_dir),
            recursive=True,
            dry_run=False
        )
        
        print(f"✅ 创建结果:")
        print(f"  - 成功创建: {actual_result['created_links']} 个软链接")
        print(f"  - 错误数量: {len(actual_result['errors'])} 个")
        
        if actual_result['errors']:
            print(f"\n❌ 错误详情:")
            for error in actual_result['errors']:
                print(f"  - {error['file']}: {error['error']}")
        
        # 显示最终状态
        show_directory_structure(test_dir, "最终文件结构")
        
        # 验证软链接
        print(f"\n🔍 软链接验证:")
        symlink_count = 0
        for file_path in test_dir.glob("*"):
            if file_path.is_symlink():
                symlink_count += 1
                target = file_path.readlink()
                print(f"  🔗 {file_path.name} -> {target.name}")
        
        print(f"\n📊 统计结果:")
        print(f"  - 原始文件: {len(list(test_dir.glob('*.strm')))} 个 STRM 文件")
        print(f"  - 元数据文件: {len(list(test_dir.glob('*.nfo')))} 个 NFO 文件")
        print(f"  - 创建软链接: {symlink_count} 个")
        
        print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    run_complete_test()
