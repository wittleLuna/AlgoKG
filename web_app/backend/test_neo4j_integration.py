#!/usr/bin/env python3
"""
测试Neo4j集成功能
"""
import asyncio
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(__file__))

from app.services.neo4j_integration_service import get_neo4j_integration_service

async def test_neo4j_integration():
    """测试Neo4j集成"""
    print("开始测试Neo4j集成...")
    
    try:
        integration_service = get_neo4j_integration_service()
        print(f"Neo4j集成服务创建成功，可用性: {integration_service.neo4j_available}")
        
        # 测试实体数据
        test_entities = [
            {
                'id': 'test_entity_1',
                'name': '括号匹配',
                'type': 'problem_type',
                'description': '括号匹配问题',
                'confidence': 0.9
            },
            {
                'id': 'test_entity_2', 
                'name': '栈',
                'type': 'data_structure',
                'description': '栈数据结构',
                'confidence': 0.8
            }
        ]
        
        test_relations = [
            {
                'source': '括号匹配',
                'target': '栈',
                'type': 'uses',
                'confidence': 0.9
            }
        ]
        
        print("开始集成测试实体...")
        result = await integration_service.integrate_note_entities(
            "test_note_123", test_entities, test_relations
        )
        
        print("集成结果:")
        print(f"- 成功: {result.get('success', False)}")
        print(f"- 集成实体数: {result.get('integrated_entities', 0)}")
        print(f"- 集成关系数: {result.get('integrated_relations', 0)}")
        print(f"- 模式: {result.get('mode', 'normal')}")
        
        if result.get('integration_details'):
            details = result['integration_details']
            print(f"- 新实体: {len(details.get('new_entities', []))}")
            print(f"- 增强实体: {len(details.get('enhanced_entities', []))}")
            print(f"- 现有实体: {len(details.get('existing_entities', []))}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_neo4j_integration())
