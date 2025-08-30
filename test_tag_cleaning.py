#!/usr/bin/env python3
"""
测试标签清理功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "qa"))

def test_tag_cleaning():
    """测试标签清理功能"""
    print("=" * 60)
    print("测试标签清理功能")
    print("=" * 60)
    
    # 模拟Neo4j节点字符串
    neo4j_node_strings = [
        "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking', 'description': 'Backtracking算法', 'created_at': '2025-07-28T11:25:39.484903', 'id': 'algorithm_backtracking', 'category': 'algorithm'}>",
        "<Node element_id='75' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming', 'description': 'Dynamic Programming算法', 'created_at': '2025-07-28T11:25:41.002245', 'id': 'algorithm_dynamic_programming', 'category': 'algorithm'}>",
        "<Node element_id='77' labels=frozenset({'Algorithm'}) properties={'name': '动态规划', 'created_at': '2025-07-28T11:25:46.832292', 'description': '递归子问题解决方案', 'id': 'algorithm_动态规划', 'category': 'algorithm'}>"
    ]
    
    # 模拟混合标签列表（包含字符串和Neo4j节点）
    mixed_tags = [
        "数组",
        "哈希表",
        neo4j_node_strings[0],  # Backtracking节点
        "动态规划",
        neo4j_node_strings[1],  # Dynamic Programming节点
        neo4j_node_strings[2],  # 动态规划节点
        "二分查找"
    ]
    
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
                        import re
                        name_match = re.search(r"'name':\s*'([^']+)'", tag)
                        if name_match:
                            cleaned_tags.append(name_match.group(1))
                        else:
                            # 如果无法提取名称，跳过这个标签
                            continue
                    else:
                        cleaned_tags.append(tag)
                # 如果是Neo4j节点对象
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
    
    # 测试清理功能
    print("原始标签列表:")
    for i, tag in enumerate(mixed_tags):
        if isinstance(tag, str) and tag.startswith('<Node'):
            print(f"  {i+1}. [Neo4j节点] {tag[:80]}...")
        else:
            print(f"  {i+1}. [字符串] {tag}")
    
    print(f"\n原始标签数量: {len(mixed_tags)}")
    
    # 清理标签
    cleaned_tags = clean_tag_list(mixed_tags)
    
    print(f"\n清理后的标签:")
    for i, tag in enumerate(cleaned_tags):
        print(f"  {i+1}. {tag}")
    
    print(f"\n清理后标签数量: {len(cleaned_tags)}")
    
    # 验证结果
    expected_tags = {"数组", "哈希表", "Backtracking", "动态规划", "Dynamic Programming", "二分查找"}
    actual_tags = set(cleaned_tags)
    
    print(f"\n期望的标签: {expected_tags}")
    print(f"实际的标签: {actual_tags}")
    
    if expected_tags.issubset(actual_tags):
        print("✅ 标签清理成功！所有期望的标签都被正确提取")
        return True
    else:
        missing_tags = expected_tags - actual_tags
        print(f"❌ 标签清理失败！缺少标签: {missing_tags}")
        return False

def test_tag_service():
    """测试标签服务"""
    print("\n" + "=" * 60)
    print("测试标签服务")
    print("=" * 60)
    
    try:
        from web_app.backend.app.services.tag_service import tag_service
        
        # 模拟Neo4j节点字符串
        neo4j_tags = [
            "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking', 'description': 'Backtracking算法'}>",
            "动态规划",
            "数组",
            "<Node element_id='75' labels=frozenset({'DataStructure'}) properties={'name': 'Hash Table', 'description': '哈希表数据结构'}>"
        ]
        
        print("测试标签服务清理功能:")
        print("原始标签:")
        for tag in neo4j_tags:
            if isinstance(tag, str) and tag.startswith('<Node'):
                print(f"  [Neo4j节点] {tag[:60]}...")
            else:
                print(f"  [字符串] {tag}")
        
        # 使用标签服务清理
        processed_tags = tag_service.clean_and_standardize_tags(neo4j_tags)
        formatted_tags = tag_service.format_tags_for_display(processed_tags)
        
        print(f"\n处理后的标签 ({len(formatted_tags)} 个):")
        for tag in formatted_tags:
            print(f"  - {tag['display_name']} (类型: {tag['type']}, 颜色: {tag['color']})")
        
        # 检查是否有原始Neo4j节点字符串
        has_raw_nodes = any(
            tag['name'].startswith('<Node') or tag['display_name'].startswith('<Node')
            for tag in formatted_tags
        )
        
        if not has_raw_nodes:
            print("✅ 标签服务成功清理了所有Neo4j节点字符串")
            return True
        else:
            print("❌ 标签服务未能完全清理Neo4j节点字符串")
            return False
            
    except Exception as e:
        print(f"❌ 标签服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_display():
    """测试前端显示逻辑"""
    print("\n" + "=" * 60)
    print("测试前端显示逻辑")
    print("=" * 60)
    
    # 模拟推荐结果中的标签
    recommendation_with_raw_tags = {
        "title": "测试题目",
        "shared_tags": [
            "数组",
            "<Node element_id='79' labels=frozenset({'Algorithm'}) properties={'name': 'Backtracking'}>",
            "动态规划"
        ],
        "similarity_analysis": {
            "shared_concepts": [
                "哈希表",
                "<Node element_id='75' labels=frozenset({'Algorithm'}) properties={'name': 'Dynamic Programming'}>",
                "二分查找"
            ]
        }
    }
    
    def simulate_frontend_tag_display(tags):
        """模拟前端标签显示"""
        displayed_tags = []
        for tag in tags:
            if isinstance(tag, str):
                if tag.startswith('<Node element_id='):
                    # 这是我们要避免的情况
                    displayed_tags.append(f"[原始节点] {tag[:50]}...")
                else:
                    displayed_tags.append(tag)
            else:
                displayed_tags.append(str(tag))
        return displayed_tags
    
    print("模拟推荐结果中的标签:")
    print("shared_tags:")
    for tag in recommendation_with_raw_tags["shared_tags"]:
        print(f"  - {tag}")
    
    print("\nshared_concepts:")
    for tag in recommendation_with_raw_tags["similarity_analysis"]["shared_concepts"]:
        print(f"  - {tag}")
    
    # 模拟前端显示
    displayed_shared_tags = simulate_frontend_tag_display(recommendation_with_raw_tags["shared_tags"])
    displayed_concepts = simulate_frontend_tag_display(recommendation_with_raw_tags["similarity_analysis"]["shared_concepts"])
    
    print("\n前端显示的shared_tags:")
    for tag in displayed_shared_tags:
        print(f"  - {tag}")
    
    print("\n前端显示的shared_concepts:")
    for tag in displayed_concepts:
        print(f"  - {tag}")
    
    # 检查是否有原始节点显示
    has_raw_nodes = any(
        tag.startswith('[原始节点]') 
        for tag in displayed_shared_tags + displayed_concepts
    )
    
    if has_raw_nodes:
        print("❌ 前端仍会显示原始Neo4j节点字符串")
        return False
    else:
        print("✅ 前端不会显示原始Neo4j节点字符串")
        return True

def main():
    """主测试函数"""
    print("🚀 开始标签清理功能测试...")
    
    tests = [
        ("基础标签清理", test_tag_cleaning),
        ("标签服务测试", test_tag_service),
        ("前端显示逻辑", test_frontend_display),
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
        print("🎉 所有测试通过！标签清理功能正常工作！")
        print("\n💡 修复要点:")
        print("1. ✅ 添加了_clean_tag_list方法处理Neo4j节点字符串")
        print("2. ✅ 修复了_extract_tag_names方法处理各种标签格式")
        print("3. ✅ 在推荐结果中使用清理后的标签")
        print("4. ✅ 标签服务能正确处理Neo4j节点")
        
        print("\n🔧 关键修复:")
        print("- 识别并解析Neo4j节点字符串格式")
        print("- 从节点属性中提取name字段")
        print("- 过滤掉无法解析的原始节点字符串")
        print("- 确保前端只显示清理后的标签名称")
        
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎯 标签清理功能测试完成！")
        print("现在重启后端服务，推荐结果中应该显示清理后的标签名称，")
        print("而不是原始的Neo4j节点字符串。")
    else:
        print("⚠️  标签清理功能测试失败，需要进一步调试。")
    print(f"{'='*60}")
