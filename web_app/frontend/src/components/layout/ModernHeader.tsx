import React from 'react';
import { Layout, Space, Button, Typography, Tooltip } from 'antd';
import {
  SettingOutlined,
  UserOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  QuestionCircleOutlined,
  SendOutlined,
  LinkOutlined,
  RobotOutlined
} from '@ant-design/icons';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { modernTheme } from '../../styles/theme';

const { Header } = Layout;
const { Title, Text } = Typography;

const StyledHeader = styled(Header)`
  background: linear-gradient(135deg, ${modernTheme.colors.primary[600]} 0%, ${modernTheme.colors.secondary[600]} 100%);
  border-bottom: 1px solid ${modernTheme.colors.border.light};
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: ${modernTheme.shadows.md};
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="60" r="0.5" fill="white" opacity="0.1"/><circle cx="90" cy="40" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    pointer-events: none;
  }
`;

const LogoContainer = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
`;

const LogoIcon = styled(motion.div)`
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #fff 0%, #f0f9ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: ${modernTheme.shadows.md};
`;

const HeaderActions = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
`;

const StatusIndicator = styled(motion.div)<{ isActive: boolean }>`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: ${props => props.isActive ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.1)'};
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.2);
  backdrop-filter: blur(10px);
`;

const SidePanelToggle = styled(Button)<{ isActive: boolean }>`
  background: ${props => props.isActive ? 'rgba(255,255,255,0.2)' : 'transparent'};
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  
  &:hover {
    background: rgba(255,255,255,0.2);
    border-color: rgba(255,255,255,0.4);
    color: white;
  }
`;

interface ModernHeaderProps {
  onSidePanelToggle: () => void;
  showSidePanel: boolean;
  sidePanelContent: 'reasoning' | 'recommendations' | 'problem' | null;
}

const ModernHeader: React.FC<ModernHeaderProps> = ({
  onSidePanelToggle,
  showSidePanel,
  sidePanelContent
}) => {
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      key: 'help',
      icon: <QuestionCircleOutlined />,
      label: '帮助',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <RobotOutlined />,
      label: '退出登录',
      danger: true,
    },
  ];

  const getSidePanelIcon = () => {
    switch (sidePanelContent) {
      case 'reasoning':
        return <BulbOutlined />;
      case 'recommendations':
        return <ThunderboltOutlined />;
      case 'problem':
        return <LinkOutlined />;
      default:
        return <SendOutlined />;
    }
  };

  const getSidePanelText = () => {
    switch (sidePanelContent) {
      case 'reasoning':
        return '推理过程';
      case 'recommendations':
        return '智能推荐';
      case 'problem':
        return '题目详情';
      default:
        return '侧边栏';
    }
  };

  return (
    <StyledHeader>
      <LogoContainer
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
      >
        <LogoIcon
          whileHover={{ scale: 1.05, rotate: 5 }}
          whileTap={{ scale: 0.95 }}
        >
          <BulbOutlined style={{ fontSize: '20px', color: modernTheme.colors.primary[600] }} />
        </LogoIcon>
        <div>
          <Title level={4} style={{ color: 'white', margin: 0, fontWeight: 600 }}>
            AlgoKG
          </Title>
          <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
            智能算法学习平台
          </Text>
        </div>
      </LogoContainer>

      <HeaderActions>
        <StatusIndicator
          isActive={true}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <motion.div
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.7, 1, 0.7]
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <div style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              background: '#52c41a' 
            }} />
          </motion.div>
          <Text style={{ color: 'white', fontSize: '12px' }}>
            系统正常
          </Text>
        </StatusIndicator>

        <Space size="middle">
          <Tooltip title="通知">
            <Button
              type="text"
              icon={<BulbOutlined />}
              style={{ color: 'white' }}
            />
          </Tooltip>

          <Tooltip title={getSidePanelText()}>
            <SidePanelToggle
              isActive={showSidePanel}
              icon={getSidePanelIcon()}
              onClick={onSidePanelToggle}
            >
              {getSidePanelText()}
            </SidePanelToggle>
          </Tooltip>

          <Button
            type="text"
            style={{
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '4px 12px',
              height: 'auto'
            }}
          >
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: 'rgba(255,255,255,0.2)',
                border: '1px solid rgba(255,255,255,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px'
              }}
            >
              <UserOutlined />
            </div>
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '12px', lineHeight: 1 }}>用户</div>
              <div style={{ fontSize: '10px', opacity: 0.8, lineHeight: 1 }}>
                算法学习者
              </div>
            </div>
          </Button>
        </Space>
      </HeaderActions>
    </StyledHeader>
  );
};

export default ModernHeader;
