import React, { useState, useEffect } from 'react';
import {
  Button,
  Space,
  message,
  Divider,
  Typography
} from 'antd';
import {
  UserOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { authService, User, UserProfile } from '../../services/authService';
import LoginModal from './LoginModal'; // 改用 LoginModal
import Portal from '../common/Portal';

const { Text } = Typography;

interface UserMenuProps {
  onProfileClick?: () => void;
  onFavoritesClick?: () => void;
  onHistoryClick?: () => void;
  onSettingsClick?: () => void;
  onAdminClick?: () => void;
  onLoginSuccess?: (token: string, user: any) => void;
  onLogout?: () => void;
  isAuthenticated?: boolean;
  currentUser?: any;
}

const UserMenu: React.FC<UserMenuProps> = ({
  onProfileClick,
  onFavoritesClick,
  onHistoryClick,
  onSettingsClick,
  onAdminClick,
  onLoginSuccess,
  onLogout,
  isAuthenticated: propIsAuthenticated,
  currentUser: propCurrentUser
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loginModalVisible, setLoginModalVisible] = useState(false);
  const [loading, setLoading] = useState(false);

  // 使用传入的认证状态，如果没有传入则使用自己的检查逻辑
  useEffect(() => {
    if (propIsAuthenticated !== undefined) {
      // 使用传入的认证状态
      if (propIsAuthenticated && propCurrentUser) {
        setUser(propCurrentUser);
        setUserProfile(propCurrentUser);
      } else {
        setUser(null);
        setUserProfile(null);
      }
    } else {
      // 回退到原来的检查逻辑
      checkAuthStatus();
    }
  }, [propIsAuthenticated, propCurrentUser]);

  const checkAuthStatus = async () => {
    if (authService.isAuthenticated()) {
      try {
        const currentUser = authService.getCurrentUser();
        setUser(currentUser);
        
        // 获取详细的用户资料
        const profile = await authService.getUserProfile();
        setUserProfile(profile);
      } catch (error) {
        console.error('获取用户信息失败:', error);
        // 如果令牌无效，清除本地存储
        authService.removeToken();
        setUser(null);
        setUserProfile(null);
      }
    }
  };

  const handleLogin = () => {
    setLoginModalVisible(true);
  };

  const handleLoginSuccess = async () => {
    setLoginModalVisible(false);
    
    // 如果有传入的登录成功回调，优先使用
    if (onLoginSuccess) {
      // 从 localStorage 获取令牌和用户信息
      const token = localStorage.getItem('token');
      const userStr = localStorage.getItem('user');
      if (token && userStr) {
        try {
          const userData = JSON.parse(userStr);
          onLoginSuccess(token, userData);
        } catch (error) {
          console.error('解析用户数据失败:', error);
        }
      }
    }
    
    // 无论是否有外部回调，都要更新本地状态
    if (authService.isAuthenticated()) {
      try {
        const currentUser = authService.getCurrentUser();
        setUser(currentUser);
        
        // 获取详细的用户资料
        const profile = await authService.getUserProfile();
        setUserProfile(profile);
      } catch (error) {
        console.error('获取用户信息失败:', error);
        // 如果获取用户信息失败，重新检查认证状态
        checkAuthStatus();
      }
    }
    
    message.success('登录成功！');
  };

  const handleLoginClose = () => {
    setLoginModalVisible(false);
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      // 如果有传入的退出回调，优先使用
      if (onLogout) {
        onLogout();
      } else {
        // 回退到原来的逻辑
        await authService.logout();
      }

      setUser(null);
      setUserProfile(null);
      setLoginModalVisible(false);
      message.success('已退出登录');
    } catch (error: any) {
      message.error(error.message || '退出登录失败');
    } finally {
      setLoading(false);
    }
  };

  const getUserDisplayName = () => {
    const currentUser = displayUser || user;
    if (!currentUser) return '';
    return currentUser.full_name || currentUser.username;
  };

  const getUserAvatar = () => {
    const currentUser = displayUser || user;
    return (
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          backgroundColor: currentUser ? '#1890ff' : '#d9d9d9',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          fontWeight: 'bold'
        }}
      >
        {currentUser ? getUserDisplayName().charAt(0).toUpperCase() : <UserOutlined />}
      </div>
    );
  };

  // 使用传入的认证状态，如果没有传入则使用本地状态
  const isLoggedIn = propIsAuthenticated !== undefined ? propIsAuthenticated : !!user;
  const displayUser = propCurrentUser || user;

  if (!isLoggedIn) {
    // 未登录状态
    return (
      <>
        <Button
          type="primary"
          icon={<UserOutlined />}
          loading={loading}
          onClick={handleLogin}
        >
          登录
        </Button>

        {/* 使用 LoginModal 替换原来的 Login 组件 */}
        <LoginModal
          visible={loginModalVisible}
          onClose={handleLoginClose}
          onSuccess={handleLoginSuccess}
        />
      </>
    );
  }

  // 已登录状态
  return (
    <>
      <Space>
        <Button
          type="text"
          onClick={() => onFavoritesClick && onFavoritesClick()}
          title="我的收藏"
        >
          收藏
        </Button>
        <Button
          type="text"
          onClick={() => onHistoryClick && onHistoryClick()}
          title="搜索历史"
        >
          历史
        </Button>
        <Space style={{ cursor: 'pointer' }} onClick={() => onProfileClick && onProfileClick()}>
          {getUserAvatar()}
          <span style={{ color: '#333' }}>
            {getUserDisplayName()}
          </span>
        </Space>
        <Button
          type="text"
          onClick={handleLogout}
          loading={loading}
          title="退出登录"
        >
          退出
        </Button>
      </Space>

      {/* 如果需要在登录后也能显示登录框（比如切换账号），保留这部分 */}
      <LoginModal
        visible={loginModalVisible}
        onClose={handleLoginClose}
        onSuccess={handleLoginSuccess}
      />
    </>
  );
};

export default UserMenu;