import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
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
  MessageOutlined,
  CloseOutlined,
  UserOutlined,
  CopyOutlined
} from '@ant-design/icons';
import { authService } from '../../services/authService';

interface FavoriteItem {
  id: string;
  type: 'query' | 'response' | 'concept' | 'problem';
  item_type?: string; // 兼容旧代码
  item_id?: string;   // 兼容旧代码
  title: string;
  content: string;
  description?: string; // 兼容旧代码
  timestamp: number;
  tags: string[];
  category: string;
  metadata?: any;
}


const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

interface FavoritesPanelProps {
  visible: boolean;
  onClose: () => void;
}

const FavoritesPanel: React.FC<FavoritesPanelProps> = ({ visible, onClose }) => {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFavorite, setSelectedFavorite] = useState<FavoriteItem | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  // Markdown渲染组件
  const MarkdownRenderer: React.FC<{ content: string }> = ({ content }) => (
    <ReactMarkdown
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter
              style={tomorrow}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props} style={{
              backgroundColor: '#f5f5f5',
              padding: '2px 4px',
              borderRadius: '3px',
              fontSize: '0.9em'
            }}>
              {children}
            </code>
          );
        },
        h1: ({ children }) => <h1 style={{ fontSize: '1.5em', fontWeight: 'bold', marginBottom: '0.5em', borderBottom: '2px solid #eee', paddingBottom: '0.3em' }}>{children}</h1>,
        h2: ({ children }) => <h2 style={{ fontSize: '1.3em', fontWeight: 'bold', marginBottom: '0.5em', borderBottom: '1px solid #eee', paddingBottom: '0.2em' }}>{children}</h2>,
        h3: ({ children }) => <h3 style={{ fontSize: '1.2em', fontWeight: 'bold', marginBottom: '0.5em' }}>{children}</h3>,
        p: ({ children }) => <p style={{ marginBottom: '1em', lineHeight: '1.6' }}>{children}</p>,
        ul: ({ children }) => <ul style={{ marginBottom: '1em', paddingLeft: '1.5em' }}>{children}</ul>,
        ol: ({ children }) => <ol style={{ marginBottom: '1em', paddingLeft: '1.5em' }}>{children}</ol>,
        li: ({ children }) => <li style={{ marginBottom: '0.3em' }}>{children}</li>,
        blockquote: ({ children }) => (
          <blockquote style={{
            borderLeft: '4px solid #ddd',
            paddingLeft: '1em',
            margin: '1em 0',
            fontStyle: 'italic',
            backgroundColor: '#f9f9f9',
            padding: '0.5em 1em'
          }}>
            {children}
          </blockquote>
        ),
        strong: ({ children }) => <strong style={{ fontWeight: 'bold' }}>{children}</strong>,
        em: ({ children }) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
      }}
    >
      {content}
    </ReactMarkdown>
  );

  useEffect(() => {
    if (visible) {
      loadFavorites();
    }
  }, [visible, activeTab]);

  const loadFavorites = async () => {
    setLoading(true);
    try {
      // 暂时使用localStorage，后续可以改为API调用
      const saved = localStorage.getItem('favorites');
      if (saved) {
        const parsed = JSON.parse(saved);
        console.log('加载的收藏数据:', parsed);
        const filtered = activeTab === 'all'
          ? parsed
          : parsed.filter((item: any) => item.type === activeTab);
        setFavorites(filtered);
      } else {
        setFavorites([]);
      }
    } catch (error: any) {
      console.error('加载收藏失败:', error);
      setFavorites([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFavorite = async (favorite: any) => {
    try {
      // 暂时使用localStorage
      const saved = localStorage.getItem('favorites');
      if (saved) {
        const favorites = JSON.parse(saved);
        const newFavorites = favorites.filter((item: any) => item.id !== favorite.id);
        localStorage.setItem('favorites', JSON.stringify(newFavorites));
        message.success('已移除收藏');
        loadFavorites();
      }
    } catch (error: any) {
      message.error('移除收藏失败');
    }
  };

  const getItemTypeIcon = (type: string) => {
    switch (type) {
      case 'query':
        return <QuestionCircleOutlined style={{ color: '#1890ff' }} />;
      case 'response':
        return <MessageOutlined style={{ color: '#52c41a' }} />;
      case 'concept':
        return <NodeIndexOutlined style={{ color: '#722ed1' }} />;
      case 'problem':
        return <UserOutlined style={{ color: '#fa8c16' }} />;
      default:
        return <UserOutlined style={{ color: '#f5222d' }} />;
    }
  };

  const getItemTypeLabel = (type: string) => {
    switch (type) {
      case 'query':
        return '问题';
      case 'response':
        return '回答';
      case 'concept':
        return '概念';
      case 'problem':
        return '问题';
      default:
        return '其他';
    }
  };

  const getItemTypeColor = (type: string) => {
    switch (type) {
      case 'query':
        return 'blue';
      case 'response':
        return 'green';
      case 'concept':
        return 'purple';
      case 'problem':
        return 'orange';
      default:
        return 'default';
    }
  };

  const filteredFavorites = favorites.filter(favorite => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      favorite.title?.toLowerCase().includes(query) ||
      favorite.content?.toLowerCase().includes(query) ||
      favorite.id?.toLowerCase().includes(query)
    );
  });

  const renderFavoriteItem = (favorite: FavoriteItem) => (
    <List.Item
      key={favorite.id}
      actions={[
        <Button
          type="text"
          onClick={(e) => {
            e.stopPropagation();
            setSelectedFavorite(favorite);
          }}
          size="small"
          title="查看详情"
        >
          查看
        </Button>,
        <Button
          type="text"
          onClick={(e) => {
            e.stopPropagation();
            handleRemoveFavorite(favorite);
          }}
          danger
          size="small"
          title="移除收藏"
        >
          删除
        </Button>
      ]}
      style={{ cursor: 'pointer' }}
      onClick={() => setSelectedFavorite(favorite)}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', width: '100%' }}>
        <div style={{ marginTop: '4px' }}>
          {getItemTypeIcon(favorite.type)}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ marginBottom: '8px' }}>
            <Space>
              <span style={{ fontWeight: 'bold' }}>{favorite.title || favorite.id}</span>
              <Tag color={getItemTypeColor(favorite.type)} size="small">
                {getItemTypeLabel(favorite.type)}
              </Tag>
            </Space>
          </div>
          {favorite.content && (
            <div style={{ marginBottom: '8px', color: '#666', lineHeight: '1.5' }}>
              {favorite.content.length > 200
                ? `${favorite.content.substring(0, 200)}...`
                : favorite.content}
            </div>
          )}
          <Text type="secondary" style={{ fontSize: '12px' }}>
            收藏时间: {new Date(favorite.timestamp).toLocaleString('zh-CN')}
          </Text>
        </div>
      </div>
    </List.Item>
  );

  const tabItems = [
    {
      key: 'all',
      label: `全部 (${favorites.length})`,
      children: (
        <List
          dataSource={filteredFavorites}
          renderItem={renderFavoriteItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无收藏" />
            )
          }}
        />
      )
    },
    {
      key: 'query',
      label: `问题 (${favorites.filter(f => f.type === 'query').length})`,
      children: (
        <List
          dataSource={filteredFavorites.filter(f => f.type === 'query')}
          renderItem={renderFavoriteItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无问题收藏" />
            )
          }}
        />
      )
    },
    {
      key: 'response',
      label: `回答 (${favorites.filter(f => f.type === 'response').length})`,
      children: (
        <List
          dataSource={filteredFavorites.filter(f => f.type === 'response')}
          renderItem={renderFavoriteItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无回答收藏" />
            )
          }}
        />
      )
    },
    {
      key: 'concept',
      label: `概念 (${favorites.filter(f => f.type === 'concept').length})`,
      children: (
        <List
          dataSource={filteredFavorites.filter(f => f.type === 'concept')}
          renderItem={renderFavoriteItem}
          loading={loading}
          locale={{
            emptyText: (
              <Empty description="暂无概念收藏" />
            )
          }}
        />
      )
    }
  ];

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
          <UserOutlined style={{ color: '#f5222d' }} />
          我的收藏
        </Space>
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={onClose}
        />
      </div>

      <div style={{ flex: 1, padding: '16px 24px', overflow: 'auto' }}>
      <div style={{ marginBottom: 16 }}>
        <Search
          placeholder="搜索收藏内容..."
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

      {/* 详情查看模态框 */}
      {selectedFavorite && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10000
          }}
          onClick={() => setSelectedFavorite(null)}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              maxWidth: '80%',
              maxHeight: '80%',
              overflow: 'auto',
              padding: '24px'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Space>
                {getItemTypeIcon(selectedFavorite.type)}
                <span style={{ fontSize: '18px', fontWeight: 'bold' }}>
                  {selectedFavorite.title}
                </span>
                <Tag color={getItemTypeColor(selectedFavorite.type)}>
                  {getItemTypeLabel(selectedFavorite.type)}
                </Tag>
              </Space>
              <Space>
                <Button
                  type="text"
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(selectedFavorite.content)}
                  title="复制内容"
                >
                  复制
                </Button>
                <Button
                  type="text"
                  icon={<CloseOutlined />}
                  onClick={() => setSelectedFavorite(null)}
                />
              </Space>
            </div>

            <div style={{ marginBottom: '16px', maxHeight: '60vh', overflow: 'auto' }}>
              <MarkdownRenderer content={selectedFavorite.content} />
            </div>

            <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '16px' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                收藏时间: {new Date(selectedFavorite.timestamp).toLocaleString('zh-CN')}
              </Text>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return createPortal(panelContent, document.body);
};

export default FavoritesPanel;
