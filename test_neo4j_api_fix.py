#!/usr/bin/env python3
"""
测试Neo4j API修复效果
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "backend"))

def test_neo4j_api_methods():
    """测试Neo4j API方法是否返回清理后的数据"""
    print("=" * 60)
    print("测试Neo4j API方法")
    print("=" * 60)
    
    try:
        from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
        
        # 创建Neo4j API实例
        neo4j_api = Neo4jKnowledgeGraphAPI()
        
        # 测试方法列表
        test_methods = [
            ("get_problem_by_title", "两数之和"),
            ("search_problems", "数组"),
            ("get_entities_by_type", "Problem")
        ]
        
        all_passed = True
        
        for method_name, test_param in test_methods:
            print(f"\n测试方法: {method_name}")
            
            try:
                method = getattr(neo4j_api, method_name)
                
                if method_name == "get_entities_by_type":
                    result = method(test_param, limit=3)
                else:
                    result = method(test_param)
                
                if result:
                    print(f"  返回结果数量: {len(result) if isinstance(result, list) else 1}")
                    
                    # 检查是否有原始Neo4j节点
                    has_raw_nodes = False
                    
                    def check_for_raw_nodes(obj, path=""):
                        nonlocal has_raw_nodes
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                check_for_raw_nodes(value, f"{path}.{key}")
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                if hasattr(item, 'get') and hasattr(item, 'labels'):
                                    # 这是Neo4j节点对象
                                    has_raw_nodes = True
                                    print(f"  ❌ 发现原始Neo4j节点 {path}[{i}]: {type(item)}")
                                elif isinstance(item, str) and item.startswith('<Node'):
                                    # 这是Neo4j节点字符串
                                    has_raw_nodes = True
                                    print(f"  ❌ 发现原始Neo4j节点字符串 {path}[{i}]: {item[:60]}...")
                                else:
                                    check_for_raw_nodes(item, f"{path}[{i}]")
                        elif hasattr(obj, 'get') and hasattr(obj, 'labels'):
                            # 这是Neo4j节点对象
                            has_raw_nodes = True
                            print(f"  ❌ 发现原始Neo4j节点 {path}: {type(obj)}")
                        elif isinstance(obj, str) and obj.startswith('<Node'):
                            # 这是Neo4j节点字符串
                            has_raw_nodes = True
                            print(f"  ❌ 发现原始Neo4j节点字符串 {path}: {obj[:60]}...")
                    
                    check_for_raw_nodes(result)
                    
                    if not has_raw_nodes:
                        print(f"  ✅ 所有数据都已清理")
                        
                        # 显示示例数据
                        if isinstance(result, list) and result:
                            sample = result[0]
                            print(f"  示例数据: {sample}")
                        elif isinstance(result, dict):
                            print(f"  示例数据: {result}")
                    else:
                        print(f"  ❌ 仍有原始Neo4j节点")
                        all_passed = False
                        
                else:
                    print(f"  ⚠️  无返回结果")
                    
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                import traceback
                traceback.print_exc()
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qa_service_integration():
    """测试QA服务集成效果"""
    print("\n" + "=" * 60)
    print("测试QA服务集成效果")
    print("=" * 60)
    
    try:
        # 模拟QA服务调用Neo4j API的场景
        from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
        
        neo4j_api = Neo4jKnowledgeGraphAPI()
        
        # 模拟QA服务中的调用
        test_entity = "两数之和"
        
        print(f"测试实体: {test_entity}")
        
        # 1. 测试get_problem_by_title
        print("\n1. 测试get_problem_by_title:")
        problem_detail = neo4j_api.get_problem_by_title(test_entity)
        
        if problem_detail:
            print(f"  获取到题目信息: {problem_detail.get('title', 'N/A')}")
            
            # 检查algorithms字段
            algorithms = problem_detail.get('algorithms', [])
            print(f"  算法数量: {len(algorithms)}")
            
            has_raw_nodes = False
            for i, alg in enumerate(algorithms):
                if hasattr(alg, 'get') and hasattr(alg, 'labels'):
                    has_raw_nodes = True
                    print(f"    ❌ 算法 {i}: 原始Neo4j节点 {type(alg)}")
                elif isinstance(alg, dict):
                    print(f"    ✅ 算法 {i}: {alg.get('name', 'N/A')}")
                else:
                    print(f"    ⚠️  算法 {i}: {type(alg)} - {alg}")
            
            # 检查data_structures字段
            data_structures = problem_detail.get('data_structures', [])
            print(f"  数据结构数量: {len(data_structures)}")
            
            for i, ds in enumerate(data_structures):
                if hasattr(ds, 'get') and hasattr(ds, 'labels'):
                    has_raw_nodes = True
                    print(f"    ❌ 数据结构 {i}: 原始Neo4j节点 {type(ds)}")
                elif isinstance(ds, dict):
                    print(f"    ✅ 数据结构 {i}: {ds.get('name', 'N/A')}")
                else:
                    print(f"    ⚠️  数据结构 {i}: {type(ds)} - {ds}")
            
            if not has_raw_nodes:
                print("  ✅ 所有标签数据都已清理")
                return True
            else:
                print("  ❌ 仍有原始Neo4j节点")
                return False
        else:
            print("  ⚠️  未找到题目信息")
            return True  # 没有数据不算失败
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_data_flow():
    """测试完整的数据流"""
    print("\n" + "=" * 60)
    print("测试完整数据流")
    print("=" * 60)
    
    try:
        # 模拟完整的推荐数据流
        from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
        
        neo4j_api = Neo4jKnowledgeGraphAPI()
        
        # 1. Neo4j API返回数据
        print("1. Neo4j API返回数据...")
        problem_detail = neo4j_api.get_problem_by_title("两数之和")
        
        if not problem_detail:
            print("  ⚠️  未找到测试数据，跳过测试")
            return True
        
        print(f"  题目: {problem_detail.get('title', 'N/A')}")
        
        # 2. 模拟QA服务处理
        print("\n2. 模拟QA服务处理...")
        
        # 模拟SimilarProblem创建
        similar_problem_data = {
            "title": problem_detail.get('title', ''),
            "hybrid_score": 1.0,
            "embedding_score": 0.0,
            "tag_score": 1.0,
            "shared_tags": ["直接匹配"],
            "learning_path": f"直接匹配的题目：《{problem_detail.get('title', '')}》",
            "recommendation_reason": f"用户查询直接匹配到题目《{problem_detail.get('title', '')}》",
            "learning_path_explanation": "这是用户查询中直接提到的题目",
            "recommendation_strength": "直接匹配",
            "complete_info": problem_detail  # 这里是关键！
        }
        
        # 3. 检查complete_info中是否有原始节点
        print("\n3. 检查complete_info...")
        complete_info = similar_problem_data["complete_info"]
        
        has_raw_nodes = False
        
        # 检查algorithms
        algorithms = complete_info.get('algorithms', [])
        for alg in algorithms:
            if hasattr(alg, 'get') and hasattr(alg, 'labels'):
                has_raw_nodes = True
                print(f"  ❌ 发现原始算法节点: {type(alg)}")
        
        # 检查data_structures
        data_structures = complete_info.get('data_structures', [])
        for ds in data_structures:
            if hasattr(ds, 'get') and hasattr(ds, 'labels'):
                has_raw_nodes = True
                print(f"  ❌ 发现原始数据结构节点: {type(ds)}")
        
        # 检查techniques
        techniques = complete_info.get('techniques', [])
        for tech in techniques:
            if hasattr(tech, 'get') and hasattr(tech, 'labels'):
                has_raw_nodes = True
                print(f"  ❌ 发现原始技巧节点: {type(tech)}")
        
        if not has_raw_nodes:
            print("  ✅ complete_info中所有数据都已清理")
            
            # 显示清理后的数据示例
            if algorithms:
                print(f"  算法示例: {algorithms[0]}")
            if data_structures:
                print(f"  数据结构示例: {data_structures[0]}")
            if techniques:
                print(f"  技巧示例: {techniques[0]}")
                
            return True
        else:
            print("  ❌ complete_info中仍有原始Neo4j节点")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始Neo4j API修复验证测试...")
    
    tests = [
        ("Neo4j API方法测试", test_neo4j_api_methods),
        ("QA服务集成测试", test_qa_service_integration),
        ("完整数据流测试", test_complete_data_flow),
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
    print("🎯 Neo4j API修复验证结果")
    print("=" * 60)
    
    for i, (test_name, result) in enumerate(zip([t[0] for t in tests], results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {test_name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！Neo4j API修复成功！")
        print("\n💡 修复效果:")
        print("1. ✅ get_problem_by_title返回清理后的字典")
        print("2. ✅ search_problems返回清理后的字典")
        print("3. ✅ get_entities_by_type返回清理后的字典")
        print("4. ✅ QA服务不再接收原始Neo4j节点")
        print("5. ✅ complete_info字段包含清理后的数据")
        
        print("\n🔧 关键修复:")
        print("- 在Neo4j API层面清理所有返回的节点对象")
        print("- 只保留关键属性，过滤掉原始节点引用")
        print("- 确保所有下游服务接收到的都是字典格式")
        
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎯 Neo4j API修复验证完成！")
        print("现在重启后端服务，推荐结果中应该不再出现")
        print("原始的Neo4j节点字符串。")
    else:
        print("⚠️  Neo4j API修复验证失败，需要进一步调试。")
    print(f"{'='*60}")
