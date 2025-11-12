/**
 * API客户端
 * 统一管理与后端的API调用
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// ========== 通用类型 ==========

export interface SavedResult {
  id: string
  name: string
  type: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas' | 'sparse_vectors' | 'retrieval_results' | 'generation_results'
  data: any
  timestamp: number
  metadata?: Record<string, any>
}

/**
 * 通用请求函数
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  // 如果 body 是 FormData，不要设置 Content-Type，让浏览器自动设置
  const isFormData = options.body instanceof FormData
  const defaultHeaders: HeadersInit = isFormData
    ? {}
    : {
        'Content-Type': 'application/json',
      }
  
  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  }
  
  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || '请求失败')
    }
    
    return await response.json()
  } catch (error) {
    console.error('API请求错误:', error)
    throw error
  }
}

// ========== 知识库相关API ==========

export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  embedding_provider: string
  embedding_model: string
  embedding_dimension: number
  vector_db_type: string
  vector_db_config: Record<string, any>
  chunk_size: number
  chunk_overlap: number
  retrieval_top_k: number
  retrieval_score_threshold: number
  document_count: number
  chunk_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CreateKnowledgeBaseData {
  name: string
  description?: string
  embedding_provider?: string
  embedding_model: string
  embedding_dimension?: number
  vector_db_type: string
  vector_db_config?: Record<string, any>
  chunk_size?: number
  chunk_overlap?: number
  retrieval_top_k?: number
  retrieval_score_threshold?: number
}

export interface UpdateKnowledgeBaseData {
  name?: string
  description?: string
  chunk_size?: number
  chunk_overlap?: number
  retrieval_top_k?: number
  retrieval_score_threshold?: number
  is_active?: boolean
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
      '/knowledge-bases',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 获取知识库列表
   */
  list: async (page = 1, pageSize = 20, isActive?: boolean) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (isActive !== undefined) {
      params.append('is_active', isActive.toString())
    }
    
    return request<{
      success: boolean
      data: KnowledgeBase[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>(`/knowledge-bases?${params}`)
  },

  /**
   * 获取知识库详情
   */
  get: async (id: string) => {
    return request<{ success: boolean; data: KnowledgeBase }>(
      `/knowledge-bases/${id}`
    )
  },

  /**
   * 更新知识库
   */
  update: async (id: string, data: UpdateKnowledgeBaseData) => {
    return request<{ success: boolean; data: KnowledgeBase; message: string }>(
      `/knowledge-bases/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 删除知识库
   */
  delete: async (id: string) => {
    return request<{ success: boolean; message: string }>(
      `/knowledge-bases/${id}`,
      {
        method: 'DELETE',
      }
    )
  },

  /**
   * 获取知识库配置
   */
  getConfig: async (id: string) => {
    return request<{ success: boolean; data: any }>(
      `/knowledge-bases/${id}/config`
    )
  },

  /**
   * 获取知识库统计信息
   */
  getStats: async (id: string) => {
    return request<{ success: boolean; data: any }>(
      `/knowledge-bases/${id}/stats`
    )
  },

  /**
   * 获取知识库Schema配置
   */
  getSchema: async (id: string) => {
    return request<{ success: boolean; data: { vector_db_type: string; fields: any[] } }>(
      `/knowledge-bases/${id}/schema`
    )
  },

  /**
   * 更新知识库Schema配置
   */
  updateSchema: async (id: string, schemaFields: any[], vectorDbType?: string, vectorDbConfig?: Record<string, any>) => {
    return request<{ success: boolean; message: string }>(
      `/knowledge-bases/${id}/schema`,
      {
        method: 'PUT',
        body: JSON.stringify({
          schema_fields: schemaFields,
          vector_db_type: vectorDbType,
          vector_db_config: vectorDbConfig,
        }),
      }
    )
  },
}

// ========== 文档相关API ==========

export interface Document {
  id: string
  kb_id: string
  name: string
  file_path: string
  file_size: number
  file_type: string
  status: string
  error_message?: string
  chunk_count: number
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

/**
 * 文档API
 */
export const documentAPI = {
  /**
   * 上传文档
   */
  upload: async (kbId: string, file: File) => {
    const formData = new FormData()
    formData.append('kb_id', kbId)
    formData.append('file', file)
    
    return request<{ success: boolean; data: Document; message: string }>(
      '/documents/upload',
      {
        method: 'POST',
        body: formData,
        headers: {}, // 让浏览器自动设置Content-Type
      }
    )
  },

  /**
   * 获取文档列表
   */
  list: async (kbId: string, page = 1, pageSize = 20, status?: string) => {
    const params = new URLSearchParams({
      kb_id: kbId,
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (status) {
      params.append('status', status)
    }
    
    return request<{
      success: boolean
      data: Document[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>(`/documents?${params}`)
  },

  /**
   * 获取文档详情
   */
  get: async (id: string) => {
    return request<{ success: boolean; data: Document }>(
      `/documents/${id}`
    )
  },

  /**
   * 删除文档
   */
  delete: async (id: string) => {
    return request<{ success: boolean; message: string }>(
      `/documents/${id}`,
      {
        method: 'DELETE',
      }
    )
  },

  /**
   * 处理文档
   */
  process: async (documentId: string, forceReprocess = false) => {
    return request<{ success: boolean; message: string }>(
      '/documents/process',
      {
        method: 'POST',
        body: JSON.stringify({
          document_id: documentId,
          force_reprocess: forceReprocess,
        }),
      }
    )
  },
}

// ========== 测试相关API ==========

export interface TestSet {
  id: string
  name: string
  description?: string
  kb_id: string
  test_type: 'retrieval' | 'generation'
  case_count: number
  created_at: string
  updated_at: string
}

export interface TestSet {
  id: string
  name: string
  description?: string
  kb_id: string
  test_type: 'retrieval' | 'generation'
  case_count: number
  kb_config?: Record<string, any>
  chunking_config?: Record<string, any>
  embedding_config?: Record<string, any>
  sparse_vector_config?: Record<string, any>
  index_config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface TestCase {
  id: string
  test_set_id: string
  kb_id: string
  query: string
  expected_chunks?: string[]
  expected_answer?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

/**
 * 测试API
 */
export const testAPI = {
  /**
   * 创建测试集
   */
  createTestSet: async (data: {
    name: string
    description?: string
    kb_id: string
    test_type: 'retrieval' | 'generation'
    kb_config?: Record<string, any>
    chunking_config?: Record<string, any>
    embedding_config?: Record<string, any>
    sparse_vector_config?: Record<string, any>
    index_config?: Record<string, any>
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>(
      '/tests/test-sets',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 获取测试集列表
   */
  listTestSets: async (kbId?: string, testType?: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (kbId) {
      params.append('kb_id', kbId)
    }
    if (testType) {
      params.append('test_type', testType)
    }
    
    return request<{
      success: boolean
      data: TestSet[]
      total: number
      page: number
      page_size: number
    }>(`/tests/test-sets?${params}`)
  },

  /**
   * 获取测试集详情
   */
  getTestSet: async (id: string) => {
    return request<{ success: boolean; data: TestSet }>(
      `/tests/test-sets/${id}`
    )
  },

  /**
   * 更新测试集
   */
  updateTestSet: async (id: string, data: {
    name?: string
    description?: string
  }) => {
    return request<{ success: boolean; message: string }>(
      `/tests/test-sets/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 删除测试集
   */
  deleteTestSet: async (id: string) => {
    return request<{ success: boolean; message: string }>(
      `/tests/test-sets/${id}`,
      {
        method: 'DELETE',
      }
    )
  },

  /**
   * 创建测试用例
   */
  createTestCase: async (data: {
    test_set_id: string
    query: string
    expected_chunks?: string[]
    expected_answer?: string
    metadata?: Record<string, any>
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>(
      '/tests/test-cases',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 获取测试用例列表
   */
  listTestCases: async (testSetId: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      test_set_id: testSetId,
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    
    return request<{
      success: boolean
      data: TestCase[]
      total: number
      page: number
      page_size: number
    }>(`/tests/test-cases?${params}`)
  },

  /**
   * 获取测试用例详情
   */
  getTestCase: async (id: string) => {
    return request<{ success: boolean; data: TestCase }>(
      `/tests/test-cases/${id}`
    )
  },

  /**
   * 更新测试用例
   */
  updateTestCase: async (id: string, data: {
    query?: string
    expected_chunks?: string[]
    expected_answer?: string
    metadata?: Record<string, any>
  }) => {
    return request<{ success: boolean; message: string }>(
      `/tests/test-cases/${id}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 删除测试用例
   */
  deleteTestCase: async (id: string) => {
    return request<{ success: boolean; message: string }>(
      `/tests/test-cases/${id}`,
      {
        method: 'DELETE',
      }
    )
  },
}

// ========== 检索器评估相关API ==========

export interface DatasetStatistics {
  total_documents: number
  total_queries: number
  total_query_doc_pairs: number
  queries_with_relevant_docs: number
  avg_relevant_docs_per_query: number
  max_relevant_docs: number
  min_relevant_docs: number
}

export interface RetrieverEvaluationResult {
  evaluation_id: string
  kb_id: string
  test_set_id: string
  total_queries: number
  successful_queries: number
  failed_queries: number
  overall_metrics: {
    precision: number
    recall: number
    f1_score: number
    mrr: number
    map: number
    ndcg: number
    hit_rate: number
  }
  config: Record<string, any>
  created_at: string
}

/**
 * 检索器评估API
 */
export const retrieverEvalAPI = {
  /**
   * 获取数据集统计信息
   */
  getDatasetStatistics: async (
    collectionPath: string,
    queriesPath: string,
    qrelsPath: string,
    maxQueries?: number,
    maxDocs?: number
  ) => {
    const params = new URLSearchParams({
      collection_path: collectionPath,
      queries_path: queriesPath,
      qrels_path: qrelsPath,
    })
    if (maxQueries) params.append('max_queries', maxQueries.toString())
    if (maxDocs) params.append('max_docs', maxDocs.toString())
    
    return request<{ success: boolean; data: DatasetStatistics }>(
      `/retriever-evaluation/dataset-statistics?${params}`
    )
  },

  /**
   * 导入T2Ranking数据集
   */
  importT2Ranking: async (data: {
    kb_id: string
    test_set_name: string
    collection_path: string
    queries_path: string
    qrels_path: string
    max_docs?: number
    max_queries?: number
    description?: string
  }) => {
    return request<{ success: boolean; data: any; message: string }>(
      '/retriever-evaluation/import-t2ranking',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 执行检索器评估
   */
  evaluate: async (data: {
    kb_id: string
    test_set_id: string
    top_k?: number
    vector_db_type?: string
    embedding_provider?: string
    embedding_model?: string
    retrieval_algorithm?: string
  }) => {
    return request<{ success: boolean; data: any; message: string }>(
      '/retriever-evaluation/evaluate',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 获取评估历史
   */
  getEvaluationHistory: async (
    kbId: string,
    testSetId?: string,
    page = 1,
    pageSize = 20
  ) => {
    const params = new URLSearchParams({
      kb_id: kbId,
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (testSetId) params.append('test_set_id', testSetId)
    
    return request<{
      success: boolean
      data: RetrieverEvaluationResult[]
      total: number
      page: number
      page_size: number
    }>(`/retriever-evaluation/evaluation-history?${params}`)
  },

  /**
   * 对比多个评估结果
   */
  compareEvaluations: async (evaluationIds: string[]) => {
    const params = new URLSearchParams({
      evaluation_ids: evaluationIds.join(','),
    })
    
    return request<{ success: boolean; data: any }>(
      `/retriever-evaluation/compare-evaluations?${params}`
    )
  },
}

// ========== 评估任务相关API ==========

export interface EvaluationTask {
  id: string
  test_set_id: string
  kb_id: string
  evaluation_type: 'retrieval' | 'generation'
  task_name?: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  retrieval_config?: Record<string, any>
  generation_config?: Record<string, any>
  total_cases: number
  completed_cases: number
  failed_cases: number
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface EvaluationSummary {
  id: string
  evaluation_task_id: string
  overall_retrieval_metrics?: Record<string, number>
  overall_ragas_retrieval_metrics?: Record<string, number>
  overall_ragas_generation_metrics?: Record<string, number>
  overall_ragas_score?: number
  metrics_distribution?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface EvaluationCaseResult {
  id: string
  evaluation_task_id: string
  test_case_id: string
  query: string
  retrieved_chunks?: any[]
  generated_answer?: string
  retrieval_time?: number
  generation_time?: number
  retrieval_metrics?: Record<string, number>
  ragas_retrieval_metrics?: Record<string, number>
  ragas_generation_metrics?: Record<string, number>
  ragas_score?: number
  status: 'pending' | 'completed' | 'failed'
  error_message?: string
  created_at: string
}

/**
 * 评估任务API
 */
export const evaluationAPI = {
  /**
   * 创建评估任务
   */
  createTask: async (data: {
    test_set_id: string
    evaluation_type: 'retrieval' | 'generation'
    task_name?: string
    retrieval_config?: Record<string, any>
    generation_config?: Record<string, any>
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>(
      '/evaluation/tasks',
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
  },

  /**
   * 执行评估任务
   */
  executeTask: async (taskId: string, saveDetailedResults = true) => {
    return request<{ success: boolean; data: EvaluationTask; message: string }>(
      `/evaluation/tasks/${taskId}/execute`,
      {
        method: 'POST',
        body: JSON.stringify({ save_detailed_results: saveDetailedResults }),
      }
    )
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
    })
    if (testSetId) params.append('test_set_id', testSetId)
    if (kbId) params.append('kb_id', kbId)
    if (status) params.append('status', status)
    
    return request<{
      success: boolean
      data: EvaluationTask[]
      total: number
      page: number
      page_size: number
    }>(`/evaluation/tasks?${params}`)
  },

  /**
   * 获取评估任务详情
   */
  getTask: async (taskId: string) => {
    return request<{ success: boolean; data: EvaluationTask }>(
      `/evaluation/tasks/${taskId}`
    )
  },

  /**
   * 获取评估汇总
   */
  getSummary: async (taskId: string) => {
    return request<{ success: boolean; data: EvaluationSummary }>(
      `/evaluation/tasks/${taskId}/summary`
    )
  },

  /**
   * 获取评估用例结果列表
   */
  listCaseResults: async (taskId: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    
    return request<{
      success: boolean
      data: EvaluationCaseResult[]
      total: number
      page: number
      page_size: number
    }>(`/evaluation/tasks/${taskId}/results?${params}`)
  },

  /**
   * 获取评估用例结果详情
   */
  getCaseResult: async (taskId: string, resultId: string) => {
    return request<{ success: boolean; data: EvaluationCaseResult }>(
      `/evaluation/tasks/${taskId}/results/${resultId}`
    )
  },
}

// ========== 健康检查 ==========

export const healthAPI = {
  check: async () => {
    return request<{ status: string }>('/health')
  },
}

// ========== 链路调试相关API ==========

export const debugAPI = {
  /**
   * 上传文档
   */
  uploadDocument: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return request<{ success: boolean; data: any }>('/debug/document/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // 让浏览器自动设置Content-Type
    })
  },

  /**
   * 解析文档
   */
  parseDocument: async (filePath: string) => {
    const params = new URLSearchParams({ file_path: filePath })
    return request<{ success: boolean; data: any }>(`/debug/document/parse?${params}`, {
      method: 'POST',
    })
  },

  /**
   * 文档分块
   */
  chunkDocument: async (data: {
    text: string
    method?: string
    chunk_size?: number
    chunk_overlap?: number
    max_sentences?: number
  }) => {
    return request<{ success: boolean; data: any }>('/debug/document/chunk', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 文档向量化
   */
  embedDocuments: async (data: {
    texts: string[]
    model?: string
    provider?: string
  }) => {
    return request<{ success: boolean; data: any }>('/debug/embedding/embed', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 获取可用的embedding模型
   */
  getEmbeddingModels: async () => {
    return request<{ success: boolean; data: any[] }>('/debug/embedding/models')
  },

  /**
   * jieba分词
   */
  tokenizeJieba: async (data: {
    texts: string[]
    mode?: string
    use_stop_words?: boolean
  }) => {
    return request<{ success: boolean; data: any }>('/debug/tokenize/jieba', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 写入向量索引
   */
  writeVectorIndex: async (data: {
    kb_id: string
    chunks: any[]
    vectors: number[][]
    fields?: string[] // 添加fields参数
  }) => {
    return request<{ success: boolean; data: any }>('/debug/index/vector/write', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 写入关键词索引
   */
  writeKeywordIndex: async (data: {
    kb_id: string
    chunks: any[]
    tokens_list: string[][]
    fields?: string[] // 添加fields参数
  }) => {
    return request<{ success: boolean; data: any }>('/debug/index/keyword/write', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 写入稀疏向量索引
   */
  writeSparseVectorIndex: async (data: {
    kb_id: string
    chunks: any[]
    sparse_vectors: any[]
    fields?: string[] // 添加fields参数
  }) => {
    return request<{ success: boolean; data: any }>('/debug/index/sparse-vector/write', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 写入混合索引（稠密向量+稀疏向量一次性写入）
   */
  writeHybridIndex: async (data: {
    kb_id: string
    chunks: any[]
    dense_vectors?: number[][]
    sparse_vectors?: any[]
    fields?: string[]
  }) => {
    return request<{ success: boolean; data: any }>('/debug/index/hybrid/write', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 混合检索
   */
  hybridSearch: async (data: {
    kb_id: string
    query: string
    top_k?: number
    vector_weight?: number
    keyword_weight?: number
    rrf_k?: number
    embedding_model?: string
    tokenize_mode?: string
  }) => {
    return request<{ success: boolean; data: any }>('/debug/retrieve/hybrid', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * Qdrant混合检索
   */
  qdrantHybridSearch: async (data: {
    kb_id: string
    query: string
    query_vector?: number[]
    query_sparse_vector?: { indices: number[]; values: number[] }
    top_k?: number
    score_threshold?: number
    fusion?: string
    embedding_model?: string
    generate_sparse_vector?: boolean
  }) => {
    return request<{ success: boolean; data: any }>('/debug/retrieve/qdrant-hybrid', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 生成稀疏向量
   */
  generateSparseVector: async (data: {
    kb_id: string
    text: string
    method?: "bm25" | "tf-idf" | "simple" | "splade"
  }) => {
    return request<{ success: boolean; data: any }>('/debug/sparse-vector/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 测试RRF融合
   */
  testRRF: async (data: {
    results_lists: any[][]
    k?: number
    weights?: number[]
  }) => {
    return request<{ success: boolean; data: any }>('/debug/test/rrf', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 保存调试结果
   */
  saveDebugResult: async (data: {
    name: string
    type: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas' | 'sparse_vectors' | 'retrieval_results' | 'generation_results'
    data: any
    metadata?: Record<string, any>
  }) => {
    return request<{ success: boolean; data: { id: string }; message: string }>('/debug/result/save', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * 列出调试结果
   */
  listDebugResults: async (resultType: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas' | 'sparse_vectors' | 'retrieval_results' | 'generation_results') => {
    return request<{ success: boolean; data: Array<{ id: string; name: string; timestamp: number; metadata?: Record<string, any> }>; message: string }>(
      `/debug/result/list/${resultType}`
    )
  },

  /**
   * 加载调试结果
   */
  loadDebugResult: async (resultType: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas' | 'sparse_vectors' | 'retrieval_results' | 'generation_results', resultId: string) => {
    return request<{ success: boolean; data: any; message: string }>(
      `/debug/result/load/${resultType}/${resultId}`
    )
  },

  /**
   * 删除调试结果
   */
  deleteDebugResult: async (resultType: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas' | 'sparse_vectors' | 'retrieval_results' | 'generation_results', resultId: string) => {
    return request<{ success: boolean; message: string }>(
      `/debug/result/delete/${resultType}/${resultId}`,
      {
        method: 'DELETE',
      }
    )
  },

  /**
   * 生成测试
   */
  generate: async (data: {
    query: string
    context?: string
    kb_id?: string
    stream?: boolean
    llm_provider?: string
    llm_model?: string
    temperature?: number
    max_tokens?: number
  }) => {
    return request<{ success: boolean; data: any }>('/debug/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}