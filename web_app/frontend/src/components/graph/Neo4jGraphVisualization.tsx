import React, { useEffect, useRef, useState } from 'react';
import { Card, Typography, Button, Space, Tooltip, Select, Slider, Input, Tag, message } from 'antd';
import { 
  FullscreenOutlined, 
  ReloadOutlined, 
  SettingOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  SearchOutlined,
  NodeIndexOutlined
} from '@ant-design/icons';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { GraphData, GraphNode, GraphEdge } from '../../types';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

interface Neo4jGraphVisualizationProps {
  data?: GraphData;
  onNodeClick?: (nodeId: string, nodeData: GraphNode) => void;
  height?: number;
  width?: string | number;
  showSearch?: boolean;
  showControls?: boolean;
}

const Neo4jGraphVisualization: React.FC<Neo4jGraphVisualizationProps> = ({
  data,
  onNodeClick,
  height = 500,
  width = '100%',
  showSearch = true,
  showControls = true
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [layoutType, setLayoutType] = useState('force');
  const [nodeSize, setNodeSize] = useState(25);
  const [edgeWidth, setEdgeWidth] = useState(2);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>(['Problem', 'Algorithm', 'DataStructure']);

  // Neo4j节点类型颜色映射
  const getNodeColor = (type: string, isCenter: boolean = false) => {
    if (isCenter) {
      return {
        background: '#ff6b6b',
        border: '#e55656',
        highlight: { background: '#ff8e8e', border: '#e55656' }
      };
    }

    const colorMap: Record<string, any> = {
      'Problem': {
        background: '#4ecdc4',
        border: '#45b7b8',
        highlight: { background: '#6bccc4', border: '#45b7b8' }
      },
      'Algorithm': {
        background: '#45b7d1',
        border: '#3d9bc1',
        highlight: { background: '#67c4d8', border: '#3d9bc1' }
      },
      'DataStructure': {
        background: '#96ceb4',
        border: '#85c1a5',
        highlight: { background: '#a8d4bd', border: '#85c1a5' }
      },
      'Technique': {
        background: '#feca57',
        border: '#f39c12',
        highlight: { background: '#fed574', border: '#f39c12' }
      },
      'Difficulty': {
        background: '#ff9ff3',
        border: '#e684db',
        highlight: { background: '#ffb3f5', border: '#e684db' }
      },
      'Platform': {
        background: '#54a0ff',
        border: '#2e86de',
        highlight: { background: '#74b9ff', border: '#2e86de' }
      },
      'Operation': {
        background: '#5f27cd',
        border: '#341f97',
        highlight: { background: '#7c4dff', border: '#341f97' }
      }
    };

    return colorMap[type] || {
      background: '#ddd',
      border: '#999',
      highlight: { background: '#eee', border: '#999' }
    };
  };

  // 转换数据格式
  const convertDataForVis = (graphData: GraphData) => {
    const nodes = new DataSet(
      graphData.nodes.map(node => {
        const isCenter = node.id === graphData.center_node || node.properties?.is_center;
        const color = getNodeColor(node.type, isCenter);
        
        return {
          id: node.id,
          label: node.label,
          title: `${node.type}: ${node.label}${node.properties?.description ? '\n' + node.properties.description : ''}`,
          color: color,
          size: isCenter ? nodeSize * 1.5 : nodeSize,
          font: {
            size: isCenter ? 16 : 14,
            color: '#333'
          },
          borderWidth: isCenter ? 3 : 2,
          chosen: true,
          physics: true,
          group: node.type
        };
      })
    );

    const edges = new DataSet(
      graphData.edges.map(edge => ({
        id: `${edge.source}-${edge.target}`,
        from: edge.source,
        to: edge.target,
        label: edge.relationship,
        title: `关系: ${edge.relationship}`,
        color: { color: '#848484', highlight: '#333' },
        width: edgeWidth,
        arrows: { to: { enabled: true, scaleFactor: 1 } },
        font: { size: 12, align: 'middle' },
        smooth: { type: 'continuous' }
      }))
    );

    return { nodes, edges };
  };

  // 网络配置
  const getNetworkOptions = () => {
    const baseOptions = {
      layout: {
        improvedLayout: true,
        clusterThreshold: 150,
        hierarchical: layoutType === 'hierarchical' ? {
          enabled: true,
          levelSeparation: 150,
          nodeSpacing: 100,
          treeSpacing: 200,
          blockShifting: true,
          edgeMinimization: true,
          parentCentralization: true,
          direction: 'UD',
          sortMethod: 'directed'
        } : false
      },
      physics: {
        enabled: layoutType === 'force',
        stabilization: { iterations: 100 },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        }
      },
      interaction: {
        hover: true,
        hoverConnectedEdges: true,
        selectConnectedEdges: false,
        tooltipDelay: 200
      },
      nodes: {
        shape: 'dot',
        scaling: {
          min: 10,
          max: 50
        },
        font: {
          size: 14,
          face: 'Tahoma'
        }
      },
      edges: {
        smooth: {
          type: 'continuous',
          roundness: 0.5
        },
        font: {
          size: 12,
          face: 'Tahoma'
        }
      }
    };

    return baseOptions;
  };

  // 初始化网络
  useEffect(() => {
    if (!containerRef.current || !data) return;

    const { nodes, edges } = convertDataForVis(data);
    const options = getNetworkOptions();

    networkRef.current = new Network(containerRef.current, { nodes, edges }, options);

    // 节点点击事件
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = data.nodes.find(n => n.id === nodeId);
        if (nodeData && onNodeClick) {
          onNodeClick(nodeId, nodeData);
        }
      }
    });

    // 双击事件 - 聚焦到节点
    networkRef.current.on('doubleClick', (params) => {
      if (params.nodes.length > 0) {
        networkRef.current?.focus(params.nodes[0], {
          scale: 1.5,
          animation: true
        });
      }
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [data, layoutType, nodeSize, edgeWidth]);

  // 搜索Neo4j图谱
  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    try {
      const response = await fetch(`/api/v1/graph/neo4j/explore?query=${encodeURIComponent(query)}&node_types=${selectedNodeTypes.join(',')}&limit=50`);
      if (response.ok) {
        const searchData = await response.json();
        // 这里需要父组件处理搜索结果
        message.success(`找到 ${searchData.nodes?.length || 0} 个相关节点`);
      }
    } catch (error) {
      message.error('搜索失败');
      console.error('Neo4j搜索错误:', error);
    }
  };

  // 控制按钮
  const renderControls = () => {
    if (!showControls) return null;

    return (
      <Space style={{ marginBottom: 16 }}>
        <Tooltip title="重新布局">
          <Button 
            icon={<ReloadOutlined />} 
            onClick={() => networkRef.current?.redraw()}
          />
        </Tooltip>
        
        <Tooltip title="放大">
          <Button 
            icon={<ZoomInOutlined />} 
            onClick={() => networkRef.current?.moveTo({ scale: (networkRef.current?.getScale() || 1) * 1.2 })}
          />
        </Tooltip>
        
        <Tooltip title="缩小">
          <Button 
            icon={<ZoomOutOutlined />} 
            onClick={() => networkRef.current?.moveTo({ scale: (networkRef.current?.getScale() || 1) * 0.8 })}
          />
        </Tooltip>

        <Select
          value={layoutType}
          onChange={setLayoutType}
          style={{ width: 120 }}
        >
          <Option value="force">力导向</Option>
          <Option value="hierarchical">层次布局</Option>
        </Select>

        <Tooltip title="设置">
          <Button 
            icon={<SettingOutlined />} 
            onClick={() => setShowSettings(!showSettings)}
          />
        </Tooltip>
      </Space>
    );
  };

  // 搜索栏
  const renderSearch = () => {
    if (!showSearch) return null;

    return (
      <div style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', display: 'flex' }}>
          <Search
            placeholder="搜索Neo4j知识图谱..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={handleSearch}
            style={{ flex: 1 }}
            enterButton={<SearchOutlined />}
          />
          <Select
            mode="multiple"
            placeholder="节点类型"
            value={selectedNodeTypes}
            onChange={setSelectedNodeTypes}
            style={{ width: 200 }}
          >
            <Option value="Problem">题目</Option>
            <Option value="Algorithm">算法</Option>
            <Option value="DataStructure">数据结构</Option>
            <Option value="Technique">技巧</Option>
            <Option value="Platform">平台</Option>
          </Select>
        </Space>
      </div>
    );
  };

  // 统计信息
  const renderStats = () => {
    if (!data) return null;

    const nodeTypeStats = data.nodes.reduce((acc, node) => {
      acc[node.type] = (acc[node.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return (
      <div style={{ marginBottom: 16 }}>
        <Space wrap>
          <Tag icon={<NodeIndexOutlined />} color="blue">
            节点: {data.nodes.length}
          </Tag>
          <Tag color="green">
            关系: {data.edges.length}
          </Tag>
          {Object.entries(nodeTypeStats).map(([type, count]) => (
            <Tag key={type} color="default">
              {type}: {count}
            </Tag>
          ))}
        </Space>
      </div>
    );
  };

  return (
    <Card 
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>Neo4j 知识图谱</Title>
          {data?.center_node && (
            <Text type="secondary">中心节点: {data.center_node}</Text>
          )}
        </div>
      }
      style={{ width: '100%' }}
    >
      {renderSearch()}
      {renderStats()}
      {renderControls()}
      
      <div
        ref={containerRef}
        style={{
          height: height,
          width: width,
          border: '1px solid #d9d9d9',
          borderRadius: '6px',
          backgroundColor: '#fafafa'
        }}
      />
      
      {!data && (
        <div style={{ 
          position: 'absolute', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)',
          textAlign: 'center'
        }}>
          <Text type="secondary">暂无图谱数据</Text>
        </div>
      )}
    </Card>
  );
};

export default Neo4jGraphVisualization;
