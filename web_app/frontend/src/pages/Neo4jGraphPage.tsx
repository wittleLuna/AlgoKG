import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Tabs, message, Spin, Button, Space, Typography, Divider, Drawer } from 'antd';
import { NodeIndexOutlined, SearchOutlined, ClusterOutlined } from '@ant-design/icons';
import Neo4jGraphVisualization from '../components/graph/Neo4jGraphVisualization';
import NodeDetailPanel from '../components/graph/NodeDetailPanel';
import { GraphData, GraphNode } from '../types';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const Neo4jGraphPage: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [activeTab, setActiveTab] = useState('explore');
  const [showNodeDetail, setShowNodeDetail] = useState(false);

  // 示例查询
  const exampleQueries = [
    { name: '动态规划', type: 'Algorithm', description: '查看动态规划相关的题目和技巧' },
    { name: '二叉树', type: 'DataStructure', description: '探索二叉树相关的算法和题目' },
    { name: '两数之和', type: 'Problem', description: '查看经典题目的知识网络' },
    { name: '贪心算法', type: 'Algorithm', description: '了解贪心算法的应用场景' }
  ];

  // 查询Neo4j图谱数据
  const queryGraphData = async (entityName: string, entityType: string) => {
    setLoading(true);
    try {
      let url = '';
      switch (entityType) {
        case 'Problem':
          url = `/api/v1/graph/neo4j/problem/${encodeURIComponent(entityName)}`;
          break;
        case 'Algorithm':
          url = `/api/v1/graph/neo4j/algorithm/${encodeURIComponent(entityName)}`;
          break;
        case 'DataStructure':
          url = `/api/v1/graph/neo4j/data-structure/${encodeURIComponent(entityName)}`;
          break;
        default:
          url = `/api/v1/graph/query`;
      }

      const response = await fetch(url, {
        method: entityType === 'Problem' || entityType === 'Algorithm' || entityType === 'DataStructure' ? 'GET' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: entityType === 'Problem' || entityType === 'Algorithm' || entityType === 'DataStructure' ? undefined : JSON.stringify({
          entity_name: entityName,
          entity_type: entityType,
          depth: 2,
          limit: 50
        })
      });

      if (response.ok) {
        const data = await response.json();
        setGraphData(data);
        message.success(`成功加载 ${entityName} 的知识图谱`);
      } else {
        message.error('加载图谱数据失败');
      }
    } catch (error) {
      console.error('查询图谱数据错误:', error);
      message.error('查询失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 探索查询
  const exploreGraph = async (query: string, nodeTypes: string[] = ['Problem', 'Algorithm', 'DataStructure']) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/graph/neo4j/explore?query=${encodeURIComponent(query)}&node_types=${nodeTypes.join(',')}&limit=100`
      );

      if (response.ok) {
        const data = await response.json();
        setGraphData(data);
        message.success(`找到 ${data.nodes?.length || 0} 个相关节点`);
      } else {
        message.error('探索查询失败');
      }
    } catch (error) {
      console.error('探索查询错误:', error);
      message.error('查询失败，请检查网络连接');
    } finally {
      setLoading(false);
    }
  };

  // 节点点击处理 - 显示节点详情而不是重新查询
  const handleNodeClick = (nodeId: string, nodeData: GraphNode) => {
    setSelectedNode(nodeData);
    setShowNodeDetail(true);

    // 可选：如果需要同时更新图谱，可以保留这个逻辑
    // if (['Problem', 'Algorithm', 'DataStructure'].includes(nodeData.type)) {
    //   queryGraphData(nodeData.label, nodeData.type);
    // }
  };

  // 关闭节点详情面板
  const handleCloseNodeDetail = () => {
    setShowNodeDetail(false);
    setSelectedNode(null);
  };

  // 初始化时加载示例数据
  useEffect(() => {
    queryGraphData('动态规划', 'Algorithm');
  }, []);

  // 渲染示例查询按钮
  const renderExampleQueries = () => (
    <Card title="示例查询" size="small" style={{ marginBottom: 16 }}>
      <Space wrap>
        {exampleQueries.map((query, index) => (
          <Button
            key={index}
            type="default"
            size="small"
            onClick={() => queryGraphData(query.name, query.type)}
            loading={loading}
          >
            {query.name}
          </Button>
        ))}
      </Space>
    </Card>
  );

  // 渲染节点详情
  const renderNodeDetails = () => {
    if (!selectedNode) {
      return (
        <Card title="节点详情" size="small">
          <Text type="secondary">点击图谱中的节点查看详细信息</Text>
        </Card>
      );
    }

    return (
      <Card title="节点详情" size="small">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>名称: </Text>
            <Text>{selectedNode.label}</Text>
          </div>
          <div>
            <Text strong>类型: </Text>
            <Text>{selectedNode.type}</Text>
          </div>
          <div>
            <Text strong>ID: </Text>
            <Text code>{selectedNode.id}</Text>
          </div>
          
          {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
            <>
              <Divider style={{ margin: '8px 0' }} />
              <Text strong>属性:</Text>
              {Object.entries(selectedNode.properties).map(([key, value]) => (
                <div key={key} style={{ marginLeft: 16 }}>
                  <Text type="secondary">{key}: </Text>
                  <Text>{String(value)}</Text>
                </div>
              ))}
            </>
          )}
          
          <Divider style={{ margin: '8px 0' }} />
          <Button
            type="primary"
            size="small"
            onClick={() => queryGraphData(selectedNode.label, selectedNode.type)}
            disabled={!['Problem', 'Algorithm', 'DataStructure'].includes(selectedNode.type)}
          >
            以此为中心查询
          </Button>
        </Space>
      </Card>
    );
  };

  // 渲染图谱统计
  const renderGraphStats = () => {
    if (!graphData) return null;

    const nodeTypeStats = graphData.nodes.reduce((acc, node) => {
      acc[node.type] = (acc[node.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <Card title="图谱统计" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                {graphData.nodes.length}
              </div>
              <div>节点总数</div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                {graphData.edges.length}
              </div>
              <div>关系总数</div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#722ed1' }}>
                {Object.keys(nodeTypeStats).length}
              </div>
              <div>节点类型</div>
            </div>
          </Col>
        </Row>
        
        <Divider style={{ margin: '12px 0' }} />
        
        <div>
          <Text strong>节点类型分布:</Text>
          <div style={{ marginTop: 8 }}>
            {Object.entries(nodeTypeStats).map(([type, count]) => (
              <div key={type} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <Text>{type}:</Text>
                <Text strong>{count}</Text>
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ClusterOutlined style={{ marginRight: 8 }} />
          Neo4j 知识图谱可视化
        </Title>
        <Paragraph type="secondary">
          基于Neo4j数据库的实时知识图谱展示，支持算法、数据结构、题目等多维度关系探索
        </Paragraph>
      </div>

      <Row gutter={24}>
        <Col span={18}>
          <Spin spinning={loading}>
            <Neo4jGraphVisualization
              data={graphData}
              onNodeClick={handleNodeClick}
              height={600}
              showSearch={true}
              showControls={true}
            />
          </Spin>
        </Col>
        
        <Col span={6}>
          {renderExampleQueries()}
          {renderGraphStats()}
          {renderNodeDetails()}
        </Col>
      </Row>

      {/* 节点详情抽屉 */}
      <Drawer
        title="节点详情"
        placement="right"
        width={600}
        onClose={handleCloseNodeDetail}
        open={showNodeDetail}
        destroyOnClose={true}
      >
        <NodeDetailPanel
          node={selectedNode}
          onClose={handleCloseNodeDetail}
          visible={showNodeDetail}
        />
      </Drawer>
    </div>
  );
};

export default Neo4jGraphPage;
