const fs = require('fs');
const path = require('path');

// 需要修复的文件列表
const filesToFix = [
  'src/components/qa/EnhancedReasoningPath.tsx',
  'src/components/qa/MessageItem.tsx',
  'src/components/qa/ReasoningPath.tsx',
  'src/components/graph/GraphAnalysisPanel.tsx'
];

// 修复函数
function fixTagSizeAttribute(content) {
  // 移除 size="small" 属性，添加 style={{ fontSize: '12px' }}
  return content.replace(
    /(<Tag[^>]*)\s+size="small"([^>]*>)/g,
    (match, before, after) => {
      // 检查是否已经有style属性
      if (before.includes('style=')) {
        // 如果已有style，在其中添加fontSize
        return before.replace(
          /style=\{\{([^}]*)\}\}/,
          (styleMatch, styleContent) => {
            if (styleContent.includes('fontSize')) {
              return styleMatch; // 已经有fontSize，不修改
            }
            return `style={{ ${styleContent.trim()}, fontSize: '12px' }}`;
          }
        ) + after;
      } else {
        // 如果没有style，添加新的style属性
        return before + ' style={{ fontSize: \'12px\' }}' + after;
      }
    }
  );
}

// 移除styled-jsx语法
function removeStyledJsx(content) {
  return content.replace(
    /<style jsx>\{`[\s\S]*?`\}<\/style>/g,
    ''
  );
}

// 修复ReactMarkdown的inline属性
function fixReactMarkdown(content) {
  return content.replace(
    /code\(\{ node, inline, className, children, \.\.\.props \}\)/g,
    'code({ node, className, children, ...props })'
  ).replace(
    /!inline && match/g,
    'match'
  );
}

// 处理每个文件
filesToFix.forEach(filePath => {
  const fullPath = path.join(__dirname, '..', 'frontend', filePath);
  
  if (fs.existsSync(fullPath)) {
    console.log(`修复文件: ${filePath}`);
    
    let content = fs.readFileSync(fullPath, 'utf8');
    
    // 应用修复
    content = fixTagSizeAttribute(content);
    content = removeStyledJsx(content);
    content = fixReactMarkdown(content);
    
    // 写回文件
    fs.writeFileSync(fullPath, content, 'utf8');
    
    console.log(`✅ 已修复: ${filePath}`);
  } else {
    console.log(`❌ 文件不存在: ${filePath}`);
  }
});

console.log('🎉 TypeScript错误修复完成！');
