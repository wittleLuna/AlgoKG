// 全局类型声明文件，用于解决TypeScript错误

declare module 'react-syntax-highlighter' {
  export const Prism: any;
}

declare module 'react-syntax-highlighter/dist/esm/styles/prism' {
  export const tomorrow: any;
}

declare module 'react-markdown' {
  interface CodeProps {
    node?: any;
    inline?: boolean;
    className?: string;
    children?: React.ReactNode;
    [key: string]: any;
  }
  
  interface Components {
    code?: (props: CodeProps) => React.ReactElement;
    [key: string]: any;
  }
  
  interface ReactMarkdownProps {
    children: string;
    components?: Components;
    [key: string]: any;
  }
  
  const ReactMarkdown: React.FC<ReactMarkdownProps>;
  export default ReactMarkdown;
}

// 扩展Ant Design组件类型
declare module 'antd' {
  export const Card: any;
  export const Typography: any;
  export const Tag: any;
  export const Button: any;
  export const Space: any;
  export const Collapse: any;
  export const Rate: any;
  export const message: any;
  export const Steps: any;
  export const Spin: any;
  export const Progress: any;
  export const ConfigProvider: any;
  export const Layout: any;
  export const Tabs: any;
  export const Input: any;
  export const Select: any;
  export const Tooltip: any;
  export const Drawer: any;
  export const Divider: any;
  export const Timeline: any;
  export const Alert: any;
  export const Empty: any;
  export const List: any;
  export const Statistic: any;
  export const Switch: any;
  export const Slider: any;

  interface TagProps {
    size?: 'small' | 'default' | 'large';
    [key: string]: any;
  }
}

// 扩展vis-network类型
declare module 'vis-network' {
  export class Network {
    constructor(container: any, data: any, options: any);
    body?: {
      data?: {
        nodes?: any;
        edges?: any;
      };
    };
    on(event: string, callback: (params: any) => void): void;
    setData(data: any): void;
    setOptions(options: any): void;
    fit(): void;
    focus(nodeId: string, options?: any): void;
    selectNodes(nodeIds: string[]): void;
    unselectAll(): void;
    getSelectedNodes(): string[];
    getConnectedNodes(nodeId: any): any[];
    getConnectedEdges(nodeId: any): any[];
    getScale(): number;
    moveTo(options: any): void;
    destroy(): void;
    [key: string]: any;
  }

  export interface Options {
    edges?: {
      smooth?: boolean | {
        enabled?: boolean;
        type?: string;
        forceDirection?: string | boolean;
        roundness?: number;
      };
      [key: string]: any;
    };
    [key: string]: any;
  }

  export class DataSet {
    constructor(data?: any[]);
    add(data: any): void;
    update(data: any): void;
    remove(id: any): void;
    get(options?: any): any[];
    [key: string]: any;
  }
}

// 全局样式声明
declare namespace JSX {
  interface IntrinsicElements {
    style: React.DetailedHTMLProps<
      React.StyleHTMLAttributes<HTMLStyleElement> & {
        jsx?: boolean;
      },
      HTMLStyleElement
    >;
  }
}
