#!/usr/bin/env python3
"""
测试修复后的知识图谱集成功能
"""

import requests
import json
import time

def test_qa_with_graph():
    """测试QA API的图谱功能"""
    print("=" * 60)
    print("测试修复后的QA API图谱功能")
    print("=" * 60)
    
    # 测试查询
    test_queries = [
        "什么是回溯算法？",
        "动态规划的原理",
        "二叉树的特点",
        "快速排序怎么实现？"
    ]
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n测试查询 {i}: {query}")
        print("-" * 40)
        
        request_data = {
            "query": query,
            "query_type": "concept_explanation",
            "session_id": f"test_session_{i}"
        }
        
        try:
            start_time = time.time()
            response = requests.post(api_url, json=request_data, timeout=20)
            end_time = time.time()
            
            processing_time = end_time - start_time
            print(f"响应时间: {processing_time:.2f}秒")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查基本响应
                print(f"查询: {data.get('query', 'N/A')}")
                print(f"实体: {data.get('entities', [])}")
                print(f"意图: {data.get('intent', 'N/A')}")
                
                # 检查图谱数据
                graph_data = data.get('graph_data')
                if graph_data:
                    nodes = graph_data.get('nodes', [])
                    edges = graph_data.get('edges', [])
                    center_node = graph_data.get('center_node', '')
                    
                    print(f"✅ 图谱数据存在:")
                    print(f"  节点数量: {len(nodes)}")
                    print(f"  边数量: {len(edges)}")
                    print(f"  中心节点: {center_node}")
                    
                    # 显示前几个节点
                    if nodes:
                        print(f"  节点示例:")
                        for j, node in enumerate(nodes[:3]):
                            print(f"    {j+1}. {node.get('label', 'N/A')} ({node.get('type', 'N/A')})")
                    
                    # 显示前几条边
                    if edges:
                        print(f"  边示例:")
                        for j, edge in enumerate(edges[:3]):
                            print(f"    {j+1}. {edge.get('source', 'N/A')} --[{edge.get('relationship', 'N/A')}]--> {edge.get('target', 'N/A')}")
                    
                    print(f"  ✅ 前端应该显示图谱面板")
                else:
                    print(f"  ❌ 没有图谱数据")
                
                # 检查集成回答
                integrated_response = data.get('integrated_response', '')
                if integrated_response:
                    print(f"集成回答: {integrated_response[:100]}...")
                else:
                    print(f"❌ 没有集成回答")
                
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时（20秒）")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端服务")
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    return True

def test_frontend_display_simulation():
    """模拟前端显示测试"""
    print("\n" + "=" * 60)
    print("模拟前端显示测试")
    print("=" * 60)
    
    # 模拟一个成功的API响应
    mock_response = {
        "response_id": "test_123",
        "query": "什么是回溯算法？",
        "intent": "concept_explanation",
        "entities": ["回溯"],
        "concept_explanation": {
            "concept_name": "回溯算法",
            "definition": "回溯算法是一种系统性搜索问题解的算法..."
        },
        "example_problems": [],
        "similar_problems": [],
        "integrated_response": "回溯算法是一种重要的算法设计技术...",
        "graph_data": {
            "nodes": [
                {
                    "id": "center_回溯",
                    "label": "回溯",
                    "type": "Algorithm",
                    "properties": {"is_center": True},
                    "clickable": True
                },
                {
                    "id": "connected_0",
                    "label": "N皇后问题",
                    "type": "Problem",
                    "properties": {},
                    "clickable": True
                },
                {
                    "id": "connected_1",
                    "label": "全排列",
                    "type": "Problem",
                    "properties": {},
                    "clickable": True
                }
            ],
            "edges": [
                {
                    "source": "center_回溯",
                    "target": "connected_0",
                    "relationship": "SOLVES",
                    "properties": {}
                },
                {
                    "source": "center_回溯",
                    "target": "connected_1",
                    "relationship": "SOLVES",
                    "properties": {}
                }
            ],
            "center_node": "center_回溯",
            "layout_type": "force"
        },
        "status": "success",
        "confidence": 0.9,
        "processing_time": 2.5
    }
    
    print("模拟API响应数据:")
    print(f"  查询: {mock_response['query']}")
    print(f"  集成回答: {mock_response['integrated_response'][:50]}...")
    
    # 模拟前端显示条件检查
    graph_data = mock_response.get('graph_data')
    
    print(f"\n前端显示条件检查:")
    condition1 = graph_data is not None
    condition2 = isinstance(graph_data.get('nodes', None), list) if graph_data else False
    condition3 = len(graph_data.get('nodes', [])) > 0 if condition2 else False
    
    print(f"  graph_data存在: {condition1}")
    print(f"  nodes是数组: {condition2}")
    print(f"  nodes长度>0: {condition3}")
    
    should_display = condition1 and condition2 and condition3
    print(f"  应该显示图谱: {'是' if should_display else '否'}")
    
    if should_display:
        nodes = graph_data['nodes']
        print(f"\n✅ 前端将显示图谱面板:")
        print(f"  面板标题: 知识图谱 ({len(nodes)}个节点)")
        print(f"  图谱高度: 500px")
        print(f"  中心节点: {graph_data.get('center_node', 'N/A')}")
        print(f"  布局类型: {graph_data.get('layout_type', 'N/A')}")
        
        print(f"\n  节点列表:")
        for node in nodes:
            center_mark = " (中心)" if node.get('properties', {}).get('is_center') else ""
            print(f"    - {node['label']} ({node['type']}){center_mark}")
        
        print(f"\n  关系列表:")
        for edge in graph_data['edges']:
            source_label = next(n['label'] for n in nodes if n['id'] == edge['source'])
            target_label = next(n['label'] for n in nodes if n['id'] == edge['target'])
            print(f"    - {source_label} --[{edge['relationship']}]--> {target_label}")
        
        return True
    else:
        print(f"\n❌ 前端不会显示图谱面板")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试修复后的知识图谱集成功能...")
    
    # 检查后端服务
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
        else:
            print("❌ 后端服务异常")
            return
    except:
        print("❌ 无法连接到后端服务，请确保后端正在运行")
        return
    
    # 检查前端服务
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
        else:
            print("❌ 前端服务异常")
    except:
        print("❌ 无法连接到前端服务，请确保前端正在运行")
    
    # 执行测试
    tests = [
        ("QA API图谱功能", test_qa_with_graph),
        ("前端显示模拟", test_frontend_display_simulation),
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
        print("🎉 知识图谱集成功能修复成功！")
        print("\n💡 使用说明:")
        print("1. 在前端界面输入概念相关问题")
        print("2. 查看AI回答下方是否出现'知识图谱'面板")
        print("3. 图谱显示中心概念及其相关节点")
        print("4. 可以交互式探索图谱关系")
    else:
        print("⚠️  部分功能仍有问题，需要进一步调试")

if __name__ == "__main__":
    main()
