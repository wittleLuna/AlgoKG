import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Tooltip, Space, Card } from 'antd';
import { SendOutlined, BulbOutlined, StopOutlined } from '@ant-design/icons';
import { addSearchHistory } from './SearchHistory';
import { QueryInputProps } from '../../types';

const { TextArea } = Input;

const QUICK_QUERIES = [
  '请解释动态规划的概念和原理',
  '推荐一些二叉树的中等难度题目',
  '基于两数之和这道题，推荐相似的题目',
  '什么是回溯算法，有哪些典型应用',
  '解释时间复杂度和空间复杂度的区别',
  '推荐一些适合初学者的算法题目',
];

const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  loading = false,
  placeholder = '请输入您的问题...',
  onCancel,
  isStreaming = false,
}) => {
  const [query, setQuery] = useState('');
  const [showQuickQueries, setShowQuickQueries] = useState(false);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const textAreaRef = useRef<any>(null);

  // 自动聚焦
  useEffect(() => {
    if (textAreaRef.current) {
      textAreaRef.current.focus();
    }
  }, []);

  const handleSubmit = () => {
    if (query.trim() && !loading) {
      const trimmedQuery = query.trim();
      addSearchHistory(trimmedQuery); // 添加到搜索历史
      onSubmit(trimmedQuery);
      setQuery('');
      setShowQuickQueries(false);
    }
  };



  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleQuickQuery = (quickQuery: string) => {
    setQuery(quickQuery);
    setShowQuickQueries(false);
    // 自动提交快速查询
    setTimeout(() => {
      onSubmit(quickQuery);
      setQuery('');
    }, 100);
  };

  return (
    <div className="query-input-container">
      {/* 快速查询建议面板 */}
      {showQuickQueries && (
        <Card
          className="quick-queries-panel"
          style={{
            marginBottom: 16,
            borderRadius: 12,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
            animation: 'slideDown 0.3s ease-out'
          }}
        >
          <div className="quick-queries-header">
            <BulbOutlined style={{ color: '#1890ff', marginRight: 8 }} />
            <span style={{ fontWeight: 500, color: '#1890ff' }}>快速查询建议</span>
          </div>
          <div className="quick-queries-grid">
            {QUICK_QUERIES.map((quickQuery, index) => (
              <div
                key={index}
                className="quick-query-item"
                onClick={() => handleQuickQuery(quickQuery)}
                style={{
                  padding: '12px 16px',
                  margin: '8px 0',
                  background: '#f8f9fa',
                  borderRadius: 8,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  border: '1px solid #e9ecef'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = '#e3f2fd';
                  e.currentTarget.style.borderColor = '#1890ff';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = '#f8f9fa';
                  e.currentTarget.style.borderColor = '#e9ecef';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                {quickQuery}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 主输入区域 - ChatGPT风格 */}
      <div className={`main-input-container ${isInputFocused ? 'focused' : ''}`}>
        <div className="input-wrapper">
          <TextArea
            ref={textAreaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            onFocus={() => setIsInputFocused(true)}
            onBlur={() => setIsInputFocused(false)}
            placeholder={placeholder}
            autoSize={{ minRows: 1, maxRows: 6 }}
            disabled={loading}
            className="modern-textarea"
            style={{
              border: 'none',
              outline: 'none',
              resize: 'none',
              fontSize: '16px',
              lineHeight: '24px',
              padding: '12px 16px',
              background: 'transparent'
            }}
          />

          <div className="input-actions-inline">
            <Space size={8}>
              <Tooltip title="快速查询建议">
                <Button
                  type="text"
                  icon={<BulbOutlined />}
                  onClick={() => {
                    setShowQuickQueries(!showQuickQueries);
                  }}
                  className={`action-button ${showQuickQueries ? 'active' : ''}`}
                  style={{
                    color: showQuickQueries ? '#1890ff' : '#8c8c8c',
                    border: 'none',
                    background: 'transparent'
                  }}
                />
              </Tooltip>

              {isStreaming && onCancel ? (
                <Button
                  type="text"
                  danger
                  icon={<StopOutlined />}
                  onClick={onCancel}
                  className="action-button stop-button"
                  style={{
                    color: '#ff4d4f',
                    border: 'none',
                    background: 'transparent'
                  }}
                />
              ) : (
                <Button
                  type="text"
                  icon={<SendOutlined />}
                  onClick={handleSubmit}
                  loading={loading}
                  disabled={!query.trim() || loading || isStreaming}
                  className="send-button-modern"
                  style={{
                    color: query.trim() && !loading && !isStreaming ? '#1890ff' : '#8c8c8c',
                    border: 'none',
                    background: 'transparent',
                    transform: query.trim() && !loading && !isStreaming ? 'scale(1.1)' : 'scale(1)',
                    transition: 'all 0.2s ease'
                  }}
                />
              )}
            </Space>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryInput;
