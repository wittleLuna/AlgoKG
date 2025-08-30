import React, { useState, useEffect } from 'react';
import { Card, List, Button, Space, Typography, Empty, Tag, message } from 'antd';
import { StarOutlined, UserOutlined, LeftOutlined, SendOutlined, FilterOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface FavoriteItem {
  id: string;
  type: 'query' | 'response' | 'concept' | 'problem';
  title: string;
  content: string;
  timestamp: number;
  tags: string[];
  category: string;
  metadata?: any;
}

interface FavoriteManagerProps {
  visible: boolean;
  onClose: () => void;
  onSelectFavorite?: (item: FavoriteItem) => void;
}

const FavoriteManager: React.FC<FavoriteManagerProps> = ({
  visible,
  onClose,
  onSelectFavorite
}) => {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // 加载收藏列表
  useEffect(() => {
    if (visible) {
      loadFavorites();
    }
  }, [visible]);

  const loadFavorites = () => {
    const saved = localStorage.getItem('favorites');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setFavorites(parsed);
      } catch (error) {
        console.error('Failed to parse favorites:', error);
      }
    }
  };

  const saveFavorites = (newFavorites: FavoriteItem[]) => {
    localStorage.setItem('favorites', JSON.stringify(newFavorites));
    setFavorites(newFavorites);
  };

  // 删除收藏
  const deleteFavorite = (id: string) => {
    const updated = favorites.filter(item => item.id !== id);
    saveFavorites(updated);
    message.success('已删除收藏');
  };

  // 预览收藏
  const previewFavorite = (item: FavoriteItem) => {
    const info = `标题: ${item.title}\n类型: ${item.type}\n内容: ${item.content}\n创建时间: ${new Date(item.timestamp).toLocaleString()}`;
    alert(info);
  };

  // 获取分类列表
  const getCategories = () => {
    const uniqueCategories = new Set(favorites.map(item => item.category));
    const categories = ['all', ...Array.from(uniqueCategories)];
    return categories;
  };

  // 过滤收藏
  const getFilteredFavorites = () => {
    if (selectedCategory === 'all') {
      return favorites;
    }
    return favorites.filter(item => item.category === selectedCategory);
  };

  // 获取分类显示名称
  const getCategoryName = (category: string) => {
    const names: Record<string, string> = {
      'all': '全部',
      'query': '查询',
      'response': '回答',
      'concept': '概念',
      'problem': '题目',
      'algorithm': '算法',
      'data_structure': '数据结构'
    };
    return names[category] || category;
  };

  // 获取类型颜色
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'query': 'blue',
      'response': 'green',
      'concept': 'purple',
      'problem': 'orange',
      'algorithm': 'red',
      'data_structure': 'cyan'
    };
    return colors[type] || 'default';
  };

  const filteredFavorites = getFilteredFavorites();

  if (!visible) return null;

  return (
    <>
      <Card
        title={
          <Space>
            <StarOutlined style={{ color: '#faad14' }} />
            <span>我的收藏</span>
            <Text type="secondary">({filteredFavorites.length})</Text>
          </Space>
        }
        extra={
          <Button type="text" size="small" onClick={onClose}>
            关闭
          </Button>
        }
        style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          right: 0,
          zIndex: 1000,
          marginTop: 8,
          maxHeight: 500,
          overflow: 'hidden',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
        }}
      >
        {/* 分类筛选 */}
        <div style={{ marginBottom: 16 }}>
          <Space wrap>
            {getCategories().map(category => (
              <Tag
                key={category}
                color={selectedCategory === category ? 'blue' : 'default'}
                style={{ cursor: 'pointer' }}
                onClick={() => setSelectedCategory(category)}
              >
                {getCategoryName(category)}
              </Tag>
            ))}
          </Space>
        </div>

        {filteredFavorites.length === 0 ? (
          <Empty
            image={null}
            description="暂无收藏内容"
            style={{ padding: '20px 0' }}
          />
        ) : (
          <List
            size="small"
            dataSource={filteredFavorites}
            style={{ maxHeight: 300, overflow: 'auto' }}
            renderItem={(item) => (
              <List.Item
                style={{
                  padding: '12px 0',
                  cursor: 'pointer',
                  borderRadius: 4,
                  margin: '4px 0'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#f5f5f5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                }}
                onClick={() => onSelectFavorite?.(item)}
                actions={[
                  <Button
                    type="text"
                    size="small"
                    icon={<SendOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      previewFavorite(item);
                    }}
                  />,
                  <Button
                    type="text"
                    size="small"
                    icon={<LeftOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteFavorite(item.id);
                    }}
                    style={{ color: '#ff4d4f' }}
                  />
                ]}
              >
                <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <FilterOutlined style={{ color: '#1890ff', marginRight: 12 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ marginBottom: 4 }}>
                      <Space>
                        <Text ellipsis style={{ fontSize: 14, maxWidth: 200 }}>
                          {item.title}
                        </Text>
                        <Tag color={getTypeColor(item.type)} size="small">
                          {item.type}
                        </Tag>
                      </Space>
                    </div>
                    <div>
                      <Paragraph
                        ellipsis={{ rows: 2 }}
                        style={{ fontSize: 12, color: '#666', margin: 0 }}
                      >
                        {item.content}
                      </Paragraph>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {new Date(item.timestamp).toLocaleString()}
                      </Text>
                    </div>
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

// 导出添加收藏的工具函数
export const addToFavorites = (item: Omit<FavoriteItem, 'id' | 'timestamp'>) => {
  const saved = localStorage.getItem('favorites');
  let favorites: FavoriteItem[] = [];
  
  if (saved) {
    try {
      favorites = JSON.parse(saved);
    } catch (error) {
      console.error('Failed to parse favorites:', error);
    }
  }

  const newItem: FavoriteItem = {
    ...item,
    id: Date.now().toString(),
    timestamp: Date.now()
  };

  const updated = [newItem, ...favorites];
  localStorage.setItem('favorites', JSON.stringify(updated));
  message.success('已添加到收藏');
};

export default FavoriteManager;
