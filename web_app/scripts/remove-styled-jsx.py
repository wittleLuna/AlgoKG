#!/usr/bin/env python3
"""
移除所有styled-jsx语法的脚本
"""

import os
import re

def remove_styled_jsx_from_file(file_path):
    """从文件中移除styled-jsx语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除styled-jsx块
        pattern = r'<style jsx>\{`[\s\S]*?`\}</style>'
        new_content = re.sub(pattern, '', content)
        
        # 移除多余的空行
        new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ 已修复: {file_path}")
            return True
        else:
            print(f"⏭️  无需修复: {file_path}")
            return False
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False

def remove_tag_size_attribute(file_path):
    """移除Tag组件的size属性"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 移除size="small"属性，并添加style={{ fontSize: '12px' }}
        pattern = r'(<Tag[^>]*)\s+size="small"([^>]*>)'
        
        def replace_tag(match):
            before = match.group(1)
            after = match.group(2)
            
            # 检查是否已经有style属性
            if 'style=' in before:
                # 如果已有style，在其中添加fontSize
                style_pattern = r'style=\{\{([^}]*)\}\}'
                def add_font_size(style_match):
                    style_content = style_match.group(1)
                    if 'fontSize' in style_content:
                        return style_match.group(0)  # 已经有fontSize，不修改
                    return f"style={{{{ {style_content.strip()}, fontSize: '12px' }}}}"
                
                before = re.sub(style_pattern, add_font_size, before)
            else:
                # 如果没有style，添加新的style属性
                before += ' style={{ fontSize: \'12px\' }}'
            
            return before + after
        
        new_content = re.sub(pattern, replace_tag, content)
        
        if content != new_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✅ 已修复Tag size属性: {file_path}")
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ 错误处理Tag属性 {file_path}: {e}")
        return False

def main():
    # 需要处理的目录
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src')
    
    # 遍历所有tsx和ts文件
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(('.tsx', '.ts')):
                file_path = os.path.join(root, file)
                remove_styled_jsx_from_file(file_path)
                remove_tag_size_attribute(file_path)
    
    print("🎉 批量修复完成！")

if __name__ == "__main__":
    main()
