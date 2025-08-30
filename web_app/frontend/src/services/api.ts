import axios, { AxiosInstance } from 'axios';
import { QARequest, QAResponse, SimilarProblem, GraphData, StreamingMessage } from '../types';

export type LLMMessage = { role: 'system' | 'user' | 'assistant'; content: string };

export type LLMChatRequest = {
  model?: string;          // 如 'qwen3:8b'
  messages: LLMMessage[];
  temperature?: number;
  max_tokens?: number;
  keepalive?: number;      // 秒
};

export type LLMChatResult = {
  content: string;
  model?: string;
  finish_reason?: string;
  usage?: Record<string, any>;
};


class ApiService {
  private client: AxiosInstance;
  private baseURL: string;

    
  

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 180000, // 增加到3分钟 (180秒)
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.client.interceptors.request.use(
      (config) => {
        console.log(`发送请求: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('请求错误:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.client.interceptors.response.use(
      (response) => {
        console.log(`收到响应: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('响应错误:', error);

        // 检查是否是用户主动取消的请求
        if (error.code === 'ERR_CANCELED' || error.message?.includes('canceled')) {
          // 用户主动取消，不显示错误提示
          throw error;
        }

        if (error.response?.status === 500) {
          throw new Error('服务器内部错误，请稍后重试');
        } else if (error.response?.status === 404) {
          throw new Error('请求的资源不存在');
        } else if (error.code === 'ECONNABORTED') {
          throw new Error('查询处理时间较长，请稍后重试或简化问题');
        } else if (error.response?.status === 504) {
          throw new Error('网关超时，服务器处理时间过长');
        } else if (error.response?.status === 502) {
          throw new Error('服务器连接错误，请稍后重试');
        }
        throw error;
      }
    );
  }
    // ===== 新增：与后端 llm_proxy 交互 =====

  // 非流式：POST /api/v1/llm/chat
  async llmChat(req: LLMChatRequest, signal?: AbortSignal): Promise<LLMChatResult> {
    const resp = await this.client.post<LLMChatResult>(
      '/api/v1/llm/chat',
      req,
      { signal, timeout: 180000 }
    );
    return resp.data;
  }

  // 流式：SSE 读取 /api/v1/llm/chat/stream
  async* llmChatStream(req: LLMChatRequest, signal?: AbortSignal): AsyncGenerator<StreamingMessage> {
      const response = await fetch(`${this.baseURL}/api/v1/llm/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(req),
        signal,
        cache: 'no-store',
      });
    
      if (!response.ok || !response.body) {
        throw new Error(`LLM stream error: ${response.status}`);
      }
    
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
    
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
    
          // 关键：按空行分事件
          const events = buffer.split(/\r?\n\r?\n/);
          buffer = events.pop() || '';
    
          for (const evt of events) {
            // 只处理以 data: 开头的行
            const line = evt.split(/\r?\n/).find(l => l.startsWith('data:'));
            if (!line) continue;
    
            const jsonStr = line.slice(5).trim();
            if (jsonStr === '[DONE]') return;
    
            try {
              const parsed = JSON.parse(jsonStr);
              const msg: StreamingMessage = {
                type: parsed.type || 'text',
                data: parsed.data || { content: '' },
                is_final: !!parsed.is_final,
              };
              yield msg;
            } catch (e) {
              console.warn('LLM stream parse error:', e, jsonStr);
            }
          }
        }
      } finally {
        try { reader.releaseLock(); } catch {}
      }
    }


  /**
   * 发送问答查询 - 针对复杂查询使用更长的超时时间
   */
  async query(request: QARequest, signal?: AbortSignal): Promise<QAResponse> {
    try {
      const response = await this.client.post<QAResponse>('/api/v1/qa/query', request, {
        signal,
        timeout: 180000, // 单独为QA查询设置3分钟超时
      });
      return response.data;
    } catch (error) {
      console.error('查询失败:', error);
      
      // 针对超时错误提供更好的用户提示
      if (error.code === 'ECONNABORTED') {
        throw new Error('查询处理时间较长，这通常发生在复杂的知识图谱查询中。请稍后重试或尝试简化问题。');
      }
      
      throw error;
    }
  }

  /**
   * 流式问答查询 - 增加重试和错误恢复机制
   */
  async* queryStream(request: QARequest, signal?: AbortSignal): AsyncGenerator<StreamingMessage> {
    let retryCount = 0;
    const maxRetries = 2;

    while (retryCount <= maxRetries) {
      try {
        // 创建一个带超时的 AbortController
        const timeoutController = new AbortController();
        const timeoutId = setTimeout(() => {
          timeoutController.abort();
        }, 300000); // 5分钟超时

        // 组合用户的signal和超时signal
        const combinedSignal = signal ? this.combineAbortSignals([signal, timeoutController.signal]) : timeoutController.signal;

        const response = await fetch(`${this.baseURL}/api/v1/qa/query/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Accept': 'text/event-stream',
          },
          body: JSON.stringify(request),
          signal: combinedSignal,
          // 禁用缓存
          cache: 'no-store',
        });

        // 清除超时定时器
        clearTimeout(timeoutId);

        if (!response.ok) {
          if (response.status === 502 || response.status === 503 || response.status === 504) {
            // 服务器错误，可以重试
            throw new Error(`Server error: ${response.status}`);
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('无法获取响应流');
        }

        const decoder = new TextDecoder();
        let buffer = '';
        let hasReceivedData = false;

        try {
          while (true) {
            // 检查是否已被取消
            if (signal?.aborted || timeoutController.signal.aborted) {
              throw new DOMException('请求已取消或超时', 'AbortError');
            }

            let readResult;
            try {
              readResult = await reader.read();
            } catch (readError) {
              console.warn('读取流数据时出错:', readError);
              if (hasReceivedData) {
                // 如果已经接收到数据，则正常结束
                break;
              }
              throw readError;
            }

            const { done, value } = readResult;

            if (done) {
              console.log('流式响应正常结束');
              break;
            }

            hasReceivedData = true;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (line.trim() === '') continue;
              
              if (line.startsWith('data: ')) {
                const dataContent = line.slice(6).trim();
                if (dataContent === '[DONE]') {
                  console.log('接收到结束标记');
                  return;
                }
                
                try {
                  const data = JSON.parse(dataContent);
                  yield data as StreamingMessage;
                } catch (parseError) {
                  console.warn('解析SSE数据失败:', parseError, '原始数据:', dataContent);
                }
              } else if (line.startsWith('event: ') || line.startsWith('id: ')) {
                // SSE事件类型或ID，暂时忽略
                continue;
              } else {
                console.warn('未识别的SSE格式:', line);
              }
            }
          }
        } finally {
          try {
            reader.releaseLock();
          } catch (e) {
            console.warn('释放reader失败:', e);
          }
          clearTimeout(timeoutId);
        }

        // 如果成功完成，退出重试循环
        return;

      } catch (error) {
        console.error(`流式查询失败 (尝试 ${retryCount + 1}/${maxRetries + 1}):`, error);
        
        retryCount++;

        // 如果是用户取消或达到最大重试次数，直接抛出错误
        if (error.name === 'AbortError' || retryCount > maxRetries) {
          if (error.name === 'AbortError') {
            throw new Error('查询超时或被取消');
          }
          
          // 根据错误类型给出具体建议
          if (error.message?.includes('ERR_INCOMPLETE_CHUNKED_ENCODING') || 
              error.message?.includes('network error')) {
            throw new Error('网络连接不稳定，请检查网络状况后重试');
          } else if (error.message?.includes('Server error')) {
            throw new Error('服务器暂时不可用，请稍后重试');
          }
          
          throw new Error(`流式查询失败: ${error.message}`);
        }

        // 等待一段时间后重试
        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
        console.log(`准备重试流式查询 (${retryCount}/${maxRetries})`);
      }
    }
  }

  /**
   * 组合多个 AbortSignal
   */
  private combineAbortSignals(signals: AbortSignal[]): AbortSignal {
    const controller = new AbortController();

    const onAbort = () => {
      controller.abort();
    };

    for (const signal of signals) {
      if (signal.aborted) {
        controller.abort();
        break;
      }
      signal.addEventListener('abort', onAbort);
    }

    // 清理事件监听器
    controller.signal.addEventListener('abort', () => {
      for (const signal of signals) {
        signal.removeEventListener('abort', onAbort);
      }
    });

    return controller.signal;
  }

  /**
   * 获取相似题目 - 保持较短超时
   */
  async getSimilarProblems(problemTitle: string, count: number = 5): Promise<SimilarProblem[]> {
    try {
      const response = await this.client.post<SimilarProblem[]>('/api/v1/qa/similar-problems', {
        problem_title: problemTitle,
        count,
        include_solutions: true,
      }, {
        timeout: 60000, // 相似题目查询1分钟超时
      });
      return response.data;
    } catch (error) {
      console.error('获取相似题目失败:', error);
      throw error;
    }
  }

  /**
   * 处理概念点击 - 可能需要较长时间
   */
  async handleConceptClick(
    conceptName: string, 
    sourceQuery: string, 
    contextType: string
  ): Promise<QAResponse> {
    try {
      const response = await this.client.post<QAResponse>('/api/v1/qa/concept/click', {
        concept_name: conceptName,
        source_query: sourceQuery,
        context_type: contextType,
      }, {
        timeout: 120000, // 概念查询2分钟超时
      });
      return response.data;
    } catch (error) {
      console.error('处理概念点击失败:', error);
      throw error;
    }
  }

  /**
   * 获取知识图谱数据 - 可能需要较长时间
   */
  async getGraphData(entityName: string, entityType?: string): Promise<GraphData> {
    try {
      const response = await this.client.post<GraphData>('/api/v1/graph/query', {
        entity_name: entityName,
        entity_type: entityType,
        depth: 2,
        limit: 20,
      }, {
        timeout: 120000, // 图谱查询2分钟超时
      });
      return response.data;
    } catch (error) {
      console.error('获取图谱数据失败:', error);
      throw error;
    }
  }

  /**
   * 获取题目图谱 - 可能需要较长时间
   */
  async getProblemGraph(problemTitle: string): Promise<GraphData> {
    try {
      const response = await this.client.get<GraphData>(
        `/api/v1/graph/problem/${encodeURIComponent(problemTitle)}/graph`,
        {
          timeout: 120000, // 题目图谱2分钟超时
        }
      );
      return response.data;
    } catch (error) {
      console.error('获取题目图谱失败:', error);
      throw error;
    }
  }

  /**
   * 获取概念图谱 - 可能需要较长时间
   */
  async getConceptGraph(conceptName: string): Promise<GraphData> {
    try {
      const response = await this.client.get<GraphData>(
        `/api/v1/graph/concept/${encodeURIComponent(conceptName)}/graph`,
        {
          timeout: 120000, // 概念图谱2分钟超时
        }
      );
      return response.data;
    } catch (error) {
      console.error('获取概念图谱失败:', error);
      throw error;
    }
  }

  /**
   * 提交反馈 - 快速操作
   */
  async submitFeedback(feedback: {
    session_id: string;
    query: string;
    response_id: string;
    rating: number;
    feedback_text?: string;
    helpful_parts?: string[];
    improvement_suggestions?: string;
  }): Promise<void> {
    try {
      await this.client.post('/api/v1/qa/feedback', feedback, {
        timeout: 15000, // 反馈提交15秒超时
      });
    } catch (error) {
      console.error('提交反馈失败:', error);
      throw error;
    }
  }

  /**
   * 获取会话历史 - 快速操作
   */
  async getSessionHistory(sessionId: string, limit: number = 10): Promise<any> {
    try {
      const response = await this.client.get(`/api/v1/qa/sessions/${sessionId}/history`, {
        params: { limit },
        timeout: 30000, // 会话历史30秒超时
      });
      return response.data;
    } catch (error) {
      console.error('获取会话历史失败:', error);
      throw error;
    }
  }

  /**
   * 清除会话 - 快速操作
   */
  async clearSession(sessionId: string): Promise<void> {
    try {
      await this.client.delete(`/api/v1/qa/sessions/${sessionId}`, {
        timeout: 15000, // 清除会话15秒超时
      });
    } catch (error) {
      console.error('清除会话失败:', error);
      throw error;
    }
  }

  /**
   * 健康检查 - 快速操作
   */
  async healthCheck(): Promise<any> {
    try {
      const response = await this.client.get('/health', {
        timeout: 10000, // 健康检查10秒超时
      });
      return response.data;
    } catch (error) {
      console.error('健康检查失败:', error);
      throw error;
    }
  }

  /**
   * 获取图谱统计信息 - 中等耗时
   */
  async getGraphStatistics(): Promise<any> {
    try {
      const response = await this.client.get('/api/v1/graph/statistics', {
        timeout: 60000, // 统计信息1分钟超时
      });
      return response.data;
    } catch (error) {
      console.error('获取图谱统计失败:', error);
      throw error;
    }
  }

  /**
   * 创建可取消的查询方法 - 用于长时间查询
   */
  createCancellableQuery() {
    const controller = new AbortController();
    
    return {
      query: (request: QARequest) => this.query(request, controller.signal),
      queryStream: (request: QARequest) => this.queryStream(request, controller.signal),
      // queryWithFallback: (request: QARequest, preferStream: boolean = true) => 
      //   this.queryWithFallback(request, preferStream, controller.signal),
      cancel: () => {
        console.log('取消查询请求');
        controller.abort();
      },
      signal: controller.signal,
    };
  }
}

// 创建单例实例
export const apiService = new ApiService();
export default apiService;