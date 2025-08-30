import spacy
from spacy.pipeline import EntityRuler
import json
import re
import asyncio
import uuid
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import logging
import os
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import os
import glob
from extractors.extract_knowledgePoint import QwenClientNative
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------
# 存档管理器
# -----------------------

class CheckpointManager:
    """存档管理器，用于实现断点续传功能"""
    
    def __init__(self, checkpoint_file: str = "extraction_checkpoint.json"):
        self.checkpoint_file = checkpoint_file
        self.processed_files = set()
        self.failed_files = []
        self.total_files = 0
        self.start_time = None
        self.load_checkpoint()
    
    def load_checkpoint(self):
        """加载存档文件"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                    self.failed_files = data.get('failed_files', [])
                    self.total_files = data.get('total_files', 0)
                    self.start_time = data.get('start_time')
                    logger.info(f"已加载存档: 已处理 {len(self.processed_files)} 个文件，失败 {len(self.failed_files)} 个文件")
            except Exception as e:
                logger.error(f"加载存档失败: {e}")
                self.reset_checkpoint()
        else:
            logger.info("未找到存档文件，将从头开始")
    
    def save_checkpoint(self):
        """保存存档文件"""
        try:
            data = {
                'processed_files': list(self.processed_files),
                'failed_files': self.failed_files,
                'total_files': self.total_files,
                'start_time': self.start_time,
                'last_update': datetime.now().isoformat(),
                'progress_percentage': len(self.processed_files) / self.total_files * 100 if self.total_files > 0 else 0
            }
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存存档失败: {e}")
    
    def reset_checkpoint(self):
        """重置存档"""
        self.processed_files = set()
        self.failed_files = []
        self.total_files = 0
        self.start_time = None
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        logger.info("存档已重置")
    
    def initialize_extraction(self, all_files: List[str]):
        """初始化提取任务"""
        if not self.start_time:
            self.start_time = datetime.now().isoformat()
        
        # 更新总文件数
        self.total_files = len(all_files)
        
        # 过滤出需要处理的文件
        files_to_process = [f for f in all_files if f not in self.processed_files]
        
        logger.info(f"总文件数: {self.total_files}")
        logger.info(f"已处理: {len(self.processed_files)}")
        logger.info(f"待处理: {len(files_to_process)}")
        logger.info(f"失败文件: {len(self.failed_files)}")
        
        return files_to_process
    
    def mark_file_processed(self, file_path: str):
        """标记文件为已处理"""
        self.processed_files.add(file_path)
        # 从失败列表中移除（如果存在）
        self.failed_files = [f for f in self.failed_files if f['file'] != file_path]
        self.save_checkpoint()
    
    def mark_file_failed(self, file_path: str, error: str):
        """标记文件处理失败"""
        failure_record = {
            'file': file_path,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        }
        # 更新或添加失败记录
        self.failed_files = [f for f in self.failed_files if f['file'] != file_path]
        self.failed_files.append(failure_record)
        self.save_checkpoint()
    
    def get_progress_info(self) -> Dict[str, Any]:
        """获取进度信息"""
        if self.total_files == 0:
            return {
                'total_files': 0,
                'processed_files': 0,
                'failed_files': 0,
                'remaining_files': 0,
                'progress_percentage': 0,
                'start_time': self.start_time
            }
        
        return {
            'total_files': self.total_files,
            'processed_files': len(self.processed_files),
            'failed_files': len(self.failed_files),
            'remaining_files': self.total_files - len(self.processed_files),
            'progress_percentage': len(self.processed_files) / self.total_files * 100,
            'start_time': self.start_time
        }
    
    def print_progress(self):
        """打印进度信息"""
        info = self.get_progress_info()
        print(f"\n=== 提取进度 ===")
        print(f"总文件数: {info['total_files']}")
        print(f"已处理: {info['processed_files']}")
        print(f"失败: {info['failed_files']}")
        print(f"剩余: {info['remaining_files']}")
        print(f"进度: {info['progress_percentage']:.1f}%")
        if info['start_time']:
            start_time = datetime.fromisoformat(info['start_time'])
            elapsed = datetime.now() - start_time
            print(f"已用时: {elapsed}")
        print("================\n")
    
    def retry_failed_files(self) -> List[str]:
        """获取失败的文件列表，用于重试"""
        return [f['file'] for f in self.failed_files]
    
    def cleanup_checkpoint(self):
        """清理存档文件（任务完成后调用）"""
        if os.path.exists(self.checkpoint_file):
            # 创建最终报告
            final_report = {
                'completion_time': datetime.now().isoformat(),
                'total_files': self.total_files,
                'successful_files': len(self.processed_files),
                'failed_files': self.failed_files,
                'start_time': self.start_time
            }
            
            report_file = f"extraction_final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(final_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"最终报告已保存: {report_file}")
            
            # 删除存档文件
            os.remove(self.checkpoint_file)
            logger.info("存档文件已清理")

# -----------------------
# 枚举和数据类
# -----------------------

class ProblemType(str, Enum):
    """题目平台类型"""
    LEETCODE = "leetcode"
    CODEFORCES = "codeforces"
    ATCODER = "atcoder"
    KAMACODER = "kamacoder"
    CUSTOM = "custom"

class ResourceType(str, Enum):
    """资源类型"""
    IMAGE = "image"
    GIF = "gif"
    CODE = "code"
    TABLE = "table"
    FORMULA = "formula"

class LanguageType(str, Enum):
    """编程语言类型"""
    CPP = "cpp"
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    GO = "go"
    RUST = "rust"
    UNKNOWN = "unknown"

@dataclass
class Example:
    """算法题目的示例"""
    input: str
    output: str
    explanation: Optional[str] = None
    image: Optional[str] = None  # 示例可能附带图片

@dataclass
class Resource:
    """资源（图片、动画、表格等）"""
    type: ResourceType
    content: str  # URL或内容
    description: Optional[str] = None
    context: Optional[str] = None  # 在原文中的上下文

@dataclass
class CodeSolution:
    """代码解决方案"""
    language: LanguageType
    code: str
    description: Optional[str] = None
    
@dataclass
class Section:
    """文档章节"""
    name: str
    text: str = ""
    resources: List[Resource] = field(default_factory=list)
    code_snippets: List[CodeSolution] = field(default_factory=list)
    subsections: List['Section'] = field(default_factory=list)  # 支持嵌套

@dataclass
class ComplexityAnalysis:
    """复杂度分析"""
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    explanation: Optional[str] = None

@dataclass
class AlgorithmInsight:
    """算法洞察"""
    title: str
    content: str
    related_images: List[str] = field(default_factory=list)

@dataclass
class AlgorithmProblemWithSolution:
    """算法问题和题解的完整实体"""
    # 基础信息
    id: str
    title: str
    alternative_titles: List[str] = field(default_factory=list)  # 同类题目
    platform: ProblemType = ProblemType.CUSTOM
    url: Optional[str] = None
    
    # 题目内容
    description: str = ""
    examples: List[Example] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    
    # 标签和分类
    algorithm_tags: List[str] = field(default_factory=list)
    data_structure_tags: List[str] = field(default_factory=list)
    technique_tags: List[str] = field(default_factory=list)
    difficulty: Optional[str] = None
    
    # 题解内容
    solution_approach: str = ""  # 主要解题思路
    key_insights: List[AlgorithmInsight] = field(default_factory=list)  # 关键洞察
    step_by_step_explanation: List[Section] = field(default_factory=list)  # 分步骤讲解
    
    # 复杂度分析
    complexity_analysis: Optional[ComplexityAnalysis] = None
    
    # 代码实现
    code_solutions: List[CodeSolution] = field(default_factory=list)
    
    # 补充内容
    common_mistakes: List[str] = field(default_factory=list)  # 常见错误
    similar_problems: List[str] = field(default_factory=list)  # 相似题目
    follow_up_questions: List[str] = field(default_factory=list)  # 进阶问题
    
    # 资源
    all_resources: List[Resource] = field(default_factory=list)  # 所有资源
    
    # 元数据
    source_file: Optional[str] = None
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_content: Optional[str] = None  # 保存原始内容
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        def convert_section(section):
            return {
                "name": section.name,
                "text": section.text,
                "resources": [asdict(r) for r in section.resources],
                "code_snippets": [asdict(c) for c in section.code_snippets],
                "subsections": [convert_section(s) for s in section.subsections]
            }
        def convert_key_insight(ki):
            if hasattr(ki, '__dataclass_fields__'):
                return asdict(ki)
            elif isinstance(ki, dict):
                return ki
            else:
                return {"content": str(ki)}
        result = asdict(self)
        result['examples'] = [asdict(ex) for ex in self.examples]
        result['key_insights'] = [convert_key_insight(ki) for ki in self.key_insights]
        result['step_by_step_explanation'] = [convert_section(s) for s in self.step_by_step_explanation]
        result['code_solutions'] = [asdict(cs) for cs in self.code_solutions]
        result['all_resources'] = [asdict(r) for r in self.all_resources]
        if self.complexity_analysis:
            result['complexity_analysis'] = asdict(self.complexity_analysis)
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

# -----------------------
# 基础提取器
# -----------------------

class BasicInfoExtractor:
    """基础信息提取器"""
    
    def __init__(self):
        self.nlp = self._setup_nlp()
    
    def _setup_nlp(self):
        """设置spaCy"""
        try:
            nlp = spacy.blank("zh")
            ruler = EntityRuler(nlp, overwrite_ents=True)
            
            patterns = [
                {"label": "TITLE", "pattern": [{"TEXT": {"REGEX": "^[^\n]{2,100}$"}}]},
                {"label": "URL", "pattern": [{"TEXT": {"REGEX": r"https?://[^\s]+"}}]},
                {"label": "SECTION_MARKER", "pattern": [{"TEXT": {"REGEX": r"^#[^#].*"}}]},
            ]
            
            ruler.add_patterns(patterns)
            nlp.add_pipe(ruler)
            return nlp
        except Exception as e:
            logger.error(f"Failed to setup NLP: {e}")
            return spacy.blank("zh")
    
    def extract(self, text: str) -> Dict[str, Any]:
        """提取基础信息"""
        info = {
            "title": None,
            "alternative_titles": [],
            "url": None,
            "platform": ProblemType.CUSTOM,
            "description": "",
            "examples": [],
            "constraints": [],
            "sections": []
        }
        
        # 提取标题
        lines = text.strip().split('\n')
        if lines:
            info["title"] = lines[0].strip()
            
            # 检查是否有同类题目
            if lines and len(lines) > 1 and lines[1].startswith("同："):
                alt_title = lines[1].replace("同：", "").strip()
                info["alternative_titles"].append(alt_title)
        
        # 提取URL和平台
        url_match = re.search(r'https?://[^\s\)]+', text)
        if url_match:
            info["url"] = url_match.group(0).strip()
            info["platform"] = self._detect_platform(info["url"])
        
        # 提取描述
        info["description"] = self._extract_description(text)
        
        # 提取示例
        info["examples"] = self._extract_examples(text)
        
        # 提取约束
        info["constraints"] = self._extract_constraints(text)
        
        # 识别主要章节
        info["sections"] = self._identify_sections(text)
        
        return info
    
    def _detect_platform(self, url: str) -> ProblemType:
        """检测平台"""
        url_lower = url.lower()
        if "leetcode" in url_lower:
            return ProblemType.LEETCODE
        elif "kamacoder" in url_lower:
            return ProblemType.KAMACODER
        return ProblemType.CUSTOM
    
    def _extract_description(self, text: str) -> str:
        """提取描述"""
        # 查找题目描述部分
        desc_patterns = [
            r'(?:给[你定]|请[你]?)(.*?)(?=示例|图示|题目数据)',
            r'力扣题目链接.*?\n\n(.*?)(?=示例|图示|#)'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_examples(self, text: str) -> List[Example]:
        """提取示例"""
        examples = []
        
        # 查找示例部分
        example_pattern = r'示例\s*(\d+)?[:：]?\s*\n(.*?)(?=示例|#|$)'
        matches = re.finditer(example_pattern, text, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            example_text = match.group(2).strip()
            
            # 检查是否有图片
            image_match = re.search(r'https?://[^\s]+\.(?:png|jpg|jpeg|gif)', example_text)
            image_url = image_match.group(0) if image_match else None
            
            # 如果只有图片，创建一个图片示例
            if image_url and len(example_text.strip()) < 100:
                examples.append(Example(
                    input="见图",
                    output="见图",
                    image=image_url
                ))
            else:
                # 尝试解析文本示例
                input_match = re.search(r'输入[:：]\s*(.+?)(?=输出|$)', example_text)
                output_match = re.search(r'输出[:：]\s*(.+?)(?=解释|$)', example_text)
                
                if input_match and output_match:
                    examples.append(Example(
                        input=input_match.group(1).strip(),
                        output=output_match.group(1).strip(),
                        image=image_url
                    ))
        
        return examples
    
    def _extract_constraints(self, text: str) -> List[str]:
        """提取约束条件"""
        constraints = []
        
        constraint_section = re.search(
            r'(?:约束|限制|注意)[:：]?\s*\n(.*?)(?=#|$)',
            text,
            re.MULTILINE | re.DOTALL
        )
        
        if constraint_section:
            constraint_text = constraint_section.group(1).strip()
            # 按行分割
            lines = constraint_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('http'):
                    constraints.append(line)
        
        return constraints
    
    def _identify_sections(self, text: str) -> List[str]:
        """识别主要章节"""
        sections = []
        
        # 查找所有#开头的章节
        section_pattern = r'^#([^#\n]+)$'
        matches = re.finditer(section_pattern, text, re.MULTILINE)
        
        for match in matches:
            section_name = match.group(1).strip()
            sections.append(section_name)
        
        return sections

# -----------------------
# 资源提取Agent
# -----------------------

class ResourceExtractionAgent:
    """使用OpenAI Function Calling提取资源，自动补全所有资源类型的双重提取逻辑"""
    def __init__(self, api_key: str = None, base_url: str = None, llm_client=None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.llm_client = llm_client or QwenClient()

    async def extract_images(self, text: str) -> List[Resource]:
        images = re.findall(r'https?://[^\s]+\.(?:png|jpg|jpeg|webp)', text, re.IGNORECASE)
        prompt = f"""
已用正则初步提取出如下图片链接：
{json.dumps(images, ensure_ascii=False)}
请结合原始内容，补全/修正所有图片链接，只返回图片URL数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return [Resource(type=ResourceType.IMAGE, content=url) for url in json.loads(response)]
        except Exception:
            return [Resource(type=ResourceType.IMAGE, content=url) for url in images]

    async def extract_gifs(self, text: str) -> List[Resource]:
        gifs = re.findall(r'https?://[^\s]+\.gif', text, re.IGNORECASE)
        prompt = f"""
已用正则初步提取出如下GIF链接：
{json.dumps(gifs, ensure_ascii=False)}
请结合原始内容，补全/修正所有GIF链接，只返回GIF URL数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return [Resource(type=ResourceType.GIF, content=url) for url in json.loads(response)]
        except Exception:
            return [Resource(type=ResourceType.GIF, content=url) for url in gifs]

    async def extract_code_solutions(self, text: str) -> List[CodeSolution]:
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        code_blocks = [block.strip('`') for block in code_blocks]
        prompt = f"""
已用正则初步提取出如下代码片段：
{json.dumps(code_blocks, ensure_ascii=False)}
请结合原始内容，补全/修正所有代码片段，只返回代码内容数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return [CodeSolution(language=LanguageType.UNKNOWN, code=code) for code in json.loads(response)]
        except Exception:
            return [CodeSolution(language=LanguageType.UNKNOWN, code=code) for code in code_blocks]

    async def extract_tables(self, text: str) -> List[Resource]:
        tables = re.findall(r'((?:^\|.+\|\n)+)', text, re.MULTILINE)
        prompt = f"""
已用正则初步提取出如下表格：
{json.dumps(tables, ensure_ascii=False)}
请结合原始内容，补全/修正所有 markdown 表格，只返回表格内容数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return [Resource(type=ResourceType.TABLE, content=table) for table in json.loads(response)]
        except Exception:
            return [Resource(type=ResourceType.TABLE, content=table) for table in tables]

    async def extract_examples(self, text: str) -> List[Example]:
        examples = re.findall(r'(?:示例|Example|样例)[\s\S]*?(?=(?:示例|Example|样例|约束|限制|Constraint|$))', text, re.IGNORECASE)
        prompt = f"""
已用正则初步提取出如下示例：
{json.dumps(examples, ensure_ascii=False)}
请结合原始内容，补全/修正所有示例，只返回示例内容数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return [Example(input=ex, output="") for ex in json.loads(response)]
        except Exception:
            return [Example(input=ex, output="") for ex in examples]

    async def extract_constraints(self, text: str) -> List[str]:
        constraints = re.findall(r'(?:约束|限制|Constraints?)[:：]?[\s\S]*?(?=(?:思路|解法|Approach|Solution|$))', text, re.IGNORECASE)
        prompt = f"""
已用正则初步提取出如下约束：
{json.dumps(constraints, ensure_ascii=False)}
请结合原始内容，补全/修正所有约束，只返回约束内容数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return json.loads(response)
        except Exception:
            return constraints

    async def extract_complexities(self, text: str) -> dict:
        time_c = re.findall(r'时间复杂度[:：]\s*O?\(([^)]+)\)', text)
        space_c = re.findall(r'空间复杂度[:：]\s*O?\(([^)]+)\)', text)
        prompt = f"""
已用正则初步提取出如下复杂度：
时间复杂度: {json.dumps(time_c, ensure_ascii=False)}
空间复杂度: {json.dumps(space_c, ensure_ascii=False)}
请结合原始内容，补全/修正时间复杂度和空间复杂度，只返回如下JSON：{{"time_complexity": "...", "space_complexity": "..."}}，不要有其他内容。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return json.loads(response)
        except Exception:
            return {"time_complexity": time_c[0] if time_c else None, "space_complexity": space_c[0] if space_c else None}

    async def extract_tags(self, text: str) -> List[str]:
        tags = re.findall(r'(?:标签|Tags?)[:：]\s*(.+)', text)
        prompt = f"""
已用正则初步提取出如下标签：
{json.dumps(tags, ensure_ascii=False)}
请结合原始内容，补全/修正所有标签，只返回标签内容数组（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return json.loads(response)
        except Exception:
            return tags

    async def extract_title(self, text: str) -> str:
        lines = text.strip().split('\n')
        title = lines[0].strip() if lines else ""
        prompt = f"""
已用正则初步提取出如下标题：{title}
请结合原始内容，补全/修正标题，只返回标题字符串（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip().replace('\n', '')
        except Exception:
            return title

    async def extract_url(self, text: str) -> str:
        url = re.search(r'https?://[\w\.-/]+', text)
        url = url.group(0) if url else ""
        prompt = f"""
已用正则初步提取出如下URL：{url}
请结合原始内容，补全/修正URL，只返回URL字符串（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip().replace('\n', '')
        except Exception:
            return url

    async def extract_platform(self, text: str) -> str:
        url = re.search(r'https?://[\w\.-/]+', text)
        url = url.group(0) if url else ""
        platform = "leetcode" if "leetcode" in url else ("codeforces" if "codeforces" in url else ("atcoder" if "atcoder" in url else ("kamacoder" if "kamacoder" in url else "custom")))
        prompt = f"""
已用正则初步提取出如下平台：{platform}
请结合原始内容，补全/修正平台，只返回平台字符串（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip().replace('\n', '')
        except Exception:
            return platform

    async def extract_description(self, text: str) -> str:
        desc_match = re.search(r'(?:题目描述|问题描述|Description)[:：]?\s*\n(.*?)(?=(?:示例|Example|约束|Constraints|思路)|$)', text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        desc = desc_match.group(1).strip() if desc_match else ""
        prompt = f"""
已用正则初步提取出如下描述：{desc}
请结合原始内容，补全/修正题目描述，只返回描述字符串（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip()
        except Exception:
            return desc

    async def extract_thought_process(self, text: str) -> str:
        thought_match = re.search(r'(?:#?\s*(?:思路|解题思路|解法|Approach|Solution))[:：]?\s*\n(.*?)(?=(?:#?\s*代码|Code|实现)|$)', text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else ""
        prompt = f"""
已用正则初步提取出如下思路：{thought}
请结合原始内容，补全/修正思路，只返回思路字符串（不要解释，不要加任何注释）。
原始内容如下：
{text}
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip()
        except Exception:
            return thought

    async def extract_all_resources(self, text: str) -> dict:
        images = await self.extract_images(text)
        gifs = await self.extract_gifs(text)
        code_solutions = await self.extract_code_solutions(text)
        tables = await self.extract_tables(text)
        examples = await self.extract_examples(text)
        constraints = await self.extract_constraints(text)
        complexities = await self.extract_complexities(text)
        tags = await self.extract_tags(text)
        title = await self.extract_title(text)
        url = await self.extract_url(text)
        platform = await self.extract_platform(text)
        description = await self.extract_description(text)
        thought_process = await self.extract_thought_process(text)
        return {
            "images": images,
            "gifs": gifs,
            "code_solutions": code_solutions,
            "tables": tables,
            "examples": examples,
            "constraints": constraints,
            "complexities": complexities,
            "tags": tags,
            "title": title,
            "url": url,
            "platform": platform,
            "description": description,
            "thought_process": thought_process
        }

# -----------------------
# 题解分析Agent
# -----------------------

class SolutionAnalysisAgent:
    """分析题解内容"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def analyze_solution(self, text: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析题解"""
        prompt = f"""
请分析以下算法题解，提取结构化信息。

题目：{basic_info.get('title', '')}

题解内容：
{text[:4000]}

请提取：
1. 解题思路的核心步骤
2. 关键洞察（为什么这样做可以解决问题）
3. 算法标签
4. 数据结构标签
5. 技巧标签
6. 常见错误或注意事项

返回JSON格式：
{{
  "solution_approach": "整体解题思路",
  "key_insights": [
    {{"title": "洞察标题", "content": "洞察内容"}}
  ],
  "algorithm_tags": ["标签1", "标签2"],
  "data_structure_tags": ["标签1", "标签2"],
  "technique_tags": ["标签1", "标签2"],
  "common_mistakes": ["错误1", "错误2"],
  "step_by_step": [
    {{"step": "步骤1", "explanation": "说明"}}
  ]
}}
"""
        
        messages = [
            {"role": "system", "content": "你是算法题解分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.llm_client.chat_completion_async(messages)
            if not response or not response.strip():
                logger.error("SolutionAnalysisAgent: LLM返回内容为空")
                return {}
            match = re.search(r'\{.*\}', response, re.DOTALL)
            json_str = match.group(0) if match else response
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Solution analysis failed: {e}, 原始LLM响应: {locals().get('response', '')}")
            return {}

# -----------------------
# 章节组织Agent
# -----------------------

class SectionOrganizationAgent:
    """组织内容为结构化章节"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def organize_sections(
        self,
        text: str,
        sections: List[str],
        resources: Dict[str, List[Any]]
    ) -> List[Section]:
        """组织章节"""
        organized_sections = []
        
        # 对每个识别出的章节进行处理
        for section_name in sections:
            section = await self._process_section(text, section_name, resources)
            if section:
                organized_sections.append(section)
        
        return organized_sections
    
    async def _process_section(
        self,
        text: str,
        section_name: str,
        resources: Dict[str, List[Any]]
    ) -> Optional[Section]:
        """处理单个章节"""
        # 提取该章节的内容
        section_pattern = rf'#{re.escape(section_name)}\s*\n(.*?)(?=\n#|$)'
        match = re.search(section_pattern, text, re.MULTILINE | re.DOTALL)
        
        if not match:
            return None
        
        section_content = match.group(1).strip()
        
        # 创建章节对象
        section = Section(
            name=section_name,
            text=section_content
        )
        
        # 分配相关资源
        # 检查内容中是否引用了图片
        for resource in resources.get("images", []):
            if resource.content in section_content:
                section.resources.append(resource)
        
        # 检查是否有代码
        for code_solution in resources.get("code_solutions", []):
            if code_solution.code[:50] in section_content:
                section.code_snippets.append(code_solution)
        
        # 检查子章节（##开头的）
        subsection_pattern = r'##([^#\n]+)\s*\n(.*?)(?=##|$)'
        subsection_matches = re.finditer(subsection_pattern, section_content, re.MULTILINE | re.DOTALL)
        
        for submatch in subsection_matches:
            subsection_name = submatch.group(1).strip()
            subsection_content = submatch.group(2).strip()
            
            subsection = Section(
                name=subsection_name,
                text=subsection_content
            )
            
            section.subsections.append(subsection)
        
        return section

# -----------------------
# 主提取器
# -----------------------

class OntologyFillingAgent:
    """LLM Agent 用于补全本体属性"""
    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def fill(self, text: str, current_info: dict) -> dict:
        prompt = f"""
请根据下列算法题原文和已提取结构，补全以下属性：
- algorithm_tags: 算法标签（如动态规划、贪心、二分等，数组）
- data_structure_tags: 数据结构标签（如链表、树、堆等，数组）
- technique_tags: 技巧标签（如双指针、滑动窗口等，数组）
- solution_approach: 主要解题思路（简明扼要，字符串）
- key_insights: 关键洞察（数组，每个元素为字符串）

请只返回如下JSON：
{{
  "algorithm_tags": [...],
  "data_structure_tags": [...],
  "technique_tags": [...],
  "solution_approach": "...",
  "key_insights": [...]
}}
不要包含 difficulty 字段，也不要有多余内容。

原文：
{text}

已提取结构：
{json.dumps(current_info, ensure_ascii=False)}
"""
        messages = [
            {"role": "system", "content": "你是算法题目本体属性补全专家。"},
            {"role": "user", "content": prompt}
        ]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            if not response or not response.strip():
                logger.error("OntologyFillingAgent: LLM返回内容为空")
                return {}
            match = re.search(r'\{.*\}', response, re.DOTALL)
            json_str = match.group(0) if match else response
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Ontology filling failed: {e}, 原始LLM响应: {locals().get('response', '')}")
            return {}

class CodeSnippetFillingAgent:
    """LLM Agent 用于补全 Section 的 code_snippets 及多语言 code_solution"""
    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def fill_section_code_snippets(self, section: Section, full_text: str) -> List[CodeSolution]:
        code_blocks = re.findall(r'```[\s\S]*?```', section.text)
        code_blocks = [block.strip('`') for block in code_blocks]
        prompt = f"""
请根据下列章节内容和原文，补全所有代码片段，识别语言类型，返回如下JSON数组：
[
  {{"language": "python/cpp/java/...", "code": "...", "description": "简要说明"}}
]
章节内容：
{section.text}
原文：
{full_text}
已用正则初步提取代码片段：
{json.dumps(code_blocks, ensure_ascii=False)}
必须遵守：只返回JSON数组，不要包含任何解释、注释、多语言代码等。
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            if not response or not response.strip():
                logger.error("CodeSnippetFillingAgent: LLM返回内容为空")
                return [CodeSolution(language=LanguageType.UNKNOWN, code=code) for code in code_blocks]
            match = re.search(r'\[\[{].*[\]\}]', response, re.DOTALL)
            json_str = match.group(0) if match else response
            return [CodeSolution(**item) for item in json.loads(json_str)]
        except Exception as e:
            logger.error(f"Code snippet filling failed: {e}, 原始LLM响应: {locals().get('response', '')}")
            return [CodeSolution(language=LanguageType.UNKNOWN, code=code) for code in code_blocks]

    async def fill_all_section_code_snippets(self, sections: List[Section], full_text: str) -> None:
        for section in sections:
            section.code_snippets = await self.fill_section_code_snippets(section, full_text)
            if hasattr(section, 'subsections') and section.subsections:
                await self.fill_all_section_code_snippets(section.subsections, full_text)

    async def extract_code_solutions(self, text: str) -> List[CodeSolution]:
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        code_blocks = [block.strip('`') for block in code_blocks]
        prompt = f"""
请根据下列原文，识别所有主要代码实现，区分不同语言，返回如下JSON数组：
[
  {{"language": "python/cpp/java/...", "code": "...", "description": "简要说明"}}
]
原文：
{text}
已用正则初步提取代码片段：
{json.dumps(code_blocks, ensure_ascii=False)}
必须遵守：只返回JSON数组，不要包含任何解释、注释、多语言代码等。
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self.llm_client.chat_completion_async(messages)
            if not response or not response.strip():
                logger.error("CodeSnippetFillingAgent: LLM返回内容为空")
                return [CodeSolution(language=LanguageType.UNKNOWN, code=code) for code in code_blocks]
            match = re.search(r'\[\[{].*[\]\}]', response, re.DOTALL)
            json_str = match.group(0) if match else response
            return [CodeSolution(**item) for item in json.loads(json_str)]
        except Exception as e:
            logger.error(f"Code solution extraction failed: {e}, 原始LLM响应: {locals().get('response', '')}")
            return [CodeSolution(language=LanguageType.UNKNOWN, code=code) for code in code_blocks]

class ImageDescriptionAgent:
    """图片识别与描述 Agent，使用 Qwen-VL 进行图片识别"""
    def __init__(self, llm_client, api_key=None, base_url=None):
        self.llm_client = llm_client
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        self.vision_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def get_image_description(self, image_url: str) -> str:
        """使用 Qwen-VL 获取图片描述"""
        try:
            logger.info(f"正在识别图片: {image_url}")
            completion = await self.vision_client.chat.completions.create(
                model="qwen-vl-max",  # 使用 qwen-vl-max 模型
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的图片分析助手。请简洁准确地描述图片内容，特别关注算法和数据结构相关的内容。"
                    },
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            },
                            {
                                "type": "text", 
                                "text": "请用一句话简洁地描述这张图片的主要内容，重点关注算法、数据结构或解题过程。"
                            }
                        ]
                    }
                ]
            )
            description = completion.choices[0].message.content.strip()
            logger.info(f"图片识别成功: {description}")
            return description
        except Exception as e:
            logger.error(f"图片识别失败 {image_url}: {e}")
            return f"图片链接: {image_url}"

    async def get_image_context_from_text(self, image_url: str, section_text: str) -> str:
        """根据章节文本内容生成图片的上下文说明"""
        try:
            # 找到图片URL在文本中的位置和周围内容
            url_index = section_text.find(image_url)
            if url_index == -1:
                return "图片相关说明"
            
            # 提取图片前后的文本作为上下文
            start = max(0, url_index - 200)
            end = min(len(section_text), url_index + len(image_url) + 200)
            context_text = section_text[start:end]
            
            prompt = f"""
根据以下文本内容，为图片生成一个简洁的上下文说明：

文本内容：
{context_text}

图片链接：{image_url}

请根据图片在文本中的位置和周围内容，生成一句话的上下文说明，描述这张图片在当前内容中的作用或相关性。
只返回说明文字，不要包含其他内容。
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip() if response else "相关图片说明"
            
        except Exception as e:
            logger.error(f"生成图片上下文失败 {image_url}: {e}")
            return "相关图片说明"

    async def get_gif_description_from_context(self, gif_url: str, full_text: str) -> str:
        """根据上下文内容为GIF生成描述"""
        try:
            # 找到GIF URL在文本中的位置和周围内容
            url_index = full_text.find(gif_url)
            if url_index == -1:
                return "动画演示"
            
            # 提取GIF前后更大范围的文本作为上下文
            start = max(0, url_index - 300)
            end = min(len(full_text), url_index + len(gif_url) + 300)
            context_text = full_text[start:end]
            
            prompt = f"""
根据以下算法题解的上下文内容，为GIF动画生成一个简洁的描述：

上下文内容：
{context_text}

GIF链接：{gif_url}

这是一个算法题解中的GIF动画。请根据周围的文本内容，推断这个GIF可能展示的内容，生成一句话的描述。
常见的算法GIF包括：
- 算法执行过程演示
- 数据结构操作过程
- 指针移动过程
- 递归调用过程
- 排序算法过程

只返回描述文字，不要包含其他内容。
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip() if response else "算法过程动画演示"
            
        except Exception as e:
            logger.error(f"生成GIF描述失败 {gif_url}: {e}")
            return "算法过程动画演示"

    async def get_gif_context_from_text(self, gif_url: str, section_text: str) -> str:
        """根据章节文本内容生成GIF的上下文说明"""
        try:
            # 找到GIF URL在文本中的位置和周围内容
            url_index = section_text.find(gif_url)
            if url_index == -1:
                return "动画演示说明"
            
            # 提取GIF前后的文本作为上下文
            start = max(0, url_index - 200)
            end = min(len(section_text), url_index + len(gif_url) + 200)
            context_text = section_text[start:end]
            
            prompt = f"""
根据以下文本内容，为GIF动画生成一个简洁的上下文说明：

文本内容：
{context_text}

GIF链接：{gif_url}

请根据GIF在文本中的位置和周围内容，生成一句话的上下文说明，描述这个GIF动画在当前算法解释中的作用。
只返回说明文字，不要包含其他内容。
"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_client.chat_completion_async(messages)
            return response.strip() if response else "动画演示说明"
            
        except Exception as e:
            logger.error(f"生成GIF上下文失败 {gif_url}: {e}")
            return "动画演示说明"

    async def fill_all_image_info(self, all_resources: List[Resource], full_text: str):
        """批量填充所有图片和GIF资源的描述和上下文"""
        image_count = sum(1 for r in all_resources if r.type in [ResourceType.IMAGE, ResourceType.GIF])
        logger.info(f"开始处理 {image_count} 个图片/GIF资源...")
        
        # 创建并发任务
        tasks = []
        for resource in all_resources:
            if resource.type == ResourceType.IMAGE:
                # 图片：使用视觉识别 + 文本上下文
                desc_task = self.get_image_description(resource.content)
                context_task = self.get_image_context_from_text(resource.content, full_text)
                tasks.append((resource, desc_task, context_task))
            elif resource.type == ResourceType.GIF:
                # GIF：仅使用文本上下文分析
                desc_task = self.get_gif_description_from_context(resource.content, full_text)
                context_task = self.get_gif_context_from_text(resource.content, full_text)
                tasks.append((resource, desc_task, context_task))
        
        # 并发执行所有任务
        for resource, desc_task, context_task in tasks:
            try:
                # 等待描述和上下文任务完成
                description, context = await asyncio.gather(desc_task, context_task)
                resource.description = description
                resource.context = context
                
                resource_type = "图片" if resource.type == ResourceType.IMAGE else "GIF"
                logger.info(f"已完成{resource_type}处理: {resource.content[:50]}...")
            except Exception as e:
                logger.error(f"处理{resource.type}资源失败 {resource.content}: {e}")
                if resource.type == ResourceType.IMAGE:
                    resource.description = f"图片链接: {resource.content}"
                    resource.context = "相关图片说明"
                else:  # GIF
                    resource.description = "算法过程动画演示"
                    resource.context = "动画演示说明"

    async def fill_section_image_descriptions(self, section: Section):
        """为章节中的图片和GIF资源填充描述"""
        logger.info(f"处理章节图片/GIF: {getattr(section, 'name', 'Unknown')}")
        
        tasks = []
        for resource in section.resources:
            if resource.type == ResourceType.IMAGE and (not resource.description or resource.description.strip() == ""):
                tasks.append(self.get_image_description(resource.content))
            elif resource.type == ResourceType.GIF and (not resource.description or resource.description.strip() == ""):
                tasks.append(self.get_gif_description_from_context(resource.content, section.text))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # 创建空任务
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            task_index = 0
            for resource in section.resources:
                if resource.type == ResourceType.IMAGE and (not resource.description or resource.description.strip() == ""):
                    result = results[task_index]
                    if isinstance(result, Exception):
                        logger.error(f"图片识别失败: {result}")
                        resource.description = f"图片链接: {resource.content}"
                    else:
                        resource.description = result
                    task_index += 1
                elif resource.type == ResourceType.GIF and (not resource.description or resource.description.strip() == ""):
                    result = results[task_index]
                    if isinstance(result, Exception):
                        logger.error(f"GIF描述生成失败: {result}")
                        resource.description = "算法过程动画演示"
                    else:
                        resource.description = result
                    task_index += 1
        
        # 递归处理子章节
        if hasattr(section, 'subsections') and section.subsections:
            for sub in section.subsections:
                await self.fill_section_image_descriptions(sub)

    async def fill_section_image_context(self, section: Section):
        """为章节中的图片和GIF资源填充上下文"""
        tasks = []
        for resource in section.resources:
            if resource.type == ResourceType.IMAGE:
                tasks.append(self.get_image_context_from_text(resource.content, section.text))
            elif resource.type == ResourceType.GIF:
                tasks.append(self.get_gif_context_from_text(resource.content, section.text))
            else:
                tasks.append(asyncio.create_task(asyncio.sleep(0)))  # 创建空任务
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            task_index = 0
            for resource in section.resources:
                if resource.type in [ResourceType.IMAGE, ResourceType.GIF]:
                    result = results[task_index]
                    if isinstance(result, Exception):
                        logger.error(f"生成{resource.type}上下文失败: {result}")
                        resource.context = "相关说明" if resource.type == ResourceType.IMAGE else "动画演示说明"
                    else:
                        resource.context = result
                    task_index += 1
        
        # 递归处理子章节
        if hasattr(section, 'subsections') and section.subsections:
            for sub in section.subsections:
                await self.fill_section_image_context(sub)

def assign_resources_to_sections(sections, all_resources):
    """将资源分配到对应的章节中"""
    for section in sections:
        section.resources = []
        for res in all_resources:
            if (hasattr(res, 'type') and hasattr(res, 'content') and 
                res.type in [ResourceType.IMAGE, ResourceType.GIF] and 
                res.content in section.text):
                section.resources.append(res)
        # 递归处理子章节
        if hasattr(section, 'subsections') and section.subsections:
            assign_resources_to_sections(section.subsections, all_resources)

class ComprehensiveAlgorithmExtractor:
    """完整的算法题目和题解提取器"""
    
    def __init__(self, llm_client=None):
        self.basic_extractor = BasicInfoExtractor()
        self.resource_agent = ResourceExtractionAgent()
        self.llm_client = llm_client or QwenClient()
        self.solution_agent = SolutionAnalysisAgent(self.llm_client)
        self.section_agent = SectionOrganizationAgent(self.llm_client)
        self.ontology_agent = OntologyFillingAgent(self.llm_client)
        self.code_agent = CodeSnippetFillingAgent(self.llm_client)
        self.image_agent = ImageDescriptionAgent(self.llm_client)

    async def extract(self, text: str, source_file: Optional[str] = None) -> AlgorithmProblemWithSolution:
        logger.info("开始提取算法题目和题解...")
        
        # 1. 提取基础信息
        logger.info("Step 1: 提取基础信息...")
        basic_info = self.basic_extractor.extract(text)
        
        # 2. 提取资源
        logger.info("Step 2: 提取资源...")
        resources = await self.resource_agent.extract_all_resources(text)
        
        # 3. 分析题解
        logger.info("Step 3: 分析题解内容...")
        solution_analysis = await self.solution_agent.analyze_solution(text, basic_info)
        
        # 4. 组织章节
        logger.info("Step 4: 组织章节结构...")
        sections = await self.section_agent.organize_sections(
            text,
            basic_info["sections"],
            resources
        )
        
        # 4.0 分配图片资源到 section.resources
        all_resources = (resources.get("images", []) + resources.get("gifs", []))
        assign_resources_to_sections(sections, all_resources)
        
        # 4.1 LLM补全每个Section的code_snippets
        logger.info("Step 4.1: LLM补全每个Section的code_snippets...")
        await self.code_agent.fill_all_section_code_snippets(sections, text)
        
        # 4.2 LLM补全多语言code_solutions
        logger.info("Step 4.2: LLM补全多语言code_solutions...")
        code_solutions = await self.code_agent.extract_code_solutions(text)
        
        # 4.3 批量处理所有图片的描述和上下文 (主要修改点)
        logger.info("Step 4.3: 批量处理图片识别和上下文生成...")
        await self.image_agent.fill_all_image_info(all_resources, text)
        
        # 5. 提取复杂度
        complexity = self._extract_complexity(text)
        
        # 6. LLM补全本体属性
        logger.info("Step 5: LLM补全本体属性...")
        current_info = {
            "algorithm_tags": solution_analysis.get("algorithm_tags", []),
            "data_structure_tags": solution_analysis.get("data_structure_tags", []),
            "technique_tags": solution_analysis.get("technique_tags", []),
            "solution_approach": solution_analysis.get("solution_approach", ""),
            "key_insights": [ins.get("content", "") for ins in solution_analysis.get("key_insights", [])]
        }
        ontology_filled = await self.ontology_agent.fill(text, current_info)
        
        # 7. 创建最终对象
        problem = AlgorithmProblemWithSolution(
            id=f"AP_{uuid.uuid4().hex[:8]}",
            title=basic_info["title"],
            alternative_titles=basic_info["alternative_titles"],
            platform=basic_info["platform"],
            url=basic_info["url"],
            description=basic_info["description"],
            examples=basic_info["examples"],
            constraints=basic_info["constraints"],
            # LLM补全属性
            algorithm_tags=ontology_filled.get("algorithm_tags", []),
            data_structure_tags=ontology_filled.get("data_structure_tags", []),
            technique_tags=ontology_filled.get("technique_tags", []),
            solution_approach=ontology_filled.get("solution_approach", ""),
            key_insights=ontology_filled.get("key_insights", []),
            # 题解内容
            common_mistakes=solution_analysis.get("common_mistakes", []),
            step_by_step_explanation=sections,
            complexity_analysis=complexity,
            code_solutions=code_solutions,
            all_resources=all_resources,
            source_file=source_file,
            raw_content=text.strip()
        )
        
        logger.info("提取完成!")
        return problem
    
    def _extract_complexity(self, text: str) -> Optional[ComplexityAnalysis]:
        """提取复杂度分析"""
        time_match = re.search(r'时间复杂度[:：]?\s*O?\(([^)]+)\)', text)
        space_match = re.search(r'空间复杂度[:：]?\s*O?\(([^)]+)\)', text)
        
        if time_match or space_match:
            # 查找复杂度说明
            complexity_section = re.search(
                r'(时间复杂度.*?空间复杂度.*?)(?=\n#|$)',
                text,
                re.MULTILINE | re.DOTALL
            )
            
            explanation = None
            if complexity_section:
                # 提取说明文本
                explain_match = re.search(
                    r'[，,](.*?)(?=\n|$)',
                    complexity_section.group(1)
                )
                if explain_match:
                    explanation = explain_match.group(1).strip()
            
            return ComplexityAnalysis(
                time_complexity=f"O({time_match.group(1)})" if time_match else None,
                space_complexity=f"O({space_match.group(1)})" if space_match else None,
                explanation=explanation
            )
        
        return None

# -----------------------
# Qwen客户端
# -----------------------

class QwenClient:
    """Qwen模型客户端"""
    def __init__(self, api_key: str = None, base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def chat_completion_async(self, messages: List[Dict], model: str = "qwen-max") -> str:
        try:
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Qwen API调用失败: {e}")
            return "{}"

# -----------------------
# 使用示例
# -----------------------

async def main():
    input_root = r"F:\algokg_platform\data\raw\programmercarl_articles\problems"
    output_root = r"F:\algokg_platform\data\problem_extration"
    os.makedirs(output_root, exist_ok=True)

    # 递归查找所有 txt 文件
    txt_files = glob.glob(os.path.join(input_root, "**", "*.txt"), recursive=True)
    print(f"共发现 {len(txt_files)} 个 txt 文件...")

    extractor = ComprehensiveAlgorithmExtractor()

    for txt_path in txt_files:
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"处理: {txt_path}")
            problem = await extractor.extract(text)
            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(txt_path))[0]
            output_path = os.path.join(output_root, base_name + ".json")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(problem.to_json())
            print(f"已保存: {output_path}\n")
        except Exception as e:
            print(f"处理失败: {txt_path}, 错误: {e}")

# -----------------------
# 使用示例 - 修改后的main函数
# -----------------------

async def main():
    input_root = r"F:\algokg_platform\data\raw\programmercarl_articles\problems"
    output_root = r"F:\algokg_platform\data\raw\problem_extration"
    
    # 创建存档管理器
    checkpoint_manager = CheckpointManager("algorithm_extraction_checkpoint.json")
    
    # 递归查找所有 txt 文件
    txt_files = glob.glob(os.path.join(input_root, "**", "*.txt"), recursive=True)
    
    # 初始化提取任务，获取需要处理的文件
    files_to_process = checkpoint_manager.initialize_extraction(txt_files)
    
    # 如果没有文件需要处理
    if not files_to_process:
        print("所有文件都已处理完成！")
        checkpoint_manager.print_progress()
        
        # 询问是否重试失败的文件
        failed_files = checkpoint_manager.retry_failed_files()
        if failed_files:
            retry_choice = input(f"发现 {len(failed_files)} 个失败的文件，是否重试？(y/n): ")
            if retry_choice.lower() == 'y':
                files_to_process = failed_files
                print("开始重试失败的文件...")
            else:
                checkpoint_manager.cleanup_checkpoint()
                return
        else:
            checkpoint_manager.cleanup_checkpoint()
            return
    
    # 创建输出目录
    os.makedirs(output_root, exist_ok=True)
    
    # 初始化提取器
    extractor = ComprehensiveAlgorithmExtractor()
    
    print(f"开始处理 {len(files_to_process)} 个文件...")
    checkpoint_manager.print_progress()
    
    # 处理文件
    for i, txt_path in enumerate(files_to_process, 1):
        try:
            print(f"[{i}/{len(files_to_process)}] 处理: {txt_path}")
            
            # 检查输出文件是否已存在
            relative_path = os.path.relpath(txt_path, input_root)
            json_relative_path = os.path.splitext(relative_path)[0] + ".json"
            output_path = os.path.join(output_root, json_relative_path)
            
            # 如果输出文件已存在且不为空，跳过处理
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"输出文件已存在，跳过: {output_path}")
                checkpoint_manager.mark_file_processed(txt_path)
                continue
            
            # 读取文件内容
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # 提取算法题目信息
            problem = await extractor.extract(text, source_file=txt_path)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存JSON文件
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(problem.to_json())
            
            # 标记文件为已处理
            checkpoint_manager.mark_file_processed(txt_path)
            
            print(f"✓ 已保存: {output_path}")
            print(f"目录结构: {relative_path} -> {json_relative_path}")
            
            # 每10个文件打印一次进度
            if i % 10 == 0:
                checkpoint_manager.print_progress()
            
        except KeyboardInterrupt:
            print("\n用户中断，进度已保存到存档文件")
            checkpoint_manager.save_checkpoint()
            break
            
        except Exception as e:
            print(f"✗ 处理失败: {txt_path}")
            print(f"错误: {e}")
            
            # 标记文件处理失败
            checkpoint_manager.mark_file_failed(txt_path, str(e))
            
            # 打印详细错误信息（可选）
            import traceback
            traceback.print_exc()
            
            # 继续处理下一个文件
            continue
    
    # 最终进度报告
    print("\n=== 提取完成 ===")
    checkpoint_manager.print_progress()
    
    # 显示失败的文件
    failed_files = checkpoint_manager.retry_failed_files()
    if failed_files:
        print(f"失败的文件 ({len(failed_files)} 个):")
        for failed_file in failed_files:
            print(f"  - {failed_file}")
        print("\n可以重新运行程序来重试失败的文件")
    else:
        print("所有文件都已成功处理！")
        checkpoint_manager.cleanup_checkpoint()

# -----------------------
# 辅助函数：重置存档
# -----------------------

def reset_checkpoint():
    """重置存档的辅助函数"""
    checkpoint_manager = CheckpointManager("algorithm_extraction_checkpoint.json")
    checkpoint_manager.reset_checkpoint()
    print("存档已重置，下次运行将从头开始")

# -----------------------
# 辅助函数：查看进度
# -----------------------

def check_progress():
    """查看当前进度的辅助函数"""
    checkpoint_manager = CheckpointManager("algorithm_extraction_checkpoint.json")
    checkpoint_manager.print_progress()
    
    failed_files = checkpoint_manager.retry_failed_files()
    if failed_files:
        print("失败的文件:")
        for i, failed_file in enumerate(failed_files[:10], 1):  # 只显示前10个
            print(f"  {i}. {failed_file}")
        if len(failed_files) > 10:
            print(f"  ... 还有 {len(failed_files) - 10} 个失败文件")

if __name__ == "__main__":
    import asyncio
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "reset":
            reset_checkpoint()
        elif sys.argv[1] == "progress":
            check_progress()
        else:
            print("用法:")
            print("  python script.py          # 正常运行")
            print("  python script.py reset    # 重置存档")
            print("  python script.py progress # 查看进度")
    else:
        asyncio.run(main())