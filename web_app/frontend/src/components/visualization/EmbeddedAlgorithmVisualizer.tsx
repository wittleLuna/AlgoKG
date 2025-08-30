import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Button, Space, Typography, message, Spin } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  CaretRightOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import * as d3 from 'd3';

const { Text } = Typography;

interface VisualizationStep {
  id: number;
  description: string;
  data: any[];
  highlights: number[];
  comparisons: number[];
  swaps?: [number, number];
  message?: string;
}

interface EmbeddedAlgorithmVisualizerProps {
  code?: string;
  data?: number[];
  algorithm?: string;
  height?: number;
  autoPlay?: boolean;
}

const EmbeddedAlgorithmVisualizer: React.FC<EmbeddedAlgorithmVisualizerProps> = ({
  code = '',
  data = [64, 34, 25, 12, 22, 11, 90],
  algorithm = 'bubble_sort',
  height = 200,
  autoPlay = false
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState<VisualizationStep[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const svgRef = useRef<SVGSVGElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 预定义算法代码
  const getAlgorithmCode = useCallback((algorithmType: string) => {
    const templates = {
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
            steps.push({
              id: steps.length,
              description: \`比较 \${data[j]} 和 \${data[j + 1]}\`,
              data: [...data],
              highlights: [j, j + 1],
              comparisons: [j, j + 1]
            });
            
            if (data[j] > data[j + 1]) {
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
      
      selection_sort: `function selectionSort(arr) {
        const steps = [];
        const n = arr.length;
        let data = [...arr];
        
        steps.push({
          id: 0,
          description: "开始选择排序",
          data: [...data],
          highlights: [],
          comparisons: []
        });
        
        for (let i = 0; i < n - 1; i++) {
          let minIdx = i;
          steps.push({
            id: steps.length,
            description: \`寻找从位置 \${i} 开始的最小元素\`,
            data: [...data],
            highlights: [i],
            comparisons: []
          });
          
          for (let j = i + 1; j < n; j++) {
            steps.push({
              id: steps.length,
              description: \`比较 \${data[j]} 和当前最小值 \${data[minIdx]}\`,
              data: [...data],
              highlights: [minIdx, j],
              comparisons: [minIdx, j]
            });
            
            if (data[j] < data[minIdx]) {
              minIdx = j;
              steps.push({
                id: steps.length,
                description: \`找到新的最小值 \${data[minIdx]} 在位置 \${minIdx}\`,
                data: [...data],
                highlights: [minIdx],
                comparisons: []
              });
            }
          }
          
          if (minIdx !== i) {
            [data[i], data[minIdx]] = [data[minIdx], data[i]];
            steps.push({
              id: steps.length,
              description: \`交换 \${data[minIdx]} 和 \${data[i]}\`,
              data: [...data],
              highlights: [i, minIdx],
              comparisons: [],
              swaps: [i, minIdx]
            });
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
      }`
    };
    
    return templates[algorithmType as keyof typeof templates] || templates.bubble_sort;
  }, []);

  // 执行算法
  const executeAlgorithm = useCallback(async () => {
    setIsExecuting(true);
    try {
      const algorithmCode = code || getAlgorithmCode(algorithm);
      const func = new Function('data', `
        ${algorithmCode}
        
        if (typeof bubbleSort !== 'undefined') {
          return bubbleSort(data);
        } else if (typeof selectionSort !== 'undefined') {
          return selectionSort(data);
        }
        
        return [];
      `);
      
      const result = func([...data]);
      setSteps(result || []);
      setCurrentStep(0);
      
      if (autoPlay && result && result.length > 0) {
        setTimeout(() => setIsPlaying(true), 500);
      }
    } catch (error) {
      console.error('算法执行错误:', error);
      message.error('算法执行出错');
    } finally {
      setIsExecuting(false);
    }
  }, [code, algorithm, data, autoPlay, getAlgorithmCode]);

  // 初始化执行
  useEffect(() => {
    executeAlgorithm();
  }, [executeAlgorithm]);

  // 可视化渲染
  useEffect(() => {
    if (!steps || !steps[currentStep] || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const step = steps[currentStep];
    const margin = { top: 20, right: 20, bottom: 40, left: 20 };
    const width = 400;
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    const barWidth = innerWidth / step.data.length;
    const maxValue = Math.max(...step.data);
    const yScale = d3.scaleLinear()
      .domain([0, maxValue])
      .range([innerHeight, 0]);

    // 绘制数组元素
    const bars = g.selectAll('.bar')
      .data(step.data)
      .enter()
      .append('g')
      .attr('class', 'bar')
      .attr('transform', (d, i) => `translate(${i * barWidth}, 0)`);

    // 绘制矩形
    bars.append('rect')
      .attr('width', barWidth - 2)
      .attr('height', d => innerHeight - yScale(d))
      .attr('y', d => yScale(d))
      .attr('fill', (d, i) => {
        if (step.highlights.includes(i)) {
          return step.comparisons.includes(i) ? '#ff4d4f' : '#52c41a';
        }
        if (step.swaps && (step.swaps[0] === i || step.swaps[1] === i)) {
          return '#faad14';
        }
        return '#1890ff';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    // 添加数值标签
    bars.append('text')
      .attr('x', barWidth / 2)
      .attr('y', d => yScale(d) - 5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text(d => d);

    // 添加索引标签
    bars.append('text')
      .attr('x', barWidth / 2)
      .attr('y', innerHeight + 15)
      .attr('text-anchor', 'middle')
      .attr('font-size', '8px')
      .attr('fill', '#666')
      .text((d, i) => i);

  }, [currentStep, steps, height]);

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
      }, 1000);
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
  }, [isPlaying, currentStep, steps]);

  const play = () => {
    if (!steps || steps.length === 0) return;
    if (currentStep >= steps.length - 1) {
      setCurrentStep(0);
    }
    setIsPlaying(true);
  };

  const pause = () => {
    setIsPlaying(false);
  };

  const reset = () => {
    pause();
    setCurrentStep(0);
  };

  const stepForward = () => {
    if (!steps || steps.length === 0) return;
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  if (isExecuting) {
    return (
      <Card size="small" style={{ textAlign: 'center', padding: '20px' }}>
        <Spin />
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">正在执行算法...</Text>
        </div>
      </Card>
    );
  }

  return (
    <Card 
      title="算法可视化" 
      size="small"
      extra={
        <Space size="small">
          <Button
            size="small"
            type={isPlaying ? "default" : "primary"}
            icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={isPlaying ? pause : play}
            disabled={!steps || steps.length === 0}
          >
            {isPlaying ? '暂停' : '播放'}
          </Button>
          <Button
            size="small"
            icon={<CaretRightOutlined />}
            onClick={stepForward}
            disabled={!steps || steps.length === 0 || currentStep >= steps.length - 1}
          />
          <Button
            size="small"
            icon={<ReloadOutlined />}
            onClick={reset}
            disabled={!steps || steps.length === 0}
          />
        </Space>
      }
    >
      <div style={{ textAlign: 'center', marginBottom: 12 }}>
        {steps && steps[currentStep] && (
          <Text style={{ fontSize: '12px' }}>
            步骤 {currentStep + 1}/{steps.length}: {steps[currentStep].description}
          </Text>
        )}
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <svg
          ref={svgRef}
          width={400}
          height={height}
          style={{ border: '1px solid #f0f0f0', borderRadius: '4px' }}
        />
      </div>

      {/* 简化的图例 */}
      <div style={{ marginTop: 8, display: 'flex', justifyContent: 'center', gap: 12, fontSize: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <div style={{ width: 8, height: 8, backgroundColor: '#1890ff' }}></div>
          <span>普通</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <div style={{ width: 8, height: 8, backgroundColor: '#52c41a' }}></div>
          <span>高亮</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <div style={{ width: 8, height: 8, backgroundColor: '#ff4d4f' }}></div>
          <span>比较</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <div style={{ width: 8, height: 8, backgroundColor: '#faad14' }}></div>
          <span>交换</span>
        </div>
      </div>
    </Card>
  );
};

export default EmbeddedAlgorithmVisualizer;
