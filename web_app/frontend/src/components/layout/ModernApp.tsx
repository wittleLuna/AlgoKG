import React, { useState, useEffect, useCallback } from 'react';
import { Layout, ConfigProvider, message } from 'antd';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';

import ModernHeader from './ModernHeader';
import ModernSidebar from './ModernSidebar';
import ChatInterface from '../chat/ChatInterface';
import Neo4jGraphPage from '../../pages/Neo4jGraphPage';
import EnhancedProblemDetail from '../problem/EnhancedProblemDetail';
import SmartRecommendationSystem from '../recommendation/SmartRecommendationSystem';
import ModernReasoningProgress from '../reasoning/ModernReasoningProgress';

import { modernTheme, antdTheme } from '../../styles/theme';
import { useAppStore, useAppActions } from '../../store';
import { apiService } from '../../services/api';
import { QARequest, ChatMessage, GraphNode } from '../../types';

const { Content } = Layout;

const StyledLayout = styled(Layout)`
  min-height: 100vh;
  background: ${modernTheme.colors.background.tertiary};
`;

const StyledContent = styled(Content)`
  margin: 0;
  padding: 0;
  background: transparent;
  overflow: hidden;
`;

const ContentContainer = styled(motion.div)`
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: ${modernTheme.colors.background.primary};
  border-radius: 24px 0 0 0;
  box-shadow: ${modernTheme.shadows.xl};
  overflow: hidden;
`;

const MainContent = styled.div`
  flex: 1;
  display: flex;
  overflow: hidden;
`;

const ChatContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  background: ${modernTheme.colors.background.primary};
`;

const SidePanel = styled(motion.div)<{ isVisible: boolean }>`
  width: ${props => props.isVisible ? '400px' : '0'};
  background: ${modernTheme.colors.background.secondary};
  border-left: 1px solid ${modernTheme.colors.border.light};
  overflow: hidden;
  transition: width 0.3s ease;
`;

interface ModernAppProps {}

const ModernApp: React.FC<ModernAppProps> = () => {
  const {
    messages,
    currentQuery,
    isLoading,
    isStreaming,
    sidebarCollapsed
  } = useAppStore();

  const {
    setCurrentQuery,
    addMessage,
    updateMessage,
    setLoading,
    setStreaming,
    setSidebarCollapsed
  } = useAppActions();

  const [activeTab, setActiveTab] = useState('chat');
  const [showSidePanel, setShowSidePanel] = useState(false);
  const [sidePanelContent, setSidePanelContent] = useState<'reasoning' | 'recommendations' | 'problem' | null>(null);
  const [currentReasoningSteps, setCurrentReasoningSteps] = useState<any[]>([]);
  const [currentRecommendations, setCurrentRecommendations] = useState<any[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<any>(null);

  // 处理查询提交
  const handleQuerySubmit = useCallback(async (query: string) => {
    if (!query.trim() || isLoading) return;

    setCurrentQuery(query);
    setLoading(true);
    setStreaming(true);

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // 添加助手消息占位符
    const assistantMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    addMessage(assistantMessage);

    try {
      // 重置推理步骤
      setCurrentReasoningSteps([]);
      setSidePanelContent('reasoning');
      setShowSidePanel(true);

      const request: QARequest = {
        query,
      };

      // 调用QA API
      const response = await apiService.query(request);

      updateMessage(assistantMessage.id, {
        content: response.integrated_response || '',
        response: response,
        isStreaming: false,
      });

      // 设置推荐数据
      if (response.similar_problems?.length > 0) {
        setCurrentRecommendations(response.similar_problems);
      }

      setStreaming(false);
      setLoading(false);
    } catch (error) {
      console.error('查询失败:', error);
      updateMessage(assistantMessage.id, {
        content: '抱歉，处理您的请求时出现了错误，请稍后重试。',
        isStreaming: false,
      });
      setStreaming(false);
      setLoading(false);
      message.error('查询失败，请重试');
    }
  }, [isLoading, messages, addMessage, updateMessage, setCurrentQuery, setLoading, setStreaming]);

  // 处理概念点击
  const handleConceptClick = useCallback((concept: string) => {
    handleQuerySubmit(`请解释${concept}的概念和原理`);
  }, [handleQuerySubmit]);

  // 处理题目点击
  const handleProblemClick = useCallback((problem: any) => {
    setSelectedProblem(problem);
    setSidePanelContent('problem');
    setShowSidePanel(true);
  }, []);

  // 处理推荐点击
  const handleRecommendationClick = useCallback(() => {
    setSidePanelContent('recommendations');
    setShowSidePanel(true);
  }, []);

  // 渲染侧边面板内容
  const renderSidePanelContent = () => {
    switch (sidePanelContent) {
      case 'reasoning':
        return (
          <ModernReasoningProgress
            steps={currentReasoningSteps}
            currentStep={currentReasoningSteps.findIndex(s => s.status === 'running')}
            isComplete={currentReasoningSteps.every(s => s.status === 'completed' || s.status === 'error')}
          />
        );
      case 'recommendations':
        return (
          <SmartRecommendationSystem
            similarProblems={currentRecommendations}
            isLoading={isLoading}
            onProblemClick={handleProblemClick}
            onRefresh={() => {
              // 重新获取推荐
              if (currentQuery) {
                handleQuerySubmit(currentQuery);
              }
            }}
          />
        );
      case 'problem':
        return selectedProblem ? (
          <EnhancedProblemDetail
            problemData={selectedProblem}
            onTagClick={(tag, type) => {
              handleQuerySubmit(`请介绍${tag}相关的算法和题目`);
            }}
            onSimilarProblems={() => {
              setSidePanelContent('recommendations');
            }}
          />
        ) : null;
      default:
        return null;
    }
  };

  // 渲染主要内容
  const renderMainContent = () => {
    switch (activeTab) {
      case 'chat':
        return (
          <ChatContainer>
            <ChatInterface
              messages={messages}
              onSubmit={handleQuerySubmit}
              isLoading={isLoading}
              isStreaming={isStreaming}
              onConceptClick={handleConceptClick}
              onProblemClick={handleProblemClick}
              onRecommendationClick={handleRecommendationClick}
            />
          </ChatContainer>
        );
      case 'graph':
        return <Neo4jGraphPage />;
      default:
        return null;
    }
  };

  return (
    <ConfigProvider theme={antdTheme}>
      <StyledLayout>
        <ModernSidebar
          collapsed={sidebarCollapsed}
          onCollapse={setSidebarCollapsed}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
        
        <Layout>
          <ModernHeader
            onSidePanelToggle={() => setShowSidePanel(!showSidePanel)}
            showSidePanel={showSidePanel}
            sidePanelContent={sidePanelContent}
          />
          
          <StyledContent>
            <ContentContainer
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <MainContent>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.3 }}
                    style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
                  >
                    {renderMainContent()}
                  </motion.div>
                </AnimatePresence>
                
                <SidePanel isVisible={showSidePanel}>
                  <AnimatePresence>
                    {showSidePanel && (
                      <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 50 }}
                        transition={{ duration: 0.3 }}
                        style={{ height: '100%', padding: '16px' }}
                      >
                        {renderSidePanelContent()}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </SidePanel>
              </MainContent>
            </ContentContainer>
          </StyledContent>
        </Layout>
      </StyledLayout>
    </ConfigProvider>
  );
};

export default ModernApp;
