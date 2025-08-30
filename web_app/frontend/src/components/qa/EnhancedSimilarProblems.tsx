import React, { useState } from 'react';
import {
  Card,
  Typography,
  Tag,
  Space,
  Progress,
  Tooltip,
  Row,
  Col,
  Button,
  Collapse,
  Divider
} from 'antd';
import './EnhancedSimilarProblems.css';
import {
  TrophyOutlined,
  ThunderboltOutlined,
  BulbOutlined,
  LinkOutlined,
  StarOutlined,
  LikeOutlined,
  EyeOutlined,
  ExpandAltOutlined
} from '@ant-design/icons';
import { SimilarProblem } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface EnhancedSimilarProblemsProps {
  problems: SimilarProblem[];
  onProblemClick: (title: string) => void;
  maxDisplay?: number;
}

const EnhancedSimilarProblems: React.FC<EnhancedSimilarProblemsProps> = ({
  problems,
  onProblemClick,
  maxDisplay = 6
}) => {
  const [showAll, setShowAll] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // 获取推荐强度图标和颜色
  const getRecommendationLevel = (score: number) => {
    if (score >= 0.8) return { icon: <TrophyOutlined />, color: '#f5222d', level: '强烈推荐', bgColor: '#fff2f0' };
    if (score >= 0.6) return { icon: <LikeOutlined />, color: '#fa8c16', level: '推荐', bgColor: '#fff7e6' };
    if (score >= 0.4) return { icon: <BulbOutlined />, color: '#1890ff', level: '建议', bgColor: '#f0f9ff' };
    return { icon: <StarOutlined />, color: '#52c41a', level: '可选', bgColor: '#f6ffed' };
  };

  // 获取难度颜色
  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case '简单': return 'green';
      case '中等': return 'orange';
      case '困难': return 'red';
      default: return 'default';
    }
  };

  // 渲染网格模式的题目卡片
  const renderGridCard = (problem: SimilarProblem, index: number) => {
    const recommendation = getRecommendationLevel(problem.hybrid_score);
    
    return (
      <Col xs={24} sm={12} lg={8} key={index}>
        <Card
          hoverable
          className="similar-problem-grid-card"
          onClick={() => onProblemClick(problem.title)}
          style={{
            height: '100%',
            borderRadius: '12px',
            border: `2px solid ${recommendation.color}20`,
            background: `linear-gradient(135deg, ${recommendation.bgColor} 0%, white 100%)`,
            transition: 'all 0.3s ease',
            cursor: 'pointer'
          }}
          bodyStyle={{ padding: '16px', height: '100%', display: 'flex', flexDirection: 'column' }}
        >
          {/* 头部：推荐级别和分数 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <Tag
              color={recommendation.color}
              style={{
                fontSize: '10px',
                padding: '2px 6px',
                borderRadius: '9px',
                border: 'none'
              }}
            >
              {recommendation.level}
            </Tag>
            <div style={{ textAlign: 'right' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>相似度</Text>
              <br />
              <Text strong style={{ color: recommendation.color, fontSize: '14px' }}>
                {(problem.hybrid_score * 100).toFixed(0)}%
              </Text>
            </div>
          </div>

          {/* 题目标题 */}
          <Title level={5} style={{ 
            margin: '0 0 8px 0', 
            color: '#1890ff',
            fontSize: '14px',
            lineHeight: '1.4',
            flex: '0 0 auto'
          }}>
            {recommendation.icon}
            <span style={{ marginLeft: '6px' }}>{problem.title}</span>
          </Title>

          {/* 推荐理由 */}
          <Paragraph 
            ellipsis={{ rows: 2 }}
            style={{ 
              fontSize: '12px', 
              color: '#666',
              margin: '0 0 12px 0',
              flex: '1 1 auto'
            }}
          >
            {problem.recommendation_reason}
          </Paragraph>

          {/* 共同标签 */}
          <div style={{ marginBottom: '8px', flex: '0 0 auto' }}>
            <Space size={[4, 4]} wrap>
              {problem.shared_tags.slice(0, 3).map(tag => (
                <Tag key={tag} size="small" color="blue" style={{ fontSize: '10px', margin: '1px' }}>
                  {tag}
                </Tag>
              ))}
              {problem.shared_tags.length > 3 && (
                <Tag size="small" color="default" style={{ fontSize: '10px' }}>
                  +{problem.shared_tags.length - 3}
                </Tag>
              )}
            </Space>
          </div>

          {/* 底部：难度和平台 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flex: '0 0 auto' }}>
            {problem.complete_info?.difficulty && (
              <Tag color={getDifficultyColor(problem.complete_info.difficulty)} size="small">
                {problem.complete_info.difficulty}
              </Tag>
            )}
            {problem.complete_info?.platform && (
              <Tag color="purple" size="small">
                {problem.complete_info.platform}
              </Tag>
            )}
          </div>
        </Card>
      </Col>
    );
  };

  // 渲染列表模式的题目卡片
  const renderListCard = (problem: SimilarProblem, index: number) => {
    const recommendation = getRecommendationLevel(problem.hybrid_score);
    
    return (
      <Card
        key={index}
        hoverable
        className="similar-problem-list-card"
        onClick={() => onProblemClick(problem.title)}
        style={{
          marginBottom: '12px',
          borderRadius: '8px',
          border: `1px solid ${recommendation.color}30`,
          borderLeft: `4px solid ${recommendation.color}`,
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
        bodyStyle={{ padding: '16px' }}
      >
        <Row gutter={16} align="middle">
          {/* 推荐级别和图标 */}
          <Col flex="auto">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ 
                width: '40px', 
                height: '40px', 
                borderRadius: '20px', 
                background: recommendation.bgColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: recommendation.color,
                fontSize: '16px'
              }}>
                {recommendation.icon}
              </div>
              
              <div style={{ flex: 1 }}>
                <Title level={5} style={{ margin: '0 0 4px 0', color: '#1890ff' }}>
                  {problem.title}
                </Title>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {problem.recommendation_reason}
                </Text>
              </div>
            </div>
          </Col>

          {/* 相似度进度条 */}
          <Col flex="120px">
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>相似度</Text>
              <Progress 
                percent={problem.hybrid_score * 100} 
                size="small" 
                strokeColor={recommendation.color}
                showInfo={false}
                style={{ margin: '4px 0' }}
              />
              <Text strong style={{ color: recommendation.color, fontSize: '12px' }}>
                {(problem.hybrid_score * 100).toFixed(0)}%
              </Text>
            </div>
          </Col>

          {/* 标签和难度 */}
          <Col flex="200px">
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Space size={[4, 4]} wrap>
                {problem.shared_tags.slice(0, 2).map(tag => (
                  <Tag key={tag} size="small" color="blue">
                    {tag}
                  </Tag>
                ))}
                {problem.shared_tags.length > 2 && (
                  <Tag size="small" color="default">
                    +{problem.shared_tags.length - 2}
                  </Tag>
                )}
              </Space>
              <Space>
                {problem.complete_info?.difficulty && (
                  <Tag color={getDifficultyColor(problem.complete_info.difficulty)} size="small">
                    {problem.complete_info.difficulty}
                  </Tag>
                )}
                {problem.complete_info?.platform && (
                  <Tag color="purple" size="small">
                    {problem.complete_info.platform}
                  </Tag>
                )}
              </Space>
            </Space>
          </Col>
        </Row>
      </Card>
    );
  };

  const displayedProblems = showAll ? problems : problems.slice(0, maxDisplay);
  const hasMore = problems.length > maxDisplay;

  return (
    <div className="enhanced-similar-problems">
      {/* 头部控制栏 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '16px',
        padding: '12px 16px',
        background: '#fafafa',
        borderRadius: '8px'
      }}>
        <Space>
          <ThunderboltOutlined style={{ color: '#1890ff' }} />
          <Text strong>相似题目推荐</Text>
          <Tag color="blue" style={{ fontSize: '10px' }}>{problems.length}道</Tag>
        </Space>
        
        <Space>
          <Tooltip title={viewMode === 'grid' ? '切换到列表视图' : '切换到网格视图'}>
            <Button 
              type="text" 
              size="small"
              icon={viewMode === 'grid' ? <EyeOutlined /> : <ExpandAltOutlined />}
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            />
          </Tooltip>
          {hasMore && (
            <Button 
              type="link" 
              size="small"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? '收起' : `查看全部 ${problems.length} 道`}
            </Button>
          )}
        </Space>
      </div>

      {/* 题目列表 */}
      {viewMode === 'grid' ? (
        <Row gutter={[16, 16]}>
          {displayedProblems.map((problem, index) => renderGridCard(problem, index))}
        </Row>
      ) : (
        <div>
          {displayedProblems.map((problem, index) => renderListCard(problem, index))}
        </div>
      )}

      {/* 底部统计信息 */}
      {problems.length > 0 && (
        <div style={{ 
          marginTop: '16px', 
          padding: '12px', 
          background: '#f0f9ff', 
          borderRadius: '6px',
          textAlign: 'center'
        }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            <ThunderboltOutlined style={{ marginRight: '4px' }} />
            基于算法标签、难度等级和学习路径智能推荐
          </Text>
        </div>
      )}
    </div>
  );
};

export default EnhancedSimilarProblems;
