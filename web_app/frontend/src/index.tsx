import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import App from './App';
import './index.css';

// 配置Ant Design主题
const theme = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    borderRadius: 8,
    fontSize: 14,
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",
  },
  components: {
    Layout: {
      bodyBg: 'transparent',
      headerBg: 'rgba(255, 255, 255, 0.95)',
      siderBg: 'rgba(255, 255, 255, 0.95)',
    },
    Card: {
      borderRadius: 12,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    },
    Button: {
      borderRadius: 6,
      fontWeight: 500,
    },
    Input: {
      borderRadius: 8,
    },
    Tabs: {
      cardBg: 'transparent',
    },
  },
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <ConfigProvider 
      locale={zhCN}
      theme={theme}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
