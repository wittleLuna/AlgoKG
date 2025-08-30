import React, { useState, useEffect } from 'react';
import { Card, Tag, Space, Button, Collapse, message, Spin } from 'antd';
import { NodeIndexOutlined, LinkOutlined, BulbOutlined } from '@ant-design/icons';

const { Panel } = Collapse;

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

interface EntityDetail {
  entity: Entity;
  graph_status: string;
  related_concepts: string[];
  integration_path: string[];
}

interface EntityDetailPanelProps {
  entities: Entity[];
  relations: Relation[];
  entityDetails: EntityDetail[];
  noteId: string;
}

const EntityDetailPanel: React.FC<EntityDetailPanelProps> = ({
  entities,
  relations,
  entityDetails,
  noteId
}) => {
  const [expandedEntities, setExpandedEntities] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

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

  const getStatusColor = (status: string) => {
    const colors = {
      'new': 'green',
      'enhanced': 'blue',
      'existing': 'orange'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts = {
      'new': '新增实体',
      'enhanced': '增强实体',
      'existing': '已存在'
    };
    return texts[status as keyof typeof texts] || status;
  };

  const getRelatedRelations = (entityId: string) => {
    return relations.filter(rel => rel.source === entityId || rel.target === entityId);
  };

  const getEntityDetail = (entityId: string) => {
    return entityDetails.find(detail => detail.entity.id === entityId);
  };

  const handleEntityExpand = (entityId: string) => {
    setExpandedEntities(prev => 
      prev.includes(entityId) 
        ? prev.filter(id => id !== entityId)
        : [...prev, entityId]
    );
  };

  const renderEntityCard = (entity: Entity) => {
    const detail = getEntityDetail(entity.id);
    const relatedRelations = getRelatedRelations(entity.id);
    const isExpanded = expandedEntities.includes(entity.id);

    return (
      <Card
        key={entity.id}
        size="small"
        style={{ marginBottom: '12px' }}
        title={
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <NodeIndexOutlined />
              <span>{entity.name}</span>
              <Tag color={getEntityTypeColor(entity.type)}>
                {getEntityTypeLabel(entity.type)}
              </Tag>
              {detail && (
                <Tag color={getStatusColor(detail.graph_status)}>
                  {getStatusText(detail.graph_status)}
                </Tag>
              )}
            </div>
            <Button
              type="text"
              size="small"
              onClick={() => handleEntityExpand(entity.id)}
            >
              {isExpanded ? '收起' : '展开'}
            </Button>
          </div>
        }
      >
        <div style={{ marginBottom: '8px' }}>
          <Space>
            <span><strong>置信度:</strong> {Math.round(entity.confidence * 100)}%</span>
            {relatedRelations.length > 0 && (
              <span><strong>关系数:</strong> {relatedRelations.length}</span>
            )}
          </Space>
        </div>

        {entity.description && (
          <div style={{ marginBottom: '8px' }}>
            <strong>描述:</strong> {entity.description}
          </div>
        )}

        {isExpanded && detail && (
          <div>
            {/* 相关概念 */}
            {detail.related_concepts.length > 0 && (
              <div style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  <BulbOutlined />
                  <strong>相关概念:</strong>
                </div>
                <Space wrap>
                  {detail.related_concepts.map((concept, index) => (
                    <Tag key={index} color="cyan" style={{ cursor: 'pointer' }}>
                      {concept}
                    </Tag>
                  ))}
                </Space>
              </div>
            )}

            {/* 集成路径 */}
            {detail.integration_path.length > 0 && (
              <div style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  <LinkOutlined />
                  <strong>知识图谱路径:</strong>
                </div>
                <div style={{ 
                  padding: '8px', 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: '4px',
                  fontFamily: 'monospace'
                }}>
                  {detail.integration_path.join(' → ')}
                </div>
              </div>
            )}

            {/* 相关关系 */}
            {relatedRelations.length > 0 && (
              <div>
                <strong>相关关系:</strong>
                <div style={{ marginTop: '8px' }}>
                  {relatedRelations.map((relation, index) => {
                    const isSource = relation.source === entity.id;
                    const otherEntityId = isSource ? relation.target : relation.source;
                    const otherEntity = entities.find(e => e.id === otherEntityId);
                    
                    return (
                      <div
                        key={index}
                        style={{
                          padding: '6px 8px',
                          backgroundColor: '#f9f9f9',
                          borderRadius: '4px',
                          marginBottom: '4px',
                          fontSize: '12px'
                        }}
                      >
                        {isSource ? (
                          <span>
                            <strong>{entity.name}</strong>
                            <span style={{ margin: '0 8px', color: '#666' }}>
                              {relation.type}
                            </span>
                            <strong>{otherEntity?.name || otherEntityId}</strong>
                          </span>
                        ) : (
                          <span>
                            <strong>{otherEntity?.name || otherEntityId}</strong>
                            <span style={{ margin: '0 8px', color: '#666' }}>
                              {relation.type}
                            </span>
                            <strong>{entity.name}</strong>
                          </span>
                        )}
                        <span style={{ marginLeft: '8px', color: '#999' }}>
                          ({Math.round(relation.confidence * 100)}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </Card>
    );
  };

  const groupedEntities = entities.reduce((groups, entity) => {
    const type = entity.type;
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(entity);
    return groups;
  }, {} as Record<string, Entity[]>);

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <Space>
          <Tag color="blue">总实体: {entities.length}</Tag>
          <Tag color="purple">关系: {relations.length}</Tag>
          <Button
            size="small"
            onClick={() => setExpandedEntities(entities.map(e => e.id))}
          >
            全部展开
          </Button>
          <Button
            size="small"
            onClick={() => setExpandedEntities([])}
          >
            全部收起
          </Button>
        </Space>
      </div>

      <Collapse defaultActiveKey={Object.keys(groupedEntities)}>
        {Object.entries(groupedEntities).map(([type, typeEntities]) => (
          <Panel
            key={type}
            header={
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Tag color={getEntityTypeColor(type)}>
                  {getEntityTypeLabel(type)}
                </Tag>
                <span>({typeEntities.length} 个实体)</span>
              </div>
            }
          >
            {typeEntities.map(entity => renderEntityCard(entity))}
          </Panel>
        ))}
      </Collapse>
    </div>
  );
};

export default EntityDetailPanel;
