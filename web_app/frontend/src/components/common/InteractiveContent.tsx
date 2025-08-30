import React, { useState, useCallback } from 'react';
import { Button, Tooltip, Tag, Popover, Space, Typography } from 'antd';
import { 
  LinkOutlined, 
  BulbOutlined, 
  CodeOutlined, 
  QuestionCircleOutlined,
  RightOutlined 
} from '@ant-design/icons';

const { Text } = Typography;

interface InteractiveContentProps {
  content: string;
  clickableConcepts?: string[];
  clickableProblems?: string[];
  onConceptClick?: (concept: string) => void;
  onProblemClick?: (problem: string) => void;
  onCodeClick?: (code: string) => void;
}

interface ClickableItem {
  text: string;
  type: 'concept' | 'problem' | 'code' | 'algorithm' | 'datastructure';
  start: number;
  end: number;
  confidence?: number;
}

const InteractiveContent: React.FC<InteractiveContentProps> = ({
  content,
  clickableConcepts = [],
  clickableProblems = [],
  onConceptClick,
  onProblemClick,
  onCodeClick
}) => {
  const [hoveredItem, setHoveredItem] = useState<ClickableItem | null>(null);

  // 智能识别可点击内容
  const identifyClickableItems = useCallback((text: string): ClickableItem[] => {
    const items: ClickableItem[] = [];
    
    // 算法概念模式
    const algorithmPatterns = [
      /动态规划|dp|dynamic programming/gi,
      /回溯|backtrack|回溯算法/gi,
      /贪心|greedy|贪心算法/gi,
      /分治|divide and conquer/gi,
      /二分查找|binary search/gi,
      /深度优先搜索|dfs|depth first search/gi,
      /广度优先搜索|bfs|breadth first search/gi,
      /双指针|two pointer/gi,
      /滑动窗口|sliding window/gi,
      /快速排序|quick sort/gi,
      /归并排序|merge sort/gi,
      /堆排序|heap sort/gi,
      /最短路径算法|shortest path/gi,
      /dijkstra|迪杰斯特拉/gi,
      /floyd-warshall|弗洛伊德/gi,
      /最小生成树|minimum spanning tree/gi,
      /prim|普里姆/gi,
      /kruskal|克鲁斯卡尔/gi,
      /拓扑排序|topological sort/gi,
      /强连通分量|strongly connected component/gi,
      /tarjan|塔尔扬/gi,
      /kosaraju/gi,
      /图论|graph theory/gi,
      /网络流|network flow/gi,
      /最大流|maximum flow/gi,
      /最小割|minimum cut/gi,
      /二分图|bipartite graph/gi,
      /匈牙利算法|hungarian algorithm/gi,
      /kmp|字符串匹配/gi,
      /manacher|马拉车/gi,
      /后缀数组|suffix array/gi,
      /ac自动机|aho-corasick/gi,
      /线性规划|linear programming/gi,
      /模拟退火|simulated annealing/gi,
      /遗传算法|genetic algorithm/gi,
      /蒙特卡洛|monte carlo/gi
    ];

    // 数据结构模式
    const dataStructurePatterns = [
      /二叉树|binary tree/gi,
      /链表|linked list/gi,
      /栈|stack/gi,
      /队列|queue/gi,
      /堆|heap/gi,
      /哈希表|hash table|hash map/gi,
      /图|graph/gi,
      /字典树|trie/gi,
      /并查集|union find|disjoint set/gi,
      /线段树|segment tree/gi,
      /树状数组|binary indexed tree|fenwick tree/gi,
      /平衡二叉树|balanced binary tree/gi,
      /avl树|avl tree/gi,
      /红黑树|red black tree/gi,
      /b树|b-tree/gi,
      /b\+树|b\+ tree/gi,
      /跳表|skip list/gi,
      /布隆过滤器|bloom filter/gi,
      /lru缓存|lru cache/gi,
      /lfu缓存|lfu cache/gi,
      /优先队列|priority queue/gi,
      /双端队列|deque|double ended queue/gi,
      /稀疏表|sparse table/gi,
      /可持久化数据结构|persistent data structure/gi,
      /函数式数据结构|functional data structure/gi
    ];

    // 题目模式（LeetCode风格）
    const problemPatterns = [
      /两数之和|two sum/gi,
      /三数之和|three sum/gi,
      /最长公共子序列|longest common subsequence/gi,
      /最长递增子序列|longest increasing subsequence/gi,
      /爬楼梯|climbing stairs/gi,
      /买卖股票|best time to buy and sell stock/gi,
      /不同路径|unique paths/gi,
      /最小路径和|minimum path sum/gi,
      /编辑距离|edit distance/gi,
      /背包问题|knapsack/gi
    ];

    // 代码模式
    const codePatterns = [
      /```[\s\S]*?```/g,
      /`[^`]+`/g
    ];

    // 处理算法概念
    algorithmPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        items.push({
          text: match[0],
          type: 'algorithm',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.9
        });
      }
    });

    // 处理数据结构
    dataStructurePatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        items.push({
          text: match[0],
          type: 'datastructure',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.9
        });
      }
    });

    // 处理题目
    problemPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        items.push({
          text: match[0],
          type: 'problem',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 0.8
        });
      }
    });

    // 处理代码
    codePatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(text)) !== null) {
        items.push({
          text: match[0],
          type: 'code',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 1.0
        });
      }
    });

    // 处理明确指定的可点击概念
    clickableConcepts.forEach(concept => {
      const regex = new RegExp(concept.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      let match;
      while ((match = regex.exec(text)) !== null) {
        items.push({
          text: match[0],
          type: 'concept',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 1.0
        });
      }
    });

    // 处理明确指定的可点击题目
    clickableProblems.forEach(problem => {
      const regex = new RegExp(problem.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      let match;
      while ((match = regex.exec(text)) !== null) {
        items.push({
          text: match[0],
          type: 'problem',
          start: match.index,
          end: match.index + match[0].length,
          confidence: 1.0
        });
      }
    });

    // 去重和排序
    const uniqueItems = items.filter((item, index, self) => 
      index === self.findIndex(i => i.start === item.start && i.end === item.end)
    );

    return uniqueItems.sort((a, b) => a.start - b.start);
  }, [clickableConcepts, clickableProblems]);

  // 获取项目图标
  const getItemIcon = (type: string) => {
    const iconMap: Record<string, React.ReactNode> = {
      'concept': <BulbOutlined />,
      'algorithm': <BulbOutlined />,
      'datastructure': <BulbOutlined />,
      'problem': <QuestionCircleOutlined />,
      'code': <CodeOutlined />
    };
    return iconMap[type] || <LinkOutlined />;
  };

  // 获取项目颜色
  const getItemColor = (type: string) => {
    const colorMap: Record<string, string> = {
      'concept': '#1890ff',
      'algorithm': '#52c41a',
      'datastructure': '#722ed1',
      'problem': '#fa8c16',
      'code': '#13c2c2'
    };
    return colorMap[type] || '#8c8c8c';
  };

  // 处理点击事件
  const handleItemClick = (item: ClickableItem) => {
    // 添加点击反馈效果
    const event = new CustomEvent('conceptClick', {
      detail: { text: item.text, type: item.type }
    });
    document.dispatchEvent(event);

    switch (item.type) {
      case 'concept':
      case 'algorithm':
      case 'datastructure':
        if (onConceptClick) {
          onConceptClick(item.text);
        }
        break;
      case 'problem':
        if (onProblemClick) {
          onProblemClick(item.text);
        }
        break;
      case 'code':
        if (onCodeClick) {
          onCodeClick(item.text);
        }
        break;
    }
  };

  // 渲染交互式内容
  const renderInteractiveContent = () => {
    const clickableItems = identifyClickableItems(content);
    
    if (clickableItems.length === 0) {
      return <span>{content}</span>;
    }

    const parts: React.ReactNode[] = [];
    let lastIndex = 0;

    clickableItems.forEach((item, index) => {
      // 添加非点击文本
      if (item.start > lastIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {content.slice(lastIndex, item.start)}
          </span>
        );
      }

      // 添加可点击项目
      const popoverContent = (
        <div style={{ maxWidth: 200 }}>
          <Space direction="vertical" size="small">
            <div>
              <Text strong>{item.text}</Text>
              <Tag
                color={getItemColor(item.type)}
                style={{ marginLeft: 8, fontSize: '12px' }}
              >
                {item.type}
              </Tag>
            </div>
            {item.confidence && (
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  置信度: {(item.confidence * 100).toFixed(0)}%
                </Text>
              </div>
            )}
            <Button
              type="primary"
              size="small"
              icon={<RightOutlined />}
              onClick={() => handleItemClick(item)}
              block
            >
              点击了解更多
            </Button>
          </Space>
        </div>
      );

      parts.push(
        <Popover
          key={`item-${index}`}
          content={popoverContent}
          title={`${item.type === 'problem' ? '题目' : '概念'}: ${item.text}`}
          trigger="hover"
          placement="top"
        >
          <Button
            type="link"
            size="small"
            icon={getItemIcon(item.type)}
            onClick={() => handleItemClick(item)}
            onMouseEnter={() => setHoveredItem(item)}
            onMouseLeave={() => setHoveredItem(null)}
            style={{
              color: getItemColor(item.type),
              padding: '0 2px',
              height: 'auto',
              fontWeight: 500,
              textDecoration: hoveredItem === item ? 'underline' : 'none',
              background: hoveredItem === item ? 'rgba(24, 144, 255, 0.1)' : 'transparent',
              borderRadius: '2px'
            }}
          >
            {item.text}
          </Button>
        </Popover>
      );

      lastIndex = item.end;
    });

    // 添加剩余文本
    if (lastIndex < content.length) {
      parts.push(
        <span key="text-end">
          {content.slice(lastIndex)}
        </span>
      );
    }

    return <>{parts}</>;
  };

  return (
    <div className="interactive-content">
      {renderInteractiveContent()}
      

    </div>
  );
};

export default InteractiveContent;
