# AlgoKG项目文件结构说明

## 项目根目录结构

```
algokg_platform/
├── web_app/                          # Web应用主目录
│   ├── frontend/                     # React前端应用
│   │   ├── src/
│   │   │   ├── components/           # React组件
│   │   │   │   ├── chat/            # 聊天相关组件
│   │   │   │   │   ├── MessageItem.tsx         # 消息项组件
│   │   │   │   │   ├── RecommendationCard.tsx  # 推荐卡片组件
│   │   │   │   │   └── ChatContainer.tsx       # 聊天容器组件
│   │   │   │   ├── common/          # 通用组件
│   │   │   │   │   ├── QueryInput.tsx          # 查询输入组件
│   │   │   │   │   ├── SearchHistory.tsx       # 搜索历史组件
│   │   │   │   │   ├── FavoriteManager.tsx     # 收藏管理组件
│   │   │   │   │   └── GraphExporter.tsx       # 图谱导出组件
│   │   │   │   ├── graph/           # 图谱可视化组件
│   │   │   │   │   ├── EnhancedGraphVisualization.tsx  # 增强图谱可视化
│   │   │   │   │   ├── GraphControls.tsx               # 图谱控制组件
│   │   │   │   │   └── NodeDetailPanel.tsx             # 节点详情面板
│   │   │   │   └── demo/            # 演示组件
│   │   │   ├── pages/               # 页面组件
│   │   │   │   ├── ChatPage.tsx                # 聊天页面
│   │   │   │   ├── UnifiedGraphPage.tsx        # 统一图谱页面
│   │   │   │   └── AlgorithmVisualizationPage.tsx  # 算法可视化页面
│   │   │   ├── store/               # 状态管理
│   │   │   │   ├── appStore.ts                 # 应用状态
│   │   │   │   └── graphStore.ts               # 图谱状态
│   │   │   ├── hooks/               # 自定义Hooks
│   │   │   │   ├── useTheme.ts                 # 主题Hook
│   │   │   │   ├── useWebSocket.ts             # WebSocket Hook
│   │   │   │   └── useGraphData.ts             # 图谱数据Hook
│   │   │   ├── services/            # 服务层
│   │   │   │   ├── apiService.ts               # API服务
│   │   │   │   ├── websocketService.ts         # WebSocket服务
│   │   │   │   └── graphService.ts             # 图谱服务
│   │   │   ├── types/               # TypeScript类型定义
│   │   │   │   ├── api.ts                      # API类型
│   │   │   │   ├── graph.ts                    # 图谱类型
│   │   │   │   └── chat.ts                     # 聊天类型
│   │   │   ├── utils/               # 工具函数
│   │   │   │   ├── formatters.ts               # 格式化工具
│   │   │   │   ├── validators.ts               # 验证工具
│   │   │   │   └── constants.ts                # 常量定义
│   │   │   ├── App.tsx              # 主应用组件
│   │   │   ├── App.css              # 全局样式
│   │   │   └── index.tsx            # 应用入口
│   │   ├── public/                  # 静态资源
│   │   ├── package.json             # 前端依赖配置
│   │   └── tsconfig.json            # TypeScript配置
│   └── backend/                     # FastAPI后端应用
│       ├── app/
│       │   ├── api/                 # API路由
│       │   │   ├── qa.py                       # 问答API
│       │   │   └── graph.py                    # 图谱API
│       │   ├── core/                # 核心模块
│       │   │   ├── config.py                   # 配置管理
│       │   │   ├── deps.py                     # 依赖注入
│       │   │   └── mock_qa.py                  # 模拟QA系统
│       │   ├── models/              # 数据模型
│       │   │   ├── request.py                  # 请求模型
│       │   │   ├── response.py                 # 响应模型
│       │   │   └── __init__.py                 # 模型导出
│       │   ├── services/            # 业务服务
│       │   │   ├── qa_service.py               # 问答服务
│       │   │   ├── unified_graph_service.py    # 统一图谱服务
│       │   │   ├── enhanced_problem_service.py # 增强题目服务
│       │   │   └── tag_service.py              # 标签服务
│       │   └── main.py              # FastAPI应用入口
│       ├── requirements.txt         # Python依赖
│       └── Dockerfile              # Docker配置
├── qa/                              # 问答系统核心
│   ├── multi_agent_qa.py           # 多智能体问答系统
│   ├── embedding_qa.py             # 嵌入向量问答系统
│   ├── enhanced_recommendation.py   # 增强推荐系统
│   └── qwen_client.py              # 通义千问客户端
├── backend/                         # 后端核心模块
│   └── neo4j_loader/               # Neo4j数据加载器
│       ├── neo4j_api.py                        # Neo4j API
│       ├── extractor2_modified.py              # 修改版提取器
│       └── neo4j_knowledge_graph.py            # Neo4j知识图谱
├── gnn_model/                       # 图神经网络模型
│   ├── train_multitask_gat2v.py    # 多任务GAT模型训练
│   ├── model_architecture.py       # 模型架构定义
│   └── data_preprocessing.py       # 数据预处理
├── extractors/                      # 数据提取器
│   ├── extract_knowledgePoint.py   # 知识点提取器
│   ├── batch_processor.py          # 批处理器
│   └── text_preprocessor.py        # 文本预处理器
├── data/                           # 数据目录
│   ├── raw/                        # 原始数据
│   │   ├── entity2id.json                     # 实体ID映射
│   │   ├── entity_id_to_title.json            # ID到标题映射
│   │   ├── problem_id_to_tags.json            # 题目标签映射
│   │   └── problem_extration/                 # 题目提取数据
│   ├── processed/                  # 处理后数据
│   └── embeddings/                 # 嵌入向量数据
├── models/                         # 模型文件
│   ├── ensemble_gnn_embedding.pt   # 集成GNN嵌入模型
│   └── checkpoints/                # 模型检查点
├── docs/                           # 文档目录
│   ├── api/                        # API文档
│   ├── deployment/                 # 部署文档
│   └── development/                # 开发文档
├── scripts/                        # 脚本目录
│   ├── setup/                      # 安装脚本
│   ├── data_processing/            # 数据处理脚本
│   └── deployment/                 # 部署脚本
├── tests/                          # 测试目录
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   └── e2e/                        # 端到端测试
├── docker-compose.yml              # Docker Compose配置
├── requirements.txt                # Python依赖
├── package.json                    # Node.js依赖
├── README.md                       # 项目说明
├── PROJECT_DOCUMENTATION.md        # 详细项目文档
└── PROJECT_STRUCTURE.md            # 项目结构说明
```

## 核心文件说明

### 前端核心文件

#### 1. 主应用文件
- **`web_app/frontend/src/App.tsx`**: 主应用组件，包含路由、布局、状态管理
- **`web_app/frontend/src/App.css`**: 全局样式，包含主题、布局、动画等样式定义
- **`web_app/frontend/src/index.tsx`**: 应用入口文件，React应用挂载点

#### 2. 组件文件
- **`components/common/QueryInput.tsx`**: 现代化查询输入组件，ChatGPT风格界面
- **`components/chat/MessageItem.tsx`**: 消息显示组件，支持推理步骤展示
- **`components/graph/EnhancedGraphVisualization.tsx`**: 增强图谱可视化组件
- **`components/common/SearchHistory.tsx`**: 搜索历史管理组件
- **`components/common/FavoriteManager.tsx`**: 收藏功能管理组件

#### 3. 状态管理
- **`store/appStore.ts`**: 全局应用状态管理，使用Zustand
- **`hooks/useTheme.ts`**: 主题切换Hook，支持浅色/深色主题

#### 4. 服务层
- **`services/apiService.ts`**: API调用服务，封装所有后端接口
- **`services/websocketService.ts`**: WebSocket服务，处理实时通信

### 后端核心文件

#### 1. 应用入口
- **`web_app/backend/app/main.py`**: FastAPI应用主文件，包含中间件、路由、异常处理

#### 2. API路由
- **`app/api/qa.py`**: 问答API路由，处理智能问答请求
- **`app/api/graph.py`**: 图谱API路由，处理知识图谱查询

#### 3. 数据模型
- **`app/models/request.py`**: 请求数据模型定义
- **`app/models/response.py`**: 响应数据模型定义

#### 4. 业务服务
- **`app/services/qa_service.py`**: 问答业务服务
- **`app/services/unified_graph_service.py`**: 统一图谱服务

#### 5. 核心配置
- **`app/core/config.py`**: 应用配置管理
- **`app/core/deps.py`**: 依赖注入管理

### AI/ML核心文件

#### 1. 多智能体系统
- **`qa/multi_agent_qa.py`**: 多智能体协作问答系统核心实现
- **`qa/embedding_qa.py`**: 基于嵌入向量的推荐系统
- **`qa/enhanced_recommendation.py`**: 增强推荐服务

#### 2. 图神经网络
- **`gnn_model/train_multitask_gat2v.py`**: 多任务GAT模型训练脚本
- **`gnn_model/model_architecture.py`**: 模型架构定义

#### 3. 数据提取
- **`extractors/extract_knowledgePoint.py`**: 知识点提取器
- **`backend/neo4j_loader/extractor2_modified.py`**: 批量知识图谱构建器

#### 4. 数据库接口
- **`backend/neo4j_loader/neo4j_api.py`**: Neo4j数据库API接口
- **`backend/neo4j_loader/neo4j_knowledge_graph.py`**: Neo4j知识图谱操作类

### 配置文件

#### 1. 前端配置
- **`web_app/frontend/package.json`**: 前端依赖和脚本配置
- **`web_app/frontend/tsconfig.json`**: TypeScript编译配置

#### 2. 后端配置
- **`web_app/backend/requirements.txt`**: Python依赖配置
- **`web_app/backend/Dockerfile`**: 后端Docker配置

#### 3. 部署配置
- **`docker-compose.yml`**: Docker Compose服务编排配置
- **`requirements.txt`**: 项目根目录Python依赖

### 数据文件

#### 1. 模型文件
- **`models/ensemble_gnn_embedding.pt`**: 训练好的GNN嵌入模型

#### 2. 数据映射文件
- **`data/raw/entity2id.json`**: 实体到ID的映射
- **`data/raw/entity_id_to_title.json`**: ID到标题的映射
- **`data/raw/problem_id_to_tags.json`**: 题目ID到标签的映射

#### 3. 原始数据
- **`data/raw/problem_extration/`**: 提取的题目数据目录

## 文件依赖关系

### 前端依赖链
```
App.tsx
├── components/chat/MessageItem.tsx
├── components/common/QueryInput.tsx
│   ├── components/common/SearchHistory.tsx
│   └── components/common/FavoriteManager.tsx
├── components/graph/EnhancedGraphVisualization.tsx
├── store/appStore.ts
├── hooks/useTheme.ts
└── services/apiService.ts
```

### 后端依赖链
```
main.py
├── api/qa.py
│   └── services/qa_service.py
│       └── qa/multi_agent_qa.py
│           ├── qa/embedding_qa.py
│           └── backend/neo4j_loader/neo4j_api.py
├── api/graph.py
│   └── services/unified_graph_service.py
│       └── backend/neo4j_loader/neo4j_api.py
└── core/deps.py
    ├── core/config.py
    └── qa/enhanced_recommendation.py
```

### 数据流依赖
```
原始题目数据
├── extractors/extract_knowledgePoint.py
├── backend/neo4j_loader/extractor2_modified.py
├── Neo4j数据库
├── gnn_model/train_multitask_gat2v.py
├── models/ensemble_gnn_embedding.pt
└── qa/embedding_qa.py
```

## 开发环境设置

### 前端开发
```bash
cd web_app/frontend
npm install
npm start
```

### 后端开发
```bash
cd web_app/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 数据库设置
```bash
# 启动Neo4j
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/123456 neo4j:5.0

# 启动Redis
docker run -p 6379:6379 redis:7-alpine
```

### 完整环境启动
```bash
docker-compose up -d
```

这个项目结构体现了现代全栈应用的最佳实践，包括前后端分离、微服务架构、容器化部署等特点。
