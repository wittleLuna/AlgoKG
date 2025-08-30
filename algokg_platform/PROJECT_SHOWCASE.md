# AlgoKG 智能知识图谱与问答平台 - 展示文档

## 1. 项目定位与价值
- **目标**: 以知识图谱为核心，面向算法学习与练习的智能助手。
- **核心能力**: 智能问答、多智能体推理、知识图谱可视化、图神经网络个性化推荐。
- **受众**: 学生、竞赛选手、工程师、教育机构。

## 2. 一图看懂架构
```mermaid
graph TD
  A[前端 React + TS] -->|REST/SSE| B[FastAPI 后端]
  B --> C[多智能体问答引擎]
  B --> D[统一图谱服务]
  B --> E[GNN 推荐服务]
  D --> F[(Neo4j 图数据库)]
  E --> G[(GNN 嵌入模型)]
  C --> H[LLM 推理(Qwen/本地模型)]
  B --> I[(Redis/缓存 可选)]
```

- **前端**: React + TypeScript + Ant Design，图谱可视化（D3/Vis）、聊天交互、主题切换。
- **后端**: FastAPI + Pydantic，API 路由划分清晰，SSE 流式输出推理步骤。
- **数据与模型**: Neo4j 存储实体/关系；PyTorch Geometric 训练 GATv2；融合结构化/标签/文本特征。

## 3. 关键功能展示
- **智能问答（SSE流式）**
  - 多智能体协作：意图识别 → 实体抽取 → 图谱查询 → 推荐融合 → LLM 生成。
  - 前端展示“推理步骤”与“最终答案”，支持上下文会话与反馈。
- **知识图谱可视化**
  - 统一图谱查询：融合 Neo4j、Embedding 和静态知识。
  - 交互操作：节点高亮、拖拽、缩放、布局切换。
- **相似题目与个性化推荐**
  - 多塔 GNN：结构特征 + 标签特征 + 文本语义（BERT）融合。
  - 集成模型：多模型投票/加权提升召回与排序准确率。

## 4. 核心技术栈（精简版）
- **前端**: React 18, TypeScript, Ant Design, Zustand, React Query, D3/Vis, Styled Components, Framer Motion。
- **后端**: FastAPI, Pydantic, asyncio/aiohttp, Uvicorn。
- **数据库/缓存**: Neo4j 5.x, Redis(可选)。
- **AI/ML**: PyTorch, PyTorch Geometric, GATv2, BERT/Transformers, scikit-learn。
- **工程化**: Docker/Compose，ESLint/Prettier/Black，GitHub Actions(可拓展)。

更多详见 `TECH_STACK.md` 与 `PROJECT_SUMMARY.md`。

## 5. 模块与代码落点
- **问答引擎**: `qa/multi_agent_qa.py`、`qa/embedding_qa.py`
- **图谱服务**: `web_app/backend/app/services/unified_graph_service.py`
- **图谱构建**: `backend/neo4j_loader/extractor2_modified.py`、`backend/neo4j_loader/neo4j_api.py`
- **GNN 训练**: `gnn_model/train_multitask_gat2v.py`
- **前端界面**: `web_app/frontend/src/App.tsx` 与 `components/*`
- **API 文档**: `API_DOCUMENTATION.md`

## 6. 端到端数据流（从用户到答案）
1) 用户在前端输入问题
2) FastAPI 接收请求并启动流式会话（SSE）
3) 多智能体流水线：意图识别 → 实体抽取 → 图谱查询/推荐 → LLM 生成
4) 统一图谱服务拼装图数据与上下文，返回前端显示
5) 推荐服务返回相似题目/学习路径，前端联动展示

## 7. 典型交互演示大纲（用于PPT）
- **Demo 1: 概念讲解**
  - 输入: “请解释动态规划” → 实时显示推理步骤 → 图谱节点联动 → 关键题目推荐。
- **Demo 2: 题目相似推荐**
  - 输入题目标题 → 返回相似题清单与解释 → 一键跳转知识点与解法。
- **Demo 3: 图谱探索**
  - 搜索实体 → 力导布局、层次布局切换 → 节点详情与关系强度展示。

## 8. 性能与指标（可在演示中引用）
- API 平均响应 < 2s；图谱查询 < 500ms（常见查询）。
- 推荐 Hit@10 > 85%（示例值）；实体识别 F1 > 90%（示例值）。
- 前端交互 60fps（常见规模图数据）。

## 9. 部署与上线
- 开发环境：`docker-compose up -d` 一键启动（见 `web_app/docker-compose.yml`）。
- 生产环境：Kubernetes + Nginx Ingress + Prometheus/Grafana（详见 `DEPLOYMENT_GUIDE.md`）。
- 访问入口：前端 3000，后端 8000，Neo4j 7474。

## 10. 差异化亮点（建议在PPT重点呈现）
- **多智能体协作推理**：可视化思考过程与责任分工。
- **统一图谱融合**：一处接入，多源协同（Neo4j/Embedding/静态知识）。
- **多塔 GNN + 集成**：结构、标签、文本三类特征深度融合。
- **可视化友好**：从聊天到图谱的一体化体验。

## 11. 风险与改进方向（Roadmap 摘要）
- 提升大规模图谱的前端渲染性能与抽样策略。
- 增强在线增量图谱构建与数据质量校验。
- 扩展更多 LLM 与私有化部署选择。
- 完善 A/B 测试与可观测性（Tracing/Profiling）。

## 12. 附录
- 主要接口参见 `API_DOCUMENTATION.md`
- 参考部署 `DEPLOYMENT_GUIDE.md`
- 代码结构 `PROJECT_STRUCTURE.md`
