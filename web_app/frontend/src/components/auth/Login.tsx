import React, { useState } from 'react';
import { Button, Card, Input, Space, message } from 'antd';
import { UserOutlined, LikeOutlined } from '@ant-design/icons';
import LoginModal from './LoginModal';  // 引入 LoginModal 组件

interface LoginProps {
  onLoginSuccess?: (token: string, user: any) => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [visible, setVisible] = useState(false);  // 控制 LoginModal 的显示

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleLogin = async () => {
    if (!formData.username.trim() || !formData.password.trim()) {
      message.error('请输入用户名和密码');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: formData.username,
          password: formData.password
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '登录失败');
      }

      const data = await response.json();
      
      // 保存令牌
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      message.success('登录成功！');
      
      if (onLoginSuccess) {
        onLoginSuccess(data.access_token, data.user);
      }

    } catch (error: any) {
      console.error('登录失败:', error);
      message.error(error.message || '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const showLoginModal = () => {
    setVisible(true);  // 打开 LoginModal 模态框
  };

  const closeLoginModal = () => {
    setVisible(false);  // 关闭 LoginModal 模态框
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '60vh',
      padding: '20px'
    }}>
      <Card title="用户登录" style={{ width: 400 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              用户名
            </label>
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
              value={formData.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              密码
            </label>
            <Input
              type="password"
              prefix={<LikeOutlined />}
              placeholder="请输入密码"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
            />
          </div>

          <Space direction="vertical" style={{ width: '100%' }}>
            <Button
              type="primary"
              loading={loading}
              onClick={handleLogin}
              style={{ width: '100%' }}
            >
              登录
            </Button>
          </Space>

          {/* 立即注册按钮 */}
          <Button
            type="link"
            onClick={showLoginModal}  // 显示 LoginModal
            style={{
              color: '#1890ff',
              fontSize: '14px',
              marginTop: '10px',
            }}
          >
            立即注册
          </Button>
        </div>
      </Card>

      {/* LoginModal 组件用于弹出登录或注册表单 */}
      <LoginModal
        visible={visible}
        onClose={closeLoginModal}  // 关闭模态框
        onSuccess={() => console.log('成功登录或注册')}
      />
    </div>
  );
};

export default Login;
