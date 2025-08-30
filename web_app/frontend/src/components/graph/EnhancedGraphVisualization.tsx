import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Card, Typography, Button, Space, Tooltip, Select, Slider, Switch, Drawer, List, Tag } from 'antd';
import { 
  FullscreenOutlined, 
  ReloadOutlined, 
  SettingOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { GraphVisualizationProps, GraphNode, GraphEdge } from '../../types';

const { Title, Text } = Typography;
const { Option } = Select;

interface EnhancedGraphVisualizationProps extends GraphVisualizationProps {
  showAnimation?: boolean;
  showMiniMap?: boolean;
  enableClustering?: boolean;
  layoutType?: 'force' | 'hierarchical' | 'circular';
  onPathHighlight?: (path: string[]) => void;
  disableBuiltinNodeInfo?: boolean; // 禁用内置的节点信息面板
}

const EnhancedGraphVisualization: React.FC<EnhancedGraphVisualizationProps> = ({
  data,
  onNodeClick,
  height = 500,
  width,
  layoutType = 'force',
  showAnimation = true,
  showMiniMap = false,
  enableClustering = false,
  onPathHighlight,
  disableBuiltinNodeInfo = false
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showNodeInfo, setShowNodeInfo] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  
  // 可视化设置
  const [currentLayoutType, setCurrentLayoutType] = useState(layoutType);
  const [nodeSize, setNodeSize] = useState(25);
  const [edgeWidth, setEdgeWidth] = useState(2);
  const [physicsEnabled, setPhysicsEnabled] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [nodeFilter, setNodeFilter] = useState<string[]>([]);
  const [edgeFilter, setEdgeFilter] = useState<string[]>([]);
  
  // 动画状态
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationSpeed, setAnimationSpeed] = useState(1000);
  
  // 统计信息
  const [graphStats, setGraphStats] = useState({
    nodeCount: 0,
    edgeCount: 0,
    nodeTypes: [] as string[],
    edgeTypes: [] as string[]
  });

  // 节点类型颜色映射（增强版）
  const getNodeColor = (type: string, isCenter: boolean = false, isHighlighted: boolean = false) => {
    if (isHighlighted) {
      return {
        background: '#ff4d4f',
        border: '#cf1322',
        highlight: { background: '#ff7875', border: '#cf1322' }
      };
    }

    if (isCenter) {
      return {
        background: '#722ed1',
        border: '#531dab',
        highlight: { background: '#9254de', border: '#531dab' }
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
        background: '#fa8c16',
        border: '#d46b08',
        highlight: { background: '#ffa940', border: '#d46b08' }
      },
      'Technique': {
        background: '#13c2c2',
        border: '#08979c',
        highlight: { background: '#36cfc9', border: '#08979c' }
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

  // 关系类型样式映射（增强版）
  const getEdgeStyle = (relationship: string, isHighlighted: boolean = false) => {
    const baseStyle = {
      'USES_ALGORITHM': { color: '#52c41a', dashes: false, width: 2 },
      'REQUIRES_DATA_STRUCTURE': { color: '#fa8c16', dashes: false, width: 2 },
      'APPLIES_TECHNIQUE': { color: '#13c2c2', dashes: false, width: 2 },
      'SIMILAR_TO': { color: '#1890ff', dashes: [5, 5], width: 1 },
      'RELATED_TO': { color: '#8c8c8c', dashes: [2, 2], width: 1 },
      'PREREQUISITE_OF': { color: '#ff4d4f', dashes: false, width: 3 },
      'EXTENDS': { color: '#722ed1', dashes: [10, 5], width: 2 }
    };

    const style = baseStyle[relationship as keyof typeof baseStyle] || { color: '#8c8c8c', dashes: false, width: 1 };
    
    if (isHighlighted) {
      return {
        ...style,
        color: '#ff4d4f',
        width: style.width * 2
      };
    }

    return style;
  };

  // 转换数据格式（增强版）
  const convertData = useCallback(() => {
    if (!data || !data.nodes || !data.edges) {
      return { nodes: new DataSet([]), edges: new DataSet([]) };
    }

    // 过滤节点
    const filteredNodes = data.nodes.filter(node => 
      nodeFilter.length === 0 || nodeFilter.includes(node.type)
    );

    // 过滤边
    const filteredEdges = data.edges.filter(edge => 
      edgeFilter.length === 0 || edgeFilter.includes(edge.relationship)
    );

    const nodes = filteredNodes.map((node: GraphNode) => {
      const isCenter = node.properties?.is_center || false;
      const isHighlighted = selectedNode?.id === node.id;
      const color = getNodeColor(node.type, isCenter, isHighlighted);
      
      return {
        id: node.id,
        label: showLabels ? node.label : '',
        title: `${node.type}: ${node.label}${isCenter ? ' (中心节点)' : ''}`,
        color,
        size: isCenter ? nodeSize * 1.5 : nodeSize,
        font: {
          size: isCenter ? 16 : 14,
          color: '#ffffff',
          strokeWidth: 2,
          strokeColor: '#000000'
        },
        borderWidth: isHighlighted ? 4 : 2,
        shape: getNodeShape(node.type),
        clickable: node.clickable,
        physics: physicsEnabled,
        // 添加自定义属性
        group: node.type,
        level: node.properties?.level || 0
      };
    });

    const edges = filteredEdges.map((edge: GraphEdge) => {
      const isHighlighted = selectedNode && (
        selectedNode.id === edge.source || selectedNode.id === edge.target
      );
      const style = getEdgeStyle(edge.relationship, isHighlighted);
      
      return {
        id: `${edge.source}-${edge.target}`,
        from: edge.source,
        to: edge.target,
        label: showLabels ? edge.relationship : '',
        color: style.color,
        width: (style.width || 1) * edgeWidth,
        dashes: style.dashes,
        arrows: { to: { enabled: true, scaleFactor: 1.2 } },
        font: { size: 10, align: 'middle' },
        smooth: { type: 'continuous', roundness: 0.5 },
        physics: physicsEnabled
      };
    });

    // 更新统计信息
    setGraphStats({
      nodeCount: nodes.length,
      edgeCount: edges.length,
      nodeTypes: Array.from(new Set(data.nodes.map(n => n.type))),
      edgeTypes: Array.from(new Set(data.edges.map(e => e.relationship)))
    });

    return {
      nodes: new DataSet(nodes),
      edges: new DataSet(edges)
    };
  }, [data, nodeFilter, edgeFilter, nodeSize, edgeWidth, physicsEnabled, showLabels, selectedNode]);

  // 获取节点形状
  const getNodeShape = (type: string) => {
    const shapeMap: Record<string, string> = {
      'Problem': 'box',
      'Algorithm': 'ellipse',
      'DataStructure': 'diamond',
      'Technique': 'triangle',
      'Concept': 'dot'
    };
    return shapeMap[type] || 'dot';
  };

  // 网络配置选项（增强版）
  const getNetworkOptions = useCallback(() => {
    const baseOptions = {
      physics: {
        enabled: physicsEnabled,
        stabilization: { iterations: 200 },
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 120,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        },
        solver: 'barnesHut'
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        hideEdgesOnDrag: false,
        hideNodesOnDrag: false,
        selectConnectedEdges: true,
        multiselect: true
      },
      nodes: {
        borderWidth: 2,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.2)',
          size: 5,
          x: 2,
          y: 2
        },
        font: {
          size: 14,
          color: '#ffffff',
          strokeWidth: 2,
          strokeColor: '#000000'
        }
      },
      edges: {
        width: edgeWidth,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.1)',
          size: 3,
          x: 1,
          y: 1
        },
        smooth: {
          type: 'continuous',
          roundness: 0.5
        }
      },
      groups: {
        Problem: { color: { background: '#1890ff' } },
        Algorithm: { color: { background: '#52c41a' } },
        DataStructure: { color: { background: '#fa8c16' } },
        Technique: { color: { background: '#13c2c2' } },
        Concept: { color: { background: '#eb2f96' } }
      }
    };

    // 根据布局类型添加特定配置
    if (currentLayoutType === 'hierarchical') {
      return {
        ...baseOptions,
        layout: {
          hierarchical: {
            enabled: true,
            direction: 'UD',
            sortMethod: 'directed',
            nodeSpacing: 200,
            levelSeparation: 200,
            treeSpacing: 250
          }
        },
        physics: {
          enabled: false
        }
      };
    } else if (currentLayoutType === 'force') {
      return {
        ...baseOptions,
        layout: {
          randomSeed: 2,
          improvedLayout: true
        }
      };
    } else if (currentLayoutType === 'circular') {
      return {
        ...baseOptions,
        layout: {
          randomSeed: undefined
        },
        physics: {
          enabled: false
        }
      };
    }

    return baseOptions;
  }, [currentLayoutType, physicsEnabled, edgeWidth]);

  // 初始化网络（增强版）
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
        if (node) {
          // 只有在未禁用内置节点信息时才显示
          if (!disableBuiltinNodeInfo) {
            setSelectedNode(node);
            setShowNodeInfo(true);
          }

          // 总是调用外部的onNodeClick回调
          if (node.clickable && onNodeClick) {
            onNodeClick(node);
          }
        }
      } else {
        setSelectedNode(null);
        setShowNodeInfo(false);
      }
    });

    networkRef.current.on('hoverNode', (params) => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'pointer';
      }
      // 高亮连接的节点和边
      const connectedNodes = networkRef.current?.getConnectedNodes(params.node);
      const connectedEdges = networkRef.current?.getConnectedEdges(params.node);
      
      if (connectedNodes && connectedEdges) {
        // 可以在这里实现高亮效果
      }
    });

    networkRef.current.on('blurNode', () => {
      if (containerRef.current) {
        containerRef.current.style.cursor = 'default';
      }
    });

    // 稳定化完成后的回调
    networkRef.current.on('stabilizationIterationsDone', () => {
      if (showAnimation && !isAnimating) {
        startAnimation();
      }
    });

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [data, convertData, getNetworkOptions, showAnimation, isAnimating]);

  // 动画控制
  const startAnimation = () => {
    if (!networkRef.current) return;
    
    setIsAnimating(true);
    // 实现节点动画效果
    const nodes = networkRef.current.body.data.nodes.get();
    let index = 0;
    
    const animateNode = () => {
      if (index < nodes.length && networkRef.current) {
        const node = nodes[index];

        try {
          // 检查节点是否存在
          const allNodes = networkRef.current.body.data.nodes.get();
          const nodeExists = allNodes.some((n: any) => n.id === node.id);

          if (nodeExists) {
            networkRef.current.selectNodes([node.id]);
          }

          setTimeout(() => {
            if (networkRef.current) {
              networkRef.current.unselectAll();
            }
            index++;
            if (index < nodes.length) {
              animateNode();
            } else {
              setIsAnimating(false);
            }
          }, animationSpeed);
        } catch (error) {
          console.warn('动画节点选择失败:', error);
          // 跳过这个节点，继续下一个
          index++;
          if (index < nodes.length) {
            animateNode();
          } else {
            setIsAnimating(false);
          }
        }
      }
    };
    
    animateNode();
  };

  const stopAnimation = () => {
    setIsAnimating(false);
  };

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

  // 查找最短路径
  const findShortestPath = (startNodeId: string, endNodeId: string) => {
    if (!networkRef.current) return [];
    
    // 简单的BFS实现
    const visited = new Set();
    const queue = [[startNodeId]];
    
    while (queue.length > 0) {
      const path = queue.shift()!;
      const node = path[path.length - 1];
      
      if (node === endNodeId) {
        return path;
      }
      
      if (!visited.has(node)) {
        visited.add(node);
        const neighbors = networkRef.current.getConnectedNodes(node);
        
        for (const neighbor of neighbors) {
          if (!visited.has(neighbor)) {
            queue.push([...path, neighbor]);
          }
        }
      }
    }
    
    return [];
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
    <>
      <Card
        className={`enhanced-graph-visualization ${isFullscreen ? 'fullscreen' : ''}`}
        title={
          <div className="graph-header">
            <Space>
              <Title level={5} style={{ margin: 0 }}>
                🕸️ 知识图谱
              </Title>
              <Tag color="blue">{graphStats.nodeCount} 节点</Tag>
              <Tag color="green">{graphStats.edgeCount} 关系</Tag>
            </Space>
            
            <Space>
              {showAnimation && (
                <Tooltip title={isAnimating ? "停止动画" : "开始动画"}>
                  <Button 
                    type="text" 
                    icon={isAnimating ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                    onClick={isAnimating ? stopAnimation : startAnimation}
                  />
                </Tooltip>
              )}
              <Tooltip title="放大">
                <Button type="text" icon={<ZoomInOutlined />} onClick={handleZoomIn} />
              </Tooltip>
              <Tooltip title="缩小">
                <Button type="text" icon={<ZoomOutOutlined />} onClick={handleZoomOut} />
              </Tooltip>
              <Tooltip title="重置视图">
                <Button type="text" icon={<ReloadOutlined />} onClick={handleReset} />
              </Tooltip>
              <Tooltip title="过滤">
                <Button 
                  type="text" 
                  icon={<FilterOutlined />} 
                  onClick={() => setShowSettings(!showSettings)}
                />
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
      >
        <div
          ref={containerRef}
          className="graph-container"
          style={{
            height: isFullscreen ? '80vh' : height || '100%',
            width: width || '100%',
            minHeight: '600px',
            border: '1px solid #d9d9d9',
            borderRadius: '6px',
            background: 'linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%)'
          }}
        />

        {/* 图例 */}
        <div className="enhanced-graph-legend">
          <Space wrap>
            {graphStats.nodeTypes.map(type => (
              <div key={type} className="legend-item">
                <div 
                  className="legend-color" 
                  style={{ 
                    background: getNodeColor(type).background,
                    borderRadius: getNodeShape(type) === 'box' ? '2px' : '50%'
                  }} 
                />
                <Text>{type}</Text>
              </div>
            ))}
          </Space>
        </div>
      </Card>

      {/* 设置面板 */}
      <Drawer
        title="图谱设置"
        placement="right"
        onClose={() => setShowSettings(false)}
        open={showSettings}
        width={320}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong>布局类型</Text>
            <Select
              value={currentLayoutType}
              onChange={setCurrentLayoutType}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Option value="hierarchical">层次布局</Option>
              <Option value="force">力导向布局</Option>
              <Option value="circular">环形布局</Option>
            </Select>
          </div>

          <div>
            <Text strong>节点大小: {nodeSize}</Text>
            <Slider
              min={15}
              max={50}
              value={nodeSize}
              onChange={setNodeSize}
              style={{ marginTop: 8 }}
            />
          </div>

          <div>
            <Text strong>边宽度: {edgeWidth}</Text>
            <Slider
              min={1}
              max={5}
              value={edgeWidth}
              onChange={setEdgeWidth}
              style={{ marginTop: 8 }}
            />
          </div>

          <div>
            <Space>
              <Text strong>物理引擎</Text>
              <Switch
                checked={physicsEnabled}
                onChange={setPhysicsEnabled}
              />
            </Space>
          </div>

          <div>
            <Space>
              <Text strong>显示标签</Text>
              <Switch
                checked={showLabels}
                onChange={setShowLabels}
              />
            </Space>
          </div>

          {showAnimation && (
            <div>
              <Text strong>动画速度: {animationSpeed}ms</Text>
              <Slider
                min={200}
                max={2000}
                value={animationSpeed}
                onChange={setAnimationSpeed}
                style={{ marginTop: 8 }}
              />
            </div>
          )}

          <div>
            <Text strong>节点类型过滤</Text>
            <Select
              mode="multiple"
              placeholder="选择要显示的节点类型"
              value={nodeFilter}
              onChange={setNodeFilter}
              style={{ width: '100%', marginTop: 8 }}
            >
              {graphStats.nodeTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </div>

          <div>
            <Text strong>关系类型过滤</Text>
            <Select
              mode="multiple"
              placeholder="选择要显示的关系类型"
              value={edgeFilter}
              onChange={setEdgeFilter}
              style={{ width: '100%', marginTop: 8 }}
            >
              {graphStats.edgeTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </div>
        </Space>
      </Drawer>

      {/* 节点信息面板 - 只在未禁用时显示 */}
      {!disableBuiltinNodeInfo && (
        <Drawer
          title="节点详情"
          placement="right"
          onClose={() => setShowNodeInfo(false)}
          open={showNodeInfo}
          width={400}
        >
          {selectedNode && (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Title level={4}>{selectedNode.label}</Title>
                <Tag color="blue">{selectedNode.type}</Tag>
              </div>

              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <Text strong>属性信息</Text>
                  <List
                    size="small"
                    dataSource={Object.entries(selectedNode.properties)}
                    renderItem={([key, value]) => (
                      <List.Item>
                        <Text strong>{key}:</Text> {String(value)}
                      </List.Item>
                    )}
                  />
                </div>
              )}

              <div>
                <Text strong>连接信息</Text>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">
                    该节点与 {networkRef.current?.getConnectedNodes(selectedNode.id)?.length || 0} 个节点相连
                  </Text>
                </div>
              </div>
            </Space>
          )}
        </Drawer>
      )}

      <style jsx>{`
        .enhanced-graph-visualization {
          position: relative;
          border-radius: 12px;
          overflow: visible;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .enhanced-graph-visualization.fullscreen {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          background: white;
          border-radius: 0;
        }

        .graph-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .graph-container {
          position: relative;
          overflow: visible;
        }

        .enhanced-graph-legend {
          margin-top: 16px;
          padding: 12px;
          background: rgba(24, 144, 255, 0.05);
          border-radius: 8px;
          border-left: 4px solid #1890ff;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .legend-color {
          width: 16px;
          height: 16px;
          border: 2px solid #fff;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
        }

        @media (max-width: 768px) {
          .graph-header {
            flex-direction: column;
            gap: 8px;
          }
        }
      `}</style>
    </>
  );
};

export default EnhancedGraphVisualization;
