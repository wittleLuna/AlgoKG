import React, { useState } from 'react';
import {
  Typography,
  Card,
  Space,
  Button,
  Input,
  message,
  Spin,
  Empty,
  List,
  Tag,
  Row,
  Col
} from 'antd';
import {
  SearchOutlined,
  NodeIndexOutlined,
  BulbOutlined,
  ClusterOutlined
} from '@ant-design/icons';
import UnifiedGraphVisualization from '../components/graph/UnifiedGraphVisualization';
import { GraphData, GraphNode } from '../types';

const { Title, Paragraph, Text } = Typography;
const { Search } = Input;

const UnifiedGraphPage: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | undefined>();
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [currentEntity, setCurrentEntity] = useState<string>('');
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  // 查询实体图谱
  const handleSearch = async (entity: string) => {
    if (!entity.trim()) {
      message.warning('请输入要查询的实体名称');
      return;
    }

    setLoading(true);
    setCurrentEntity(entity.trim());

    try {
      // 调用统一图谱API
      const response = await fetch('/api/v1/graph/unified/query?data_sources=neo4j&data_sources=embedding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_name: entity.trim(),
          depth: 2,
          limit: 50
        }),
      });

      if (!response.ok) {
        throw new Error(`查询失败: ${response.status}`);
      }

      const data = await response.json();
      setGraphData(data);

      // 添加到搜索历史
      setSearchHistory(prev => {
        const newHistory = [entity.trim(), ...prev.filter(h => h !== entity.trim())];
        return newHistory.slice(0, 10); // 保留最近10次搜索
      });

      message.success(`成功加载 "${entity}" 的知识图谱`);
    } catch (error) {
      console.error('查询图谱失败:', error);
      message.error('查询图谱失败，请稍后重试');
      setGraphData(undefined);
    } finally {
      setLoading(false);
    }
  };

  // 处理节点点击
  const handleNodeClick = (nodeId: string, nodeData: GraphNode) => {
    setSelectedNode(nodeData);
    console.log('节点点击:', nodeId, nodeData);
  };

  // 示例查询
  const exampleQueries = ['动态规划', '两数之和', '链表', '二分查找', '贪心算法', '回溯算法'];

  return (
    <div style={{
      height: 'calc(100vh - 120px)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px',
      overflow: 'auto'
    }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24, flexShrink: 0 }}>
        <Title level={2}>
          <NodeIndexOutlined style={{ marginRight: 8 }} />
          知识图谱
        </Title>
        <Paragraph type="secondary">
          输入实体名称，查看以该实体为核心的知识图谱
        </Paragraph>
      </div>

      {/* 搜索区域 */}
      <Card style={{ marginBottom: 24, flexShrink: 0 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="请输入要查询的实体名称，如：动态规划、两数之和、链表等"
            enterButton={<Button type="primary" icon={<SearchOutlined />}>查询图谱</Button>}
            size="large"
            onSearch={handleSearch}
            loading={loading}
          />

          {/* 示例查询 */}
          <div>
            <Text type="secondary" style={{ marginRight: 8 }}>快速查询:</Text>
            <Space wrap>
              {exampleQueries.map((query) => (
                <Button
                  key={query}
                  size="small"
                  type="link"
                  onClick={() => handleSearch(query)}
                  disabled={loading}
                >
                  {query}
                </Button>
              ))}
            </Space>
          </div>

          {/* 搜索历史 */}
          {searchHistory.length > 0 && (
            <div>
              <Text type="secondary" style={{ marginRight: 8 }}>最近查询:</Text>
              <Space wrap>
                {searchHistory.slice(0, 5).map((query) => (
                  <Button
                    key={query}
                    size="small"
                    type="text"
                    onClick={() => handleSearch(query)}
                    disabled={loading}
                  >
                    {query}
                  </Button>
                ))}
              </Space>
            </div>
          )}
        </Space>
      </Card>

      {/* 图谱显示区域 */}
      <div style={{ flex: 1, minHeight: '800px', overflow: 'visible' }}>
        {loading ? (
          <Card style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column'
          }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Text>正在加载图谱数据...</Text>
            </div>
          </Card>
        ) : graphData ? (
          <Card
            title={
              <Space>
                <NodeIndexOutlined />
                <Text strong>{currentEntity}</Text>
                <Text type="secondary">的知识图谱</Text>
              </Space>
            }
            style={{ height: '800px', overflow: 'visible' }}
            bodyStyle={{
              height: 'calc(800px - 57px)',
              padding: 0,
              overflow: 'visible'
            }}
          >
            <UnifiedGraphVisualization
              data={graphData}
              onNodeClick={handleNodeClick}
              height="100%"
              showControls={true}
              defaultDataSources={['neo4j', 'embedding']}
              disableBuiltinNodeDetail={true}
            />
          </Card>
        ) : (
          <Card style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column'
          }}>
            <Empty
              description="请输入实体名称开始探索知识图谱"
            />
          </Card>
        )}
      </div>
    </div>
  );
};

export default UnifiedGraphPage;
