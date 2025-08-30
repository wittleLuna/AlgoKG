import React, { useEffect, useRef, useState } from 'react';
import { Card, Button, Space, message, Spin, Tag, Divider } from 'antd';
import { NodeIndexOutlined, ReloadOutlined, FullscreenOutlined } from '@ant-design/icons';

interface GraphNode {
  id: string;
  name: string;
  type: string;
  status: 'new' | 'enhanced' | 'existing';
  confidence: number;
  description: string;
  source: string;
  note_id?: string;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
  confidence: number;
  source_note: string;
}

interface IntegrationStats {
  total_entities: number;
  integrated_entities: number;
  new_entities: number;
  enhanced_entities: number;
}

interface EntityDetail {
  entity: any;
  graph_status: string;
  related_concepts: string[];
  integration_path: string[];
}

interface GraphData {
  note_id: string;
  graph_nodes: GraphNode[];
  graph_edges: GraphEdge[];
  integration_stats: IntegrationStats;
  entity_details: EntityDetail[];
  visualization_config: {
    node_colors: Record<string, string>;
    edge_colors: Record<string, string>;
  };
}

interface EntityGraphVisualizationProps {
  noteId: string;
  onClose?: () => void;
}

const EntityGraphVisualization: React.FC<EntityGraphVisualizationProps> = ({ noteId, onClose }) => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const fetchGraphData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/notes/${noteId}/graph`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('获取图谱数据失败');
      }

      const data = await response.json();
      console.log('获取到的图谱数据:', data);
      setGraphData(data);

      // 绘制图谱
      setTimeout(() => drawGraph(data), 100);
    } catch (error: any) {
      console.error('获取图谱数据失败:', error);
      message.error(error.message || '获取图谱数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraphData();
  }, [noteId]);

  const handleReExtractEntities = async () => {
    setExtracting(true);
    try {
      const token = localStorage.getItem('token');
      console.log('开始重新抽取实体，笔记ID:', noteId);

      const response = await fetch(`/api/v1/notes/${noteId}/extract-entities`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '重新抽取实体失败');
      }

      const result = await response.json();
      console.log('重新抽取实体结果:', result);
      message.success(`实体重新抽取成功！提取了 ${result.entity_count} 个实体，${result.relation_count} 个关系`);

      // 重新获取图谱数据
      await fetchGraphData();
    } catch (error: any) {
      console.error('重新抽取实体失败:', error);
      message.error(error.message || '重新抽取实体失败');
    } finally {
      setExtracting(false);
    }
  };

  const drawGraph = (data: GraphData) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 设置画布大小
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const nodes = data.graph_nodes;
    const edges = data.graph_edges;

    console.log('绘制图谱 - 节点数:', nodes.length, '边数:', edges.length);

    if (nodes.length === 0) {
      // 如果没有节点，显示提示信息
      ctx.fillStyle = '#999';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('暂无实体数据', canvas.width / 2, canvas.height / 2);
      return;
    }

    // 简单的力导向布局
    const nodePositions = new Map<string, { x: number; y: number }>();
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 4;

    // 为节点分配位置
    if (nodes.length === 1) {
      // 单个节点放在中心
      nodePositions.set(nodes[0].id, { x: centerX, y: centerY });
    } else {
      // 多个节点围成圆形
      nodes.forEach((node, index) => {
        const angle = (index / nodes.length) * 2 * Math.PI;
        const x = centerX + Math.cos(angle) * radius;
        const y = centerY + Math.sin(angle) * radius;
        nodePositions.set(node.id, { x, y });
      });
    }

    // 绘制边
    edges.forEach(edge => {
      const sourcePos = nodePositions.get(edge.source);
      const targetPos = nodePositions.get(edge.target);

      if (sourcePos && targetPos) {
        // 根据关系类型设置不同的样式
        const isInternal = edge.source_note === `note_${noteId}`;
        ctx.strokeStyle = isInternal ? '#722ed1' : '#eb2f96';
        ctx.lineWidth = isInternal ? 3 : 2;
        ctx.setLineDash(isInternal ? [] : [5, 5]);

        ctx.beginPath();
        ctx.moveTo(sourcePos.x, sourcePos.y);
        ctx.lineTo(targetPos.x, targetPos.y);
        ctx.stroke();

        // 重置线条样式
        ctx.setLineDash([]);

        // 绘制边标签
        const midX = (sourcePos.x + targetPos.x) / 2;
        const midY = (sourcePos.y + targetPos.y) / 2;
        ctx.fillStyle = '#666';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(edge.type, midX, midY - 5);

        // 绘制置信度
        if (edge.confidence < 1) {
          ctx.fillStyle = '#999';
          ctx.font = '10px Arial';
          ctx.fillText(`${Math.round(edge.confidence * 100)}%`, midX, midY + 10);
        }
      }
    });

    // 绘制节点
    nodes.forEach(node => {
      const pos = nodePositions.get(node.id);
      if (!pos) return;

      // 节点颜色和大小
      const color = data.visualization_config.node_colors[node.status] || '#ccc';
      const radius = node.source === 'note' ? 35 : 25; // 来自笔记的节点更大

      // 绘制节点阴影
      ctx.beginPath();
      ctx.arc(pos.x + 2, pos.y + 2, radius, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
      ctx.fill();

      // 绘制节点圆圈
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 3;
      ctx.stroke();

      // 绘制状态指示器
      if (node.status === 'new') {
        ctx.beginPath();
        ctx.arc(pos.x + radius - 8, pos.y - radius + 8, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#52c41a';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
      } else if (node.status === 'enhanced') {
        ctx.beginPath();
        ctx.arc(pos.x + radius - 8, pos.y - radius + 8, 6, 0, 2 * Math.PI);
        ctx.fillStyle = '#1890ff';
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // 绘制节点标签
      ctx.fillStyle = '#000';
      ctx.font = 'bold 14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(node.name, pos.x, pos.y + radius + 20);

      // 绘制置信度
      if (node.confidence < 1) {
        ctx.fillStyle = '#999';
        ctx.font = '10px Arial';
        ctx.fillText(`${Math.round(node.confidence * 100)}%`, pos.x, pos.y + radius + 35);
      }
    });
  };

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!graphData) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // 检查点击的节点
    const nodes = graphData.graph_nodes;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 3;

    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      const angle = (i / nodes.length) * 2 * Math.PI;
      const nodeX = centerX + Math.cos(angle) * radius;
      const nodeY = centerY + Math.sin(angle) * radius;

      const distance = Math.sqrt((x - nodeX) ** 2 + (y - nodeY) ** 2);
      if (distance <= 30) {
        setSelectedNode(node);
        break;
      }
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      'new': 'green',
      'enhanced': 'blue',
      'existing': 'orange'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts = {
      'new': '新增实体',
      'enhanced': '增强实体',
      'existing': '已存在'
    };
    return texts[status as keyof typeof texts] || status;
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <NodeIndexOutlined />
              <span>实体知识图谱集成</span>
            </div>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchGraphData}
                loading={loading}
              >
                刷新图谱
              </Button>
              <Button
                type="primary"
                loading={extracting}
                onClick={handleReExtractEntities}
              >
                重新抽取实体
              </Button>
              <Button
                onClick={() => {
                  // 这里可以跳转到完整的知识图谱页面
                  message.info('完整知识图谱功能开发中...');
                }}
              >
                查看完整图谱
              </Button>
              {onClose && (
                <Button onClick={onClose}>
                  关闭
                </Button>
              )}
            </Space>
          </div>
        }
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column' }}
      >
        <Spin spinning={loading}>
          {graphData && (
            <div style={{ flex: 1, display: 'flex', gap: '16px' }}>
              {/* 图谱可视化区域 */}
              <div style={{ flex: 2, display: 'flex', flexDirection: 'column' }}>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>知识图谱集成统计：</strong>
                  </div>
                  <Space wrap>
                    <Tag color="green">新增实体: {graphData.integration_stats.new_entities}</Tag>
                    <Tag color="blue">增强实体: {graphData.integration_stats.enhanced_entities}</Tag>
                    <Tag color="orange">总实体: {graphData.integration_stats.total_entities}</Tag>
                    <Tag color="purple">集成实体: {graphData.integration_stats.integrated_entities}</Tag>
                  </Space>
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                    💡 绿色表示新加入知识图谱的实体，蓝色表示增强了现有图谱实体
                  </div>
                </div>
                
                <canvas
                  ref={canvasRef}
                  style={{
                    flex: 1,
                    border: '1px solid #d9d9d9',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    minHeight: '400px'
                  }}
                  onClick={handleCanvasClick}
                />
              </div>

              {/* 实体详情面板 */}
              <div style={{ flex: 1, maxWidth: '300px' }}>
                <Card size="small" title="实体详情">
                  {selectedNode ? (
                    <div>
                      <div style={{ marginBottom: '12px' }}>
                        <strong>{selectedNode.name}</strong>
                        <div style={{ marginTop: '4px' }}>
                          <Tag color={getStatusColor(selectedNode.status)}>
                            {getStatusText(selectedNode.status)}
                          </Tag>
                        </div>
                      </div>
                      
                      <div style={{ marginBottom: '8px' }}>
                        <strong>类型:</strong> {selectedNode.type}
                      </div>
                      
                      <div style={{ marginBottom: '8px' }}>
                        <strong>置信度:</strong> {Math.round(selectedNode.confidence * 100)}%
                      </div>
                      
                      {selectedNode.description && (
                        <div style={{ marginBottom: '8px' }}>
                          <strong>描述:</strong> {selectedNode.description}
                        </div>
                      )}
                      
                      <div style={{ marginBottom: '8px' }}>
                        <strong>来源:</strong> {selectedNode.source === 'note' ? '笔记' : '知识图谱'}
                      </div>

                      <div style={{ marginBottom: '8px' }}>
                        <strong>图谱状态:</strong>
                        <div style={{ marginTop: '4px' }}>
                          <Tag color={getStatusColor(selectedNode.status)}>
                            {getStatusText(selectedNode.status)}
                          </Tag>
                          {selectedNode.status === 'enhanced' && (
                            <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
                              此实体已存在于知识图谱中，通过此笔记得到了增强
                            </div>
                          )}
                          {selectedNode.status === 'new' && (
                            <div style={{ fontSize: '12px', color: '#666', marginTop: '2px' }}>
                              此实体是通过此笔记新加入知识图谱的
                            </div>
                          )}
                        </div>
                      </div>

                      {/* 显示相关概念和集成路径 */}
                      {graphData.entity_details.map((detail, index) => {
                        if (detail.entity.id === selectedNode.id) {
                          return (
                            <div key={index}>
                              {detail.related_concepts.length > 0 && (
                                <div style={{ marginBottom: '8px' }}>
                                  <strong>相关概念:</strong>
                                  <div style={{ marginTop: '4px' }}>
                                    {detail.related_concepts.map((concept, i) => (
                                      <Tag key={i} size="small">{concept}</Tag>
                                    ))}
                                  </div>
                                </div>
                              )}
                              
                              {detail.integration_path.length > 0 && (
                                <div>
                                  <strong>集成路径:</strong>
                                  <div style={{ marginTop: '4px' }}>
                                    {detail.integration_path.join(' → ')}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        }
                        return null;
                      })}
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                      点击图谱中的节点查看详情
                    </div>
                  )}
                </Card>
              </div>
            </div>
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default EntityGraphVisualization;
