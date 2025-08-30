import React, { useState, useEffect } from 'react';
import { Card, Button, Space, message, Spin, Divider, Tag } from 'antd';
import { LeftOutlined, NodeIndexOutlined, FilterOutlined } from '@ant-design/icons';
import EntityDetailPanel from './EntityDetailPanel';

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

interface Entity {
  id: string;
  name: string;
  type: string;
  description: string;
  confidence: number;
}

interface Relation {
  source: string;
  target: string;
  type: string;
  confidence: number;
}

interface EntityData {
  note_id: string;
  entities: Entity[];
  relations: Relation[];
  metadata: any;
  extracted: boolean;
}

interface NoteDetailProps {
  note: Note;
  onBack?: () => void;
  onEntityVisualize?: (note: Note) => void;
}

const NoteDetail: React.FC<NoteDetailProps> = ({ note, onBack, onEntityVisualize }) => {
  const [entityData, setEntityData] = useState<EntityData | null>(null);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);

  const fetchEntityData = async () => {
    if (!note.entities_extracted) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/notes/${note.id}/entities`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('获取实体数据失败');
      }

      const data = await response.json();
      setEntityData(data);
    } catch (error: any) {
      console.error('获取实体数据失败:', error);
      message.error(error.message || '获取实体数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntityData();
  }, [note.id]);

  const handleReExtractEntities = async () => {
    setExtracting(true);
    try {
      const token = localStorage.getItem('token');
      console.log('开始重新抽取实体，笔记ID:', note.id);

      const response = await fetch(`/api/v1/notes/${note.id}/extract-entities`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '重新抽取实体失败');
      }

      const result = await response.json();
      console.log('重新抽取实体结果:', result);
      message.success(`实体重新抽取成功！提取了 ${result.entity_count} 个实体，${result.relation_count} 个关系`);

      // 重新获取实体数据
      await fetchEntityData();
    } catch (error: any) {
      console.error('重新抽取实体失败:', error);
      message.error(error.message || '重新抽取实体失败');
    } finally {
      setExtracting(false);
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

  const getEntityTypeColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      'algorithm_paradigm': 'blue',
      'data_structure': 'green',
      'technique': 'orange',
      'problem_type': 'purple',
      'complexity': 'red',
      'default': 'default'
    };
    return colorMap[type] || colorMap.default;
  };

  const getEntityTypeLabel = (type: string) => {
    const labelMap: { [key: string]: string } = {
      'algorithm_paradigm': '算法范式',
      'data_structure': '数据结构',
      'technique': '算法技巧',
      'problem_type': '问题类型',
      'complexity': '复杂度',
    };
    return labelMap[type] || type;
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <Button
          icon={<LeftOutlined />}
          onClick={onBack}
          style={{ marginBottom: '16px' }}
        >
          返回列表
        </Button>
        
        <Card
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FilterOutlined />
              <span>{note.title}</span>
              <Tag color="blue">{getTypeLabel(note.note_type)}</Tag>
            </div>
          }
        >
          <div style={{ marginBottom: '16px' }}>
            <strong>描述：</strong>
            <div style={{ marginTop: '4px', color: '#666' }}>
              {note.description || '无描述'}
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <strong>标签：</strong>
            <div style={{ marginTop: '4px' }}>
              <Space wrap>
                {note.tags.map((tag, index) => (
                  <Tag key={index} color="cyan">{tag}</Tag>
                ))}
                {note.tags.length === 0 && <span style={{ color: '#999' }}>无标签</span>}
              </Space>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <Space>
              <span><strong>文件格式：</strong>{note.file_format.toUpperCase()}</span>
              <span><strong>创建时间：</strong>{formatDate(note.created_at)}</span>
              <span><strong>更新时间：</strong>{formatDate(note.updated_at)}</span>
            </Space>
          </div>

          <Divider />

          <div style={{ marginBottom: '16px' }}>
            <strong>笔记内容：</strong>
            <div style={{
              marginTop: '8px',
              padding: '12px',
              backgroundColor: '#f5f5f5',
              borderRadius: '6px',
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              maxHeight: '400px',
              overflow: 'auto'
            }}>
              {note.content}
            </div>
          </div>
        </Card>
      </div>

      {note.entities_extracted && (
        <Card
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <NodeIndexOutlined />
                <span>提取的实体信息</span>
                {entityData && (
                  <Tag color="green">
                    {entityData.entities.length} 个实体，{entityData.relations.length} 个关系
                  </Tag>
                )}
              </div>
              <Space>
                <Button
                  type="primary"
                  size="small"
                  loading={extracting}
                  onClick={handleReExtractEntities}
                >
                  重新抽取
                </Button>
                <Button
                  size="small"
                  icon={<NodeIndexOutlined />}
                  onClick={() => {
                    if (onEntityVisualize) {
                      onEntityVisualize(note);
                    } else {
                      message.info('图谱可视化功能暂不可用');
                    }
                  }}
                >
                  图谱可视化
                </Button>
              </Space>
            </div>
          }
        >
          <Spin spinning={loading}>
            {entityData ? (
              <div>
                {entityData.entities.length > 0 ? (
                  <EntityDetailPanel
                    entities={entityData.entities}
                    relations={entityData.relations}
                    entityDetails={[]} // 这里可以传入更详细的实体信息
                    noteId={note.id}
                  />
                ) : (
                  <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                    未提取到实体信息
                  </div>
                )}

                {entityData.metadata && (
                  <div style={{ marginTop: '16px' }}>
                    <strong>提取信息：</strong>
                    <div style={{
                      marginTop: '8px',
                      padding: '8px',
                      backgroundColor: '#f0f0f0',
                      borderRadius: '4px',
                      fontSize: '12px',
                      color: '#666'
                    }}>
                      <div>提取方法: {entityData.metadata.method || '未知'}</div>
                      {entityData.metadata.title && (
                        <div>识别标题: {entityData.metadata.title}</div>
                      )}
                      {entityData.metadata.solution_approach && (
                        <div>解题思路: {entityData.metadata.solution_approach}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
                {note.entities_extracted ? '加载实体信息中...' : '未进行实体提取'}
              </div>
            )}
          </Spin>
        </Card>
      )}

      {!note.entities_extracted && (
        <Card title="实体提取">
          <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
            该笔记未进行实体提取
          </div>
        </Card>
      )}


    </div>
  );
};

export default NoteDetail;
