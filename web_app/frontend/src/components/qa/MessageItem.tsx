import React, { useState } from 'react';
import { Card, Typography, Tag, Button, Space, Collapse, Rate, message as antdMessage, Tooltip, Spin } from 'antd';
import {
  UserOutlined,
  RobotOutlined,
  CopyOutlined,
  LikeOutlined,
  DislikeOutlined,
  ExpandAltOutlined,
  LinkOutlined,
  NodeIndexOutlined,
  StarOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { MessageItemProps, ProblemInfo, SimilarProblem } from '../../types';
import { authService } from '../../services/authService';
import ReasoningPath from './ReasoningPath';
import EnhancedReasoningPath from './EnhancedReasoningPath';
import InteractiveContent from '../common/InteractiveContent';
import SmartLinkSuggestions from '../common/SmartLinkSuggestions';
import SmartTagDisplay from '../common/SmartTagDisplay';
import UnifiedGraphVisualization from '../graph/UnifiedGraphVisualization';
import EmbeddedAlgorithmVisualizer from '../visualization/EmbeddedAlgorithmVisualizer';
import InlineKnowledgeGraph from './InlineKnowledgeGraph';
import EnhancedSimilarProblems from './EnhancedSimilarProblems';

const { Text, Title, Paragraph } = Typography;
const { Panel } = Collapse;

const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onConceptClick,
  onProblemClick,
}) => {
  const [showFullResponse, setShowFullResponse] = useState(false);
  const [userRating, setUserRating] = useState<number>(0);
  const [enhancedGraphData, setEnhancedGraphData] = useState<any>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);

  const isUser = message.type === 'user';
  const response = message.response;

  // 检查是否已收藏
  React.useEffect(() => {
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    const messageId = `${message.type}-${message.timestamp}-${message.content.substring(0, 50)}`;
    setIsFavorited(favorites.some((fav: any) => fav.id === messageId));
  }, [message]);

  // 收藏/取消收藏
  const handleFavorite = () => {
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    const messageId = `${message.type}-${message.timestamp}-${message.content.substring(0, 50)}`;

    if (isFavorited) {
      // 取消收藏
      const newFavorites = favorites.filter((fav: any) => fav.id !== messageId);
      localStorage.setItem('favorites', JSON.stringify(newFavorites));
      setIsFavorited(false);
      antdMessage.success('已取消收藏');
    } else {
      // 添加收藏
      const favoriteItem = {
        id: messageId,
        type: message.type === 'user' ? 'query' : 'response',
        title: message.type === 'user' ? message.content.substring(0, 100) : '系统回答',
        content: message.content,
        timestamp: message.timestamp || Date.now(),
        tags: response?.entities || [],
        category: response?.intent || 'general',
        metadata: {
          reasoning_path: response?.reasoning_path,
          similar_problems: response?.similar_problems,
          response_metadata: response?.metadata
        }
      };

      const newFavorites = [...favorites, favoriteItem];
      localStorage.setItem('favorites', JSON.stringify(newFavorites));
      setIsFavorited(true);
      antdMessage.success('已添加到收藏');
    }
  };

  // 获取增强的图谱数据（使用与独立图谱页面相同的API）
  const fetchEnhancedGraphData = async (entityName: string) => {
    if (!entityName || graphLoading) return;

    setGraphLoading(true);
    try {
      const response = await fetch('/api/v1/graph/unified/query?data_sources=neo4j&data_sources=embedding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entity_name: entityName.trim(),
          depth: 2,
          limit: 50
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setEnhancedGraphData(data);
        console.log(`✅ 获取增强图谱数据成功: ${entityName}`, data);
      } else {
        console.error('❌ 获取增强图谱数据失败:', response.status);
      }
    } catch (error) {
      console.error('❌ 获取增强图谱数据错误:', error);
    } finally {
      setGraphLoading(false);
    }
  };

  // 当有实体时自动获取增强图谱数据
  React.useEffect(() => {
    if (response?.entities && response.entities.length > 0 && !enhancedGraphData && !graphLoading) {
      const mainEntity = response.entities[0];
      console.log(`🔍 检测到实体，获取增强图谱数据: ${mainEntity}`);
      fetchEnhancedGraphData(mainEntity);
    }
  }, [response?.entities, enhancedGraphData, graphLoading]);

  // 检测是否包含可视化的算法代码
  const detectAlgorithmCode = (code: string, language: string) => {
    if (!code || (language !== 'javascript' && language !== 'js')) return null;

    const algorithmPatterns = {
      bubble_sort: /bubbleSort|冒泡排序/i,
      selection_sort: /selectionSort|选择排序/i,
      insertion_sort: /insertionSort|插入排序/i,
      quick_sort: /quickSort|快速排序/i,
      merge_sort: /mergeSort|归并排序/i,
      binary_search: /binarySearch|二分查找/i
    };

    for (const [algorithm, pattern] of Object.entries(algorithmPatterns)) {
      if (pattern.test(code)) {
        return algorithm;
      }
    }

    return null;
  };

  // 提取数组数据
  const extractArrayData = (code: string): number[] => {
    const arrayMatch = code.match(/\[[\d\s,]+\]/);
    if (arrayMatch) {
      try {
        return JSON.parse(arrayMatch[0]);
      } catch (e) {
        // 忽略解析错误
      }
    }
    return [64, 34, 25, 12, 22, 11, 90]; // 默认数据
  };

  // 深度调试函数
  const debugData = (data: any, name: string) => {
    console.log(`=== ${name} 调试信息 ===`);
    console.log('类型:', typeof data);
    console.log('值:', data);
    if (data && typeof data === 'object') {
      console.log('键:', Object.keys(data));
      console.log('JSON:', JSON.stringify(data, null, 2));
    }
    console.log('========================');
  };

  // 调试消息和响应数据
  React.useEffect(() => {
    debugData(message, 'Message');
    debugData(message.content, 'Message Content');
    debugData(response, 'Response');
    if (response) {
      debugData(response.integrated_response, 'Integrated Response');
      debugData(response.concept_explanation, 'Concept Explanation');
    }
  }, [message, response]);

  // 安全渲染函数，处理对象显示问题
  const safeRender = (value: any): string => {
    if (value === null || value === undefined) {
      return '';
    }
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' || typeof value === 'boolean') {
      return String(value);
    }
    if (Array.isArray(value)) {
      return value.map(item => safeRender(item)).filter(Boolean).join(', ');
    }
    if (value && typeof value === 'object') {
      // 检查是否是React元素
      if (value.$$typeof) {
        return '[React Element]';
      }

      // 特殊处理Neo4j节点对象
      if (value.element_id && value.labels && value.properties) {
        const props = value.properties;
        const name = props.name || props.title || props.concept_name || '未知算法';
        const description = props.description || '';
        const category = props.category || '';

        // 返回美化的节点信息
        return `**${name}**${category ? ` (${category})` : ''}${description ? ` - ${description}` : ''}`;
      }

      // 特殊处理常见的对象类型 - 按优先级排序
      if (value.name && typeof value.name === 'string') return value.name;
      if (value.title && typeof value.title === 'string') return value.title;
      if (value.text && typeof value.text === 'string') return value.text;
      if (value.content && typeof value.content === 'string') return value.content;
      if (value.label && typeof value.label === 'string') return value.label;
      if (value.description && typeof value.description === 'string') return value.description;
      if (value.concept_name && typeof value.concept_name === 'string') return value.concept_name;
      if (value.algorithm && typeof value.algorithm === 'string') return value.algorithm;

      // 如果对象只有一个属性，返回该属性的值
      const keys = Object.keys(value);
      if (keys.length === 1) {
        return safeRender(value[keys[0]]);
      }

      // 对于复杂对象，尝试提取有意义的信息
      if (keys.includes('algorithm') && keys.includes('description')) {
        return `${safeRender(value.algorithm)}: ${safeRender(value.description)}`;
      }
      if (keys.includes('concept') && keys.includes('explanation')) {
        return `${safeRender(value.concept)} - ${safeRender(value.explanation)}`;
      }
      if (keys.includes('concept_name') && keys.includes('definition')) {
        return `${safeRender(value.concept_name)}: ${safeRender(value.definition)}`;
      }

      // 尝试找到最有意义的字符串属性
      const meaningfulKeys = keys.filter(key =>
        typeof value[key] === 'string' &&
        value[key].length > 0 &&
        !['id', 'created_at', 'updated_at', '$$typeof'].includes(key)
      );

      if (meaningfulKeys.length > 0) {
        return safeRender(value[meaningfulKeys[0]]);
      }

      // 最后返回简化的描述而不是[object Object]
      return keys.length > 0 ? `{${keys.slice(0, 2).join(', ')}}` : '{}';
    }
    return String(value || '');
  };

  // 安全渲染数组
  const safeRenderArray = (arr: any[]): string[] => {
    if (!Array.isArray(arr)) {
      return [safeRender(arr)];
    }
    return arr.map(item => safeRender(item));
  };

  // 深度清理对象引用的函数
  const deepCleanObjectReferences = (text: string): string => {
    return text
      // 清理各种对象引用模式
      .replace(/\[object Object\]/g, '')
      .replace(/\{object Object\}/g, '')
      .replace(/Object\s*\{\s*\}/g, '')
      .replace(/\{\s*\[object Object\]\s*\}/g, '')
      .replace(/\[\s*\[object Object\]\s*\]/g, '')
      // 清理空的数据结构
      .replace(/\{\s*\}/g, '')
      .replace(/\[\s*\]/g, '')
      .replace(/\(\s*\)/g, '')
      // 清理多余的标点符号
      .replace(/,\s*,/g, ',')
      .replace(/:\s*,/g, '')
      .replace(/,\s*:/g, ':')
      // 清理多余的空白
      .replace(/\s{3,}/g, '  ')
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      .trim();
  };

  // 处理消息内容，替换可能的对象引用
  const processMessageContent = (content: any): string => {
    if (!content) return '';

    console.log('MessageItem - 原始消息内容:', content);
    console.log('MessageItem - 内容类型:', typeof content);

    // 简化处理逻辑，避免过度复杂化
    let processedContent = '';

    // 处理不同类型的内容
    if (typeof content === 'string') {
      processedContent = content;
    } else if (content && typeof content === 'object') {
      // 如果内容是对象，尝试提取有意义的信息
      if (content.integrated_response) {
        processedContent = String(content.integrated_response);
      } else if (content.content) {
        processedContent = String(content.content);
      } else if (content.text) {
        processedContent = String(content.text);
      } else {
        // 对于其他对象，使用简单的字符串转换
        processedContent = JSON.stringify(content, null, 2);
      }
    } else {
      processedContent = String(content || '');
    }

    // 首先处理Neo4j节点对象的显示 - 在其他清理之前进行
    processedContent = processedContent
      // 处理完整的Neo4j节点格式
      .replace(/<Node element_id='(\d+)' labels=frozenset\(\{[^}]*\}\) properties=\{([^}]+)\}>/g, (match, elementId, propertiesStr) => {
        console.log('Neo4j节点匹配:', match);
        console.log('属性字符串:', propertiesStr);

        try {
          // 尝试解析属性字符串 - 更精确的匹配
          const nameMatch = propertiesStr.match(/'name':\s*'([^']+)'/);
          const descMatch = propertiesStr.match(/'description':\s*'([^']+)'/);
          const categoryMatch = propertiesStr.match(/'category':\s*'([^']+)'/);
          const difficultyMatch = propertiesStr.match(/'difficulty':\s*'([^']+)'/);
          const platformMatch = propertiesStr.match(/'platform':\s*'([^']+)'/);
          const tagsMatch = propertiesStr.match(/'tags':\s*\[([^\]]*)\]/);
          const titleMatch = propertiesStr.match(/'title':\s*'([^']+)'/);

          const name = nameMatch ? nameMatch[1] : (titleMatch ? titleMatch[1] : '未知内容');
          const description = descMatch ? descMatch[1] : '';
          const category = categoryMatch ? categoryMatch[1] : '';
          const difficulty = difficultyMatch ? difficultyMatch[1] : '';
          const platform = platformMatch ? platformMatch[1] : '';

          console.log('解析结果:', { name, description, category, difficulty, platform });

          // 过滤掉Solution节点，只显示有意义的节点
          const isSolutionNode = match.includes("'Solution'") || match.includes('"Solution"');
          if (isSolutionNode) {
            console.log('跳过Solution节点');
            return ''; // 不显示Solution节点
          }

          // 检查是否是题目节点（通过标签或字段判断）
          const isAlgorithmNode = match.includes("'Algorithm'") || match.includes('"Algorithm"');
          const isProblemNode = match.includes("'Problem'") || match.includes('"Problem"') ||
                               difficulty || platform ||
                               name.includes('路径') || name.includes('问题') || name.includes('题目');

          if (isProblemNode && !isAlgorithmNode) {
            // 题目节点的格式化显示
            let result = `\n\n> 📝 **${name}**`;

            // 添加难度标签
            if (difficulty) {
              const difficultyColor = difficulty === '简单' ? '🟢' : difficulty === '中等' ? '🟡' : '🔴';
              result += ` ${difficultyColor} \`${difficulty}\``;
            }

            // 添加平台标签
            if (platform) {
              result += ` 🏷️ \`${platform}\``;
            }

            // 添加描述
            if (description) {
              result += `\n> \n> ${description}`;
            }

            // 添加分类
            if (category) {
              result += `\n> \n> 🏷️ **分类**: ${category}`;
            }

            console.log('题目节点格式化结果:', result);
            return result + '\n';
          } else {
            // 算法节点的格式化显示
            const result = `\n\n> 🔍 **${name}**${category ? ` \`${category}\`` : ''}\n> \n> ${description || '相关算法概念'}\n`;
            console.log('算法节点格式化结果:', result);
            return result;
          }
        } catch (e) {
          console.error('Neo4j节点解析错误:', e);
          return `\n\n> 🔍 **相关内容**\n`;
        }
      })
      // 处理简化的Neo4j节点格式（只有属性部分）
      .replace(/\{[^}]*'name':\s*'([^']+)'[^}]*'description':\s*'([^']*)'[^}]*'category':\s*'([^']*)'[^}]*\}/g, (match, name, description, category) => {
        console.log('简化节点匹配:', { name, description, category });
        return `\n\n> 🔍 **${name}**${category ? ` \`${category}\`` : ''}\n> \n> ${description || '相关概念'}\n`;
      })
      // 处理数组中的多个节点（如 +12个）
      .replace(/\+(\d+)个/g, (match, count) => {
        return `等${count}个相关内容`;
      })
      // 处理单独的节点属性显示
      .replace(/properties=\{([^}]+)\}/g, (match, propertiesStr) => {
        try {
          const nameMatch = propertiesStr.match(/'name':\s*'([^']+)'/);
          const descMatch = propertiesStr.match(/'description':\s*'([^']+)'/);
          const categoryMatch = propertiesStr.match(/'category':\s*'([^']+)'/);

          if (nameMatch) {
            const name = nameMatch[1];
            const description = descMatch ? descMatch[1] : '';
            const category = categoryMatch ? categoryMatch[1] : '';
            return `**${name}**${category ? ` (${category})` : ''}${description ? ` - ${description}` : ''}`;
          }
        } catch (e) {
          console.error('属性解析错误:', e);
        }
        return '相关内容';
      });

    // 在Neo4j节点处理完成后，进行其他清理
    processedContent = processedContent
      // 清理对象引用
      .replace(/\[object Object\]/g, '相关内容')
      .replace(/\{object Object\}/g, '相关内容')
      .replace(/Object\s*\{\s*\}/g, '')
      // 清理多余的符号和空值，但保留Markdown格式
      .replace(/\{\}/g, '')
      .replace(/\[\]/g, '')
      .replace(/\bundefined\b/g, '')  // 只替换独立的undefined单词
      .replace(/\bnull\b/g, '')       // 只替换独立的null单词
      .replace(/,\s*:/g, ':')
      .replace(/:\s*,/g, '')
      .replace(/,\s*,/g, ',')
      // 清理"相似题目推荐：无"等无效推荐信息
      .replace(/相似题目推荐\s*[:：]\s*无\s*/g, '')
      .replace(/相似题目推荐\s*[:：]\s*暂无\s*/g, '')
      .replace(/相似题目推荐\s*[:：]\s*\n\s*无\s*/g, '')
      .replace(/##?\s*相似题目推荐\s*\n\s*无\s*/g, '')
      .replace(/##?\s*相似题目推荐\s*\n\s*暂无\s*/g, '')
      // 保留Markdown格式：只合并行内的多个空格，保留换行和缩进
      .replace(/[ \t]+/g, ' ')        // 合并行内的空格和制表符
      .replace(/\n[ \t]+\n/g, '\n\n') // 清理空行中的空格
      .replace(/\n{3,}/g, '\n\n')     // 合并超过2个的连续换行
      .trim();

    // 最后检查：如果内容为空或仍有问题，提供默认内容
    if (!processedContent || processedContent.trim() === '' || processedContent.trim() === 'undefined') {
      processedContent = '正在生成回答...';
    }

    console.log('处理后的内容:', processedContent);
    return processedContent;
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    antdMessage.success('已复制到剪贴板');
  };

  const handleConceptClick = (concept: string) => {
    if (onConceptClick) {
      onConceptClick(concept);
    }
  };

  const handleProblemClick = (problem: string) => {
    if (onProblemClick) {
      onProblemClick(problem);
    }
  };

  // 获取可点击的概念和题目
  const getClickableItems = () => {
    // 从多个来源收集可点击概念
    const conceptSources = [
      // 1. 概念解释中的可点击概念
      ...(response?.concept_explanation?.clickable_concepts || []),

      // 2. 学习进阶中的前置和后续概念
      ...(response?.concept_explanation?.learning_progression?.prerequisites || []),
      ...(response?.concept_explanation?.learning_progression?.next_concepts || []),

      // 3. 从实体列表中提取
      ...(response?.entities || []),

      // 4. 从题目标签中提取算法和数据结构概念
      ...(response?.example_problems?.flatMap(p => [
        ...(p.algorithm_tags || []),
        ...(p.data_structure_tags || []),
        ...(p.technique_tags || [])
      ]) || []),

      // 5. 从相似题目的共享标签中提取
      ...(response?.similar_problems?.flatMap(p => p.shared_tags || []) || []),

      // 6. 常见算法概念（硬编码的重要概念）
      '深度优先搜索', '广度优先搜索', '动态规划', '贪心算法', '回溯算法',
      '分治算法', '二分查找', '双指针', '滑动窗口', '最短路径算法',
      'Dijkstra', 'Floyd-Warshall', '最小生成树', 'Prim', 'Kruskal',
      '二叉树', '链表', '栈', '队列', '堆', '哈希表', '图', '字典树', '并查集', '线段树'
    ];

    // 去重并过滤空值
    const filteredSources = conceptSources.filter(Boolean);
    const uniqueSet = new Set(filteredSources);
    const concepts = Array.from(uniqueSet);

    const problems = [
      ...(response?.example_problems?.map(p => p.title) || []),
      ...(response?.similar_problems?.map(p => p.title) || [])
    ];

    return { concepts, problems };
  };

  const renderProblemCard = (problem: ProblemInfo, index: number) => (
    <Tooltip title="点击查看题目详情" placement="top">
      <Card
        key={index}
        size="small"
        className="problem-card"
        hoverable
        onClick={() => handleProblemClick(problem.title)}
        style={{
          marginBottom: 8,
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
      >
        <div className="problem-header">
          <Title level={5} style={{ margin: 0, color: '#1890ff' }}>
            🔗 {problem.title}
          </Title>
        <Space>
          {problem.difficulty && (
            <Tag color={
              problem.difficulty === '简单' ? 'green' :
              problem.difficulty === '中等' ? 'orange' : 'red'
            }>
              {problem.difficulty}
            </Tag>
          )}
          {problem.platform && (
            <Tag color="blue">{problem.platform}</Tag>
          )}
        </Space>
      </div>
      
      {problem.description && (
        <Paragraph 
          ellipsis={{ rows: 2, expandable: true }}
          style={{ marginTop: 8, marginBottom: 8 }}
        >
          {problem.description}
        </Paragraph>
      )}
      
      <div className="problem-tags">
        {problem.algorithm_tags.map(tag => (
          <Tag key={tag} color="purple" size="small">{tag}</Tag>
        ))}
        {problem.data_structure_tags.map(tag => (
          <Tag key={tag} color="cyan" size="small">{tag}</Tag>
        ))}
      </div>
    </Card>
    </Tooltip>
  );

  const renderSimilarProblem = (similar: SimilarProblem, index: number) => (
    <Tooltip title="点击查看题目详情" placement="top">
      <Card
        key={index}
        size="small"
        className="similar-problem-card"
        hoverable
        onClick={() => handleProblemClick(similar.title)}
        style={{
          marginBottom: 8,
          cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
      >
        <div className="similar-header">
          <Title level={5} style={{ margin: 0, color: '#1890ff' }}>
            🔗 {similar.title}
          </Title>
          <div className="similarity-score">
            <Text type="secondary">相似度: </Text>
            <Text strong>{Math.min(similar.hybrid_score * 100, 100).toFixed(1)}%</Text>
          </div>
        </div>
      
      <div className="recommendation-info">
        <Text type="secondary">推荐理由: </Text>
        <Text>{similar.recommendation_reason}</Text>
      </div>
      
      {similar.learning_path && (
        <div className="learning-path">
          <Text type="secondary">学习路径: </Text>
          <Text italic>{similar.learning_path}</Text>
        </div>
      )}
      
      <div className="shared-tags">
        <SmartTagDisplay
          tags={similar.shared_tags}
          maxTags={6}
          size="small"
          showTooltip={true}
        />
      </div>
    </Card>
    </Tooltip>
  );

  if (isUser) {
    return (
      <div className="message-item user-message">
        <div className="message-avatar">
          <UserOutlined />
        </div>
        <div className="message-content">
          <Card>
            <Text>{message.content}</Text>
          </Card>
        </div>
        
        <style jsx>{`
          .message-item {
            display: flex;
            margin-bottom: 16px;
            align-items: flex-start;
          }
          
          .user-message {
            flex-direction: row-reverse;
          }
          
          .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #1890ff;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            margin: 0 12px;
            flex-shrink: 0;
          }
          
          .message-content {
            flex: 1;
            max-width: 70%;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="message-item assistant-message">
      <div className="message-avatar">
        <RobotOutlined />
      </div>

      <div className="message-content">
        <Card className={`response-card ${message.isCancelled ? 'cancelled-message' : ''}`}>
          {/* 取消状态提示 */}
          {message.isCancelled && (
            <div className="cancelled-notice">
              <Tag color="orange">回答已取消</Tag>
              <Text type="secondary" style={{ marginLeft: 8 }}>
                用户取消了此次回答
              </Text>
            </div>
          )}

          {/* 推理路径 */}
          {!message.isCancelled && (() => {
            console.log('MessageItem - 检查推理步骤:', message.reasoning_steps);
            console.log('MessageItem - 推理步骤长度:', Array.isArray(message.reasoning_steps) ? message.reasoning_steps.length : 0);
            return Array.isArray(message.reasoning_steps) && message.reasoning_steps.length > 0;
          })() && (
            <div className="reasoning-section">
              <EnhancedReasoningPath
                steps={message.reasoning_steps}
                isStreaming={message.isStreaming}
                onStepClick={(step) => {
                  console.log('Step clicked:', step);
                  // 可以在这里添加步骤点击处理逻辑
                }}
              />
            </div>
          )}

          {/* 主要回答内容 */}
          <div className="main-response">
            <div className="response-header">
              <Space>
                <Text strong>AI助手回答</Text>
                {response && (
                  <Tag color="green">
                    置信度: {(response.confidence * 100).toFixed(1)}%
                  </Tag>
                )}
              </Space>
              
              <Space>
                <Button
                  type="text"
                  icon={<CopyOutlined />}
                  onClick={() => handleCopy(message.content)}
                  size="small"
                />
                <Button
                  type="text"
                  icon={<StarOutlined style={{ color: isFavorited ? '#faad14' : undefined }} />}
                  onClick={handleFavorite}
                  size="small"
                  title={isFavorited ? '取消收藏' : '收藏'}
                />
                <Button
                  type="text"
                  icon={<ExpandAltOutlined />}
                  onClick={() => setShowFullResponse(!showFullResponse)}
                  size="small"
                />
              </Space>
            </div>

            <div className="response-content">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeContent = String(children).replace(/\n$/, '');
                    const language = match ? match[1] : '';
                    const detectedAlgorithm = detectAlgorithmCode(codeContent, language);

                    if (!inline && match) {
                      return (
                        <div style={{ marginBottom: 16 }}>
                          <SyntaxHighlighter
                            style={tomorrow}
                            language={language}
                            PreTag="div"
                            {...props}
                          >
                            {codeContent}
                          </SyntaxHighlighter>

                          {detectedAlgorithm && (
                            <div style={{ marginTop: 12 }}>
                              <EmbeddedAlgorithmVisualizer
                                code={codeContent}
                                algorithm={detectedAlgorithm}
                                data={extractArrayData(codeContent)}
                                height={180}
                                autoPlay={true}
                              />
                            </div>
                          )}
                        </div>
                      );
                    } else {
                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                  },
                  // 自定义文本渲染以支持交互式内容
                  p({ children }) {
                    console.log('ReactMarkdown p children:', children);
                    console.log('ReactMarkdown p children type:', typeof children);
                    console.log('ReactMarkdown p children Array.isArray:', Array.isArray(children));

                    // 正确处理children参数
                    let content = '';
                    if (typeof children === 'string') {
                      content = children;
                    } else if (Array.isArray(children)) {
                      content = children.map(child =>
                        typeof child === 'string' ? child :
                        typeof child === 'object' && child?.props?.children ? child.props.children :
                        ''
                      ).join('');
                    } else if (children && typeof children === 'object' && children.props?.children) {
                      content = String(children.props.children);
                    } else {
                      content = String(children || '');
                    }

                    console.log('ReactMarkdown p processed content:', content);

                    const { concepts, problems } = getClickableItems();
                    return (
                      <p>
                        <InteractiveContent
                          content={content}
                          clickableConcepts={concepts}
                          clickableProblems={problems}
                          onConceptClick={handleConceptClick}
                          onProblemClick={handleProblemClick}
                          onCodeClick={(code) => {
                            navigator.clipboard.writeText(code);
                            antdMessage.success('代码已复制到剪贴板');
                          }}
                        />
                      </p>
                    );
                  }
                }}
              >
                {processMessageContent(message.content)}
              </ReactMarkdown>
            </div>

            {/* 内嵌知识图谱 - 优先使用增强图谱数据 */}
            {((enhancedGraphData && enhancedGraphData.nodes && enhancedGraphData.nodes.length > 0) ||
              (response?.graph_data && Array.isArray(response.graph_data.nodes) && response.graph_data.nodes.length > 0)) &&
             response.entities &&
             response.entities.length > 0 && (
              <InlineKnowledgeGraph
                graphData={enhancedGraphData || response.graph_data}
                entities={response.entities}
                showAnimation={false}
                isEnhanced={!!enhancedGraphData}
                onNodeClick={(nodeId, nodeData) => {
                  console.log('图谱节点点击:', nodeId, nodeData);
                  // 可以在这里添加节点点击处理逻辑
                }}
                onExpandClick={() => {
                  console.log('跳转到完整图谱页面');
                  // 可以在这里添加跳转到完整图谱页面的逻辑
                }}
              />
            )}

            {/* 图谱加载状态 */}
            {graphLoading && response.entities && response.entities.length > 0 && (
              <div style={{
                padding: '16px',
                textAlign: 'center',
                background: '#f0f9ff',
                borderRadius: '8px',
                margin: '16px 0'
              }}>
                <Space>
                  <Spin size="small" />
                  <Text type="secondary">正在加载增强图谱数据...</Text>
                </Space>
              </div>
            )}
          </div>

          {/* 详细信息展开区域 */}
          {response && showFullResponse && (
            <Collapse className="response-details" ghost>
              {/* 概念解释 */}
              {response.concept_explanation && (
                <Panel header="概念解释详情" key="concept">
                  <div className="concept-details">
                    <Title level={4}>
                      {safeRender(response.concept_explanation.concept_name) || '概念解释'}
                    </Title>
                    <Paragraph>
                      {safeRender(response.concept_explanation.definition)}
                    </Paragraph>
                    
                    {Array.isArray(response.concept_explanation.core_principles) && response.concept_explanation.core_principles.length > 0 && (
                      <div>
                        <Text strong>核心原理:</Text>
                        <ul>
                          {response.concept_explanation.core_principles.map((principle, i) => (
                            <li key={i}>
                              {safeRender(principle)}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </Panel>
              )}

              {/* 示例题目 */}
              {Array.isArray(response.example_problems) && response.example_problems.length > 0 && (
                <Panel header={`示例题目 (${response.example_problems.length}道)`} key="examples">
                  <div className="example-problems">
                    {response.example_problems.map((problem, index) => 
                      renderProblemCard(problem, index)
                    )}
                  </div>
                </Panel>
              )}

              {/* 相似题目 - 使用增强版组件 */}
              {Array.isArray(response.similar_problems) && response.similar_problems.length > 0 &&
               response.similar_problems.some(p => p.title && p.title !== '无' && p.title.trim() !== '') && (
                <Panel header="🎯 智能推荐" key="similar">
                  <EnhancedSimilarProblems
                    problems={response.similar_problems.filter(p => p.title && p.title !== '无' && p.title.trim() !== '')}
                    onProblemClick={handleProblemClick}
                    maxDisplay={6}
                  />
                </Panel>
              )}


            </Collapse>
          )}

          {/* 智能链接建议 */}
          <SmartLinkSuggestions
            response={response}
            onConceptClick={handleConceptClick}
            onProblemClick={handleProblemClick}
          />

          {/* 用户反馈区域 */}
          <div className="feedback-section">
            <Space>
              <Text type="secondary">这个回答对您有帮助吗？</Text>
              <Rate
                value={userRating}
                onChange={setUserRating}
                style={{ fontSize: 16 }}
              />
              <Button
                type="text"
                icon={<LikeOutlined />}
                size="small"
              />
              <Button
                type="text"
                icon={<DislikeOutlined />}
                size="small"
              />
            </Space>
          </div>
        </Card>
      </div>

      <style jsx>{`
        .message-item {
          display: flex;
          margin-bottom: 24px;
          align-items: flex-start;
        }
        
        .message-avatar {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: #52c41a;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          margin: 0 12px;
          flex-shrink: 0;
        }
        
        .message-content {
          flex: 1;
          max-width: 85%;
        }
        
        .response-card {
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .cancelled-message {
          opacity: 0.7;
          border: 1px solid #faad14;
          background-color: #fffbe6;
        }

        .cancelled-notice {
          margin-bottom: 12px;
          padding: 8px 12px;
          background-color: #fff7e6;
          border: 1px solid #ffd591;
          border-radius: 6px;
          display: flex;
          align-items: center;
        }
        
        .reasoning-section {
          margin-bottom: 16px;
          padding-bottom: 16px;
          border-bottom: 1px solid #f0f0f0;
        }
        
        .response-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid #f0f0f0;
        }
        
        .response-content {
          line-height: 1.6;
          color: #333;
        }
        
        .problem-card, .similar-problem-card {
          border: 1px solid #e8e8e8;
          transition: all 0.2s;
        }
        
        .problem-card:hover, .similar-problem-card:hover {
          border-color: #1890ff;
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
        }
        
        .problem-header, .similar-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }
        
        .problem-tags, .shared-tags {
          margin-top: 8px;
        }
        
        .recommendation-info, .learning-path {
          margin: 4px 0;
          font-size: 13px;
        }
        
        .feedback-section {
          margin-top: 16px;
          padding-top: 12px;
          border-top: 1px solid #f0f0f0;
        }
        
        @media (max-width: 768px) {
          .message-content {
            max-width: 90%;
          }
          
          .response-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
        }
      `}</style>
    </div>
  );
};

export default MessageItem;
