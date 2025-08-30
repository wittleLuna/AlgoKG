#!/usr/bin/env python3
"""
调试节点详情API响应格式
"""

import requests
import json

def test_node_detail_api():
    """测试节点详情API"""
    print("🔍 测试节点详情API响应格式...")
    
    # 测试不同类型的节点
    test_nodes = [
        {
            "id": "neo4j_两两交换链表中的节点",
            "type": "Problem",
            "label": "两两交换链表中的节点"
        },
        {
            "id": "neo4j_回溯算法",
            "type": "Algorithm", 
            "label": "回溯算法"
        },
        {
            "id": "neo4j_链表",
            "type": "DataStructure",
            "label": "链表"
        }
    ]
    
    for i, node in enumerate(test_nodes, 1):
        print(f"\n{'='*60}")
        print(f"测试节点 {i}: {node['label']} ({node['type']})")
        print('='*60)
        
        url = f"http://localhost:8000/api/v1/graph/unified/node/{requests.utils.quote(node['id'])}/details?node_type={node['type']}"
        print(f"请求URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ API响应成功")
                print(f"响应数据结构:")
                
                # 检查顶级字段
                top_level_keys = list(data.keys())
                print(f"  顶级字段: {top_level_keys}")
                
                # 检查basic_info字段
                if 'basic_info' in data:
                    basic_info = data['basic_info']
                    print(f"  basic_info存在: ✅")
                    print(f"  basic_info类型: {type(basic_info)}")
                    if isinstance(basic_info, dict):
                        print(f"  basic_info字段: {list(basic_info.keys())}")
                        print(f"  title: {basic_info.get('title', 'N/A')}")
                        print(f"  type: {basic_info.get('type', 'N/A')}")
                        print(f"  difficulty: {basic_info.get('difficulty', 'N/A')}")
                        print(f"  platform: {basic_info.get('platform', 'N/A')}")
                    else:
                        print(f"  ❌ basic_info不是字典类型")
                else:
                    print(f"  ❌ basic_info字段不存在")
                
                # 检查其他字段
                other_fields = ['algorithms', 'data_structures', 'techniques', 'related_problems', 'complexity']
                for field in other_fields:
                    if field in data:
                        value = data[field]
                        if isinstance(value, list):
                            print(f"  {field}: 数组 (长度: {len(value)})")
                        elif isinstance(value, dict):
                            print(f"  {field}: 字典 (键: {list(value.keys())})")
                        else:
                            print(f"  {field}: {type(value)} = {value}")
                    else:
                        print(f"  {field}: 不存在")
                
                # 保存响应到文件
                filename = f"node_detail_response_{i}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  完整响应已保存到: {filename}")
                
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端服务")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

def check_api_consistency():
    """检查API一致性"""
    print(f"\n" + "="*60)
    print("检查API一致性")
    print("="*60)
    
    print("预期的数据结构:")
    expected_structure = {
        "basic_info": {
            "title": "string",
            "type": "string", 
            "description": "string (optional)",
            "difficulty": "string (optional)",
            "platform": "string (optional)",
            "category": "string (optional)"
        },
        "algorithms": "array (optional)",
        "data_structures": "array (optional)", 
        "techniques": "array (optional)",
        "related_problems": "array (optional)",
        "complexity": "object (optional)"
    }
    
    print(json.dumps(expected_structure, indent=2))
    
    print(f"\n如果API响应与预期不符，可能的问题:")
    print(f"1. 后端API返回的数据结构不一致")
    print(f"2. 某些节点类型的数据格式不同")
    print(f"3. API版本不匹配")
    print(f"4. 数据库中的数据格式异常")

def main():
    """主函数"""
    print("🚀 开始调试节点详情API...")
    
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
        return
    
    # 测试节点详情API
    test_node_detail_api()
    
    # 检查API一致性
    check_api_consistency()
    
    print(f"\n" + "="*60)
    print("🎯 调试总结")
    print("="*60)
    
    print("请检查以下内容:")
    print("1. 查看生成的JSON文件，确认API响应格式")
    print("2. 确认basic_info字段是否存在且格式正确")
    print("3. 检查不同节点类型的响应是否一致")
    print("4. 如果发现格式问题，需要修复后端API或前端适配")
    
    print(f"\n修复建议:")
    print("1. 如果basic_info不存在，前端需要添加兼容处理")
    print("2. 如果字段名不匹配，需要统一API规范")
    print("3. 如果数据类型不正确，需要修复数据转换逻辑")

if __name__ == "__main__":
    main()
