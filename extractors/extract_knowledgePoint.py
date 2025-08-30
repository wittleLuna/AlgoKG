import spacy
import json
import re
import os
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio
from enum import Enum
import aiohttp

# 加载环境变量
load_dotenv()

# 实体类别枚举
class EntityLabels(str, Enum):
    ALGORITHM_PARADIGM = "algorithm_paradigm"
    DATA_STRUCTURE = "data_structure"
    SPECIFIC_ALGORITHM = "specific_algorithm"
    PROBLEM_TYPE = "problem_type"
    CORE_CONCEPT = "core_concept"
    COMPLEXITY = "complexity"
    TECHNIQUE = "technique"

@dataclass
class KnowledgePoint:
    id: str
    name: str
    alias: List[str]
    type: str
    description: str
    key_concepts: List[str]
    applications: List[str]
    created_at: str = None
    updated_at: str = None
    source_files: Optional[List[str]] = None
    spacy_entities: Optional[Dict[str, List[str]]] = None
    
    def to_dict(self):
        result = {
            "id": self.id,
            "name": self.name,
            "alias": self.alias,
            "type": self.type,
            "description": self.description,
            "key_concepts": self.key_concepts,
            "applications": self.applications,
            "created_at": self.created_at or datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_files": self.source_files or [],
            "spacy_entities": self.spacy_entities or {}
        }
        return result

class QwenClient:
    """Qwen模型客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat_completion_async(self, messages: List[Dict], model: str = "qwen-max") -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Qwen API异步调用失败: {e}")
            return "{}"
            

# 兜底：无论模型是否仍输出，统一清理 <think>...</think>（跨行/大小写）
_THINK_RE = re.compile(r"<\s*think\s*>.*?<\s*/\s*think\s*>\s*", flags=re.S | re.I)

def strip_think(text: str) -> str:
    return _THINK_RE.sub("", text).strip()

class QwenClientNative:
    """原生 Ollama /api/chat 客户端（异步）
    - 从源头: options.think = False 关闭思考输出
    """

    def __init__(
        self,
        host: str | None = None,
        default_model: str = "qwen3:8b",
        timeout: int = 120,
        clean_output: bool = True,
        inject_no_think: bool = True,
    ):
        # 优先环境变量
        env_host = os.getenv("OLLAMA_BASE_URL")
        self.host = (host or env_host or "http://127.0.0.1:11434").rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.clean_output = clean_output
        self.inject_no_think = inject_no_think

    async def chat_completion_async(
        self,
        messages: List[Dict],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        stream: bool = False,
        keepalive: Optional[int] = None,  # 可选：给模型保活秒数（不想释放显存）
    ) -> str:
        """调用原生 /api/chat，返回字符串结果"""
        url = f"{self.host}/api/chat"

        # 可选：在消息最前注入 system 指令，进一步压制 think 输出
        final_messages = messages
        if self.inject_no_think:
            sys_msg = {
                "role": "system",
                "content": "请只输出最终答案，不要输出任何思考过程或 <think> 标签。"
            }
            if not messages or messages[0].get("role") != "system":
                final_messages = [sys_msg] + messages

        payload: Dict = {
            "model": model or self.default_model,
            "messages": final_messages,
            "stream": stream,
            # 原生 options：这里的 think=False 才会被识别
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "think": False
            }
        }
        if keepalive is not None:
            # 告诉 Ollama 在本次调用后保留模型 keepalive 秒（减少冷启动）
            payload["keep_alive"] = f"{int(keepalive)}s"

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as r:
                r.raise_for_status()

                if stream:
                    # 流式：把片段先缓冲起来，最后统一清洗（避免think被分块拆开）
                    buf: List[str] = []
                    async for line in r.content:
                        if not line:
                            continue
                        try:
                            data = json.loads(line.decode("utf-8"))
                        except Exception:
                            continue
                        part = data.get("message", {}).get("content", "")
                        if part:
                            buf.append(part)
                        if data.get("done"):
                            break
                    text = "".join(buf)
                else:
                    data = await r.json()
                    text = data.get("message", {}).get("content", "") or ""

        return strip_think(text) if self.clean_output else text


class PreciseEntityExtractor:
    """精确的实体提取器 - 专注于LLM准确性"""
    
    def __init__(self, qwen_api_key: str = None, pattern_path: str = "patterns.json"):
        # 初始化spaCy
        self.nlp = spacy.load("zh_core_web_sm")
        
        # 禁用默认NER，避免通用实体干扰
        if "ner" in self.nlp.pipe_names:
            self.nlp.remove_pipe("ner")
            print("🚫 已禁用spaCy默认NER，避免通用实体干扰")
        
        # 添加实体规则器
        self.ruler = self.nlp.add_pipe("entity_ruler")
        self.setup_patterns(pattern_path)
        
        self.qwen_client = QwenClient(api_key=qwen_api_key)
        self.current_version = "v2.1"
        
        # 初始化精确词典
        self.init_precise_dictionaries()

    def setup_patterns(self, config_path="patterns.json"):
        """设置spaCy模式"""
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                self.ruler.add_patterns(patterns)
                print(f"✅ 成功加载模式文件: {config_path}，共 {len(patterns)} 个模式")
            except Exception as e:
                print(f"❌ 加载模式文件失败: {e}")
                self.setup_default_patterns()
        else:
            print(f"⚠️ 模式文件 {config_path} 不存在，使用默认模式")
            self.setup_default_patterns()

    def setup_default_patterns(self):
        """设置默认的spaCy模式"""
        default_patterns = [
            # 算法范式
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "动态规划"}]},
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "dp"}]},
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "贪心"}]},
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "分治"}]},
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "回溯"}]},
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "dfs"}]},
            {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "bfs"}]},
            
            # 数据结构
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "数组"}]},
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "链表"}]},
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "栈"}]},
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "队列"}]},
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "树"}]},
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "图"}]},
            {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "哈希表"}]},
            
            # 具体算法
            {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "快速排序"}]},
            {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "归并排序"}]},
            {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "二分查找"}]},
            {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "kmp"}]},
            
            # 技巧
            {"label": "TECHNIQUE", "pattern": [{"LOWER": "双指针"}]},
            {"label": "TECHNIQUE", "pattern": [{"LOWER": "滑动窗口"}]},
            {"label": "TECHNIQUE", "pattern": [{"LOWER": "前缀和"}]},
            
            # 核心概念
            {"label": "CORE_CONCEPT", "pattern": [{"LOWER": "时间复杂度"}]},
            {"label": "CORE_CONCEPT", "pattern": [{"LOWER": "空间复杂度"}]},
            {"label": "CORE_CONCEPT", "pattern": [{"LOWER": "递归"}]},
        ]
        
        self.ruler.add_patterns(default_patterns)
        print(f"✅ 加载默认模式，共 {len(default_patterns)} 个模式")

    def init_precise_dictionaries(self):
        """初始化精确词典"""
        
        # 问题类型词典 - 最重要，需要最精确
        self.problem_type_dict = {
            # 背包类问题
            '01背包问题', '0-1背包问题', '完全背包问题', '多重背包问题', '混合背包问题', '背包问题',
            # 路径类问题  
            '最短路径问题', '最长路径问题', '单源最短路径问题', '多源最短路径问题',
            # 序列类问题
            '最长公共子序列问题', '最长递增子序列问题', '最长公共子串问题', '最长回文子序列问题',
            # 匹配类问题
            '字符串匹配问题', '模式匹配问题', '正则匹配问题',
            # 遍历类问题
            '图遍历问题', '树遍历问题', '二叉树遍历问题',
            # 基础问题类型
            '排序问题', '查找问题', '搜索问题',
            # 特殊问题
            '连通性问题', '环检测问题', '拓扑排序问题',
            '区间调度问题', '任务调度问题', '作业调度问题',
            # 经典问题
            '斐波那契问题', '爬楼梯问题', '硬币问题', '切割问题', '股票问题'
        }
        
        # 复杂度词典 - 标准格式
        self.complexity_dict = {
            'O(1)', 'O(log n)', 'O(logn)', 'O(n)', 'O(n log n)', 'O(nlogn)', 
            'O(n²)', 'O(n^2)', 'O(n³)', 'O(n^3)', 'O(2^n)', 'O(n!)', 
            'O(mn)', 'O(m*n)', 'O(m+n)', 'O(V+E)', 'O(ElogV)'
        }
        
        # 算法范式词典
        self.algorithm_paradigm_dict = {
            '动态规划', 'DP', '贪心算法', '贪心策略', '分治算法', '分治法',
            '回溯算法', '回溯法', '深度优先搜索', 'DFS', '广度优先搜索', 'BFS',
            '枚举算法', '暴力搜索', '递归算法', '迭代算法'
        }
        
        # 具体算法词典
        self.specific_algorithm_dict = {
            'KMP算法', 'KMP', '快速排序', '归并排序', '堆排序', '冒泡排序', '插入排序', '选择排序',
            '二分查找', '二分搜索', 'Dijkstra算法', 'Floyd算法', 'Prim算法', 'Kruskal算法',
            'A*算法', 'Bellman-Ford算法', '拓扑排序算法', '最小生成树算法'
        }
        
        # 数据结构词典
        self.data_structure_dict = {
            '数组', '链表', '单链表', '双链表', '环形链表',
            '栈', '队列', '优先队列', '双端队列',
            '树', '二叉树', '二叉搜索树', '平衡树', 'AVL树', '红黑树',
            '图', '有向图', '无向图', '加权图',
            '哈希表', '散列表', '字典', '集合',
            '堆', '最大堆', '最小堆', '二叉堆',
            '字典树', 'Trie树', '前缀树'
        }
        
        # 技巧词典
        self.technique_dict = {
            '双指针', '快慢指针', '左右指针', '对撞指针',
            '滑动窗口', '固定窗口', '可变窗口',
            '前缀和', '前缀积', '差分数组', '二维前缀和',
            '单调栈', '单调递增栈', '单调递减栈', '单调队列',
            '前缀表', 'next数组', 'Z算法',
            '状态压缩', '位运算优化', '记忆化搜索', '记忆化',
            '并查集', '路径压缩', '按秩合并',
            '线段树', '树状数组', '分块算法',
            '哈希技巧', '双哈希', '滚动哈希'
        }
        
        # 核心概念词典
        self.core_concept_dict = {
            '时间复杂度', '空间复杂度', '渐进复杂度',
            '递归', '迭代', '分治', '贪心策略',
            '最优子结构', '重叠子问题', '状态转移方程', '边界条件',
            '状态定义', '状态转移', '初始化', '遍历顺序',
            '动态规划', '记忆化', '自顶向下', '自底向上',
            '回溯算法', '剪枝优化', '搜索空间', '解空间',
            '贪心选择', '局部最优', '全局最优'
        }

    def extract_by_precise_dictionary(self, text: str) -> Dict[str, List[str]]:
        """使用精确词典匹配"""
        entities = {}
        
        # 问题类型匹配 - 最严格
        found_problems = []
        for problem in self.problem_type_dict:
            if problem in text:
                found_problems.append(problem)
        if found_problems:
            entities["PROBLEM_TYPE"] = found_problems
        
        # 复杂度匹配 - 标准格式
        found_complexities = []
        for complexity in self.complexity_dict:
            variants = [complexity, complexity.replace(' ', ''), complexity.replace('²', '^2'), complexity.replace('³', '^3')]
            for variant in variants:
                if variant in text and complexity not in found_complexities:
                    found_complexities.append(complexity)
                    break
        if found_complexities:
            entities["COMPLEXITY"] = found_complexities
        
        # 算法范式匹配
        found_paradigms = []
        for paradigm in self.algorithm_paradigm_dict:
            if paradigm in text:
                found_paradigms.append(paradigm)
        if found_paradigms:
            entities["ALGORITHM_PARADIGM"] = found_paradigms
        
        # 具体算法匹配
        found_algorithms = []
        for algorithm in self.specific_algorithm_dict:
            if algorithm in text:
                found_algorithms.append(algorithm)
        if found_algorithms:
            entities["SPECIFIC_ALGORITHM"] = found_algorithms
        
        # 数据结构匹配
        found_structures = []
        for structure in self.data_structure_dict:
            if structure in text:
                found_structures.append(structure)
        if found_structures:
            entities["DATA_STRUCTURE"] = found_structures
        
        # 技巧匹配
        found_techniques = []
        for technique in self.technique_dict:
            if technique in text:
                found_techniques.append(technique)
        if found_techniques:
            entities["TECHNIQUE"] = found_techniques
        
        # 核心概念匹配
        found_concepts = []
        for concept in self.core_concept_dict:
            if concept in text:
                found_concepts.append(concept)
        if found_concepts:
            entities["CORE_CONCEPT"] = found_concepts
        
        return entities

    def extract_with_spacy_rules(self, text: str) -> Dict[str, List[str]]:
        """使用spaCy规则提取"""
        doc = self.nlp(text)
        entities = {}
        
        # 定义算法相关标签
        algorithm_labels = {
            "ALGORITHM_PARADIGM", "DATA_STRUCTURE", "SPECIFIC_ALGORITHM",
            "PROBLEM_TYPE", "CORE_CONCEPT", "COMPLEXITY", "TECHNIQUE"
        }
        
        for ent in doc.ents:
            label = ent.label_
            if label in algorithm_labels:
                if label not in entities:
                    entities[label] = []
                if ent.text not in entities[label]:
                    entities[label].append(ent.text)
        
        return entities

    def clean_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """清理提取的实体"""
        cleaned_entities = {}
        
        for entity_type, entity_list in entities.items():
            cleaned_list = []
            
            for entity in entity_list:
                entity = entity.strip()
                
                # 基本长度过滤
                if not (2 <= len(entity) <= 20):
                    continue
                
                # 针对问题类型的特殊过滤
                if entity_type == "PROBLEM_TYPE":
                    # 严格过滤问题类型
                    if (3 <= len(entity) <= 12 and
                        not any(word in entity for word in ["所以", "重点", "就是", "其实", "需要", "通过", "这是", "也就是", "讲解", "开始", "标准", "纯", "先", "如果", "因为"]) and
                        not entity.startswith(("这", "也", "所", "其", "如", "因")) and
                        any(keyword in entity for keyword in ["问题", "背包", "路径", "序列", "匹配", "排序", "查找", "遍历"])):
                        cleaned_list.append(entity)
                
                # 针对复杂度的特殊过滤
                elif entity_type == "COMPLEXITY":
                    if entity.startswith("O(") and entity.endswith(")"):
                        cleaned_list.append(entity)
                
                # 其他类型的基本过滤
                else:
                    if not any(word in entity for word in ["所以", "重点", "就是", "其实", "需要", "通过", "这是", "也就是"]):
                        cleaned_list.append(entity)
            
            if cleaned_list:
                # 去重
                cleaned_entities[entity_type] = list(set(cleaned_list))
        
        return cleaned_entities

    async def enhance_with_precise_llm(self, text: str, spacy_entities: Dict[str, List[str]]) -> Dict:
        """使用LLM进行精确增强"""
        
        # 过滤spaCy结果
        filtered_spacy = self.clean_entities(spacy_entities)
        
        spacy_summary = ""
        if filtered_spacy:
            spacy_summary = "\n已通过规则提取到的实体："
            for label, entities in filtered_spacy.items():
                spacy_summary += f"\n- {label}: {', '.join(entities[:5])}"  # 只显示前5个
        
        messages = [
            {
                "role": "system",
                "content": """你是专业的算法知识点提取专家。你的核心任务是精确识别算法文本中的实体，特别是问题类型必须是标准的名词性短语。

核心原则：
1. 问题类型(PROBLEM_TYPE)必须是规范的问题名称，如"01背包问题"、"最短路径问题"
2. 绝对不要提取包含"所以"、"重点"、"就是"等解释词的句子片段
3. 复杂度必须是标准格式，如"O(n)"、"O(n²)"
4. 专注于算法领域的核心术语，避免通用词汇
5. 每个类别只提取最重要、最准确的实体"""
            },
            {
                "role": "user",
                "content": f"""
请精确分析以下算法文本，提取其中的专业实体。重点关注PROBLEM_TYPE的准确性。

文本内容：
{text[:1200]}

{spacy_summary}

提取要求：

**PROBLEM_TYPE（问题类型）- 最重要**：
- 必须是标准问题名称：如"01背包问题"、"最短路径问题"、"最长公共子序列问题"
- 长度3-12个字符
- 不能包含解释性文字或完整句子
- 不能以"这"、"所以"、"重点"等开头

**其他实体类型**：
- ALGORITHM_PARADIGM：动态规划、贪心算法、分治算法等
- SPECIFIC_ALGORITHM：快速排序、KMP算法、Dijkstra算法等  
- DATA_STRUCTURE：数组、链表、树、图、哈希表等
- TECHNIQUE：双指针、滑动窗口、前缀和、单调栈等
- CORE_CONCEPT：时间复杂度、状态转移、最优子结构等
- COMPLEXITY：O(n)、O(n²)、O(logn)等标准格式

请返回JSON格式：

{{
  "name": "主要知识点名称",
  "alias": ["别名1", "别名2"],
  "type": "algorithm_paradigm/data_structure/specific_algorithm/problem_type/core_concept/technique",
  "description": "详细描述",
  "key_concepts": ["核心概念1", "核心概念2"],
  "applications": ["应用场景1", "应用场景2"],
  "refined_entities": {{
    "problem_type": ["标准问题类型名称"],
    "algorithm_paradigm": ["算法范式"],
    "specific_algorithm": ["具体算法"],
    "data_structure": ["数据结构"],
    "technique": ["技巧方法"],
    "core_concept": ["核心概念"],
    "complexity": ["标准复杂度格式"]
  }}
}}

注意：如果某个类别没有合适的实体，请留空数组。确保每个实体都是准确的专业术语。

只返回JSON，不要其他内容。
"""
            }
        ]
        
        response = await self.qwen_client.chat_completion_async(messages, model="qwen-max")
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                # 严格的后处理验证
                if "refined_entities" in result:
                    validated_entities = {}
                    for entity_type, entity_list in result["refined_entities"].items():
                        validated_list = []
                        for entity in entity_list:
                            if isinstance(entity, str):
                                entity = entity.strip()
                                
                                # 问题类型严格验证
                                if entity_type == "problem_type":
                                    if (3 <= len(entity) <= 12 and
                                        not any(word in entity for word in ["所以", "重点", "就是", "其实", "这是", "也就是", "如果", "因为", "需要", "通过", "讲解"]) and
                                        any(keyword in entity for keyword in ["问题", "背包", "路径", "序列", "匹配", "排序", "查找", "遍历"])):
                                        validated_list.append(entity)
                                
                                # 复杂度严格验证
                                elif entity_type == "complexity":
                                    if entity.startswith("O(") and entity.endswith(")") and len(entity) <= 15:
                                        validated_list.append(entity)
                                
                                # 其他类型基本验证
                                elif (2 <= len(entity) <= 15 and
                                      not any(word in entity for word in ["所以", "重点", "就是", "其实", "这是", "也就是"])):
                                    validated_list.append(entity)
                        
                        if validated_list:
                            validated_entities[entity_type] = validated_list
                    
                    result["refined_entities"] = validated_entities
                
                return result
            else:
                print("⚠️ 无法从LLM响应中提取JSON")
                return {}
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败: {e}")
            return {}

    def merge_extraction_results(self, spacy_entities: Dict[str, List[str]], 
                                dictionary_entities: Dict[str, List[str]],
                                llm_result: Dict, source_file: str = None) -> KnowledgePoint:
        """合并多种提取结果"""
        
        name = llm_result.get("name", "Unknown")
        alias = llm_result.get("alias", [])
        entity_type = llm_result.get("type", "core_concept")
        description = llm_result.get("description", "")
        key_concepts = llm_result.get("key_concepts", [])
        applications = llm_result.get("applications", [])
        
        # 合并所有实体
        final_entities = {}
        algorithm_labels = {
            "ALGORITHM_PARADIGM", "DATA_STRUCTURE", "SPECIFIC_ALGORITHM",
            "PROBLEM_TYPE", "CORE_CONCEPT", "COMPLEXITY", "TECHNIQUE"
        }
        
        # 1. 优先使用词典结果（最可靠）
        for label, entities in dictionary_entities.items():
            if label.upper() in algorithm_labels:
                final_entities[label.upper()] = entities.copy()
        
        # 2. 加入LLM精炼的实体
        refined_entities = llm_result.get("refined_entities", {})
        for entity_type_key, entity_list in refined_entities.items():
            label = entity_type_key.upper()
            if label in algorithm_labels:
                if label not in final_entities:
                    final_entities[label] = []
                for entity in entity_list:
                    if entity not in final_entities[label]:
                        final_entities[label].append(entity)
        
        # 3. 补充spaCy结果（经过清理）
        cleaned_spacy = self.clean_entities(spacy_entities)
        for label, entities in cleaned_spacy.items():
            if label in algorithm_labels:
                if label not in final_entities:
                    final_entities[label] = []
                for entity in entities:
                    if entity not in final_entities[label]:
                        final_entities[label].append(entity)
        
        # 生成唯一ID
        id_prefix = self.generate_id_prefix(entity_type)
        kp_id = f"{id_prefix}{abs(hash(name)) % 1000:03d}"
        
        return KnowledgePoint(
            id=kp_id,
            name=name,
            alias=alias,
            type=entity_type,
            description=description,
            key_concepts=key_concepts,
            applications=applications,
            source_files=[source_file] if source_file else [],
            spacy_entities=final_entities
        )

    def generate_id_prefix(self, type_str: str) -> str:
        """生成ID前缀"""
        prefixes = {
            EntityLabels.ALGORITHM_PARADIGM.value: "AP",
            EntityLabels.DATA_STRUCTURE.value: "DS", 
            EntityLabels.SPECIFIC_ALGORITHM.value: "SA",
            EntityLabels.PROBLEM_TYPE.value: "PT",
            EntityLabels.CORE_CONCEPT.value: "CC",
            EntityLabels.TECHNIQUE.value: "TQ"
        }
        return prefixes.get(type_str, "KP")

    async def extract_knowledge_point(self, text: str, source_file: str = None) -> KnowledgePoint:
        """主要的知识点提取方法"""
        print(f"🔍 开始精确提取知识点: {source_file or 'unknown'}")
        
        start_time = datetime.now()
        
        # Step 1: spaCy规则提取
        print("  📝 Step 1: spaCy规则提取...")
        spacy_entities = self.extract_with_spacy_rules(text)
        
        # Step 2: 精确词典匹配（最可靠）
        print("  📚 Step 2: 精确词典匹配...")
        dictionary_entities = self.extract_by_precise_dictionary(text)
        
        # Step 3: LLM精确增强
        print("  🧠 Step 3: LLM精确增强...")
        llm_result = await self.enhance_with_precise_llm(text, spacy_entities)
        
        # Step 4: 智能合并结果
        print("  🔗 Step 4: 智能合并结果...")
        knowledge_point = self.merge_extraction_results(
            spacy_entities, dictionary_entities, llm_result, source_file
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"  ✅ 完成提取: {knowledge_point.name} ({processing_time:.2f}s)")
        
        return knowledge_point

class JsonFileManager:
    """JSON文件管理器，处理智能文件合并"""
    
    def __init__(self, output_dir: str = "knowledge_points_json"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.qwen_client = QwenClient()

    def extract_base_name(self, txt_filename: str) -> str:
        """提取文件的基础名称（去掉后缀标识）"""
        base_name = Path(txt_filename).stem
        
        # 后缀模式
        suffix_patterns = [
            r'_kama$', r'_wiki$', r'_leetcode$', r'_csdn$', r'_blog$',
            r'_官方$', r'_详解$', r'_基础$', r'_进阶$', r'_\d+$', r'_[a-zA-Z]+$'
        ]
        
        for pattern in suffix_patterns:
            if re.search(pattern, base_name, re.IGNORECASE):
                base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
                break
        
        return base_name

    def get_json_filename(self, txt_filename: str) -> str:
        """根据txt文件名生成json文件名"""
        base_name = self.extract_base_name(txt_filename)
        return f"{base_name}.json"

    def json_file_exists(self, json_filename: str) -> bool:
        """检查JSON文件是否存在"""
        return (self.output_dir / json_filename).exists()

    def load_existing_json(self, json_filename: str) -> Optional[Dict]:
        """加载已存在的JSON文件"""
        json_path = self.output_dir / json_filename
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 加载JSON文件失败: {e}")
        return None

    async def merge_knowledge_points(self, existing_kp_dict: Dict, new_kp: KnowledgePoint, 
                                   new_source_file: str) -> Dict:
        """使用LLM合并知识点"""
        
        messages = [
            {
                "role": "system",
                "content": "你是知识点合并专家。将新的知识点信息与现有知识点智能合并，保留所有有价值的信息，形成更完整准确的知识点描述。"
            },
            {
                "role": "user",
                "content": f"""
现有知识点：
{json.dumps(existing_kp_dict, ensure_ascii=False, indent=2)}

新的知识点信息：
{json.dumps(new_kp.to_dict(), ensure_ascii=False, indent=2)}

新来源文件：{new_source_file}

合并规则：
1. 保持原有的id和name不变
2. 合并alias列表，去重，保留所有有意义的别名
3. 综合两个描述，生成更完整详细的description
4. 合并key_concepts和applications，去重，保持逻辑性
5. 合并source_files列表，记录所有来源
6. 合并spacy_entities，去重但保留有价值的实体
7. 更新updated_at时间戳

请返回完整的合并后的JSON，格式与输入保持一致。
只返回JSON，不要其他解释。
"""
            }
        ]
        
        response = await self.qwen_client.chat_completion_async(messages, model="qwen-max")
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response[json_start:json_end]
                merged_dict = json.loads(json_str)
                merged_dict["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                return merged_dict
            else:
                return self.manual_merge(existing_kp_dict, new_kp, new_source_file)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败，使用手动合并: {e}")
            return self.manual_merge(existing_kp_dict, new_kp, new_source_file)

    def manual_merge(self, existing_kp_dict: Dict, new_kp: KnowledgePoint, 
                    new_source_file: str) -> Dict:
        """手动合并知识点（备用方案）"""
        merged = existing_kp_dict.copy()
        new_dict = new_kp.to_dict()
        
        # 合并各种字段
        for field in ["alias", "key_concepts", "applications"]:
            existing_set = set(merged.get(field, []))
            new_set = set(new_dict.get(field, []))
            merged[field] = list(existing_set | new_set)
        
        # 合并source_files
        existing_sources = set(merged.get("source_files", []))
        existing_sources.add(new_source_file)
        merged["source_files"] = list(existing_sources)
        
        # 合并spacy_entities
        existing_entities = merged.get("spacy_entities", {})
        new_entities = new_dict.get("spacy_entities", {})
        for entity_type, entity_list in new_entities.items():
            if entity_type not in existing_entities:
                existing_entities[entity_type] = []
            existing_entities[entity_type] = list(set(existing_entities[entity_type] + entity_list))
        merged["spacy_entities"] = existing_entities
        
        # 智能合并描述
        old_desc = merged.get("description", "")
        new_desc = new_dict.get("description", "")
        if len(new_desc) > len(old_desc) * 1.5:
            merged["description"] = new_desc
        elif len(new_desc) > 50 and old_desc not in new_desc and new_desc not in old_desc:
            merged["description"] = f"{old_desc}\n\n补充信息：{new_desc}"
        
        merged["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        return merged

    def save_knowledge_point(self, knowledge_point_dict: Dict, json_filename: str):
        """保存知识点到JSON文件"""
        json_path = self.output_dir / json_filename
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(knowledge_point_dict, f, ensure_ascii=False, indent=2)
            print(f"💾 保存成功: {json_path}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")

    async def process_knowledge_point(self, knowledge_point: KnowledgePoint, 
                                    source_file: str) -> str:
        """处理知识点：新建或合并"""
        json_filename = self.get_json_filename(source_file)
        
        if self.json_file_exists(json_filename):
            existing_dict = self.load_existing_json(json_filename)
            if existing_dict:
                # 检查是否已经包含此源文件
                existing_sources = existing_dict.get("source_files", [])
                if source_file in existing_sources:
                    print(f"⏭️ 文件已处理过，跳过: {source_file}")
                    return "skipped"
                
                print(f"🔄 发现相关JSON文件，准备合并: {json_filename}")
                merged_dict = await self.merge_knowledge_points(
                    existing_dict, knowledge_point, source_file
                )
                self.save_knowledge_point(merged_dict, json_filename)
                sources = merged_dict.get('source_files', [])
                print(f"✅ 合并完成: {merged_dict['name']} (来源: {', '.join(sources)})")
                return "merged"
        
        # 新建文件
        kp_dict = knowledge_point.to_dict()
        if source_file not in kp_dict["source_files"]:
            kp_dict["source_files"].append(source_file)
        
        self.save_knowledge_point(kp_dict, json_filename)
        print(f"✅ 新建完成: {knowledge_point.name}")
        return "created"

class MainProcessor:
    """主处理器"""
    
    def __init__(self, input_dir: str = r"F:\My_project\programmercarl_articles\knowledepoints", 
                 output_dir: str = "knowledge_points_json"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.extractor = PreciseEntityExtractor()
        self.json_manager = JsonFileManager(output_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    def scan_txt_files(self) -> List[Path]:
        """扫描txt文件"""
        txt_files = list(self.input_dir.rglob("*.txt"))
        print(f"🔍 发现 {len(txt_files)} 个txt文件")
        return txt_files

    def read_txt_file(self, file_path: Path) -> str:
        """读取txt文件内容"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read().strip()
            except UnicodeDecodeError:
                continue
        
        raise Exception(f"无法解码文件 {file_path}")

    def preprocess_content(self, content: str) -> str:
        """预处理文本内容"""
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = re.sub(r'[ \t]+', ' ', content)
        return content

    def validate_content(self, content: str, file_path: Path) -> bool:
        """验证文件内容质量"""
        if len(content) < 50:
            print(f"⚠️ 内容过短，跳过: {file_path.name}")
            return False
        
        algorithm_keywords = [
            '算法', '数据结构', '排序', '查找', '树', '图', '动态规划', 'dp',
            'algorithm', 'complexity', '递归', '迭代', '链表', '数组', '栈', '队列'
        ]
        
        has_algorithm_content = any(keyword in content.lower() for keyword in algorithm_keywords)
        if not has_algorithm_content:
            print(f"⚠️ 未检测到算法相关内容: {file_path.name}")
        
        return True

    async def process_single_file(self, file_path: Path) -> bool:
        """处理单个txt文件"""
        try:
            print(f"\n📄 处理文件: {file_path.name}")
            
            # 读取文件
            content = self.read_txt_file(file_path)
            
            # 预处理
            processed_content = self.preprocess_content(content)
            
            # 验证内容
            if not self.validate_content(processed_content, file_path):
                return False
            
            # 提取知识点
            knowledge_point = await self.extractor.extract_knowledge_point(
                processed_content, 
                file_path.name
            )
            
            # 处理JSON文件（新建或合并）
            result = await self.json_manager.process_knowledge_point(
                knowledge_point, 
                file_path.name
            )
            
            print(f"🎯 处理结果: {result}")
            return True
            
        except Exception as e:
            print(f"❌ 处理失败 {file_path.name}: {e}")
            return False

    def group_files_by_base_name(self, txt_files: List[Path]) -> Dict[str, List[Path]]:
        """按基础名称分组文件"""
        file_groups = {}
        
        for file_path in txt_files:
            base_name = self.json_manager.extract_base_name(file_path.name)
            
            if base_name not in file_groups:
                file_groups[base_name] = []
            file_groups[base_name].append(file_path)
        
        # 显示分组信息
        print(f"\n📊 文件分组结果:")
        for base_name, files in file_groups.items():
            if len(files) > 1:
                print(f"  🔗 {base_name}: {len(files)} 个文件")
                for file in files:
                    print(f"    - {file.name}")
            else:
                print(f"  📄 {base_name}: 1 个文件 ({files[0].name})")
        
        return file_groups

    async def process_all_files(self, max_files: int = None, skip_processed: bool = True) -> Dict:
        """处理所有txt文件"""
        print(f"🚀 算法知识点精确提取系统 v2.1")
        print(f"📁 输入目录: {self.input_dir}")
        print(f"📁 输出目录: {self.output_dir}")
        print("=" * 60)
        
        # 扫描文件
        txt_files = self.scan_txt_files()
        
        if max_files:
            txt_files = txt_files[:max_files]
            print(f"🔢 限制处理文件数: {max_files}")
        
        # 按基础名称分组文件
        file_groups = self.group_files_by_base_name(txt_files)
        print(f"🔗 检测到 {len(file_groups)} 个知识点组，共 {sum(len(group) for group in file_groups.values())} 个文件")
        
        # 处理统计
        stats = {
            "total_files": len(txt_files),
            "total_groups": len(file_groups),
            "processed_files": 0,
            "failed_files": 0,
            "created_json": 0,
            "merged_json": 0,
            "skipped_files": 0,
            "failed_files_list": [],
            "processing_time": 0
        }
        
        start_time = datetime.now()
        
        # 按组处理文件
        group_index = 0
        for base_name, file_group in file_groups.items():
            group_index += 1
            print(f"\n[组 {group_index}/{len(file_groups)}] 处理知识点: {base_name}")
            print(f"📄 相关文件: {[f.name for f in file_group]}")
            print("=" * 50)
            
            # 按文件大小排序，优先处理主要文件
            file_group.sort(key=lambda f: f.stat().st_size, reverse=True)
            
            for i, file_path in enumerate(file_group, 1):
                print(f"\n  [{i}/{len(file_group)}] 处理文件: {file_path.name}")
                
                # 检查是否跳过已处理的文件
                json_filename = self.json_manager.get_json_filename(file_path.name)
                if skip_processed and self.json_manager.json_file_exists(json_filename):
                    existing_json = self.json_manager.load_existing_json(json_filename)
                    if existing_json and file_path.name in existing_json.get("source_files", []):
                        print(f"    ⏭️ 跳过已处理文件: {file_path.name}")
                        stats["skipped_files"] += 1
                        continue
                
                try:
                    success = await self.process_single_file(file_path)
                    
                    if success:
                        stats["processed_files"] += 1
                        
                        # 检查是新建还是合并
                        json_path = self.output_dir / json_filename
                        if json_path.exists():
                            existing_json = self.json_manager.load_existing_json(json_filename)
                            if existing_json and len(existing_json.get("source_files", [])) > 1:
                                stats["merged_json"] += 1
                            else:
                                stats["created_json"] += 1
                    else:
                        stats["failed_files"] += 1
                        stats["failed_files_list"].append({
                            "file": file_path.name,
                            "reason": "处理失败"
                        })
                        
                except Exception as e:
                    print(f"    ❌ 文件处理异常 {file_path.name}: {e}")
                    stats["failed_files"] += 1
                    stats["failed_files_list"].append({
                        "file": file_path.name,
                        "reason": str(e)
                    })
        
        stats["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        # 生成处理报告
        self.generate_report(stats)
        
        return stats

    def generate_report(self, stats: Dict):
        """生成处理报告"""
        print(f"\n" + "="*60)
        print("📊 处理完成报告")
        print("="*60)
        print(f"📁 输入目录: {self.input_dir}")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"⏱️ 处理时间: {stats['processing_time']:.1f} 秒")
        print()
        print(f"📄 总文件数: {stats['total_files']}")
        print(f"🔗 知识点组数: {stats['total_groups']}")
        print(f"✅ 成功处理: {stats['processed_files']}")
        print(f"❌ 处理失败: {stats['failed_files']}")
        print(f"⏭️ 跳过文件: {stats['skipped_files']}")
        print()
        print(f"🆕 新建JSON: {stats['created_json']}")
        print(f"🔄 合并JSON: {stats['merged_json']}")
        
        if stats["failed_files_list"]:
            print(f"\n❌ 失败文件列表:")
            for failed in stats["failed_files_list"]:
                print(f"   - {failed['file']}: {failed['reason']}")
        
        # 保存详细报告
        report_path = self.output_dir / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"\n📋 详细报告已保存: {report_path}")
        except Exception as e:
            print(f"⚠️ 报告保存失败: {e}")

    def list_generated_files(self):
        """列出生成的JSON文件"""
        json_files = list(self.output_dir.glob("*.json"))
        # 过滤掉报告文件
        json_files = [f for f in json_files if not f.name.startswith("processing_report_")]
        
        print(f"\n📚 已生成的JSON文件 ({len(json_files)}个):")
        
        for json_file in sorted(json_files):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get("name", "Unknown")
                    sources = data.get("source_files", [])
                    problem_types = data.get("spacy_entities", {}).get("PROBLEM_TYPE", [])
                    
                    print(f"   📄 {json_file.name}")
                    print(f"      🏷️ 名称: {name}")
                    print(f"      📁 来源({len(sources)}): {', '.join(sources)}")
                    if problem_types:
                        print(f"      🎯 问题类型: {', '.join(problem_types)}")
                    print()
            except Exception as e:
                print(f"   ❌ {json_file.name}: 读取失败 ({e})")

# 配置文件创建函数
def create_default_patterns_file():
    """创建默认的patterns.json文件"""
    patterns_file = Path("patterns.json")
    
    if patterns_file.exists():
        print(f"✅ patterns.json 已存在")
        return
    
    default_patterns = [
        # 算法范式
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "动态规划"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "dp"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "贪心"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "贪心算法"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "分治"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "分治算法"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "回溯"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "回溯算法"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "深度优先搜索"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "dfs"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "广度优先搜索"}]},
        {"label": "ALGORITHM_PARADIGM", "pattern": [{"LOWER": "bfs"}]},
        
        # 数据结构
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "数组"}]},
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "链表"}]},
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "栈"}]},
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "队列"}]},
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "树"}]},
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "图"}]},
        {"label": "DATA_STRUCTURE", "pattern": [{"LOWER": "哈希表"}]},
        
        # 具体算法
        {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "快速排序"}]},
        {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "归并排序"}]},
        {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "二分查找"}]},
        {"label": "SPECIFIC_ALGORITHM", "pattern": [{"LOWER": "kmp"}]},
        
        # 技巧
        {"label": "TECHNIQUE", "pattern": [{"LOWER": "双指针"}]},
        {"label": "TECHNIQUE", "pattern": [{"LOWER": "滑动窗口"}]},
        {"label": "TECHNIQUE", "pattern": [{"LOWER": "前缀和"}]},
        
        # 核心概念
        {"label": "CORE_CONCEPT", "pattern": [{"LOWER": "时间复杂度"}]},
        {"label": "CORE_CONCEPT", "pattern": [{"LOWER": "空间复杂度"}]},
        {"label": "CORE_CONCEPT", "pattern": [{"LOWER": "递归"}]},
    ]
    
    try:
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(default_patterns, f, ensure_ascii=False, indent=2)
        print(f"✅ 创建默认patterns.json文件，共 {len(default_patterns)} 个模式")
    except Exception as e:
        print(f"❌ 创建patterns.json失败: {e}")

# 测试函数
async def test_single_file():
    """测试单个文件处理"""
    test_content = """
# 01背包问题

01背包问题是动态规划中的经典问题之一。

## 问题描述
给定n个物品，每个物品有重量和价值，背包容量为W，求最大价值。

## 解法思路
使用动态规划，状态转移方程为：dp[i][j] = max(dp[i-1][j], dp[i-1][j-weight[i]] + value[i])

## 时间复杂度
O(nW)，其中n是物品数量，W是背包容量。

## 应用场景
- 资源分配问题
- 投资组合优化
"""
    
    print("🧪 测试单个文件处理...")
    
    extractor = PreciseEntityExtractor()
    kp = await extractor.extract_knowledge_point(test_content, "test_01背包.txt")
    
    print("\n📋 提取结果:")
    print(json.dumps(kp.to_dict(), ensure_ascii=False, indent=2))

def test_base_name_extraction():
    """测试基础名称提取功能"""
    print("🧪 测试文件名提取功能")
    print("=" * 40)
    
    json_manager = JsonFileManager()
    
    test_files = [
        "BFS_kama.txt", "BFS_wiki.txt", "DFS_leetcode.txt", "DFS_官方.txt",
        "动态规划_详解.txt", "动态规划_基础.txt", "KMP_blog.txt", "KMP_csdn.txt",
        "背包问题.txt", "01背包_1.txt", "01背包_2.txt"
    ]
    
    base_name_groups = {}
    
    for filename in test_files:
        base_name = json_manager.extract_base_name(filename)
        json_filename = json_manager.get_json_filename(filename)
        
        if base_name not in base_name_groups:
            base_name_groups[base_name] = []
        base_name_groups[base_name].append(filename)
        
        print(f"📄 {filename} -> {base_name} -> {json_filename}")
    
    print(f"\n📊 分组结果:")
    for base_name, files in base_name_groups.items():
        if len(files) > 1:
            print(f"🔗 {base_name}: {files}")
        else:
            print(f"📄 {base_name}: {files[0]}")

def view_existing_json():
    """查看现有的JSON文件"""
    output_dir = Path("knowledge_points_json")
    if not output_dir.exists():
        print("📁 输出目录不存在")
        return
    
    json_files = list(output_dir.glob("*.json"))
    json_files = [f for f in json_files if not f.name.startswith("processing_report_")]
    
    if not json_files:
        print("📁 暂无JSON文件")
        return
    
    print(f"📚 现有JSON文件 ({len(json_files)}个):")
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"\n📄 {json_file.name}")
                print(f"   🏷️ 名称: {data.get('name', 'Unknown')}")
                print(f"   📝 类型: {data.get('type', 'Unknown')}")
                print(f"   📁 来源: {', '.join(data.get('source_files', []))}")
                
                # 显示问题类型提取结果
                problem_types = data.get('spacy_entities', {}).get('PROBLEM_TYPE', [])
                if problem_types:
                    print(f"   🎯 问题类型: {', '.join(problem_types)}")
                
                concepts = data.get('key_concepts', [])
                if concepts:
                    print(f"   🔑 概念: {', '.join(concepts[:3])}{'...' if len(concepts) > 3 else ''}")
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")

# 主函数
async def main():
    """主函数"""
    print("🚀 算法知识点精确提取系统 v2.1")
    print("🎯 专注于LLM one-shot准确性")
    print("=" * 50)
    
    # 创建默认配置文件
    create_default_patterns_file()
    
    # 初始化主处理器
    try:
        processor = MainProcessor(
            input_dir=r"F:\algokg_platform\data\raw\programmercarl_articles\knowledepoints",
            output_dir=r"F:\algokg_platform\data\raw\knowledgePoint_extraction"
        )
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("请确认输入目录路径正确")
        return
    
    print(f"\n🔧 当前提取方法组合:")
    print(f"  📝 spaCy规则匹配: ✅")
    print(f"  📚 精确词典匹配: ✅") 
    print(f"  🧠 LLM精确增强: ✅")
    print(f"  🔧 智能后处理: ✅")
    
    try:
        # 处理所有文件
        stats = await processor.process_all_files(
            max_files=None,  # 不限制文件数量
            skip_processed=True  # 跳过已处理的文件
        )
        
        # 列出生成的文件
        processor.list_generated_files()
        
        print(f"\n🎉 处理完成！")
        print(f"✅ 成功: {stats['processed_files']}")
        print(f"❌ 失败: {stats['failed_files']}")
        print(f"🆕 新建: {stats['created_json']}")
        print(f"🔄 合并: {stats['merged_json']}")
        print(f"🔗 知识点组: {stats['total_groups']}")
        
    except Exception as e:
        print(f"❌ 处理过程出错: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            # 测试单个文件
            asyncio.run(test_single_file())
        elif command == "view":
            # 查看现有文件
            view_existing_json()
        elif command == "patterns":
            # 创建patterns文件
            create_default_patterns_file()
        elif command == "test-names":
            # 测试文件名提取
            test_base_name_extraction()
        else:
            print("可用命令:")
            print("  test       - 测试单个文件处理")
            print("  view       - 查看现有JSON文件")
            print("  patterns   - 创建默认patterns.json")
            print("  test-names - 测试文件名提取功能")
    else:
        # 运行主程序
        asyncio.run(main())