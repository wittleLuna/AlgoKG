#!/usr/bin/env python3
"""
调试API响应，检查图谱数据
"""

import requests
import json

def test_api_response():
    """测试API响应"""
    print("=" * 60)
    print("测试API响应中的图谱数据")
    print("=" * 60)
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    request_data = {
        "query": "什么是回溯算法？",
        "query_type": "concept_explanation",
        "session_id": "debug_session"
    }
    
    print(f"请求URL: {api_url}")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    
    try:
        print(f"\n发送请求...")
        response = requests.post(api_url, json=request_data, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n响应数据结构:")
            for key in data.keys():
                value = data[key]
                if isinstance(value, list):
                    print(f"  {key}: 列表 (长度: {len(value)})")
                elif isinstance(value, dict):
                    print(f"  {key}: 字典 (键: {list(value.keys())})")
                else:
                    print(f"  {key}: {type(value).__name__} = {value}")
            
            # 重点检查graph_data
            graph_data = data.get('graph_data')
            print(f"\n图谱数据详细检查:")
            print(f"  graph_data存在: {'是' if graph_data is not None else '否'}")
            
            if graph_data is not None:
                print(f"  graph_data类型: {type(graph_data)}")
                print(f"  graph_data内容:")
                print(json.dumps(graph_data, ensure_ascii=False, indent=4))
                
                # 检查前端显示条件
                nodes = graph_data.get('nodes', [])
                edges = graph_data.get('edges', [])
                
                print(f"\n前端显示条件检查:")
                condition1 = graph_data is not None
                condition2 = isinstance(nodes, list)
                condition3 = len(nodes) > 0 if isinstance(nodes, list) else False
                
                print(f"  condition1 (graph_data存在): {condition1}")
                print(f"  condition2 (nodes是数组): {condition2}")
                print(f"  condition3 (nodes长度>0): {condition3}")
                
                should_display = condition1 and condition2 and condition3
                print(f"  最终判断 (应该显示图谱): {should_display}")
                
                if should_display:
                    print(f"\n✅ 图谱应该在前端显示")
                    print(f"  节点数量: {len(nodes)}")
                    print(f"  边数量: {len(edges)}")
                    print(f"  中心节点: {graph_data.get('center_node', 'N/A')}")
                else:
                    print(f"\n❌ 图谱不会在前端显示")
                    if not condition1:
                        print(f"    原因: graph_data不存在")
                    elif not condition2:
                        print(f"    原因: nodes不是数组")
                    elif not condition3:
                        print(f"    原因: nodes数组为空")
            else:
                print(f"  ❌ graph_data为null，图谱不会显示")
            
            # 保存完整响应到文件
            with open('api_response_debug.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n完整响应已保存到: api_response_debug.json")
            
        else:
            print(f"❌ API请求失败")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

def check_frontend_code():
    """检查前端代码中的图谱显示逻辑"""
    print("\n" + "=" * 60)
    print("检查前端图谱显示逻辑")
    print("=" * 60)
    
    # 读取前端MessageItem.tsx文件
    try:
        with open('web_app/frontend/src/components/qa/MessageItem.tsx', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找图谱显示相关的代码
        lines = content.split('\n')
        graph_lines = []
        
        for i, line in enumerate(lines):
            if 'graph_data' in line.lower() or '知识图谱' in line:
                graph_lines.append((i+1, line.strip()))
        
        if graph_lines:
            print("前端图谱相关代码:")
            for line_num, line in graph_lines:
                print(f"  第{line_num}行: {line}")
        else:
            print("❌ 未找到图谱相关代码")
            
    except FileNotFoundError:
        print("❌ 无法找到前端MessageItem.tsx文件")
    except Exception as e:
        print(f"❌ 读取前端文件失败: {e}")

def main():
    """主函数"""
    print("🔍 开始调试API响应和前端显示...")
    
    # 测试API响应
    test_api_response()
    
    # 检查前端代码
    check_frontend_code()
    
    print("\n" + "=" * 60)
    print("🎯 调试总结")
    print("=" * 60)
    print("1. 检查api_response_debug.json文件中的完整响应")
    print("2. 确认graph_data字段是否存在且格式正确")
    print("3. 检查前端控制台是否有JavaScript错误")
    print("4. 确认前端组件是否正确渲染")

if __name__ == "__main__":
    main()
