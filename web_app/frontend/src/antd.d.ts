// Ant Design 模块声明文件
declare module 'antd' {
  import * as React from 'react';
  
  // 导出所有常用组件
  export const Card: React.ComponentType<any>;
  export const Typography: React.ComponentType<any> & {
    Title: React.ComponentType<any>;
    Text: React.ComponentType<any>;
    Paragraph: React.ComponentType<any>;
  };
  export const Tag: React.ComponentType<any>;
  export const Button: React.ComponentType<any>;
  export const Space: React.ComponentType<any>;
  export const Collapse: React.ComponentType<any> & {
    Panel: React.ComponentType<any>;
  };
  export const Rate: React.ComponentType<any>;
  export const Steps: React.ComponentType<any> & {
    Step: React.ComponentType<any>;
  };
  export const Spin: React.ComponentType<any>;
  export const Progress: React.ComponentType<any>;
  export const ConfigProvider: React.ComponentType<any>;
  export const Layout: React.ComponentType<any> & {
    Header: React.ComponentType<any>;
    Content: React.ComponentType<any>;
    Sider: React.ComponentType<any>;
    Footer: React.ComponentType<any>;
  };
  export const Tabs: React.ComponentType<any> & {
    TabPane: React.ComponentType<any>;
  };
  export const Input: React.ComponentType<any> & {
    TextArea: React.ComponentType<any>;
    Search: React.ComponentType<any>;
  };
  export const Select: React.ComponentType<any> & {
    Option: React.ComponentType<any>;
  };
  export const Tooltip: React.ComponentType<any>;
  export const Drawer: React.ComponentType<any>;
  export const Divider: React.ComponentType<any>;
  export const Timeline: React.ComponentType<any> & {
    Item: React.ComponentType<any>;
  };
  export const Alert: React.ComponentType<any>;
  export const Empty: React.ComponentType<any>;
  export const List: React.ComponentType<any> & {
    Item: React.ComponentType<any>;
  };
  export const Statistic: React.ComponentType<any>;
  export const Switch: React.ComponentType<any>;
  export const Slider: React.ComponentType<any>;
  export const Popover: React.ComponentType<any>;
  export const Row: React.ComponentType<any>;
  export const Col: React.ComponentType<any>;
  
  // message 全局方法
  export const message: {
    success: (content: string) => void;
    error: (content: string) => void;
    info: (content: string) => void;
    warning: (content: string) => void;
    loading: (content: string) => void;
    [key: string]: any;
  };
}

declare module 'antd/locale/zh_CN' {
  const zhCN: any;
  export default zhCN;
}

declare module '@ant-design/icons' {
  import * as React from 'react';
  
  export const UserOutlined: React.ComponentType<any>;
  export const RobotOutlined: React.ComponentType<any>;
  export const CopyOutlined: React.ComponentType<any>;
  export const LikeOutlined: React.ComponentType<any>;
  export const DislikeOutlined: React.ComponentType<any>;
  export const ExpandAltOutlined: React.ComponentType<any>;
  export const LinkOutlined: React.ComponentType<any>;
  export const SendOutlined: React.ComponentType<any>;
  export const AudioOutlined: React.ComponentType<any>;
  export const BulbOutlined: React.ComponentType<any>;
  export const ThunderboltOutlined: React.ComponentType<any>;
  export const SearchOutlined: React.ComponentType<any>;
  export const CheckCircleOutlined: React.ComponentType<any>;
  export const LoadingOutlined: React.ComponentType<any>;
  export const ExclamationCircleOutlined: React.ComponentType<any>;
  export const EyeOutlined: React.ComponentType<any>;
  export const EyeInvisibleOutlined: React.ComponentType<any>;
  export const MessageOutlined: React.ComponentType<any>;
  export const NodeIndexOutlined: React.ComponentType<any>;
  export const SettingOutlined: React.ComponentType<any>;
  export const MenuFoldOutlined: React.ComponentType<any>;
  export const MenuUnfoldOutlined: React.ComponentType<any>;
  export const FullscreenOutlined: React.ComponentType<any>;
  export const FullscreenExitOutlined: React.ComponentType<any>;
  export const ReloadOutlined: React.ComponentType<any>;
  export const ZoomInOutlined: React.ComponentType<any>;
  export const ZoomOutOutlined: React.ComponentType<any>;
  export const DownloadOutlined: React.ComponentType<any>;
  export const FilterOutlined: React.ComponentType<any>;
  export const CloseOutlined: React.ComponentType<any>;
  export const InfoCircleOutlined: React.ComponentType<any>;
  export const QuestionCircleOutlined: React.ComponentType<any>;
  export const WarningOutlined: React.ComponentType<any>;
  export const ClockCircleOutlined: React.ComponentType<any>;
  export const SyncOutlined: React.ComponentType<any>;
  export const PlayCircleOutlined: React.ComponentType<any>;
  export const PauseCircleOutlined: React.ComponentType<any>;
  export const StopOutlined: React.ComponentType<any>;
  export const CaretRightOutlined: React.ComponentType<any>;
  export const CaretDownOutlined: React.ComponentType<any>;
  export const RightOutlined: React.ComponentType<any>;
  export const LeftOutlined: React.ComponentType<any>;
  export const UpOutlined: React.ComponentType<any>;
  export const DownOutlined: React.ComponentType<any>;
  export const CodeOutlined: React.ComponentType<any>;
  export const StarOutlined: React.ComponentType<any>;
  export const TrophyOutlined: React.ComponentType<any>;
  export const BranchesOutlined: React.ComponentType<any>;
  export const ClusterOutlined: React.ComponentType<any>;
  export const BarChartOutlined: React.ComponentType<any>;
}
