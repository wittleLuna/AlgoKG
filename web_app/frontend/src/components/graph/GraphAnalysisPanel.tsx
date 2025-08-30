import React, { useState, useEffect } from 'react';
import { Card, Statistic, Row, Col, Progress, List, Tag, Typography, Space, Button, Tooltip } from 'antd';
import { 
  NodeIndexOutlined, 
  BranchesOutlined, 
  ClusterOutlined,
  TrophyOutlined,
  InfoCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { GraphData, GraphNode, GraphEdge } from '../../types';

const { Title, Text } = Typography;

interface GraphAnalysisPanelProps {
  data?: GraphData;
  selectedNode?: GraphNode;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

interface GraphMetrics {
  totalNodes: number;
  totalEdges: number;
  nodeTypes: Record<string, number>;
  edgeTypes: Record<string, number>;
  centralityScores: Record<string, number>;
  clusteringCoefficient: number;
  averageDegree: number;
  maxDegree: number;
  diameter: number;
  connectedComponents: number;
}

interface NodeAnalysis {
  id: string;
  label: string;
  type: string;
  degree: number;
  betweennessCentrality: number;
  closenessCentrality: number;
  clusteringCoefficient: number;
  importance: number;
}

const GraphAnalysisPanel: React.FC<GraphAnalysisPanelProps> = ({
  data,
  selectedNode,
  onNodeClick,
  className
}) => {
  const [metrics, setMetrics] = useState<GraphMetrics | null>(null);
  const [topNodes, setTopNodes] = useState<NodeAnalysis[]>([]);
  const [loading, setLoading] = useState(false);

  // 计算图谱指标
  const calculateMetrics = (graphData: GraphData): GraphMetrics => {
    const nodes = graphData.nodes;
    const edges = graphData.edges;

    // 基础统计
    const totalNodes = nodes.length;
    const totalEdges = edges.length;

    // 节点类型统计
    const nodeTypes: Record<string, number> = {};
    nodes.forEach(node => {
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;
    });

    // 边类型统计
    const edgeTypes: Record<string, number> = {};
    edges.forEach(edge => {
      edgeTypes[edge.relationship] = (edgeTypes[edge.relationship] || 0) + 1;
    });

    // 构建邻接表
    const adjacencyList: Record<string, string[]> = {};
    nodes.forEach(node => {
      adjacencyList[node.id] = [];
    });
    edges.forEach(edge => {
      adjacencyList[edge.source]?.push(edge.target);
      adjacencyList[edge.target]?.push(edge.source);
    });

    // 计算度数
    const degrees: Record<string, number> = {};
    Object.keys(adjacencyList).forEach(nodeId => {
      degrees[nodeId] = adjacencyList[nodeId].length;
    });

    const averageDegree = Object.values(degrees).reduce((sum, degree) => sum + degree, 0) / totalNodes;
    const maxDegree = Math.max(...Object.values(degrees));

    // 计算中心性指标（简化版）
    const centralityScores: Record<string, number> = {};
    nodes.forEach(node => {
      // 度中心性（归一化）
      centralityScores[node.id] = degrees[node.id] / (totalNodes - 1);
    });

    // 计算聚类系数（简化版）
    let totalClusteringCoefficient = 0;
    nodes.forEach(node => {
      const neighbors = adjacencyList[node.id];
      if (neighbors.length < 2) return;

      let triangles = 0;
      for (let i = 0; i < neighbors.length; i++) {
        for (let j = i + 1; j < neighbors.length; j++) {
          if (adjacencyList[neighbors[i]]?.includes(neighbors[j])) {
            triangles++;
          }
        }
      }

      const possibleTriangles = (neighbors.length * (neighbors.length - 1)) / 2;
      totalClusteringCoefficient += possibleTriangles > 0 ? triangles / possibleTriangles : 0;
    });

    const clusteringCoefficient = totalNodes > 0 ? totalClusteringCoefficient / totalNodes : 0;

    // 计算直径（简化版 - 使用BFS）
    const diameter = calculateDiameter(adjacencyList);

    // 计算连通分量数量
    const connectedComponents = calculateConnectedComponents(adjacencyList);

    return {
      totalNodes,
      totalEdges,
      nodeTypes,
      edgeTypes,
      centralityScores,
      clusteringCoefficient,
      averageDegree,
      maxDegree,
      diameter,
      connectedComponents
    };
  };

  // 计算图的直径
  const calculateDiameter = (adjacencyList: Record<string, string[]>): number => {
    let maxDistance = 0;
    const nodes = Object.keys(adjacencyList);

    for (const startNode of nodes) {
      const distances = bfs(adjacencyList, startNode);
      const maxDistanceFromStart = Math.max(...Object.values(distances).filter(d => d !== Infinity));
      maxDistance = Math.max(maxDistance, maxDistanceFromStart);
    }

    return maxDistance;
  };

  // BFS算法
  const bfs = (adjacencyList: Record<string, string[]>, startNode: string): Record<string, number> => {
    const distances: Record<string, number> = {};
    const visited = new Set<string>();
    const queue = [{ node: startNode, distance: 0 }];

    Object.keys(adjacencyList).forEach(node => {
      distances[node] = Infinity;
    });
    distances[startNode] = 0;

    while (queue.length > 0) {
      const { node, distance } = queue.shift()!;
      
      if (visited.has(node)) continue;
      visited.add(node);

      adjacencyList[node].forEach(neighbor => {
        if (!visited.has(neighbor) && distances[neighbor] === Infinity) {
          distances[neighbor] = distance + 1;
          queue.push({ node: neighbor, distance: distance + 1 });
        }
      });
    }

    return distances;
  };

  // 计算连通分量
  const calculateConnectedComponents = (adjacencyList: Record<string, string[]>): number => {
    const visited = new Set<string>();
    let components = 0;

    const dfs = (node: string) => {
      visited.add(node);
      adjacencyList[node].forEach(neighbor => {
        if (!visited.has(neighbor)) {
          dfs(neighbor);
        }
      });
    };

    Object.keys(adjacencyList).forEach(node => {
      if (!visited.has(node)) {
        dfs(node);
        components++;
      }
    });

    return components;
  };

  // 分析重要节点
  const analyzeNodes = (graphData: GraphData, metrics: GraphMetrics): NodeAnalysis[] => {
    const nodeAnalyses: NodeAnalysis[] = [];

    graphData.nodes.forEach(node => {
      const degree = Object.values(graphData.edges).filter(
        edge => edge.source === node.id || edge.target === node.id
      ).length;

      const centrality = metrics.centralityScores[node.id] || 0;
      
      // 简化的重要性评分
      const importance = (degree / metrics.maxDegree) * 0.6 + centrality * 0.4;

      nodeAnalyses.push({
        id: node.id,
        label: node.label,
        type: node.type,
        degree,
        betweennessCentrality: centrality, // 简化
        closenessCentrality: centrality, // 简化
        clusteringCoefficient: 0, // 简化
        importance
      });
    });

    return nodeAnalyses.sort((a, b) => b.importance - a.importance).slice(0, 10);
  };

  // 当数据变化时重新计算
  useEffect(() => {
    if (data && data.nodes.length > 0) {
      setLoading(true);
      
      // 模拟异步计算
      setTimeout(() => {
        const newMetrics = calculateMetrics(data);
        const newTopNodes = analyzeNodes(data, newMetrics);
        
        setMetrics(newMetrics);
        setTopNodes(newTopNodes);
        setLoading(false);
      }, 500);
    }
  }, [data]);

  if (!data || !metrics) {
    return (
      <Card className={className} loading={loading}>
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Text type="secondary">暂无分析数据</Text>
        </div>
      </Card>
    );
  }

  return (
    <div className={`graph-analysis-panel ${className || ''}`}>
      {/* 基础统计 */}
      <Card title="图谱概览" size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="节点数量"
              value={metrics.totalNodes}
              prefix={<NodeIndexOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="关系数量"
              value={metrics.totalEdges}
              prefix={<BranchesOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="平均度数"
              value={metrics.averageDegree}
              precision={1}
              prefix={<ClusterOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="连通分量"
              value={metrics.connectedComponents}
              prefix={<InfoCircleOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* 图谱质量指标 */}
      <Card title="图谱质量" size="small" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>聚类系数</Text>
            <Tooltip title="衡量图中节点聚集程度的指标">
              <InfoCircleOutlined style={{ marginLeft: 4, color: '#1890ff' }} />
            </Tooltip>
            <Progress
              percent={metrics.clusteringCoefficient * 100}
              size="small"
              strokeColor="#52c41a"
              style={{ marginTop: 4 }}
            />
          </div>
          
          <div>
            <Text strong>图直径: {metrics.diameter}</Text>
            <Tooltip title="图中任意两点间最短路径的最大值">
              <InfoCircleOutlined style={{ marginLeft: 4, color: '#1890ff' }} />
            </Tooltip>
          </div>
        </Space>
      </Card>

      {/* 节点类型分布 */}
      <Card title="节点类型分布" size="small" style={{ marginBottom: 16 }}>
        <List
          size="small"
          dataSource={Object.entries(metrics.nodeTypes)}
          renderItem={([type, count]) => (
            <List.Item>
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                  <Tag color="blue">{type}</Tag>
                  <Text>{count} 个</Text>
                </Space>
                <Progress
                  percent={(count / metrics.totalNodes) * 100}
                  size="small"
                  style={{ width: 60 }}
                  showInfo={false}
                />
              </Space>
            </List.Item>
          )}
        />
      </Card>

      {/* 重要节点排名 */}
      <Card 
        title={
          <Space>
            <TrophyOutlined />
            <span>重要节点排名</span>
          </Space>
        } 
        size="small"
      >
        <List
          size="small"
          dataSource={topNodes}
          renderItem={(node, index) => (
            <List.Item
              className="important-node-item"
              onClick={() => onNodeClick && onNodeClick(node.id)}
            >
              <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                  <Text strong style={{ color: '#1890ff' }}>
                    #{index + 1}
                  </Text>
                  <div>
                    <Text strong>{node.label}</Text>
                    <br />
                    <Tag size="small" color="purple">{node.type}</Tag>
                    <Tag size="small" color="orange">度数: {node.degree}</Tag>
                  </div>
                </Space>
                <div style={{ textAlign: 'right' }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    重要性
                  </Text>
                  <br />
                  <Progress
                    type="circle"
                    percent={node.importance * 100}
                    width={40}
                    strokeColor="#faad14"
                  />
                </div>
              </Space>
            </List.Item>
          )}
        />
      </Card>

      {/* 选中节点详情 */}
      {selectedNode && (
        <Card 
          title="选中节点详情" 
          size="small" 
          style={{ marginTop: 16 }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Title level={5}>{selectedNode.label}</Title>
              <Tag color="blue">{selectedNode.type}</Tag>
            </div>
            
            {selectedNode.properties && (
              <div>
                <Text strong>属性信息:</Text>
                <div style={{ marginTop: 8 }}>
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: 4 }}>
                      <Text type="secondary">{key}:</Text>
                      <Text style={{ marginLeft: 8 }}>{String(value)}</Text>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Space>
        </Card>
      )}

      <style jsx>{`
        .graph-analysis-panel {
          height: 100%;
          overflow-y: auto;
        }

        .important-node-item {
          cursor: pointer;
          transition: all 0.2s ease;
          border-radius: 6px;
          padding: 8px !important;
        }

        .important-node-item:hover {
          background: rgba(24, 144, 255, 0.05);
          transform: translateX(2px);
        }

        .graph-analysis-panel :global(.ant-card) {
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }

        .graph-analysis-panel :global(.ant-statistic-title) {
          font-size: 12px;
        }

        .graph-analysis-panel :global(.ant-statistic-content) {
          font-size: 18px;
        }

        @media (max-width: 768px) {
          .graph-analysis-panel :global(.ant-col) {
            margin-bottom: 16px;
          }
        }
      `}</style>
    </div>
  );
};

export default GraphAnalysisPanel;
