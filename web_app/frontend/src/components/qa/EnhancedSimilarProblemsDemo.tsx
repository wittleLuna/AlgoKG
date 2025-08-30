import React from 'react';
import { Card, Typography, Space } from 'antd';
import EnhancedSimilarProblems from './EnhancedSimilarProblems';
import { SimilarProblem } from '../../types';

const { Title, Paragraph } = Typography;

// 模拟测试数据
const mockSimilarProblems: SimilarProblem[] = [
  {
    title: "三数之和",
    hybrid_score: 0.85,
    embedding_score: 0.82,
    tag_score: 0.88,
    shared_tags: ["数组", "双指针", "排序"],
    learning_path: "掌握双指针技巧后学习多指针问题",
    recommendation_reason: "同样使用双指针技巧，是两数之和的进阶版本",
    learning_path_explanation: "在掌握两数之和的基础上，学习如何处理三个数的组合问题",
    recommendation_strength: "强烈推荐",
    clickable: true,
    complete_info: {
      id: "problem_three_sum",
      title: "三数之和",
      difficulty: "中等",
      platform: "LeetCode",
      algorithm_tags: ["双指针", "排序"],
      data_structure_tags: ["数组"],
      technique_tags: ["双指针"],
      solutions: [],
      code_implementations: [],
      key_insights: [],
      step_by_step_explanation: [],
      clickable: true
    }
  },
  {
    title: "四数之和",
    hybrid_score: 0.72,
    embedding_score: 0.70,
    tag_score: 0.74,
    shared_tags: ["数组", "双指针", "排序", "哈希表"],
    learning_path: "三数之和的扩展，学习多层循环优化",
    recommendation_reason: "进一步扩展多指针技巧，增加问题复杂度",
    learning_path_explanation: "基于三数之和的思路，学习如何处理更复杂的多数组合问题",
    recommendation_strength: "推荐",
    clickable: true,
    complete_info: {
      id: "problem_four_sum",
      title: "四数之和",
      difficulty: "中等",
      platform: "LeetCode",
      algorithm_tags: ["双指针", "排序"],
      data_structure_tags: ["数组", "哈希表"],
      technique_tags: ["双指针"],
      solutions: [],
      code_implementations: [],
      key_insights: [],
      step_by_step_explanation: [],
      clickable: true
    }
  },
  {
    title: "两数相加",
    hybrid_score: 0.68,
    embedding_score: 0.65,
    tag_score: 0.71,
    shared_tags: ["链表", "数学", "模拟"],
    learning_path: "学习链表操作和数学计算结合",
    recommendation_reason: "虽然数据结构不同，但都涉及两个数的处理逻辑",
    learning_path_explanation: "从数组操作转向链表操作，学习不同数据结构的处理方式",
    recommendation_strength: "推荐",
    clickable: true,
    complete_info: {
      id: "problem_add_two_numbers",
      title: "两数相加",
      difficulty: "中等",
      platform: "LeetCode",
      algorithm_tags: ["模拟"],
      data_structure_tags: ["链表"],
      technique_tags: ["模拟"],
      solutions: [],
      code_implementations: [],
      key_insights: [],
      step_by_step_explanation: [],
      clickable: true
    }
  },
  {
    title: "有效的括号",
    hybrid_score: 0.45,
    embedding_score: 0.42,
    tag_score: 0.48,
    shared_tags: ["栈", "字符串"],
    learning_path: "学习栈的基本应用",
    recommendation_reason: "都是经典的基础算法题，适合初学者练习",
    learning_path_explanation: "学习栈数据结构的基本应用，培养算法思维",
    recommendation_strength: "建议",
    clickable: true,
    complete_info: {
      id: "problem_valid_parentheses",
      title: "有效的括号",
      difficulty: "简单",
      platform: "LeetCode",
      algorithm_tags: ["栈"],
      data_structure_tags: ["字符串"],
      technique_tags: ["栈"],
      solutions: [],
      code_implementations: [],
      key_insights: [],
      step_by_step_explanation: [],
      clickable: true
    }
  },
  {
    title: "最长公共前缀",
    hybrid_score: 0.38,
    embedding_score: 0.35,
    tag_score: 0.41,
    shared_tags: ["字符串", "分治"],
    learning_path: "字符串处理基础练习",
    recommendation_reason: "同样是字符串处理的基础题目",
    learning_path_explanation: "练习字符串的基本操作和比较技巧",
    recommendation_strength: "可选",
    clickable: true,
    complete_info: {
      id: "problem_longest_common_prefix",
      title: "最长公共前缀",
      difficulty: "简单",
      platform: "LeetCode",
      algorithm_tags: ["分治"],
      data_structure_tags: ["字符串"],
      technique_tags: ["分治"],
      solutions: [],
      code_implementations: [],
      key_insights: [],
      step_by_step_explanation: [],
      clickable: true
    }
  },
  {
    title: "合并两个有序链表",
    hybrid_score: 0.42,
    embedding_score: 0.40,
    tag_score: 0.44,
    shared_tags: ["链表", "递归", "迭代"],
    learning_path: "链表操作基础",
    recommendation_reason: "都涉及到两个元素的处理，是很好的对比学习",
    learning_path_explanation: "学习链表的基本操作，理解递归和迭代的区别",
    recommendation_strength: "建议",
    clickable: true,
    complete_info: {
      id: "problem_merge_two_sorted_lists",
      title: "合并两个有序链表",
      difficulty: "简单",
      platform: "LeetCode",
      algorithm_tags: ["递归", "迭代"],
      data_structure_tags: ["链表"],
      technique_tags: ["递归", "迭代"],
      solutions: [],
      code_implementations: [],
      key_insights: [],
      step_by_step_explanation: [],
      clickable: true
    }
  }
];

const EnhancedSimilarProblemsDemo: React.FC = () => {
  const handleProblemClick = (title: string) => {
    console.log('点击题目:', title);
    alert(`点击了题目: ${title}`);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Card>
          <Title level={2}>增强版相似推荐题目组件演示</Title>
          <Paragraph>
            这是新设计的相似推荐题目组件，具有以下特点：
          </Paragraph>
          <ul>
            <li>🎯 <strong>智能推荐级别</strong>：根据相似度分数显示不同的推荐强度</li>
            <li>🎨 <strong>美观的卡片设计</strong>：支持网格和列表两种显示模式</li>
            <li>📊 <strong>可视化相似度</strong>：使用进度条和颜色直观显示相似程度</li>
            <li>🏷️ <strong>智能标签显示</strong>：展示共同标签，超出部分自动折叠</li>
            <li>📱 <strong>响应式设计</strong>：适配不同屏幕尺寸</li>
            <li>⚡ <strong>交互体验</strong>：悬停效果、点击反馈等</li>
          </ul>
        </Card>

        <Card title="相似推荐题目展示">
          <EnhancedSimilarProblems
            problems={mockSimilarProblems}
            onProblemClick={handleProblemClick}
            maxDisplay={4}
          />
        </Card>

        <Card>
          <Title level={3}>推荐级别说明</Title>
          <Space direction="vertical">
            <div>🏆 <strong style={{ color: '#f5222d' }}>强烈推荐</strong> (80%+)：高度相似，强烈建议学习</div>
            <div>👍 <strong style={{ color: '#fa8c16' }}>推荐</strong> (60-80%)：较为相似，建议学习</div>
            <div>💡 <strong style={{ color: '#1890ff' }}>建议</strong> (40-60%)：有一定相似性，可以考虑</div>
            <div>⭐ <strong style={{ color: '#52c41a' }}>可选</strong> (40%以下)：相关度较低，可选择性学习</div>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default EnhancedSimilarProblemsDemo;
