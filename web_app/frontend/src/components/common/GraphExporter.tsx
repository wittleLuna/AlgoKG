import React, { useState } from 'react';
import { Button, Select, Space, Typography, message } from 'antd';
import { DownloadOutlined, FilterOutlined, SendOutlined, UserOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { Option } = Select;

interface GraphExporterProps {
  graphData: any;
  graphRef?: React.RefObject<any>;
  visible: boolean;
  onClose: () => void;
}

type ExportFormat = 'png' | 'jpg' | 'svg' | 'pdf' | 'json';
type ExportQuality = 1 | 2 | 3 | 4;

const GraphExporter: React.FC<GraphExporterProps> = ({
  graphData,
  graphRef,
  visible,
  onClose
}) => {
  const [format, setFormat] = useState<ExportFormat>('json');
  const [exporting, setExporting] = useState(false);



  // 导出为JSON
  const exportAsJSON = () => {
    try {
      const exportData = {
        timestamp: new Date().toISOString(),
        version: '1.0',
        data: graphData
      };

      const jsonString = JSON.stringify(exportData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `knowledge-graph-${Date.now()}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      message.success('JSON导出成功');
    } catch (error) {
      console.error('JSON export error:', error);
      message.error('JSON导出失败');
    }
  };



  // 执行导出
  const handleExport = async () => {
    setExporting(true);

    try {
      exportAsJSON();
    } catch (error) {
      console.error('Export failed:', error);
      message.error('导出失败');
    } finally {
      setExporting(false);
    }
  };

  if (!visible) return null;

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      background: 'white',
      padding: 24,
      borderRadius: 8,
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      zIndex: 1000,
      minWidth: 300
    }}>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <DownloadOutlined />
          <Text strong>导出知识图谱</Text>
        </Space>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Text>将图谱数据导出为JSON格式</Text>
      </div>

      <div style={{ textAlign: 'right' }}>
        <Space>
          <Button onClick={onClose}>
            取消
          </Button>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            loading={exporting}
            onClick={handleExport}
          >
            导出JSON
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default GraphExporter;
