#!/usr/bin/env python3
"""
测试内嵌知识图谱功能
"""

import requests
import json
import time

def test_inline_graph():
    """测试内嵌知识图谱功能"""
    print("🔍 测试内嵌知识图谱功能...")
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    test_queries = [
        "什么是回溯算法？",
        "动态规划的原理是什么？",
        "二叉树有什么特点？",
        "快速排序的时间复杂度是多少？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"测试查询 {i}: {query}")
        print('='*60)
        
        request_data = {
            "query": query,
            "query_type": "concept_explanation",
            "session_id": f"inline_test_{i}"
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
                print(f"\n📋 基本信息:")
                print(f"  查询: {data.get('query', 'N/A')}")
                print(f"  实体: {data.get('entities', [])}")
                print(f"  状态: {data.get('status', 'N/A')}")
                
                # 检查图谱数据
                graph_data = data.get('graph_data')
                entities = data.get('entities', [])
                
                print(f"\n🕸️ 内嵌图谱显示条件检查:")
                
                condition1 = graph_data is not None
                condition2 = isinstance(graph_data.get('nodes', None), list) if graph_data else False
                condition3 = len(graph_data.get('nodes', [])) > 0 if condition2 else False
                condition4 = entities is not None and len(entities) > 0
                
                print(f"  graph_data存在: {condition1}")
                print(f"  nodes是数组: {condition2}")
                print(f"  nodes长度>0: {condition3}")
                print(f"  entities存在: {condition4}")
                
                should_display = condition1 and condition2 and condition3 and condition4
                
                if should_display:
                    nodes = graph_data['nodes']
                    edges = graph_data['edges']
                    
                    print(f"\n✅ 内嵌图谱应该显示:")
                    print(f"  节点数量: {len(nodes)}")
                    print(f"  边数量: {len(edges)}")
                    print(f"  中心节点: {graph_data.get('center_node', 'N/A')}")
                    print(f"  查询实体: {entities}")
                    
                    # 节点类型统计
                    node_types = {}
                    for node in nodes:
                        node_type = node.get('type', 'Unknown')
                        node_types[node_type] = node_types.get(node_type, 0) + 1
                    
                    print(f"  节点类型分布:")
                    for node_type, count in node_types.items():
                        print(f"    {node_type}: {count}个")
                    
                    # 显示前几个节点
                    print(f"  节点示例:")
                    for j, node in enumerate(nodes[:3]):
                        is_center = node.get('properties', {}).get('is_center', False)
                        center_mark = " (中心)" if is_center else ""
                        print(f"    {j+1}. {node.get('label', 'N/A')} ({node.get('type', 'N/A')}){center_mark}")
                    
                    print(f"\n🎯 前端预期效果:")
                    print(f"  1. AI回答内容正常显示")
                    print(f"  2. 回答下方显示内嵌知识图谱卡片")
                    print(f"  3. 图谱卡片显示: '知识图谱 {len(nodes)}个节点 {len(edges)}条关系'")
                    print(f"  4. 显示查询实体标签: {', '.join(entities)}")
                    print(f"  5. 显示节点类型统计")
                    print(f"  6. 点击'展开'可查看完整图谱")
                    print(f"  7. 点击图谱节点可查看详细信息")
                    print(f"  8. 点击'完整视图'可跳转到独立图谱页面")
                    
                else:
                    print(f"\n❌ 内嵌图谱不会显示")
                    if not condition1:
                        print(f"    原因: graph_data不存在")
                    elif not condition2:
                        print(f"    原因: nodes不是数组")
                    elif not condition3:
                        print(f"    原因: nodes数组为空")
                    elif not condition4:
                        print(f"    原因: entities为空")
                
                # 保存响应数据
                filename = f"inline_graph_test_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"\n💾 完整响应已保存到: {filename}")
                
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端服务")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

def check_backend_status():
    """检查后端服务状态"""
    print("🔍 检查后端服务状态...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正常运行")
            return True
        else:
            print(f"❌ 后端服务异常: {response.status_code}")
            return False
    except:
        print("❌ 无法连接到后端服务")
        print("请确保后端服务正在运行:")
        print("  cd web_app/backend")
        print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False

def main():
    """主函数"""
    print("🚀 开始测试内嵌知识图谱功能...")
    
    # 检查后端服务
    if not check_backend_status():
        return
    
    # 测试内嵌图谱功能
    test_inline_graph()
    
    print(f"\n" + "="*60)
    print("🎯 测试总结")
    print("="*60)
    
    print("✅ 新的内嵌知识图谱设计特点:")
    print("1. 🎨 美观的卡片式设计，集成在AI回答中")
    print("2. 📊 显示节点和边的统计信息")
    print("3. 🏷️ 显示查询实体和节点类型分布")
    print("4. 🔍 支持展开/收起图谱可视化")
    print("5. 👆 点击节点显示详细信息抽屉")
    print("6. 🔗 支持跳转到完整图谱页面")
    print("7. 📱 响应式设计，适配不同屏幕")
    
    print("\n💡 使用说明:")
    print("1. 在前端输入概念相关问题")
    print("2. 查看AI回答下方的内嵌知识图谱卡片")
    print("3. 点击'展开'查看完整图谱可视化")
    print("4. 点击图谱中的节点查看详细信息")
    print("5. 点击'完整视图'跳转到独立图谱页面")

if __name__ == "__main__":
    main()
