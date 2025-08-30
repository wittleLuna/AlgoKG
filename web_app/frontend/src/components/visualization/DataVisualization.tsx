import React, { useEffect, useRef } from 'react';
import { Card } from 'antd';
import * as d3 from 'd3';

interface VisualizationStep {
  id: number;
  description: string;
  data: any[];
  highlights: number[];
  comparisons: number[];
  swaps?: [number, number];
  message?: string;
}

interface DataVisualizationProps {
  step?: VisualizationStep;
  width?: number;
  height?: number;
  type?: 'array' | 'tree' | 'graph';
}

const DataVisualization: React.FC<DataVisualizationProps> = ({
  step,
  width = 600,
  height = 300,
  type = 'array'
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!step || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // 清除之前的内容

    if (type === 'array') {
      renderArrayVisualization(svg, step, width, height);
    } else if (type === 'tree') {
      renderTreeVisualization(svg, step, width, height);
    } else if (type === 'graph') {
      renderGraphVisualization(svg, step, width, height);
    }
  }, [step, width, height, type]);

  const renderArrayVisualization = (svg: any, step: VisualizationStep, w: number, h: number) => {
    const data = step.data;
    const margin = { top: 50, right: 50, bottom: 50, left: 50 };
    const innerWidth = w - margin.left - margin.right;
    const innerHeight = h - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // 计算每个元素的位置和大小
    const barWidth = innerWidth / data.length;
    const maxValue = Math.max(...data);
    const yScale = d3.scaleLinear()
      .domain([0, maxValue])
      .range([innerHeight, 0]);

    // 绘制数组元素
    const bars = g.selectAll('.bar')
      .data(data)
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
      .attr('stroke-width', 1)
      .style('transition', 'all 0.3s ease');

    // 添加数值标签
    bars.append('text')
      .attr('x', barWidth / 2)
      .attr('y', d => yScale(d) - 5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', '#333')
      .text(d => d);

    // 添加索引标签
    bars.append('text')
      .attr('x', barWidth / 2)
      .attr('y', innerHeight + 20)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text((d, i) => i);

    // 添加动画效果
    if (step.swaps) {
      const [i, j] = step.swaps;
      // 添加交换动画
      g.selectAll('.bar')
        .filter((d, index) => index === i || index === j)
        .select('rect')
        .transition()
        .duration(300)
        .attr('transform', 'scale(1.1)')
        .transition()
        .duration(300)
        .attr('transform', 'scale(1)');
    }

    // 添加比较指示器
    if (step.comparisons.length === 2) {
      const [i, j] = step.comparisons;
      g.append('path')
        .attr('d', `M ${i * barWidth + barWidth/2} ${innerHeight + 35} 
                   Q ${(i + j) * barWidth/2 + barWidth/2} ${innerHeight + 50} 
                   ${j * barWidth + barWidth/2} ${innerHeight + 35}`)
        .attr('stroke', '#ff4d4f')
        .attr('stroke-width', 2)
        .attr('fill', 'none')
        .attr('marker-end', 'url(#arrowhead)');

      // 添加箭头标记
      svg.append('defs')
        .append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 8)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#ff4d4f');
    }
  };

  const renderTreeVisualization = (svg: any, step: VisualizationStep, w: number, h: number) => {
    // 树形结构可视化实现
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = w - margin.left - margin.right;
    const innerHeight = h - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // 这里可以根据具体的树形数据结构来实现
    // 暂时显示提示信息
    g.append('text')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('fill', '#666')
      .text('树形可视化 - 开发中');
  };

  const renderGraphVisualization = (svg: any, step: VisualizationStep, w: number, h: number) => {
    // 图形结构可视化实现
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = w - margin.left - margin.right;
    const innerHeight = h - margin.top - margin.bottom;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // 这里可以根据具体的图形数据结构来实现
    // 暂时显示提示信息
    g.append('text')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '16px')
      .attr('fill', '#666')
      .text('图形可视化 - 开发中');
  };

  return (
    <Card
      title="算法可视化"
      size="small"
      style={{ minHeight: height + 100 }}
      bodyStyle={{ overflow: 'visible' }}
    >
      <div style={{ textAlign: 'center', marginBottom: 16 }}>
        {step && (
          <div>
            <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: 8 }}>
              步骤 {step.id + 1}: {step.description}
            </div>
            {step.message && (
              <div style={{ fontSize: '12px', color: '#666' }}>
                {step.message}
              </div>
            )}
          </div>
        )}
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <svg
          ref={svgRef}
          width={width}
          height={height}
          style={{ border: '1px solid #f0f0f0', borderRadius: '4px' }}
        />
      </div>

      {/* 图例 */}
      <div style={{ marginTop: 16, display: 'flex', justifyContent: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 12, height: 12, backgroundColor: '#1890ff' }}></div>
          <span style={{ fontSize: '12px' }}>普通元素</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 12, height: 12, backgroundColor: '#52c41a' }}></div>
          <span style={{ fontSize: '12px' }}>高亮元素</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 12, height: 12, backgroundColor: '#ff4d4f' }}></div>
          <span style={{ fontSize: '12px' }}>比较元素</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 12, height: 12, backgroundColor: '#faad14' }}></div>
          <span style={{ fontSize: '12px' }}>交换元素</span>
        </div>
      </div>
    </Card>
  );
};

export default DataVisualization;
