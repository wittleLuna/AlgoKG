import React from 'react';
import { Card, Row, Col, Typography, Divider } from 'antd';
import MessageItem from '../qa/MessageItem';
import { ChatMessage } from '../../types';

const { Title, Paragraph } = Typography;

const AlgorithmDemo: React.FC = () => {
  // 模拟包含算法代码的消息
  const demoMessages: ChatMessage[] = [
    {
      id: '1',
      type: 'assistant',
      content: `# 冒泡排序算法详解

冒泡排序是一种简单的排序算法，它重复地遍历要排序的数列，一次比较两个元素，如果它们的顺序错误就把它们交换过来。

## 算法实现

\`\`\`javascript
function bubbleSort(arr) {
  const n = arr.length;
  let data = [...arr];
  
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      if (data[j] > data[j + 1]) {
        // 交换元素
        [data[j], data[j + 1]] = [data[j + 1], data[j]];
      }
    }
  }
  
  return data;
}

// 测试数据
const testArray = [64, 34, 25, 12, 22, 11, 90];
console.log(bubbleSort(testArray));
\`\`\`

## 算法特点

- **时间复杂度**: O(n²)
- **空间复杂度**: O(1)
- **稳定性**: 稳定排序
- **适用场景**: 小规模数据排序`,
      timestamp: new Date(),
      reasoning_steps: [],
      response: {
        response_id: '1',
        query: '',
        intent: 'algorithm_explanation',
        entities: [],
        example_problems: [],
        similar_problems: [],
        integrated_response: '',
        reasoning_path: [],
        status: 'success',
        confidence: 0.9,
        processing_time: 0,
        metadata: {},
        timestamp: new Date().toISOString(),
        concept_explanation: {
          concept_name: '冒泡排序',
          definition: '冒泡排序是一种简单的排序算法',
          core_principles: [],
          advantages: [],
          disadvantages: [],
          implementation_key_points: [],
          common_variations: [],
          real_world_applications: [],
          learning_progression: {},
          clickable_concepts: []
        },
        graph_data: {
          nodes: [],
          edges: [],
          layout_type: 'force'
        }
      }
    },
    {
      id: '2',
      type: 'assistant',
      content: `# 选择排序算法

选择排序是一种简单直观的排序算法。它的工作原理是每次从待排序的数据元素中选出最小（或最大）的一个元素，存放在序列的起始位置。

## 算法实现

\`\`\`javascript
function selectionSort(arr) {
  const n = arr.length;
  let data = [...arr];
  
  for (let i = 0; i < n - 1; i++) {
    let minIdx = i;
    
    // 找到最小元素的索引
    for (let j = i + 1; j < n; j++) {
      if (data[j] < data[minIdx]) {
        minIdx = j;
      }
    }
    
    // 交换最小元素到当前位置
    if (minIdx !== i) {
      [data[i], data[minIdx]] = [data[minIdx], data[i]];
    }
  }
  
  return data;
}

// 测试数据
const numbers = [29, 10, 14, 37, 13, 25, 8];
console.log(selectionSort(numbers));
\`\`\`

## 算法分析

选择排序的主要优点是实现简单，缺点是效率较低，不适合大规模数据排序。`,
      timestamp: new Date(),
      reasoning_steps: [],
      response: {
        response_id: '2',
        query: '',
        intent: 'algorithm_explanation',
        entities: [],
        example_problems: [],
        similar_problems: [],
        integrated_response: '',
        reasoning_path: [],
        status: 'success',
        confidence: 0.9,
        processing_time: 0,
        metadata: {},
        timestamp: new Date().toISOString(),
        concept_explanation: {
          concept_name: '选择排序',
          definition: '选择排序是一种简单直观的排序算法',
          core_principles: [],
          advantages: [],
          disadvantages: [],
          implementation_key_points: [],
          common_variations: [],
          real_world_applications: [],
          learning_progression: {},
          clickable_concepts: []
        },
        graph_data: {
          nodes: [],
          edges: [],
          layout_type: 'force'
        }
      }
    }
  ];

  return (
    <div style={{ padding: '0 24px' }}>
      <Title level={2}>算法可视化演示</Title>
      <Paragraph>
        以下演示展示了如何在智能问答中自动检测算法代码并提供实时可视化。
        当系统检测到排序算法代码时，会自动在代码下方显示动画可视化。
      </Paragraph>
      
      <Divider />
      
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card title="冒泡排序可视化演示" size="small">
            <MessageItem
              message={demoMessages[0]}
              onConceptClick={(concept) => console.log('点击概念:', concept)}
              onProblemClick={(problem) => console.log('点击题目:', problem)}
            />
          </Card>
        </Col>
        
        <Col span={24}>
          <Card title="选择排序可视化演示" size="small">
            <MessageItem
              message={demoMessages[1]}
              onConceptClick={(concept) => console.log('点击概念:', concept)}
              onProblemClick={(problem) => console.log('点击题目:', problem)}
            />
          </Card>
        </Col>
      </Row>
      
      <Divider />
      
      <Card title="功能特点" size="small">
        <Row gutter={16}>
          <Col span={6}>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎯</div>
              <div style={{ fontWeight: 'bold' }}>自动检测</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                智能识别算法代码类型
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎬</div>
              <div style={{ fontWeight: 'bold' }}>实时动画</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                逐步展示算法执行过程
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎮</div>
              <div style={{ fontWeight: 'bold' }}>交互控制</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                播放、暂停、单步执行
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div style={{ textAlign: 'center', padding: '16px' }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>📊</div>
              <div style={{ fontWeight: 'bold' }}>数据可视化</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                直观的图形化展示
              </div>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default AlgorithmDemo;
