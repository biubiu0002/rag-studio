/**
 * API客户端
 * 统一管理与后端的API调用
 */
import { env } from "next-runtime-env";
function getApiBaseUrl(): string {
  return (
    env("NEXT_PUBLIC_API_URL") ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
}

// 导出获取函数，供外部使用
export const getAPIBaseURL = getApiBaseUrl;

// ========== 通用类型 ==========

export interface SavedResult {
  id: string;
  name: string;
  type:
    | "chunks"
    | "embeddings"
    | "tokens"
    | "index_data"
    | "schemas"
    | "sparse_vectors"
    | "retrieval_results"
    | "generation_results";
  data: any;
  timestamp: number;
  metadata?: Record<string, any>;
}

/**
 * 通用请求函数
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${getApiBaseUrl()}${endpoint}`;

  // 如果 body 是 FormData，不要设置 Content-Type，让浏览器自动设置
  const isFormData = options.body instanceof FormData;
  const defaultHeaders: HeadersInit = isFormData
    ? {}
    : {
        "Content-Type": "application/json",
      };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "请求失败");
    }

    return await response.json();
  } catch (error) {
    console.error("API请求错误:", error);
    throw error;
  }
}

// ========== 知识库相关API ==========

export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  embedding_provider: string;
  embedding_model: string;
  embedding_dimension: number;
  embedding_endpoint?: string;
  chat_provider: string;
  chat_model?: string;
  chat_endpoint?: string;
  vector_db_type: string;
  vector_db_config: Record<string, any>;
  chunk_size: number;
  chunk_overlap: number;
  retrieval_top_k: number;
  retrieval_score_threshold: number;
  document_count: number;
  chunk_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateKnowledgeBaseData {
  name: string;
  description?: string;
  embedding_provider?: string;
  embedding_model: string;
  embedding_dimension?: number;
  embedding_endpoint?: string;
  chat_provider?: string;
  chat_model?: string;
  chat_endpoint?: string;
  vector_db_type: string;
  vector_db_config?: Record<string, any>;
  chunk_size?: number;
  chunk_overlap?: number;
  retrieval_top_k?: number;
  retrieval_score_threshold?: number;
}

export interface UpdateKnowledgeBaseData {
  name?: string;
  description?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  retrieval_top_k?: number;
  retrieval_score_threshold?: number;
  is_active?: boolean;
}

export interface AIModelConfig {
  embedding_provider: string;
  embedding_model: string;
  embedding_endpoint?: string;
  chat_provider: string;
  chat_model: string;
  chat_endpoint?: string;
}

/**
 * 知识库API
 */
export const knowledgeBaseAPI = {
  /**
   * 创建知识库
   */
  create: async (data: CreateKnowledgeBaseData) => {
    return request<{ success: boolean; data: KnowledgeBase; message: string }>(
      "/knowledge-bases",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 获取知识库列表
   */
  list: async (page = 1, pageSize = 20, isActive?: boolean) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (isActive !== undefined) {
      params.append("is_active", isActive.toString());
    }

    return request<{
      success: boolean;
      data: KnowledgeBase[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/knowledge-bases?${params}`);
  },

  /**
   * 获取知识库详情
   */
  get: async (id: string) => {
    return request<{ success: boolean; data: KnowledgeBase }>(
      `/knowledge-bases/${id}`
    );
  },

  /**
   * 更新知识库
   */
  update: async (id: string, data: UpdateKnowledgeBaseData) => {
    return request<{ success: boolean; data: KnowledgeBase; message: string }>(
      `/knowledge-bases/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 删除知识库
   */
  delete: async (id: string) => {
    return request<{ success: boolean; message: string }>(
      `/knowledge-bases/${id}`,
      {
        method: "DELETE",
      }
    );
  },

  /**
   * 获取知识库配置
   */
  getConfig: async (id: string) => {
    return request<{ success: boolean; data: any }>(
      `/knowledge-bases/${id}/config`
    );
  },

  /**
   * 获取知识库统计信息
   */
  getStats: async (id: string) => {
    return request<{ success: boolean; data: any }>(
      `/knowledge-bases/${id}/stats`
    );
  },

  /**
   * 获取知识库Schema配置
   */
  getSchema: async (id: string) => {
    return request<{
      success: boolean;
      data: { vector_db_type: string; fields: any[] };
    }>(`/knowledge-bases/${id}/schema`);
  },

  /**
   * 更新知识库Schema配置
   */
  updateSchema: async (
    id: string,
    schemaFields: any[],
    vectorDbType?: string,
    vectorDbConfig?: Record<string, any>
  ) => {
    return request<{ success: boolean; message: string }>(
      `/knowledge-bases/${id}/schema`,
      {
        method: "PUT",
        body: JSON.stringify({
          schema_fields: schemaFields,
          vector_db_type: vectorDbType,
          vector_db_config: vectorDbConfig,
        }),
      }
    );
  },

  /**
   * 获取AI模型配置
   */
  getAIModelConfig: async (id: string) => {
    return request<{ success: boolean; data: AIModelConfig }>(
      `/knowledge-bases/${id}/ai-model-config`
    );
  },

  /**
   * 更新AI模型配置
   */
  updateAIModelConfig: async (id: string, config: AIModelConfig) => {
    return request<{ success: boolean; message: string }>(
      `/knowledge-bases/${id}/ai-model-config`,
      {
        method: "PUT",
        body: JSON.stringify(config),
      }
    );
  },
};

// ========== 文档相关API ==========

export interface Document {
  id: string;
  kb_id: string;
  name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  status: string;
  error_message?: string;
  chunk_count: number;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * 文档API
 */
export const documentAPI = {
  /**
   * 上传文档
   */
  upload: async (kbId: string, file: File) => {
    const formData = new FormData();
    formData.append("kb_id", kbId);
    formData.append("file", file);

    return request<{ success: boolean; data: Document; message: string }>(
      "/documents/upload",
      {
        method: "POST",
        body: formData,
        headers: {}, // 让浏览器自动设置Content-Type
      }
    );
  },

  /**
   * 获取文档列表
   */
  list: async (kbId: string, page = 1, pageSize = 20, status?: string) => {
    const params = new URLSearchParams({
      kb_id: kbId,
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (status) {
      params.append("status", status);
    }

    return request<{
      success: boolean;
      data: Document[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/documents?${params}`);
  },

  /**
   * 获取文档详情
   */
  get: async (id: string) => {
    return request<{ success: boolean; data: Document }>(`/documents/${id}`);
  },

  /**
   * 删除文档
   */
  delete: async (id: string) => {
    return request<{ success: boolean; message: string }>(`/documents/${id}`, {
      method: "DELETE",
    });
  },

  /**
   * 处理文档
   */
  process: async (documentId: string, forceReprocess = false) => {
    return request<{ success: boolean; message: string }>(
      "/documents/process",
      {
        method: "POST",
        body: JSON.stringify({
          document_id: documentId,
          force_reprocess: forceReprocess,
        }),
      }
    );
  },
};

// ========== 测试相关API ==========

export interface TestSet {
  id: string;
  name: string;
  description?: string;
  kb_id?: string; // 改为可选
  test_type: "retrieval" | "generation";
  case_count: number;
  kb_config?: Record<string, any>;
  chunking_config?: Record<string, any>;
  embedding_config?: Record<string, any>;
  sparse_vector_config?: Record<string, any>;
  index_config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: string;
  test_set_id: string;
  kb_id: string;
  query: string;
  expected_chunks?: string[];
  expected_answer?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// ========== 新测试管理API类型定义 ==========

/**
 * 期望答案对象
 */
export interface ExpectedAnswer {
  answer_text: string;
  chunk_id?: string;
  relevance_score: number;
}

/**
 * 检索器测试用例
 */
export interface RetrieverTestCase {
  id: string;
  test_set_id: string;
  question: string;
  expected_answers: ExpectedAnswer[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * 创建检索器测试用例
 */
export interface RetrieverTestCaseCreate {
  test_set_id: string;
  question: string;
  expected_answers: ExpectedAnswer[];
  metadata?: Record<string, any>;
}

/**
 * 更新检索器测试用例
 */
export interface RetrieverTestCaseUpdate {
  question?: string;
  expected_answers?: ExpectedAnswer[];
  metadata?: Record<string, any>;
}

/**
 * 参考答案对象
 */
export interface ReferenceAnswer {
  answer_text: string;
  ground_truth?: string;
}

/**
 * 生成测试用例
 */
export interface GenerationTestCase {
  id: string;
  test_set_id: string;
  question: string;
  reference_answer: ReferenceAnswer;
  contexts?: string[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * 创建生成测试用例
 */
export interface GenerationTestCaseCreate {
  test_set_id: string;
  question: string;
  reference_answer: ReferenceAnswer;
  contexts?: string[];
  metadata?: Record<string, any>;
}

/**
 * 更新生成测试用例
 */
export interface GenerationTestCaseUpdate {
  question?: string;
  reference_answer?: ReferenceAnswer;
  contexts?: string[];
  metadata?: Record<string, any>;
}

/**
 * 测试API
 */
export const testAPI = {
  /**
   * 创建测试集
   */
  createTestSet: async (data: {
    name: string;
    description?: string;
    kb_id?: string; // 改为可选
    test_type: "retrieval" | "generation";
    kb_config?: Record<string, any>;
    chunking_config?: Record<string, any>;
    embedding_config?: Record<string, any>;
    sparse_vector_config?: Record<string, any>;
    index_config?: Record<string, any>;
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>(
      "/tests/test-sets",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 获取测试集列表
   */
  listTestSets: async (
    kbId?: string,
    testType?: string,
    page = 1,
    pageSize = 20
  ) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (kbId) {
      params.append("kb_id", kbId);
    }
    if (testType) {
      params.append("test_type", testType);
    }

    return request<{
      success: boolean;
      data: TestSet[];
      total: number;
      page: number;
      page_size: number;
    }>(`/tests/test-sets?${params}`);
  },

  /**
   * 获取测试集详情
   */
  getTestSet: async (id: string) => {
    return request<{ success: boolean; data: TestSet }>(
      `/tests/test-sets/${id}`
    );
  },

  /**
   * 更新测试集
   */
  updateTestSet: async (
    id: string,
    data: {
      name?: string;
      description?: string;
    }
  ) => {
    return request<{ success: boolean; message: string }>(
      `/tests/test-sets/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 删除测试集
   */
  deleteTestSet: async (id: string) => {
    return request<{ success: boolean; message: string }>(
      `/tests/test-sets/${id}`,
      {
        method: "DELETE",
      }
    );
  },

  /**
   * 预览导入结果
   */
  previewTestSetImport: async (testSetId: string, kbId: string) => {
    return request<{
      success: boolean;
      data: {
        total_answers: number;
        new_docs: number;
        existing_docs: number;
        skipped_docs: number;
      };
      message: string;
    }>(`/tests/test-sets/${testSetId}/import-preview?kb_id=${kbId}`);
  },

  /**
   * 导入测试集到知识库
   */
  importTestSetToKnowledgeBase: async (
    testSetId: string,
    data: {
      kb_id: string;
      update_existing?: boolean;
    }
  ) => {
    return request<{
      success: boolean;
      data: {
        id: string;
        test_set_id: string;
        kb_id: string;
        status: string;
        progress: number;
        total_docs: number;
        imported_docs: number;
        failed_docs: number;
        error_message?: string;
        started_at?: string;
        completed_at?: string;
        created_at: string;
      };
      message: string;
    }>(`/tests/test-sets/${testSetId}/import-to-kb`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * 获取测试集导入历史
   */
  getTestSetImportHistory: async (
    testSetId: string,
    page = 1,
    pageSize = 20
  ) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    return request<{
      success: boolean;
      data: Array<{
        id: string;
        test_set_id: string;
        kb_id: string;
        imported_at: string;
        import_config: Record<string, any>;
        kb_deleted: boolean;
        test_set_deleted: boolean;
        import_task?: {
          id: string;
          status: string;
          progress: number;
          total_docs: number;
          imported_docs: number;
          failed_docs: number;
        };
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/tests/test-sets/${testSetId}/import-history?${params}`);
  },

  /**
   * 获取导入任务详情
   */
  getImportTask: async (importTaskId: string) => {
    return request<{
      success: boolean;
      data: {
        id: string;
        test_set_id: string;
        kb_id: string;
        status: string;
        progress: number;
        total_docs: number;
        imported_docs: number;
        failed_docs: number;
        error_message?: string;
        started_at?: string;
        completed_at?: string;
        created_at: string;
      };
      message: string;
    }>(`/tests/import-tasks/${importTaskId}`);
  },

  /**
   * 终止导入任务
   */
  cancelImportTask: async (importTaskId: string) => {
    return request<{
      success: boolean;
      data: { import_task_id: string };
      message: string;
    }>(`/tests/import-tasks/${importTaskId}/cancel`, {
      method: "POST",
    });
  },

  /**
   * 获取知识库已导入的测试集列表
   */
  getKnowledgeBaseTestSets: async (kbId: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    return request<{
      success: boolean;
      data: Array<{
        test_set: TestSet;
        imported_at: string;
        import_config: Record<string, any>;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/tests/knowledge-bases/${kbId}/test-sets?${params}`);
  },
};

// ========== 评估任务相关API ==========

export interface EvaluationTask {
  id: string;
  test_set_id: string;
  kb_id: string;
  evaluation_type: "retrieval" | "generation";
  task_name?: string;
  status: "pending" | "running" | "completed" | "failed" | "archived";
  retrieval_config?: Record<string, any>;
  generation_config?: Record<string, any>;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface EvaluationSummary {
  id: string;
  evaluation_task_id: string;
  overall_retrieval_metrics?: Record<string, number>;
  overall_ragas_retrieval_metrics?: Record<string, number>;
  overall_ragas_generation_metrics?: Record<string, number>;
  overall_ragas_score?: number;
  metrics_distribution?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ExpectedAnswer {
  answer_text: string;
  chunk_id?: string;
  relevance_score: number;
}

export interface EvaluationCaseResult {
  id: string;
  evaluation_task_id: string;
  test_case_id: string;
  query: string;
  retrieved_chunks?: any[];
  generated_answer?: string;
  retrieval_time?: number;
  generation_time?: number;
  retrieval_metrics?: Record<string, number>;
  ragas_retrieval_metrics?: Record<string, number>;
  ragas_generation_metrics?: Record<string, number>;
  ragas_score?: number;
  status: "pending" | "completed" | "failed";
  error_message?: string;
  expected_answers?: ExpectedAnswer[];
  created_at: string;
}

/**
 * 评估任务API
 */
export const evaluationAPI = {
  /**
   * 创建评估任务
   */
  createTask: async (data: {
    test_set_id: string;
    kb_id: string;
    evaluation_type: "retrieval" | "generation";
    task_name?: string;
    retrieval_config?: Record<string, any>;
    generation_config?: Record<string, any>;
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>(
      "/evaluation/tasks",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 执行评估任务
   */
  executeTask: async (taskId: string, saveDetailedResults = true) => {
    return request<{ success: boolean; data: EvaluationTask; message: string }>(
      `/evaluation/tasks/${taskId}/execute`,
      {
        method: "POST",
        body: JSON.stringify({ save_detailed_results: saveDetailedResults }),
      }
    );
  },

  /**
   * 获取评估任务列表
   */
  listTasks: async (
    testSetId?: string,
    kbId?: string,
    status?: string,
    page = 1,
    pageSize = 20
  ) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (testSetId) params.append("test_set_id", testSetId);
    if (kbId) params.append("kb_id", kbId);
    if (status) params.append("status", status);

    return request<{
      success: boolean;
      data: EvaluationTask[];
      total: number;
      page: number;
      page_size: number;
    }>(`/evaluation/tasks?${params}`);
  },

  /**
   * 获取评估任务详情
   */
  getTask: async (taskId: string) => {
    return request<{ success: boolean; data: EvaluationTask }>(
      `/evaluation/tasks/${taskId}`
    );
  },

  /**
   * 获取评估汇总
   */
  getSummary: async (taskId: string) => {
    return request<{ success: boolean; data: EvaluationSummary }>(
      `/evaluation/tasks/${taskId}/summary`
    );
  },

  /**
   * 获取评估用例结果列表
   */
  listCaseResults: async (taskId: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    return request<{
      success: boolean;
      data: EvaluationCaseResult[];
      total: number;
      page: number;
      page_size: number;
    }>(`/evaluation/tasks/${taskId}/results?${params}`);
  },

  /**
   * 获取评估用例结果详情
   */
  getCaseResult: async (taskId: string, resultId: string) => {
    return request<{ success: boolean; data: EvaluationCaseResult }>(
      `/evaluation/tasks/${taskId}/results/${resultId}`
    );
  },

  /**
   * 终止评估任务
   */
  cancelTask: async (taskId: string) => {
    return request<{
      success: boolean;
      data: { task_id: string };
      message: string;
    }>(`/evaluation/tasks/${taskId}/cancel`, {
      method: "POST",
    });
  },
};

// ========== 健康检查 ==========

export const healthAPI = {
  check: async () => {
    return request<{ status: string }>("/health");
  },
};

// ========== 链路调试相关API ==========

export const debugAPI = {
  /**
   * 上传文档
   */
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    return request<{ success: boolean; data: any }>("/debug/document/upload", {
      method: "POST",
      body: formData,
      headers: {}, // 让浏览器自动设置Content-Type
    });
  },

  /**
   * 解析文档
   */
  parseDocument: async (filePath: string) => {
    const params = new URLSearchParams({ file_path: filePath });
    return request<{ success: boolean; data: any }>(
      `/debug/document/parse?${params}`,
      {
        method: "POST",
      }
    );
  },

  /**
   * 文档分块
   */
  chunkDocument: async (data: {
    text: string;
    method?: string;
    chunk_size?: number;
    chunk_overlap?: number;
    max_sentences?: number;
  }) => {
    return request<{ success: boolean; data: any }>("/debug/document/chunk", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * 文档向量化
   */
  embedDocuments: async (data: {
    texts: string[];
    model?: string;
    provider?: string;
    service_url?: string;
    api_key?: string;
  }) => {
    return request<{ success: boolean; data: any }>("/debug/embedding/embed", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * 获取可用的embedding模型
   */
  getEmbeddingModels: async () => {
    return request<{ success: boolean; data: any[] }>(
      "/debug/embedding/models"
    );
  },

  /**
   * jieba分词
   */
  tokenizeJieba: async (data: {
    texts: string[];
    mode?: string;
    use_stop_words?: boolean;
  }) => {
    return request<{ success: boolean; data: any }>("/debug/tokenize/jieba", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * 写入混合索引（稠密向量+稀疏向量一次性写入）
   */
  writeHybridIndex: async (data: {
    kb_id: string;
    chunks: any[];
    dense_vectors?: number[][];
    sparse_vectors?: any[];
    fields?: string[];
  }) => {
    return request<{ success: boolean; data: any }>(
      "/debug/index/hybrid/write",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 统一检索接口
   */
  unifiedSearch: async (data: {
    kb_id: string;
    query: string;
    retrieval_mode?: "semantic" | "keyword" | "hybrid";
    top_k?: number;
    fusion_method?: "rrf" | "weighted";
    rrf_k?: number;
    semantic_weight?: number;
    keyword_weight?: number;
    score_threshold?: number;
  }) => {
    return request<{ success: boolean; data: any }>("/debug/retrieve/unified", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Qdrant混合检索
   */
  qdrantHybridSearch: async (data: {
    kb_id: string;
    query: string;
    query_vector?: number[];
    query_sparse_vector?: { indices: number[]; values: number[] };
    top_k?: number;
    score_threshold?: number;
    fusion?: string;
    embedding_model?: string;
    generate_sparse_vector?: boolean;
  }) => {
    return request<{ success: boolean; data: any }>(
      "/debug/retrieve/qdrant-hybrid",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 生成稀疏向量
   */
  generateSparseVector: async (data: {
    kb_id: string;
    text: string;
    method?: "bm25" | "tf-idf" | "simple" | "splade";
  }) => {
    return request<{ success: boolean; data: any }>(
      "/debug/sparse-vector/generate",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 保存调试结果
   */
  saveDebugResult: async (data: {
    name: string;
    type:
      | "chunks"
      | "embeddings"
      | "tokens"
      | "index_data"
      | "schemas"
      | "sparse_vectors"
      | "retrieval_results"
      | "generation_results";
    data: any;
    metadata?: Record<string, any>;
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>(
      "/debug/result/save",
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  /**
   * 列出调试结果
   */
  listDebugResults: async (
    resultType:
      | "chunks"
      | "embeddings"
      | "tokens"
      | "index_data"
      | "schemas"
      | "sparse_vectors"
      | "retrieval_results"
      | "generation_results"
  ) => {
    return request<{
      success: boolean;
      data: Array<{
        id: string;
        name: string;
        timestamp: number;
        metadata?: Record<string, any>;
      }>;
      message: string;
    }>(`/debug/result/list/${resultType}`);
  },

  /**
   * 加载调试结果
   */
  loadDebugResult: async (
    resultType:
      | "chunks"
      | "embeddings"
      | "tokens"
      | "index_data"
      | "schemas"
      | "sparse_vectors"
      | "retrieval_results"
      | "generation_results",
    resultId: string
  ) => {
    return request<{ success: boolean; data: any; message: string }>(
      `/debug/result/load/${resultType}/${resultId}`
    );
  },

  /**
   * 删除调试结果
   */
  deleteDebugResult: async (
    resultType:
      | "chunks"
      | "embeddings"
      | "tokens"
      | "index_data"
      | "schemas"
      | "sparse_vectors"
      | "retrieval_results"
      | "generation_results",
    resultId: string
  ) => {
    return request<{ success: boolean; message: string }>(
      `/debug/result/delete/${resultType}/${resultId}`,
      {
        method: "DELETE",
      }
    );
  },

  /**
   * 生成测试
   */
  generate: async (data: {
    query: string;
    context?: string;
    kb_id?: string;
    stream?: boolean;
    llm_provider?: string;
    llm_model?: string;
    temperature?: number;
    max_tokens?: number;
  }) => {
    return request<{ success: boolean; data: any }>("/debug/generate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

// ========== 新测试管理API ==========

/**
 * 检索器测试用例API
 */
export const retrieverTestCaseAPI = {
  /**
   * 创建检索器测试用例
   */
  create: async (data: RetrieverTestCaseCreate) => {
    return request<{
      success: boolean;
      data: RetrieverTestCase;
      message: string;
    }>("/tests/retriever/cases", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * 批量创建检索器测试用例
   */
  createBatch: async (cases: RetrieverTestCaseCreate[]) => {
    return request<{
      success: boolean;
      data: {
        created_count: number;
        failed_count: number;
        created_cases: RetrieverTestCase[];
        errors: any[];
      };
      message: string;
    }>("/tests/retriever/cases/batch", {
      method: "POST",
      body: JSON.stringify({ cases }),
    });
  },

  /**
   * 获取检索器测试用例列表
   */
  list: async (testSetId?: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (testSetId) {
      params.append("test_set_id", testSetId);
    }

    return request<{
      success: boolean;
      data: RetrieverTestCase[];
      total: number;
      page: number;
      page_size: number;
    }>(`/tests/retriever/cases?${params}`);
  },

  /**
   * 获取检索器测试用例详情
   */
  get: async (caseId: string) => {
    return request<{ success: boolean; data: RetrieverTestCase }>(
      `/tests/retriever/cases/${caseId}`
    );
  },

  /**
   * 更新检索器测试用例
   */
  update: async (caseId: string, data: RetrieverTestCaseUpdate) => {
    return request<{
      success: boolean;
      data: RetrieverTestCase;
      message: string;
    }>(`/tests/retriever/cases/${caseId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /**
   * 删除检索器测试用例
   */
  delete: async (caseId: string) => {
    return request<{ success: boolean; message: string }>(
      `/tests/retriever/cases/${caseId}`,
      {
        method: "DELETE",
      }
    );
  },

  /**
   * 批量删除检索器测试用例
   */
  deleteBatch: async (caseIds: string[]) => {
    return request<{
      success: boolean;
      data: {
        deleted_count: number;
        failed_count: number;
        errors: any[];
      };
      message: string;
    }>("/tests/retriever/cases/batch", {
      method: "DELETE",
      body: JSON.stringify({ case_ids: caseIds }),
    });
  },

  /**
   * 添加期望答案
   */
  addAnswer: async (caseId: string, answer: ExpectedAnswer) => {
    return request<{
      success: boolean;
      data: RetrieverTestCase;
      message: string;
    }>(`/tests/retriever/cases/${caseId}/answers`, {
      method: "POST",
      body: JSON.stringify(answer),
    });
  },

  /**
   * 更新期望答案
   */
  updateAnswer: async (
    caseId: string,
    answerIndex: number,
    answer: ExpectedAnswer
  ) => {
    return request<{
      success: boolean;
      data: RetrieverTestCase;
      message: string;
    }>(`/tests/retriever/cases/${caseId}/answers/${answerIndex}`, {
      method: "PUT",
      body: JSON.stringify(answer),
    });
  },

  /**
   * 删除期望答案
   */
  deleteAnswer: async (caseId: string, answerIndex: number) => {
    return request<{
      success: boolean;
      data: RetrieverTestCase;
      message: string;
    }>(`/tests/retriever/cases/${caseId}/answers/${answerIndex}`, {
      method: "DELETE",
    });
  },
};

/**
 * 生成测试用例API
 */
export const generationTestCaseAPI = {
  /**
   * 创建生成测试用例
   */
  create: async (data: GenerationTestCaseCreate) => {
    return request<{
      success: boolean;
      data: GenerationTestCase;
      message: string;
    }>("/tests/generation/cases", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * 批量创建生成测试用例
   */
  createBatch: async (cases: GenerationTestCaseCreate[]) => {
    return request<{
      success: boolean;
      data: {
        created_count: number;
        failed_count: number;
        created_cases: GenerationTestCase[];
        errors: any[];
      };
      message: string;
    }>("/tests/generation/cases/batch", {
      method: "POST",
      body: JSON.stringify({ cases }),
    });
  },

  /**
   * 获取生成测试用例列表
   */
  list: async (testSetId?: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (testSetId) {
      params.append("test_set_id", testSetId);
    }

    return request<{
      success: boolean;
      data: GenerationTestCase[];
      total: number;
      page: number;
      page_size: number;
    }>(`/tests/generation/cases?${params}`);
  },

  /**
   * 获取生成测试用例详情
   */
  get: async (caseId: string) => {
    return request<{ success: boolean; data: GenerationTestCase }>(
      `/tests/generation/cases/${caseId}`
    );
  },

  /**
   * 更新生成测试用例
   */
  update: async (caseId: string, data: GenerationTestCaseUpdate) => {
    return request<{
      success: boolean;
      data: GenerationTestCase;
      message: string;
    }>(`/tests/generation/cases/${caseId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  /**
   * 删除生成测试用例
   */
  delete: async (caseId: string) => {
    return request<{ success: boolean; message: string }>(
      `/tests/generation/cases/${caseId}`,
      {
        method: "DELETE",
      }
    );
  },

  /**
   * 批量删除生成测试用例
   */
  deleteBatch: async (caseIds: string[]) => {
    return request<{
      success: boolean;
      data: {
        deleted_count: number;
        failed_count: number;
        errors: any[];
      };
      message: string;
    }>("/tests/generation/cases/batch", {
      method: "DELETE",
      body: JSON.stringify({ case_ids: caseIds }),
    });
  },

  /**
   * 添加上下文
   */
  addContext: async (caseId: string, context: string) => {
    return request<{
      success: boolean;
      data: GenerationTestCase;
      message: string;
    }>(`/tests/generation/cases/${caseId}/contexts`, {
      method: "POST",
      body: JSON.stringify({ context }),
    });
  },

  /**
   * 更新上下文
   */
  updateContext: async (
    caseId: string,
    contextIndex: number,
    context: string
  ) => {
    return request<{
      success: boolean;
      data: GenerationTestCase;
      message: string;
    }>(`/tests/generation/cases/${caseId}/contexts/${contextIndex}`, {
      method: "PUT",
      body: JSON.stringify({ context }),
    });
  },

  /**
   * 删除上下文
   */
  deleteContext: async (caseId: string, contextIndex: number) => {
    return request<{
      success: boolean;
      data: GenerationTestCase;
      message: string;
    }>(`/tests/generation/cases/${caseId}/contexts/${contextIndex}`, {
      method: "DELETE",
    });
  },
};
