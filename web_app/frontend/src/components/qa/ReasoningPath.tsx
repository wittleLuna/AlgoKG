import React from 'react';
import { Steps, Card, Typography, Tag, Spin, Progress } from 'antd';
import { 
  CheckCircleOutlined, 
  LoadingOutlined, 
  ExclamationCircleOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import { ReasoningPathProps, AgentStep } from '../../types';

const { Text, Title } = Typography;
const { Step } = Steps;

const ReasoningPath: React.FC<ReasoningPathProps> = ({ 
  steps, 
  isStreaming = false 
}) => {
  if (!steps || steps.length === 0) {
    return null;
  }

  const getStepIcon = (status: string, isActive: boolean) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'processing':
        return isActive ? <LoadingOutlined spin /> : <ClockCircleOutlined />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  const getStepStatus = (status: string) => {
    switch (status) {
      case 'success':
        return 'finish';
      case 'processing':
        return 'process';
      case 'error':
        return 'error';
      default:
        return 'wait';
    }
  };

  const getCurrentStep = () => {
    const processingIndex = steps.findIndex(step => step.status === 'processing');
    if (processingIndex !== -1) return processingIndex;
    
    const lastFinishedIndex = steps.map(step => step.status).lastIndexOf('success');
    return lastFinishedIndex + 1;
  };

  const getProgressPercent = () => {
    const completedSteps = steps.filter(step => step.status === 'success').length;
    return Math.round((completedSteps / steps.length) * 100);
  };

  return (
    <Card 
      className="reasoning-path-card"
      title={
        <div className="reasoning-header">
          <Title level={5} style={{ margin: 0 }}>
            🧠 AI推理过程
          </Title>
          {isStreaming && (
            <div className="streaming-indicator">
              <Spin size="small" />
              <Text type="secondary" style={{ marginLeft: 8 }}>
                正在思考中...
              </Text>
            </div>
          )}
        </div>
      }
      size="small"
    >
      {/* 进度条 */}
      <div className="progress-section">
        <Progress
          percent={getProgressPercent()}
          status={isStreaming ? 'active' : 'success'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          size="small"
        />
        <Text type="secondary" style={{ fontSize: 12, marginTop: 4 }}>
          {steps.filter(s => s.status === 'success').length} / {steps.length} 步骤完成
        </Text>
      </div>

      {/* 步骤列表 */}
      <Steps
        current={getCurrentStep()}
        direction="vertical"
        size="small"
        className="reasoning-steps"
      >
        {steps.map((step, index) => {
          const isActive = step.status === 'processing';
          const duration = step.end_time && step.start_time 
            ? new Date(step.end_time).getTime() - new Date(step.start_time).getTime()
            : null;

          return (
            <Step
              key={index}
              status={getStepStatus(step.status)}
              icon={getStepIcon(step.status, isActive)}
              title={
                <div className="step-title">
                  <Text strong>{step.description}</Text>
                  <div className="step-meta">
                    <Tag color="blue" size="small">
                      {step.agent_name}
                    </Tag>
                    {step.confidence && (
                      <Tag color="green" size="small">
                        置信度: {(step.confidence * 100).toFixed(1)}%
                      </Tag>
                    )}
                    {duration && (
                      <Tag color="orange" size="small">
                        {duration}ms
                      </Tag>
                    )}
                  </div>
                </div>
              }
              description={
                step.result && (
                  <div className="step-result">
                    {step.step_type === 'analysis' && step.result.entities && (
                      <div>
                        <Text type="secondary">识别实体: </Text>
                        {step.result.entities.map((entity: string, i: number) => (
                          <Tag key={i} size="small" color="purple">
                            {entity}
                          </Tag>
                        ))}
                      </div>
                    )}
                    
                    {step.step_type === 'retrieval' && step.result.count && (
                      <div>
                        <Text type="secondary">
                          检索到 {step.result.count} 条相关信息
                        </Text>
                      </div>
                    )}
                    
                    {step.step_type === 'explanation' && step.result.concepts && (
                      <div>
                        <Text type="secondary">解释概念: </Text>
                        {step.result.concepts.map((concept: string, i: number) => (
                          <Tag key={i} size="small" color="cyan">
                            {concept}
                          </Tag>
                        ))}
                      </div>
                    )}
                    
                    {step.step_type === 'integration' && step.result.sections && (
                      <div>
                        <Text type="secondary">整合内容: </Text>
                        <Text>{step.result.sections.join(', ')}</Text>
                      </div>
                    )}
                  </div>
                )
              }
            />
          );
        })}
      </Steps>

      {/* 实时状态指示器 */}
      {isStreaming && (
        <div className="streaming-status">
          <div className="pulse-dot" />
          <Text type="secondary">AI正在分析您的问题...</Text>
        </div>
      )}

      <style jsx>{`
        .reasoning-path-card {
          background: linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%);
          border: 1px solid #e1e8ed;
          border-radius: 8px;
        }

        .reasoning-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .streaming-indicator {
          display: flex;
          align-items: center;
        }

        .progress-section {
          margin-bottom: 16px;
        }

        .reasoning-steps {
          margin-top: 8px;
        }

        .step-title {
          margin-bottom: 4px;
        }

        .step-meta {
          margin-top: 4px;
          display: flex;
          gap: 4px;
          flex-wrap: wrap;
        }

        .step-result {
          margin-top: 8px;
          padding: 8px;
          background: #fafafa;
          border-radius: 4px;
          font-size: 12px;
        }

        .streaming-status {
          display: flex;
          align-items: center;
          margin-top: 16px;
          padding: 8px;
          background: #f0f9ff;
          border-radius: 4px;
          border-left: 3px solid #1890ff;
        }

        .pulse-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #1890ff;
          margin-right: 8px;
          animation: pulse 1.5s infinite;
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

        @media (max-width: 768px) {
          .reasoning-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }

          .step-meta {
            flex-direction: column;
            gap: 2px;
          }
        }
      `}</style>
    </Card>
  );
};

export default ReasoningPath;
