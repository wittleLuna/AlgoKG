import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import './App.css';

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <div className="App">
        <header className="App-header">
          <h1>AlgoKG智能问答系统</h1>
          <p>系统正在启动中...</p>
          <p>如果您看到这个页面，说明前端已经成功启动！</p>
        </header>
      </div>
    </ConfigProvider>
  );
};

export default App;
