import React, { useState, useEffect } from 'react';
import {
  Layout,
  Button,
  List,
  Typography,
  Space,
  Input,
  message,
  Empty
} from 'antd';
import {
  MessageOutlined,
  SearchOutlined,
  CloseOutlined,
  UserOutlined,
  MenuFoldOutlined
} from '@ant-design/icons';
import { authService, Session } from '../../services/authService';

const { Sider } = Layout;
const { Text, Title } = Typography;
const { Search } = Input;

interface SessionSidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  currentSessionId?: string;
  onSessionSelect: (sessionId: string) => void;
  onNewSession: () => void;
}

const SessionSidebar: React.FC<SessionSidebarProps> = ({
  collapsed,
  onCollapse,
  currentSessionId,
  onSessionSelect,
  onNewSession
}) => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (authService.isAuthenticated()) {
      loadSessions();
    }
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await authService.getUserSessions();
      setSessions(data);
    } catch (error: any) {
      console.error('加载会话列表失败:', error);
      // 如果用户未登录，不显示错误
      if (authService.isAuthenticated()) {
        message.error('加载会话列表失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (firstMessage?: string) => {
    try {
      if (authService.isAuthenticated()) {
        // 根据第一条消息生成标题
        let title = '新对话';
        if (firstMessage) {
          // 取前20个字符作为标题
          title = firstMessage.length > 20 ? `${firstMessage.substring(0, 20)}...` : firstMessage;
          // 移除换行符和多余空格
          title = title.replace(/\s+/g, ' ').trim();
        }

        const newSession = await authService.createSession({
          title: title,
          description: '智能问答会话'
        });

        setSessions(prev => [newSession, ...prev]);
        onSessionSelect(newSession.id.toString());
        message.success('新会话已创建');
        return newSession;
      } else {
        onNewSession();
        message.info('已创建新会话');
        return null;
      }
    } catch (error: any) {
      message.error(error.message || '创建会话失败');
      return null;
    }
  };

  const filteredSessions = sessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getSessionTitle = (session: Session) => {
    // 如果标题是默认的"新会话"格式，尝试生成更有意义的标题
    if (session.title.startsWith('新会话') || session.title === '新对话') {
      return `对话 ${session.id}`;
    }
    return session.title;
  };

  const deleteSession = async (sessionId: number, event: React.MouseEvent) => {
    event.stopPropagation(); // 防止触发选择会话

    try {
      await authService.deleteSession(sessionId);
      message.success('会话已删除');
      loadSessions(); // 重新加载会话列表

      // 如果删除的是当前会话，切换到新会话
      if (currentSessionId === sessionId.toString()) {
        onNewSession();
      }
    } catch (error) {
      console.error('删除会话失败:', error);
      message.error('删除会话失败');
    }
  };

  const renderSessionItem = (session: Session) => {
    const isActive = currentSessionId === session.id.toString();
    const displayTitle = getSessionTitle(session);

    return (
      <List.Item
        key={session.id}
        className={`session-item ${isActive ? 'active' : ''}`}
        style={{
          padding: '8px 12px',
          cursor: 'pointer',
          backgroundColor: isActive ? '#e6f7ff' : 'transparent',
          borderLeft: isActive ? '3px solid #1890ff' : '3px solid transparent',
          marginBottom: '4px',
          borderRadius: '6px',
          position: 'relative'
        }}
        onClick={() => onSessionSelect(session.id.toString())}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', width: '100%' }}>
          <div style={{ marginTop: '4px' }}>
            <MessageOutlined style={{ color: isActive ? '#1890ff' : '#666' }} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{
              color: isActive ? 'var(--session-active-border)' : 'var(--text-primary)',
              fontWeight: isActive ? '600' : '500',
              marginBottom: '4px',
              paddingRight: '32px', // 为删除按钮留出空间
              fontSize: '14px',
              lineHeight: '1.4',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              transition: 'color 0.2s ease'
            }}>
              {displayTitle}
            </div>
            {!collapsed && (
              <div style={{
                fontSize: '11px',
                color: 'var(--text-tertiary)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'color 0.2s ease'
              }}>
                <span>
                  {session.message_count > 0 ? `${session.message_count} 条消息` : '暂无消息'}
                </span>
                <span>·</span>
                <span>
                  {new Date(session.updated_at).toLocaleDateString('zh-CN', {
                    month: 'short',
                    day: 'numeric'
                  })}
                </span>
              </div>
            )}
          </div>

          {/* 删除按钮 */}
          <div
            style={{
              position: 'absolute',
              right: '8px',
              top: '8px',
              opacity: 0.6,
              transition: 'opacity 0.2s'
            }}
            className="delete-btn"
            onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = '0.6'}
          >
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={(e) => deleteSession(session.id, e)}
              style={{
                color: '#ff4d4f',
                border: 'none',
                boxShadow: 'none'
              }}
            />
          </div>
        </div>
      </List.Item>
    );
  };

  if (!authService.isAuthenticated()) {
    return (
      <Sider
        width={280}
        collapsedWidth={0}
        collapsed={collapsed}
        onCollapse={onCollapse}
        className="session-sidebar"
        style={{
          background: 'var(--sidebar-bg)',
          borderRight: collapsed ? 'none' : '1px solid var(--border-color)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: collapsed ? 'none' : '2px 0 8px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden'
        }}
        trigger={null}
      >
        <div style={{ padding: '16px', textAlign: 'center' }}>
          <Text type="secondary">
            {collapsed ? '登录后查看会话' : '请登录后查看会话历史'}
          </Text>
        </div>
      </Sider>
    );
  }

  return (
    <>
      {/* 移动端遮罩层 */}
      {!collapsed && (
        <div
          className="mobile-sidebar-overlay"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 1000,
            display: 'none'
          }}
          onClick={() => onCollapse(true)}
        />
      )}

      <Sider
        width={280}
        collapsedWidth={0}
        collapsed={collapsed}
        onCollapse={onCollapse}
        className="session-sidebar"
        style={{
          background: 'var(--sidebar-bg)',
          borderRight: collapsed ? 'none' : '1px solid var(--border-color)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: collapsed ? 'none' : '2px 0 8px rgba(0, 0, 0, 0.1)',
          overflow: 'hidden'
        }}
        trigger={null}
      >
        <div style={{ padding: '16px' }}>
          {/* 头部 */}
          <div style={{ marginBottom: '16px' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              {!collapsed && (
                <Title level={5} style={{ margin: 0, color: 'var(--text-primary)' }}>
                  会话历史
                </Title>
              )}
              <Space>
                <Button
                  type="primary"
                  icon={<UserOutlined />}
                  size={collapsed ? 'small' : 'default'}
                  onClick={handleCreateSession}
                style={{ borderRadius: '6px' }}
                title="新建会话"
              >
                {!collapsed && '新会话'}
              </Button>
              {!collapsed && (
                <Button
                  type="text"
                  icon={<MenuFoldOutlined />}
                  size="small"
                  onClick={() => onCollapse(true)}
                  title="收起侧边栏"
                  style={{ color: 'var(--text-secondary)' }}
                />
              )}
              </Space>
            </Space>
          </div>

          {/* 搜索框 */}
          {!collapsed && (
            <div style={{ marginBottom: '16px' }}>
              <Search
                placeholder="搜索会话..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                allowClear
                size="small"
                style={{
                  borderRadius: '8px',
                  backgroundColor: 'var(--session-hover-bg)',
                  border: '1px solid var(--border-color)'
                }}
                className="session-search"
              />
            </div>
          )}

          {/* 会话列表 */}
          <div style={{ height: 'calc(100vh - 200px)', overflowY: 'auto' }}>
            <List
              dataSource={filteredSessions}
              renderItem={renderSessionItem}
              loading={loading}
              locale={{
                emptyText: (
                  <Empty
                    description={collapsed ? '无会话' : '暂无会话历史'}
                    style={{ padding: '20px 0' }}
                  />
                )
              }}
            />
          </div>
        </div>
      </Sider>
    </>
  );
};

export default SessionSidebar;
