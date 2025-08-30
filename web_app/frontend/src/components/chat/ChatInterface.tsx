import React, { useState } from 'react';
import { Card, Input, Button, Space } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import MessageItem from '../qa/MessageItem';
import { ChatMessage } from '../../types';

const { TextArea } = Input;

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSubmit: (query: string) => void;
  isLoading: boolean;
  isStreaming: boolean;
  onConceptClick?: (concept: string) => void;
  onProblemClick?: (problem: any) => void;
  onRecommendationClick?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  onSubmit,
  isLoading,
  isStreaming,
  onConceptClick,
  onProblemClick,
  onRecommendationClick
}) => {
  const [inputValue, setInputValue] = useState('');

  const handleSubmit = () => {
    if (!inputValue.trim() || isLoading) return;
    
    onSubmit(inputValue.trim());
    setInputValue('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, padding: '16px', overflowY: 'auto' }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧠</div>
            <h2>欢迎使用 AlgoKG 智能助手</h2>
            <p>我可以帮您解答算法问题、解释概念、推荐相关题目</p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageItem
              key={message.id}
              message={message}
              onConceptClick={onConceptClick}
              onProblemClick={onProblemClick}
            />
          ))
        )}
      </div>

      <Card style={{ margin: '16px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <TextArea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="请输入您的问题..."
            autoSize={{ minRows: 1, maxRows: 4 }}
            disabled={isLoading}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSubmit}
            disabled={isLoading || !inputValue.trim()}
            loading={isLoading}
          >
            发送
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default ChatInterface;
