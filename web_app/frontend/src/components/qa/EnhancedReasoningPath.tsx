import React, { useState, useEffect } from 'react';
import { Card, Timeline, Progress, Tag, Collapse, Typography, Space, Button } from 'antd';
import {
  ThunderboltOutlined,
  SearchOutlined,
  BulbOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons';
import { AgentStep } from '../../types';

const { Text, Title } = Typography;
const { Panel } = Collapse;

interface EnhancedReasoningPathProps {
  steps: AgentStep[];
  isStreaming?: boolean;
  onStepClick?: (step: AgentStep) => void;
}

const EnhancedReasoningPath: React.FC<EnhancedReasoningPathProps> = ({
  steps,
  isStreaming = false,
  onStepClick
}) => {
  const [expandedSteps, setExpandedSteps] = useState<string[]>([]);
  const [showDetails, setShowDetails] = useState(false); // 默认隐藏详情
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false); // 是否完成所有步骤

  // 调试信息
  console.log('EnhancedReasoningPath - steps:', steps);
  console.log('EnhancedReasoningPath - steps length:', steps?.length);
  console.log('EnhancedReasoningPath - isStreaming:', isStreaming);

  // 如果没有步骤数据，显示默认信息
  if (!steps || steps.length === 0) {
    console.log('EnhancedReasoningPath - 没有推理步骤数据');
  }

  // 智能体图标映射
  const getAgentIcon = (agentName: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'analyzer': <ThunderboltOutlined style={{ color: '#1890ff' }} />,
      'knowledge_retriever': <SearchOutlined style={{ color: '#52c41a' }} />,
      'concept_explainer': <BulbOutlined style={{ color: '#faad14' }} />,
      'similar_problem_finder': <LinkOutlined style={{ color: '#722ed1' }} />,
      'integrator': <CheckCircleOutlined style={{ color: '#13c2c2' }} />,
    };
    return iconMap[agentName] || <ThunderboltOutlined style={{ color: '#8c8c8c' }} />;
  };

  // 获取步骤状态颜色
  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      'success': '#52c41a',
      'processing': '#1890ff',
      'error': '#ff4d4f',
      'partial': '#faad14'
    };
    return colorMap[status] || '#8c8c8c';
  };

  // 获取步骤状态图标
  const getStatusIcon = (status: string, isActive: boolean) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'processing':
        return isActive ? <LoadingOutlined spin style={{ color: '#1890ff' }} /> : <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <LoadingOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  // 计算进度
  const getProgress = () => {
    if (steps.length === 0) return 0;
    const completedSteps = steps.filter(step => step.status === 'success').length;
    return Math.round((completedSteps / steps.length) * 100);
  };

  // 获取当前活跃步骤
  const getCurrentStep = () => {
    const processingIndex = steps.findIndex(step => step.status === 'processing');
    if (processingIndex !== -1) return processingIndex;
    
    const lastCompletedIndex = steps.map(step => step.status).lastIndexOf('success');
    return Math.min(lastCompletedIndex + 1, steps.length - 1);
  };

  // 更新当前步骤索引和完成状态
  useEffect(() => {
    setCurrentStepIndex(getCurrentStep());

    // 检查是否所有步骤都已完成
    const allCompleted = steps.length > 0 && steps.every(step => step.status === 'success');
    if (allCompleted && !isCompleted) {
      setIsCompleted(true);
      // 完成后自动显示详情
      setTimeout(() => {
        setShowDetails(true);
      }, 500);
    }
  }, [steps, isCompleted]);

  // 格式化持续时间
  const formatDuration = (startTime: string, endTime?: string) => {
    if (!endTime) return null;
    const duration = new Date(endTime).getTime() - new Date(startTime).getTime();
    return duration < 1000 ? `${duration}ms` : `${(duration / 1000).toFixed(1)}s`;
  };

  // 获取步骤显示名称
  const getStepDisplayName = (agentName: string) => {
    const nameMap: Record<string, string> = {
      'analyzer': '查询分析',
      'knowledge_retriever': '知识检索',
      'concept_explainer': '概念解释',
      'recommender': '题目推荐',
      'similar_problem_finder': '相似题目',
      'integrator': '信息整合',
      'system': '系统处理'
    };
    return nameMap[agentName] || agentName;
  };

  // 渲染步骤详情
  const renderStepDetails = (step: AgentStep) => {
    return (
      <div className="step-details">
        {/* 基本信息 */}
        <div className="step-basic-info">
          <div className="info-row">
            <Text type="secondary">执行时间:</Text>
            <Text>{formatDuration(step.start_time, step.end_time) || '计算中...'}</Text>
          </div>
          {step.confidence && (
            <div className="info-row">
              <Text type="secondary">置信度:</Text>
              <Text strong style={{ color: step.confidence > 0.8 ? '#52c41a' : step.confidence > 0.6 ? '#faad14' : '#ff4d4f' }}>
                {(step.confidence * 100).toFixed(1)}%
              </Text>
            </div>
          )}
        </div>

        {step.result && (
          <div className="step-result">
            {/* 分析结果 */}
            {step.step_type === 'analysis' && (
              <div className="result-section">
                <Text strong>查询分析结果:</Text>
                {step.result.intent && (
                  <div className="analysis-item">
                    <Text type="secondary">意图识别:</Text>
                    <Tag color="blue">{step.result.intent}</Tag>
                  </div>
                )}
                {step.result.entities && step.result.entities.length > 0 && (
                  <div className="analysis-item">
                    <Text type="secondary">关键实体:</Text>
                    <div style={{ marginTop: 4 }}>
                      {step.result.entities.map((entity: string, i: number) => (
                        <Tag key={i} color="purple" size="small">
                          {entity}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}
                {step.result.difficulty && (
                  <div className="analysis-item">
                    <Text type="secondary">难度评估:</Text>
                    <Tag color={
                      step.result.difficulty === '简单' ? 'green' :
                      step.result.difficulty === '中等' ? 'orange' : 'red'
                    }>
                      {step.result.difficulty}
                    </Tag>
                  </div>
                )}
              </div>
            )}

            {/* 检索结果 */}
            {step.step_type === 'retrieval' && (
              <div className="result-section">
                <Text strong>知识检索结果:</Text>
                <div className="retrieval-stats">
                  {step.result.count !== undefined && (
                    <div className="stat-item">
                      <Text type="secondary">检索到:</Text>
                      <Tag color="green" size="small">
                        {step.result.count} 条相关信息
                      </Tag>
                    </div>
                  )}
                  {step.result.sources && (
                    <div className="stat-item">
                      <Text type="secondary">数据源:</Text>
                      <div style={{ marginTop: 4 }}>
                        {Array.isArray(step.result.sources) ?
                          step.result.sources.map((source: string, i: number) => (
                            <Tag key={i} color="blue" size="small">{source}</Tag>
                          )) :
                          <Tag color="blue" size="small">{step.result.sources}</Tag>
                        }
                      </div>
                    </div>
                  )}
                  {step.result.query_expansion && (
                    <div className="stat-item">
                      <Text type="secondary">查询扩展:</Text>
                      <Text italic style={{ fontSize: '12px' }}>{step.result.query_expansion}</Text>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 解释结果 */}
            {step.step_type === 'explanation' && (
              <div className="result-section">
                <Text strong>概念解释结果:</Text>
                <div className="explanation-details">
                  {step.result.concepts && (
                    <div className="explanation-item">
                      <Text type="secondary">解释概念:</Text>
                      <div style={{ marginTop: 4 }}>
                        {step.result.concepts.map((concept: string, i: number) => (
                          <Tag key={i} color="cyan" size="small">
                            {concept}
                          </Tag>
                        ))}
                      </div>
                    </div>
                  )}
                  {step.result.definition_quality && (
                    <div className="explanation-item">
                      <Text type="secondary">定义质量:</Text>
                      <Tag color="green" size="small">{step.result.definition_quality}</Tag>
                    </div>
                  )}
                  {step.result.examples_count && (
                    <div className="explanation-item">
                      <Text type="secondary">示例数量:</Text>
                      <Tag color="orange" size="small">{step.result.examples_count} 个</Tag>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 推荐结果 */}
            {step.step_type === 'recommendation' && (
              <div className="result-section">
                <Text strong>题目推荐结果:</Text>
                <div className="recommendation-details">
                  {step.status === 'error' ? (
                    <div className="recommendation-item">
                      <Text type="secondary">状态:</Text>
                      <Tag color="red" size="small">推荐服务暂时不可用</Tag>
                    </div>
                  ) : step.result?.problems ? (
                    <div className="recommendation-item">
                      <Text type="secondary">推荐题目:</Text>
                      <div style={{ marginTop: 4 }}>
                        {step.result.problems.slice(0, 3).map((problem: string, i: number) => (
                          <Tag key={i} color="orange" size="small">
                            {problem}
                          </Tag>
                        ))}
                        {step.result.problems.length > 3 && (
                          <Tag size="small">+{step.result.problems.length - 3} 更多</Tag>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="recommendation-item">
                      <Text type="secondary">状态:</Text>
                      <Tag color="blue" size="small">推荐生成完成</Tag>
                    </div>
                  )}
                  {step.result?.recommendation_strategy && (
                    <div className="recommendation-item">
                      <Text type="secondary">推荐策略:</Text>
                      <Text italic style={{ fontSize: '12px' }}>{step.result.recommendation_strategy}</Text>
                    </div>
                  )}
                  {step.result?.difficulty_distribution && (
                    <div className="recommendation-item">
                      <Text type="secondary">难度分布:</Text>
                      <Text style={{ fontSize: '12px' }}>{step.result.difficulty_distribution}</Text>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 整合结果 */}
            {step.step_type === 'integration' && (
              <div className="result-section">
                <Text strong>信息整合结果:</Text>
                <div className="integration-details">
                  {step.result.sections && (
                    <div className="integration-item">
                      <Text type="secondary">整合内容:</Text>
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {Array.isArray(step.result.sections) ?
                            step.result.sections.join(' → ') :
                            step.result.sections
                          }
                        </Text>
                      </div>
                    </div>
                  )}
                  {step.result.response_length && (
                    <div className="integration-item">
                      <Text type="secondary">回答长度:</Text>
                      <Tag color="blue" size="small">{step.result.response_length} 字符</Tag>
                    </div>
                  )}
                  {step.result.completeness_score && (
                    <div className="integration-item">
                      <Text type="secondary">完整性评分:</Text>
                      <Tag color="green" size="small">{step.result.completeness_score}</Tag>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 置信度和耗时 */}
        <div className="step-metrics">
          {step.confidence && (
            <div className="metric-item">
              <Text type="secondary">置信度:</Text>
              <Progress
                percent={step.confidence * 100}
                size="small"
                style={{ width: 80, marginLeft: 8 }}
                strokeColor={step.confidence > 0.8 ? '#52c41a' : step.confidence > 0.6 ? '#faad14' : '#ff4d4f'}
              />
            </div>
          )}
          
          {formatDuration(step.start_time, step.end_time) && (
            <div className="metric-item">
              <Text type="secondary">耗时:</Text>
              <Tag size="small" color="default" style={{ marginLeft: 4 }}>
                {formatDuration(step.start_time, step.end_time)}
              </Tag>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (!steps || steps.length === 0) {
    return null;
  }

  // 如果正在流式处理且未完成，显示简洁的加载界面
  if (isStreaming && !isCompleted) {
    return (
      <Card
        className="enhanced-reasoning-path streaming-mode"
        size="small"
        bodyStyle={{ padding: '16px' }}
      >
        <div className="streaming-header">
          <Space>
            <div className="ai-avatar">
              <ThunderboltOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
            </div>
            <div className="streaming-info">
              <Text strong style={{ color: '#1890ff' }}>AI正在思考中...</Text>
              <div className="streaming-progress">
                <div className="progress-dots">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
                <Text type="secondary" style={{ fontSize: '12px', marginLeft: '8px' }}>
                  {getCurrentStep() + 1}/{steps.length} 步骤
                </Text>
              </div>
            </div>
          </Space>
        </div>

        <div className="current-step-preview">
          {steps[getCurrentStep()] && (
            <div className="step-preview">
              <div className="step-icon">
                {getStatusIcon(steps[getCurrentStep()].status, true)}
              </div>
              <div className="step-content">
                <Text className="step-name">
                  {getStepDisplayName(steps[getCurrentStep()].agent_name)}
                </Text>
                <Text type="secondary" className="step-desc">
                  {steps[getCurrentStep()].description}
                </Text>
              </div>
              <div className="step-status">
                {steps[getCurrentStep()].status === 'processing' ? (
                  <LoadingOutlined style={{ color: '#1890ff' }} />
                ) : (
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                )}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  return (
    <Card 
      className="enhanced-reasoning-path"
      title={
        <div className="reasoning-header">
          <Space>
            <ThunderboltOutlined style={{ color: '#1890ff', fontSize: 18 }} />
            <Title level={5} style={{ margin: 0 }}>
              AI推理过程
            </Title>
            {isStreaming && (
              <Tag color="processing" icon={<LoadingOutlined />}>
                思考中
              </Tag>
            )}
          </Space>
          
          <Space>
            <Button
              type="text"
              size="small"
              icon={showDetails ? <EyeInvisibleOutlined /> : <EyeOutlined />}
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? '隐藏详情' : '显示详情'}
            </Button>
          </Space>
        </div>
      }
      size="small"
    >
      {/* 总体进度 */}
      <div className="overall-progress">
        <div className="progress-info">
          <Text strong>推理进度</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {steps.filter(s => s.status === 'success').length} / {steps.length} 步骤完成
          </Text>
        </div>
        <Progress
          percent={getProgress()}
          status={isStreaming ? 'active' : 'success'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          trailColor="#f0f0f0"
        />
      </div>

      {/* 步骤时间线 */}
      <div className="steps-timeline">
        <Timeline mode="left">
          {steps.map((step, index) => {
            const isActive = index === currentStepIndex && step.status === 'processing';
            const isExpanded = expandedSteps.includes(step.agent_name + index);
            
            return (
              <Timeline.Item
                key={index}
                dot={getStatusIcon(step.status, isActive)}
                color={getStatusColor(step.status)}
                className={`timeline-item ${isActive ? 'active' : ''}`}
              >
                <div className="step-content">
                  <div 
                    className="step-header"
                    onClick={() => onStepClick && onStepClick(step)}
                    style={{ cursor: onStepClick ? 'pointer' : 'default' }}
                  >
                    <div className="step-title">
                      <Space>
                        {getAgentIcon(step.agent_name)}
                        <Text strong>{step.description}</Text>
                        {isActive && (
                          <div className="pulse-indicator" />
                        )}
                      </Space>
                    </div>
                    
                    <div className="step-meta">
                      <Tag color="blue" style={{ fontSize: '12px' }}>
                        {step.agent_name}
                      </Tag>
                      <Tag color="default" style={{ fontSize: '12px' }}>
                        {step.step_type}
                      </Tag>
                      {step.confidence && (
                        <Tag
                          color={step.confidence > 0.8 ? 'green' : step.confidence > 0.6 ? 'orange' : 'red'}
                          size="small"
                        >
                          {(step.confidence * 100).toFixed(0)}%
                        </Tag>
                      )}
                      <Tag color="orange" size="small">
                        耗时: {formatDuration(step.start_time, step.end_time) || '0ms'}
                      </Tag>
                    </div>
                  </div>

                  {/* 详细信息 */}
                  {showDetails && (
                    <Collapse 
                      ghost 
                      size="small"
                      activeKey={isExpanded ? ['details'] : []}
                      onChange={(keys) => {
                        const stepKey = step.agent_name + index;
                        if (keys.includes('details')) {
                          setExpandedSteps([...expandedSteps, stepKey]);
                        } else {
                          setExpandedSteps(expandedSteps.filter(k => k !== stepKey));
                        }
                      }}
                    >
                      <Panel header="查看详情" key="details">
                        {renderStepDetails(step)}
                      </Panel>
                    </Collapse>
                  )}
                </div>
              </Timeline.Item>
            );
          })}
        </Timeline>
      </div>

      {/* 实时状态指示器 */}
      {isStreaming && (
        <div className="streaming-indicator">
          <div className="streaming-content">
            <div className="pulse-dot" />
            <Text type="secondary">
              AI正在{steps[currentStepIndex]?.description || '处理您的问题'}...
            </Text>
          </div>
          <div className="streaming-progress">
            <div className="progress-bar" style={{ width: `${getProgress()}%` }} />
          </div>
        </div>
      )}

      <style jsx>{`
        .enhanced-reasoning-path {
          background: linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%);
          border: 1px solid #e1e8ed;
          border-radius: 12px;
          overflow: hidden;
        }

        .reasoning-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .overall-progress {
          margin-bottom: 20px;
          padding: 16px;
          background: rgba(24, 144, 255, 0.05);
          border-radius: 8px;
          border-left: 4px solid #1890ff;
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .steps-timeline {
          margin: 16px 0;
        }

        .timeline-item.active {
          background: rgba(24, 144, 255, 0.05);
          border-radius: 8px;
          padding: 8px;
          margin: -8px;
        }

        .step-content {
          width: 100%;
        }

        .step-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }

        .step-title {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .step-meta {
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
        }

        .pulse-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #1890ff;
          animation: pulse 1.5s infinite;
        }

        .step-details {
          margin-top: 12px;
          padding: 16px;
          background: #fafafa;
          border-radius: 8px;
          border-left: 3px solid #1890ff;
        }

        .step-basic-info {
          margin-bottom: 16px;
          padding-bottom: 12px;
          border-bottom: 1px solid #e8e8e8;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .info-row:last-child {
          margin-bottom: 0;
        }

        .result-section {
          margin-bottom: 16px;
        }

        .result-section:last-child {
          margin-bottom: 0;
        }

        .analysis-item,
        .stat-item,
        .explanation-item,
        .recommendation-item,
        .integration-item {
          margin-bottom: 12px;
          padding: 8px 12px;
          background: white;
          border-radius: 6px;
          border: 1px solid #e8e8e8;
        }

        .analysis-item:last-child,
        .stat-item:last-child,
        .explanation-item:last-child,
        .recommendation-item:last-child,
        .integration-item:last-child {
          margin-bottom: 0;
        }

        .retrieval-stats,
        .explanation-details,
        .recommendation-details,
        .integration-details {
          margin-top: 8px;
        }

        .step-metrics {
          display: flex;
          gap: 16px;
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #f0f0f0;
        }

        .metric-item {
          display: flex;
          align-items: center;
        }

        .streaming-indicator {
          margin-top: 16px;
          padding: 12px;
          background: linear-gradient(90deg, #f0f9ff 0%, #e6f7ff 100%);
          border-radius: 8px;
          border: 1px solid #91d5ff;
        }

        .streaming-content {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
        }

        .pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #1890ff;
          margin-right: 8px;
          animation: pulse 1.5s infinite;
        }

        .streaming-progress {
          height: 2px;
          background: #f0f0f0;
          border-radius: 1px;
          overflow: hidden;
        }

        .progress-bar {
          height: 100%;
          background: linear-gradient(90deg, #1890ff 0%, #52c41a 100%);
          transition: width 0.3s ease;
          animation: shimmer 2s infinite;
        }

        @keyframes pulse {
          0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.7);
          }
          
          70% {
            transform: scale(1);
            box-shadow: 0 0 0 10px rgba(24, 144, 255, 0);
          }
          
          100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(24, 144, 255, 0);
          }
        }

        @keyframes shimmer {
          0% {
            background-position: -200px 0;
          }
          100% {
            background-position: calc(200px + 100%) 0;
          }
        }

        /* 流式模式样式 */
        .streaming-mode {
          border: 1px solid #e6f7ff;
          background: linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%);
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
        }

        .streaming-header {
          margin-bottom: 16px;
        }

        .ai-avatar {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }

        .streaming-info {
          flex: 1;
        }

        .streaming-progress {
          display: flex;
          align-items: center;
          margin-top: 4px;
        }

        .progress-dots {
          display: flex;
          gap: 4px;
        }

        .progress-dots .dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #1890ff;
          animation: dotPulse 1.5s infinite ease-in-out;
        }

        .progress-dots .dot:nth-child(2) {
          animation-delay: 0.2s;
        }

        .progress-dots .dot:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes dotPulse {
          0%, 60%, 100% {
            opacity: 0.3;
            transform: scale(0.8);
          }
          30% {
            opacity: 1;
            transform: scale(1);
          }
        }

        .current-step-preview {
          background: rgba(24, 144, 255, 0.05);
          border-radius: 8px;
          padding: 12px;
          border-left: 3px solid #1890ff;
        }

        .step-preview {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .step-icon {
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: rgba(24, 144, 255, 0.1);
        }

        .step-content {
          flex: 1;
        }

        .step-name {
          display: block;
          font-weight: 500;
          color: #1890ff;
          margin-bottom: 2px;
        }

        .step-desc {
          display: block;
          font-size: 12px;
          line-height: 1.4;
        }

        .step-status {
          display: flex;
          align-items: center;
        }

        @media (max-width: 768px) {
          .reasoning-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }

          .step-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }

          .step-meta {
            width: 100%;
          }

          .step-metrics {
            flex-direction: column;
            gap: 8px;
          }
        }
      `}</style>
    </Card>
  );
};

export default EnhancedReasoningPath;
