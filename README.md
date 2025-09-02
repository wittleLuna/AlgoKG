

[English](#english) | [中文](#中文)

# AlgoKG <img width="25" height="32" alt="logo" src="https://github.com/user-attachments/assets/befdbe85-fdcc-4bde-a74b-4385a899aae7" />



## 中文

### 📌 简介

AlgoKG 是一个 **基于知识图谱的智能算法学习助手**，集成了 **多智能体协作推理**、**图神经网络增强推荐**、**实时流式响应** 和 **知识图谱可视化** 等先进技术，为学习者提供个性化、交互式的算法学习体验。



### 🚀 核心特性

#### 🤖 智能问答系统

* 多智能体协作：分工合作的 AI 推理架构
* 实时推理展示：可视化 AI 思考过程
* 多轮对话支持：上下文理解与会话管理
* 流式响应：逐步展示推理步骤与结果

#### 🕸️ 知识图谱可视化

* 多数据源融合：Neo4j + 向量嵌入 + 静态知识
* 交互式探索：节点点击、缩放、拖拽操作
* 动态布局：力导向 / 层次化布局等
* 实时查询：基于 Cypher 的高效图查询

#### 🧠 图神经网络推荐

* 多塔架构：结构化 + 标签 + 文本特征融合
* GATv2 网络：捕捉节点复杂关系
* 集成学习：多模型融合提升推荐效果
* 个性化推荐：基于用户行为的智能推荐



### 📚 项目定位与价值

* **目标**：打造面向算法学习与练习的智能助手
* **核心能力**：智能问答、多智能体推理、知识图谱可视化、个性化推荐
* **受众**：学生、竞赛选手、工程师、教育机构



### 🏗️ 系统架构 (System Architecture)

整体系统由 **数据源层 → 数据存储层 → 模型层 → 服务层 → API接口层 → 前端展示层** 组成，涵盖了数据采集、图谱构建、模型训练、推荐推理、可视化交互的全流程。


<img width="1043" height="1308" alt="5d5304efa0df21cb42cb74c9236cce35" src="https://github.com/user-attachments/assets/b1268f12-afa3-4941-8307-267ac7577407" />



### 🛠️ 技术栈

* **前端**：React 18, TypeScript, Ant Design, Zustand, React Query, D3/Vis, Styled Components, Framer Motion
* **后端**：FastAPI, Pydantic, asyncio/aiohttp, Uvicorn
* **数据库/缓存**：Neo4j 5.x, Redis
* **AI/ML**：PyTorch, PyTorch Geometric, GATv2, BERT/Transformers, scikit-learn



### ⚡ 部署方式

#### 🔹 1. 使用 Docker 镜像

* 前端镜像：

  ```bash
  docker run -d -p 3000:3000 crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/frontend:latest
  ```

* 后端镜像：

  ```bash
  docker run -d -p 8000:8000 crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/backend:latest
  ```

#### 🔹 2. 使用 Docker Compose

在 `docker-compose.yml` 文件中写入：

```yaml
version: '3.8'
services:
  frontend:
    image: crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/frontend:latest
    ports:
      - "3000:3000"
    restart: always

  backend:
    image: crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/backend:latest
    ports:
      - "8000:8000"
    restart: always
```

运行：

```bash
docker compose up -d
```

## 📜 许可证

本项目使用 **Apache License 2.0** 许可证 - 详情参见 [LICENSE](./LICENSE) 文件。



## English

### 📌 Overview

AlgoKG is an **intelligent algorithm learning assistant** powered by **knowledge graphs**, featuring **multi-agent reasoning**, **graph neural network–enhanced recommendation**, **real-time streaming responses**, and **interactive knowledge graph visualization**.



### 🚀 Key Features

#### 🤖 Intelligent QA System

* Multi-agent reasoning: distributed AI reasoning workflow
* Real-time reasoning visualization: trace AI thought process
* Multi-turn dialogue: context-aware conversations
* Streaming responses: progressive step-by-step answers

#### 🕸️ Knowledge Graph Visualization

* Multi-source integration: Neo4j + vector embeddings + static knowledge
* Interactive exploration: node click, zoom, drag, and layout switching
* Dynamic layouts: force-directed, hierarchical, etc.
* Real-time querying: Cypher-based efficient graph queries

#### 🧠 Graph Neural Network Recommendation

* Multi-tower architecture: structural + tag + text feature fusion
* GATv2 network: attention mechanism for graph learning
* Ensemble learning: multiple model fusion for robustness
* Personalized recommendation: behavior-based adaptive results



### 🏗️ System Architecture

The system consists of **Data Source Layer → Data Storage Layer → Model Layer → Service Layer → API Interface Layer → Frontend Presentation Layer**, covering the entire workflow from data ingestion, graph construction, model training, recommendation, reasoning, to visualization.


<img width="1043" height="1314" alt="0968325778fd7eb6b7ad00b239f3cf83" src="https://github.com/user-attachments/assets/e4633b2e-f10a-4b14-9118-63bbf9f11624" />



### 🛠️ Tech Stack

* **Frontend**: React 18, TypeScript, Ant Design, Zustand, React Query, D3/Vis, Styled Components, Framer Motion
* **Backend**: FastAPI, Pydantic, asyncio/aiohttp, Uvicorn
* **Database/Cache**: Neo4j 5.x, Redis
* **AI/ML**: PyTorch, PyTorch Geometric, GATv2, BERT/Transformers, scikit-learn



### ⚡ Deployment

#### 🔹 1. Run via Docker Images

* Frontend:

  ```bash
  docker run -d -p 3000:3000 crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/frontend:latest
  ```

* Backend:

  ```bash
  docker run -d -p 8000:8000 crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/backend:latest
  ```

#### 🔹 2. Run via Docker Compose

```yaml
version: '3.8'
services:
  frontend:
    image: crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/frontend:latest
    ports:
      - "3000:3000"
    restart: always

  backend:
    image: crpi-punn3h5bue3iyauo.cn-chengdu.personal.cr.aliyuncs.com/algokg/backend:latest
    ports:
      - "8000:8000"
    restart: always
```

Run:

```bash
docker compose up -d
```

## 📜 License 

This project is licensed under the **Apache License 2.0** - see the [LICENSE](./LICENSE) file for details.  




