import React, { useState, useEffect } from 'react';
import { Card, Typography, Button, Space, Spin, Alert, Tag, Drawer, Divider, List, message } from 'antd';
import {
  NodeIndexOutlined,
  ExpandAltOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  CodeOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  CloseOutlined
} from '@ant-design/icons';
import { GraphData, GraphNode } from '../../types';
import UnifiedGraphVisualization from '../graph/UnifiedGraphVisualization';

const { Text, Title, Paragraph } = Typography;

interface InlineKnowledgeGraphProps {
  graphData: GraphData;
  entities: string[];
  onNodeClick?: (nodeId: string, nodeData: GraphNode) => void;
  onExpandClick?: () => void;
  showAnimation?: boolean; // 是否显示动画，默认false（暂停）
  isEnhanced?: boolean; // 是否为增强图谱数据
}

interface NodeDetailInfo {
  basic_info: {
    title: string;
    type: string;
    description?: string;
    difficulty?: string;
    platform?: string;
    category?: string;
    url?: string;
    properties?: any;
  };
  error?: string;
  algorithms?: Array<{
    name: string;
    description?: string;
    category?: string;
  }>;
  data_structures?: Array<{
    name: string;
    description?: string;
    category?: string;
  }>;
  techniques?: Array<{
    name: string;
    description?: string;
  }>;
  solutions?: Array<{
    approach?: string;
    language?: string;
    code?: string;
    description?: string;
    time_complexity?: string;
    space_complexity?: string;
  }>;
  related_problems?: Array<{
    title: string;
    difficulty?: string;
    similarity_score?: number;
    platform?: string;
  }>;
  insights?: Array<{
    title?: string;
    content?: string;
    type?: string;
  }>;
  advantages?: Array<string | {content?: string; description?: string}>;
  disadvantages?: Array<string | {content?: string; description?: string}>;
  operations?: Array<{
    name: string;
    complexity?: string;
    description?: string;
  }>;
  applications?: Array<string>;
  use_cases?: Array<string>;
  complexity?: {
    time?: string;
    space?: string;
    access?: string;
    search?: string;
    insertion?: string;
    deletion?: string;
  };
}

const InlineKnowledgeGraph: React.FC<InlineKnowledgeGraphProps> = ({
  graphData,
  entities,
  onNodeClick,
  onExpandClick,
  showAnimation = false, // 默认暂停动画
  isEnhanced = false // 是否为增强图谱数据
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeDetailVisible, setNodeDetailVisible] = useState(false);
  const [nodeDetailLoading, setNodeDetailLoading] = useState(false);
  const [nodeDetailInfo, setNodeDetailInfo] = useState<NodeDetailInfo | null>(null);
  const [nodeDetailError, setNodeDetailError] = useState<string | null>(null);

  // 获取节点详细信息 - 使用统一的API路径
  const fetchNodeDetail = async (nodeId: string, nodeType: string) => {
    setNodeDetailLoading(true);
    setNodeDetailError(null);

    try {
      // 使用统一的API路径，与独立面板保持一致
      const url = `/api/v1/graph/unified/node/${encodeURIComponent(nodeId)}/details?node_type=${nodeType}`;

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // 验证数据结构
      if (!data || typeof data !== 'object') {
        console.error('❌ API响应数据格式无效:', data);
        throw new Error('API响应数据格式无效');
      }

      console.log('✅ 节点详情API响应:', data);
      console.log('📊 数据字段检查:', {
        hasBasicInfo: !!data.basic_info,
        hasAlgorithms: !!data.algorithms,
        algorithmsLength: data.algorithms?.length || 0,
        hasDataStructures: !!data.data_structures,
        dataStructuresLength: data.data_structures?.length || 0,
        hasTechniques: !!data.techniques,
        techniquesLength: data.techniques?.length || 0,
        hasComplexity: !!data.complexity,
        hasSolutions: !!data.solutions,
        solutionsLength: data.solutions?.length || 0
      });

      setNodeDetailInfo(data);
    } catch (err: any) {
      console.error('获取节点详情失败:', err);
      setNodeDetailError(err.message || '获取节点详情失败');
    } finally {
      setNodeDetailLoading(false);
    }
  };

  // 处理节点点击
  const handleNodeClick = (nodeId: string, nodeData: GraphNode) => {
    console.log('InlineKnowledgeGraph - 节点点击:', { nodeId, nodeData });

    setSelectedNode(nodeData);
    setNodeDetailVisible(true);

    // 智能选择查询参数：
    // 1. 如果是独立图谱的节点ID格式（node_problem_xxx），使用节点的label（题目名称）
    // 2. 如果是增强图谱的节点ID格式（neo4j_xxx），使用节点ID
    console.log(`🔍 节点ID分析: ${nodeId}, label: ${nodeData.label}`);

    let queryParam = nodeId;
    if (nodeId.startsWith('node_problem_') || nodeId.startsWith('node_algorithm_') || nodeId.startsWith('node_datastructure_')) {
      // 独立图谱格式，使用label作为查询参数
      queryParam = nodeData.label;
      console.log(`🔄 独立图谱节点，使用label查询: ${nodeData.label}`);
    } else {
      // 增强图谱格式，使用nodeId
      console.log(`🔄 增强图谱节点，使用nodeId查询: ${nodeId}`);
    }

    console.log(`📤 最终查询参数: ${queryParam}`);

    fetchNodeDetail(queryParam, nodeData.type);

    // 不调用外部的onNodeClick回调，避免重复处理
    // if (onNodeClick) {
    //   onNodeClick(nodeId, nodeData);
    // }
  };

  // 统计不同类型的节点
  const getNodeStats = () => {
    const stats: { [key: string]: number } = {};
    graphData.nodes.forEach(node => {
      stats[node.type] = (stats[node.type] || 0) + 1;
    });
    return stats;
  };

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

  const nodeStats = getNodeStats();
  const totalNodes = graphData.nodes.length;
  const totalEdges = graphData.edges.length;

  // 找到中心节点
  const centerNode = graphData.nodes.find(node => 
    node.properties?.is_center || node.id === graphData.center_node
  );

  const handleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const handleDownloadGraph = () => {
    console.log('📥 开始下载图谱');

    try {
      // 查找图谱容器中的Canvas元素（vis.js使用Canvas渲染）
      // 首先尝试在当前组件的容器中查找
      const currentContainer = document.querySelector('.unified-graph-visualization');
      let graphContainer: HTMLCanvasElement | null = null;

      if (currentContainer) {
        graphContainer = currentContainer.querySelector('canvas') as HTMLCanvasElement;
      }

      // 如果没找到，尝试其他选择器
      if (!graphContainer) {
        graphContainer = document.querySelector('.graph-container canvas') as HTMLCanvasElement ||
                        document.querySelector('.enhanced-graph-visualization canvas') as HTMLCanvasElement ||
                        document.querySelector('canvas') as HTMLCanvasElement;
      }

      if (!graphContainer) {
        console.warn('⚠️ 未找到图谱Canvas元素，尝试备用方法');
        // 显示所有Canvas元素用于调试
        const allCanvases = document.querySelectorAll('canvas');
        console.log('🔍 页面中的所有Canvas元素:', allCanvases.length);

        if (allCanvases.length > 0) {
          // 使用第一个找到的Canvas作为备用
          console.log('📋 使用第一个Canvas作为备用');
          graphContainer = allCanvases[0] as HTMLCanvasElement;
        } else {
          console.error('❌ 页面中没有找到任何Canvas元素');
          message.error('无法找到图谱元素，请确保图谱已加载完成');
          return;
        }
      }

      const canvas = graphContainer;

      // 创建新的Canvas用于添加背景和边距
      const downloadCanvas = document.createElement('canvas');
      const ctx = downloadCanvas.getContext('2d');

      if (!ctx) {
        console.error('❌ 无法创建Canvas上下文');
        return;
      }

      // 设置下载Canvas的尺寸（添加边距）
      const padding = 40;
      downloadCanvas.width = canvas.width + padding * 2;
      downloadCanvas.height = canvas.height + padding * 2;

      // 设置白色背景
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, downloadCanvas.width, downloadCanvas.height);

      // 绘制原始图谱到新Canvas（添加边距）
      ctx.drawImage(canvas, padding, padding);

      // 添加标题
      ctx.fillStyle = '#333';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('知识图谱', downloadCanvas.width / 2, 25);

      // 添加时间戳
      ctx.font = '12px Arial';
      ctx.textAlign = 'right';
      ctx.fillStyle = '#999';
      const timestamp = new Date().toLocaleString('zh-CN');
      ctx.fillText(`生成时间: ${timestamp}`, downloadCanvas.width - 10, downloadCanvas.height - 10);

      // 转换为PNG并下载
      downloadCanvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `knowledge-graph-${Date.now()}.png`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);

          // 清理URL
          URL.revokeObjectURL(url);

          console.log('✅ 图谱下载成功');
          message.success('图谱下载成功！');
        }
      }, 'image/png', 0.95); // 高质量PNG

    } catch (error) {
      console.error('❌ 下载图谱时出错:', error);
      message.error('下载图谱时出错，请稍后重试');
    }
  };

  return (
    <Card
      size="small"
      style={{
        margin: '16px 0',
        border: '1px solid #d9d9d9',
        borderRadius: '8px',
        background: 'linear-gradient(135deg, #f6ffed 0%, #f0f9ff 100%)'
      }}
      bodyStyle={{ padding: '16px' }}
    >
      {/* 头部信息 */}
      <div style={{ marginBottom: '12px' }}>
        <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space align="center">
            <NodeIndexOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
            <Title level={5} style={{ margin: 0, color: '#1890ff' }}>
              知识图谱
            </Title>
            <Tag color="blue">{totalNodes}个节点</Tag>
            <Tag color="green">{totalEdges}条关系</Tag>
            {isEnhanced && <Tag color="orange">增强数据</Tag>}
          </Space>
          <Space>
            <Button
              type="text"
              size="small"
              icon={<DownloadOutlined />}
              onClick={handleDownloadGraph}
            >
              下载图谱
            </Button>
            <Button 
              type="text" 
              size="small" 
              icon={<ExpandAltOutlined />}
              onClick={handleExpand}
            >
              {isExpanded ? '收起' : '展开'}
            </Button>
          </Space>
        </Space>
      </div>

      {/* 实体和统计信息 */}
      <div style={{ marginBottom: '12px' }}>
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          {/* 查询实体 */}
          <div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              <InfoCircleOutlined style={{ marginRight: '4px' }} />
              查询实体：
            </Text>
            <Space size="small" wrap>
              {entities.map((entity, index) => (
                <Tag key={index} color="processing" style={{ fontSize: '12px' }}>
                  {entity}
                </Tag>
              ))}
            </Space>
          </div>

          {/* 节点类型统计 */}
          <div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              节点类型：
            </Text>
            <Space size="small" wrap>
              {Object.entries(nodeStats).map(([type, count]) => (
                <Tag key={type} style={{ fontSize: '12px' }}>
                  {type}: {count}
                </Tag>
              ))}
            </Space>
          </div>

          {/* 中心节点信息 */}
          {centerNode && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                中心节点：
              </Text>
              <Tag color="gold" style={{ fontSize: '12px' }}>
                {centerNode.label} ({centerNode.type})
              </Tag>
            </div>
          )}
        </Space>
      </div>

      {/* 图谱可视化区域 */}
      {isExpanded && (
        <div
          style={{
            height: '400px',
            border: '1px solid #e8e8e8',
            borderRadius: '6px',
            background: 'white',
            position: 'relative',
            overflow: 'auto', // 添加滚动支持
            cursor: 'grab' // 添加拖拽光标提示
          }}
          onMouseDown={(e) => {
            // 拖拽时改变光标
            e.currentTarget.style.cursor = 'grabbing';
          }}
          onMouseUp={(e) => {
            // 释放时恢复光标
            e.currentTarget.style.cursor = 'grab';
          }}
          onMouseLeave={(e) => {
            // 鼠标离开时恢复光标
            e.currentTarget.style.cursor = 'grab';
          }}
        >
          {/* 滚动提示 */}
          <div style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            background: 'rgba(0, 0, 0, 0.6)',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            zIndex: 10,
            pointerEvents: 'none'
          }}>
            可滚动查看
          </div>

          {loading ? (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%'
            }}>
              <Spin tip="加载图谱中..." />
            </div>
          ) : (
            <UnifiedGraphVisualization
              data={graphData}
              height="100%"
              showControls={true}
              onNodeClick={handleNodeClick}
              defaultDataSources={['neo4j', 'embedding']}
              showAnimation={showAnimation}
              disableBuiltinNodeDetail={true}
              disableEnhancedNodeInfo={true}
            />
          )}
        </div>
      )}

      {/* 简化预览（未展开时） */}
      {!isExpanded && (
        <div 
          style={{ 
            height: '120px', 
            border: '1px solid #e8e8e8', 
            borderRadius: '6px',
            background: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          onClick={handleExpand}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#fafafa';
            e.currentTarget.style.borderColor = '#1890ff';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'white';
            e.currentTarget.style.borderColor = '#e8e8e8';
          }}
        >
          <Space direction="vertical" align="center">
            <NodeIndexOutlined style={{ fontSize: '32px', color: '#1890ff' }} />
            <Text type="secondary" style={{ fontSize: '14px' }}>
              点击展开查看知识图谱
            </Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {totalNodes}个节点，{totalEdges}条关系
            </Text>
          </Space>
        </div>
      )}

      {/* 底部说明 */}
      <div style={{ marginTop: '12px', textAlign: 'center' }}>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          基于查询实体"{entities.join('、')}"生成的知识关系图谱
        </Text>
      </div>

      {/* 节点详情抽屉 */}
      <Drawer
        title={
          selectedNode ? (
            <Space>
              {getNodeIcon(selectedNode.type)}
              <span>{selectedNode.label}</span>
              <Tag color="blue">{selectedNode.type}</Tag>
            </Space>
          ) : '节点详情'
        }
        placement="right"
        width={480}
        onClose={() => setNodeDetailVisible(false)}
        open={nodeDetailVisible}
        extra={
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={() => setNodeDetailVisible(false)}
          />
        }
      >
        {nodeDetailLoading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin tip="加载节点详情中..." />
          </div>
        ) : nodeDetailError ? (
          <Alert
            message="加载失败"
            description={nodeDetailError}
            type="error"
            showIcon
          />
        ) : nodeDetailInfo ? (
          <div>
            {/* 调试信息 - 临时显示 */}
            <Card size="small" title="🔍 调试信息" style={{ marginBottom: 16, background: '#f0f9ff' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">算法数量: {nodeDetailInfo?.algorithms?.length || 0}</Text>
                <Text type="secondary">数据结构数量: {nodeDetailInfo?.data_structures?.length || 0}</Text>
                <Text type="secondary">技巧数量: {nodeDetailInfo?.techniques?.length || 0}</Text>
                <Text type="secondary">解决方案数量: {nodeDetailInfo?.solutions?.length || 0}</Text>
                <Text type="secondary">相关题目数量: {nodeDetailInfo?.related_problems?.length || 0}</Text>
                <Text type="secondary">数据字段: {Object.keys(nodeDetailInfo || {}).join(', ')}</Text>
                {nodeDetailInfo?.error && (
                  <Text type="danger">❌ 错误信息: {nodeDetailInfo.error}</Text>
                )}
                <Text type="secondary">节点ID: {selectedNode?.id}</Text>
                <Text type="secondary">节点类型: {selectedNode?.type}</Text>
              </Space>
            </Card>

            {/* 基本信息 - 使用安全的数据访问 */}
            <Card size="small" title="基本信息" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>名称：</Text>
                  <Text>
                    {nodeDetailInfo?.basic_info?.title ||
                     selectedNode?.label ||
                     '未知'}
                  </Text>
                </div>
                <div>
                  <Text strong>类型：</Text>
                  <Tag color="blue">
                    {nodeDetailInfo?.basic_info?.type ||
                     selectedNode?.type ||
                     '未知'}
                  </Tag>
                </div>
                {nodeDetailInfo?.basic_info?.difficulty && nodeDetailInfo.basic_info.difficulty !== null && (
                  <div>
                    <Text strong>难度：</Text>
                    <Tag color={getDifficultyColor(nodeDetailInfo.basic_info.difficulty)}>
                      {nodeDetailInfo.basic_info.difficulty}
                    </Tag>
                  </div>
                )}
                {nodeDetailInfo?.basic_info?.category && (
                  <div>
                    <Text strong>分类：</Text>
                    <Tag color="purple">{nodeDetailInfo.basic_info.category}</Tag>
                  </div>
                )}
                {nodeDetailInfo?.basic_info?.url && (
                  <div>
                    <Text strong>链接：</Text>
                    <a href={nodeDetailInfo.basic_info.url} target="_blank" rel="noopener noreferrer">
                      查看题目
                    </a>
                  </div>
                )}
                {nodeDetailInfo?.basic_info?.platform && (
                  <div>
                    <Text strong>平台：</Text>
                    <Text>{nodeDetailInfo.basic_info.platform}</Text>
                  </div>
                )}
                {nodeDetailInfo?.basic_info?.description && (
                  <div>
                    <Text strong>描述：</Text>
                    <Paragraph>{nodeDetailInfo.basic_info.description}</Paragraph>
                  </div>
                )}

              </Space>
            </Card>

            {/* 算法信息 */}
            {nodeDetailInfo?.algorithms && Array.isArray(nodeDetailInfo.algorithms) && nodeDetailInfo.algorithms.length > 0 && (
              <Card size="small" title="相关算法" style={{ marginBottom: 16 }}>
                <List
                  size="small"
                  dataSource={nodeDetailInfo.algorithms}
                  renderItem={(item) => (
                    <List.Item>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>{item?.name || '未知算法'}</Text>
                        {item?.description && <Text type="secondary">{item.description}</Text>}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 数据结构信息 */}
            {nodeDetailInfo?.data_structures && Array.isArray(nodeDetailInfo.data_structures) && nodeDetailInfo.data_structures.length > 0 && (
              <Card size="small" title="相关数据结构" style={{ marginBottom: 16 }}>
                <List
                  size="small"
                  dataSource={nodeDetailInfo.data_structures}
                  renderItem={(item) => (
                    <List.Item>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>{item?.name || '未知数据结构'}</Text>
                        {item?.description && <Text type="secondary">{item.description}</Text>}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 复杂度信息 */}
            {nodeDetailInfo?.complexity && typeof nodeDetailInfo.complexity === 'object' && (
              <Card size="small" title="复杂度分析" style={{ marginBottom: 16 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {nodeDetailInfo.complexity.time && (
                    <div>
                      <Text strong>时间复杂度：</Text>
                      <Tag color="green">{nodeDetailInfo.complexity.time}</Tag>
                    </div>
                  )}
                  {nodeDetailInfo.complexity.space && (
                    <div>
                      <Text strong>空间复杂度：</Text>
                      <Tag color="blue">{nodeDetailInfo.complexity.space}</Tag>
                    </div>
                  )}
                  {/* 数据结构的复杂度信息 */}
                  {nodeDetailInfo.complexity.access && (
                    <div>
                      <Text strong>访问复杂度：</Text>
                      <Tag color="cyan">{nodeDetailInfo.complexity.access}</Tag>
                    </div>
                  )}
                  {nodeDetailInfo.complexity.search && (
                    <div>
                      <Text strong>搜索复杂度：</Text>
                      <Tag color="purple">{nodeDetailInfo.complexity.search}</Tag>
                    </div>
                  )}
                  {nodeDetailInfo.complexity.insertion && (
                    <div>
                      <Text strong>插入复杂度：</Text>
                      <Tag color="orange">{nodeDetailInfo.complexity.insertion}</Tag>
                    </div>
                  )}
                  {nodeDetailInfo.complexity.deletion && (
                    <div>
                      <Text strong>删除复杂度：</Text>
                      <Tag color="red">{nodeDetailInfo.complexity.deletion}</Tag>
                    </div>
                  )}
                </Space>
              </Card>
            )}

            {/* 相关题目 */}
            {nodeDetailInfo?.related_problems && Array.isArray(nodeDetailInfo.related_problems) && nodeDetailInfo.related_problems.length > 0 && (
              <Card size="small" title="相关题目" style={{ marginBottom: 16 }}>
                <List
                  size="small"
                  dataSource={nodeDetailInfo.related_problems}
                  renderItem={(item) => (
                    <List.Item>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Space>
                          <Text strong>{item?.title || '未知题目'}</Text>
                          {item?.difficulty && (
                            <Tag color={getDifficultyColor(item.difficulty)}>
                              {item.difficulty}
                            </Tag>
                          )}
                          {item?.similarity_score && (
                            <Tag color="purple">
                              相似度: {(item.similarity_score * 100).toFixed(1)}%
                            </Tag>
                          )}
                        </Space>
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 技巧信息 */}
            {nodeDetailInfo?.techniques && Array.isArray(nodeDetailInfo.techniques) && nodeDetailInfo.techniques.length > 0 && (
              <Card size="small" title="相关技巧" style={{ marginBottom: 16 }}>
                <List
                  size="small"
                  dataSource={nodeDetailInfo.techniques}
                  renderItem={(item) => (
                    <List.Item>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>{item?.name || '未知技巧'}</Text>
                        {item?.description && <Text type="secondary">{item.description}</Text>}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 解决方案 */}
            {nodeDetailInfo?.solutions && Array.isArray(nodeDetailInfo.solutions) && nodeDetailInfo.solutions.length > 0 && (
              <Card size="small" title="解决方案" style={{ marginBottom: 16 }}>
                <List
                  size="small"
                  dataSource={nodeDetailInfo.solutions}
                  renderItem={(item) => (
                    <List.Item>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>{item?.approach || '解决方案'}</Text>
                        {item?.description && <Paragraph style={{ margin: 0 }}>{item.description}</Paragraph>}
                        {item?.time_complexity && (
                          <div>
                            <Text type="secondary">时间复杂度: </Text>
                            <Tag color="green">{item.time_complexity}</Tag>
                          </div>
                        )}
                        {item?.space_complexity && (
                          <div>
                            <Text type="secondary">空间复杂度: </Text>
                            <Tag color="blue">{item.space_complexity}</Tag>
                          </div>
                        )}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}

            {/* 关键洞察 */}
            {nodeDetailInfo?.insights && Array.isArray(nodeDetailInfo.insights) && nodeDetailInfo.insights.length > 0 && (
              <Card size="small" title="关键洞察" style={{ marginBottom: 16 }}>
                <List
                  size="small"
                  dataSource={nodeDetailInfo.insights}
                  renderItem={(item) => (
                    <List.Item>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>{item?.title || '洞察'}</Text>
                        {item?.content && <Paragraph style={{ margin: 0 }}>{item.content}</Paragraph>}
                      </Space>
                    </List.Item>
                  )}
                />
              </Card>
            )}
          </div>
        ) : selectedNode ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Text type="secondary">暂无详细信息</Text>
          </div>
        ) : null}
      </Drawer>
    </Card>
  );
};

export default InlineKnowledgeGraph;
