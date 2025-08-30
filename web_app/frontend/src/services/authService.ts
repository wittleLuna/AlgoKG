/**
 * 用户认证服务 - 更新版本
 */

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  role: 'user' | 'admin' | 'moderator';
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  login_count: number;
}

export interface UserStats {
  total_questions: number;
  total_sessions: number;
  total_favorites: number;
  total_uploads: number;
  last_activity?: string;
}

export interface UserProfile extends User {
  stats: UserStats;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface TestLoginResponse {
  success: boolean;
  message: string;
  token?: string;
  user?: User;
}

export interface Favorite {
  id: number;
  user_id: number;
  item_type: string;
  item_id: string;
  title?: string;
  description?: string;
  created_at: string;
}

export interface SearchHistory {
  id: number;
  user_id: number;
  query: string;
  search_type: string;
  results_count: number;
  created_at: string;
}

export interface Session {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

class AuthService {
  private baseURL = '/api/v1';
  private tokenKey = 'auth_token';
  private userKey = 'current_user';

  // 获取存储的令牌
  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  // 设置令牌
  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  // 移除令牌
  removeToken(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  // 获取当前用户
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  // 设置当前用户
  setCurrentUser(user: User): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // 获取请求头
  private getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  // 处理API响应 - 增强错误处理
  private async handleResponse<T>(response: Response): Promise<T> {
    console.log(`API响应: ${response.status} ${response.url}`);
    
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      let errorDetail = '';
      
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || JSON.stringify(errorData);
      } catch (e) {
        // 如果无法解析JSON，尝试获取文本
        try {
          errorDetail = await response.text();
        } catch (textError) {
          errorDetail = '无法获取错误详情';
        }
      }
      
      console.error(`API错误 ${response.status}:`, errorDetail);
      
      // 根据状态码提供更具体的错误信息
      switch (response.status) {
        case 400:
          errorMessage = '请求参数错误: ' + errorDetail;
          break;
        case 401:
          errorMessage = '未授权访问，请重新登录';
          this.removeToken(); // 清除无效token
          break;
        case 403:
          errorMessage = '访问被拒绝: ' + errorDetail;
          break;
        case 404:
          errorMessage = '请求的资源不存在';
          break;
        case 500:
          errorMessage = '服务器内部错误，请稍后重试';
          break;
        case 502:
          errorMessage = '服务器连接错误';
          break;
        case 503:
          errorMessage = '服务暂时不可用';
          break;
        default:
          errorMessage = `请求失败 (${response.status}): ${errorDetail}`;
      }
      
      throw new Error(errorMessage);
    }
    
    try {
      return await response.json();
    } catch (e) {
      console.warn('响应不是有效的JSON格式');
      return {} as T;
    }
  }

  // **新增: 测试登录方法**
  async testLogin(): Promise<TestLoginResponse> {
    console.log('发送测试登录请求...');
    
    try {
      const response = await fetch(`${this.baseURL}/auth/test-login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          test: true,
          timestamp: Date.now()
        }),
      });

      console.log('测试登录响应状态:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('测试登录错误响应:', errorText);
        
        let errorMessage = '测试登录失败';
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorJson.message || errorMessage;
        } catch {
          errorMessage += `: HTTP ${response.status}`;
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('测试登录成功:', result);
      
      return result;
    } catch (error) {
      console.error('测试登录异常:', error);
      throw new Error(`测试登录失败: ${error.message}`);
    }
  }

  // **增强: 用户注册 - 添加更好的错误处理**
  async register(data: RegisterRequest): Promise<AuthResponse> {
    console.log('发送注册请求:', { ...data, password: '[HIDDEN]' });

    try {
      const response = await fetch(`${this.baseURL}/auth/register`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data),
      });

      console.log('注册响应状态:', response.status);

      const result = await this.handleResponse<AuthResponse>(response);

      // 保存令牌和用户信息
      this.setToken(result.access_token);
      this.setCurrentUser(result.user);

      console.log('注册成功');
      return result;
    } catch (error) {
      console.error('注册失败:', error);
      throw error;
    }
  }

  // **增强: 用户登录 - 添加更好的错误处理**
  async login(data: LoginRequest): Promise<AuthResponse> {
    console.log('发送登录请求:', { ...data, password: '[HIDDEN]' });
    
    try {
      const response = await fetch(`${this.baseURL}/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data),
      });

      const result = await this.handleResponse<AuthResponse>(response);
      
      // 保存令牌和用户信息
      this.setToken(result.access_token);
      this.setCurrentUser(result.user);
      
      console.log('登录成功');
      return result;
    } catch (error) {
      console.error('登录失败:', error);
      throw error;
    }
  }

  // **新增: 检查API连通性**
  async checkApiHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL.replace('/api/v1', '')}/health`, {
        method: 'GET',
        
      });
      return response.ok;
    } catch (error) {
      console.error('API健康检查失败:', error);
      return false;
    }
  }

  // 用户登出
  async logout(): Promise<void> {
    try {
      await fetch(`${this.baseURL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
      console.log('服务端登出成功');
    } catch (error) {
      console.warn('服务端登出失败:', error);
    } finally {
      // 无论请求是否成功，都清除本地存储
      this.removeToken();
      console.log('本地登出完成');
    }
  }

  // 获取用户资料
  async getUserProfile(): Promise<UserProfile> {
    const response = await fetch(`${this.baseURL}/auth/me`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<UserProfile>(response);
  }

  // 更新用户信息
  async updateUser(data: Partial<User>): Promise<User> {
    const response = await fetch(`${this.baseURL}/auth/me`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    const result = await this.handleResponse<User>(response);
    
    // 更新本地存储的用户信息
    this.setCurrentUser(result);
    
    return result;
  }

  // 验证令牌
  async verifyToken(): Promise<User> {
    const response = await fetch(`${this.baseURL}/auth/verify-token`, {
      headers: this.getAuthHeaders(),
    });

    const result = await this.handleResponse<User>(response);
    
    // 更新本地存储的用户信息
    this.setCurrentUser(result);
    
    return result;
  }

  // 添加收藏
  async addFavorite(itemType: string, itemId: string, title?: string, description?: string): Promise<Favorite> {
    const response = await fetch(`${this.baseURL}/auth/favorites`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        item_type: itemType,
        item_id: itemId,
        title,
        description,
      }),
    });

    return this.handleResponse<Favorite>(response);
  }

  // 获取收藏列表
  async getFavorites(itemType?: string, limit = 50, offset = 0): Promise<Favorite[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (itemType) {
      params.append('item_type', itemType);
    }

    const response = await fetch(`${this.baseURL}/auth/favorites?${params}`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<Favorite[]>(response);
  }

  // 移除收藏
  async removeFavorite(itemType: string, itemId: string): Promise<void> {
    const response = await fetch(`${this.baseURL}/auth/favorites/${itemType}/${itemId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    await this.handleResponse<{ message: string }>(response);
  }

  // 添加搜索历史
  async addSearchHistory(query: string, searchType: string, resultsCount = 0): Promise<SearchHistory> {
    const response = await fetch(`${this.baseURL}/auth/search-history`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        query,
        search_type: searchType,
        results_count: resultsCount,
      }),
    });

    return this.handleResponse<SearchHistory>(response);
  }

  // 获取搜索历史
  async getSearchHistory(searchType?: string, limit = 50, offset = 0): Promise<SearchHistory[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (searchType) {
      params.append('search_type', searchType);
    }

    const response = await fetch(`${this.baseURL}/auth/search-history?${params}`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<SearchHistory[]>(response);
  }

  // 清空搜索历史
  async clearSearchHistory(searchType?: string): Promise<void> {
    const params = searchType ? `?search_type=${searchType}` : '';

    const response = await fetch(`${this.baseURL}/auth/search-history${params}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    await this.handleResponse<{ message: string }>(response);
  }

  // 会话管理相关方法
  async createSession(sessionData: { title: string; description?: string }): Promise<Session> {
    const response = await fetch(`${this.baseURL}/auth/sessions`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(sessionData),
    });

    return this.handleResponse<Session>(response);
  }

  async getUserSessions(limit = 50, offset = 0): Promise<Session[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(`${this.baseURL}/auth/sessions?${params}`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<Session[]>(response);
  }

  async getSession(sessionId: number): Promise<Session> {
    const response = await fetch(`${this.baseURL}/auth/sessions/${sessionId}`, {
      headers: this.getAuthHeaders(),
    });

    return this.handleResponse<Session>(response);
  }

  async updateSession(sessionId: number, sessionData: { title?: string; description?: string }): Promise<Session> {
    const response = await fetch(`${this.baseURL}/auth/sessions/${sessionId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(sessionData),
    });

    return this.handleResponse<Session>(response);
  }

  async deleteSession(sessionId: number): Promise<void> {
    const response = await fetch(`${this.baseURL}/auth/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
    });

    await this.handleResponse<{ message: string }>(response);
  }
}

// 导出单例实例
export const authService = new AuthService();
export default authService;