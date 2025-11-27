/**
 * 全局环境配置类型定义
 * 用于运行时配置注入
 */
declare global {
  interface Window {
    __APP_CONFIG__?: {
      API_BASE_URL: string;
    };
  }
}

export {};

