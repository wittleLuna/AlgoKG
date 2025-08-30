import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Tag,
  Space,
  Button,
  Spin,
  Alert,
  Divider,
  List,
  Tooltip
} from 'antd';
import {
  InfoCircleOutlined,
  CodeOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  CloseOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { GraphNode } from '../../types';

const { Title, Text, Paragraph } = Typography;

interface NodeDetailPanelProps {
  node: GraphNode | null;
  onClose: () => void;
  visible: boolean;
}

interface NodeDetailInfo {
  basic_info: {
    title: string;
    type: string;
    description?: string;
    difficulty?: string;
    platform?: string;
    category?: string;
  };
  algorithms?: Array<{
    name: string;
    description?: string;
  }>;
  data_structures?: Array<{
    name: string;
    description?: string;
  }>;
  techniques?: Array<{
    name: string;
    description?: string;
  }>;
  solutions?: Array<{
    language: string;
    code: string;
  }>;
  related_problems?: Array<{
    title: string;
    difficulty?: string;
    similarity_score?: number;
  }>;
  insights?: Array<{
    content: string;
    type?: string;
  }>;
  complexity?: {
    time: string;
    space: string;
  };
}

const NodeDetailPanel: React.FC<NodeDetailPanelProps> = ({
  node,
  onClose,
  visible
}) => {
  const [loading, setLoading] = useState(false);
  const [detailInfo, setDetailInfo] = useState<NodeDetailInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  // 获取节点详细信息
  const fetchNodeDetail = async (nodeLabel: string, nodeType: string) => {
    setLoading(true);
    setError(null);

    try {
      let url: string;

      if (nodeType === 'Problem') {
        url = `/api/graph/problem/${encodeURIComponent(nodeLabel)}/detail`;
      } else if (nodeType === 'Algorithm') {
        url = `/api/graph/algorithm/${encodeURIComponent(nodeLabel)}/detail`;
      } else if (nodeType === 'DataStructure') {
        url = `/api/graph/datastructure/${encodeURIComponent(nodeLabel)}/detail`;
      } else {
        url = `/api/graph/node/${encodeURIComponent(nodeLabel)}/detail?type=${nodeType}`;
      }

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setDetailInfo(data);
    } catch (err: any) {
      console.error('获取节点详情失败:', err);
      setError(err.message || '获取节点详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 当节点改变时获取详细信息
  useEffect(() => {
    if (node && visible) {
      fetchNodeDetail(node.label, node.type);
    }
  }, [node, visible]);

  // 获取节点类型图标
  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'Problem':
        return <CodeOutlined />;
      case 'Algorithm':
        return <ThunderboltOutlined />;
      case 'DataStructure':
        return <InfoCircleOutlined />;
      case 'Technique':
        return <BulbOutlined />;
      default:
        return <InfoCircleOutlined />;
    }
  };

  // 获取难度颜色
  const getDifficultyColor = (difficulty?: string) => {
    switch (difficulty) {
      case '简单':
        return 'green';
      case '中等':
        return 'orange';
      case '困难':
        return 'red';
      default:
        return 'default';
    }
  };

  // 渲染基本信息
  const renderBasicInfo = () => {
    if (!detailInfo?.basic_info) return null;

    const { basic_info } = detailInfo;

    return (
      <Card size="small" title="基本信息" style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 12 }}>
          <Space>
            {getNodeIcon(basic_info.type)}
            <Text strong>{basic_info.title}</Text>
            <Tag color="blue">{basic_info.type}</Tag>
          </Space>
        </div>

        {basic_info.difficulty && (
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">难度：</Text>
            <Tag color={getDifficultyColor(basic_info.difficulty)}>
              {basic_info.difficulty}
            </Tag>
          </div>
        )}

        {basic_info.platform && (
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">平台：</Text>
            <Tag>{basic_info.platform}</Tag>
          </div>
        )}

        {basic_info.category && (
          <div style={{ marginBottom: 8 }}>
            <Text type="secondary">分类：</Text>
            <Tag color="purple">{basic_info.category}</Tag>
          </div>
        )}

        {basic_info.description && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <div>
              <Text type="secondary">描述：</Text>
              <div style={{ marginTop: 4 }}>
                {basic_info.description}
              </div>
            </div>
          </>
        )}
      </Card>
    );
  };

  // 渲染相关概念列表
  const renderConceptList = (
    title: string, 
    items: Array<{name: string; description?: string}> | undefined,
    icon: React.ReactNode
  ) => {
    if (!items || items.length === 0) return null;

    return (
      <Card size="small" title={<Space>{icon} {title}</Space>} style={{ marginBottom: 16 }}>
        <List
          size="small"
          dataSource={items}
          renderItem={(item) => (
            <List.Item>
              <div>
                <Text strong>{item.name}</Text>
                {item.description && (
                  <div style={{ marginTop: 4 }}>
                    <Text type="secondary">{item.description}</Text>
                  </div>
                )}
              </div>
            </List.Item>
          )}
        />
      </Card>
    );
  };

  // 渲染相关题目
  const renderRelatedProblems = () => {
    if (!detailInfo?.related_problems || detailInfo.related_problems.length === 0) return null;

    return (
      <Card size="small" title={<Space><CodeOutlined /> 相关题目</Space>} style={{ marginBottom: 16 }}>
        <List
          size="small"
          dataSource={detailInfo.related_problems}
          renderItem={(problem) => (
            <List.Item>
              <div>
                <Space>
                  <Text strong>{problem.title}</Text>
                  {problem.difficulty && (
                    <Tag size="small" color={getDifficultyColor(problem.difficulty)}>
                      {problem.difficulty}
                    </Tag>
                  )}
                  {problem.similarity_score && (
                    <Tag color="green">
                      {Math.round(problem.similarity_score * 100)}%
                    </Tag>
                  )}
                </Space>
              </div>
            </List.Item>
          )}
        />
      </Card>
    );
  };

  // 渲染复杂度信息
  const renderComplexity = () => {
    if (!detailInfo?.complexity) return null;

    return (
      <Card size="small" title="复杂度分析" style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">时间复杂度：</Text>
          <Tag color="blue">{detailInfo.complexity.time}</Tag>
        </div>
        <div>
          <Text type="secondary">空间复杂度：</Text>
          <Tag color="green">{detailInfo.complexity.space}</Tag>
        </div>
      </Card>
    );
  };

  if (!visible || !node) {
    return null;
  }

  return (
    <Card
      title={
        <Space>
          {getNodeIcon(node.type)}
          <Text strong>{node.label}</Text>
          <Tag color="blue">{node.type}</Tag>
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="刷新">
            <Button 
              icon={<ReloadOutlined />} 
              size="small" 
              onClick={() => node && fetchNodeDetail(node.label, node.type)}
            />
          </Tooltip>
          <Tooltip title="关闭">
            <Button icon={<CloseOutlined />} size="small" onClick={onClose} />
          </Tooltip>
        </Space>
      }
      style={{ height: '100%', overflow: 'auto' }}
    >
      {loading && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在加载节点详情...</Text>
          </div>
        </div>
      )}

      {error && (
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => node && fetchNodeDetail(node.label, node.type)}>
              重试
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      {!loading && !error && detailInfo && (
        <div>
          {renderBasicInfo()}
          {renderConceptList('相关算法', detailInfo.algorithms, <ThunderboltOutlined />)}
          {renderConceptList('数据结构', detailInfo.data_structures, <InfoCircleOutlined />)}
          {renderConceptList('相关技巧', detailInfo.techniques, <BulbOutlined />)}
          {renderRelatedProblems()}
          {renderComplexity()}
        </div>
      )}
    </Card>
  );
};

export default NodeDetailPanel;
