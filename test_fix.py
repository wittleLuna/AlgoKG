#!/usr/bin/env python3
import requests
import urllib.parse

def test_datastructure_fix():
    """测试修复后的数据结构节点"""
    node_id = 'neo4j_数组'
    node_type = 'DataStructure'
    encoded_id = urllib.parse.quote(node_id, safe='')
    url = f'http://localhost:8000/api/v1/graph/unified/node/{encoded_id}/details?node_type={node_type}'

    print('🔧 测试修复后的数据结构节点...')
    print(f'URL: {url}')

    try:
        response = requests.get(url, timeout=10)
        print(f'状态码: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                print(f'❌ 错误: {data["error"]}')
            else:
                print('✅ 成功获取数据')
                print(f'字段: {list(data.keys())}')
                if 'basic_info' in data:
                    print(f'标题: {data["basic_info"].get("title", "N/A")}')
                    print(f'类型: {data["basic_info"].get("type", "N/A")}')
        else:
            print(f'❌ HTTP错误: {response.status_code}')
            
    except Exception as e:
        print(f'❌ 请求失败: {e}')

if __name__ == "__main__":
    test_datastructure_fix()
