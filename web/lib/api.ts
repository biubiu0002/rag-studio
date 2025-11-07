/**
 * API客户端
 * 统一管理与后端的API调用
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

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
  const defaultHeaders = isFormData
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
      const error = await response.json()
      throw new Error(error.message || '请求失败')
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
  updateSchema: async (id: string, schemaFields: any[], vectorDbType?: string) => {
    return request<{ success: boolean; message: string }>(
      `/knowledge-bases/${id}/schema`,
      {
        method: 'PUT',
        body: JSON.stringify({
          schema_fields: schemaFields,
          vector_db_type: vectorDbType,
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
  }) => {
    return request<{ success: boolean; data: TestSet; message: string }>(
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
  listTestSets: async (kbId?: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    })
    if (kbId) {
      params.append('kb_id', kbId)
    }
    
    return request<{
      success: boolean
      data: TestSet[]
      total: number
    }>(`/tests/test-sets?${params}`)
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
  }) => {
    return request<{ success: boolean; data: any }>('/debug/index/keyword/write', {
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
    type: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas'
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
  listDebugResults: async (resultType: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas') => {
    return request<{ success: boolean; data: Array<{ id: string; name: string; timestamp: number; metadata?: Record<string, any> }>; message: string }>(
      `/debug/result/list/${resultType}`
    )
  },

  /**
   * 加载调试结果
   */
  loadDebugResult: async (resultType: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas', resultId: string) => {
    return request<{ success: boolean; data: any; message: string }>(
      `/debug/result/load/${resultType}/${resultId}`
    )
  },

  /**
   * 删除调试结果
   */
  deleteDebugResult: async (resultType: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas', resultId: string) => {
    return request<{ success: boolean; message: string }>(
      `/debug/result/delete/${resultType}/${resultId}`,
      {
        method: 'DELETE',
      }
    )
  },
}

