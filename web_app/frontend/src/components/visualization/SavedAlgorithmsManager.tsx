import React, { useState, useEffect, useCallback } from 'react';
import { Card, List, Button, Space, Typography, message, Tag } from 'antd';
import { LeftOutlined, SendOutlined, PlayCircleOutlined, UserOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface SavedAlgorithm {
  id: string;
  name: string;
  description: string;
  dataStructure: string;
  code: string;
  inputData: string;
  createdAt: string;
}

interface SavedAlgorithmsManagerProps {
  onLoadAlgorithm: (algorithm: SavedAlgorithm) => void;
}

const SavedAlgorithmsManager: React.FC<SavedAlgorithmsManagerProps> = ({
  onLoadAlgorithm
}) => {
  const [savedAlgorithms, setSavedAlgorithms] = useState<SavedAlgorithm[]>([]);

  // 加载保存的算法
  const loadSavedAlgorithms = useCallback(() => {
    try {
      const saved = localStorage.getItem('customAlgorithms');
      if (saved) {
        const algorithms = JSON.parse(saved);
        setSavedAlgorithms(algorithms);
      }
    } catch (error) {
      console.error('加载保存的算法失败:', error);
      message.error('加载保存的算法失败');
    }
  }, []);

  useEffect(() => {
    loadSavedAlgorithms();
  }, [loadSavedAlgorithms]);

  // 删除算法
  const handleDelete = useCallback((algorithmId: string) => {
    try {
      const updatedAlgorithms = savedAlgorithms.filter(alg => alg.id !== algorithmId);
      localStorage.setItem('customAlgorithms', JSON.stringify(updatedAlgorithms));
      setSavedAlgorithms(updatedAlgorithms);
      message.success('算法已删除');
    } catch (error) {
      console.error('删除算法失败:', error);
      message.error('删除算法失败');
    }
  }, [savedAlgorithms]);

  // 加载算法到编辑器
  const handleLoad = useCallback((algorithm: SavedAlgorithm) => {
    onLoadAlgorithm(algorithm);
    message.success(`已加载算法: ${algorithm.name}`);
  }, [onLoadAlgorithm]);

  // 预览算法
  const handlePreview = useCallback((algorithm: SavedAlgorithm) => {
    const info = `算法名称: ${algorithm.name}\n数据结构: ${getDataStructureName(algorithm.dataStructure)}\n描述: ${algorithm.description || '无描述'}\n创建时间: ${new Date(algorithm.createdAt).toLocaleString()}`;
    alert(info);
  }, []);

  // 获取数据结构标签颜色
  const getDataStructureColor = (dataStructure: string) => {
    const colors: { [key: string]: string } = {
      array: 'blue',
      stack: 'green',
      queue: 'orange',
      tree: 'purple',
      graph: 'red'
    };
    return colors[dataStructure] || 'default';
  };

  // 获取数据结构中文名
  const getDataStructureName = (dataStructure: string) => {
    const names: { [key: string]: string } = {
      array: '数组',
      stack: '栈',
      queue: '队列',
      tree: '二叉树',
      graph: '图'
    };
    return names[dataStructure] || dataStructure;
  };

  return (
    <>
      <Card 
        title={
          <Space>
            <UserOutlined />
            保存的算法模板
            <Tag color="blue">{savedAlgorithms.length}个</Tag>
          </Space>
        }
        extra={
          <Button onClick={loadSavedAlgorithms} size="small">
            刷新
          </Button>
        }
      >
        {savedAlgorithms.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            <UserOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <div>暂无保存的算法模板</div>
            <div style={{ fontSize: 12, marginTop: 8 }}>
              在自定义算法编辑器中创建并保存算法模板
            </div>
          </div>
        ) : (
          <List
            dataSource={savedAlgorithms}
            renderItem={(algorithm) => (
              <List.Item
                actions={[
                  <Button
                    type="text"
                    icon={<SendOutlined />}
                    onClick={() => handlePreview(algorithm)}
                    size="small"
                  >
                    预览
                  </Button>,
                  <Button
                    type="text"
                    icon={<PlayCircleOutlined />}
                    onClick={() => handleLoad(algorithm)}
                    size="small"
                  >
                    加载
                  </Button>,
                  <Button
                    type="text"
                    icon={<LeftOutlined />}
                    onClick={() => {
                      if (window.confirm('确定要删除这个算法模板吗？')) {
                        handleDelete(algorithm.id);
                      }
                    }}
                    danger
                    size="small"
                  >
                    删除
                  </Button>
                ]}
              >
                <div>
                  <div style={{ marginBottom: 8 }}>
                    <Space>
                      <Text strong>{algorithm.name}</Text>
                      <Tag color={getDataStructureColor(algorithm.dataStructure)}>
                        {getDataStructureName(algorithm.dataStructure)}
                      </Tag>
                    </Space>
                  </div>
                  <div>
                    <Paragraph
                      ellipsis={{ rows: 2 }}
                      style={{ marginBottom: 8, color: '#666' }}
                    >
                      {algorithm.description || '无描述'}
                    </Paragraph>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      创建时间: {new Date(algorithm.createdAt).toLocaleString()}
                    </Text>
                  </div>
                </div>
              </List.Item>
            )}
          />
        )}
      </Card>


    </>
  );
};

export default SavedAlgorithmsManager;
