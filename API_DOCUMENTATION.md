# AlgoKG API接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API版本**: `v1`
- **认证方式**: JWT Token (可选)
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
  "status": "success",
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 错误响应
```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "error_message": "错误描述",
  "details": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 1. 问答系统API

### 1.1 智能问答

#### POST `/api/v1/qa/query`

**描述**: 处理用户的智能问答请求

**请求体**:
```json
{
  "query": "请解释动态规划的概念",
  "session_id": "session_123",
  "query_type": "concept_explanation",
  "difficulty": "中等",
  "context": [
    {
      "role": "user",
      "content": "之前的对话内容"
    }
  ]
}
```

**响应**:
```json
{
  "response_id": "resp_123",
  "query": "请解释动态规划的概念",
  "intent": "concept_explanation",
  "entities": ["动态规划"],
  "integrated_response": "动态规划是一种算法设计技术...",
  "reasoning_steps": [
    {
      "step_id": "step_1",
      "title": "概念识别",
      "content": "识别到用户询问动态规划概念",
      "timestamp": "2024-01-01T00:00:01Z"
    }
  ],
  "recommendations": [
    {
      "type": "problem",
      "title": "斐波那契数列",
      "description": "经典动态规划入门题目",
      "difficulty": "简单",
      "tags": ["动态规划", "递推"],
      "similarity_score": 0.95
    }
  ],
  "graph_data": {
    "nodes": [],
    "edges": [],
    "center_node": "动态规划",
    "layout_type": "force"
  },
  "status": "completed",
  "processing_time": 2.5,
  "metadata": {
    "model_version": "qwen-turbo",
    "confidence": 0.92
  }
}
```

### 1.2 流式问答

#### POST `/api/v1/qa/stream`

**描述**: 流式返回问答结果，实时展示推理过程

**请求体**: 同上

**响应**: Server-Sent Events (SSE)
```
data: {"type": "reasoning_step", "content": {"step_id": "step_1", "title": "意图识别", "content": "正在分析用户意图..."}, "timestamp": "2024-01-01T00:00:01Z"}

data: {"type": "reasoning_step", "content": {"step_id": "step_2", "title": "实体提取", "content": "提取到实体: 动态规划"}, "timestamp": "2024-01-01T00:00:02Z"}

data: {"type": "final_response", "content": {...}, "timestamp": "2024-01-01T00:00:05Z"}

data: [DONE]
```

### 1.3 相似题目推荐

#### POST `/api/v1/qa/similar-problems`

**描述**: 根据题目标题获取相似题目推荐

**请求体**:
```json
{
  "problem_title": "两数之和",
  "limit": 10,
  "difficulty_filter": ["简单", "中等"],
  "tag_filter": ["数组", "哈希表"]
}
```

**响应**:
```json
{
  "query_problem": {
    "title": "两数之和",
    "difficulty": "简单",
    "tags": ["数组", "哈希表"]
  },
  "similar_problems": [
    {
      "title": "三数之和",
      "difficulty": "中等",
      "tags": ["数组", "双指针"],
      "similarity_score": 0.85,
      "platform": "LeetCode",
      "problem_id": "15"
    }
  ],
  "total_count": 25,
  "processing_time": 0.5
}
```

### 1.4 概念链接

#### POST `/api/v1/qa/concept-link`

**描述**: 获取概念的相关链接和扩展信息

**请求体**:
```json
{
  "concept": "动态规划",
  "link_types": ["related_concepts", "example_problems", "learning_resources"]
}
```

**响应**:
```json
{
  "concept": "动态规划",
  "related_concepts": [
    {
      "name": "递归",
      "relationship": "基础概念",
      "description": "动态规划的基础是递归思想"
    }
  ],
  "example_problems": [
    {
      "title": "爬楼梯",
      "difficulty": "简单",
      "description": "经典的动态规划入门题目"
    }
  ],
  "learning_resources": [
    {
      "type": "article",
      "title": "动态规划详解",
      "url": "https://example.com/dp-guide"
    }
  ]
}
```

### 1.5 用户反馈

#### POST `/api/v1/qa/feedback`

**描述**: 提交用户对回答的反馈

**请求体**:
```json
{
  "response_id": "resp_123",
  "rating": 5,
  "feedback_type": "helpful",
  "comment": "回答很详细，帮助很大",
  "suggestions": ["可以增加更多例子"]
}
```

**响应**:
```json
{
  "feedback_id": "feedback_456",
  "status": "received",
  "message": "感谢您的反馈"
}
```

## 2. 知识图谱API

### 2.1 图谱查询

#### POST `/api/v1/graph/query`

**描述**: 查询知识图谱数据

**请求体**:
```json
{
  "entity_name": "动态规划",
  "entity_type": "Algorithm",
  "depth": 2,
  "limit": 50,
  "layout_type": "force"
}
```

**响应**:
```json
{
  "nodes": [
    {
      "id": "algorithm_dp",
      "label": "动态规划",
      "type": "Algorithm",
      "properties": {
        "description": "一种算法设计技术",
        "time_complexity": "O(n)",
        "space_complexity": "O(n)",
        "is_center": true
      }
    }
  ],
  "edges": [
    {
      "source": "algorithm_dp",
      "target": "problem_fibonacci",
      "relationship": "APPLIES_TO",
      "properties": {
        "strength": 0.9,
        "description": "动态规划应用于斐波那契数列"
      }
    }
  ],
  "center_node": "algorithm_dp",
  "layout_type": "force",
  "metadata": {
    "total_nodes": 25,
    "total_edges": 40,
    "query_time": 0.3
  }
}
```

### 2.2 统一图谱查询

#### POST `/api/v1/graph/unified/query`

**描述**: 多数据源融合的图谱查询

**请求体**:
```json
{
  "entity_name": "二分查找",
  "entity_type": "Algorithm",
  "depth": 2,
  "limit": 50,
  "data_sources": ["neo4j", "embedding", "static"]
}
```

**响应**: 同上，但包含多数据源的融合结果

### 2.3 节点详情

#### GET `/api/v1/graph/node/{node_id}/details`

**描述**: 获取图谱节点的详细信息

**路径参数**:
- `node_id`: 节点ID

**查询参数**:
- `node_type`: 节点类型 (required)

**响应**:
```json
{
  "node_id": "problem_two_sum",
  "node_type": "Problem",
  "basic_info": {
    "title": "两数之和",
    "difficulty": "简单",
    "platform": "LeetCode",
    "problem_id": "1"
  },
  "detailed_info": {
    "description": "给定一个整数数组...",
    "solution_approach": "使用哈希表...",
    "time_complexity": "O(n)",
    "space_complexity": "O(n)"
  },
  "relationships": [
    {
      "target_node": "algorithm_hash_table",
      "relationship": "USES_ALGORITHM",
      "strength": 0.9
    }
  ],
  "statistics": {
    "view_count": 1000,
    "like_count": 850,
    "difficulty_rating": 4.2
  }
}
```

### 2.4 题目详情

#### GET `/api/v1/graph/problem/{problem_title}/detail`

**描述**: 获取题目的完整详细信息

**路径参数**:
- `problem_title`: 题目标题

**响应**:
```json
{
  "problem_info": {
    "title": "两数之和",
    "description": "给定一个整数数组 nums 和一个整数目标值 target...",
    "difficulty": "简单",
    "platform": "LeetCode",
    "problem_id": "1",
    "tags": ["数组", "哈希表"],
    "constraints": ["2 <= nums.length <= 10^4"],
    "examples": [
      {
        "input": "nums = [2,7,11,15], target = 9",
        "output": "[0,1]",
        "explanation": "因为 nums[0] + nums[1] == 9"
      }
    ]
  },
  "similar_problems": [
    {
      "title": "三数之和",
      "similarity_score": 0.75,
      "difficulty": "中等"
    }
  ],
  "algorithms": [
    {
      "name": "哈希表",
      "description": "使用哈希表存储数组元素",
      "time_complexity": "O(n)"
    }
  ],
  "data_structures": [
    {
      "name": "数组",
      "description": "输入数据结构"
    }
  ],
  "solution_templates": [
    {
      "language": "python",
      "template": "def twoSum(self, nums, target):\n    # Your code here\n    pass"
    }
  ]
}
```

### 2.5 概念图谱

#### GET `/api/v1/graph/concept/{concept_name}`

**描述**: 获取概念相关的图谱数据

**路径参数**:
- `concept_name`: 概念名称

**查询参数**:
- `depth`: 查询深度 (default: 2)
- `limit`: 结果限制 (default: 50)

**响应**: 同图谱查询响应格式

## 3. 系统管理API

### 3.1 健康检查

#### GET `/health`

**描述**: 系统健康状态检查

**响应**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "neo4j": "healthy - connected",
    "redis": "healthy - connected",
    "qwen_api": "healthy - api_key_valid",
    "recommendation_system": "healthy - model_loaded"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "uptime": 3600
}
```

### 3.2 系统信息

#### GET `/`

**描述**: 获取系统基本信息

**响应**:
```json
{
  "message": "欢迎使用AlgoKG智能问答系统",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "features": [
    "智能问答",
    "知识图谱可视化",
    "个性化推荐",
    "实时推理展示"
  ]
}
```

## 4. 错误码说明

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| INVALID_REQUEST | 400 | 请求参数无效 |
| UNAUTHORIZED | 401 | 未授权访问 |
| FORBIDDEN | 403 | 禁止访问 |
| NOT_FOUND | 404 | 资源未找到 |
| METHOD_NOT_ALLOWED | 405 | 方法不允许 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| INTERNAL_SERVER_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |
| NEO4J_CONNECTION_ERROR | 500 | Neo4j连接错误 |
| REDIS_CONNECTION_ERROR | 500 | Redis连接错误 |
| LLM_API_ERROR | 500 | 大语言模型API错误 |
| RECOMMENDATION_ERROR | 500 | 推荐系统错误 |

## 5. 使用示例

### JavaScript/TypeScript
```typescript
// 智能问答
const response = await fetch('/api/v1/qa/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: '请解释快速排序算法',
    session_id: 'session_123'
  })
});

const data = await response.json();
console.log(data.integrated_response);

// 流式问答
const eventSource = new EventSource('/api/v1/qa/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'reasoning_step') {
    console.log('推理步骤:', data.content);
  } else if (data.type === 'final_response') {
    console.log('最终回答:', data.content);
  }
};
```

### Python
```python
import requests
import json

# 智能问答
response = requests.post('http://localhost:8000/api/v1/qa/query', 
  json={
    'query': '请解释快速排序算法',
    'session_id': 'session_123'
  }
)

data = response.json()
print(data['integrated_response'])

# 图谱查询
response = requests.post('http://localhost:8000/api/v1/graph/query',
  json={
    'entity_name': '快速排序',
    'entity_type': 'Algorithm',
    'depth': 2,
    'limit': 50
  }
)

graph_data = response.json()
print(f"节点数: {len(graph_data['nodes'])}")
print(f"边数: {len(graph_data['edges'])}")
```

## 6. 认证和授权 (可选)

### JWT Token使用
```http
Authorization: Bearer <jwt_token>
```

### 获取Token
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}
```

### 刷新Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

## 7. 限流和配额

- **请求频率限制**: 100 requests/minute per IP
- **流式请求限制**: 10 concurrent streams per session
- **查询复杂度限制**: 图谱查询深度最大为5层
- **响应大小限制**: 单次响应最大10MB

## 8. WebSocket API (可选)

### 连接
```
ws://localhost:8000/ws/chat/{session_id}
```

### 消息格式
```json
{
  "type": "query",
  "data": {
    "query": "请解释动态规划",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

这个API文档提供了完整的接口说明，包括请求格式、响应格式、错误处理和使用示例，便于前端开发和第三方集成。
