import React, { useState, useEffect } from 'react';
import { Card, List, Button, Space, Typography, Empty, Tooltip, Input } from 'antd';
import { UserOutlined, LeftOutlined, SearchOutlined, ClockCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { Search } = Input;

interface SearchHistoryItem {
  id: string;
  query: string;
  timestamp: number;
  category?: string;
}

interface SearchHistoryProps {
  onSelectHistory: (query: string) => void;
  visible: boolean;
  onClose: () => void;
}

const SearchHistory: React.FC<SearchHistoryProps> = ({
  onSelectHistory,
  visible,
  onClose
}) => {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<SearchHistoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  // 加载搜索历史
  useEffect(() => {
    const savedHistory = localStorage.getItem('search_history');
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setHistory(parsed);
        setFilteredHistory(parsed);
      } catch (error) {
        console.error('Failed to parse search history:', error);
      }
    }
  }, [visible]);

  // 过滤搜索历史
  useEffect(() => {
    if (searchTerm.trim()) {
      const filtered = history.filter(item =>
        item.query.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredHistory(filtered);
    } else {
      setFilteredHistory(history);
    }
  }, [searchTerm, history]);

  // 添加搜索历史
  const addToHistory = (query: string) => {
    const newItem: SearchHistoryItem = {
      id: Date.now().toString(),
      query: query.trim(),
      timestamp: Date.now(),
      category: 'general'
    };

    const updatedHistory = [newItem, ...history.filter(item => item.query !== query.trim())].slice(0, 50);
    setHistory(updatedHistory);
    localStorage.setItem('search_history', JSON.stringify(updatedHistory));
  };

  // 删除单个历史记录
  const deleteHistoryItem = (id: string) => {
    const updatedHistory = history.filter(item => item.id !== id);
    setHistory(updatedHistory);
    setFilteredHistory(updatedHistory);
    localStorage.setItem('search_history', JSON.stringify(updatedHistory));
  };

  // 清空所有历史记录
  const clearAllHistory = () => {
    setHistory([]);
    setFilteredHistory([]);
    localStorage.removeItem('search_history');
  };

  // 选择历史记录
  const handleSelectHistory = (query: string) => {
    onSelectHistory(query);
    addToHistory(query); // 重新添加到顶部
    onClose();
  };

  // 格式化时间
  const formatTime = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    return new Date(timestamp).toLocaleDateString();
  };

  if (!visible) return null;

  return (
    <Card
      title={
        <Space>
          <UserOutlined />
          <span>搜索历史</span>
          <Text type="secondary">({filteredHistory.length})</Text>
        </Space>
      }
      extra={
        <Space>
          <Button
            type="text"
            size="small"
            onClick={clearAllHistory}
            disabled={history.length === 0}
          >
            清空
          </Button>
          <Button type="text" size="small" onClick={onClose}>
            关闭
          </Button>
        </Space>
      }
      style={{
        position: 'absolute',
        top: '100%',
        left: 0,
        right: 0,
        zIndex: 1000,
        marginTop: 8,
        maxHeight: 400,
        overflow: 'hidden',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
      }}
    >
      {history.length > 0 && (
        <Search
          placeholder="搜索历史记录..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ marginBottom: 16 }}
          allowClear
        />
      )}

      {filteredHistory.length === 0 ? (
        <Empty
          image={null}
          description={
            history.length === 0 ? "暂无搜索历史" : "未找到匹配的历史记录"
          }
          style={{ padding: '20px 0' }}
        />
      ) : (
        <List
          size="small"
          dataSource={filteredHistory}
          style={{ maxHeight: 250, overflow: 'auto' }}
          renderItem={(item) => (
            <List.Item
              style={{
                padding: '8px 0',
                cursor: 'pointer',
                borderRadius: 4,
                margin: '2px 0'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#f5f5f5';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'transparent';
              }}
              onClick={() => handleSelectHistory(item.query)}
              actions={[
                <Tooltip title="删除">
                  <Button
                    type="text"
                    size="small"
                    icon={<LeftOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteHistoryItem(item.id);
                    }}
                    style={{ color: '#999' }}
                  />
                </Tooltip>
              ]}
            >
              <div style={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <ClockCircleOutlined style={{ color: '#999', marginRight: 12 }} />
                <div style={{ flex: 1 }}>
                  <Text ellipsis style={{ fontSize: 14 }}>
                    {item.query}
                  </Text>
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {formatTime(item.timestamp)}
                    </Text>
                  </div>
                </div>
              </div>

            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

// 导出添加历史记录的工具函数
export const addSearchHistory = (query: string) => {
  const savedHistory = localStorage.getItem('search_history');
  let history: SearchHistoryItem[] = [];
  
  if (savedHistory) {
    try {
      history = JSON.parse(savedHistory);
    } catch (error) {
      console.error('Failed to parse search history:', error);
    }
  }

  const newItem: SearchHistoryItem = {
    id: Date.now().toString(),
    query: query.trim(),
    timestamp: Date.now(),
    category: 'general'
  };

  const updatedHistory = [newItem, ...history.filter(item => item.query !== query.trim())].slice(0, 50);
  localStorage.setItem('search_history', JSON.stringify(updatedHistory));
};

export default SearchHistory;
