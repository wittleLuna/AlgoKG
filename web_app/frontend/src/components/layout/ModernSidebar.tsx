import React from 'react';
import { Layout, Button, Tooltip } from 'antd';
import {
  MessageOutlined,
  ClusterOutlined,
  StopOutlined,
  ReloadOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  LinkOutlined,
  StarOutlined
} from '@ant-design/icons';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { modernTheme } from '../../styles/theme';

const { Sider } = Layout;

const StyledSider = styled(Sider)`
  background: linear-gradient(180deg, ${modernTheme.colors.gray[900]} 0%, ${modernTheme.colors.gray[800]} 100%);
  border-right: 1px solid ${modernTheme.colors.border.dark};
  box-shadow: ${modernTheme.shadows.lg};
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.02) 50%, transparent 70%);
    pointer-events: none;
  }
  
  .ant-layout-sider-trigger {
    background: ${modernTheme.colors.gray[800]};
    border-top: 1px solid ${modernTheme.colors.border.dark};
    color: white;
    
    &:hover {
      background: ${modernTheme.colors.gray[700]};
    }
  }
`;

const StyledMenu = styled.div`
  background: transparent;
  border: none;

  .menu-group {
    margin-bottom: 24px;
  }

  .menu-group-title {
    color: ${modernTheme.colors.text.secondary};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 0 16px 8px 16px;
    opacity: 0.7;
  }

  .menu-item {
    color: ${modernTheme.colors.text.inverse};
    margin: 8px 12px;
    border-radius: 12px;
    height: 48px;
    display: flex;
    align-items: center;
    transition: all 0.3s ease;
    cursor: pointer;
    padding: 0 16px;

    &:hover {
      background: rgba(255,255,255,0.1);
      color: white;
    }

    &.selected {
      background: linear-gradient(135deg, ${modernTheme.colors.primary[600]} 0%, ${modernTheme.colors.secondary[600]} 100%);
      color: white;
      box-shadow: ${modernTheme.shadows.md};
    }

    .menu-item-icon {
      font-size: 18px;
      min-width: 18px;
      margin-right: 12px;
    }
  }
  
  .ant-menu-item-group-title {
    color: ${modernTheme.colors.text.muted};
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 16px 24px 8px;
  }
`;

const CollapseButton = styled(Button)`
  position: absolute;
  top: 16px;
  right: -12px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: ${modernTheme.colors.primary[600]};
  border: 2px solid white;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  box-shadow: ${modernTheme.shadows.md};
  
  &:hover {
    background: ${modernTheme.colors.primary[700]};
    color: white;
    transform: scale(1.1);
  }
  
  .anticon {
    font-size: 12px;
  }
`;

const QuickActions = styled(motion.div)`
  position: absolute;
  bottom: 80px;
  left: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const QuickActionButton = styled(Button)`
  height: 40px;
  border-radius: 10px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: rgba(255,255,255,0.2);
    border-color: rgba(255,255,255,0.3);
    color: white;
    transform: translateY(-2px);
  }
`;

interface ModernSidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const ModernSidebar: React.FC<ModernSidebarProps> = ({
  collapsed,
  onCollapse,
  activeTab,
  onTabChange
}) => {
  const menuItems = [
    {
      type: 'group',
      label: '主要功能',
      children: [
        {
          key: 'chat',
          icon: <MessageOutlined />,
          label: '智能问答',
        },
        {
          key: 'graph',
          icon: <ClusterOutlined />,
          label: '知识图谱',
        },
      ],
    },
    {
      type: 'group',
      label: '学习工具',
      children: [
        {
          key: 'history',
          icon: <StopOutlined />,
          label: '学习历史',
        },
        {
          key: 'favorites',
          icon: <StarOutlined />,
          label: '收藏夹',
        },
        {
          key: 'library',
          icon: <ReloadOutlined />,
          label: '题库',
        },
      ],
    },
    {
      type: 'group',
      label: '系统',
      children: [
        {
          key: 'settings',
          icon: <SettingOutlined />,
          label: '设置',
        },
      ],
    },
  ];

  const quickActions = [
    {
      key: 'ai-tutor',
      icon: <BulbOutlined />,
      tooltip: 'AI导师',
    },
    {
      key: 'quick-solve',
      icon: <ThunderboltOutlined />,
      tooltip: '快速解题',
    },
    {
      key: 'knowledge-base',
      icon: <LinkOutlined />,
      tooltip: '知识库',
    },
  ];

  return (
    <StyledSider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      trigger={null}
      width={240}
      collapsedWidth={80}
    >
      <CollapseButton
        type="text"
        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        onClick={() => onCollapse(!collapsed)}
        size="small"
      />

      <div style={{ padding: '24px 0 0 0', height: '100%', position: 'relative' }}>
        <StyledMenu>
          {menuItems.map((item, index) => (
            <div key={`group-${index}`} className="menu-group">
              <div className="menu-group-title">{item.label}</div>
              {item.children?.map((child) => (
                <div
                  key={child.key}
                  className={`menu-item ${activeTab === child.key ? 'selected' : ''}`}
                  onClick={() => onTabChange(child.key)}
                >
                  <span className="menu-item-icon">{child.icon}</span>
                  <span>{child.label}</span>
                </div>
              ))}
            </div>
          ))}
        </StyledMenu>

        <AnimatePresence>
          {!collapsed && (
            <QuickActions
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.3 }}
            >
              {quickActions.map((action, index) => (
                <motion.div
                  key={action.key}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Tooltip title={action.tooltip} placement="right">
                    <QuickActionButton
                      icon={action.icon}
                      block
                    >
                      {action.tooltip}
                    </QuickActionButton>
                  </Tooltip>
                </motion.div>
              ))}
            </QuickActions>
          )}
        </AnimatePresence>

        {collapsed && (
          <div style={{ 
            position: 'absolute', 
            bottom: 80, 
            left: '50%', 
            transform: 'translateX(-50%)',
            display: 'flex',
            flexDirection: 'column',
            gap: 8
          }}>
            {quickActions.map((action, index) => (
              <Tooltip key={action.key} title={action.tooltip} placement="right">
                <QuickActionButton
                  icon={action.icon}
                  style={{ width: 40, height: 40 }}
                />
              </Tooltip>
            ))}
          </div>
        )}
      </div>
    </StyledSider>
  );
};

export default ModernSidebar;
