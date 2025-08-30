#!/usr/bin/env python3
"""
快速修复TypeScript错误的脚本
"""

import os
import re

def fix_file(file_path):
    """修复单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. 移除所有 size="small" 属性
        content = re.sub(r'\s+size="small"', '', content)
        
        # 2. 移除所有 styled-jsx 块
        content = re.sub(r'<style jsx>\{`[\s\S]*?`\}</style>', '', content)
        
        # 3. 修复 message.success 问题 - 确保导入了 message
        if 'message.success' in content and 'import {' in content:
            # 检查是否已经导入了 message
            if ', message' not in content and 'message,' not in content:
                # 在第一个 import 语句中添加 message
                content = re.sub(
                    r"(import\s*\{[^}]*)(}\s*from\s*['\"]antd['\"])",
                    r'\1, message\2',
                    content
                )
        
        # 4. 修复 ReactMarkdown inline 属性问题
        content = re.sub(
            r'code\(\{\s*node,\s*inline,\s*className,\s*children,\s*\.\.\.props\s*\}\)',
            'code({ node, className, children, ...props })',
            content
        )
        
        # 5. 修复 !inline && match 问题
        content = re.sub(r'!inline && match', 'match', content)
        
        # 6. 修复 SyntaxHighlighter style 问题
        content = re.sub(
            r'style=\{tomorrow\}',
            'style={tomorrow as any}',
            content
        )
        
        # 7. 移除多余的空行
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修复: {file_path}")
            return True
        else:
            print(f"⏭️  无需修复: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False

def main():
    # 需要修复的文件
    files_to_fix = [
        'src/components/qa/EnhancedReasoningPath.tsx',
        'src/components/qa/MessageItem.tsx', 
        'src/components/qa/ReasoningPath.tsx',
        'src/components/graph/GraphAnalysisPanel.tsx',
        'src/components/graph/EnhancedGraphVisualization.tsx',
        'src/components/graph/GraphVisualization.tsx',
        'src/components/common/QueryInput.tsx',
        'src/components/common/SmartLinkSuggestions.tsx'
    ]
    
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    
    for file_path in files_to_fix:
        full_path = os.path.join(frontend_dir, file_path)
        if os.path.exists(full_path):
            fix_file(full_path)
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    print("🎉 批量修复完成！")

if __name__ == "__main__":
    main()
