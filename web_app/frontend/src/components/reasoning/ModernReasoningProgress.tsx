import React, { useState, useEffect } from 'react';
import { Card, Progress, Typography, Space, Tag, Button, Collapse, Timeline } from 'antd';
import { 
  CheckCircleOutlined, 
  LoadingOutlined, 
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  LinkOutlined,
  BulbOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';

const { Text, Title } = Typography;
const { Panel } = Collapse;

interface ReasoningStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  duration?: number;
  startTime?: number;
  endTime?: number;
  data_source?: string;
  output_summary?: string;
  quality_score?: number;
  details?: any;
  agent_name?: string;
}

interface ModernReasoningProgressProps {
  steps: ReasoningStep[];
  currentStep: number;
  isComplete: boolean;
  onStepClick?: (stepIndex: number) => void;
  onPause?: () => void;
  onResume?: () => void;
  isPaused?: boolean;
}

const StyledCard = styled(Card)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(102, 126, 234, 0.1);
  overflow: hidden;
  
  .ant-card-body {
    padding: 24px;
  }
`;

const StepCard = styled(motion.div)<{ status: string; isActive: boolean }>`
  background: ${props => {
    if (props.status === 'completed') return 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    if (props.status === 'running') return 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)';
    if (props.status === 'error') return 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)';
    return 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)';
  }};
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: ${props => props.isActive ? '2px solid #667eea' : '1px solid rgba(255,255,255,0.2)'};
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
  }
`;

const ProgressContainer = styled.div`
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  backdrop-filter: blur(10px);
`;

const getStepIcon = (step: ReasoningStep) => {
  const iconMap: Record<string, React.ReactNode> = {
    'analyzer': <SearchOutlined />,
    'concept_explainer': <BulbOutlined />,
    'knowledge_retriever': <LinkOutlined />,
    'hybrid_recommender': <BulbOutlined />,
    'similar_problem_finder': <ThunderboltOutlined />,
  };
  
  const agentType = step.agent_name?.toLowerCase() || '';
  for (const [key, icon] of Object.entries(iconMap)) {
    if (agentType.includes(key)) {
      return icon;
    }
  }
  
  return <InfoCircleOutlined />;
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    case 'running':
      return <LoadingOutlined style={{ color: '#1890ff' }} />;
    case 'error':
      return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
    default:
      return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
  }
};

const getDataSourceColor = (source: string) => {
  const colorMap: Record<string, string> = {
    '训练模型': '#722ed1',
    '知识图谱': '#13c2c2',
    'LLM生成': '#eb2f96',
    '混合来源': '#52c41a',
    '训练模型 + 知识图谱': '#1890ff',
    '知识图谱 + LLM生成': '#fa8c16',
  };
  return colorMap[source] || '#d9d9d9';
};

const ModernReasoningProgress: React.FC<ModernReasoningProgressProps> = ({
  steps,
  currentStep,
  isComplete,
  onStepClick,
  onPause,
  onResume,
  isPaused = false
}) => {
  const [expandedSteps, setExpandedSteps] = useState<string[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);

  useEffect(() => {
    const completedSteps = steps.filter(step => step.status === 'completed').length;
    const progress = isComplete ? 100 : (completedSteps / steps.length) * 100;
    setOverallProgress(progress);
  }, [steps, isComplete]);

  const formatDuration = (duration?: number) => {
    if (!duration) return '0ms';
    if (duration < 1000) return `${Math.round(duration)}ms`;
    return `${(duration / 1000).toFixed(1)}s`;
  };

  const getQualityColor = (score?: number) => {
    if (!score) return '#d9d9d9';
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#faad14';
    return '#ff4d4f';
  };

  const toggleStepExpansion = (stepId: string) => {
    setExpandedSteps(prev => 
      prev.includes(stepId) 
        ? prev.filter(id => id !== stepId)
        : [...prev, stepId]
    );
  };

  return (
    <StyledCard>
      <div style={{ color: 'white' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <Title level={4} style={{ color: 'white', margin: 0 }}>
            🧠 智能推理进度
          </Title>
          <Space>
            {!isComplete && (
              <Button
                type="text"
                icon={isPaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
                onClick={isPaused ? onResume : onPause}
                style={{ color: 'white' }}
              >
                {isPaused ? '继续' : '暂停'}
              </Button>
            )}
            <Tag color={isComplete ? 'success' : 'processing'}>
              {isComplete ? '推理完成' : `${currentStep + 1}/${steps.length} 进行中`}
            </Tag>
          </Space>
        </div>

        <ProgressContainer>
          <Progress
            percent={overallProgress}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            trailColor="rgba(255,255,255,0.2)"
            strokeWidth={8}
            showInfo={false}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
            <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
              总体进度: {Math.round(overallProgress)}%
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
              {steps.filter(s => s.status === 'completed').length} / {steps.length} 步骤完成
            </Text>
          </div>
        </ProgressContainer>

        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <AnimatePresence>
            {steps.map((step, index) => (
              <StepCard
                key={step.id}
                status={step.status}
                isActive={index === currentStep}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                onClick={() => {
                  onStepClick?.(index);
                  toggleStepExpansion(step.id);
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                      <Space>
                        {getStepIcon(step)}
                        {getStatusIcon(step.status)}
                        <Text strong style={{ color: 'white' }}>
                          {step.name}
                        </Text>
                      </Space>
                    </div>
                    
                    <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                      {step.description}
                    </Text>
                    
                    {step.status === 'running' && (
                      <div style={{ marginTop: 8 }}>
                        <Progress
                          percent={step.progress}
                          size="small"
                          strokeColor="#fff"
                          trailColor="rgba(255,255,255,0.3)"
                        />
                      </div>
                    )}
                  </div>
                  
                  <div style={{ textAlign: 'right', marginLeft: 16 }}>
                    <Space direction="vertical" size="small">
                      {step.data_source && (
                        <Tag 
                          color={getDataSourceColor(step.data_source)}
                          style={{ margin: 0, fontSize: '10px' }}
                        >
                          {step.data_source}
                        </Tag>
                      )}
                      {step.duration && (
                        <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '11px' }}>
                          {formatDuration(step.duration)}
                        </Text>
                      )}
                      {step.quality_score && (
                        <div style={{ display: 'flex', alignItems: 'center' }}>
                          <div 
                            style={{ 
                              width: 8, 
                              height: 8, 
                              borderRadius: '50%', 
                              backgroundColor: getQualityColor(step.quality_score),
                              marginRight: 4
                            }} 
                          />
                          <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '10px' }}>
                            {Math.round(step.quality_score * 100)}%
                          </Text>
                        </div>
                      )}
                    </Space>
                  </div>
                </div>
                
                {expandedSteps.includes(step.id) && step.output_summary && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    style={{ 
                      marginTop: 12, 
                      paddingTop: 12, 
                      borderTop: '1px solid rgba(255,255,255,0.2)' 
                    }}
                  >
                    <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                      📊 输出摘要: {step.output_summary}
                    </Text>
                  </motion.div>
                )}
              </StepCard>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </StyledCard>
  );
};

export default ModernReasoningProgress;
