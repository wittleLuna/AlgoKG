import React, { useState, useEffect } from 'react';
import { Card, Typography, Space, Tag, Button, Empty, Spin, Rate, Progress, Tooltip } from 'antd';
import { 
  RobotOutlined, 
  BulbOutlined,
  ThunderboltOutlined,
  LinkOutlined,
  StarOutlined,
  TrophyOutlined,
  ReloadOutlined,
  RightOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';

const { Title, Text, Paragraph } = Typography;

interface SimilarProblem {
  title: string;
  hybrid_score: number;
  embedding_score: number;
  tag_score: number;
  shared_tags: string[];
  learning_path: string;
  recommendation_reason: string;
  learning_path_explanation: string;
  recommendation_strength: string;
  complete_info?: any;
}

interface SmartRecommendationSystemProps {
  similarProblems: SimilarProblem[];
  isLoading: boolean;
  onProblemClick?: (problem: SimilarProblem) => void;
  onRefresh?: () => void;
  fallbackRecommendations?: string[];
}

const StyledCard = styled(Card)`
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
  overflow: hidden;
  
  .ant-card-head {
    background: linear-gradient(135deg, #13c2c2 0%, #52c41a 100%);
    border-bottom: none;
    
    .ant-card-head-title {
      color: white;
      font-weight: 600;
    }
  }
`;

const RecommendationCard = styled(motion.div)`
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin: 12px 0;
  border: 1px solid #e8e8e8;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border-color: #1890ff;
  }
`;

const ScoreContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 12px 0;
  padding: 12px;
  background: #f6f8fa;
  border-radius: 8px;
`;

const ScoreItem = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
`;

const FallbackContainer = styled.div`
  background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
  border-radius: 12px;
  padding: 20px;
  margin: 16px 0;
  color: white;
`;

const getScoreColor = (score: number) => {
  if (score >= 0.8) return '#52c41a';
  if (score >= 0.6) return '#faad14';
  if (score >= 0.4) return '#ff7a45';
  return '#ff4d4f';
};

const getRecommendationStrengthIcon = (strength: string) => {
  switch (strength.toLowerCase()) {
    case 'strong':
    case '强':
      return <TrophyOutlined style={{ color: '#faad14' }} />;
    case 'medium':
    case '中':
      return <StarOutlined style={{ color: '#1890ff' }} />;
    default:
      return <ReloadOutlined style={{ color: '#52c41a' }} />;
  }
};

const SmartRecommendationSystem: React.FC<SmartRecommendationSystemProps> = ({
  similarProblems,
  isLoading,
  onProblemClick,
  onRefresh,
  fallbackRecommendations = []
}) => {
  const [displayedProblems, setDisplayedProblems] = useState<SimilarProblem[]>([]);
  const [showFallback, setShowFallback] = useState(false);

  useEffect(() => {
    if (similarProblems.length > 0) {
      setDisplayedProblems(similarProblems);
      setShowFallback(false);
    } else if (!isLoading && fallbackRecommendations.length > 0) {
      setShowFallback(true);
    }
  }, [similarProblems, isLoading, fallbackRecommendations]);

  const renderScoreBreakdown = (problem: SimilarProblem) => (
    <ScoreContainer>
      <ScoreItem>
        <Text style={{ fontSize: '12px', color: '#666' }}>综合得分</Text>
        <div style={{ display: 'flex', alignItems: 'center', marginTop: 4 }}>
          <Progress
            type="circle"
            size={40}
            percent={Math.min(Math.round(problem.hybrid_score * 100), 100)}
            strokeColor={getScoreColor(problem.hybrid_score)}
            format={() => (
              <Text style={{ fontSize: '10px', fontWeight: 'bold' }}>
                {Math.min(Math.round(problem.hybrid_score * 100), 100)}
              </Text>
            )}
          />
        </div>
      </ScoreItem>
      
      <ScoreItem>
        <Text style={{ fontSize: '12px', color: '#666' }}>语义相似度</Text>
        <div style={{ marginTop: 4 }}>
          <Progress
            percent={Math.min(Math.round(problem.embedding_score * 100), 100)}
            size="small"
            strokeColor="#722ed1"
            showInfo={false}
          />
          <Text style={{ fontSize: '11px', color: '#722ed1' }}>
            {Math.min(Math.round(problem.embedding_score * 100), 100)}%
          </Text>
        </div>
      </ScoreItem>
      
      <ScoreItem>
        <Text style={{ fontSize: '12px', color: '#666' }}>标签匹配度</Text>
        <div style={{ marginTop: 4 }}>
          <Progress
            percent={Math.min(Math.round(problem.tag_score * 100), 100)}
            size="small"
            strokeColor="#13c2c2"
            showInfo={false}
          />
          <Text style={{ fontSize: '11px', color: '#13c2c2' }}>
            {Math.min(Math.round(problem.tag_score * 100), 100)}%
          </Text>
        </div>
      </ScoreItem>
    </ScoreContainer>
  );

  const renderRecommendationCard = (problem: SimilarProblem, index: number) => (
    <RecommendationCard
      key={`${problem.title}-${index}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      onClick={() => onProblemClick?.(problem)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div style={{ flex: 1 }}>
          <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
            {getRecommendationStrengthIcon(problem.recommendation_strength)}
            <span style={{ marginLeft: 8 }}>{problem.title}</span>
          </Title>
          
          <Space wrap style={{ marginBottom: 8 }}>
            <Tag icon={<RobotOutlined />} color="blue">
              训练模型推荐
            </Tag>
            <Tag color={getScoreColor(problem.hybrid_score)}>
              {problem.recommendation_strength} 推荐
            </Tag>
          </Space>
        </div>
        
        <Tooltip title="查看详情">
          <Button type="text" icon={<RightOutlined />} />
        </Tooltip>
      </div>

      {renderScoreBreakdown(problem)}

      <div style={{ marginBottom: 12 }}>
        <Text strong style={{ fontSize: '13px', color: '#666' }}>推荐理由:</Text>
        <Paragraph style={{ margin: '4px 0', fontSize: '14px', lineHeight: '1.5' }}>
          {problem.recommendation_reason}
        </Paragraph>
      </div>

      <div style={{ marginBottom: 12 }}>
        <Text strong style={{ fontSize: '13px', color: '#666' }}>学习路径:</Text>
        <Paragraph style={{ margin: '4px 0', fontSize: '14px', lineHeight: '1.5' }}>
          {problem.learning_path_explanation || problem.learning_path}
        </Paragraph>
      </div>

      {problem.shared_tags.length > 0 && (
        <div>
          <Text strong style={{ fontSize: '13px', color: '#666' }}>共同标签:</Text>
          <div style={{ marginTop: 4 }}>
            {problem.shared_tags.map(tag => (
              <Tag key={tag} size="small" style={{ margin: '2px' }}>
                {tag}
              </Tag>
            ))}
          </div>
        </div>
      )}
    </RecommendationCard>
  );

  const renderFallbackRecommendations = () => (
    <FallbackContainer>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
        <BulbOutlined style={{ fontSize: '20px', marginRight: 8 }} />
        <Title level={5} style={{ color: 'white', margin: 0 }}>
          LLM 智能推荐
        </Title>
      </div>
      
      <Text style={{ color: 'white', marginBottom: 16, display: 'block' }}>
        训练模型暂未找到相似题目，但基于LLM分析为您推荐以下相关内容：
      </Text>
      
      <div>
        {fallbackRecommendations.map((recommendation, index) => (
          <div key={index} style={{ 
            background: 'rgba(255,255,255,0.2)', 
            padding: '12px', 
            borderRadius: '8px', 
            marginBottom: '8px' 
          }}>
            <Text style={{ color: 'white' }}>
              {index + 1}. {recommendation}
            </Text>
          </div>
        ))}
      </div>
    </FallbackContainer>
  );

  const renderEmptyState = () => (
    <Empty
      image={null}
      description={
        <div>
          <Text type="secondary">暂无相似题目推荐</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            尝试刷新或使用不同的查询条件
          </Text>
        </div>
      }
    >
      <Button type="primary" icon={<ReloadOutlined />} onClick={onRefresh}>
        重新推荐
      </Button>
    </Empty>
  );

  return (
    <StyledCard
      title={
        <Space>
          <ThunderboltOutlined />
          智能推荐系统
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="推荐算法基于深度学习模型和知识图谱">
            <InfoCircleOutlined style={{ color: 'white' }} />
          </Tooltip>
          <Button 
            type="text" 
            icon={<ReloadOutlined />} 
            onClick={onRefresh}
            style={{ color: 'white' }}
            size="small"
          >
            刷新
          </Button>
        </Space>
      }
    >
      <Spin spinning={isLoading}>
        <AnimatePresence mode="wait">
          {displayedProblems.length > 0 ? (
            <motion.div
              key="recommendations"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <LinkOutlined style={{ color: '#1890ff' }} />
                  <Text strong>找到 {displayedProblems.length} 个相似题目</Text>
                </Space>
              </div>
              
              {displayedProblems.map((problem, index) => 
                renderRecommendationCard(problem, index)
              )}
            </motion.div>
          ) : showFallback ? (
            <motion.div
              key="fallback"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {renderFallbackRecommendations()}
            </motion.div>
          ) : !isLoading ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {renderEmptyState()}
            </motion.div>
          ) : null}
        </AnimatePresence>
      </Spin>
    </StyledCard>
  );
};

export default SmartRecommendationSystem;
