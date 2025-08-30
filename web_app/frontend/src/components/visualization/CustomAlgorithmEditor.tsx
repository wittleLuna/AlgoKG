import React, { useState, useCallback } from 'react';
import { Card, Input, Button, Select, Space, Typography, message, Row, Col, Divider } from 'antd';
import { PlayCircleOutlined, UserOutlined, CodeOutlined, BulbOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;

interface CustomAlgorithmEditorProps {
  onExecute: (code: string, dataStructure: string, inputData: any) => void;
  isExecuting?: boolean;
}

const CustomAlgorithmEditor: React.FC<CustomAlgorithmEditorProps> = ({
  onExecute,
  isExecuting = false
}) => {
  const [code, setCode] = useState('');
  const [dataStructure, setDataStructure] = useState('array');
  const [inputData, setInputData] = useState('');
  const [algorithmName, setAlgorithmName] = useState('');
  const [description, setDescription] = useState('');

  // 数据结构模板
  const dataStructureTemplates = {
    array: {
      name: '数组',
      template: `function customAlgorithm(arr) {
  const steps = [];
  const n = arr.length;
  let data = [...arr];
  
  // 添加初始步骤
  steps.push({
    id: 0,
    description: "开始处理数组",
    data: [...data],
    highlights: [],
    comparisons: []
  });
  
  // 在这里实现你的算法逻辑
  for (let i = 0; i < n; i++) {
    steps.push({
      id: steps.length,
      description: \`处理索引 \${i}: \${data[i]}\`,
      data: [...data],
      highlights: [i],
      comparisons: []
    });
  }
  
  return steps;
}`,
      defaultData: '[64, 34, 25, 12, 22, 11, 90]',
      description: '适用于排序、搜索等数组操作算法'
    },
    stack: {
      name: '栈',
      template: `function customStackAlgorithm(operations) {
  const steps = [];
  const stack = [];
  
  steps.push({
    id: 0,
    description: "初始化空栈",
    data: [...stack],
    highlights: [],
    operation: 'init'
  });
  
  operations.forEach((op, index) => {
    if (op.type === 'push') {
      stack.push(op.value);
      steps.push({
        id: steps.length,
        description: \`入栈: \${op.value}\`,
        data: [...stack],
        highlights: [stack.length - 1],
        operation: 'push'
      });
    } else if (op.type === 'pop') {
      const popped = stack.pop();
      steps.push({
        id: steps.length,
        description: \`出栈: \${popped || 'empty'}\`,
        data: [...stack],
        highlights: [],
        operation: 'pop'
      });
    }
  });
  
  return steps;
}`,
      defaultData: '[{"type":"push","value":1},{"type":"push","value":2},{"type":"pop"},{"type":"push","value":3}]',
      description: '适用于栈相关算法，如括号匹配、表达式求值等'
    },
    queue: {
      name: '队列',
      template: `function customQueueAlgorithm(operations) {
  const steps = [];
  const queue = [];
  
  steps.push({
    id: 0,
    description: "初始化空队列",
    data: [...queue],
    highlights: [],
    operation: 'init'
  });
  
  operations.forEach((op, index) => {
    if (op.type === 'enqueue') {
      queue.push(op.value);
      steps.push({
        id: steps.length,
        description: \`入队: \${op.value}\`,
        data: [...queue],
        highlights: [queue.length - 1],
        operation: 'enqueue'
      });
    } else if (op.type === 'dequeue') {
      const dequeued = queue.shift();
      steps.push({
        id: steps.length,
        description: \`出队: \${dequeued || 'empty'}\`,
        data: [...queue],
        highlights: [],
        operation: 'dequeue'
      });
    }
  });
  
  return steps;
}`,
      defaultData: '[{"type":"enqueue","value":1},{"type":"enqueue","value":2},{"type":"dequeue"},{"type":"enqueue","value":3}]',
      description: '适用于队列相关算法，如BFS、任务调度等'
    },
    tree: {
      name: '二叉树',
      template: `function customTreeAlgorithm(treeData) {
  const steps = [];
  
  // 树的遍历示例
  function traverse(node, path = []) {
    if (!node) return;
    
    steps.push({
      id: steps.length,
      description: \`访问节点: \${node.value}\`,
      data: treeData,
      highlights: [node.id],
      path: [...path, node.id],
      operation: 'visit'
    });
    
    if (node.left) traverse(node.left, [...path, node.id]);
    if (node.right) traverse(node.right, [...path, node.id]);
  }
  
  steps.push({
    id: 0,
    description: "开始遍历二叉树",
    data: treeData,
    highlights: [],
    operation: 'init'
  });
  
  traverse(treeData);
  return steps;
}`,
      defaultData: '{"id":1,"value":10,"left":{"id":2,"value":5,"left":{"id":4,"value":3},"right":{"id":5,"value":7}},"right":{"id":3,"value":15,"left":{"id":6,"value":12},"right":{"id":7,"value":18}}}',
      description: '适用于二叉树相关算法，如遍历、搜索、平衡等'
    },
    graph: {
      name: '图',
      template: `function customGraphAlgorithm(graphData) {
  const steps = [];
  const { nodes, edges } = graphData;
  const visited = new Set();
  
  steps.push({
    id: 0,
    description: "开始图算法",
    data: graphData,
    highlights: [],
    visited: [],
    operation: 'init'
  });
  
  // DFS示例
  function dfs(nodeId) {
    if (visited.has(nodeId)) return;
    
    visited.add(nodeId);
    steps.push({
      id: steps.length,
      description: \`访问节点: \${nodeId}\`,
      data: graphData,
      highlights: [nodeId],
      visited: Array.from(visited),
      operation: 'visit'
    });
    
    // 访问邻接节点
    edges.filter(edge => edge.from === nodeId)
         .forEach(edge => dfs(edge.to));
  }
  
  if (nodes.length > 0) {
    dfs(nodes[0].id);
  }
  
  return steps;
}`,
      defaultData: '{"nodes":[{"id":"A","value":"A"},{"id":"B","value":"B"},{"id":"C","value":"C"},{"id":"D","value":"D"}],"edges":[{"from":"A","to":"B"},{"from":"A","to":"C"},{"from":"B","to":"D"},{"from":"C","to":"D"}]}',
      description: '适用于图相关算法，如DFS、BFS、最短路径等'
    }
  };

  const handleDataStructureChange = useCallback((value: string) => {
    setDataStructure(value);
    const template = dataStructureTemplates[value as keyof typeof dataStructureTemplates];
    setCode(template.template);
    setInputData(template.defaultData);
  }, []);

  const handleExecute = useCallback(() => {
    if (!code.trim()) {
      message.error('请输入算法代码');
      return;
    }

    if (!inputData.trim()) {
      message.error('请输入测试数据');
      return;
    }

    try {
      // 验证输入数据格式
      const parsedData = JSON.parse(inputData);
      onExecute(code, dataStructure, parsedData);
    } catch (error) {
      message.error('输入数据格式错误，请检查JSON格式');
    }
  }, [code, dataStructure, inputData, onExecute]);

  const handleSaveTemplate = useCallback(() => {
    if (!algorithmName.trim()) {
      message.error('请输入算法名称');
      return;
    }

    // 保存到本地存储
    const savedAlgorithms = JSON.parse(localStorage.getItem('customAlgorithms') || '[]');
    const newAlgorithm = {
      id: Date.now().toString(),
      name: algorithmName,
      description,
      dataStructure,
      code,
      inputData,
      createdAt: new Date().toISOString()
    };

    savedAlgorithms.push(newAlgorithm);
    localStorage.setItem('customAlgorithms', JSON.stringify(savedAlgorithms));
    
    message.success('算法模板已保存');
    setAlgorithmName('');
    setDescription('');
  }, [algorithmName, description, dataStructure, code, inputData]);

  const currentTemplate = dataStructureTemplates[dataStructure as keyof typeof dataStructureTemplates];

  return (
    <Card title={
      <Space>
        <CodeOutlined />
        自定义算法编辑器
      </Space>
    }>
      <Row gutter={[24, 16]}>
        {/* 左侧：配置区域 */}
        <Col span={8}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <div>
              <Text strong>数据结构类型</Text>
              <Select
                value={dataStructure}
                onChange={handleDataStructureChange}
                style={{ width: '100%', marginTop: 8 }}
                placeholder="选择数据结构"
              >
                {Object.entries(dataStructureTemplates).map(([key, template]) => (
                  <Option key={key} value={key}>
                    {template.name}
                  </Option>
                ))}
              </Select>
              <Paragraph style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                {currentTemplate?.description}
              </Paragraph>
            </div>

            <div>
              <Text strong>测试数据</Text>
              <TextArea
                value={inputData}
                onChange={(e) => setInputData(e.target.value)}
                placeholder="输入JSON格式的测试数据"
                rows={4}
                style={{ marginTop: 8 }}
              />
            </div>

            <Divider />

            <div>
              <Text strong>保存为模板</Text>
              <Input
                value={algorithmName}
                onChange={(e) => setAlgorithmName(e.target.value)}
                placeholder="算法名称"
                style={{ marginTop: 8 }}
              />
              <TextArea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="算法描述"
                rows={2}
                style={{ marginTop: 8 }}
              />
              <Button
                icon={<UserOutlined />}
                onClick={handleSaveTemplate}
                style={{ marginTop: 8, width: '100%' }}
              >
                保存模板
              </Button>
            </div>
          </Space>
        </Col>

        {/* 右侧：代码编辑器 */}
        <Col span={16}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Text strong>算法代码</Text>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleExecute}
                loading={isExecuting}
              >
                执行算法
              </Button>
            </div>
            
            <TextArea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="在这里编写你的算法代码..."
              rows={20}
              style={{
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '13px'
              }}
            />
            
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                <BulbOutlined style={{ marginRight: 4 }} />
                提示：算法函数必须返回包含步骤信息的数组，每个步骤包含id、description、data等字段
              </Text>
            </div>
          </div>
        </Col>
      </Row>
    </Card>
  );
};

export default CustomAlgorithmEditor;
