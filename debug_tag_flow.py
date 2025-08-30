#!/usr/bin/env python3
"""
调试标签数据流的脚本
"""

import sys
import os
from pathlib import Path
import json
import logging

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "qa"))
sys.path.append(str(project_root / "web_app" / "backend"))

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_neo4j_query_result():
    """测试Neo4j查询返回的实际数据结构"""
    print("=" * 60)
    print("测试Neo4j查询返回的数据结构")
    print("=" * 60)
    
    try:
        # 导入必要的模块
        from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
        
        # 创建Neo4j API实例
        neo4j_api = Neo4jKnowledgeGraphAPI()
        
        # 测试查询一个题目的标签
        test_query = """
        MATCH (p:Problem)
        WHERE p.title CONTAINS '两数之和' OR p.title CONTAINS '爬楼梯'
        OPTIONAL MATCH (p)-[:HAS_TAG]->(t:Tag)
        RETURN p.title as title, collect(DISTINCT t) as tags
        LIMIT 1
        """
        
        print("执行测试查询...")
        result = neo4j_api.run_query(test_query)
        
        if result:
            print(f"查询结果数量: {len(result)}")
            for i, record in enumerate(result):
                print(f"\n记录 {i+1}:")
                print(f"  题目: {record.get('title', 'N/A')}")
                
                tags = record.get('tags', [])
                print(f"  标签数量: {len(tags)}")
                
                for j, tag in enumerate(tags):
                    print(f"    标签 {j+1}:")
                    print(f"      类型: {type(tag)}")
                    print(f"      字符串表示: {str(tag)[:100]}...")
                    
                    # 尝试获取标签属性
                    if hasattr(tag, 'get'):
                        print(f"      name属性: {tag.get('name', 'N/A')}")
                        print(f"      type属性: {tag.get('type', 'N/A')}")
                    
                    if hasattr(tag, 'labels'):
                        print(f"      Neo4j标签: {list(tag.labels)}")
                        
                    print()
        else:
            print("查询无结果")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_agent_tag_extraction():
    """测试多智能体系统的标签提取"""
    print("\n" + "=" * 60)
    print("测试多智能体系统标签提取")
    print("=" * 60)
    
    try:
        # 导入多智能体系统
        from qa.multi_agent_qa import EnhancedNeo4jKnowledgeGraphAPI
        from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
        
        # 加载实体映射
        entity_id_to_title_path = r"F:\algokg_platform\data\raw\entity_id_to_title.json"
        
        if not os.path.exists(entity_id_to_title_path):
            print(f"❌ 实体映射文件不存在: {entity_id_to_title_path}")
            return False
            
        with open(entity_id_to_title_path, 'r', encoding='utf-8') as f:
            entity_id_to_title = json.load(f)
        
        print(f"加载了 {len(entity_id_to_title)} 个实体映射")
        
        # 创建增强的Neo4j API
        neo4j_api = Neo4jKnowledgeGraphAPI()
        enhanced_api = EnhancedNeo4jKnowledgeGraphAPI(neo4j_api, entity_id_to_title)
        
        # 测试获取一个题目的完整信息
        test_titles = ["两数之和", "爬楼梯", "二分查找"]
        
        for title in test_titles:
            print(f"\n测试题目: {title}")
            
            try:
                problem_info = enhanced_api.get_complete_problem_info(problem_title=title)
                
                if problem_info:
                    print(f"  获取到题目信息: {problem_info.get('title', 'N/A')}")
                    print(f"  算法标签: {problem_info.get('algorithm_tags', [])}")
                    print(f"  数据结构标签: {problem_info.get('data_structure_tags', [])}")
                    print(f"  技巧标签: {problem_info.get('technique_tags', [])}")
                    
                    # 检查是否有原始Neo4j节点
                    all_tags = (
                        problem_info.get('algorithm_tags', []) +
                        problem_info.get('data_structure_tags', []) +
                        problem_info.get('technique_tags', [])
                    )
                    
                    has_raw_nodes = any(
                        isinstance(tag, str) and tag.startswith('<Node')
                        for tag in all_tags
                    )
                    
                    if has_raw_nodes:
                        print("  ❌ 发现原始Neo4j节点！")
                        for tag in all_tags:
                            if isinstance(tag, str) and tag.startswith('<Node'):
                                print(f"    原始节点: {tag[:80]}...")
                    else:
                        print("  ✅ 所有标签都已清理")
                        
                else:
                    print(f"  ❌ 未找到题目信息")
                    
            except Exception as e:
                print(f"  ❌ 获取题目信息失败: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recommendation_flow():
    """测试推荐流程中的标签处理"""
    print("\n" + "=" * 60)
    print("测试推荐流程中的标签处理")
    print("=" * 60)
    
    try:
        # 导入推荐系统
        from qa.multi_agent_qa import GraphBasedSimilarProblemFinderAgent, EnhancedNeo4jKnowledgeGraphAPI
        from backend.neo4j_loader.neo4j_api import Neo4jKnowledgeGraphAPI
        from web_app.backend.app.services.enhanced_recommendation_service import EnhancedRecommendationSystem
        
        # 加载配置
        entity_id_to_title_path = r"F:\algokg_platform\data\raw\entity_id_to_title.json"
        
        if not os.path.exists(entity_id_to_title_path):
            print(f"❌ 实体映射文件不存在: {entity_id_to_title_path}")
            return False
            
        with open(entity_id_to_title_path, 'r', encoding='utf-8') as f:
            entity_id_to_title = json.load(f)
        
        # 创建系统组件
        neo4j_api = Neo4jKnowledgeGraphAPI()
        enhanced_api = EnhancedNeo4jKnowledgeGraphAPI(neo4j_api, entity_id_to_title)
        
        # 检查推荐系统配置
        config = {
            "embedding_path": r"F:\algokg_platform\models\ensemble_gnn_embedding.pt",
            "entity2id_path": r"F:\algokg_platform\data\raw\entity2id.json", 
            "id2title_path": r"F:\algokg_platform\data\raw\entity_id_to_title.json",
            "tag_label_path": r"F:\algokg_platform\data\raw\problem_id_to_tags.json"
        }
        
        # 检查文件是否存在
        missing_files = []
        for key, path in config.items():
            if not os.path.exists(path):
                missing_files.append(f"{key}: {path}")
        
        if missing_files:
            print("❌ 缺少推荐系统文件:")
            for file in missing_files:
                print(f"  - {file}")
            print("使用模拟推荐系统...")
            rec_system = None
        else:
            try:
                rec_system = EnhancedRecommendationSystem(
                    embedding_path=config["embedding_path"],
                    entity2id_path=config["entity2id_path"],
                    id2title_path=config["id2title_path"],
                    tag_label_path=config["tag_label_path"]
                )
                print("✅ 推荐系统加载成功")
            except Exception as e:
                print(f"❌ 推荐系统加载失败: {e}")
                rec_system = None
        
        # 创建相似题目查找Agent
        similar_finder = GraphBasedSimilarProblemFinderAgent(rec_system, enhanced_api)
        
        # 测试查找相似题目
        test_title = "两数之和"
        print(f"\n测试查找与《{test_title}》相似的题目...")
        
        import asyncio
        
        async def test_async():
            response = await similar_finder.find_similar_problems(test_title, 3)
            
            if response and response.content:
                print(f"找到 {len(response.content)} 个相似题目:")
                
                for i, item in enumerate(response.content):
                    print(f"\n  相似题目 {i+1}:")
                    print(f"    标题: {item.get('title', 'N/A')}")
                    print(f"    混合得分: {item.get('hybrid_score', 0)}")
                    
                    # 检查similarity_analysis中的shared_concepts
                    similarity_analysis = item.get('similarity_analysis', {})
                    shared_concepts = similarity_analysis.get('shared_concepts', [])
                    
                    print(f"    共同概念数量: {len(shared_concepts)}")
                    
                    has_raw_nodes = False
                    for concept in shared_concepts:
                        if isinstance(concept, str) and concept.startswith('<Node'):
                            has_raw_nodes = True
                            print(f"    ❌ 发现原始节点: {concept[:60]}...")
                    
                    if not has_raw_nodes and shared_concepts:
                        print(f"    ✅ 共同概念: {shared_concepts}")
                    elif not shared_concepts:
                        print(f"    ⚠️  无共同概念")
                        
            else:
                print("❌ 未找到相似题目")
        
        # 运行异步测试
        asyncio.run(test_async())
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始调试标签数据流...")
    
    tests = [
        ("Neo4j查询结果", test_neo4j_query_result),
        ("多智能体标签提取", test_multi_agent_tag_extraction),
        ("推荐流程标签处理", test_recommendation_flow),
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
    print("🎯 调试结果总结")
    print("=" * 60)
    
    for i, (test_name, result) in enumerate(zip([t[0] for t in tests], results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {test_name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有调试测试通过！")
    else:
        print("⚠️  部分测试失败，需要进一步检查")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎯 标签数据流调试完成！")
    else:
        print("⚠️  标签数据流调试发现问题，需要进一步修复。")
    print(f"{'='*60}")
