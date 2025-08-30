## 知识图谱 Embedding 策略

本文档系统性说明本项目在知识图谱（KG）中的节点/边表示学习（embedding）策略、训练与评测方法、推理与服务集成方案，以及落地运维与版本化规范。内容与现有代码和模型资源保持一致，便于研发、实验与上线协同。

---

### 1. 目标与约束

- 目标
  - 为节点（知识点、题目、概念、标签等）与关系（依赖、属于、相似、引用等）学习统一向量表示，支持下游检索、推荐、可视化、问答、推理增强。
  - 提供可扩展的多模态融合能力：结构（图拓扑）+ 文本（标题、正文、标签）+ 统计特征。
- 约束
  - 与现有数据管线与存储兼容：`neo4j_loader/neo4j_api.py`、Neo4j 实例、`data/raw/*.pt|*.json`。
  - 与现有模型与服务对齐：`gnn_model/train_multitask_gat2v.py`、`gnn_model/embedding_service.py`、`models/ensemble_gnn_*.pt*`。
  - 推理需满足在线延迟要求，支持批量离线生成与缓存。

---

### 2. 数据与特征

- 图结构
  - 节点类型：知识点、问题（题目）、概念/标签等。
  - 边类型：先修/依赖、同主题、相似、题目-知识点映射等。
  - 存储：Neo4j；训练样本在 `data/raw/edge_index_with_problem_edges.pt`。

- 文本特征
  - 题目标题/内容、知识点名称与描述、标签文本。
  - 现有嵌入：`data/raw/bert_title_features.pt`。

- 统计/结构特征
  - 度、Pagerank、聚类系数、类型 one-hot、入度/出度、时间信息（可选）。

- 映射/索引
  - `data/raw/entity2id.json`、`entity_id_to_title.json`、`problem_id_to_tags.json` 提供节点与文本、标签映射。

---

### 3. 模型策略总览

采用“结构 GNN + 文本语义 + 关系学习”的多任务/多目标联合建模，并通过模型集成提升稳健性。

- 结构学习（首选）：
  - GATv2/GAT：利用注意力聚合邻居信息，适合异质局部结构。
  - GraphSAGE（备选）：采样式聚合，适合扩展性与在线推理。

- 文本语义融合：
  - 预计算 BERT/SimCSE 等句向量（如 `bert_title_features.pt`），在节点层进行拼接或门控融合（MLP/Gate/Attention）。

- 关系学习：
  - 边预测（link prediction）作为主任务，辅以类型分类、标签多标签分类等辅助任务。

- 传统 KG 嵌入（补充/回退）：
  - TransE/DistMult/RotatE 可作为轻量替代或蒸馏教师模型，适合冷启动与资源受限场景。

- 集成策略：
  - `models/ensemble_gnn_model.pt.*`、`models/ensemble_gnn_embedding.pt` 体现多子模型融合：
    - 模型级：不同初始化/折叠的同架构模型平均或加权融合。
    - 特征级：结构向量与文本向量拼接/加权求和。

---

### 4. 训练任务与损失设计

- 主任务：链接预测（Link Prediction）
  - 样本构造：
    - 正样本：图中真实边。
    - 负采样：基于同类型节点的随机替换、结构约束负采样、难负样本（`triplet_indices_hard_neg.pt`）。
  - 打分函数：
    - GNN 表示后采用双塔内积/MLP 打分；或结合 DistMult/RotatE 风格打分。
  - 损失：
    - 二元交叉熵（BCE with logits）或 margin ranking loss；难负样本使用更高权重。

- 辅助任务：
  - 节点类型分类：提升类型可分性与判别性。
  - 标签多标签分类：利用 `problem_id_to_tags.json` 进行弱监督对齐。
  - 文本对比学习：节点文本向量与结构向量进行 InfoNCE 对齐，缓解模态鸿沟。

- 正则化与稳定性：
  - Dropout、LayerNorm、L2 正则；Edge dropout 提升泛化。
  - 温度/对比损失系数、任务损失权重通过验证集调优。

---

### 5. 训练数据流与实现要点

- 数据准备
  - 按 `entity2id.json` 固定节点索引，确保训练/推理一致。
  - 从 Neo4j/缓存导出边集合到稀疏表示（`edge_index_with_problem_edges.pt`）。
  - 加载文本向量（`bert_title_features.pt`），对齐至相同节点索引序。

- 训练实现参考
  - 入口：`gnn_model/train_multitask_gat2v.py`（GATv2 多任务）
  - 模型：
    - 图编码器：GATv2 层堆叠，支持异构边类型权重（可通过 edge type embedding 或 attention bias）。
    - 文本融合：节点初始化向量 = concat(结构初始化, 文本向量) → MLP 投影。
  - 负采样器：
    - 简单随机负采样 + 难例缓存（从前几轮中高分的负样本中抽取）。
  - 训练技巧：
    - 边 mini-batch 训练，控制显存；邻居采样（GraphSAGE 风格）可选。
    - 混合精度与梯度累积，提升吞吐。

---

### 6. 评测与监控

- 链接预测指标
  - MRR、Hits@K（K ∈ {1, 3, 10}）、ROC-AUC。

- 下游任务指标
  - 推荐召回/命中率（离线 top-K）、NDCG；问答检索召回；相似节点检索质量。

- 在线监控
  - 向量分布漂移（均值/方差/范数范围）；检索延迟 P50/P95；服务错误率。

- 对齐与对比
  - 结构-only vs 文本-only vs 融合模型的消融实验；
  - 不同负采样策略、不同任务权重的对比实验。

---

### 7. 推理、服务与集成

- 向量生成
  - 离线批处理：按全量节点生成并落盘为 `.pt` 或 `.npy`，归档到 `models/ensemble_gnn_embedding.pt` 或分片文件。
  - 在线增量：新节点入库后触发异步编码并写回缓存（Redis/本地文件/向量库）。

- 在线服务
  - 服务入口：`gnn_model/embedding_service.py`。
  - 能力：
    - 单节点/批量节点向量生成 API。
    - 最近邻检索（可接 Milvus/Faiss 或内存 Annoy/ScaNN）。
  - 性能建议：
    - 模型常驻内存 + FP16；批量化请求；热身若干批；线程池/异步 IO。

- 与 Neo4j 集成
  - 通过 `neo4j_loader/neo4j_api.py` 读取节点与边；可在节点属性中缓存 embedding 摘要（如前 8 维与范数），完整向量存外部存储。

---

### 8. 实验配置建议

- 结构编码器
  - GATv2 层数 2–3，头数 4–8，隐藏维 256–512。
  - GraphSAGE 作为替代，对大图用邻居采样（每层 10–25 采样）。

- 向量维度与融合
  - 文本向量维 768（BERT）；结构向量维 256–512；融合后投影到 256–512。

- 训练
  - 批大小（边 mini-batch）10k–50k；学习率 1e-3–3e-4；训练 20–50 epoch。
  - Warmup 5% 步数；余弦退火或根据验证 MRR 早停。

- 负采样
  - 正负比 1:5–1:10；引入 20–30% 难负样本。

- 正则与鲁棒
  - Dropout 0.2–0.5；L2 1e-5–1e-4；对比损失温度 0.05–0.1。

---

### 9. 版本化与可复现

- 数据版本
  - 对 `entity2id.json`、边文件、文本向量文件打版本标签（日期+hash）。

- 代码/配置
  - 将训练脚本参数（模型维度、损失权重、采样策略）固化为 yaml/json 并归档到 `web_app/scripts` 或根目录 `configs/`（建议新增）。

- 模型与指标
  - 模型权重、训练日志、验证指标与随机种子统一归档到 `models/` 与日志目录，记录 Git 提交号。

---

### 10. 上线与运维SOP

1) 训练与验收
   - 在开发环境完成训练，产出权重与验证报告（MRR、Hits@K、召回/NDCG）。
2) 兼容性回归
   - 运行现有测试：`test_recommendation_*.py`、`test_knowledge_graph_integration.py`、`test_final_*` 确认集成无回归。
3) 部署
   - 将权重放入 `models/`，更新 `embedding_service.py` 加载路径；服务冷/热启动自检与健康检查。
4) 监控与告警
   - 延迟、错误率、吞吐、向量范数与相似度分布监控；异常漂移触发回滚或再训练。

---

### 11. 风险与对策

- 语义-结构不一致：采用对比学习与门控融合；做消融对比。
- 冷启动：使用文本-only 或 TransE 轻量模型兜底，后续增量训练。
- 负样本过易：引入难负样本与自适应权重。
- 在线延迟：批量化 + FP16 + 近邻索引；必要时蒸馏到小模型。

---

### 12. 后续路线图

- 引入异构图建模（边类型/关系注意力更显式）。
- 文本自适应编码（微调 MiniLM/Chinese SimCSE），统一向量空间。
- 蒸馏/量化（INT8/FP8）以进一步降低延迟与成本。
- 引入向量数据库（Milvus/FAISS Server）与 ANN 索引持久化。

---

### 13. 参考实现位置

- 训练脚本：`gnn_model/train_multitask_gat2v.py`
- 在线服务：`gnn_model/embedding_service.py`
- 数据加载：`neo4j_loader/neo4j_api.py`
- 现有模型：`models/ensemble_gnn_model.pt.*`、`models/ensemble_gnn_embedding.pt`
- 数据文件：`data/raw/*.pt|*.json`

---

如需我基于当前数据直接补齐配置样例或新增 `configs/` 与评测脚本，请告知你的偏好（训练/推理环境与约束）。
