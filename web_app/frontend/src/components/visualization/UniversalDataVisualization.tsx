import React, { useEffect, useRef } from 'react';
import { Card } from 'antd';
import * as d3 from 'd3';

interface VisualizationStep {
  id: number;
  description: string;
  data: any;
  highlights?: number[];
  comparisons?: number[];
  swaps?: number[];
  visited?: any[];
  path?: any[];
  operation?: string;
}

interface UniversalDataVisualizationProps {
  step: VisualizationStep;
  dataStructure: string;
  width?: number;
  height?: number;
}

const UniversalDataVisualization: React.FC<UniversalDataVisualizationProps> = ({
  step,
  dataStructure,
  width = 800,
  height = 400
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !step) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    switch (dataStructure) {
      case 'array':
        renderArray(g, step, innerWidth, innerHeight);
        break;
      case 'stack':
        renderStack(g, step, innerWidth, innerHeight);
        break;
      case 'queue':
        renderQueue(g, step, innerWidth, innerHeight);
        break;
      case 'tree':
        renderTree(g, step, innerWidth, innerHeight);
        break;
      case 'graph':
        renderGraph(g, step, innerWidth, innerHeight);
        break;
      default:
        renderArray(g, step, innerWidth, innerHeight);
    }
  }, [step, dataStructure, width, height]);

  const renderArray = (g: any, step: VisualizationStep, width: number, height: number) => {
    const data = Array.isArray(step.data) ? step.data : [];
    if (data.length === 0) return;

    const cellWidth = Math.min(60, width / data.length);
    const cellHeight = 50;
    const startX = (width - cellWidth * data.length) / 2;
    const startY = height / 2 - cellHeight / 2;

    // 绘制数组元素
    const cells = g.selectAll(".array-cell")
      .data(data)
      .enter()
      .append("g")
      .attr("class", "array-cell")
      .attr("transform", (d: any, i: number) => `translate(${startX + i * cellWidth}, ${startY})`);

    // 绘制矩形
    cells.append("rect")
      .attr("width", cellWidth - 2)
      .attr("height", cellHeight)
      .attr("fill", (d: any, i: number) => {
        if (step.highlights?.includes(i)) return "#ff7875";
        if (step.comparisons?.includes(i)) return "#ffd666";
        if (step.swaps?.includes(i)) return "#95de64";
        return "#f0f0f0";
      })
      .attr("stroke", "#d9d9d9")
      .attr("stroke-width", 1);

    // 绘制数值
    cells.append("text")
      .attr("x", cellWidth / 2 - 1)
      .attr("y", cellHeight / 2)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "middle")
      .attr("font-size", "14px")
      .attr("font-weight", "bold")
      .text((d: any) => d);

    // 绘制索引
    cells.append("text")
      .attr("x", cellWidth / 2 - 1)
      .attr("y", -5)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text((d: any, i: number) => i);
  };

  const renderStack = (g: any, step: VisualizationStep, width: number, height: number) => {
    const data = Array.isArray(step.data) ? step.data : [];
    const cellWidth = 80;
    const cellHeight = 40;
    const startX = width / 2 - cellWidth / 2;
    const startY = height - 50;

    // 绘制栈底标识
    g.append("text")
      .attr("x", startX + cellWidth / 2)
      .attr("y", startY + 30)
      .attr("text-anchor", "middle")
      .attr("font-size", "12px")
      .attr("fill", "#666")
      .text("栈底");

    // 绘制栈元素
    data.forEach((value: any, index: number) => {
      const y = startY - (index + 1) * cellHeight;
      
      g.append("rect")
        .attr("x", startX)
        .attr("y", y)
        .attr("width", cellWidth)
        .attr("height", cellHeight - 2)
        .attr("fill", step.highlights?.includes(index) ? "#ff7875" : "#f0f0f0")
        .attr("stroke", "#d9d9d9")
        .attr("stroke-width", 1);

      g.append("text")
        .attr("x", startX + cellWidth / 2)
        .attr("y", y + cellHeight / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("font-size", "14px")
        .attr("font-weight", "bold")
        .text(value);
    });

    // 绘制栈顶指针
    if (data.length > 0) {
      const topY = startY - data.length * cellHeight;
      g.append("text")
        .attr("x", startX + cellWidth + 10)
        .attr("y", topY + cellHeight / 2)
        .attr("dominant-baseline", "middle")
        .attr("font-size", "12px")
        .attr("fill", "#1890ff")
        .text("← 栈顶");
    }
  };

  const renderQueue = (g: any, step: VisualizationStep, width: number, height: number) => {
    const data = Array.isArray(step.data) ? step.data : [];
    if (data.length === 0) return;

    const cellWidth = Math.min(60, width / Math.max(data.length, 5));
    const cellHeight = 50;
    const startX = (width - cellWidth * data.length) / 2;
    const startY = height / 2 - cellHeight / 2;

    // 绘制队列元素
    data.forEach((value: any, index: number) => {
      const x = startX + index * cellWidth;
      
      g.append("rect")
        .attr("x", x)
        .attr("y", startY)
        .attr("width", cellWidth - 2)
        .attr("height", cellHeight)
        .attr("fill", step.highlights?.includes(index) ? "#ff7875" : "#f0f0f0")
        .attr("stroke", "#d9d9d9")
        .attr("stroke-width", 1);

      g.append("text")
        .attr("x", x + cellWidth / 2 - 1)
        .attr("y", startY + cellHeight / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("font-size", "14px")
        .attr("font-weight", "bold")
        .text(value);
    });

    // 绘制队头和队尾标识
    if (data.length > 0) {
      g.append("text")
        .attr("x", startX + cellWidth / 2 - 1)
        .attr("y", startY - 10)
        .attr("text-anchor", "middle")
        .attr("font-size", "12px")
        .attr("fill", "#1890ff")
        .text("队头");

      g.append("text")
        .attr("x", startX + (data.length - 1) * cellWidth + cellWidth / 2 - 1)
        .attr("y", startY - 10)
        .attr("text-anchor", "middle")
        .attr("font-size", "12px")
        .attr("fill", "#52c41a")
        .text("队尾");
    }
  };

  const renderTree = (g: any, step: VisualizationStep, width: number, height: number) => {
    const treeData = step.data;
    if (!treeData) return;

    const nodeRadius = 20;
    const levelHeight = 60;

    // 计算节点位置
    const calculatePositions = (node: any, level: number = 0, index: number = 0, levelWidth: number = 1): any => {
      if (!node) return null;

      const x = (index + 0.5) * (width / levelWidth);
      const y = 50 + level * levelHeight;

      const leftChild = node.left ? calculatePositions(node.left, level + 1, index * 2, levelWidth * 2) : null;
      const rightChild = node.right ? calculatePositions(node.right, level + 1, index * 2 + 1, levelWidth * 2) : null;

      return {
        ...node,
        x,
        y,
        left: leftChild,
        right: rightChild
      };
    };

    const positionedTree = calculatePositions(treeData);

    // 绘制连接线
    const drawConnections = (node: any) => {
      if (!node) return;

      if (node.left) {
        g.append("line")
          .attr("x1", node.x)
          .attr("y1", node.y)
          .attr("x2", node.left.x)
          .attr("y2", node.left.y)
          .attr("stroke", "#d9d9d9")
          .attr("stroke-width", 2);
        drawConnections(node.left);
      }

      if (node.right) {
        g.append("line")
          .attr("x1", node.x)
          .attr("y1", node.y)
          .attr("x2", node.right.x)
          .attr("y2", node.right.y)
          .attr("stroke", "#d9d9d9")
          .attr("stroke-width", 2);
        drawConnections(node.right);
      }
    };

    // 绘制节点
    const drawNodes = (node: any) => {
      if (!node) return;

      const isHighlighted = step.highlights?.includes(node.id);
      
      g.append("circle")
        .attr("cx", node.x)
        .attr("cy", node.y)
        .attr("r", nodeRadius)
        .attr("fill", isHighlighted ? "#ff7875" : "#f0f0f0")
        .attr("stroke", "#d9d9d9")
        .attr("stroke-width", 2);

      g.append("text")
        .attr("x", node.x)
        .attr("y", node.y)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("font-size", "12px")
        .attr("font-weight", "bold")
        .text(node.value);

      drawNodes(node.left);
      drawNodes(node.right);
    };

    drawConnections(positionedTree);
    drawNodes(positionedTree);
  };

  const renderGraph = (g: any, step: VisualizationStep, width: number, height: number) => {
    const { nodes = [], edges = [] } = step.data || {};
    if (nodes.length === 0) return;

    const nodeRadius = 25;
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(edges).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .stop();

    // 运行模拟
    for (let i = 0; i < 300; ++i) simulation.tick();

    // 绘制边
    edges.forEach((edge: any) => {
      const source = nodes.find((n: any) => n.id === edge.from);
      const target = nodes.find((n: any) => n.id === edge.to);
      
      if (source && target) {
        g.append("line")
          .attr("x1", source.x)
          .attr("y1", source.y)
          .attr("x2", target.x)
          .attr("y2", target.y)
          .attr("stroke", "#d9d9d9")
          .attr("stroke-width", 2);
      }
    });

    // 绘制节点
    nodes.forEach((node: any) => {
      const isHighlighted = step.highlights?.includes(node.id);
      const isVisited = step.visited?.includes(node.id);
      
      g.append("circle")
        .attr("cx", node.x)
        .attr("cy", node.y)
        .attr("r", nodeRadius)
        .attr("fill", isHighlighted ? "#ff7875" : isVisited ? "#95de64" : "#f0f0f0")
        .attr("stroke", "#d9d9d9")
        .attr("stroke-width", 2);

      g.append("text")
        .attr("x", node.x)
        .attr("y", node.y)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("font-size", "14px")
        .attr("font-weight", "bold")
        .text(node.value || node.id);
    });
  };

  return (
    <Card 
      title={`${step.description} (步骤 ${step.id + 1})`}
      size="small"
      style={{ minHeight: height + 100 }}
      bodyStyle={{ overflow: 'visible' }}
    >
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ border: '1px solid #f0f0f0', borderRadius: '4px' }}
      />
    </Card>
  );
};

export default UniversalDataVisualization;
