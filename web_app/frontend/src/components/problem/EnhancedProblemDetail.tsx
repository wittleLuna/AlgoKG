import React, { useState } from 'react';
import { Card, Typography, Space, Tag, Button, Tabs, Collapse, Timeline, Divider } from 'antd';
import { 
  CodeOutlined, 
  BulbOutlined, 
  ReloadOutlined,
  ThunderboltOutlined,
  PlayCircleOutlined,
  CopyOutlined,
  DownloadOutlined,
  StarOutlined as ShareOutlined,
  UserOutlined,
  StarOutlined
} from '@ant-design/icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;

interface CodeSnippet {
  language: string;
  code: string;
  description: string;
}

interface KeyInsight {
  content: string;
}

interface StepExplanation {
  name: string;
  text: string;
  code_snippets: CodeSnippet[];
  subsections?: any[];
}

interface ProblemData {
  id: string;
  title: string;
  description: string;
  platform: string;
  url: string;
  algorithm_tags: string[];
  data_structure_tags: string[];
  technique_tags: string[];
  difficulty?: string;
  solution_approach: string;
  key_insights: KeyInsight[];
  step_by_step_explanation: StepExplanation[];
}

interface EnhancedProblemDetailProps {
  problemData: ProblemData;
  onTagClick?: (tag: string, type: string) => void;
  onSimilarProblems?: () => void;
}

const StyledCard = styled(Card)`
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
  overflow: hidden;
  
  .ant-card-head {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-bottom: none;
    
    .ant-card-head-title {
      color: white;
      font-weight: 600;
    }
  }
`;

const TagContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
`;

const CodeContainer = styled.div`
  border-radius: 12px;
  overflow: hidden;
  margin: 16px 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const InsightCard = styled(motion.div)`
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 12px;
  padding: 16px;
  margin: 8px 0;
  color: white;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(240, 147, 251, 0.3);
  }
`;

const StepCard = styled(Card)`
  margin: 16px 0;
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  
  .ant-card-head {
    background: #fafafa;
    border-bottom: 1px solid #e8e8e8;
  }
`;

const getDifficultyColor = (difficulty?: string) => {
  switch (difficulty?.toLowerCase()) {
    case '简单':
    case 'easy':
      return '#52c41a';
    case '中等':
    case 'medium':
      return '#faad14';
    case '困难':
    case 'hard':
      return '#ff4d4f';
    default:
      return '#d9d9d9';
  }
};

const getTagColor = (type: string) => {
  const colorMap: Record<string, string> = {
    algorithm: '#722ed1',
    data_structure: '#13c2c2',
    technique: '#eb2f96',
  };
  return colorMap[type] || '#1890ff';
};

const EnhancedProblemDetail: React.FC<EnhancedProblemDetailProps> = ({
  problemData,
  onTagClick,
  onSimilarProblems
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedInsights, setExpandedInsights] = useState<number[]>([]);

  const toggleInsight = (index: number) => {
    setExpandedInsights(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const copyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    // 可以添加成功提示
  };

  const renderCodeSnippet = (snippet: CodeSnippet, index: number) => (
    <CodeContainer key={index}>
      <div style={{ 
        background: '#1e1e1e', 
        padding: '12px 16px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <Space>
          <Tag color="blue">{snippet.language.toUpperCase()}</Tag>
          <Text style={{ color: '#fff', fontSize: '12px' }}>
            {snippet.description}
          </Text>
        </Space>
        <Button
          type="text"
          icon={<CopyOutlined />}
          onClick={() => copyCode(snippet.code)}
          style={{ color: '#fff' }}
          size="small"
        />
      </div>
      <SyntaxHighlighter
        language={snippet.language}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: '13px',
          lineHeight: '1.5',
        }}
      >
        {snippet.code}
      </SyntaxHighlighter>
    </CodeContainer>
  );

  const renderOverview = () => (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3}>{problemData.title}</Title>
        <Space wrap style={{ marginBottom: 16 }}>
          <Tag color="blue">{problemData.platform}</Tag>
          {problemData.difficulty && (
            <Tag color={getDifficultyColor(problemData.difficulty)}>
              {problemData.difficulty}
            </Tag>
          )}
          <Button type="link" href={problemData.url} target="_blank" size="small">
            查看原题 →
          </Button>
        </Space>
      </div>

      <Paragraph style={{ fontSize: '16px', lineHeight: '1.6' }}>
        {problemData.description}
      </Paragraph>

      <Divider />

      <div>
        <Title level={4}>🎯 解题思路</Title>
        <Paragraph style={{ fontSize: '15px', lineHeight: '1.6', background: '#f6f8fa', padding: '16px', borderRadius: '8px' }}>
          {problemData.solution_approach}
        </Paragraph>
      </div>

      <TagContainer>
        <div>
          <Text strong style={{ marginRight: 8 }}>算法标签:</Text>
          {problemData.algorithm_tags.map(tag => (
            <Tag
              key={tag}
              color={getTagColor('algorithm')}
              style={{ cursor: 'pointer' }}
              onClick={() => onTagClick?.(tag, 'algorithm')}
            >
              {tag}
            </Tag>
          ))}
        </div>
        <div>
          <Text strong style={{ marginRight: 8 }}>数据结构:</Text>
          {problemData.data_structure_tags.map(tag => (
            <Tag
              key={tag}
              color={getTagColor('data_structure')}
              style={{ cursor: 'pointer' }}
              onClick={() => onTagClick?.(tag, 'data_structure')}
            >
              {tag}
            </Tag>
          ))}
        </div>
        <div>
          <Text strong style={{ marginRight: 8 }}>技巧:</Text>
          {problemData.technique_tags.map(tag => (
            <Tag
              key={tag}
              color={getTagColor('technique')}
              style={{ cursor: 'pointer' }}
              onClick={() => onTagClick?.(tag, 'technique')}
            >
              {tag}
            </Tag>
          ))}
        </div>
      </TagContainer>
    </div>
  );

  const renderInsights = () => (
    <div>
      <Title level={4}>💡 关键洞察</Title>
      {problemData.key_insights.map((insight, index) => (
        <InsightCard
          key={index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          onClick={() => toggleInsight(index)}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start' }}>
            <BulbOutlined style={{ marginRight: 12, marginTop: 4, fontSize: '16px' }} />
            <Text style={{ color: 'white', lineHeight: '1.6' }}>
              {insight.content}
            </Text>
          </div>
        </InsightCard>
      ))}
    </div>
  );

  const renderStepByStep = () => (
    <div>
      <Title level={4}>📚 详细解析</Title>
      <Timeline>
        {problemData.step_by_step_explanation.map((step, index) => (
          <Timeline.Item
            key={index}
            dot={<ThunderboltOutlined style={{ fontSize: '16px' }} />}
          >
            <StepCard
              title={`${index + 1}. ${step.name}`}
              size="small"
            >
              <Paragraph style={{ marginBottom: 16 }}>
                {step.text}
              </Paragraph>
              
              {step.code_snippets.map((snippet, snippetIndex) => 
                renderCodeSnippet(snippet, snippetIndex)
              )}
            </StepCard>
          </Timeline.Item>
        ))}
      </Timeline>
    </div>
  );

  return (
    <StyledCard
      title={
        <Space>
          <CodeOutlined />
          题目详解
        </Space>
      }
      extra={
        <Space>
          <Button icon={<UserOutlined />} type="text" style={{ color: 'white' }}>
            收藏
          </Button>
          <Button icon={<ShareOutlined />} type="text" style={{ color: 'white' }}>
            分享
          </Button>
        </Space>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane
          tab={
            <span>
              <ReloadOutlined />
              题目概览
            </span>
          }
          key="overview"
        >
          {renderOverview()}
        </TabPane>
        
        <TabPane
          tab={
            <span>
              <BulbOutlined />
              关键洞察
            </span>
          }
          key="insights"
        >
          {renderInsights()}
        </TabPane>
        
        <TabPane
          tab={
            <span>
              <ThunderboltOutlined />
              详细解析
            </span>
          }
          key="steps"
        >
          {renderStepByStep()}
        </TabPane>
      </Tabs>
      
      <div style={{ marginTop: 24, textAlign: 'center' }}>
        <Button
          type="primary"
          size="large"
          onClick={onSimilarProblems}
          style={{ borderRadius: '8px' }}
        >
          查看相似题目 →
        </Button>
      </div>
    </StyledCard>
  );
};

export default EnhancedProblemDetail;
