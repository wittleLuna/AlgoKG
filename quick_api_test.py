#!/usr/bin/env python3
"""
快速API测试
"""

import requests
import json

def test_api():
    """快速测试API"""
    print("测试API响应...")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/qa/query",
            json={
                "query": "什么是回溯算法？",
                "query_type": "concept_explanation",
                "session_id": "quick_test"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ API响应成功")
            print(f"查询: {data.get('query')}")
            print(f"实体: {data.get('entities')}")
            
            graph_data = data.get('graph_data')
            if graph_data:
                print(f"✅ 图谱数据存在")
                print(f"节点数量: {len(graph_data.get('nodes', []))}")
                print(f"边数量: {len(graph_data.get('edges', []))}")
                
                # 保存到文件
                with open('api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"完整响应已保存到: api_response.json")
            else:
                print(f"❌ 图谱数据不存在")
        else:
            print(f"❌ API失败: {response.status_code}")
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    test_api()
