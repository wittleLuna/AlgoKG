import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Button, Select, Slider, Space, Typography, Row, Col, message, Spin, Input } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  CaretRightOutlined,
  ReloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
// import MonacoEditor from '@monaco-editor/react';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface VisualizationStep {
  id: number;
  description: string;
  data: any[];
  highlights: number[];
  comparisons: number[];
  swaps?: [number, number];
  message?: string;
}

interface AlgorithmVisualizerProps {
  algorithm?: string;
  initialCode?: string;
  data?: number[];
  onStepChange?: (step: VisualizationStep) => void;
}

const AlgorithmVisualizer: React.FC<AlgorithmVisualizerProps> = ({
  algorithm = 'bubble_sort',
  initialCode = '',
  data = [64, 34, 25, 12, 22, 11, 90],
  onStepChange
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState<VisualizationStep[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(500);
  const [code, setCode] = useState(initialCode);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState(algorithm);
  const [isExecuting, setIsExecuting] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 预定义算法代码模板
  const algorithmTemplates = {
    bubble_sort: `function bubbleSort(arr) {
  const steps = [];
  const n = arr.length;
  let data = [...arr];
  
  steps.push({
    id: 0,
    description: "开始冒泡排序",
    data: [...data],
    highlights: [],
    comparisons: []
  });
  
  for (let i = 0; i < n - 1; i++) {
    for (let j = 0; j < n - i - 1; j++) {
      // 比较相邻元素
      steps.push({
        id: steps.length,
        description: \`比较 \${data[j]} 和 \${data[j + 1]}\`,
        data: [...data],
        highlights: [j, j + 1],
        comparisons: [j, j + 1]
      });
      
      if (data[j] > data[j + 1]) {
        // 交换元素
        [data[j], data[j + 1]] = [data[j + 1], data[j]];
        steps.push({
          id: steps.length,
          description: \`交换 \${data[j + 1]} 和 \${data[j]}\`,
          data: [...data],
          highlights: [j, j + 1],
          comparisons: [],
          swaps: [j, j + 1]
        });
      }
    }
  }
  
  steps.push({
    id: steps.length,
    description: "排序完成",
    data: [...data],
    highlights: [],
    comparisons: []
  });
  
  return steps;
}`,
    
    quick_sort: `function quickSort(arr, low = 0, high = arr.length - 1, steps = []) {
  if (steps.length === 0) {
    steps.push({
      id: 0,
      description: "开始快速排序",
      data: [...arr],
      highlights: [],
      comparisons: []
    });
  }
  
  if (low < high) {
    const pi = partition(arr, low, high, steps);
    quickSort(arr, low, pi - 1, steps);
    quickSort(arr, pi + 1, high, steps);
  }
  
  return steps;
}

function partition(arr, low, high, steps) {
  const pivot = arr[high];
  let i = low - 1;
  
  steps.push({
    id: steps.length,
    description: \`选择基准元素: \${pivot}\`,
    data: [...arr],
    highlights: [high],
    comparisons: []
  });
  
  for (let j = low; j < high; j++) {
    steps.push({
      id: steps.length,
      description: \`比较 \${arr[j]} 与基准 \${pivot}\`,
      data: [...arr],
      highlights: [j, high],
      comparisons: [j, high]
    });
    
    if (arr[j] < pivot) {
      i++;
      [arr[i], arr[j]] = [arr[j], arr[i]];
      steps.push({
        id: steps.length,
        description: \`交换 \${arr[j]} 和 \${arr[i]}\`,
        data: [...arr],
        highlights: [i, j],
        comparisons: [],
        swaps: [i, j]
      });
    }
  }
  
  [arr[i + 1], arr[high]] = [arr[high], arr[i + 1]];
  steps.push({
    id: steps.length,
    description: \`将基准放到正确位置\`,
    data: [...arr],
    highlights: [i + 1, high],
    comparisons: [],
    swaps: [i + 1, high]
  });
  
  return i + 1;
}`,

    binary_search: `function binarySearch(arr, target) {
  const steps = [];
  let left = 0;
  let right = arr.length - 1;
  
  steps.push({
    id: 0,
    description: \`在有序数组中查找 \${target}\`,
    data: [...arr],
    highlights: [],
    comparisons: []
  });
  
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    
    steps.push({
      id: steps.length,
      description: \`检查中间位置 \${mid}: \${arr[mid]}\`,
      data: [...arr],
      highlights: [mid],
      comparisons: [mid]
    });
    
    if (arr[mid] === target) {
      steps.push({
        id: steps.length,
        description: \`找到目标值 \${target} 在位置 \${mid}\`,
        data: [...arr],
        highlights: [mid],
        comparisons: []
      });
      return steps;
    }
    
    if (arr[mid] < target) {
      left = mid + 1;
      steps.push({
        id: steps.length,
        description: \`\${arr[mid]} < \${target}, 在右半部分查找\`,
        data: [...arr],
        highlights: Array.from({length: right - left + 1}, (_, i) => left + i),
        comparisons: []
      });
    } else {
      right = mid - 1;
      steps.push({
        id: steps.length,
        description: \`\${arr[mid]} > \${target}, 在左半部分查找\`,
        data: [...arr],
        highlights: Array.from({length: right - left + 1}, (_, i) => left + i),
        comparisons: []
      });
    }
  }
  
  steps.push({
    id: steps.length,
    description: \`未找到目标值 \${target}\`,
    data: [...arr],
    highlights: [],
    comparisons: []
  });
  
  return steps;
}`
  };

  // 初始化代码
  useEffect(() => {
    if (algorithmTemplates[selectedAlgorithm as keyof typeof algorithmTemplates]) {
      setCode(algorithmTemplates[selectedAlgorithm as keyof typeof algorithmTemplates]);
    }
  }, [selectedAlgorithm]);

  // 执行算法代码
  const executeAlgorithm = useCallback(async () => {
    setIsExecuting(true);
    try {
      // 创建安全的执行环境
      const func = new Function('data', `
        ${code}
        
        // 根据算法类型调用相应函数
        if (typeof bubbleSort !== 'undefined') {
          return bubbleSort(data);
        } else if (typeof quickSort !== 'undefined') {
          return quickSort([...data]);
        } else if (typeof binarySearch !== 'undefined') {
          return binarySearch(data, 25); // 默认查找25
        }
        
        return [];
      `);
      
      const result = func([...data]);
      setSteps(result || []);
      setCurrentStep(0);
      message.success('算法执行成功！');
    } catch (error) {
      console.error('算法执行错误:', error);
      message.error('代码执行出错，请检查语法');
    } finally {
      setIsExecuting(false);
    }
  }, [code, data]);

  // 播放控制
  const play = useCallback(() => {
    if (!steps || steps.length === 0) return;
    if (currentStep >= steps.length - 1) {
      setCurrentStep(0);
    }
    setIsPlaying(true);
  }, [currentStep, steps]);

  const pause = useCallback(() => {
    setIsPlaying(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    pause();
    setCurrentStep(0);
  }, [pause]);

  const stepForward = useCallback(() => {
    if (!steps || steps.length === 0) return;
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  }, [currentStep, steps]);

  // 自动播放
  useEffect(() => {
    if (isPlaying && steps && steps.length > 0 && currentStep < steps.length - 1) {
      intervalRef.current = setInterval(() => {
        setCurrentStep(prev => {
          if (!steps || prev >= steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, speed);
    } else {
      setIsPlaying(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, currentStep, steps, speed]);

  // 通知父组件步骤变化
  useEffect(() => {
    if (steps && steps[currentStep] && onStepChange) {
      onStepChange(steps[currentStep]);
    }
  }, [currentStep, steps, onStepChange]);

  return (
    <div style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        {/* 代码编辑器 */}
        <Col span={12}>
          <Card 
            title="算法代码" 
            size="small"
            extra={
              <Space>
                <Select
                  value={selectedAlgorithm}
                  onChange={setSelectedAlgorithm}
                  style={{ width: 120 }}
                >
                  <Option value="bubble_sort">冒泡排序</Option>
                  <Option value="quick_sort">快速排序</Option>
                  <Option value="binary_search">二分查找</Option>
                </Select>
                <Button 
                  type="primary" 
                  onClick={executeAlgorithm}
                  loading={isExecuting}
                  size="small"
                >
                  执行
                </Button>
              </Space>
            }
          >
            <TextArea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="在此输入JavaScript算法代码..."
              style={{
                height: 300,
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '12px'
              }}
              autoSize={false}
            />
          </Card>
        </Col>

        {/* 可视化控制 */}
        <Col span={12}>
          <Card title="可视化控制" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              {/* 播放控制 */}
              <Space>
                <Button
                  type={isPlaying ? "default" : "primary"}
                  icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  onClick={isPlaying ? pause : play}
                  disabled={!steps || steps.length === 0}
                >
                  {isPlaying ? '暂停' : '播放'}
                </Button>
                <Button
                  icon={<CaretRightOutlined />}
                  onClick={stepForward}
                  disabled={!steps || steps.length === 0 || currentStep >= steps.length - 1}
                >
                  单步
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={reset}
                  disabled={!steps || steps.length === 0}
                >
                  重置
                </Button>
              </Space>

              {/* 速度控制 */}
              <div>
                <Text>播放速度: {speed}ms</Text>
                <Slider
                  min={100}
                  max={2000}
                  step={100}
                  value={speed}
                  onChange={setSpeed}
                  style={{ marginTop: 8 }}
                />
              </div>

              {/* 步骤信息 */}
              {steps && steps.length > 0 && (
                <div>
                  <Text>步骤: {currentStep + 1} / {steps.length}</Text>
                  <div style={{ marginTop: 8 }}>
                    <Text type="secondary">
                      {steps[currentStep]?.description || ''}
                    </Text>
                  </div>
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AlgorithmVisualizer;
