#!/usr/bin/env python3
import requests
import urllib.parse

def test_specific_node_id():
    """测试特定的节点ID"""
    node_id = 'node_problem_AP_103fc0d4'
    node_type = 'Problem'
    encoded_id = urllib.parse.quote(node_id, safe='')
    url = f'http://localhost:8000/api/v1/graph/unified/node/{encoded_id}/details?node_type={node_type}'

    print('🔧 测试特定节点ID...')
    print(f'节点ID: {node_id}')
    print(f'节点类型: {node_type}')
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
                    print(f'平台: {data["basic_info"].get("platform", "N/A")}')
                    print(f'分类: {data["basic_info"].get("category", "N/A")}')
                    
                print(f'算法数量: {len(data.get("algorithms", []))}')
                print(f'数据结构数量: {len(data.get("data_structures", []))}')
                print(f'技巧数量: {len(data.get("techniques", []))}')
                print(f'解决方案数量: {len(data.get("solutions", []))}')
        else:
            print(f'❌ HTTP错误: {response.status_code}')
            print(f'错误内容: {response.text}')
            
    except Exception as e:
        print(f'❌ 请求失败: {e}')

def test_element_id_query():
    """直接测试element_id查询"""
    print(f'\n🔍 测试element_id查询...')
    
    # 测试通过element_id查询
    element_id = 'AP_103fc0d4'
    
    try:
        import sys
        sys.path.append('web_app/backend')
        from app.core.database import get_neo4j_api
        
        neo4j_api = get_neo4j_api()
        
        with neo4j_api.driver.session() as session:
            query = """
            MATCH (p:Problem)
            WHERE elementId(p) = $element_id
            RETURN p.title as title, p.difficulty as difficulty, p.platform as platform
            """
            result = session.run(query, element_id=element_id).single()
            
            if result:
                print(f'✅ 找到题目:')
                print(f'  标题: {result["title"]}')
                print(f'  难度: {result["difficulty"]}')
                print(f'  平台: {result["platform"]}')
            else:
                print(f'❌ 未找到element_id: {element_id}')
                
                # 尝试查询所有题目的element_id
                print(f'\n🔍 查询前5个题目的element_id...')
                query2 = """
                MATCH (p:Problem)
                RETURN p.title as title, elementId(p) as element_id
                LIMIT 5
                """
                results = session.run(query2)
                for record in results:
                    print(f'  {record["title"]} -> {record["element_id"]}')
                    
    except Exception as e:
        print(f'❌ 直接查询失败: {e}')

if __name__ == "__main__":
    test_specific_node_id()
    test_element_id_query()
