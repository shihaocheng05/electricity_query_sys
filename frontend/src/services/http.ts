// HTTP 客户端：封装请求库（如 fetch/axios），处理鉴权头、错误拦截与重试策略。
import axios from 'axios';
import { ErrorCodes } from '@/utils/errorCodes.ts';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse,InternalAxiosRequestConfig} from 'axios';

class HttpService {
    private client: AxiosInstance;
    private isRefreshing = false; // Token 刷新状态标志，防止重复刷新
    private refreshSubscribers: Array<(token: string) => void> = []; // 等待 token 的请求队列

    constructor(){
      this.client = axios.create({
        baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api/v1', // 建议：从环境变量读取，便于切换环境
        timeout: 30000, // 增加到30秒，邮件发送可能较慢
        headers:{"Content-Type":"application/json"}
      });
      this.setupInterceptors(); // 建议：在构造函数中调用，确保拦截器初始化
    }

    // 全部刷新
    private onTokenRefreshed(token: string): void {
      this.refreshSubscribers.forEach(callback => callback(token));
      this.refreshSubscribers = [];
    }

    // 订阅 token 刷新事件
    private onRefreshing(callback: (token: string) => void): void {
      this.refreshSubscribers.push(callback);
    }

    // Token 刷新方法
    private async refreshToken(): Promise<string> {
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
          throw new Error("No refresh token found");
        }

        // 使用不带拦截器的原生 axios 实例避免死循环
        const response = await axios.post(
          `${this.client.defaults.baseURL}/user/refresh-token`,
          { refresh_token: refreshToken },
          { timeout: 10000 }
        );

        const newToken = response.data.data?.access_token || response.data.data?.token;
        if (!newToken) {
          throw new Error("Failed to get new token");
        }

        localStorage.setItem("auth_token", newToken);
        // 建议：如果后端返回新的 refresh_token，也需要更新
        if (response.data.data?.refresh_token) {
          localStorage.setItem("refresh_token", response.data.data.refresh_token);
        }

        return newToken;
      } catch (error) {
        // 刷新失败，清除 token 并重定向到登录
        localStorage.removeItem("auth_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/auth/login";
        throw error;
      }
    }

    // 拦截器
    private setupInterceptors() {
        this.client.interceptors.request.use(
            (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
                // 不需要认证的接口列表
                const noAuthUrls = [
                    '/user/login',
                    '/user/register',
                    '/user/send-reset-code',
                    '/user/reset-password',
                    '/user/refresh-token'
                ];
                
                // 检查当前请求是否需要跳过认证
                const needsAuth = !noAuthUrls.some(url => config.url?.includes(url));
                
                // 在请求发送前添加鉴权头
                const token=localStorage.getItem("auth_token");
                if(token && config.headers && needsAuth){
                    config.headers["Authorization"]="Bearer "+token;
                }
                return config;
            },
            (error)=>{
                console.error("请求错误：",error.message);
                return Promise.reject(error);
            }
        )
        this.client.interceptors.response.use(
            (response:AxiosResponse<any>):any => {
            // 处理响应数据
                const res=response.data;
                if(res.code&&res.code!==200){       //200是业务成功
                    console.error("响应错误：",res.message||"未知错误");
                    return Promise.reject(new ErrorCodes(res))      //封装为自定义错误类型
            }
                return res;
            },
            async (error)=>{
                // 新增：Token 刷新逻辑
                const config = error.config;

                // 检查是否是 401 Unauthorized（token 过期）
                if (error.response?.status === 401 && config && !config._retry) {
                  config._retry = true; // 标记已重试，避免无限循环

                  // 如果正在刷新 token，将当前请求加入队列等待
                  if (this.isRefreshing) {
                    return new Promise((resolve) => {
                      this.onRefreshing((token: string) => {
                        config.headers["Authorization"] = `Bearer ${token}`;
                        resolve(this.client(config));
                      });
                    });
                  }

                  // 开始刷新 token
                  this.isRefreshing = true;

                  try {
                    const newToken = await this.refreshToken();
                    this.isRefreshing = false;
                    this.onTokenRefreshed(newToken); // 通知所有等待的请求

                    // 用新 token 重试原请求
                    config.headers["Authorization"] = `Bearer ${newToken}`;
                    return this.client(config);
                  } catch (refreshError) {
                    this.isRefreshing = false;
                    this.refreshSubscribers = [];
                    return Promise.reject(refreshError);
                  }
                }

                console.error("响应错误：",error.message);
                return Promise.reject(error);
            }
        )
    }

    // 建议：添加公共请求方法，便于在组件中使用
    public get<T = any>(url: string, config?: AxiosRequestConfig) {
        return this.client.get<T>(url, config);
    }

    public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
        return this.client.post<T>(url, data, config);
    }

    public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
        return this.client.put<T>(url, data, config);
    }

    public delete<T = any>(url: string, config?: AxiosRequestConfig) {
        return this.client.delete<T>(url, config);
    }
}

// 导出单例
export const httpService = new HttpService();

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
  code?: number;
}