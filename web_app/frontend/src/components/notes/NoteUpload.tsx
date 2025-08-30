import React, { useState } from 'react';
import { Button, Input, Select, Switch, message, Card, Space } from 'antd';
import { FilterOutlined } from '@ant-design/icons';

const { TextArea } = Input;
const { Option } = Select;

interface NoteUploadProps {
  onUploadSuccess?: (noteId: string) => void;
  onCancel?: () => void;
}

const NoteUpload: React.FC<NoteUploadProps> = ({ onUploadSuccess, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [uploadMethod, setUploadMethod] = useState<'text' | 'file'>('text');

  // 表单状态
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    note_type: 'algorithm',
    file_format: 'txt',
    tags: [] as string[],
    is_public: false,
    extract_entities: true,
    content: '',
    file: null as File | null
  });

  const handleSubmit = async () => {
    if (!formData.title.trim()) {
      message.error('请输入笔记标题');
      return;
    }

    if (uploadMethod === 'text' && !formData.content.trim()) {
      message.error('请输入笔记内容');
      return;
    }

    if (uploadMethod === 'file' && !formData.file) {
      message.error('请选择要上传的文件');
      return;
    }

    setLoading(true);
    try {
      const submitData = new FormData();

      // 基本信息
      submitData.append('title', formData.title);
      submitData.append('description', formData.description || '');
      submitData.append('note_type', formData.note_type);
      submitData.append('file_format', formData.file_format);
      submitData.append('tags', JSON.stringify(formData.tags || []));
      submitData.append('is_public', formData.is_public ? 'true' : 'false');
      submitData.append('extract_entities', formData.extract_entities ? 'true' : 'false');

      // 内容
      if (uploadMethod === 'text') {
        submitData.append('file_content', formData.content);
      } else if (formData.file) {
        submitData.append('file', formData.file);
      }
      
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/notes/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: submitData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '上传失败');
      }

      const result = await response.json();
      message.success('笔记上传成功！');

      if (onUploadSuccess) {
        onUploadSuccess(result.id);
      }

      // 重置表单
      setFormData({
        title: '',
        description: '',
        note_type: 'algorithm',
        file_format: 'txt',
        tags: [],
        is_public: false,
        extract_entities: true,
        content: '',
        file: null
      });
      
    } catch (error: any) {
      console.error('上传失败:', error);
      message.error(error.message || '上传失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const noteTypes = [
    { value: 'algorithm', label: '算法笔记' },
    { value: 'data_structure', label: '数据结构笔记' },
    { value: 'problem_solving', label: '题解笔记' },
    { value: 'theory', label: '理论笔记' },
    { value: 'general', label: '通用笔记' },
  ];

  const fileFormats = [
    { value: 'txt', label: '纯文本' },
    { value: 'md', label: 'Markdown' },
    { value: 'pdf', label: 'PDF' },
    { value: 'docx', label: 'Word文档' },
  ];

  const handleInputChange = (field: string, value: any) => {
    console.log('表单字段更新:', field, value);
    setFormData(prev => {
      const newData = { ...prev, [field]: value };
      console.log('新的表单数据:', newData);
      return newData;
    });
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    setFormData(prev => ({ ...prev, file }));
  };

  return (
    <Card title="上传笔记" style={{ maxWidth: 800, margin: '0 auto' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

        {/* 测试Select组件 */}
        <div style={{ padding: '8px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
          <div style={{ marginBottom: '8px', fontSize: '12px', color: '#666' }}>
            🔧 测试Select组件（如果这个能正常工作，说明其他Select也应该能工作）:
          </div>
          <Select
            placeholder="测试选择框"
            style={{ width: 200 }}
            onChange={(value) => console.log('测试选择:', value)}
            getPopupContainer={(trigger) => trigger.parentElement || document.body}
            dropdownStyle={{ zIndex: 9999 }}
          >
            <Option value="test1">测试选项1</Option>
            <Option value="test2">测试选项2</Option>
            <Option value="test3">测试选项3</Option>
          </Select>
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
            笔记标题 *
          </label>
          <Input
            placeholder="请输入笔记标题"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
            笔记描述
          </label>
          <Input.TextArea
            rows={2}
            placeholder="请输入笔记描述（可选）"
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
          />
        </div>

        <Space size="large" style={{ width: '100%' }}>
          <div style={{ minWidth: 150 }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              笔记类型
            </label>
            <Select
              key="note_type"
              value={formData.note_type}
              onChange={(value) => handleInputChange('note_type', value)}
              style={{ width: '100%' }}
              placeholder="选择笔记类型"
              getPopupContainer={(trigger) => trigger.parentElement || document.body}
              dropdownStyle={{ zIndex: 9999 }}
            >
              {noteTypes.map(type => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </div>

          <div style={{ minWidth: 120 }}>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              文件格式
            </label>
            <Select
              key="file_format"
              value={formData.file_format}
              onChange={(value) => handleInputChange('file_format', value)}
              style={{ width: '100%' }}
              placeholder="选择文件格式"
              getPopupContainer={(trigger) => trigger.parentElement || document.body}
              dropdownStyle={{ zIndex: 9999 }}
            >
              {fileFormats.map(format => (
                <Option key={format.value} value={format.value}>
                  {format.label}
                </Option>
              ))}
            </Select>
          </div>
        </Space>

        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
            标签
          </label>
          <Select
            key="tags"
            mode="tags"
            placeholder="输入标签，按回车添加"
            style={{ width: '100%' }}
            value={formData.tags}
            onChange={(value) => handleInputChange('tags', value)}
            getPopupContainer={(trigger) => trigger.parentElement || document.body}
            dropdownStyle={{ zIndex: 9999 }}
          />
        </div>

        <Space size="large" style={{ width: '100%' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              公开笔记
            </label>
            <Switch
              checked={formData.is_public}
              onChange={(checked) => handleInputChange('is_public', checked)}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              抽取实体
            </label>
            <Switch
              checked={formData.extract_entities}
              onChange={(checked) => handleInputChange('extract_entities', checked)}
            />
          </div>
        </Space>

        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
            上传方式
          </label>
          <Select
            value={uploadMethod}
            onChange={setUploadMethod}
            style={{ width: 200 }}
            getPopupContainer={(trigger) => trigger.parentElement || document.body}
            dropdownStyle={{ zIndex: 9999 }}
          >
            <Option value="text">直接输入文本</Option>
            <Option value="file">上传文件</Option>
          </Select>
        </div>

        {uploadMethod === 'text' ? (
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              笔记内容 *
            </label>
            <Input.TextArea
              rows={12}
              placeholder="请输入笔记内容..."
              style={{ fontFamily: 'monospace' }}
              value={formData.content}
              onChange={(e) => handleInputChange('content', e.target.value)}
            />
          </div>
        ) : (
          <div>
            <label style={{ display: 'block', marginBottom: '4px', fontWeight: 'bold' }}>
              选择文件 *
            </label>
            <input
              type="file"
              accept=".txt,.md,.pdf,.docx,.doc"
              onChange={handleFileChange}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d9d9d9',
                borderRadius: '6px'
              }}
            />
            {formData.file && (
              <div style={{ marginTop: '8px', color: '#666' }}>
                已选择文件: {formData.file.name}
              </div>
            )}
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <Space>
            <Button
              onClick={() => {
                setFormData({
                  title: '',
                  description: '',
                  note_type: 'algorithm',
                  file_format: 'txt',
                  tags: [],
                  is_public: false,
                  extract_entities: true,
                  content: '',
                  file: null
                });
                console.log('表单已重置');
              }}
            >
              重置表单
            </Button>
            <Button
              type="primary"
              loading={loading}
              icon={<FilterOutlined />}
              onClick={handleSubmit}
            >
              上传笔记
            </Button>
            {onCancel && (
              <Button onClick={onCancel}>
                取消
              </Button>
            )}
          </Space>
        </div>
      </div>
    </Card>
  );
};

export default NoteUpload;
