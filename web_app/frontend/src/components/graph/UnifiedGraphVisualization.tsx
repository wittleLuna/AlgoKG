import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Typography, 
  Button, 
  Space, 
  Tooltip, 
  Select, 
  Input, 
  Tag, 
  message,
  Switch,
  Row,
  Col,
  Spin,
  Drawer
} from 'antd';
import {
  NodeIndexOutlined,
  SearchOutlined,
  SettingOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  MessageOutlined,
  BulbOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { GraphData, GraphNode } from '../../types';
import EnhancedGraphVisualization from './EnhancedGraphVisualization';
const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

interface UnifiedGraphVisualizationProps {
  data?: GraphData;
  onNodeClick?: (nodeId: string, nodeData: GraphNode) => void;
  height?: number | string;
  showControls?: boolean;
  defaultDataSources?: string[];
  showAnimation?: boolean; // 是否显示动画
  disableBuiltinNodeDetail?: boolean; // 是否禁用UnifiedGraphVisualization的节点详情功能
  disableEnhancedNodeInfo?: boolean; // 是否禁用EnhancedGraphVisualization的节点信息面板
}

interface DataSourceConfig {
  key: string;
  label: string;
  icon: React.ReactNode;
  description: string;
  enabled: boolean;
}

const UnifiedGraphVisualization: React.FC<UnifiedGraphVisualizationProps> = ({
  data,
  onNodeClick,
  height = 600,
  showControls = true,
  defaultDataSources = ['neo4j'],
  showAnimation = true,
  disableBuiltinNodeDetail = false,
  disableEnhancedNodeInfo = false
}) => {
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<GraphData | undefined>(data);
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>(defaultDataSources);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [nodeDetails, setNodeDetails] = useState<any>(null);
  const [showNodeDetails, setShowNodeDetails] = useState(false);

  // 数据源配置
  const [dataSources, setDataSources] = useState<DataSourceConfig[]>([
    {
      key: 'neo4j',
      label: 'Neo4j图谱',
      icon: <MessageOutlined />,
      description: '基于Neo4j数据库的实时知识图谱',
      enabled: true
    },
    {
      key: 'embedding',
      label: '智能推荐',
      icon: <BulbOutlined />,
      description: '基于embedding的智能题目推荐图谱',
      enabled: false
    },
    {
      key: 'static',
      label: '静态图谱',
      icon: <FilterOutlined />,
      description: '预定义的静态知识图谱',
      enabled: false
    }
  ]);

  // 更新图谱数据
  useEffect(() => {
    setGraphData(data);
  }, [data]);

  // 查询统一图谱
  const queryUnifiedGraph = useCallback(async (query: string, sources: string[]) => {
    if (!query.trim()) {
      message.warning('请输入查询关键词');
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        entity_name: query,
        depth: '2',
        limit: '50'
      });
      
      // 添加数据源参数
      sources.forEach(source => {
        params.append('data_sources', source);
      });

      const response = await fetch(`/api/v1/graph/unified/query?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_name: query,
          depth: 2,
          limit: 50
        })
      });

      if (response.ok) {
        const result = await response.json();
        setGraphData(result);
        message.success(`查询成功，找到 ${result.nodes?.length || 0} 个节点`);
      } else {
        throw new Error(`查询失败: ${response.statusText}`);
      }
    } catch (error) {
      console.error('统一图谱查询错误:', error);
      message.error('查询失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, []);

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    const enabledSources = dataSources.filter(ds => ds.enabled).map(ds => ds.key);
    queryUnifiedGraph(value, enabledSources);
  };

  // 处理节点点击
  const handleNodeClick = async (nodeData: GraphNode) => {
    // 调用外部回调
    if (onNodeClick) {
      onNodeClick(nodeData.id, nodeData);
    }

    // 只有在未禁用内置节点详情时才获取详情
    if (!disableBuiltinNodeDetail) {
      try {
        const response = await fetch(`/api/v1/graph/unified/node/${encodeURIComponent(nodeData.id)}/details?node_type=${nodeData.type}`);
        if (response.ok) {
          const details = await response.json();
          setNodeDetails({ ...nodeData, details });
          setShowNodeDetails(true);
        }
      } catch (error) {
        console.error('获取节点详情失败:', error);
      }
    } else {
      // 禁用时确保不显示内置节点详情
      setShowNodeDetails(false);
      setNodeDetails(null);
    }
  };

  // 数据源切换
  const handleDataSourceToggle = (sourceKey: string, enabled: boolean) => {
    setDataSources(prev => 
      prev.map(ds => 
        ds.key === sourceKey ? { ...ds, enabled } : ds
      )
    );
  };

  // 渲染数据源设置
  const renderDataSourceSettings = () => (
    <div style={{ padding: '16px' }}>
      <Title level={5}>数据源配置</Title>
      <Space direction="vertical" style={{ width: '100%' }}>
        {dataSources.map(source => (
          <Card key={source.key} size="small">
            <Row justify="space-between" align="middle">
              <Col>
                <Space>
                  {source.icon}
                  <div>
                    <Text strong>{source.label}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {source.description}
                    </Text>
                  </div>
                </Space>
              </Col>
              <Col>
                <Switch
                  checked={source.enabled}
                  onChange={(checked) => handleDataSourceToggle(source.key, checked)}
                />
              </Col>
            </Row>
          </Card>
        ))}
      </Space>
    </div>
  );

  // 渲染控制面板
  const renderControls = () => {
    if (!showControls) return null;

    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Search
              placeholder="输入实体名称进行图谱查询..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              enterButton={<SearchOutlined />}
              size="large"
            />
          </Col>
          <Col>
            <Space>
              <Tooltip title="数据源设置">
                <Button
                  icon={<SettingOutlined />}
                  onClick={() => setShowSettings(true)}
                />
              </Tooltip>
              <Tooltip title="刷新">
                <Button
                  icon={<ReloadOutlined />}
                  onClick={() => {
                    if (searchQuery) {
                      handleSearch(searchQuery);
                    }
                  }}
                />
              </Tooltip>
            </Space>
          </Col>
        </Row>
        
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">已启用数据源: </Text>
          {dataSources.filter(ds => ds.enabled).map(ds => (
            <Tag key={ds.key} icon={ds.icon} color="blue" style={{ marginRight: 4 }}>
              {ds.label}
            </Tag>
          ))}
        </div>
      </Card>
    );
  };

  // 渲染节点详情
  const renderNodeDetails = () => (
    <Drawer
      title={`节点详情: ${nodeDetails?.label}`}
      placement="right"
      width={400}
      open={showNodeDetails}
      onClose={() => setShowNodeDetails(false)}
    >
      {nodeDetails && (
        <div>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Card size="small">
              <Text strong>基本信息</Text>
              <div style={{ marginTop: 8 }}>
                <p><Text type="secondary">ID:</Text> {nodeDetails.id}</p>
                <p><Text type="secondary">类型:</Text> <Tag>{nodeDetails.type}</Tag></p>
                <p><Text type="secondary">标签:</Text> {nodeDetails.label}</p>
              </div>
            </Card>
            
            {nodeDetails.properties && (
              <Card size="small">
                <Text strong>属性信息</Text>
                <div style={{ marginTop: 8 }}>
                  {Object.entries(nodeDetails.properties).map(([key, value]) => (
                    <p key={key}>
                      <Text type="secondary">{key}:</Text> {String(value)}
                    </p>
                  ))}
                </div>
              </Card>
            )}
            
            {nodeDetails.details && (
              <Card size="small">
                <Text strong>详细信息</Text>
                <div style={{ marginTop: 8 }}>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                    {JSON.stringify(nodeDetails.details, null, 2)}
                  </pre>
                </div>
              </Card>
            )}
          </Space>
        </div>
      )}
    </Drawer>
  );

  return (
    <div
      className="unified-graph-visualization"
      style={{
        height: typeof height === 'string' ? height : `${height}px`,
        width: '100%',
        overflow: 'visible',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {showControls && renderControls()}

      <Spin spinning={loading}>
        <div style={{
          height: showControls ? 'calc(100% - 60px)' : '100%',
          width: '100%',
          overflow: 'visible',
          flex: 1
        }}>
          <EnhancedGraphVisualization
            data={graphData}
            onNodeClick={handleNodeClick}
            height={700}
            layoutType="force"
            showAnimation={showAnimation}
            showMiniMap={false}
            enableClustering={true}
            disableBuiltinNodeInfo={disableEnhancedNodeInfo}
          />
        </div>
      </Spin>

      {/* 设置抽屉 */}
      <Drawer
        title="图谱设置"
        placement="right"
        width={350}
        open={showSettings}
        onClose={() => setShowSettings(false)}
      >
        {renderDataSourceSettings()}
      </Drawer>

      {/* 节点详情抽屉 - 只在未禁用时显示 */}
      {!disableBuiltinNodeDetail && renderNodeDetails()}
    </div>
  );
};

export default UnifiedGraphVisualization;
