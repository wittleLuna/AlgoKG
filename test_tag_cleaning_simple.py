#!/usr/bin/env python3
"""
简单的标签清理测试
"""

import re

def clean_tag_list(tags):
    """清理标签列表，确保返回字符串列表而不是Neo4j节点对象"""
    if not tags:
        return []
    
    cleaned_tags = []
    for tag in tags:
        if not tag:
            continue
            
        try:
            # 如果是字符串，直接使用
            if isinstance(tag, str):
                # 检查是否是Neo4j节点字符串表示
                if tag.startswith('<Node element_id='):
                    # 尝试从Neo4j节点字符串中提取名称
                    name_match = re.search(r"'name':\s*'([^']+)'", tag)
                    if name_match:
                        cleaned_tags.append(name_match.group(1))
                    else:
                        # 如果无法提取名称，跳过这个标签
                        continue
                else:
                    cleaned_tags.append(tag)
            # 如果是Neo4j节点对象（模拟）
            elif hasattr(tag, 'get') and hasattr(tag, 'labels'):
                name = tag.get("name", "")
                if name:
                    cleaned_tags.append(name)
            # 如果是字典
            elif hasattr(tag, 'get'):
                name = tag.get("name", "") or tag.get("title", "")
                if name:
                    cleaned_tags.append(name)
            # 其他情况，尝试转换为字符串
            else:
                tag_str = str(tag)
                if tag_str and not tag_str.startswith('<Node'):
                    cleaned_tags.append(tag_str)
                    
        except Exception as e:
            print(f"清理标签时出错: {tag}, 错误: {e}")
            continue
    
    return list(set(cleaned_tags))  # 去重

def test_tag_cleaning():
    """测试标签清理功能"""
    print("=" * 60)
    print("测试标签清理功能")
    print("=" * 60)
    
    # 模拟包含原始Neo4j节点的标签列表
    test_cases = [
        {
            "name": "混合标签列表",
            "input": [
                "数组",
                "哈希表",
                "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking', 'description': 'Backtracking算法', 'created_at': '2025-07-28T11:25:39.484903', 'id': 'algorithm_backtracking', 'category': 'algorithm'}>",
                "动态规划",
                "<Node element_id='75' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming', 'description': 'Dynamic Programming算法', 'created_at': '2025-07-28T11:25:41.002245', 'id': 'algorithm_dynamic_programming', 'category': 'algorithm'}>",
                "二分查找"
            ],
            "expected": {"数组", "哈希表", "Backtracking", "动态规划", "Dynamic Programming", "二分查找"}
        },
        {
            "name": "全部是原始节点",
            "input": [
                "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking'}>",
                "<Node element_id='75' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming'}>",
                "<Node element_id='77' labels=frozenset({'DataStructure'}) properties={'name': 'Array'}>"
            ],
            "expected": {"Backtracking", "Dynamic Programming", "Array"}
        },
        {
            "name": "全部是字符串",
            "input": ["数组", "哈希表", "动态规划", "二分查找"],
            "expected": {"数组", "哈希表", "动态规划", "二分查找"}
        },
        {
            "name": "空列表",
            "input": [],
            "expected": set()
        },
        {
            "name": "包含None和空字符串",
            "input": ["数组", None, "", "哈希表"],
            "expected": {"数组", "哈希表"}
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['name']}")
        print(f"输入: {len(test_case['input'])} 个标签")
        
        # 显示输入的前几个标签
        for j, tag in enumerate(test_case['input'][:3]):
            if isinstance(tag, str) and tag.startswith('<Node'):
                print(f"  输入 {j+1}: [Neo4j节点] {tag[:60]}...")
            else:
                print(f"  输入 {j+1}: [字符串] {tag}")
        
        if len(test_case['input']) > 3:
            print(f"  ... 还有 {len(test_case['input']) - 3} 个标签")
        
        # 执行清理
        result = clean_tag_list(test_case['input'])
        result_set = set(result)
        
        print(f"输出: {len(result)} 个标签")
        for tag in result:
            print(f"  输出: {tag}")
        
        # 验证结果
        if result_set == test_case['expected']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            print(f"期望: {test_case['expected']}")
            print(f"实际: {result_set}")
            print(f"缺少: {test_case['expected'] - result_set}")
            print(f"多余: {result_set - test_case['expected']}")
            all_passed = False
    
    return all_passed

def test_recommendation_data_structure():
    """测试推荐数据结构中的标签清理"""
    print("\n" + "=" * 60)
    print("测试推荐数据结构中的标签清理")
    print("=" * 60)
    
    # 模拟推荐结果数据结构
    mock_recommendation = {
        "title": "测试题目",
        "hybrid_score": 0.85,
        "embedding_score": 0.80,
        "tag_score": 0.90,
        "shared_tags": [
            "数组",
            "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking'}>",
            "动态规划"
        ],
        "similarity_analysis": {
            "embedding_similarity": 0.80,
            "tag_similarity": 0.90,
            "hybrid_score": 0.85,
            "shared_concepts": [
                "哈希表",
                "<Node element_id='75' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming'}>",
                "二分查找"
            ]
        },
        "learning_path": {
            "path_description": "测试学习路径",
            "reasoning": "测试推理"
        },
        "recommendation_reason": "测试推荐理由"
    }
    
    print("原始推荐数据:")
    print(f"  shared_tags: {len(mock_recommendation['shared_tags'])} 个")
    for tag in mock_recommendation['shared_tags']:
        if tag.startswith('<Node'):
            print(f"    [Neo4j节点] {tag[:60]}...")
        else:
            print(f"    [字符串] {tag}")
    
    print(f"  shared_concepts: {len(mock_recommendation['similarity_analysis']['shared_concepts'])} 个")
    for concept in mock_recommendation['similarity_analysis']['shared_concepts']:
        if concept.startswith('<Node'):
            print(f"    [Neo4j节点] {concept[:60]}...")
        else:
            print(f"    [字符串] {concept}")
    
    # 清理标签
    cleaned_shared_tags = clean_tag_list(mock_recommendation['shared_tags'])
    cleaned_shared_concepts = clean_tag_list(mock_recommendation['similarity_analysis']['shared_concepts'])
    
    print(f"\n清理后的数据:")
    print(f"  shared_tags: {cleaned_shared_tags}")
    print(f"  shared_concepts: {cleaned_shared_concepts}")
    
    # 检查是否还有原始节点
    has_raw_nodes = any(
        tag.startswith('<Node') for tag in cleaned_shared_tags + cleaned_shared_concepts
    )
    
    if not has_raw_nodes:
        print("✅ 所有标签都已清理")
        return True
    else:
        print("❌ 仍有原始Neo4j节点")
        return False

def main():
    """主测试函数"""
    print("🚀 开始简单标签清理测试...")
    
    tests = [
        ("基础标签清理", test_tag_cleaning),
        ("推荐数据结构清理", test_recommendation_data_structure),
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
    print("🎯 测试结果总结")
    print("=" * 60)
    
    for i, (test_name, result) in enumerate(zip([t[0] for t in tests], results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {test_name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！标签清理逻辑正确！")
        print("\n💡 关键发现:")
        print("1. ✅ 正则表达式能正确提取Neo4j节点中的name属性")
        print("2. ✅ 混合标签列表能正确处理")
        print("3. ✅ 推荐数据结构中的标签能正确清理")
        
        print("\n🔧 下一步:")
        print("- 确保在所有推荐路径中都使用了标签清理")
        print("- 检查是否有遗漏的数据传递路径")
        print("- 重启后端服务测试实际效果")
        
        return True
    else:
        print("⚠️  部分测试失败，标签清理逻辑需要调整")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎯 简单标签清理测试完成！")
        print("标签清理逻辑验证正确，现在需要确保在所有")
        print("推荐数据传递路径中都使用了这个清理逻辑。")
    else:
        print("⚠️  标签清理测试失败，需要进一步调试。")
    print(f"{'='*60}")
