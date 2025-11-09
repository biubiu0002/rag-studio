"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { debugAPI } from "@/lib/api"
import { knowledgeBaseAPI } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function RetrievalView() {
  const [loading, setLoading] = useState(false)
  const [kbId, setKbId] = useState<string>("")
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [searchResults, setSearchResults] = useState<any>(null)
  const [searchConfig, setSearchConfig] = useState({
    top_k: 5,
    vector_weight: 0.7,
    keyword_weight: 0.3,
    rrf_k: 60,
    embedding_model: "bge-m3:latest",
    tokenize_mode: "search"
  })
  const [sparseVectorConfig, setSparseVectorConfig] = useState({
    method: "bm25",
    generate_sparse: false
  })

  // 加载知识库列表
  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  const loadKnowledgeBases = async () => {
    try {
      const result = await knowledgeBaseAPI.list(1, 100)
      setKnowledgeBases(result.data || [])
      if (result.data && result.data.length > 0 && !kbId) {
        setKbId(result.data[0].id)
      }
    } catch (error) {
      console.error("加载知识库列表失败:", error)
    }
  }

  // 执行混合检索
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      showToast("请输入查询文本", "warning")
      return
    }
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      const result = await debugAPI.hybridSearch({
        kb_id: kbId,
        query: searchQuery,
        top_k: searchConfig.top_k,
        vector_weight: searchConfig.vector_weight,
        keyword_weight: searchConfig.keyword_weight,
        rrf_k: searchConfig.rrf_k,
        embedding_model: searchConfig.embedding_model,
        tokenize_mode: searchConfig.tokenize_mode
      })
      
      setSearchResults(result.data)
    } catch (error) {
      console.error("检索失败:", error)
      showToast("检索失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 执行Qdrant混合检索
  const handleQdrantHybridSearch = async () => {
    if (!searchQuery.trim()) {
      showToast("请输入查询文本", "warning")
      return
    }
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      const result = await debugAPI.qdrantHybridSearch({
        kb_id: kbId,
        query: searchQuery,
        top_k: searchConfig.top_k,
        vector_weight: searchConfig.vector_weight,
        keyword_weight: searchConfig.keyword_weight,
        rrf_k: searchConfig.rrf_k,
        embedding_model: searchConfig.embedding_model,
        tokenize_mode: searchConfig.tokenize_mode,
        sparse_vector_config: sparseVectorConfig
      })
      
      setSearchResults(result.data)
    } catch (error) {
      console.error("检索失败:", error)
      showToast("检索失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">检索测试</h2>
        <p className="text-sm text-gray-500 mt-1">
          混合检索（向量检索 + 关键词检索 + RRF融合）
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>步骤1: 选择知识库</CardTitle>
          <CardDescription>选择要检索的目标知识库</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select
              value={kbId}
              onChange={(e) => setKbId(e.target.value)}
              className="flex-1 p-2 border rounded"
            >
              <option value="">请选择知识库</option>
              {knowledgeBases.map(kb => (
                <option key={kb.id} value={kb.id}>{kb.name} ({kb.id})</option>
              ))}
            </select>
            <Button onClick={loadKnowledgeBases} variant="outline">
              刷新列表
            </Button>
          </div>
          {kbId && (
            <div className="p-3 bg-blue-50 rounded text-sm text-blue-800">
              已选择知识库: {knowledgeBases.find(kb => kb.id === kbId)?.name || kbId}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤2: 配置检索参数</CardTitle>
          <CardDescription>设置混合检索的参数</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">返回结果数 (top_k)</label>
              <input
                type="number"
                value={searchConfig.top_k}
                onChange={(e) => setSearchConfig({ ...searchConfig, top_k: parseInt(e.target.value) || 5 })}
                className="w-full p-2 border rounded"
                min="1"
                max="50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">RRF参数 (k)</label>
              <input
                type="number"
                value={searchConfig.rrf_k}
                onChange={(e) => setSearchConfig({ ...searchConfig, rrf_k: parseInt(e.target.value) || 60 })}
                className="w-full p-2 border rounded"
                min="1"
                max="100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">向量权重</label>
              <input
                type="number"
                step="0.1"
                value={searchConfig.vector_weight}
                onChange={(e) => setSearchConfig({ ...searchConfig, vector_weight: parseFloat(e.target.value) || 0.7 })}
                className="w-full p-2 border rounded"
                min="0"
                max="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">关键词权重</label>
              <input
                type="number"
                step="0.1"
                value={searchConfig.keyword_weight}
                onChange={(e) => setSearchConfig({ ...searchConfig, keyword_weight: parseFloat(e.target.value) || 0.3 })}
                className="w-full p-2 border rounded"
                min="0"
                max="1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Embedding模型</label>
              <input
                type="text"
                value={searchConfig.embedding_model}
                onChange={(e) => setSearchConfig({ ...searchConfig, embedding_model: e.target.value })}
                className="w-full p-2 border rounded"
                placeholder="bge-m3:latest"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">分词模式</label>
              <select
                value={searchConfig.tokenize_mode}
                onChange={(e) => setSearchConfig({ ...searchConfig, tokenize_mode: e.target.value })}
                className="w-full p-2 border rounded"
              >
                <option value="default">默认模式</option>
                <option value="search">搜索引擎模式</option>
                <option value="all">全模式</option>
              </select>
            </div>
          </div>
          
          {/* 稀疏向量配置 */}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-2">稀疏向量配置</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">稀疏向量算法</label>
                <select
                  value={sparseVectorConfig.method}
                  onChange={(e) => setSparseVectorConfig({ ...sparseVectorConfig, method: e.target.value })}
                  className="w-full p-2 border rounded"
                >
                  <option value="bm25">BM25</option>
                  <option value="tf">词频(TF)</option>
                  <option value="simple">简单词频</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">生成稀疏向量</label>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={sparseVectorConfig.generate_sparse}
                    onChange={(e) => setSparseVectorConfig({ ...sparseVectorConfig, generate_sparse: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">自动生成稀疏向量</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤3: 输入查询并检索</CardTitle>
          <CardDescription>输入查询文本，执行混合检索</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">查询文本</label>
            <textarea
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-24 p-2 border rounded"
              placeholder="输入您的查询问题..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Button 
              onClick={handleSearch} 
              disabled={!searchQuery.trim() || !kbId || loading}
            >
              {loading ? "检索中..." : "执行混合检索"}
            </Button>
            <Button 
              onClick={handleQdrantHybridSearch} 
              disabled={!searchQuery.trim() || !kbId || loading}
              variant="outline"
            >
              {loading ? "检索中..." : "Qdrant混合检索"}
            </Button>
          </div>

          {/* 检索结果 */}
          {searchResults && (
            <div>
              <div className="font-medium mb-2">
                检索结果: 找到 {searchResults.results?.length || 0} 个相关文档
              </div>
              {searchResults.metrics && (
                <div className="mb-4 p-3 bg-gray-50 rounded text-sm">
                  <div>向量检索结果数: {searchResults.metrics.vector_count || "N/A"}</div>
                  <div>关键词检索结果数: {searchResults.metrics.keyword_count || "N/A"}</div>
                  <div>融合后结果数: {searchResults.metrics.fused_count || "N/A"}</div>
                </div>
              )}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {searchResults.results?.map((result: any, idx: number) => (
                  <div key={idx} className="p-3 border rounded bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">#{result.rank || idx + 1}</span>
                      <span className="text-sm text-gray-600">
                        分数: {result.score?.toFixed(4) || "N/A"} | 来源: {result.source || "N/A"}
                      </span>
                    </div>
                    <div className="text-sm">{result.content?.substring(0, 200) || "无内容"}...</div>
                    {result.metadata && (
                      <div className="text-xs text-gray-500 mt-1">
                        元数据: {JSON.stringify(result.metadata)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
