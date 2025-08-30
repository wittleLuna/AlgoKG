import React, { useState, useEffect } from 'react';
import { Card, List, Button, Tag, Space, Typography, Divider, Tooltip, Popover, Progress } from 'antd';
import {
  BulbOutlined,
  QuestionCircleOutlined,
  RightOutlined,
  StarOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { QAResponse } from '../../types';

const { Text, Title } = Typography;

interface SmartLinkSuggestionsProps {
  response?: QAResponse;
  onConceptClick?: (concept: string) => void;
  onProblemClick?: (problem: string) => void;
  className?: string;
}

interface Suggestion {
  id: string;
  title: string;
  type: 'concept' | 'problem' | 'learning_path';
  description: string;
  difficulty?: string;
  tags: string[];
  relevance: number;
  reason: string;
}

const SmartLinkSuggestions: React.FC<SmartLinkSuggestionsProps> = ({
  response,
  onConceptClick,
  onProblemClick,
  className
}) => {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);

  // 生成智能建议
  const generateSuggestions = (response: QAResponse): Suggestion[] => {
    const suggestions: Suggestion[] = [];

    // 基于概念解释生成建议
    if (response.concept_explanation) {
      const concept = response.concept_explanation;
      
      // 前置概念建议
      const prerequisites = concept.learning_progression?.prerequisites || [];
      prerequisites.forEach((prereq, index) => {
        suggestions.push({
          id: `prereq-${index}`,
          title: prereq,
          type: 'concept',
          description: `学习${concept.concept_name}的前置知识`,
          tags: ['前置知识', '基础'],
          relevance: 0.9,
          reason: '掌握前置知识有助于更好理解当前概念'
        });
      });

      // 后续概念建议
      const nextConcepts = concept.learning_progression?.next_concepts || [];
      nextConcepts.forEach((next, index) => {
        suggestions.push({
          id: `next-${index}`,
          title: next,
          type: 'concept',
          description: `${concept.concept_name}的进阶学习`,
          tags: ['进阶', '拓展'],
          relevance: 0.8,
          reason: '继续深入学习相关高级概念'
        });
      });

      // 相似概念建议
      concept.clickable_concepts?.forEach((similar, index) => {
        if (!prerequisites.includes(similar) && !nextConcepts.includes(similar)) {
          suggestions.push({
            id: `similar-${index}`,
            title: similar,
            type: 'concept',
            description: `与${concept.concept_name}相关的概念`,
            tags: ['相关概念'],
            relevance: 0.7,
            reason: '了解相关概念有助于建立知识体系'
          });
        }
      });
    }

    // 基于示例题目生成建议
    response.example_problems?.forEach((problem, index) => {
      if (problem.clickable) {
        suggestions.push({
          id: `example-${index}`,
          title: problem.title,
          type: 'problem',
          description: problem.description || '相关练习题目',
          difficulty: problem.difficulty,
          tags: [...problem.algorithm_tags, ...problem.data_structure_tags],
          relevance: 0.85,
          reason: '通过练习加深理解'
        });
      }
    });

    // 基于相似题目生成建议
    response.similar_problems?.forEach((similar, index) => {
      if (similar.clickable) {
        suggestions.push({
          id: `similar-problem-${index}`,
          title: similar.title,
          type: 'problem',
          description: similar.recommendation_reason,
          difficulty: similar.complete_info?.difficulty,
          tags: similar.shared_tags,
          relevance: similar.hybrid_score,
          reason: similar.learning_path_explanation
        });
      }
    });

    // 基于实体生成学习路径建议
    if (response.entities && response.entities.length > 0) {
      const mainEntity = response.entities[0];
      suggestions.push({
        id: 'learning-path',
        title: `${mainEntity}学习路径`,
        type: 'learning_path',
        description: `系统学习${mainEntity}的完整路径`,
        tags: ['学习路径', '系统学习'],
        relevance: 0.9,
        reason: '系统性学习能够建立完整的知识体系'
      });
    }

    // 按相关性排序并去重
    const uniqueSuggestions = suggestions.filter((suggestion, index, self) =>
      index === self.findIndex(s => s.title === suggestion.title && s.type === suggestion.type)
    );

    return uniqueSuggestions
      .sort((a, b) => b.relevance - a.relevance)
      .slice(0, 8); // 限制建议数量
  };

  // 当响应变化时更新建议
  useEffect(() => {
    if (response) {
      setLoading(true);
      // 模拟异步处理
      setTimeout(() => {
        const newSuggestions = generateSuggestions(response);
        setSuggestions(newSuggestions);
        setLoading(false);
      }, 500);
    }
  }, [response]);

  // 获取类型图标
  const getTypeIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'concept': <BulbOutlined style={{ color: '#1890ff' }} />,
      'problem': <QuestionCircleOutlined style={{ color: '#fa8c16' }} />,
      'learning_path': <TrophyOutlined style={{ color: '#52c41a' }} />
    };
    return iconMap[type] || <BulbOutlined />;
  };

  // 获取难度颜色
  const getDifficultyColor = (difficulty?: string) => {
    const colorMap: Record<string, string> = {
      '简单': 'green',
      '中等': 'orange',
      '困难': 'red'
    };
    return colorMap[difficulty || ''] || 'default';
  };

  // 生成详细信息的Popover内容
  const getDetailedPopoverContent = (suggestion: any) => {
    return (
      <div style={{ maxWidth: 300 }}>
        <div style={{ marginBottom: 12 }}>
          <Text strong>{suggestion.title}</Text>
          {suggestion.difficulty && (
            <Tag
              color={getDifficultyColor(suggestion.difficulty)}
              style={{ marginLeft: 8 }}
            >
              {suggestion.difficulty}
            </Tag>
          )}
        </div>

        {suggestion.description && (
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">{suggestion.description}</Text>
          </div>
        )}

        {suggestion.relevance && (
          <div style={{ marginBottom: 8 }}>
            <Text strong>相关性: </Text>
            <Progress
              percent={Math.round(suggestion.relevance * 100)}
              size="small"
              showInfo={false}
              style={{ width: 100, display: 'inline-block', marginLeft: 4 }}
            />
            <Text type="secondary" style={{ marginLeft: 8 }}>
              {(suggestion.relevance * 100).toFixed(1)}%
            </Text>
          </div>
        )}

        {suggestion.tags && suggestion.tags.length > 0 && (
          <div style={{ marginBottom: 8 }}>
            <div style={{ marginBottom: 4 }}>
              <StarOutlined style={{ marginRight: 4 }} />
              <Text strong>标签:</Text>
            </div>
            <div>
              {suggestion.tags.slice(0, 5).map((tag: string, index: number) => (
                <Tag key={index} size="small" style={{ marginBottom: 2 }}>
                  {tag}
                </Tag>
              ))}
              {suggestion.tags.length > 5 && (
                <Text type="secondary">+{suggestion.tags.length - 5}个</Text>
              )}
            </div>
          </div>
        )}

        {suggestion.reason && (
          <div>
            <Text strong>推荐理由: </Text>
            <Text type="secondary">{suggestion.reason}</Text>
          </div>
        )}
      </div>
    );
  };

  // 处理点击事件
  const handleSuggestionClick = (suggestion: Suggestion) => {
    // 添加点击反馈
    const clickedElement = document.querySelector(`[data-suggestion-id="${suggestion.id}"]`);
    if (clickedElement) {
      clickedElement.classList.add('suggestion-clicked');
      setTimeout(() => {
        clickedElement.classList.remove('suggestion-clicked');
      }, 300);
    }

    switch (suggestion.type) {
      case 'concept':
        if (onConceptClick) {
          onConceptClick(suggestion.title);
        }
        break;
      case 'problem':
        if (onProblemClick) {
          onProblemClick(suggestion.title);
        }
        break;
      case 'learning_path':
        // 可以触发学习路径查询
        if (onConceptClick) {
          onConceptClick(`${suggestion.title.replace('学习路径', '')}的学习路径`);
        }
        break;
    }
  };

  if (!response || suggestions.length === 0) {
    return null;
  }

  return (
    <Card
      className={`smart-link-suggestions ${className || ''}`}
      title={
        <Space>
          <StarOutlined style={{ color: '#faad14' }} />
          <Title level={5} style={{ margin: 0 }}>
            智能推荐
          </Title>
        </Space>
      }
      size="small"
      loading={loading}
    >
      <List
        size="small"
        dataSource={suggestions}
        renderItem={(suggestion) => (
          <List.Item
            className="suggestion-item"
            data-suggestion-id={suggestion.id}
            onClick={() => handleSuggestionClick(suggestion)}
          >
            <div className="suggestion-content">
              <div className="suggestion-header">
                <Space>
                  {getTypeIcon(suggestion.type)}
                  <Text strong className="suggestion-title">
                    {suggestion.title}
                  </Text>
                  {suggestion.difficulty && (
                    <Tag
                      color={getDifficultyColor(suggestion.difficulty)}
                      style={{ fontSize: '12px' }}
                    >
                      {suggestion.difficulty}
                    </Tag>
                  )}
                </Space>
                
                <div className="suggestion-actions">
                  <Tooltip title={`相关性: ${(suggestion.relevance * 100).toFixed(0)}%`}>
                    <div className="relevance-indicator">
                      <div
                        className="relevance-bar"
                        style={{ width: `${suggestion.relevance * 100}%` }}
                      />
                    </div>
                  </Tooltip>
                  <Space>
                    <Popover
                      content={getDetailedPopoverContent(suggestion)}
                      title="详细信息"
                      trigger="hover"
                      placement="topRight"
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<InfoCircleOutlined />}
                        className="suggestion-info-button"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popover>
                    <Button
                      type="text"
                      size="small"
                      icon={<RightOutlined />}
                      className="suggestion-button"
                    />
                  </Space>
                </div>
              </div>

              <div className="suggestion-description">
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {suggestion.description}
                </Text>
              </div>

              {suggestion.tags.length > 0 && (
                <div className="suggestion-tags">
                  {suggestion.tags.slice(0, 3).map((tag, index) => (
                    <Tag key={index} color="blue" style={{ fontSize: '12px' }}>
                      {tag}
                    </Tag>
                  ))}
                </div>
              )}

              <div className="suggestion-reason">
                <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
                  💡 {suggestion.reason}
                </Text>
              </div>
            </div>
          </List.Item>
        )}
      />

      <style jsx>{`
        .smart-link-suggestions {
          margin-top: 16px;
          border: 1px solid #e8f4fd;
          background: linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%);
        }

        .suggestion-item {
          cursor: pointer;
          transition: all 0.2s ease;
          border-radius: 6px;
          margin-bottom: 4px;
          padding: 8px !important;
        }

        .suggestion-item:hover {
          background: rgba(24, 144, 255, 0.05);
          transform: translateX(4px);
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
        }

        .suggestion-item.suggestion-clicked {
          background: rgba(24, 144, 255, 0.1);
          transform: scale(0.98);
          box-shadow: 0 0 0 2px #1890ff;
        }

        .suggestion-content {
          width: 100%;
        }

        .suggestion-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 4px;
        }

        .suggestion-title {
          color: #1890ff;
          font-size: 13px;
        }

        .suggestion-actions {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .relevance-indicator {
          width: 40px;
          height: 4px;
          background: #f0f0f0;
          border-radius: 2px;
          overflow: hidden;
        }

        .relevance-bar {
          height: 100%;
          background: linear-gradient(90deg, #faad14 0%, #52c41a 100%);
          transition: width 0.3s ease;
        }

        .suggestion-button {
          opacity: 0;
          transition: opacity 0.2s ease;
        }

        .suggestion-item:hover .suggestion-button {
          opacity: 1;
        }

        .suggestion-description {
          margin: 4px 0;
        }

        .suggestion-tags {
          margin: 4px 0;
        }

        .suggestion-reason {
          margin-top: 4px;
          padding-top: 4px;
          border-top: 1px solid #f0f0f0;
        }

        @keyframes clickFeedback {
          0% { transform: scale(1); }
          50% { transform: scale(0.95); }
          100% { transform: scale(1); }
        }

        .suggestion-clicked {
          animation: clickFeedback 0.3s ease;
        }

        @media (max-width: 768px) {
          .suggestion-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 4px;
          }

          .suggestion-actions {
            align-self: flex-end;
          }
        }
      `}</style>
    </Card>
  );
};

export default SmartLinkSuggestions;
