// API请求和响应类型定义

export interface QARequest {
  query: string;
  query_type?: 'concept_explanation' | 'problem_recommendation' | 'similar_problems' | 'learning_path' | 'code_implementation';
  difficulty?: '简单' | '中等' | '困难';
  context?: Record<string, any>;
  session_id?: string;
}

export interface ConceptExplanation {
  concept_name: string;
  definition: string;
  core_principles: string[];
  when_to_use?: string;
  advantages: string[];
  disadvantages: string[];
  implementation_key_points: string[];
  common_variations: string[];
  real_world_applications: string[];
  learning_progression: Record<string, string[]>;
  visual_explanation?: string;
  clickable_concepts: string[];
}

export interface ProblemInfo {
  id: string;
  title: string;
  description?: string;
  difficulty?: string;
  platform?: string;
  url?: string;
  algorithm_tags: string[];
  data_structure_tags: string[];
  technique_tags: string[];
  solutions: Solution[];
  code_implementations: CodeImplementation[];
  key_insights: Insight[];
  step_by_step_explanation: Step[];
  clickable: boolean;
}

export interface Solution {
  approach: string;
  time_complexity: string;
  space_complexity: string;
  description: string;
}

export interface CodeImplementation {
  language: string;
  code: string;
  description: string;
}

export interface Insight {
  content: string;
  category: string;
}

export interface Step {
  name: string;
  text: string;
  order: number;
  code_snippets?: CodeImplementation[];
}

export interface SimilarProblem {
  title: string;
  hybrid_score: number;
  embedding_score: number;
  tag_score: number;
  shared_tags: string[];
  learning_path: string;
  recommendation_reason: string;
  learning_path_explanation: string;
  recommendation_strength: string;
  complete_info?: ProblemInfo;
  clickable: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
  clickable?: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  center_node?: string;
  layout_type: string;
}

export interface AgentStep {
  agent_name: string;
  step_type: string;
  description: string;
  status: 'success' | 'error' | 'partial' | 'processing';
  start_time: string;
  end_time?: string;
  result?: Record<string, any>;
  confidence?: number;
}

export interface QAResponse {
  response_id: string;
  query: string;
  intent: string;
  entities: string[];
  concept_explanation?: ConceptExplanation;
  example_problems: ProblemInfo[];
  similar_problems: SimilarProblem[];
  recommendations_struct?: Record<string, any>;
  integrated_response: string;
  graph_data?: GraphData;
  reasoning_path: AgentStep[];
  status: 'success' | 'error' | 'partial' | 'processing';
  confidence: number;
  processing_time: number;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface StreamingMessage {
  type: string;
  data: Record<string, any>;
  step_id?: string;
  is_final: boolean;
  timestamp?: string;
}

// UI状态类型
export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  response?: QAResponse;
  isStreaming?: boolean;
  reasoning_steps?: AgentStep[];
  isCancelled?: boolean;
}

export interface AppState {
  // 聊天相关
  messages: ChatMessage[];
  currentQuery: string;
  isLoading: boolean;
  isStreaming: boolean;
  
  // 会话相关
  sessionId: string;
  
  // UI状态
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  activeTab: string;
  
  // 图谱相关
  graphData?: GraphData;
  selectedNode?: GraphNode;
  
  // 错误处理
  error?: string;
}

// 组件Props类型
export interface QueryInputProps {
  onSubmit: (query: string) => void;
  loading?: boolean;
  placeholder?: string;
  onCancel?: () => void;
  isStreaming?: boolean;
}

export interface MessageItemProps {
  message: ChatMessage;
  onConceptClick?: (concept: string) => void;
  onProblemClick?: (problem: string) => void;
}

export interface GraphVisualizationProps {
  data?: GraphData;
  onNodeClick?: (node: GraphNode) => void;
  height?: number | string;
  width?: number | string;
}

export interface ReasoningPathProps {
  steps: AgentStep[];
  isStreaming?: boolean;
}

// API服务类型
export interface ApiService {
  query: (request: QARequest) => Promise<QAResponse>;
  queryStream: (request: QARequest) => AsyncGenerator<StreamingMessage>;
  getSimilarProblems: (problemTitle: string, count?: number) => Promise<SimilarProblem[]>;
  handleConceptClick: (conceptName: string, sourceQuery: string, contextType: string) => Promise<QAResponse>;
  getGraphData: (entityName: string, entityType?: string) => Promise<GraphData>;
}
