import React from 'react';
import { Tag, Tooltip, Space } from 'antd';
import {
  CodeOutlined,
  MessageOutlined,
  BulbOutlined,
  StarOutlined,
  SettingOutlined,
  NodeIndexOutlined,
  LinkOutlined
} from '@ant-design/icons';
import styled from 'styled-components';

interface TagInfo {
  name: string;
  type: string;
  category?: string;
  description?: string;
  color?: string;
  icon?: string;
  display_name?: string;
}

interface SmartTagDisplayProps {
  tags: string[] | TagInfo[];
  maxTags?: number;
  size?: 'small' | 'default' | 'large';
  showTooltip?: boolean;
  className?: string;
}

const StyledTagContainer = styled.div`
  .smart-tag {
    margin: 2px 4px 2px 0;
    border-radius: 6px;
    font-size: 12px;
    line-height: 20px;
    padding: 2px 8px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    
    &.algorithm {
      background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
      border: 1px solid #91d5ff;
      color: #0958d9;
    }
    
    &.data-structure {
      background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
      border: 1px solid #b7eb8f;
      color: #389e0d;
    }
    
    &.technique {
      background: linear-gradient(135deg, #f9f0ff 0%, #efdbff 100%);
      border: 1px solid #d3adf7;
      color: #722ed1;
    }
    
    &.difficulty {
      background: linear-gradient(135deg, #fff7e6 0%, #ffd591 100%);
      border: 1px solid #ffb84d;
      color: #d46b08;
    }
    
    &.platform {
      background: linear-gradient(135deg, #e6fffb 0%, #87e8de 100%);
      border: 1px solid #5cdbd3;
      color: #08979c;
    }
    
    &.category {
      background: linear-gradient(135deg, #fff0f6 0%, #ffadd2 100%);
      border: 1px solid #ff85c0;
      color: #c41d7f;
    }
    
    &.relationship {
      background: linear-gradient(135deg, #fffbe6 0%, #fff566 100%);
      border: 1px solid #ffec3d;
      color: #d48806;
    }
    
    &.default {
      background: linear-gradient(135deg, #f5f5f5 0%, #d9d9d9 100%);
      border: 1px solid #bfbfbf;
      color: #595959;
    }
    
    .tag-icon {
      font-size: 10px;
    }
  }
  
  .more-tags {
    color: #8c8c8c;
    font-size: 12px;
    cursor: pointer;
    
    &:hover {
      color: #1890ff;
    }
  }
`;

const SmartTagDisplay: React.FC<SmartTagDisplayProps> = ({
  tags,
  maxTags = 8,
  size = 'small',
  showTooltip = true,
  className
}) => {
  // 解析标签数据
  const parseTag = (tag: string | TagInfo): TagInfo => {
    if (typeof tag === 'string') {
      // 简单的字符串标签解析
      const cleanTag = tag.replace(/^[🔧📊💡⭐🌐📂🔗]\s*/, ''); // 移除emoji前缀
      
      // 根据内容推断类型
      let type = 'default';
      if (tag.includes('算法') || tag.includes('排序') || tag.includes('搜索') || tag.includes('动态规划') || tag.includes('贪心')) {
        type = 'algorithm';
      } else if (tag.includes('数据结构') || tag.includes('数组') || tag.includes('链表') || tag.includes('树') || tag.includes('图')) {
        type = 'data-structure';
      } else if (tag.includes('技巧') || tag.includes('双指针') || tag.includes('滑动窗口')) {
        type = 'technique';
      } else if (tag.includes('简单') || tag.includes('中等') || tag.includes('困难')) {
        type = 'difficulty';
      } else if (tag.includes('LeetCode') || tag.includes('牛客') || tag.includes('平台')) {
        type = 'platform';
      } else if (tag.includes('关系') || tag.includes('相似') || tag.includes('推荐')) {
        type = 'relationship';
      } else {
        type = 'category';
      }
      
      return {
        name: cleanTag,
        type,
        display_name: tag
      };
    }
    return tag;
  };

  // 获取图标
  const getIcon = (type: string) => {
    switch (type) {
      case 'algorithm':
        return <CodeOutlined className="tag-icon" />;
      case 'data-structure':
        return <MessageOutlined className="tag-icon" />;
      case 'technique':
        return <BulbOutlined className="tag-icon" />;
      case 'difficulty':
        return <StarOutlined className="tag-icon" />;
      case 'platform':
        return <SettingOutlined className="tag-icon" />;
      case 'category':
        return <NodeIndexOutlined className="tag-icon" />;
      case 'relationship':
        return <LinkOutlined className="tag-icon" />;
      default:
        return null;
    }
  };

  if (!tags || tags.length === 0) {
    return null;
  }

  const parsedTags = tags.map(parseTag);
  const displayTags = parsedTags.slice(0, maxTags);
  const remainingCount = parsedTags.length - maxTags;

  const renderTag = (tagInfo: TagInfo, index: number) => {
    const tagContent = (
      <span className={`smart-tag ${tagInfo.type}`}>
        {getIcon(tagInfo.type)}
        {tagInfo.display_name || tagInfo.name}
      </span>
    );

    if (showTooltip && tagInfo.description) {
      return (
        <Tooltip 
          key={index}
          title={
            <div>
              <div><strong>{tagInfo.name}</strong></div>
              {tagInfo.category && <div>类别: {tagInfo.category}</div>}
              {tagInfo.description && <div>{tagInfo.description}</div>}
            </div>
          }
        >
          {tagContent}
        </Tooltip>
      );
    }

    return <span key={index}>{tagContent}</span>;
  };

  return (
    <StyledTagContainer className={className}>
      <Space size={[4, 4]} wrap>
        {displayTags.map(renderTag)}
        {remainingCount > 0 && (
          <Tooltip title={`还有 ${remainingCount} 个标签`}>
            <span className="more-tags">+{remainingCount}</span>
          </Tooltip>
        )}
      </Space>
    </StyledTagContainer>
  );
};

export default SmartTagDisplay;
