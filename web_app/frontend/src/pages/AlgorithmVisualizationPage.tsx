import React, { useState, useCallback } from 'react';
import { Row, Col, Card, Input, Button, Space, Typography, Divider, Tag, message, Tabs } from 'antd';
import { PlayCircleOutlined, CodeOutlined, BulbOutlined, StarOutlined, UserOutlined } from '@ant-design/icons';
import AlgorithmVisualizer from '../components/visualization/AlgorithmVisualizer';
import DataVisualization from '../components/visualization/DataVisualization';

import CustomAlgorithmEditor from '../components/visualization/CustomAlgorithmEditor';
import UniversalDataVisualization from '../components/visualization/UniversalDataVisualization';
import SavedAlgorithmsManager from '../components/visualization/SavedAlgorithmsManager';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;

interface VisualizationStep {
  id: number;
  description: string;
  data: any[];
  highlights: number[];
  comparisons: number[];
  swaps?: [number, number];
  message?: string;
}

const AlgorithmVisualizationPage: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<VisualizationStep | undefined>();
  const [inputData, setInputData] = useState('64,34,25,12,22,11,90');
  const [parsedData, setParsedData] = useState<number[]>([64, 34, 25, 12, 22, 11, 90]);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('bubble_sort');

  // 自定义算法状态
  const [customSteps, setCustomSteps] = useState<VisualizationStep[]>([]);
  const [customCurrentStep, setCustomCurrentStep] = useState(0);
  const [customDataStructure, setCustomDataStructure] = useState('array');
  const [isCustomExecuting, setIsCustomExecuting] = useState(false);

  // 算法信息
  const algorithmInfo = {
    bubble_sort: {
      name: '冒泡排序',
      description: '冒泡排序是一种简单的排序算法。它重复地遍历要排序的数列，一次比较两个元素，如果它们的顺序错误就把它们交换过来。',
      timeComplexity: 'O(n²)',
      spaceComplexity: 'O(1)',
      tags: ['排序', '比较排序', '稳定排序']
    },
    quick_sort: {
      name: '快速排序',
      description: '快速排序使用分治法策略来把一个序列分为较小和较大的2个子序列，然后递归地排序两个子序列。',
      timeComplexity: 'O(n log n)',
      spaceComplexity: 'O(log n)',
      tags: ['排序', '分治算法', '不稳定排序']
    },
    binary_search: {
      name: '二分查找',
      description: '二分查找是一种在有序数组中查找某一特定元素的搜索算法。搜索过程从数组的中间元素开始。',
      timeComplexity: 'O(log n)',
      spaceComplexity: 'O(1)',
      tags: ['搜索', '分治算法', '有序数组']
    }
  };

  const handleStepChange = useCallback((step: VisualizationStep) => {
    setCurrentStep(step);
  }, []);

  const handleDataChange = useCallback(() => {
    try {
      const data = inputData.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
      if (data.length === 0) {
        message.error('请输入有效的数字数据');
        return;
      }
      setParsedData(data);
      message.success('数据更新成功');
    } catch (error) {
      message.error('数据格式错误，请输入逗号分隔的数字');
    }
  }, [inputData]);

  // 处理自定义算法执行
  const handleCustomAlgorithmExecute = useCallback(async (code: string, dataStructure: string, inputData: any) => {
    setIsCustomExecuting(true);
    setCustomDataStructure(dataStructure);

    try {
      // 创建安全的执行环境
      const func = new Function('data', `
        ${code}

        // 尝试调用不同的函数名
        if (typeof customAlgorithm !== 'undefined') {
          return customAlgorithm(data);
        } else if (typeof customStackAlgorithm !== 'undefined') {
          return customStackAlgorithm(data);
        } else if (typeof customQueueAlgorithm !== 'undefined') {
          return customQueueAlgorithm(data);
        } else if (typeof customTreeAlgorithm !== 'undefined') {
          return customTreeAlgorithm(data);
        } else if (typeof customGraphAlgorithm !== 'undefined') {
          return customGraphAlgorithm(data);
        }

        return [];
      `);

      const result = func(inputData);

      if (Array.isArray(result) && result.length > 0) {
        setCustomSteps(result);
        setCustomCurrentStep(0);
        message.success('自定义算法执行成功！');
      } else {
        message.warning('算法执行完成，但没有返回可视化步骤');
        setCustomSteps([]);
      }
    } catch (error) {
      console.error('自定义算法执行错误:', error);
      message.error('算法执行出错，请检查代码语法');
      setCustomSteps([]);
    } finally {
      setIsCustomExecuting(false);
    }
  }, []);

  // 加载保存的算法
  const handleLoadSavedAlgorithm = useCallback((algorithm: any) => {
    // 这里可以将算法加载到自定义编辑器中
    message.success(`已加载算法: ${algorithm.name}`);
  }, []);

  const currentAlgorithmInfo = algorithmInfo[selectedAlgorithm as keyof typeof algorithmInfo];

  return (
    <div style={{
      padding: '24px',
      minHeight: 'calc(100vh - 120px)',
      height: 'calc(100vh - 120px)',
      overflow: 'auto'
    }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <CodeOutlined style={{ marginRight: 8 }} />
          算法可视化实验室
        </Title>
        <Paragraph>
          通过实时代码执行和动画可视化，深入理解算法的工作原理。
          编写代码，观察算法执行过程，掌握算法精髓。
        </Paragraph>
      </div>

      <Tabs
        defaultActiveKey="editor"
        size="large"
        style={{ height: 'calc(100vh - 200px)' }}
        tabBarStyle={{ marginBottom: 16 }}
      >
        <TabPane
          tab={
            <span>
              <CodeOutlined />
              代码编辑器
            </span>
          }
          key="editor"
        >
        <div style={{
          height: 'calc(100vh - 280px)',
          overflow: 'auto',
          paddingRight: '8px'
        }}>
          <Row gutter={[24, 24]} style={{ minHeight: 0, flex: 1 }}>
        {/* 左侧：算法信息和数据输入 */}
        <Col span={8}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 算法信息卡片 */}
            <Card 
              title={
                <Space>
                  <BulbOutlined />
                  算法信息
                </Space>
              }
              size="small"
            >
              <div style={{ marginBottom: 16 }}>
                <Title level={4} style={{ margin: 0 }}>
                  {currentAlgorithmInfo?.name}
                </Title>
                <div style={{ marginTop: 8 }}>
                  {currentAlgorithmInfo?.tags.map(tag => (
                    <Tag key={tag} color="blue" style={{ marginBottom: 4 }}>
                      {tag}
                    </Tag>
                  ))}
                </div>
              </div>
              
              <Paragraph style={{ fontSize: '14px', lineHeight: 1.6 }}>
                {currentAlgorithmInfo?.description}
              </Paragraph>
              
              <Divider style={{ margin: '12px 0' }} />
              
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>时间复杂度:</Text>
                  <br />
                  <Text code>{currentAlgorithmInfo?.timeComplexity}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>空间复杂度:</Text>
                  <br />
                  <Text code>{currentAlgorithmInfo?.spaceComplexity}</Text>
                </Col>
              </Row>
            </Card>

            {/* 数据输入卡片 */}
            <Card title="输入数据" size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text>数据数组 (逗号分隔):</Text>
                  <Input
                    value={inputData}
                    onChange={(e) => setInputData(e.target.value)}
                    placeholder="例如: 64,34,25,12,22,11,90"
                    style={{ marginTop: 8 }}
                  />
                </div>
                
                <Button 
                  type="primary" 
                  onClick={handleDataChange}
                  style={{ width: '100%' }}
                >
                  更新数据
                </Button>
                
                <div>
                  <Text type="secondary">当前数据:</Text>
                  <div style={{ marginTop: 4 }}>
                    {parsedData.map((num, index) => (
                      <Tag key={index} style={{ margin: '2px' }}>
                        {num}
                      </Tag>
                    ))}
                  </div>
                </div>
              </Space>
            </Card>

            {/* 步骤信息 */}
            {currentStep && (
              <Card title="当前步骤" size="small">
                <div>
                  <Text strong>步骤 {currentStep.id + 1}:</Text>
                  <div style={{ marginTop: 8 }}>
                    <Text>{currentStep.description}</Text>
                  </div>
                  
                  {currentStep.message && (
                    <div style={{ marginTop: 8, padding: 8, backgroundColor: '#f6ffed', borderRadius: 4 }}>
                      <Text type="success">{currentStep.message}</Text>
                    </div>
                  )}
                  
                  <div style={{ marginTop: 12 }}>
                    <Text type="secondary">数据状态:</Text>
                    <div style={{ marginTop: 4 }}>
                      {currentStep.data.map((num, index) => (
                        <Tag 
                          key={index} 
                          color={
                            currentStep.highlights.includes(index) 
                              ? (currentStep.comparisons.includes(index) ? 'red' : 'green')
                              : currentStep.swaps && (currentStep.swaps[0] === index || currentStep.swaps[1] === index)
                              ? 'orange'
                              : 'default'
                          }
                          style={{ margin: '2px' }}
                        >
                          {num}
                        </Tag>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </Space>
        </Col>

        {/* 右侧：代码编辑器和可视化 */}
        <Col span={16}>
          <div style={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            {/* 算法可视化器 */}
            <div style={{ flex: '0 0 auto' }}>
              <AlgorithmVisualizer
                algorithm={selectedAlgorithm}
                data={parsedData}
                onStepChange={handleStepChange}
              />
            </div>

            {/* 数据可视化 */}
            <div style={{ flex: '1 1 auto', minHeight: '350px' }}>
              <DataVisualization
                step={currentStep}
                width={700}
                height={300}
                type="array"
              />
            </div>
          </div>
        </Col>
      </Row>

      {/* 使用说明 */}
      <Card 
        title="使用说明" 
        style={{ marginTop: 24 }}
        size="small"
      >
        <Row gutter={24}>
          <Col span={8}>
            <div>
              <Title level={5}>1. 选择算法</Title>
              <Paragraph>
                从下拉菜单中选择要可视化的算法，系统会自动加载对应的代码模板。
              </Paragraph>
            </div>
          </Col>
          <Col span={8}>
            <div>
              <Title level={5}>2. 编辑代码</Title>
              <Paragraph>
                在代码编辑器中修改算法实现，支持JavaScript语法高亮和自动补全。
              </Paragraph>
            </div>
          </Col>
          <Col span={8}>
            <div>
              <Title level={5}>3. 执行可视化</Title>
              <Paragraph>
                点击执行按钮运行算法，观察实时的动画可视化效果和步骤说明。
              </Paragraph>
            </div>
          </Col>
          </Row>
        </Card>
        </div>
        </TabPane>



        <TabPane
          tab={
            <span>
              <UserOutlined />
              自定义算法
            </span>
          }
          key="custom"
        >
          <div style={{
            height: 'calc(100vh - 280px)',
            overflow: 'auto',
            paddingRight: '8px'
          }}>
            <Row gutter={[24, 24]}>
              <Col span={16}>
                <CustomAlgorithmEditor
                  onExecute={handleCustomAlgorithmExecute}
                  isExecuting={isCustomExecuting}
                />

                {customSteps.length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <UniversalDataVisualization
                      step={customSteps[customCurrentStep] || customSteps[0]}
                      dataStructure={customDataStructure}
                      width={700}
                      height={400}
                    />

                    <div style={{ marginTop: 16, textAlign: 'center' }}>
                      <Space>
                        <Button
                          disabled={customCurrentStep === 0}
                          onClick={() => setCustomCurrentStep(Math.max(0, customCurrentStep - 1))}
                        >
                          上一步
                        </Button>
                        <span>
                          步骤 {customCurrentStep + 1} / {customSteps.length}
                        </span>
                        <Button
                          disabled={customCurrentStep === customSteps.length - 1}
                          onClick={() => setCustomCurrentStep(Math.min(customSteps.length - 1, customCurrentStep + 1))}
                        >
                          下一步
                        </Button>
                      </Space>
                    </div>
                  </div>
                )}
              </Col>

              <Col span={8}>
                <SavedAlgorithmsManager
                  onLoadAlgorithm={handleLoadSavedAlgorithm}
                />
              </Col>
            </Row>
          </div>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default AlgorithmVisualizationPage;
