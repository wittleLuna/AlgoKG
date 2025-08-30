#!/usr/bin/env python3
"""
全面调试知识图谱显示问题
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def check_services():
    """检查服务状态"""
    print("=" * 60)
    print("检查服务状态")
    print("=" * 60)
    
    services = {
        "后端服务": "http://localhost:8000/health",
        "前端服务": "http://localhost:3000"
    }
    
    service_status = {}
    
    for service_name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: 正常运行")
                service_status[service_name] = True
            else:
                print(f"❌ {service_name}: 异常 (状态码: {response.status_code})")
                service_status[service_name] = False
        except requests.exceptions.ConnectionError:
            print(f"❌ {service_name}: 无法连接")
            service_status[service_name] = False
        except Exception as e:
            print(f"❌ {service_name}: 错误 - {e}")
            service_status[service_name] = False
    
    return service_status

def test_api_response():
    """测试API响应"""
    print("\n" + "=" * 60)
    print("测试API响应")
    print("=" * 60)
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    test_queries = [
        "什么是回溯算法？",
        "动态规划的原理是什么？",
        "二叉树有什么特点？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n测试查询 {i}: {query}")
        print("-" * 40)
        
        request_data = {
            "query": query,
            "query_type": "concept_explanation",
            "session_id": f"debug_session_{i}"
        }
        
        try:
            start_time = time.time()
            response = requests.post(api_url, json=request_data, timeout=30)
            end_time = time.time()
            
            print(f"响应时间: {end_time - start_time:.2f}秒")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 基本信息
                print(f"查询: {data.get('query', 'N/A')}")
                print(f"实体: {data.get('entities', [])}")
                print(f"状态: {data.get('status', 'N/A')}")
                
                # 重点检查graph_data
                graph_data = data.get('graph_data')
                print(f"\n图谱数据检查:")
                
                if graph_data is None:
                    print(f"  ❌ graph_data为null")
                    continue
                
                print(f"  ✅ graph_data存在")
                print(f"  类型: {type(graph_data)}")
                
                # 检查nodes
                nodes = graph_data.get('nodes')
                if nodes is None:
                    print(f"  ❌ nodes为null")
                    continue
                
                if not isinstance(nodes, list):
                    print(f"  ❌ nodes不是数组，类型: {type(nodes)}")
                    continue
                
                print(f"  ✅ nodes是数组，长度: {len(nodes)}")
                
                if len(nodes) == 0:
                    print(f"  ❌ nodes数组为空")
                    continue
                
                # 检查edges
                edges = graph_data.get('edges', [])
                print(f"  ✅ edges数组，长度: {len(edges)}")
                
                # 前端显示条件
                condition1 = graph_data is not None
                condition2 = isinstance(nodes, list)
                condition3 = len(nodes) > 0
                
                print(f"\n  前端显示条件:")
                print(f"    graph_data存在: {condition1}")
                print(f"    nodes是数组: {condition2}")
                print(f"    nodes长度>0: {condition3}")
                
                should_display = condition1 and condition2 and condition3
                print(f"    最终判断: {'应该显示' if should_display else '不应该显示'}")
                
                if should_display:
                    print(f"\n  ✅ 前端应该显示图谱面板")
                    
                    # 显示节点详情
                    print(f"  节点详情:")
                    for j, node in enumerate(nodes[:3]):
                        print(f"    {j+1}. {node}")
                    
                    # 保存响应到文件
                    filename = f"api_response_{i}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"  完整响应已保存到: {filename}")
                    
                    return True
                else:
                    print(f"  ❌ 前端不会显示图谱面板")
                    
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时")
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    
    return False

def check_frontend_code():
    """检查前端代码"""
    print("\n" + "=" * 60)
    print("检查前端代码")
    print("=" * 60)
    
    frontend_file = Path("web_app/frontend/src/components/qa/MessageItem.tsx")
    
    if not frontend_file.exists():
        print(f"❌ 前端文件不存在: {frontend_file}")
        return False
    
    try:
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键代码
        checks = [
            ("graph_data检查", "response.graph_data"),
            ("数组检查", "Array.isArray(response.graph_data.nodes)"),
            ("长度检查", "response.graph_data.nodes.length > 0"),
            ("图谱面板", "知识图谱"),
            ("UnifiedGraphVisualization", "UnifiedGraphVisualization")
        ]
        
        print("前端代码检查:")
        for check_name, pattern in checks:
            if pattern in content:
                print(f"  ✅ {check_name}: 找到")
            else:
                print(f"  ❌ {check_name}: 未找到")
        
        # 查找具体的显示条件
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'graph_data' in line and 'Array.isArray' in line:
                print(f"\n找到显示条件 (第{i+1}行):")
                print(f"  {line.strip()}")
                
                # 显示前后几行
                start = max(0, i-2)
                end = min(len(lines), i+3)
                print(f"\n上下文:")
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j+1:4d}: {lines[j]}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ 读取前端文件失败: {e}")
        return False

def check_browser_console():
    """检查浏览器控制台"""
    print("\n" + "=" * 60)
    print("浏览器控制台检查指南")
    print("=" * 60)
    
    print("请手动检查浏览器控制台:")
    print("1. 打开浏览器开发者工具 (F12)")
    print("2. 切换到 Console 标签")
    print("3. 发送一个测试查询")
    print("4. 查看是否有JavaScript错误")
    print("5. 查看Network标签中的API请求和响应")
    
    print("\n常见问题:")
    print("- JavaScript错误导致组件渲染失败")
    print("- API响应格式不正确")
    print("- 组件状态更新问题")
    print("- CSS样式问题导致图谱不可见")

def check_component_rendering():
    """检查组件渲染"""
    print("\n" + "=" * 60)
    print("组件渲染检查指南")
    print("=" * 60)
    
    print("请检查以下内容:")
    print("1. MessageItem组件是否正确接收到response数据")
    print("2. response.graph_data是否存在且格式正确")
    print("3. Collapse组件是否正常展开")
    print("4. Panel组件是否正确渲染")
    print("5. UnifiedGraphVisualization组件是否正常工作")
    
    print("\n调试建议:")
    print("1. 在MessageItem组件中添加console.log(response.graph_data)")
    print("2. 检查UnifiedGraphVisualization组件的props")
    print("3. 确认图谱容器的CSS样式")
    print("4. 检查是否有条件渲染阻止了图谱显示")

def generate_test_data():
    """生成测试数据"""
    print("\n" + "=" * 60)
    print("生成测试数据")
    print("=" * 60)
    
    test_response = {
        "response_id": "test_123",
        "query": "什么是回溯算法？",
        "intent": "concept_explanation",
        "entities": ["回溯算法"],
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
                    "id": "neo4j_center",
                    "label": "回溯算法",
                    "type": "Algorithm",
                    "properties": {"is_center": True},
                    "clickable": True
                },
                {
                    "id": "neo4j_problem1",
                    "label": "N皇后问题",
                    "type": "Problem",
                    "properties": {},
                    "clickable": True
                },
                {
                    "id": "neo4j_problem2",
                    "label": "全排列",
                    "type": "Problem",
                    "properties": {},
                    "clickable": True
                }
            ],
            "edges": [
                {
                    "source": "neo4j_center",
                    "target": "neo4j_problem1",
                    "relationship": "SOLVES",
                    "properties": {}
                },
                {
                    "source": "neo4j_center",
                    "target": "neo4j_problem2",
                    "relationship": "SOLVES",
                    "properties": {}
                }
            ],
            "center_node": "neo4j_center",
            "layout_type": "force"
        },
        "status": "success",
        "confidence": 0.9,
        "processing_time": 2.1
    }
    
    # 保存测试数据
    with open('test_response.json', 'w', encoding='utf-8') as f:
        json.dump(test_response, f, ensure_ascii=False, indent=2)
    
    print("测试数据已生成: test_response.json")
    print("可以用这个数据测试前端组件")
    
    # 验证测试数据
    graph_data = test_response.get('graph_data')
    if graph_data and isinstance(graph_data.get('nodes'), list) and len(graph_data.get('nodes')) > 0:
        print("✅ 测试数据格式正确，前端应该显示图谱")
    else:
        print("❌ 测试数据格式有问题")

def main():
    """主函数"""
    print("🔍 开始全面调试知识图谱显示问题...")
    
    # 检查服务状态
    service_status = check_services()
    
    if not service_status.get("后端服务", False):
        print("\n❌ 后端服务未运行，请先启动后端服务:")
        print("cd web_app/backend")
        print("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    if not service_status.get("前端服务", False):
        print("\n❌ 前端服务未运行，请先启动前端服务:")
        print("cd web_app/frontend")
        print("npm start")
        return
    
    # 测试API响应
    api_success = test_api_response()
    
    # 检查前端代码
    frontend_code_ok = check_frontend_code()
    
    # 生成测试数据
    generate_test_data()
    
    # 检查指南
    check_browser_console()
    check_component_rendering()
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 调试总结")
    print("=" * 60)
    
    print(f"后端服务: {'✅ 正常' if service_status.get('后端服务') else '❌ 异常'}")
    print(f"前端服务: {'✅ 正常' if service_status.get('前端服务') else '❌ 异常'}")
    print(f"API响应: {'✅ 正常' if api_success else '❌ 异常'}")
    print(f"前端代码: {'✅ 正常' if frontend_code_ok else '❌ 异常'}")
    
    if api_success and frontend_code_ok:
        print("\n✅ 后端和前端代码都正常")
        print("如果图谱仍然不显示，请检查:")
        print("1. 浏览器控制台的JavaScript错误")
        print("2. 网络请求是否成功")
        print("3. 组件状态是否正确更新")
        print("4. CSS样式是否正确")
    else:
        print("\n❌ 发现问题，请根据上述检查结果进行修复")

if __name__ == "__main__":
    main()
