#!/usr/bin/env python3
"""
调试图谱数据响应问题
"""

import requests
import json
import sys

def test_qa_api_response():
    """测试QA API响应中的图谱数据"""
    print("=" * 60)
    print("调试QA API响应中的图谱数据")
    print("=" * 60)
    
    # 测试查询
    test_query = "什么是回溯算法？"
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    print(f"测试查询: {test_query}")
    print(f"API地址: {api_url}")
    
    # 构建请求数据
    request_data = {
        "query": test_query,
        "query_type": "concept_explanation",
        "session_id": "debug_session"
    }
    
    try:
        print(f"\n发送请求...")
        response = requests.post(api_url, json=request_data, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            
            print(f"\n响应数据结构:")
            print(f"  response_id: {response_data.get('response_id', 'N/A')}")
            print(f"  query: {response_data.get('query', 'N/A')}")
            print(f"  intent: {response_data.get('intent', 'N/A')}")
            print(f"  entities: {response_data.get('entities', [])}")
            print(f"  status: {response_data.get('status', 'N/A')}")
            print(f"  confidence: {response_data.get('confidence', 0.0)}")
            
            # 检查图谱数据
            graph_data = response_data.get('graph_data')
            print(f"\n图谱数据检查:")
            print(f"  graph_data存在: {'是' if graph_data is not None else '否'}")
            
            if graph_data:
                print(f"  graph_data类型: {type(graph_data)}")
                print(f"  graph_data内容: {json.dumps(graph_data, indent=2, ensure_ascii=False)[:500]}...")
                
                # 检查节点和边
                nodes = graph_data.get('nodes', [])
                edges = graph_data.get('edges', [])
                center_node = graph_data.get('center_node')
                layout_type = graph_data.get('layout_type')
                
                print(f"\n图谱数据详情:")
                print(f"  节点数量: {len(nodes) if isinstance(nodes, list) else 'N/A'}")
                print(f"  边数量: {len(edges) if isinstance(edges, list) else 'N/A'}")
                print(f"  中心节点: {center_node}")
                print(f"  布局类型: {layout_type}")
                
                # 检查前端显示条件
                print(f"\n前端显示条件检查:")
                condition1 = graph_data is not None
                condition2 = isinstance(nodes, list)
                condition3 = len(nodes) > 0 if isinstance(nodes, list) else False
                
                print(f"  graph_data存在: {condition1}")
                print(f"  nodes是数组: {condition2}")
                print(f"  nodes长度>0: {condition3}")
                
                should_display = condition1 and condition2 and condition3
                print(f"  应该显示图谱: {'是' if should_display else '否'}")
                
                if should_display:
                    print(f"\n✅ 图谱数据格式正确，前端应该显示图谱面板")
                    
                    # 显示前几个节点作为示例
                    print(f"\n节点示例:")
                    for i, node in enumerate(nodes[:3]):
                        print(f"  节点{i+1}: {node}")
                    
                    print(f"\n边示例:")
                    for i, edge in enumerate(edges[:3]):
                        print(f"  边{i+1}: {edge}")
                        
                    return True
                else:
                    print(f"\n❌ 图谱数据格式有问题，前端不会显示图谱面板")
                    return False
            else:
                print(f"  ❌ 没有图谱数据")
                return False
                
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务，请确保后端正在运行在 {api_url}")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_frontend_conditions():
    """测试前端显示条件"""
    print("\n" + "=" * 60)
    print("测试前端显示条件")
    print("=" * 60)
    
    # 模拟不同的图谱数据情况
    test_cases = [
        {
            "name": "正常图谱数据",
            "graph_data": {
                "nodes": [
                    {"id": "1", "label": "回溯", "type": "Algorithm"},
                    {"id": "2", "label": "N皇后", "type": "Problem"}
                ],
                "edges": [
                    {"source": "1", "target": "2", "relationship": "SOLVES"}
                ],
                "center_node": "1",
                "layout_type": "force"
            },
            "expected": True
        },
        {
            "name": "空节点数组",
            "graph_data": {
                "nodes": [],
                "edges": [],
                "center_node": None,
                "layout_type": "force"
            },
            "expected": False
        },
        {
            "name": "null图谱数据",
            "graph_data": None,
            "expected": False
        },
        {
            "name": "节点不是数组",
            "graph_data": {
                "nodes": "not_array",
                "edges": [],
                "center_node": "1",
                "layout_type": "force"
            },
            "expected": False
        }
    ]
    
    print("前端显示条件: response.graph_data && Array.isArray(response.graph_data.nodes) && response.graph_data.nodes.length > 0")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['name']}")
        
        graph_data = test_case['graph_data']
        
        # 模拟前端条件判断
        condition1 = graph_data is not None
        condition2 = isinstance(graph_data.get('nodes', None), list) if graph_data else False
        condition3 = len(graph_data.get('nodes', [])) > 0 if condition2 else False
        
        should_display = condition1 and condition2 and condition3
        
        print(f"  graph_data存在: {condition1}")
        print(f"  nodes是数组: {condition2}")
        print(f"  nodes长度>0: {condition3}")
        print(f"  应该显示: {should_display}")
        print(f"  期望结果: {test_case['expected']}")
        
        if should_display == test_case['expected']:
            print(f"  ✅ 测试通过")
        else:
            print(f"  ❌ 测试失败")

def check_frontend_running():
    """检查前端是否正在运行"""
    print("\n" + "=" * 60)
    print("检查前端服务状态")
    print("=" * 60)
    
    frontend_urls = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    for url in frontend_urls:
        try:
            print(f"检查 {url}...")
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ 前端服务运行在 {url}")
                return True
        except:
            print(f"❌ {url} 不可访问")
    
    print(f"\n⚠️  前端服务似乎没有运行")
    print(f"请确保前端服务已启动:")
    print(f"  cd web_app/frontend")
    print(f"  npm start")
    
    return False

def main():
    """主函数"""
    print("🔍 开始调试图谱数据响应问题...")
    
    # 检查前端是否运行
    frontend_running = check_frontend_running()
    
    # 测试API响应
    api_success = test_qa_api_response()
    
    # 测试前端条件
    test_frontend_conditions()
    
    print("\n" + "=" * 60)
    print("🎯 调试结果总结")
    print("=" * 60)
    
    print(f"前端服务状态: {'✅ 运行中' if frontend_running else '❌ 未运行'}")
    print(f"API图谱数据: {'✅ 正常' if api_success else '❌ 异常'}")
    
    if not frontend_running:
        print(f"\n🔧 解决方案:")
        print(f"1. 启动前端服务:")
        print(f"   cd web_app/frontend")
        print(f"   npm install  # 如果是第一次运行")
        print(f"   npm start")
        print(f"2. 在浏览器中访问 http://localhost:3000")
        print(f"3. 重新测试图谱显示功能")
    elif not api_success:
        print(f"\n🔧 解决方案:")
        print(f"1. 检查后端日志中的错误信息")
        print(f"2. 确认Neo4j服务正常运行")
        print(f"3. 检查图谱数据生成逻辑")
    else:
        print(f"\n✅ 后端和前端都正常，图谱应该能正常显示")
        print(f"如果仍然看不到图谱，请检查:")
        print(f"1. 浏览器开发者工具中的网络请求")
        print(f"2. 浏览器控制台中的JavaScript错误")
        print(f"3. 前端组件的渲染状态")

if __name__ == "__main__":
    main()
