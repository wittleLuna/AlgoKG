# AlgoKG算法知识图谱平台技术架构

## 架构总览

AlgoKG平台是一个集算法学习、智能问答、知识图谱、智能推荐、算法可视化于一体的综合性平台。平台采用分层架构设计，融合了知识图谱(KG)、大语言模型(LLM)、图神经网络(GNN)等先进技术，实现前后端分离的现代化架构。

### 核心设计理念
- **分层架构**：数据源层 → 数据处理层 → 存储层 → AI模型层 → 服务层 → API层 → 前端层
- **混合智能**：KG+LLM+GNN协同，实现知识推理与智能问答
- **容器化部署**：Docker + Docker Compose，支持一键部署
- **模块化设计**：各功能模块独立，便于维护和扩展

---

## 技术架构分层详解

### 一、数据源层 (Data Source Layer)

数据源层是平台的基础，提供原始数据和半结构化数据。

#### 1.1 结构化数据源
- **算法题目数据**：`data/raw/`、`data/processed/`
  - 题目描述、难度标签、分类信息
  - 算法标签、数据结构标签
  - 题目间的关系数据
- **用户行为数据**：`web_app/backend/data/*.db`
  - 用户笔记、学习记录
  - 答题历史、偏好数据

#### 1.2 非结构化数据源
- **算法知识点文本**：`data/programmercarl_articles/`
  - 算法原理、实现方法
  - 复杂度分析、应用场景
- **用户上传内容**：笔记、代码片段
- **外部API数据**：算法竞赛平台数据

#### 1.3 模型产物数据
- **GNN训练结果**：`models/*.pt`
  - 实体嵌入向量
  - 图神经网络模型权重
- **特征索引数据**：`data/gnn/`
  - 预计算的相似度矩阵
  - 推荐系统特征

---

### 二、数据处理层 (Data Processing Layer)

数据处理层负责数据的抽取、转换、加载和特征工程。

#### 2.1 实体关系抽取
- **知识点抽取器**：`extractors/extract_knowledgePoint.py`
  - 从算法文本中抽取知识点实体
  - 识别算法、数据结构、技术概念
- **题目实体抽取器**：`extractors/extract_problem_entity.py`
  - 从题目描述中抽取算法标签
  - 建立题目与算法的关联关系
- **关系抽取**：识别实体间的依赖、相似、包含关系

#### 2.2 数据转换与清洗
- **文本预处理**：`extractors/preprocess_latex.py`
  - LaTeX公式标准化
  - 特殊字符处理
- **数据标准化**：统一数据格式和编码
- **质量检查**：数据完整性验证

#### 2.3 特征工程
- **嵌入向量生成**：`qa/embedding_qa.py`
  - 文本向量化
  - 标签权重计算(IDF)
  - 混合特征构建

---

### 三、数据存储层 (Data Storage Layer)

数据存储层提供多种存储方案，满足不同数据类型的需求。

#### 3.1 图数据库 (Neo4j)
- **主知识库**：`backend/neo4j_loader/neo4j_api.py`
  - 实体类型：Problem、Algorithm、DataStructure、Technique
  - 关系类型：USES_ALGORITHM、SIMILAR_TO、PREREQUISITE_OF
  - 支持复杂图查询和路径分析

#### 3.2 关系数据库 (SQLite)
- **应用数据**：`web_app/backend/data/*.db`
  - 用户信息、认证数据
  - 笔记内容、学习记录
  - 系统配置、日志数据

#### 3.3 文件存储
- **模型文件**：`models/*.pt`
  - GNN模型权重
  - 嵌入向量文件
- **配置文件**：JSON格式的配置和模式文件
- **日志文件**：系统运行日志

---

### 四、AI模型层 (AI/ML Model Layer)

AI模型层是平台的核心智能引擎，集成了多种先进的AI技术。

#### 4.1 图神经网络 (GNN)
- **多任务GATv2**：`gnn_model/train_multitask_gat2v.py`
  - 图注意力网络，学习节点表示
  - 多任务学习，同时优化多个目标
  - 支持实体相似度计算和关系预测

#### 4.2 推荐系统
- **混合推荐算法**：`qa/embedding_qa.py`
  - 嵌入相似度 + 标签权重混合
  - MMR多样性算法，避免推荐重复
  - 个性化学习路径推荐

#### 4.3 多智能体问答系统
- **多Agent架构**：`qa/multi_agent_qa.py`
  - Analyzer：问题分析和意图识别
  - KG Retriever：知识图谱检索
  - Concept Explainer：概念解释
  - Similar Finder：相似问题查找
  - Integrator：答案整合和推理

#### 4.4 大语言模型集成
- **LLM增强**：结合知识图谱的LLM问答
- **推理链生成**：结构化推理过程
- **答案解释**：详细的解题思路

---

### 五、服务层 (Service Layer)

服务层提供业务逻辑封装和核心服务能力。

#### 5.1 统一图谱服务
- **图谱数据服务**：`web_app/backend/app/services/unified_graph_service.py`
  - 融合Neo4j和推荐结果
  - 提供统一的图数据接口
  - 支持节点详情查询和关系分析

#### 5.2 笔记管理服务
- **笔记服务**：`web_app/backend/app/services/note_service.py`
  - 笔记上传和解析
  - 内容分析和实体抽取
  - 与知识图谱的集成

#### 5.3 增强推荐服务
- **推荐服务**：`web_app/backend/app/services/enhanced_recommendation_service.py`
  - 个性化推荐算法
  - 学习路径规划
  - 推荐理由生成

#### 5.4 核心基础服务
- **认证服务**：`web_app/backend/app/core/auth.py`
  - JWT认证机制
  - 用户权限管理
- **配置服务**：系统配置管理
- **依赖注入**：服务间依赖管理

---

### 六、API接口层 (API Interface Layer)

API接口层提供标准化的RESTful接口，支持前端和外部系统调用。

#### 6.1 图谱查询API
- **统一图谱接口**：`web_app/backend/app/api/graph.py`
  - 图谱数据查询
  - 节点详情获取
  - 相似关系检索

#### 6.2 问答系统API
- **智能问答接口**：多Agent问答服务
- **推荐接口**：个性化推荐API
- **笔记接口**：笔记管理API

#### 6.3 用户管理API
- **认证接口**：`web_app/backend/app/api/auth.py`
  - 用户注册登录
  - 权限验证
- **用户数据接口**：用户信息管理

#### 6.4 算法可视化API
- **可视化接口**：算法执行和可视化
- **数据接口**：图表数据提供

---

### 七、前端表现层 (Frontend Presentation Layer)

前端表现层基于React + TypeScript构建，提供现代化的用户界面。

#### 7.1 核心框架
- **React应用**：`web_app/frontend/src/`
- **TypeScript**：类型安全的开发
- **Ant Design**：企业级UI组件库

#### 7.2 图谱可视化组件
- **图谱组件**：`web_app/frontend/src/components/graph/`
  - GraphVisualization.tsx：基础图谱展示
  - EnhancedGraphVisualization.tsx：增强图谱功能
  - 支持交互式节点点击和关系探索

#### 7.3 算法可视化组件
- **算法可视化**：`web_app/frontend/src/components/visualization/`
  - AlgorithmVisualizer.tsx：算法执行可视化
  - 支持步骤控制和动画展示
  - 实时数据更新

#### 7.4 功能模块组件
- **问答模块**：`web_app/frontend/src/components/qa/`
  - 智能问答界面
  - 推理过程展示
- **推荐模块**：`web_app/frontend/src/components/recommendation/`
  - SmartRecommendationSystem.tsx：智能推荐系统
  - 学习路径展示
- **笔记模块**：`web_app/frontend/src/components/notes/`
  - 笔记管理界面
  - 内容编辑和分享
- **用户模块**：`web_app/frontend/src/components/user/`
  - 用户管理界面
  - 个人中心

#### 7.5 布局和路由
- **布局组件**：`web_app/frontend/src/components/layout/`
  - 响应式布局设计
  - 导航菜单管理
- **页面路由**：`web_app/frontend/src/pages/`
  - 统一图谱页面
  - 算法可视化页面
  - 问答和推荐页面

---

### 八、基础设施层 (Infrastructure Layer)

基础设施层提供部署、运维和监控支持。

#### 8.1 容器化部署
- **Docker配置**：
  - 后端Dockerfile：`web_app/backend/Dockerfile`
  - 前端Dockerfile：`web_app/frontend/Dockerfile`
  - 编排文件：`docker-compose.yml`

#### 8.2 开发工具
- **构建脚本**：`web_app/Makefile`
- **部署脚本**：`web_app/scripts/`
- **配置管理**：环境变量和配置文件

#### 8.3 依赖管理
- **后端依赖**：`requirements.txt`
- **前端依赖**：`package.json`
- **版本控制**：Git版本管理

---

## 关键技术选型

### 1. 图数据库：Neo4j
- **优势**：天然支持图关系建模，查询语言Cypher直观
- **应用**：知识图谱存储和查询，支持复杂路径分析

### 2. 图神经网络：GATv2
- **优势**：注意力机制，多任务学习能力
- **应用**：实体表示学习，相似度计算

### 3. 推荐算法：混合推荐 + MMR
- **优势**：结合内容特征和协同过滤，保证多样性
- **应用**：个性化题目推荐，学习路径规划

### 4. 前端技术栈：React + TypeScript + Ant Design
- **优势**：组件化开发，类型安全，企业级UI
- **应用**：现代化用户界面，交互式可视化

### 5. 后端框架：FastAPI
- **优势**：高性能，自动API文档，类型提示
- **应用**：RESTful API服务，异步处理

---

## 数据流向

### 1. 知识图谱构建流程
```
原始文本 → 实体抽取 → 关系抽取 → Neo4j存储 → 图神经网络训练 → 嵌入向量
```

### 2. 推荐系统流程
```
用户输入 → 特征提取 → 相似度计算 → MMR多样性 → 推荐结果 → 前端展示
```

### 3. 问答系统流程
```
用户问题 → 多Agent分析 → 知识图谱检索 → LLM生成 → 答案整合 → 结构化输出
```

### 4. 笔记集成流程
```
笔记上传 → 内容解析 → 实体抽取 → 图谱更新 → 统一查询 → 可视化展示
```

---

## 性能优化策略

### 1. 数据库优化
- Neo4j索引优化
- 查询缓存机制
- 读写分离

### 2. 前端优化
- 组件懒加载
- 虚拟滚动
- 图片压缩

### 3. 模型优化
- 模型量化
- 推理加速
- 批量处理

---

## 安全与权限

### 1. 认证授权
- JWT令牌认证
- 用户权限控制
- API访问限制

### 2. 数据安全
- 敏感数据加密
- 访问日志记录
- 数据备份策略

---

## 监控与运维

### 1. 日志管理
- 结构化日志
- 错误追踪
- 性能监控

### 2. 健康检查
- 服务健康检查
- 数据库连接监控
- 资源使用监控

---

## 扩展性设计

### 1. 水平扩展
- 微服务架构
- 负载均衡
- 数据库分片

### 2. 功能扩展
- 插件化设计
- API版本管理
- 模块化开发

---

## 总结

AlgoKG平台采用现代化的分层架构设计，集成了知识图谱、图神经网络、大语言模型等先进技术，实现了算法学习、智能问答、知识图谱、智能推荐、算法可视化的完整功能闭环。平台具有良好的可扩展性、可维护性和用户体验，为算法学习者提供了全方位的智能学习支持。
