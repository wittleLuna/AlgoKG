#!/usr/bin/env python3
"""
测试推荐系统修复的脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "web_app" / "backend"))

def test_mock_recommendation_system():
    """测试模拟推荐系统"""
    print("=" * 50)
    print("测试模拟推荐系统")
    print("=" * 50)
    
    try:
        from web_app.backend.app.core.mock_qa import MockEnhancedRecommendationSystem
        
        # 创建模拟推荐系统实例
        mock_rec = MockEnhancedRecommendationSystem()
        print("✅ 模拟推荐系统创建成功")
        
        # 测试recommend方法
        if hasattr(mock_rec, 'recommend'):
            print("✅ recommend方法存在")
            
            # 调用recommend方法
            result = mock_rec.recommend(
                query_title="动态规划",
                top_k=5,
                alpha=0.7,
                enable_diversity=True,
                diversity_lambda=0.3
            )
            
            print(f"✅ recommend方法调用成功")
            print(f"返回状态: {result.get('status', 'unknown')}")
            print(f"推荐数量: {len(result.get('recommendations', []))}")
            
            if result.get('recommendations'):
                print("推荐结果示例:")
                for i, rec in enumerate(result['recommendations'][:2]):
                    print(f"  {i+1}. {rec['title']} (分数: {rec['hybrid_score']})")
            
        else:
            print("❌ recommend方法不存在")
            return False
            
    except Exception as e:
        print(f"❌ 模拟推荐系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_deps_initialization():
    """测试依赖注入初始化"""
    print("\n" + "=" * 50)
    print("测试依赖注入初始化")
    print("=" * 50)
    
    try:
        # 设置环境变量
        os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
        os.environ.setdefault('NEO4J_USER', 'neo4j')
        os.environ.setdefault('NEO4J_PASSWORD', 'password')
        os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
        
        from web_app.backend.app.core.deps import get_recommendation_system
        
        # 获取推荐系统实例
        rec_system = get_recommendation_system()
        print("✅ 推荐系统获取成功")
        
        if rec_system:
            print(f"推荐系统类型: {type(rec_system).__name__}")
            
            if hasattr(rec_system, 'recommend'):
                print("✅ recommend方法存在")
                
                # 测试调用
                result = rec_system.recommend(
                    query_title="测试题目",
                    top_k=3
                )
                
                print(f"✅ 推荐系统调用成功")
                print(f"返回状态: {result.get('status', 'unknown')}")
                print(f"推荐数量: {len(result.get('recommendations', []))}")
                
            else:
                print("❌ recommend方法不存在")
                return False
        else:
            print("❌ 推荐系统为None")
            return False
            
    except Exception as e:
        print(f"❌ 依赖注入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_qa_service():
    """测试QA服务"""
    print("\n" + "=" * 50)
    print("测试QA服务推荐功能")
    print("=" * 50)
    
    try:
        # 设置环境变量
        os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
        os.environ.setdefault('NEO4J_USER', 'neo4j')
        os.environ.setdefault('NEO4J_PASSWORD', 'password')
        os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
        
        from web_app.backend.app.services.qa_service import QAService
        from web_app.backend.app.models.request import QARequest
        
        # 创建QA服务
        qa_service = QAService()
        print("✅ QA服务创建成功")
        
        # 创建测试请求
        request = QARequest(
            query="请推荐一些动态规划的题目",
            session_id="test_session",
            query_type="problem_recommendation"
        )
        
        # 测试处理查询
        import asyncio
        
        async def test_query():
            try:
                response = await qa_service.process_query(request)
                print("✅ QA查询处理成功")
                print(f"推荐数量: {len(response.recommendations)}")
                
                if response.recommendations:
                    print("推荐结果:")
                    for i, rec in enumerate(response.recommendations[:3]):
                        print(f"  {i+1}. {rec.title} (强度: {rec.recommendation_strength})")
                
                return True
            except Exception as e:
                print(f"❌ QA查询处理失败: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        result = asyncio.run(test_query())
        return result
        
    except Exception as e:
        print(f"❌ QA服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试推荐系统修复...")
    
    results = []
    
    # 测试1: 模拟推荐系统
    results.append(test_mock_recommendation_system())
    
    # 测试2: 依赖注入
    results.append(test_deps_initialization())
    
    # 测试3: QA服务
    results.append(test_qa_service())
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    
    test_names = [
        "模拟推荐系统",
        "依赖注入初始化", 
        "QA服务推荐功能"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n总体结果: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！推荐系统修复成功！")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
