"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { debugAPI } from "@/lib/api"
import { knowledgeBaseAPI } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { saveResultToStorage, listResultsByType, loadResultFromStorage, exportResultToFile, importResultFromFile, SavedResult } from "@/lib/storage"
import RetrievalConfigComponent, { defaultRetrievalConfig, RetrievalConfig } from "@/components/ui/retrieval-config"

export default function RetrievalView() {
  const [loading, setLoading] = useState(false)
  const [kbId, setKbId] = useState<string>("")
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [searchResults, setSearchResults] = useState<any>(null)
  const [searchConfig, setSearchConfig] = useState<RetrievalConfig>({
    ...defaultRetrievalConfig,
    top_k: 5
  })
  const [savedResults, setSavedResults] = useState<SavedResult[]>([])
  const [selectedResultId, setSelectedResultId] = useState<string>("")
  const [saveName, setSaveName] = useState<string>("")  
  const jsonFileInputRef = useRef<HTMLInputElement>(null)

  // 加载知识库列表
  useEffect(() => {
    loadKnowledgeBases()
    loadSavedResults()
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

  const loadSavedResults = async () => {
    try {
      const results = await listResultsByType('retrieval_results')
      setSavedResults(results)
    } catch (error) {
      console.error("加载已保存结果失败:", error)
    }
  }

  // 执行检索
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
      
      const result = await debugAPI.unifiedSearch({
        kb_id: kbId,
        query: searchQuery,
        retrieval_mode: searchConfig.retrieval_mode,
        top_k: searchConfig.top_k,
        score_threshold: searchConfig.score_threshold,
        fusion_method: searchConfig.fusion_method,
        rrf_k: searchConfig.rrf_k,
        semantic_weight: searchConfig.semantic_weight,
        keyword_weight: searchConfig.keyword_weight
      })
      
      setSearchResults(result.data)
    } catch (error) {
      console.error("检索失败:", error)
      showToast("检索失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 保存检索结果
  const handleSaveResults = async () => {
    if (!searchResults) {
      showToast("没有可保存的检索结果", "warning")
      return
    }
    
    try {
      const name = saveName.trim() || `检索结果_${new Date().toLocaleString()}`
      const id = await saveResultToStorage({
        name,
        type: 'retrieval_results',
        data: {
          results: searchResults,
          query: searchQuery,
          config: searchConfig,
          kb_id: kbId
        },
        metadata: {
          result_count: searchResults.results?.length || 0,
          kb_id: kbId
        }
      })
      
      showToast(`保存成功！ID: ${id}`, "success")
      setSaveName("")
      await loadSavedResults()
    } catch (error) {
      showToast("保存失败: " + (error as Error).message, "error")
    }
  }

  // 加载已保存的检索结果
  const handleLoadResults = async () => {
    if (!selectedResultId) {
      showToast("请选择要加载的结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('retrieval_results', selectedResultId)
      if (!result || result.type !== 'retrieval_results') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      setSearchResults(result.data.results || result.data)
      setSearchQuery(result.data.query || "")
      if (result.data.config) {
        setSearchConfig(result.data.config)
      }
      if (result.data.kb_id) {
        setKbId(result.data.kb_id)
      }
      
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  // 导出JSON文件
  const handleExportResults = () => {
    if (!searchResults) {
      showToast("没有可导出的结果", "warning")
      return
    }
    
    const result: SavedResult = {
      id: '',
      name: saveName.trim() || `检索结果_${new Date().toLocaleString()}`,
      type: 'retrieval_results',
      data: {
        results: searchResults,
        query: searchQuery,
        config: searchConfig,
        kb_id: kbId
      },
      timestamp: Date.now(),
      metadata: {
        result_count: searchResults.results?.length || 0,
        kb_id: kbId
      }
    }
    
    exportResultToFile(result)
  }

  // 导入JSON文件
  const handleImportJson = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    try {
      const result = await importResultFromFile(file)
      if (result.type === 'retrieval_results') {
        setSearchResults(result.data.results || result.data)
        setSearchQuery(result.data.query || "")
        if (result.data.config) {
          setSearchConfig(result.data.config)
        }
        if (result.data.kb_id) {
          setKbId(result.data.kb_id)
        }
        showToast(`导入成功！${result.name}`, "success")
      } else {
        showToast("文件类型不匹配，需要retrieval_results类型", "error")
      }
    } catch (error) {
      showToast("导入失败: " + (error as Error).message, "error")
    } finally {
      if (jsonFileInputRef.current) {
        jsonFileInputRef.current.value = ''
      }
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
          <CardTitle>步骤2: 输入查询并检索</CardTitle>
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

        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤3: 配置检索参数</CardTitle>
          <CardDescription>选择检索模式并设置相关参数</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <RetrievalConfigComponent value={searchConfig} onChange={setSearchConfig} />

          {/* 执行检索按钮 */}
          <div>
            <Button 
              onClick={handleSearch} 
              disabled={!searchQuery.trim() || !kbId || loading}
              className="w-full"
            >
              {loading ? "检索中..." : `执行${searchConfig.retrieval_mode === "semantic" ? "语义向量" : searchConfig.retrieval_mode === "keyword" ? "关键词" : "混合"}检索`}
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

      <Card>
        <CardHeader>
          <CardTitle>步骤4: 保存/加载检索结果</CardTitle>
          <CardDescription>保存当前检索结果供后续使用或加载已保存的结果</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 保存当前结果 */}
          {searchResults && (
            <div className="border-b pb-4">
              <h3 className="text-sm font-medium mb-2">保存当前结果</h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="输入保存名称（可选）"
                  className="flex-1 p-2 border rounded text-sm"
                />
                <Button onClick={handleSaveResults} variant="outline" size="sm">
                  保存到本地
                </Button>
                <Button onClick={handleExportResults} variant="outline" size="sm">
                  导出JSON
                </Button>
              </div>
            </div>
          )}

          {/* 加载已保存的结果 */}
          <div>
            <label className="block text-sm font-medium mb-2">从已保存结果加载</label>
            <div className="flex gap-2">
              <select
                value={selectedResultId}
                onChange={(e) => setSelectedResultId(e.target.value)}
                className="flex-1 p-2 border rounded text-sm"
              >
                <option value="">选择已保存的检索结果...</option>
                {savedResults.map((result) => (
                  <option key={result.id} value={result.id}>
                    {result.name} ({new Date(result.timestamp).toLocaleString()}) - {result.metadata?.result_count || 0}个结果
                  </option>
                ))}
              </select>
              <Button onClick={handleLoadResults} disabled={!selectedResultId} variant="outline" size="sm">
                加载
              </Button>
              <Button onClick={loadSavedResults} variant="outline" size="sm">
                刷新
              </Button>
            </div>
          </div>

          {/* 从JSON文件导入 */}
          <div>
            <label className="block text-sm font-medium mb-2">从JSON文件导入</label>
            <input
              ref={jsonFileInputRef}
              type="file"
              accept=".json"
              onChange={handleImportJson}
              className="hidden"
            />
            <Button onClick={() => jsonFileInputRef.current?.click()} variant="outline" className="w-full" size="sm">
              选择JSON文件导入
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
