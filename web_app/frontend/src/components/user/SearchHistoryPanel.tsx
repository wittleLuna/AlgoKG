import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import {
  List,
  Button,
  Empty,
  message,
  Tabs,
  Space,
  Typography,
  Tag,
  Input
} from 'antd';
import {
  SearchOutlined,
  QuestionCircleOutlined,
  NodeIndexOutlined,
  CloseOutlined,
  UserOutlined
} from '@ant-design/icons';
import { authService, SearchHistory } from '../../services/authService';

const { Title, Text } = Typography;
const { Search } = Input;

interface SearchHistoryPanelProps {
  visible: boolean;
  onClose: () => void;
  onSearchClick?: (query: string, searchType: string) => void;
}

const SearchHistoryPanel: React.FC<SearchHistoryPanelProps> = ({ 
  visible, 
  onClose, 
  onSearchClick 
}) => {
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (visible) {
      loadSearchHistory();
    }
  }, [visible, activeTab]);

  const loadSearchHistory = async () => {
    setLoading(true);
    try {
      const searchType = activeTab === 'all' ? undefined : activeTab;
      const data = await authService.getSearchHistory(searchType);
      setSearchHistory(data);
    } catch (error: any) {
      message.error(error.message || '加载搜索历史失败');
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async (searchType?: string) => {
    try {
      await authService.clearSearchHistory(searchType);
      message.success('搜索历史已清空');
      loadSearchHistory();
    } catch (error: any) {
      message.error(error.message || '清空搜索历史失败');
    }
  };

  const handleSearchClick = (history: SearchHistory) => {
    if (onSearchClick) {
      onSearchClick(history.query, history.search_type);
    }
  };

  const getSearchTypeIcon = (type: string) => {
    switch (type) {
      case 'qa':
        return <QuestionCircleOutlined style={{ color: '#1890ff' }} />;
      case 'graph':
        return <NodeIndexOutlined style={{ color: '#52c41a' }} />;
      case 'problem':
        return <SearchOutlined style={{ color: '#faad14' }} />;
      default:
        return <SearchOutlined style={{ color: '#666' }} />;
    }
  };

  const getSearchTypeLabel = (type: string) => {
    switch (type) {
      case 'qa':
        return '问答';
      case 'graph':
        return '图谱';
      case 'problem':
        return '题目';
      default:
        return '其他';
    }
  };

  const getSearchTypeColor = (type: string) => {
    switch (type) {
      case 'qa':
        return 'blue';
      case 'graph':
        return 'green';
      case 'problem':
        return 'orange';
      default:
        return 'default';
    }
  };

  const filteredHistory = searchHistory.filter(history => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return history.query.toLowerCase().includes(query);
  });

  const renderHistoryItem = (history: SearchHistory) => (
    <List.Item
      key={history.id}
      actions={[
        <Button
          type="text"
          size="small"
          onClick={() => handleSearchClick(history)}
          title="重新搜索"
        >
          搜索
        </Button>
      ]}
      style={{ cursor: 'pointer' }}
      onClick={() => handleSearchClick(history)}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', width: '100%' }}>
        <div style={{ marginTop: '4px' }}>
          {getSearchTypeIcon(history.search_type)}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ marginBottom: '8px' }}>
            <Space>
              <span style={{ fontWeight: 'bold' }}>{history.query}</span>
              <Tag color={getSearchTypeColor(history.search_type)} size="small">
                {getSearchTypeLabel(history.search_type)}
              </Tag>
              {history.results_count > 0 && (
                <span style={{
                  backgroundColor: '#52c41a',
                  color: 'white',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  fontSize: '12px'
                }}>
                  {history.results_count}
                </span>
              )}
            </Space>
          </div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            搜索时间: {new Date(history.created_at).toLocaleString('zh-CN')}
          </Text>
        </div>
      </div>
    </List.Item>
  );

  const getTabExtra = (searchType?: string) => (
    <Button
      type="text"
      size="small"
      danger
      onClick={() => {
        if (window.confirm(`确定要清空${searchType ? getSearchTypeLabel(searchType) : '全部'}搜索历史吗？`)) {
          handleClearHistory(searchType);
        }
      }}
    >
      清空
    </Button>
  );

  const tabItems = [
    {
      key: 'all',
      label: `全部 (${searchHistory.length})`,
      children: (
        <List
          dataSource={filteredHistory}
          renderItem={renderHistoryItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无搜索历史" />
            )
          }}
        />
      )
    },
    {
      key: 'qa',
      label: `问答 (${searchHistory.filter(h => h.search_type === 'qa').length})`,
      children: (
        <List
          dataSource={filteredHistory.filter(h => h.search_type === 'qa')}
          renderItem={renderHistoryItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无问答搜索历史" />
            )
          }}
        />
      )
    },
    {
      key: 'graph',
      label: `图谱 (${searchHistory.filter(h => h.search_type === 'graph').length})`,
      children: (
        <List
          dataSource={filteredHistory.filter(h => h.search_type === 'graph')}
          renderItem={renderHistoryItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无图谱搜索历史" />
            )
          }}
        />
      )
    },
    {
      key: 'problem',
      label: `题目 (${searchHistory.filter(h => h.search_type === 'problem').length})`,
      children: (
        <List
          dataSource={filteredHistory.filter(h => h.search_type === 'problem')}
          renderItem={renderHistoryItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无题目搜索历史" />
            )
          }}
        />
      )
    }
  ];

  console.log('SearchHistoryPanel render:', visible);
  if (!visible) return null;

  const panelContent = (
    <div style={{
      position: 'fixed',
      top: 0,
      right: 0,
      width: '480px',
      height: '100vh',
      backgroundColor: 'white',
      boxShadow: '-2px 0 8px rgba(0, 0, 0, 0.15)',
      zIndex: 9999,
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{
        padding: '16px 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <Space>
          <UserOutlined style={{ color: '#1890ff' }} />
          搜索历史
        </Space>
        <Space>
          {getTabExtra(activeTab === 'all' ? undefined : activeTab)}
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={onClose}
          />
        </Space>
      </div>

      <div style={{ flex: 1, padding: '16px 24px', overflow: 'auto' }}>
      <div style={{ marginBottom: 16 }}>
        <Search
          placeholder="搜索历史记录..."
          allowClear
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        size="small"
      />
      </div>
    </div>
  );

  return createPortal(panelContent, document.body);
};

export default SearchHistoryPanel;
