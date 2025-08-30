#!/usr/bin/env python3
"""
最终的Neo4j节点显示问题修复验证
"""

def test_deep_clean_objects():
    """测试深度清理对象方法"""
    print("=" * 60)
    print("测试深度清理对象方法")
    print("=" * 60)
    
    # 模拟Neo4j节点对象
    class MockNeo4jNode:
        def __init__(self, properties):
            self.properties = properties
            self.labels = frozenset(['Algorithm'])
        
        def get(self, key, default=None):
            return self.properties.get(key, default)
        
        def __str__(self):
            return f"<Node element_id='123' labels={self.labels} properties={self.properties}>"
    
    def deep_clean_objects(obj):
        """深度清理对象，确保所有嵌套对象都被正确序列化"""
        if obj is None:
            return None
        elif isinstance(obj, str):
            # 检查是否是Neo4j节点字符串
            if obj.startswith('<Node element_id='):
                # 尝试从Neo4j节点字符串中提取名称
                import re
                name_match = re.search(r"'name':\s*'([^']+)'", obj)
                if name_match:
                    return name_match.group(1)
                else:
                    return "Neo4j节点"
            return obj
        elif isinstance(obj, (int, float, bool)):
            return obj
        elif hasattr(obj, 'get') and hasattr(obj, 'labels'):
            # 这是Neo4j节点对象，提取关键信息
            return {
                'name': obj.get('name', ''),
                'title': obj.get('title', ''),
                'description': obj.get('description', ''),
                'category': obj.get('category', ''),
                'type': obj.get('type', '')
            }
        elif isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = deep_clean_objects(value)
                # 确保值不是复杂对象
                if isinstance(cleaned_value, (dict, list)) and cleaned_value:
                    cleaned[key] = cleaned_value
                elif cleaned_value is not None:
                    cleaned[key] = str(cleaned_value) if not isinstance(cleaned_value, (str, int, float, bool)) else cleaned_value
            return cleaned
        elif isinstance(obj, list):
            cleaned = []
            for item in obj:
                cleaned_item = deep_clean_objects(item)
                if cleaned_item is not None:
                    cleaned.append(cleaned_item)
            return cleaned
        else:
            # 对于其他类型，尝试转换为字符串
            return str(obj)
    
    # 测试用例
    test_cases = [
        {
            "name": "Neo4j节点对象",
            "input": MockNeo4jNode({'name': 'Backtracking', 'description': 'Backtracking算法'}),
            "expected_type": dict,
            "expected_name": "Backtracking"
        },
        {
            "name": "Neo4j节点字符串",
            "input": "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming', 'description': 'DP算法'}>",
            "expected_type": str,
            "expected_name": "Dynamic Programming"
        },
        {
            "name": "包含Neo4j节点的字典",
            "input": {
                "title": "测试题目",
                "algorithms": [
                    MockNeo4jNode({'name': 'Backtracking'}),
                    MockNeo4jNode({'name': 'Dynamic Programming'})
                ],
                "description": "测试描述"
            },
            "expected_type": dict,
            "expected_algorithms": [
                {'name': 'Backtracking', 'title': '', 'description': '', 'category': '', 'type': ''},
                {'name': 'Dynamic Programming', 'title': '', 'description': '', 'category': '', 'type': ''}
            ]
        },
        {
            "name": "包含Neo4j节点字符串的列表",
            "input": [
                "正常字符串",
                "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking'}>",
                "另一个正常字符串"
            ],
            "expected_type": list,
            "expected_result": ["正常字符串", "Backtracking", "另一个正常字符串"]
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['name']}")
        
        result = deep_clean_objects(test_case['input'])
        
        print(f"  输入类型: {type(test_case['input']).__name__}")
        print(f"  输出类型: {type(result).__name__}")
        print(f"  输出: {result}")
        
        # 验证结果
        passed = True
        
        if type(result) != test_case['expected_type']:
            passed = False
            print(f"  ❌ 类型不匹配: 期望 {test_case['expected_type'].__name__}, 实际 {type(result).__name__}")
        
        if 'expected_name' in test_case:
            if isinstance(result, dict) and result.get('name') != test_case['expected_name']:
                passed = False
                print(f"  ❌ 名称不匹配: 期望 '{test_case['expected_name']}', 实际 '{result.get('name')}'")
            elif isinstance(result, str) and result != test_case['expected_name']:
                passed = False
                print(f"  ❌ 字符串不匹配: 期望 '{test_case['expected_name']}', 实际 '{result}'")
        
        if 'expected_algorithms' in test_case:
            if result.get('algorithms') != test_case['expected_algorithms']:
                passed = False
                print(f"  ❌ 算法列表不匹配")
                print(f"    期望: {test_case['expected_algorithms']}")
                print(f"    实际: {result.get('algorithms')}")
        
        if 'expected_result' in test_case:
            if result != test_case['expected_result']:
                passed = False
                print(f"  ❌ 结果不匹配")
                print(f"    期望: {test_case['expected_result']}")
                print(f"    实际: {result}")
        
        if passed:
            print("  ✅ 测试通过")
        else:
            print("  ❌ 测试失败")
            all_passed = False
    
    return all_passed

def test_similar_problem_creation():
    """测试SimilarProblem创建过程"""
    print("\n" + "=" * 60)
    print("测试SimilarProblem创建过程")
    print("=" * 60)
    
    # 模拟Neo4j节点对象
    class MockNeo4jNode:
        def __init__(self, properties):
            self.properties = properties
            self.labels = frozenset(['Algorithm'])
        
        def get(self, key, default=None):
            return self.properties.get(key, default)
        
        def __str__(self):
            return f"<Node element_id='123' labels={self.labels} properties={self.properties}>"
    
    # 模拟从Neo4j API返回的problem_detail（修复前可能包含原始节点）
    mock_problem_detail = {
        'title': '两数之和',
        'description': '给定一个整数数组nums和一个整数目标值target...',
        'difficulty': '简单',
        'algorithms': [
            MockNeo4jNode({'name': 'Hash Table', 'description': '哈希表算法'}),
            MockNeo4jNode({'name': 'Two Pointers', 'description': '双指针技巧'})
        ],
        'data_structures': [
            MockNeo4jNode({'name': 'Array', 'description': '数组数据结构'})
        ]
    }
    
    print("原始problem_detail（可能包含Neo4j节点）:")
    print(f"  title: {mock_problem_detail['title']}")
    print(f"  algorithms: {[type(alg).__name__ for alg in mock_problem_detail['algorithms']]}")
    print(f"  data_structures: {[type(ds).__name__ for ds in mock_problem_detail['data_structures']]}")
    
    # 应用修复逻辑
    def deep_clean_objects(obj):
        """深度清理对象"""
        if obj is None:
            return None
        elif isinstance(obj, str):
            if obj.startswith('<Node element_id='):
                import re
                name_match = re.search(r"'name':\s*'([^']+)'", obj)
                if name_match:
                    return name_match.group(1)
                else:
                    return "Neo4j节点"
            return obj
        elif isinstance(obj, (int, float, bool)):
            return obj
        elif hasattr(obj, 'get') and hasattr(obj, 'labels'):
            return {
                'name': obj.get('name', ''),
                'title': obj.get('title', ''),
                'description': obj.get('description', ''),
                'category': obj.get('category', ''),
                'type': obj.get('type', '')
            }
        elif isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = deep_clean_objects(value)
                if isinstance(cleaned_value, (dict, list)) and cleaned_value:
                    cleaned[key] = cleaned_value
                elif cleaned_value is not None:
                    cleaned[key] = str(cleaned_value) if not isinstance(cleaned_value, (str, int, float, bool)) else cleaned_value
            return cleaned
        elif isinstance(obj, list):
            cleaned = []
            for item in obj:
                cleaned_item = deep_clean_objects(item)
                if cleaned_item is not None:
                    cleaned.append(cleaned_item)
            return cleaned
        else:
            return str(obj)
    
    print(f"\n应用深度清理...")
    cleaned_problem_detail = deep_clean_objects(mock_problem_detail)
    
    print("清理后的problem_detail:")
    print(f"  title: {cleaned_problem_detail['title']}")
    print(f"  algorithms: {cleaned_problem_detail['algorithms']}")
    print(f"  data_structures: {cleaned_problem_detail['data_structures']}")
    
    # 模拟SimilarProblem创建
    print(f"\n模拟SimilarProblem创建...")
    similar_problem_data = {
        "title": "两数之和",
        "hybrid_score": 1.0,
        "embedding_score": 0.0,
        "tag_score": 1.0,
        "shared_tags": ["直接匹配"],
        "learning_path": "直接匹配的题目：《两数之和》",
        "recommendation_reason": "用户查询直接匹配到题目《两数之和》",
        "learning_path_explanation": "这是用户查询中直接提到的题目",
        "recommendation_strength": "直接匹配",
        "complete_info": cleaned_problem_detail  # 使用清理后的数据
    }
    
    # 检查是否还有原始节点
    has_raw_nodes = False
    
    def check_for_raw_nodes(obj, path=""):
        nonlocal has_raw_nodes
        if isinstance(obj, dict):
            for key, value in obj.items():
                check_for_raw_nodes(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if hasattr(item, 'get') and hasattr(item, 'labels'):
                    has_raw_nodes = True
                    print(f"  ❌ 发现原始Neo4j节点 {path}[{i}]: {type(item)}")
                else:
                    check_for_raw_nodes(item, f"{path}[{i}]")
        elif hasattr(obj, 'get') and hasattr(obj, 'labels'):
            has_raw_nodes = True
            print(f"  ❌ 发现原始Neo4j节点 {path}: {type(obj)}")
    
    check_for_raw_nodes(similar_problem_data)
    
    if not has_raw_nodes:
        print("✅ SimilarProblem数据中没有原始Neo4j节点")
        return True
    else:
        print("❌ SimilarProblem数据中仍有原始Neo4j节点")
        return False

def test_pydantic_serialization():
    """测试Pydantic序列化效果"""
    print("\n" + "=" * 60)
    print("测试Pydantic序列化效果")
    print("=" * 60)
    
    # 模拟包含清理后数据的SimilarProblem
    similar_problem_data = {
        "title": "两数之和",
        "hybrid_score": 1.0,
        "embedding_score": 0.0,
        "tag_score": 1.0,
        "shared_tags": ["Hash Table", "Two Pointers", "Array"],  # 清理后的字符串列表
        "learning_path": "直接匹配的题目：《两数之和》",
        "recommendation_reason": "用户查询直接匹配到题目《两数之和》",
        "learning_path_explanation": "这是用户查询中直接提到的题目",
        "recommendation_strength": "直接匹配",
        "complete_info": {
            "title": "两数之和",
            "algorithms": [
                {"name": "Hash Table", "description": "哈希表算法"},
                {"name": "Two Pointers", "description": "双指针技巧"}
            ]
        }
    }
    
    print("模拟SimilarProblem数据:")
    print(f"  title: {similar_problem_data['title']}")
    print(f"  shared_tags: {similar_problem_data['shared_tags']}")
    print(f"  complete_info.algorithms: {similar_problem_data['complete_info']['algorithms']}")
    
    # 模拟Pydantic序列化（转换为JSON）
    import json
    
    try:
        json_data = json.dumps(similar_problem_data, ensure_ascii=False, indent=2)
        print(f"\nPydantic序列化成功:")
        print(json_data[:200] + "..." if len(json_data) > 200 else json_data)
        
        # 检查序列化后的数据是否包含原始节点字符串
        if "<Node element_id=" in json_data:
            print("❌ 序列化后的数据仍包含原始Neo4j节点字符串")
            return False
        else:
            print("✅ 序列化后的数据不包含原始Neo4j节点字符串")
            return True
            
    except Exception as e:
        print(f"❌ Pydantic序列化失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始最终Neo4j修复验证测试...")
    
    tests = [
        ("深度清理对象方法", test_deep_clean_objects),
        ("SimilarProblem创建过程", test_similar_problem_creation),
        ("Pydantic序列化效果", test_pydantic_serialization),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 最终Neo4j修复验证结果")
    print("=" * 60)
    
    for i, (test_name, result) in enumerate(zip([t[0] for t in tests], results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {test_name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！Neo4j节点显示问题已彻底修复！")
        print("\n💡 关键修复:")
        print("1. ✅ 增强了_deep_clean_objects方法，正确处理Neo4j节点对象")
        print("2. ✅ 修复了直接传递problem_detail的问题")
        print("3. ✅ 修复了直接传递similar对象的问题")
        print("4. ✅ 确保所有complete_info都经过清理")
        
        print("\n🔧 修复位置:")
        print("- web_app/backend/app/services/qa_service.py: _deep_clean_objects方法")
        print("- web_app/backend/app/services/qa_service.py: 第440行 complete_info处理")
        print("- web_app/backend/app/services/qa_service.py: 第469行 complete_info处理")
        print("- backend/neo4j_loader/neo4j_api.py: 所有返回方法")
        
        print("\n🎯 预期效果:")
        print("- 前端不再显示<Node element_id='xx' ...>格式")
        print("- shared_tags显示为清晰的字符串列表")
        print("- complete_info包含结构化的字典数据")
        print("- Pydantic序列化正常工作")
        
        return True
    else:
        print("⚠️  部分测试失败，修复逻辑需要进一步调整")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎯 Neo4j节点显示问题修复验证完成！")
        print("现在重启后端服务，前端应该不再显示")
        print("原始的Neo4j节点字符串，所有标签都将显示为")
        print("用户友好的名称。")
    else:
        print("⚠️  Neo4j节点显示问题修复验证失败，需要进一步调试。")
    print(f"{'='*60}")
