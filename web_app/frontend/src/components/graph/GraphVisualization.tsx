import React, { useEffect, useRef, useState } from 'react';
import { Card, Typography, Button, Space, Tooltip, Select, Slider } from 'antd';
import { 
  FullscreenOutlined, 
  ReloadOutlined, 
  SettingOutlined,
  ZoomInOutlined,
  ZoomOutOutlined 
} from '@ant-design/icons';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { GraphVisualizationProps, GraphNode, GraphEdge } from '../../types';

const { Title, Text } = Typography;
const { Option } = Select;

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  data,
  onNodeClick,
  height = 400,
  width
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [layoutType, setLayoutType] = useState('hierarchical');
  const [nodeSize, setNodeSize] = useState(25);
  const [edgeWidth, setEdgeWidth] = useState(2);

  // 节点类型颜色映射
  const getNodeColor = (type: string, isCenter: boolean = false) => {
    if (isCenter) {
      return {
        background: '#ff4d4f',
        border: '#cf1322',
        highlight: { background: '#ff7875', border: '#cf1322' }
      };
    }

    const colorMap: Record<string, any> = {
      'Problem': {
        background: '#1890ff',
        border: '#096dd9',
        highlight: { background: '#40a9ff', border: '#096dd9' }
      },
      'Algorithm': {
        background: '#52c41a',
        border: '#389e0d',
        highlight: { background: '#73d13d', border: '#389e0d' }
      },
      'DataStructure': {
        background: '#722ed1',
        border: '#531dab',
        highlight: { background: '#9254de', border: '#531dab' }
      },
      'Technique': {
        background: '#fa8c16',
        border: '#d46b08',
        highlight: { background: '#ffa940', border: '#d46b08' }
      },
      'Concept': {
        background: '#eb2f96',
        border: '#c41d7f',
        highlight: { background: '#f759ab', border: '#c41d7f' }
      }
    };

    return colorMap[type] || {
      background: '#8c8c8c',
      border: '#595959',
      highlight: { background: '#bfbfbf', border: '#595959' }
    };
  };

  // 关系类型样式映射
  const getEdgeStyle = (relationship: string) => {
    const styleMap: Record<string, any> = {
      'USES_ALGORITHM': { color: '#52c41a', dashes: false },
      'REQUIRES_DATA_STRUCTURE': { color: '#722ed1', dashes: false },
      'APPLIES_TECHNIQUE': { color: '#fa8c16', dashes: false },
      'SIMILAR_TO': { color: '#1890ff', dashes: [5, 5] },
      'RELATED_TO': { color: '#8c8c8c', dashes: [2, 2] },
      'PREREQUISITE_OF': { color: '#ff4d4f', dashes: false }
    };

    return styleMap[relationship] || { color: '#8c8c8c', dashes: false };
  };

  // 转换数据格式
  const convertData = () => {
    if (!data || !data.nodes || !data.edges) {
      return { nodes: new DataSet([]), edges: new DataSet([]) };
    }

    const nodes = data.nodes.map((node: GraphNode) => {
      const isCenter = node.properties?.is_center || false;
      const color = getNodeColor(node.type, isCenter);
      
      return {
        id: node.id,
        label: node.label,
        title: `${node.type}: ${node.label}${isCenter ? ' (中心节点)' : ''}`,
        color,
        size: isCenter ? nodeSize * 1.5 : nodeSize,
        font: {
          size: isCenter ? 16 : 14,
          color: '#ffffff',
          strokeWidth: 2,
          strokeColor: '#000000'
        },
        borderWidth: 2,
        shape: node.type === 'Problem' ? 'box' : 'dot',
        clickable: node.clickable
      };
    });

    const edges = data.edges.map((edge: GraphEdge) => {
      const style = getEdgeStyle(edge.relationship);
      
      return {
        id: `${edge.source}-${edge.target}`,
        from: edge.source,
        to: edge.target,
        label: edge.relationship,
        color: style.color,
        width: edgeWidth,
        dashes: style.dashes,
        arrows: { to: { enabled: true, scaleFactor: 1 } },
        font: { size: 12, align: 'middle' },
        smooth: { type: 'continuous' }
      };
    });

    return {
      nodes: new DataSet(nodes),
      edges: new DataSet(edges)
    };
  };

  // 网络配置选项
  const getNetworkOptions = () => {
    const baseOptions = {
      physics: {
        enabled: true,
        stabilization: { iterations: 100 },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        hideEdgesOnDrag: false,
        hideNodesOnDrag: false
      },
      nodes: {
        borderWidth: 2,
        shadow: true,
        font: {
          size: 14,
          color: '#ffffff',
          strokeWidth: 2,
          strokeColor: '#000000'
        }
      },
      edges: {
        width: edgeWidth,
        shadow: true,
        smooth: {
          type: 'continuous',
          roundness: 0.5
        }
      }
    };

    // 根据布局类型添加特定配置
    if (layoutType === 'hierarchical') {
      return {
        ...baseOptions,
        layout: {
          hierarchical: {
            enabled: true,
            direction: 'UD',
            sortMethod: 'directed',
            nodeSpacing: 150,
            levelSeparation: 150
          }
        },
        physics: {
          enabled: false
        }
      };
    } else if (layoutType === 'force') {
      return {
        ...baseOptions,
        layout: {
          randomSeed: 2
        }
      };
    } else {
      return {
        ...baseOptions,
        layout: {
          randomSeed: undefined
        }
      };
    }
  };

  // 初始化网络
  useEffect(() => {
    if (!containerRef.current || !data) return;

    const networkData = convertData();
    const options = getNetworkOptions();

    networkRef.current = new Network(containerRef.current, networkData, options);

    // 添加事件监听器
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = data.nodes.find(n => n.id === nodeId);
        if (node && node.clickable && onNodeClick) {
          onNodeClick(node);
        }
      }
    });

    networkRef.current.on('hoverNode', () => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'pointer';
      }
    });

    networkRef.current.on('blurNode', () => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default';
      }
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [data, layoutType, nodeSize, edgeWidth]);

  // 控制函数
  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale() * 1.2;
      networkRef.current.moveTo({ scale });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale() * 0.8;
      networkRef.current.moveTo({ scale });
    }
  };

  const handleReset = () => {
    if (networkRef.current) {
      networkRef.current.fit();
    }
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <Card className="graph-placeholder">
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Text type="secondary">暂无图谱数据</Text>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className={`graph-visualization ${isFullscreen ? 'fullscreen' : ''}`}
      title={
        <div className="graph-header">
          <Title level={5} style={{ margin: 0 }}>
            🕸️ 知识图谱
          </Title>
          <Space>
            <Tooltip title="放大">
              <Button type="text" icon={<ZoomInOutlined />} onClick={handleZoomIn} />
            </Tooltip>
            <Tooltip title="缩小">
              <Button type="text" icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
            </Tooltip>
            <Tooltip title="重置视图">
              <Button type="text" icon={<ReloadOutlined />} onClick={handleReset} />
            </Tooltip>
            <Tooltip title="设置">
              <Button 
                type="text" 
                icon={<SettingOutlined />} 
                onClick={() => setShowSettings(!showSettings)}
              />
            </Tooltip>
            <Tooltip title="全屏">
              <Button type="text" icon={<FullscreenOutlined />} onClick={handleFullscreen} />
            </Tooltip>
          </Space>
        </div>
      }
      extra={
        showSettings && (
          <div className="graph-settings">
            <Space direction="vertical" size="small">
              <div>
                <Text strong>布局类型:</Text>
                <Select
                  value={layoutType}
                  onChange={setLayoutType}
                  style={{ width: 120, marginLeft: 8 }}
                  size="small"
                >
                  <Option value="hierarchical">层次布局</Option>
                  <Option value="force">力导向布局</Option>
                  <Option value="random">随机布局</Option>
                </Select>
              </div>
              <div>
                <Text strong>节点大小:</Text>
                <Slider
                  min={15}
                  max={40}
                  value={nodeSize}
                  onChange={setNodeSize}
                  style={{ width: 100, marginLeft: 8 }}
                />
              </div>
              <div>
                <Text strong>边宽度:</Text>
                <Slider
                  min={1}
                  max={5}
                  value={edgeWidth}
                  onChange={setEdgeWidth}
                  style={{ width: 100, marginLeft: 8 }}
                />
              </div>
            </Space>
          </div>
        )
      }
    >
      <div
        ref={containerRef}
        className="graph-container"
        style={{
          height: isFullscreen ? '80vh' : height,
          width: width || '100%',
          border: '1px solid #d9d9d9',
          borderRadius: '6px'
        }}
      />

      {/* 图例 */}
      <div className="graph-legend">
        <Space wrap>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#1890ff' }} />
            <Text>题目</Text>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#52c41a' }} />
            <Text>算法</Text>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#722ed1' }} />
            <Text>数据结构</Text>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#fa8c16' }} />
            <Text>技巧</Text>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ff4d4f' }} />
            <Text>中心节点</Text>
          </div>
        </Space>
      </div>

      <style jsx>{`
        .graph-visualization {
          position: relative;
        }

        .graph-visualization.fullscreen {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          background: white;
        }

        .graph-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .graph-settings {
          position: absolute;
          top: 60px;
          right: 16px;
          background: white;
          padding: 12px;
          border-radius: 6px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          z-index: 10;
        }

        .graph-container {
          background: #fafafa;
        }

        .graph-legend {
          margin-top: 12px;
          padding: 8px;
          background: #f5f5f5;
          border-radius: 4px;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .legend-color {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .graph-placeholder {
          min-height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        @media (max-width: 768px) {
          .graph-header {
            flex-direction: column;
            gap: 8px;
          }

          .graph-settings {
            position: relative;
            top: 0;
            right: 0;
            margin-top: 12px;
          }
        }
      `}</style>
    </Card>
  );
};

export default GraphVisualization;
