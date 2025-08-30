#!/usr/bin/env python3
"""
测试API响应，确认graph_data字段
"""

import requests
import json
import sys

def test_api_response():
    """测试API响应"""
    print("🔍 测试API响应中的graph_data字段...")
    
    api_url = "http://localhost:8000/api/v1/qa/query"
    
    request_data = {
        "query": "什么是回溯算法？",
        "query_type": "concept_explanation",
        "session_id": "test_graph_data"
    }
    
    print(f"请求URL: {api_url}")
    print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    
    try:
        print(f"\n发送请求...")
        response = requests.post(api_url, json=request_data, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API请求失败")
            print(f"响应内容: {response.text}")
            return False
        
        # 解析响应
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"原始响应: {response.text[:500]}...")
            return False
        
        # 保存完整响应
        with open('api_response_test.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 完整响应已保存到: api_response_test.json")
        
        # 检查基本字段
        print(f"\n📋 基本字段检查:")
        basic_fields = ['response_id', 'query', 'intent', 'entities', 'status']
        for field in basic_fields:
            value = data.get(field)
            print(f"  {field}: {value}")
        
        # 重点检查graph_data
        print(f"\n🎯 graph_data字段详细检查:")
        
        graph_data = data.get('graph_data')
        
        if graph_data is None:
            print(f"  ❌ graph_data字段不存在或为null")
            print(f"  可用字段: {list(data.keys())}")
            return False
        
        print(f"  ✅ graph_data字段存在")
        print(f"  类型: {type(graph_data)}")
        
        if not isinstance(graph_data, dict):
            print(f"  ❌ graph_data不是字典类型")
            return False
        
        # 检查graph_data的子字段
        print(f"  graph_data包含的字段: {list(graph_data.keys())}")
        
        required_fields = ['nodes', 'edges', 'center_node', 'layout_type']
        for field in required_fields:
            value = graph_data.get(field)
            if field == 'nodes':
                if isinstance(value, list):
                    print(f"  {field}: 数组，长度={len(value)}")
                    if len(value) > 0:
                        print(f"    第一个节点: {json.dumps(value[0], ensure_ascii=False)}")
                else:
                    print(f"  {field}: {type(value)} = {value}")
            elif field == 'edges':
                if isinstance(value, list):
                    print(f"  {field}: 数组，长度={len(value)}")
                    if len(value) > 0:
                        print(f"    第一条边: {json.dumps(value[0], ensure_ascii=False)}")
                else:
                    print(f"  {field}: {type(value)} = {value}")
            else:
                print(f"  {field}: {value}")
        
        # 前端显示条件验证
        print(f"\n🖥️ 前端显示条件验证:")
        
        nodes = graph_data.get('nodes')
        
        condition1 = graph_data is not None
        condition2 = isinstance(nodes, list)
        condition3 = len(nodes) > 0 if isinstance(nodes, list) else False
        
        print(f"  条件1 (graph_data存在): {condition1}")
        print(f"  条件2 (nodes是数组): {condition2}")
        print(f"  条件3 (nodes长度>0): {condition3}")
        
        should_display = condition1 and condition2 and condition3
        
        if should_display:
            print(f"  ✅ 最终判断: 前端应该显示知识图谱")
            print(f"  预期面板标题: 知识图谱 ({len(nodes)}个节点)")
        else:
            print(f"  ❌ 最终判断: 前端不会显示知识图谱")
            if not condition1:
                print(f"    原因: graph_data不存在")
            elif not condition2:
                print(f"    原因: nodes不是数组")
            elif not condition3:
                print(f"    原因: nodes数组为空")
        
        return should_display
        
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务: {api_url}")
        print(f"请确保后端服务正在运行:")
        print(f"  cd web_app/backend")
        print(f"  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def check_backend_logs():
    """提供检查后端日志的指导"""
    print(f"\n📋 后端日志检查指导:")
    print(f"1. 查看后端控制台输出")
    print(f"2. 寻找以下关键日志:")
    print(f"   - '为实体 XXX 生成知识图谱'")
    print(f"   - '成功生成知识图谱: X个节点, Y条边'")
    print(f"   - 'QA响应构建 - 图谱数据状态'")
    print(f"   - '最终QA响应中的graph_data: True/False'")
    print(f"3. 如果没有看到这些日志，说明图谱生成逻辑没有被调用")
    print(f"4. 如果看到错误日志，请检查Neo4j连接和查询")

def main():
    """主函数"""
    print("🚀 开始测试API响应中的graph_data字段...")
    
    # 测试API响应
    success = test_api_response()
    
    # 提供后端日志检查指导
    check_backend_logs()
    
    # 总结
    print(f"\n" + "=" * 60)
    print(f"🎯 测试结果总结")
    print(f"=" * 60)
    
    if success:
        print(f"✅ API响应正常，graph_data字段存在且格式正确")
        print(f"✅ 前端应该显示知识图谱面板")
        print(f"\n如果前端仍然不显示图谱，请检查:")
        print(f"1. 前端控制台是否有JavaScript错误")
        print(f"2. MessageItem组件是否正确接收到数据")
        print(f"3. UnifiedGraphVisualization组件是否正常工作")
        print(f"4. 浏览器开发者工具中的调试输出")
    else:
        print(f"❌ API响应有问题，graph_data字段不存在或格式错误")
        print(f"\n请检查:")
        print(f"1. 后端服务是否正常运行")
        print(f"2. Neo4j服务是否正常运行")
        print(f"3. 后端日志中的错误信息")
        print(f"4. 图谱生成逻辑是否被正确调用")
    
    print(f"\n📁 相关文件:")
    print(f"  - api_response_test.json: 完整的API响应")
    print(f"  - GRAPH_DEBUG_STATUS.md: 详细的调试状态")

if __name__ == "__main__":
    main()
