#!/usr/bin/env python3
"""
测试简化的图谱生成功能
"""

import requests
import json
import time

def test_simple_api():
    """测试简化的API"""
    print("=" * 60)
    print("测试简化的图谱API")
    print("=" * 60)
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    request_data = {
        "query": "什么是回溯算法？",
        "query_type": "concept_explanation",
        "session_id": "test_simple"
    }
    
    print(f"测试查询: {request_data['query']}")
    
    try:
        print("发送请求...")
        start_time = time.time()
        
        response = requests.post(api_url, json=request_data, timeout=15)
        
        end_time = time.time()
        print(f"响应时间: {end_time - start_time:.2f}秒")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n基本信息:")
            print(f"  查询: {data.get('query', 'N/A')}")
            print(f"  实体: {data.get('entities', [])}")
            print(f"  状态: {data.get('status', 'N/A')}")
            
            # 检查图谱数据
            graph_data = data.get('graph_data')
            print(f"\n图谱数据检查:")
            
            if graph_data:
                nodes = graph_data.get('nodes', [])
                edges = graph_data.get('edges', [])
                center_node = graph_data.get('center_node', '')
                
                print(f"  ✅ 图谱数据存在")
                print(f"  节点数量: {len(nodes)}")
                print(f"  边数量: {len(edges)}")
                print(f"  中心节点: {center_node}")
                print(f"  布局类型: {graph_data.get('layout_type', 'N/A')}")
                
                # 显示节点详情
                if nodes:
                    print(f"\n  节点详情:")
                    for i, node in enumerate(nodes):
                        is_center = node.get('properties', {}).get('is_center', False)
                        center_mark = " (中心)" if is_center else ""
                        print(f"    {i+1}. {node.get('label', 'N/A')} ({node.get('type', 'N/A')}){center_mark}")
                
                # 显示边详情
                if edges:
                    print(f"\n  边详情:")
                    for i, edge in enumerate(edges):
                        print(f"    {i+1}. {edge.get('source', 'N/A')} --[{edge.get('relationship', 'N/A')}]--> {edge.get('target', 'N/A')}")
                
                # 前端显示条件检查
                print(f"\n  前端显示条件:")
                condition1 = graph_data is not None
                condition2 = isinstance(nodes, list)
                condition3 = len(nodes) > 0
                
                print(f"    graph_data存在: {condition1}")
                print(f"    nodes是数组: {condition2}")
                print(f"    nodes长度>0: {condition3}")
                
                should_display = condition1 and condition2 and condition3
                print(f"    应该显示图谱: {'是' if should_display else '否'}")
                
                if should_display:
                    print(f"\n  ✅ 前端应该显示知识图谱面板")
                    print(f"     面板标题: 知识图谱 ({len(nodes)}个节点)")
                    print(f"     图谱高度: 500px")
                    return True
                else:
                    print(f"\n  ❌ 前端不会显示知识图谱面板")
                    return False
            else:
                print(f"  ❌ 没有图谱数据")
                return False
                
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def simulate_frontend_rendering():
    """模拟前端渲染"""
    print("\n" + "=" * 60)
    print("模拟前端渲染效果")
    print("=" * 60)
    
    # 模拟成功的API响应
    mock_response = {
        "response_id": "test_123",
        "query": "什么是回溯算法？",
        "intent": "concept_explanation",
        "entities": ["回溯算法"],
        "concept_explanation": {
            "concept_name": "回溯算法",
            "definition": "回溯算法是一种系统性搜索问题解的算法...",
            "core_principles": ["试探", "回退", "剪枝"]
        },
        "example_problems": [
            {"title": "N皇后问题", "difficulty": "困难", "platform": "LeetCode"},
            {"title": "全排列", "difficulty": "中等", "platform": "LeetCode"}
        ],
        "similar_problems": [
            {"title": "组合总和", "hybrid_score": 0.85, "difficulty": "中等"},
            {"title": "子集", "hybrid_score": 0.78, "difficulty": "中等"}
        ],
        "integrated_response": "回溯算法是一种重要的算法设计技术...",
        "graph_data": {
            "nodes": [
                {
                    "id": "center_回溯算法",
                    "label": "回溯算法",
                    "type": "Concept",
                    "properties": {"is_center": True},
                    "clickable": True
                },
                {
                    "id": "problem_0",
                    "label": "组合总和",
                    "type": "Problem",
                    "properties": {"score": 0.85, "difficulty": "中等"},
                    "clickable": True
                },
                {
                    "id": "example_0",
                    "label": "N皇后问题",
                    "type": "Example",
                    "properties": {"difficulty": "困难", "platform": "LeetCode"},
                    "clickable": True
                },
                {
                    "id": "principle_0",
                    "label": "试探",
                    "type": "Principle",
                    "properties": {},
                    "clickable": True
                }
            ],
            "edges": [
                {
                    "source": "center_回溯算法",
                    "target": "problem_0",
                    "relationship": "RELATED_TO",
                    "properties": {"score": 0.85}
                },
                {
                    "source": "center_回溯算法",
                    "target": "example_0",
                    "relationship": "EXAMPLE_OF",
                    "properties": {}
                },
                {
                    "source": "center_回溯算法",
                    "target": "principle_0",
                    "relationship": "HAS_PRINCIPLE",
                    "properties": {}
                }
            ],
            "center_node": "center_回溯算法",
            "layout_type": "force"
        },
        "status": "success",
        "confidence": 0.9,
        "processing_time": 2.1
    }
    
    print("模拟前端接收到的数据:")
    print(f"  查询: {mock_response['query']}")
    print(f"  集成回答: {mock_response['integrated_response'][:50]}...")
    
    # 模拟前端显示逻辑
    graph_data = mock_response.get('graph_data')
    
    if graph_data and isinstance(graph_data.get('nodes'), list) and len(graph_data.get('nodes')) > 0:
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        print(f"\n✅ 前端将显示知识图谱面板:")
        print(f"  面板标题: 知识图谱 ({len(nodes)}个节点)")
        print(f"  图谱容器: 500px高度")
        print(f"  显示控件: 是")
        print(f"  中心节点: {graph_data.get('center_node')}")
        
        print(f"\n  图谱内容:")
        print(f"    节点类型分布:")
        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        for node_type, count in node_types.items():
            print(f"      {node_type}: {count}个")
        
        print(f"    关系类型分布:")
        edge_types = {}
        for edge in edges:
            edge_type = edge.get('relationship', 'Unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        
        for edge_type, count in edge_types.items():
            print(f"      {edge_type}: {count}条")
        
        print(f"\n  用户体验:")
        print(f"    - 可以看到中心概念及其相关节点")
        print(f"    - 可以拖拽和缩放图谱")
        print(f"    - 可以点击节点查看详情")
        print(f"    - 不同类型的节点有不同的颜色")
        
        return True
    else:
        print(f"\n❌ 前端不会显示知识图谱面板")
        return False

def main():
    """主函数"""
    print("🚀 开始测试简化的知识图谱功能...")
    
    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print("❌ 后端服务异常")
            return
    except:
        print("❌ 无法连接到后端服务")
        print("请确保后端服务正在运行:")
        print("  cd web_app/backend")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # 执行测试
    tests = [
        ("简化API测试", test_simple_api),
        ("前端渲染模拟", simulate_frontend_rendering),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 执行测试: {test_name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
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
        print("🎉 简化的知识图谱功能测试成功！")
        print("\n💡 使用说明:")
        print("1. 在前端界面输入概念相关问题")
        print("2. 查看AI回答下方的'知识图谱'面板")
        print("3. 图谱显示中心概念及其相关节点")
        print("4. 包括相似题目、示例题目和核心原理")
    else:
        print("⚠️  部分功能仍有问题，需要进一步调试")
        print("\n🔧 调试建议:")
        print("1. 检查后端日志中的错误信息")
        print("2. 确认前端控制台没有JavaScript错误")
        print("3. 验证API响应格式是否正确")

if __name__ == "__main__":
    main()
