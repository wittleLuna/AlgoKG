import React, { useState, useEffect } from 'react';
import { Card, Button, Space, message, Input, Select, Spin, Empty } from 'antd';
import { FilterOutlined, EyeOutlined, LeftOutlined, SearchOutlined, UserOutlined, NodeIndexOutlined } from '@ant-design/icons';

const { Search } = Input;
const { Option } = Select;

interface Note {
  id: string;
  title: string;
  content: string;
  note_type: string;
  file_format: string;
  tags: string[];
  description: string;
  is_public: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  entities_extracted: boolean;
  entity_count: number;
}

interface NoteListProps {
  onNoteSelect?: (note: Note) => void;
  onNoteDelete?: (noteId: string) => void;
  onUploadClick?: () => void;
  onEntityVisualize?: (note: Note) => void;
}

const NoteList: React.FC<NoteListProps> = ({ onNoteSelect, onNoteDelete, onUploadClick, onEntityVisualize }) => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [noteTypeFilter, setNoteTypeFilter] = useState<string>('');
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
    total: 0
  });

  const noteTypes = [
    { value: '', label: '全部类型' },
    { value: 'algorithm', label: '算法笔记' },
    { value: 'data_structure', label: '数据结构笔记' },
    { value: 'problem_solving', label: '题解笔记' },
    { value: 'theory', label: '理论笔记' },
    { value: 'general', label: '通用笔记' },
  ];

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        message.error('请先登录');
        return;
      }

      const params = new URLSearchParams({
        page: pagination.page.toString(),
        size: pagination.size.toString(),
      });

      if (searchQuery) {
        params.append('search_query', searchQuery);
      }
      if (noteTypeFilter) {
        params.append('note_type', noteTypeFilter);
      }

      const response = await fetch(`/api/v1/notes/list?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '获取笔记列表失败');
      }

      const data = await response.json();
      setNotes(data.notes);
      setPagination(prev => ({
        ...prev,
        total: data.total
      }));

    } catch (error: any) {
      console.error('获取笔记列表失败:', error);
      message.error(error.message || '获取笔记列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, [pagination.page, pagination.size, searchQuery, noteTypeFilter]);

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleTypeFilter = (value: string) => {
    setNoteTypeFilter(value);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleDelete = async (noteId: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/notes/${noteId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('删除失败');
      }

      message.success('笔记删除成功');
      fetchNotes();
      
      if (onNoteDelete) {
        onNoteDelete(noteId);
      }
    } catch (error: any) {
      message.error(error.message || '删除失败');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getTypeLabel = (type: string) => {
    const typeMap: { [key: string]: string } = {
      'algorithm': '算法',
      'data_structure': '数据结构',
      'problem_solving': '题解',
      'theory': '理论',
      'general': '通用'
    };
    return typeMap[type] || type;
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>我的笔记</h2>
          <Button
            type="primary"
            icon={<UserOutlined />}
            onClick={onUploadClick}
          >
            上传笔记
          </Button>
        </div>

        <Space size="middle" style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Search
              placeholder="搜索笔记标题或内容"
              allowClear
              onSearch={handleSearch}
              style={{ width: 300 }}
              enterButton={<SearchOutlined />}
            />
            <Select
              value={noteTypeFilter}
              onChange={handleTypeFilter}
              style={{ width: 150 }}
            >
              {noteTypes.map(type => (
                <Option key={type.value} value={type.value}>
                  {type.label}
                </Option>
              ))}
            </Select>
          </Space>
          <div>
            共 {pagination.total} 条笔记
          </div>
        </Space>
      </div>

      <Spin spinning={loading}>
        {notes.length === 0 ? (
          <Empty
            description="暂无笔记"
            style={{ margin: '40px 0' }}
          />
        ) : (
          <div style={{ display: 'grid', gap: '16px' }}>
            {notes.map((note) => (
              <Card
                key={note.id}
                size="small"
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FilterOutlined />
                    <span>{note.title}</span>
                    <span style={{
                      fontSize: '12px',
                      color: '#666',
                      backgroundColor: '#f0f0f0',
                      padding: '2px 6px',
                      borderRadius: '4px'
                    }}>
                      {getTypeLabel(note.note_type)}
                    </span>
                  </div>
                }
                extra={
                  <Space>
                    <Button
                      type="text"
                      icon={<EyeOutlined />}
                      onClick={() => {
                        console.log('点击查看笔记:', note);
                        if (onNoteSelect) {
                          onNoteSelect(note);
                        } else {
                          message.warning('查看功能暂不可用');
                        }
                      }}
                    >
                      查看详情
                    </Button>
                    {note.entities_extracted && (
                      <Button
                        type="text"
                        icon={<NodeIndexOutlined />}
                        onClick={() => {
                          console.log('点击实体可视化:', note);
                          if (onEntityVisualize) {
                            onEntityVisualize(note);
                          } else if (onNoteSelect) {
                            onNoteSelect(note);
                          } else {
                            message.warning('实体可视化功能暂不可用');
                          }
                        }}
                        style={{ color: '#1890ff' }}
                      >
                        实体图谱
                      </Button>
                    )}
                    <Button
                      type="text"
                      danger
                      icon={<LeftOutlined />}
                      onClick={() => handleDelete(note.id)}
                    >
                      删除
                    </Button>
                  </Space>
                }
              >
                <div style={{ marginBottom: '8px' }}>
                  <div style={{ color: '#666', fontSize: '14px' }}>
                    {note.description || '无描述'}
                  </div>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space size="small">
                    {note.tags.map((tag, index) => (
                      <span
                        key={index}
                        style={{
                          backgroundColor: '#e6f7ff',
                          color: '#1890ff',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}
                      >
                        {tag}
                      </span>
                    ))}
                  </Space>
                  
                  <Space size="small" style={{ fontSize: '12px', color: '#999' }}>
                    {note.entities_extracted ? (
                      <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
                        ✅ 已提取 {note.entity_count || 0} 个实体
                      </span>
                    ) : (
                      <span style={{ color: '#faad14' }}>
                        ⏳ 未提取实体
                      </span>
                    )}
                    <span>{formatDate(note.created_at)}</span>
                  </Space>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Spin>

      {notes.length > 0 && (
        <div style={{ textAlign: 'center', marginTop: '20px' }}>
          <Space>
            <Button
              disabled={pagination.page <= 1}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            >
              上一页
            </Button>
            <span>
              第 {pagination.page} 页，共 {Math.ceil(pagination.total / pagination.size)} 页
            </span>
            <Button
              disabled={pagination.page >= Math.ceil(pagination.total / pagination.size)}
              onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            >
              下一页
            </Button>
          </Space>
        </div>
      )}
    </div>
  );
};

export default NoteList;
