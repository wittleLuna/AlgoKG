import React, { useState, useEffect, useCallback } from 'react';
import { Layout, Tabs, Button, Space, message, Spin, Alert } from 'antd';
import {
  MessageOutlined,
  NodeIndexOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BulbOutlined,
  CodeOutlined,
  UserOutlined,
  LeftOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { useTheme } from './hooks/useTheme';
import QueryInput from './components/common/QueryInput';
import MessageItem from './components/qa/MessageItem';
import UnifiedGraphPage from './pages/UnifiedGraphPage';
import AlgorithmVisualizationPage from './pages/AlgorithmVisualizationPage';
import UserMenu from './components/auth/UserMenu';
import FavoritesPanel from './components/user/FavoritesPanel';
import NoteUpload from './components/notes/NoteUpload';
import NoteList from './components/notes/NoteList';
import NoteDetail from './components/notes/NoteDetail';
import EntityGraphVisualization from './components/notes/EntityGraphVisualization';
import Login from './components/auth/LoginModal';
import SearchHistoryPanel from './components/user/SearchHistoryPanel';
import SessionSidebar from './components/chat/SessionSidebar';
import { useAppStore, useAppActions } from './store';
import { apiService } from './services/api';
import { authService } from './services/authService';
import { QARequest, ChatMessage, GraphNode } from './types';
import './App.css';
import './components/components.css';

const { Header, Sider, Content } = Layout;
const { TabPane } = Tabs;

const App: React.FC = () => {
  const {
    messages,
    currentQuery,
    isLoading,
    isStreaming,
    theme,
    sidebarCollapsed,
    activeTab,
    graphData,
    selectedNode,
    error,
    sessionId
  } = useAppStore();

  // 认证相关状态
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<any>(null);

  // 笔记相关状态
  const [noteUploadVisible, setNoteUploadVisible] = useState(false);
  const [selectedNote, setSelectedNote] = useState<any>(null);
  const [showNoteDetail, setShowNoteDetail] = useState(false);
  const [showEntityGraph, setShowEntityGraph] = useState(false);
  const [entityGraphNote, setEntityGraphNote] = useState<any>(null);

  const {
    setCurrentQuery,
    setLoading,
    setStreaming,
    addMessage,
    updateMessage,
    clearMessages,
    setTheme,
    setSidebarCollapsed,
    setActiveTab,
    setGraphData,
    setSelectedNode,
    setError,
    handleQueryResponse,
    handleStreamingStep,
    abortController,
    setAbortController,
    cancelCurrentRequest
  } = useAppActions();

  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [favoritesVisible, setFavoritesVisible] = useState(false);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string>(sessionId);

  // 健康检查
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiService.healthCheck();
        setHealthStatus('healthy');
      } catch (error) {
        console.error('健康检查失败:', error);
        setHealthStatus('unhealthy');
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // 每30秒检查一次
    return () => clearInterval(interval);
  }, []);

  // 认证处理
  const checkAuthStatus = useCallback(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');

    console.log('检查认证状态:', { token: !!token, user: !!user }); // 调试日志

    if (token && user) {
      try {
        const userData = JSON.parse(user);
        console.log('设置认证状态为 true, 用户:', userData); // 调试日志
        setIsAuthenticated(true);
        setCurrentUser(userData);
      } catch (error) {
        console.error('解析用户数据失败:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setCurrentUser(null);
      }
    } else {
      console.log('没有令牌或用户数据，设置为未认证'); // 调试日志
      setIsAuthenticated(false);
      setCurrentUser(null);
    }
  }, []);

  const handleLoginSuccess = useCallback((token: string, user: any) => {
    setIsAuthenticated(true);
    setCurrentUser(user);
  }, []);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setCurrentUser(null);
    message.success('已退出登录');
  }, []);

  // 笔记处理
  const handleNoteUploadSuccess = useCallback((noteId: string) => {
    message.success('笔记上传成功！');
    setNoteUploadVisible(false);
    // 如果当前在笔记标签页，刷新列表
    if (activeTab === 'notes') {
      // 这里可以触发笔记列表刷新
    }
  }, [activeTab]);

  const handleNoteUploadCancel = useCallback(() => {
    setNoteUploadVisible(false);
  }, []);

  const handleNoteSelect = useCallback((note: any) => {
    setSelectedNote(note);
    setShowNoteDetail(true);
  }, []);

  const handleNoteDetailBack = useCallback(() => {
    setShowNoteDetail(false);
    setSelectedNote(null);
  }, []);

  const handleEntityVisualize = useCallback((note: any) => {
    console.log('打开实体图谱可视化:', note);
    setEntityGraphNote(note);
    setShowEntityGraph(true);
  }, []);

  // 认证状态检查
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // 立即检查认证状态（组件挂载时）
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');

    console.log('组件挂载时检查认证状态:', { token: !!token, user: !!user });

    if (token && user) {
      try {
        const userData = JSON.parse(user);
        console.log('组件挂载时设置认证状态为 true');
        setIsAuthenticated(true);
        setCurrentUser(userData);
      } catch (error) {
        console.error('组件挂载时解析用户数据失败:', error);
        setIsAuthenticated(false);
        setCurrentUser(null);
      }
    } else {
      setIsAuthenticated(false);
      setCurrentUser(null);
    }
  }, []); // 空依赖数组，只在组件挂载时执行一次

  // 添加搜索历史
  const addToSearchHistory = useCallback(async (query: string, searchType: string, resultsCount = 0) => {
    if (authService.isAuthenticated()) {
      try {
        await authService.addSearchHistory(query, searchType, resultsCount);
      } catch (error) {
        console.warn('添加搜索历史失败:', error);
      }
    }
  }, []);

  // 处理搜索历史点击
  const handleSearchHistoryClick = useCallback((query: string, searchType: string) => {
    setCurrentQuery(query);
    if (searchType === 'qa') {
      setActiveTab('chat');
      handleQuerySubmit(query);
    } else if (searchType === 'graph') {
      setActiveTab('graph');
    }
    setHistoryVisible(false);
  }, []);

  // 处理会话选择
  const handleSessionSelect = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
    // 这里可以加载会话的历史消息
    console.log('切换到会话:', sessionId);
  }, []);

  // 处理新建会话
  const handleNewSession = useCallback(() => {
    const newSessionId = Math.random().toString(36).substr(2, 9);
    setCurrentSessionId(newSessionId);
    clearMessages();
    console.log('创建新会话:', newSessionId);
  }, [clearMessages]);

  // 处理查询提交
  const handleQuerySubmit = useCallback(async (query: string) => {
    if (!query.trim() || isLoading || isStreaming) return;

    // 如果是新会话的第一条消息，且用户已登录，创建会话
    if (messages.length === 0 && authService.isAuthenticated()) {
      try {
        const newSession = await authService.createSession({
          title: query.length > 20 ? `${query.substring(0, 20)}...` : query,
          description: '智能问答会话'
        });
        setCurrentSessionId(newSession.id.toString());
        console.log('自动创建新会话:', newSession);
      } catch (error) {
        console.error('创建会话失败:', error);
        // 继续执行查询，不因为会话创建失败而中断
      }
    }

    // 取消之前的请求
    if (abortController) {
      abortController.abort();
    }

    // 创建新的AbortController
    const newAbortController = new AbortController();
    setAbortController(newAbortController);

    setError(undefined);
    setLoading(true);

    const request: QARequest = {
      query: query.trim(),
      session_id: sessionId,
      context: {
        previous_queries: messages.slice(-5).map(m => m.content)
      }
    };

    try {
      // 使用流式响应
      const messageId = Math.random().toString(36).substr(2, 9);

      // 添加用户消息
      const userMessage: ChatMessage = {
        id: Math.random().toString(36).substr(2, 9),
        type: 'user',
        content: query,
        timestamp: new Date()
      };
      addMessage(userMessage);

      // 添加助手消息占位符
      const assistantMessage: ChatMessage = {
        id: messageId,
        type: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
        reasoning_steps: []
      };
      addMessage(assistantMessage);

      setStreaming(true);
      setLoading(false);

      // 处理流式响应
      try {
        for await (const chunk of apiService.queryStream(request, newAbortController.signal)) {
          // 检查是否已被取消
          if (newAbortController.signal.aborted) {
            console.log('请求已被取消');
            break;
          }
          if (chunk.type === 'step') {
            // 更新推理步骤
            console.log('收到步骤数据:', chunk.data);
            handleStreamingStep({
              agent_name: chunk.data.agent_name || chunk.data.agent || 'system',
              step_type: chunk.data.step_type || 'processing',
              description: chunk.data.description || '',
              status: 'processing',
              start_time: chunk.data.start_time || new Date().toISOString(),
              confidence: chunk.data.confidence
            }, messageId);
          } else if (chunk.type === 'step_complete') {
            // 步骤完成
            console.log('收到步骤完成数据:', chunk.data);
            handleStreamingStep({
              agent_name: chunk.data.agent_name || chunk.data.agent || 'system',
              step_type: chunk.data.step_type || 'processing',
              description: chunk.data.description || '',
              status: chunk.data.status || 'success',
              start_time: chunk.data.start_time || new Date().toISOString(),
              end_time: chunk.data.end_time || new Date().toISOString(),
              confidence: chunk.data.confidence,
              result: chunk.data.result
            }, messageId);
          } else if (chunk.type === 'final_result') {
            // 最终结果
            const response = chunk.data;
            console.log('最终结果数据:', response);
            console.log('推理路径数据:', response.reasoning_path);

            // 确保内容是字符串
            let content = response.integrated_response;
            if (typeof content !== 'string') {
              if (content && typeof content === 'object') {
                content = JSON.stringify(content);
              } else {
                content = String(content || '正在生成回答...');
              }
            }

            updateMessage(messageId, {
              content: content,
              response: response as any,
              reasoning_steps: response.reasoning_path || [],
              isStreaming: false
            });

            // 更新图谱数据
            if (response.graph_data) {
              setGraphData(response.graph_data);
            }

            // 添加到搜索历史
            addToSearchHistory(query, 'qa', 1);
          } else if (chunk.type === 'error') {
            throw new Error(chunk.data.error);
          }
        }
      } catch (streamError: any) {
        console.error('流式处理错误:', streamError);

        // 检查是否是用户主动取消的请求
        if (streamError.name === 'AbortError' ||
            streamError.code === 'ERR_CANCELED' ||
            streamError.message?.includes('canceled') ||
            streamError.message?.includes('请求已取消')) {
          console.log('流式请求被用户取消');
          return; // 不继续处理
        }

        // 回退到普通请求
        try {
          const response = await apiService.query(request, newAbortController.signal);
          updateMessage(messageId, {
            content: response.integrated_response,
            response: response,
            isStreaming: false
          });

          if (response.graph_data) {
            setGraphData(response.graph_data);
          }
        } catch (fallbackError: any) {
          // 如果回退请求也失败，检查是否是取消操作
          if (fallbackError.name === 'AbortError' ||
              fallbackError.code === 'ERR_CANCELED' ||
              fallbackError.message?.includes('canceled')) {
            return; // 不显示错误
          }
          throw fallbackError; // 重新抛出其他错误
        }
      }

    } catch (error: any) {
      console.error('查询失败:', error);

      // 检查是否是用户主动取消的请求
      if (error.name === 'AbortError' ||
          error.code === 'ERR_CANCELED' ||
          error.message?.includes('canceled') ||
          error.message?.includes('请求已取消')) {
        console.log('用户主动取消请求，不显示错误提示');
        return; // 不显示错误提示
      }

      setError(error.message || '查询失败，请稍后重试');
      message.error('查询失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }, [isLoading, isStreaming, sessionId, messages, addMessage, updateMessage, handleStreamingStep, setError, setLoading, setStreaming, setGraphData]);

  // 处理概念点击 - 修改为直接发送用户消息
  const handleConceptClick = useCallback(async (concept: string) => {
    console.log('概念点击:', concept);

    // 显示用户反馈
    message.info(`正在为您查询"${concept}"的相关信息...`);

    // 切换到智能问答标签页
    setActiveTab('chat');

    // 构造用户查询消息
    const userQuery = `请详细解释${concept}的概念`;

    // 直接调用查询处理函数，就像用户输入了这个问题一样
    await handleQuerySubmit(userQuery);

  }, [setActiveTab, handleQuerySubmit]);

  // 处理题目点击 - 修改为直接发送用户消息
  const handleProblemClick = useCallback(async (problemTitle: string) => {
    console.log('题目点击:', problemTitle);

    // 显示用户反馈
    message.info(`正在为您分析"${problemTitle}"题目...`);

    // 切换到智能问答标签页
    setActiveTab('chat');

    // 构造用户查询消息
    const userQuery = `请分析${problemTitle}这道题目，包括解题思路和代码实现`;

    // 直接调用查询处理函数，就像用户输入了这个问题一样
    await handleQuerySubmit(userQuery);

  }, [setActiveTab, handleQuerySubmit]);

  // 处理图谱节点点击
  const handleGraphNodeClick = useCallback(async (node: GraphNode) => {
    setSelectedNode(node);
    
    if (node.type === 'Problem') {
      await handleProblemClick(node.label);
    } else {
      await handleConceptClick(node.label);
    }
  }, [setSelectedNode, handleProblemClick, handleConceptClick]);

  // 渲染健康状态
  const renderHealthStatus = () => {
    if (healthStatus === 'checking') {
      return <Spin size="small" />;
    } else if (healthStatus === 'unhealthy') {
      return (
        <Alert
          message="服务连接异常"
          description="无法连接到后端服务，请检查服务状态"
          type="error"
          showIcon
          style={{ margin: '16px 0' }}
        />
      );
    }
    return null;
  };

  return (
    <Layout className={`app-layout theme-${theme}`}>
      {/* 会话管理侧边栏 */}
      <SessionSidebar
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />

      {/* 浮动展开按钮 */}
      {sidebarCollapsed && (
        <Button
          type="primary"
          icon={<MenuUnfoldOutlined />}
          size="large"
          onClick={() => setSidebarCollapsed(false)}
          style={{
            position: 'fixed',
            top: '20px',
            left: '20px',
            zIndex: 1002,
            borderRadius: '50%',
            width: '48px',
            height: '48px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            transition: 'all 0.3s ease'
          }}
          className="floating-menu-btn"
        />
      )}

      {/* 主内容区 */}
      <Layout className="main-layout">
        {/* 顶部导航 */}
        <Header className="app-header">
          <div className="header-left">
            <Button
              type="text"
              icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="collapse-button"
            />
            <div className="header-title">
              AlgoKG智能问答系统
            </div>
          </div>

          <div className="header-right">
            {renderHealthStatus()}
            <Button
              type="text"
              icon={theme === 'dark' ? <UserOutlined /> : <LeftOutlined />}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="theme-button"
              title={theme === 'dark' ? '切换到浅色主题' : '切换到深色主题'}
            />

            <UserMenu
              onFavoritesClick={() => setFavoritesVisible(true)}
              onHistoryClick={() => setHistoryVisible(true)}
              onSettingsClick={() => message.info('个人设置功能开发中...')}
              onAdminClick={() => message.info('管理后台功能开发中...')}
              onLoginSuccess={handleLoginSuccess}
              onLogout={handleLogout}
              isAuthenticated={isAuthenticated}
              currentUser={currentUser}
            />

            {/* 调试按钮 */}
            <Button
              type="text"
              onClick={() => {
                checkAuthStatus();
                const token = localStorage.getItem('token');
                const user = localStorage.getItem('user');
                console.log('手动检查认证状态:', {
                  token: !!token,
                  user: !!user,
                  isAuthenticated,
                  currentUser
                });
                message.info(`认证状态: ${isAuthenticated ? '已登录' : '未登录'}`);
              }}
              style={{ marginLeft: 8, fontSize: '12px' }}
            >
              检查状态
            </Button>
          </div>
        </Header>

        {/* 内容区 */}
        <Content className="app-content">
          {error && (
            <Alert
              message="系统错误"
              description={error}
              type="error"
              closable
              onClose={() => setError(undefined)}
              style={{ marginBottom: 16 }}
            />
          )}

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            className="content-tabs"
          >
            <TabPane
              tab={
                <span>
                  <MessageOutlined />
                  智能问答
                </span>
              }
              key="chat"
            >
              <div className="chat-container">
                <div className="messages-container">
                  {messages.map((message) => (
                    <MessageItem
                      key={message.id}
                      message={message}
                      onConceptClick={handleConceptClick}
                      onProblemClick={handleProblemClick}
                    />
                  ))}
                  
                  {messages.length === 0 && (
                    <div className="welcome-message">
                      <div className="welcome-content">
                        <BulbOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
                        <h2>欢迎使用AlgoKG智能问答系统</h2>
                        <p>我是您的算法学习助手，可以帮您：</p>
                        <ul>
                          <li>解释算法和数据结构概念</li>
                          <li>推荐相关练习题目</li>
                          <li>分析题目解法和代码实现</li>
                          <li>构建个性化学习路径</li>
                        </ul>
                        <p>请在下方输入您的问题开始对话！</p>
                      </div>
                    </div>
                  )}
                </div>

                <div className="input-container">
                  <QueryInput
                    onSubmit={handleQuerySubmit}
                    loading={isLoading}
                    isStreaming={isStreaming}
                    onCancel={cancelCurrentRequest}
                    placeholder="请输入您的问题，比如：请解释动态规划的概念和原理"
                  />
                </div>
              </div>
            </TabPane>

            <TabPane
              tab={
                <span>
                  <NodeIndexOutlined />
                  知识图谱
                </span>
              }
              key="knowledge-graph"
            >
              <UnifiedGraphPage />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <CodeOutlined />
                  算法可视化
                </span>
              }
              key="algorithm-visualization"
            >
              <AlgorithmVisualizationPage />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <FilterOutlined />
                  笔记管理
                </span>
              }
              key="notes"
            >
              {!isAuthenticated ? (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '400px',
                  textAlign: 'center'
                }}>
                  <div style={{ marginBottom: '24px' }}>
                    <FilterOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
                    <h3 style={{ color: '#666' }}>笔记管理</h3>
                    <p style={{ color: '#999', marginBottom: '24px' }}>
                      请先登录后再管理您的笔记
                    </p>
                  </div>
                  <div style={{ color: '#999', fontSize: '14px' }}>
                    <p>登录后您可以：</p>
                    <ul style={{ textAlign: 'left', marginTop: '8px' }}>
                      <li>📝 上传和管理笔记</li>
                      <li>🔍 查看提取的实体信息</li>
                      <li>🎯 实体知识图谱可视化</li>
                      <li>🔄 重新抽取实体</li>
                      <li>🗑️ 删除不需要的笔记</li>
                    </ul>
                    <p style={{ marginTop: '16px', color: '#1890ff' }}>
                      👆 请点击右上角的用户图标进行登录
                    </p>
                  </div>
                </div>
              ) : showNoteDetail && selectedNote ? (
                <NoteDetail
                  note={selectedNote}
                  onBack={handleNoteDetailBack}
                  onEntityVisualize={handleEntityVisualize}
                />
              ) : (
                <NoteList
                  onNoteSelect={handleNoteSelect}
                  onNoteDelete={() => {
                    // 刷新列表的逻辑可以在这里添加
                  }}
                  onUploadClick={() => setNoteUploadVisible(true)}
                  onEntityVisualize={handleEntityVisualize}
                />
              )}
            </TabPane>
          </Tabs>
        </Content>
      </Layout>

      {/* 用户面板 */}
      <FavoritesPanel
        visible={favoritesVisible}
        onClose={() => setFavoritesVisible(false)}
      />

      <SearchHistoryPanel
        visible={historyVisible}
        onClose={() => setHistoryVisible(false)}
        onSearchClick={handleSearchHistoryClick}
      />

      {/* 笔记上传面板 */}
      {noteUploadVisible && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          onClick={handleNoteUploadCancel}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: 8,
              padding: 24,
              maxWidth: 900,
              width: '90%',
              maxHeight: '90%',
              overflow: 'auto',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <NoteUpload
              onUploadSuccess={handleNoteUploadSuccess}
              onCancel={handleNoteUploadCancel}
            />
          </div>
        </div>
      )}

      {/* 实体图谱可视化模态框 */}
      {showEntityGraph && entityGraphNote && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            zIndex: 999999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '20px'
          }}
          onClick={() => setShowEntityGraph(false)}
        >
          <div
            style={{
              backgroundColor: 'white',
              borderRadius: 8,
              width: '95%',
              height: '90%',
              maxWidth: '1200px',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
              display: 'flex',
              flexDirection: 'column'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <EntityGraphVisualization
              noteId={entityGraphNote.id}
              onClose={() => setShowEntityGraph(false)}
            />
          </div>
        </div>
      )}
    </Layout>
  );
};

export default App;
