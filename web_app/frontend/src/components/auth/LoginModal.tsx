import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Input, Button, message, Divider } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { authService, LoginRequest, RegisterRequest } from '../../services/authService';

interface LoginModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const LoginModal: React.FC<LoginModalProps> = ({ visible, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [registerData, setRegisterData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  });
  const [validationErrors, setValidationErrors] = useState<{[key: string]: string}>({});

  // 使用 useCallback 确保函数引用稳定
  const handleClose = useCallback(() => {
    setLoginData({ username: '', password: '' });
    setRegisterData({ username: '', email: '', password: '', confirmPassword: '', full_name: '' });
    setValidationErrors({});
    setActiveTab('login');
    setLoading(false);
    onClose();
  }, [onClose]);

  const handleSuccess = useCallback(() => {
    setLoginData({ username: '', password: '' });
    setRegisterData({ username: '', email: '', password: '', confirmPassword: '', full_name: '' });
    setValidationErrors({});
    setActiveTab('login');
    setLoading(false);
    onSuccess();
    onClose();
  }, [onSuccess, onClose]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!loginData.username || !loginData.password) {
      message.error('请填写完整信息');
      return;
    }

    setLoading(true);
    try {
      // 使用与 Login 组件相同的登录逻辑
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: loginData.username,
          password: loginData.password
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '登录失败');
      }

      const data = await response.json();
      
      // 保存令牌和用户信息
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      
      message.success('登录成功！');
      
      // 确保状态更新和回调执行
      setLoginData({ username: '', password: '' });
      setValidationErrors({});
      setActiveTab('login');
      
      // 先调用成功回调，再关闭模态框
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('登录失败:', error);
      message.error(error.message || '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleTestLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/test-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '测试登录失败');
      }

      const data = await response.json();

      console.log('测试登录响应数据:', data); // 调试日志

      // 保存令牌和用户信息
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      console.log('已保存令牌和用户数据到 localStorage'); // 调试日志
      console.log('令牌:', data.access_token);
      console.log('用户:', data.user);

      message.success('测试登录成功！');

      // 确保状态更新和回调执行
      setLoginData({ username: '', password: '' });
      setValidationErrors({});
      setActiveTab('login');

      // 先调用成功回调，再关闭模态框
      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('测试登录失败:', error);
      message.error(error.message || '测试登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // 详细的前端验证
    if (!registerData.username || !registerData.email || !registerData.password) {
      message.error('请填写完整信息');
      return;
    }

    if (registerData.username.length < 3) {
      message.error('用户名至少需要3个字符');
      return;
    }

    if (registerData.username.length > 50) {
      message.error('用户名最多50个字符');
      return;
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(registerData.username)) {
      message.error('用户名只能包含字母、数字、下划线和连字符');
      return;
    }

    const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailPattern.test(registerData.email)) {
      message.error('请输入有效的邮箱地址');
      return;
    }

    if (registerData.password.length < 6) {
      message.error('密码至少需要6个字符');
      return;
    }

    // 检查密码强度（必须包含字母和数字）
    const hasLetter = /[a-zA-Z]/.test(registerData.password);
    const hasDigit = /[0-9]/.test(registerData.password);
    if (!hasLetter || !hasDigit) {
      message.error('密码必须包含字母和数字');
      return;
    }

    if (registerData.password !== registerData.confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      const { confirmPassword, ...submitData } = registerData;
      const response = await authService.register(submitData);
      message.success('注册成功！');
      
      // 注册成功后自动登录
      try {
        await authService.login({
          username: registerData.username,
          password: registerData.password
        });
        
        // 清理状态
        setRegisterData({ username: '', email: '', password: '', confirmPassword: '', full_name: '' });
        setValidationErrors({});
        setActiveTab('login');
        
        // 调用成功回调
        onSuccess();
        onClose();
      } catch (loginError) {
        // 如果自动登录失败，切换到登录标签页
        setActiveTab('login');
        message.info('注册成功，请重新登录');
      }
    } catch (error: any) {
      message.error(error.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  // 实时验证函数
  const validateField = (field: string, value: string) => {
    const errors = { ...validationErrors };

    switch (field) {
      case 'username':
        if (value.length > 0 && value.length < 3) {
          errors.username = '用户名至少需要3个字符';
        } else if (value.length > 50) {
          errors.username = '用户名最多50个字符';
        } else if (value.length > 0 && !/^[a-zA-Z0-9_-]+$/.test(value)) {
          errors.username = '只能包含字母、数字、下划线和连字符';
        } else {
          delete errors.username;
        }
        break;
      case 'email':
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (value.length > 0 && !emailPattern.test(value)) {
          errors.email = '请输入有效的邮箱地址';
        } else {
          delete errors.email;
        }
        break;
      case 'password':
        if (value.length > 0 && value.length < 6) {
          errors.password = '密码至少需要6个字符';
        } else if (value.length >= 6) {
          const hasLetter = /[a-zA-Z]/.test(value);
          const hasDigit = /[0-9]/.test(value);
          if (!hasLetter || !hasDigit) {
            errors.password = '密码必须包含字母和数字';
          } else {
            delete errors.password;
          }
        } else {
          delete errors.password;
        }
        break;
      case 'confirmPassword':
        if (value.length > 0 && value !== registerData.password) {
          errors.confirmPassword = '两次输入的密码不一致';
        } else {
          delete errors.confirmPassword;
        }
        break;
    }

    setValidationErrors(errors);
  };

  // 当模态框关闭时重置状态
  useEffect(() => {
    if (!visible) {
      setLoginData({ username: '', password: '' });
      setRegisterData({ username: '', email: '', password: '', confirmPassword: '', full_name: '' });
      setValidationErrors({});
      setActiveTab('login');
      setLoading(false);
    }
  }, [visible]);

  // 监听ESC键和防止背景滚动
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && visible) {
        event.preventDefault();
        handleClose();
      }
    };

    if (visible) {
      document.addEventListener('keydown', handleKeyDown, true);
      // 防止背景滚动
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      
      return () => {
        document.removeEventListener('keydown', handleKeyDown, true);
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [visible, handleClose]);

  // 切换标签页的处理函数
  const handleTabSwitch = useCallback((tab: string) => {
    setActiveTab(tab);
    setValidationErrors({});
  }, []);

  const loginTab = (
    <div>
      <form onSubmit={handleLogin}>
        <div style={{ marginBottom: '20px' }}>
          <Input
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="用户名或邮箱"
            value={loginData.username}
            onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
            size="large"
            style={{ borderRadius: '6px' }}
            autoComplete="username"
          />
        </div>

        <div style={{ marginBottom: '24px' }}>
          <Input
            type="password"
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="密码"
            value={loginData.password}
            onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
            size="large"
            style={{ borderRadius: '6px' }}
            autoComplete="current-password"
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            size="large"
            style={{
              borderRadius: '6px',
              height: '44px',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            登录
          </Button>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <Button
            type="default"
            loading={loading}
            block
            size="large"
            onClick={handleTestLogin}
            style={{
              borderRadius: '6px',
              height: '44px',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            测试登录（开发用）
          </Button>
        </div>
      </form>

      <Divider style={{ margin: '20px 0' }}>
        <span style={{ color: '#999', fontSize: '14px' }}>
          还没有账号？
        </span>
      </Divider>

      <Button
        type="link"
        block
        onClick={() => handleTabSwitch('register')}
        style={{
          color: '#1890ff',
          fontSize: '14px',
          height: '40px'
        }}
      >
        立即注册
      </Button>
    </div>
  );

  const registerTab = (
    <div>
      <form onSubmit={handleRegister}>
        <div style={{ marginBottom: '16px' }}>
          <Input
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="用户名（3-50个字符）"
            value={registerData.username}
            onChange={(e) => {
              const value = e.target.value;
              setRegisterData({ ...registerData, username: value });
              validateField('username', value);
            }}
            size="large"
            style={{
              borderRadius: '6px',
              borderColor: validationErrors.username ? '#ff4d4f' : undefined
            }}
            autoComplete="username"
          />
          {validationErrors.username && (
            <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>
              {validationErrors.username}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '16px' }}>
          <Input
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="邮箱地址"
            type="email"
            value={registerData.email}
            onChange={(e) => {
              const value = e.target.value;
              setRegisterData({ ...registerData, email: value });
              validateField('email', value);
            }}
            size="large"
            style={{
              borderRadius: '6px',
              borderColor: validationErrors.email ? '#ff4d4f' : undefined
            }}
            autoComplete="email"
          />
          {validationErrors.email && (
            <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>
              {validationErrors.email}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '16px' }}>
          <Input
            type="password"
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="密码（至少6个字符，包含字母和数字）"
            value={registerData.password}
            onChange={(e) => {
              const value = e.target.value;
              setRegisterData({ ...registerData, password: value });
              validateField('password', value);
              // 如果确认密码已输入，也要重新验证
              if (registerData.confirmPassword) {
                validateField('confirmPassword', registerData.confirmPassword);
              }
            }}
            size="large"
            style={{
              borderRadius: '6px',
              borderColor: validationErrors.password ? '#ff4d4f' : undefined
            }}
            autoComplete="new-password"
          />
          {validationErrors.password && (
            <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>
              {validationErrors.password}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '16px' }}>
          <Input
            type="password"
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="确认密码"
            value={registerData.confirmPassword}
            onChange={(e) => {
              const value = e.target.value;
              setRegisterData({ ...registerData, confirmPassword: value });
              validateField('confirmPassword', value);
            }}
            size="large"
            style={{
              borderRadius: '6px',
              borderColor: validationErrors.confirmPassword ? '#ff4d4f' : undefined
            }}
            autoComplete="new-password"
          />
          {validationErrors.confirmPassword && (
            <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>
              {validationErrors.confirmPassword}
            </div>
          )}
        </div>

        <div style={{ marginBottom: '20px' }}>
          <Input
            prefix={<UserOutlined style={{ color: '#1890ff' }} />}
            placeholder="真实姓名（可选）"
            value={registerData.full_name}
            onChange={(e) => setRegisterData({ ...registerData, full_name: e.target.value })}
            size="large"
            style={{ borderRadius: '6px' }}
            autoComplete="name"
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            size="large"
            style={{
              borderRadius: '6px',
              height: '44px',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            注册
          </Button>
        </div>
      </form>

      <Divider style={{ margin: '20px 0' }}>
        <span style={{ color: '#999', fontSize: '14px' }}>
          已有账号？
        </span>
      </Divider>

      <Button
        type="link"
        block
        onClick={() => handleTabSwitch('login')}
        style={{
          color: '#1890ff',
          fontSize: '14px',
          height: '40px'
        }}
      >
        立即登录
      </Button>
    </div>
  );

  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    // 点击背景关闭模态框
    if (e.target === e.currentTarget) {
      e.preventDefault();
      e.stopPropagation();
      handleClose();
    }
  }, [handleClose]);

  const handleModalClick = useCallback((e: React.MouseEvent) => {
    // 阻止模态框内部点击事件冒泡
    e.stopPropagation();
  }, []);

  if (!visible) return null;

  const modalContent = (
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
        zIndex: 10000, // 提高 z-index
        padding: '20px',
        boxSizing: 'border-box'
      }}
      onClick={handleBackdropClick}
    >
      <div 
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '32px',
          width: '420px',
          maxWidth: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          position: 'relative',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          transform: 'translateZ(0)' // 创建新的层叠上下文
        }}
        onClick={handleModalClick}
      >
        {/* 关闭按钮 */}
        <Button
          onClick={handleClose}
          style={{
            position: 'absolute',
            top: '16px',
            right: '16px',
            border: 'none',
            background: 'transparent',
            fontSize: '20px',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            zIndex: 1
          }}
        >
          ×
        </Button>

        {/* 标题 */}
        <div style={{
          textAlign: 'center',
          fontSize: '24px',
          fontWeight: 'bold',
          marginBottom: '32px',
          color: '#1890ff'
        }}>
          {activeTab === 'login' ? '登录' : '注册'} AlgoKG
        </div>

        {/* 内容 */}
        <div>
          {activeTab === 'login' ? loginTab : registerTab}
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default LoginModal;