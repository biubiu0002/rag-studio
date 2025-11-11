"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { debugAPI } from "@/lib/api"
import { saveResultToStorage, listResultsByType, loadResultFromStorage, exportResultToFile, importResultFromFile, SavedResult } from "@/lib/storage"
import { showToast } from "@/lib/toast"

// 定义chunk的类型
type ChunkType = string | { content: string; [key: string]: any }

export default function DocumentTokenizationView() {
  const [loading, setLoading] = useState(false)
  const [chunksText, setChunksText] = useState<string>("")
  const [chunks, setChunks] = useState<ChunkType[]>([])
  const [tokens, setTokens] = useState<string[][]>([])
  const [tokenPreview, setTokenPreview] = useState<any[]>([])
  const [tokenConfig, setTokenConfig] = useState({
    mode: "search",
    use_stop_words: true
  })
  
  // 稀疏向量相关状态
  const [sparseVectors, setSparseVectors] = useState<any[]>([])
  const [sparseVectorPreview, setSparseVectorPreview] = useState<any[]>([])
  const [sparseVectorConfig, setSparseVectorConfig] = useState({
    method: "bm25" as "bm25" | "tf-idf" | "simple" | "splade"
  })
  const [savedSparseVectors, setSavedSparseVectors] = useState<SavedResult[]>([])
  const [selectedSparseVectorId, setSelectedSparseVectorId] = useState<string>("")
  
  const jsonFileInputRef = useRef<HTMLInputElement>(null)
  
  // 保存的结果列表
  const [savedChunks, setSavedChunks] = useState<SavedResult[]>([])
  const [savedTokens, setSavedTokens] = useState<SavedResult[]>([])
  const [selectedChunkId, setSelectedChunkId] = useState<string>("")
  const [selectedTokenId, setSelectedTokenId] = useState<string>("")
  const [saveName, setSaveName] = useState<string>("")

  // 加载已保存的结果列表
  useEffect(() => {
    loadSavedChunks().catch(console.error)
    loadSavedTokens().catch(console.error)
    loadSavedSparseVectors().catch(console.error)
  }, [])

  const loadSavedChunks = async () => {
    const results = await listResultsByType('chunks')
    setSavedChunks(results)
  }

  const loadSavedTokens = async () => {
    const results = await listResultsByType('tokens')
    setSavedTokens(results)
  }

  const loadSavedSparseVectors = async () => {
    const results = await listResultsByType('sparse_vectors')
    setSavedSparseVectors(results)
  }

  // 执行分词
  const handleTokenize = async () => {
    if (chunks.length === 0) {
      showToast("请先选择文档", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      const result = await debugAPI.tokenizeJieba({
        texts: chunks.map(chunk => typeof chunk === 'string' ? chunk : chunk.content),
        mode: tokenConfig.mode,
        use_stop_words: tokenConfig.use_stop_words
      })
      
      setTokens(result.data.tokens || [])
      setTokenPreview(result.data.preview || [])
      
      showToast(`分词完成！共处理 ${chunks.length} 个分块`, "success")
    } catch (error) {
      console.error("分词失败:", error)
      showToast("分词失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 生成稀疏向量
  const handleGenerateSparseVectors = async () => {
    if (chunks.length === 0) {
      showToast("请先选择文档", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      // 并行调用API生成稀疏向量（处理所有分块）
      const method = sparseVectorConfig.method === "bm25" ? "bm25" : 
                     sparseVectorConfig.method === "tf-idf" ? "tf-idf" : 
                     sparseVectorConfig.method
      
      // 分批处理，避免一次发起太多请求
      const BATCH_SIZE = 10  // 每批10个并发请求
      const allResults: any[] = []
      
      for (let batchStart = 0; batchStart < chunks.length; batchStart += BATCH_SIZE) {
        const batchEnd = Math.min(batchStart + BATCH_SIZE, chunks.length)
        const batchChunks = chunks.slice(batchStart, batchEnd)
        
        console.log(`处理第 ${batchStart + 1}-${batchEnd} 个分块（共 ${chunks.length} 个）`)
        
        const promises = batchChunks.map(async (chunk, batchIndex) => {
          const i = batchStart + batchIndex  // 全局索引
          try {
            // 确保获取正确的文本内容
            const textContent = typeof chunk === 'string' ? chunk : chunk.content
            
            const result = await debugAPI.generateSparseVector({
              kb_id: "temp_kb", // 临时知识库ID，调试模式不需要真实知识库
              text: textContent,
              method: method
            })
            
            return {
              success: true,
              index: i,
              data: result.data,
              preview: {
                index: i,
                original: textContent,
                sparse_vector: result.data.sparse_vector,
                qdrant_format: result.data.qdrant_format,
                sparsity: result.data.sparsity
              }
            }
          } catch (error) {
            // 确保获取正确的文本内容
            const textContent = typeof chunk === 'string' ? chunk : chunk.content
            
            console.error(`生成第${i}个分块的稀疏向量失败:`, error)
            return {
              success: false,
              index: i,
              preview: {
                index: i,
                original: textContent,
                error: (error as Error).message
              }
            }
          }
        })
        
        // 等待当前批次完成
        const batchResults = await Promise.all(promises)
        allResults.push(...batchResults)
        
        // 显示进度
        showToast(`已处理 ${batchEnd}/${chunks.length} 个分块...`, "info")
      }
      
      // 分离成功和失败的结果
      const sparseVectorsData = allResults
        .filter(r => r.success)
        .map(r => r.data)
      
      const previewData = allResults.map(r => r.preview)
      
      setSparseVectors(sparseVectorsData)
      setSparseVectorPreview(previewData)
      
      const successCount = allResults.filter(r => r.success).length
      const failCount = allResults.filter(r => !r.success).length
      
      if (failCount > 0) {
        showToast(`稀疏向量生成完成！成功 ${successCount} 个，失败 ${failCount} 个`, "warning")
      } else {
        showToast(`稀疏向量生成完成！共处理 ${chunks.length} 个分块`, "success")
      }
    } catch (error) {
      console.error("稀疏向量生成失败:", error)
      showToast("稀疏向量生成失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 保存稀疏向量结果
  const handleSaveSparseVectors = async () => {
    if (sparseVectors.length === 0) {
      showToast("没有可保存的稀疏向量数据", "warning")
      return
    }
    
    try {
      const name = saveName.trim() || `稀疏向量结果_${new Date().toLocaleString()}`
      const id = await saveResultToStorage({
        name,
        type: 'sparse_vectors',
        data: {
          vectors: sparseVectors,
          preview: sparseVectorPreview,
          chunks: chunks,
          config: sparseVectorConfig
        },
        metadata: {
          vector_count: sparseVectors.length,
          method: sparseVectorConfig.method
        }
      })
      
      showToast(`保存成功！ID: ${id}`, "success")
      setSaveName("")
      await loadSavedSparseVectors()
    } catch (error) {
      showToast("保存失败: " + (error as Error).message, "error")
    }
  }

  // 加载已保存的稀疏向量
  const handleLoadSparseVectors = async () => {
    if (!selectedSparseVectorId) {
      showToast("请选择要加载的稀疏向量结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('sparse_vectors', selectedSparseVectorId)
      if (!result || result.type !== 'sparse_vectors') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      setSparseVectors(result.data.vectors || [])
      setSparseVectorPreview(result.data.preview || [])
      if (result.data.chunks) {
        setChunks(result.data.chunks)
        setChunksText(result.data.chunks.join('\n'))
      }
      if (result.data.config) {
        setSparseVectorConfig(result.data.config)
      }
      
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  // 导出稀疏向量为JSON文件
  const handleExportSparseVectors = () => {
    if (sparseVectors.length === 0) {
      showToast("没有可导出的稀疏向量数据", "warning")
      return
    }
    
    const result: SavedResult = {
      id: '',
      name: saveName.trim() || `稀疏向量结果_${new Date().toLocaleString()}`,
      type: 'sparse_vectors',
      data: {
        vectors: sparseVectors,
        preview: sparseVectorPreview,
        chunks: chunks,
        config: sparseVectorConfig
      },
      timestamp: Date.now(),
      metadata: {
        vector_count: sparseVectors.length,
        method: sparseVectorConfig.method
      }
    }
    
    exportResultToFile(result)
  }

  // 从chunks结果加载
  const handleLoadChunks = async () => {
    if (!selectedChunkId) {
      showToast("请选择要加载的chunks结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('chunks', selectedChunkId)
      if (!result || result.type !== 'chunks') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      const chunksData = result.data.chunks || []
      const texts = chunksData.map((chunk: any) => chunk.content || chunk)
      setChunks(texts)
      setChunksText(texts.join('\n'))
      
      showToast(`加载成功！${result.name}，共 ${texts.length} 个分块`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  // 保存tokens结果
  const handleSaveTokens = async () => {
    if (tokens.length === 0) {
      showToast("没有可保存的分词数据", "warning")
      return
    }
    
    try {
      const name = saveName.trim() || `分词结果_${new Date().toLocaleString()}`
      const id = await saveResultToStorage({
        name,
        type: 'tokens',
        data: {
          tokens,
          preview: tokenPreview,
          chunks: chunks,
          config: tokenConfig
        },
        metadata: {
          token_count: tokens.length,
          mode: tokenConfig.mode
        }
      })
      
      showToast(`保存成功！ID: ${id}`, "success")
      setSaveName("")
      await loadSavedTokens()
    } catch (error) {
      showToast("保存失败: " + (error as Error).message, "error")
    }
  }

  // 加载已保存的tokens
  const handleLoadTokens = async () => {
    if (!selectedTokenId) {
      showToast("请选择要加载的结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('tokens', selectedTokenId)
      if (!result || result.type !== 'tokens') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      setTokens(result.data.tokens || [])
      setTokenPreview(result.data.preview || [])
      if (result.data.chunks) {
        setChunks(result.data.chunks)
        setChunksText(result.data.chunks.join('\n'))
      }
      if (result.data.config) {
        setTokenConfig(result.data.config)
      }
      
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  // 导入JSON文件
  const handleImportJson = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    
    try {
      const result = await importResultFromFile(file)
      if (result.type === 'chunks') {
        const chunksData = result.data.chunks || []
        const texts = chunksData.map((chunk: any) => chunk.content || chunk)
        setChunks(texts)
        setChunksText(texts.join('\n'))
        showToast(`导入成功！${result.name}，共 ${texts.length} 个分块`, "success")
      } else if (result.type === 'tokens') {
        setTokens(result.data.tokens || [])
        setTokenPreview(result.data.preview || [])
        if (result.data.chunks) {
          setChunks(result.data.chunks)
          setChunksText(result.data.chunks.join('\n'))
        }
        showToast(`导入成功！${result.name}`, "success")
      } else if (result.type === 'sparse_vectors') {
        setSparseVectors(result.data.vectors || [])
        setSparseVectorPreview(result.data.preview || [])
        if (result.data.chunks) {
          setChunks(result.data.chunks)
          setChunksText(result.data.chunks.join('\n'))
        }
        showToast(`导入成功！${result.name}`, "success")
      } else {
        showToast("文件类型不匹配，需要chunks、tokens或sparse_vectors类型", "error")
      }
    } catch (error) {
      showToast("导入失败: " + (error as Error).message, "error")
    } finally {
      if (jsonFileInputRef.current) {
        jsonFileInputRef.current.value = ''
      }
    }
  }

  // 导出为JSON文件
  const handleExportTokens = () => {
    if (tokens.length === 0) {
      showToast("没有可导出的分词数据", "warning")
      return
    }
    
    const result: SavedResult = {
      id: '',
      name: saveName.trim() || `分词结果_${new Date().toLocaleString()}`,
      type: 'tokens',
      data: {
        tokens,
        preview: tokenPreview,
        chunks: chunks,
        config: tokenConfig
      },
      timestamp: Date.now(),
      metadata: {
        token_count: tokens.length,
        mode: tokenConfig.mode
      }
    }
    
    exportResultToFile(result)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">文档分词</h2>
        <p className="text-sm text-gray-500 mt-1">
          使用jieba进行中文分词处理
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>步骤1: 选择文档</CardTitle>
          <CardDescription>从文档处理结果或JSON文件中选择需要分词的文档</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 从已保存的chunks加载 */}
          <div>
            <label className="block text-sm font-medium mb-2">从文档处理结果加载</label>
            <div className="flex gap-2">
              <select
                value={selectedChunkId}
                onChange={(e) => setSelectedChunkId(e.target.value)}
                className="flex-1 p-2 border rounded text-sm"
              >
                <option value="">选择已保存的chunks结果...</option>
                {savedChunks.map((result) => (
                  <option key={result.id} value={result.id}>
                    {result.name} ({new Date(result.timestamp).toLocaleString()}) - {result.metadata?.chunk_count || 0}个分块
                  </option>
                ))}
              </select>
              <Button onClick={handleLoadChunks} disabled={!selectedChunkId} variant="outline">
                加载
              </Button>
              <Button onClick={loadSavedChunks} variant="outline" size="sm">
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
            <Button onClick={() => jsonFileInputRef.current?.click()} variant="outline" className="w-full">
              选择JSON文件导入
            </Button>
          </div>

          {/* 文档展示 */}
          <div className="border-t pt-4">
            <label className="block text-sm font-medium mb-2">文档展示</label>
            <textarea
              value={chunksText}
              readOnly
              className="w-full h-48 p-2 border rounded bg-gray-50"
              placeholder="请从文档处理结果加载或导入JSON文件..."
            />
            <div className="text-sm text-gray-500 mt-1">
              共 {chunks.length} 个分块
            </div>
          </div>

          {chunks.length > 0 && (
            <div className="p-3 bg-green-50 rounded">
              <div className="text-sm text-green-800">
                ✓ 已加载 {chunks.length} 个分块
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤2: 配置分词参数</CardTitle>
          <CardDescription>设置jieba分词的模式和选项</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">分词模式</label>
              <select
                value={tokenConfig.mode}
                onChange={(e) => setTokenConfig({ ...tokenConfig, mode: e.target.value })}
                className="w-full p-2 border rounded"
              >
                <option value="default">默认模式</option>
                <option value="search">搜索引擎模式</option>
                <option value="all">全模式</option>
              </select>
              <div className="text-xs text-gray-500 mt-1">
                {tokenConfig.mode === "default" && "精确模式，适合文本分析"}
                {tokenConfig.mode === "search" && "搜索引擎模式，适合检索场景"}
                {tokenConfig.mode === "all" && "全模式，速度快但可能冗余"}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">停用词</label>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={tokenConfig.use_stop_words}
                  onChange={(e) => setTokenConfig({ ...tokenConfig, use_stop_words: e.target.checked })}
                  className="w-4 h-4"
                />
                <span className="text-sm">使用停用词过滤</span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                过滤常见的无意义词汇（如：的、了、在等）
              </div>
            </div>
          </div>
          
          {/* 稀疏向量配置 */}
          <div className="border-t pt-4">
            <label className="block text-sm font-medium mb-2">稀疏向量配置</label>
            <div className="p-3 bg-blue-50 rounded mb-3">
              <div className="text-xs text-blue-800">
                💡 调试模式：无需选择知识库，系统将自动使用独立的稀疏向量服务进行生成
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">生成方法</label>
                <select
                  value={sparseVectorConfig.method}
                  onChange={(e) => setSparseVectorConfig({ ...sparseVectorConfig, method: e.target.value as "bm25" | "tf-idf" | "simple" | "splade" })}
                  className="w-full p-2 border rounded"
                >
                  <option value="bm25">BM25</option>
                  <option value="tf-idf">TF-IDF</option>
                  <option value="simple">简单词频</option>
                  <option value="splade">SPLADE</option>
                </select>
                <div className="text-xs text-gray-500 mt-1">
                  {sparseVectorConfig.method === "bm25" && "基于BM25算法的稀疏向量"}
                  {sparseVectorConfig.method === "tf-idf" && "基于TF-IDF算法的稀疏向量"}
                  {sparseVectorConfig.method === "simple" && "基于简单词频的稀疏向量"}
                  {sparseVectorConfig.method === "splade" && "基于SPLADE模型的稀疏向量"}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤3: 执行分词</CardTitle>
          <CardDescription>对分块文本进行jieba分词处理</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 bg-blue-50 rounded">
            <div className="text-sm text-blue-800">
              待处理分块: {chunks.length} 个
            </div>
            <div className="text-xs text-blue-600 mt-1">
              💡 将处理所有分块，分批并发（每批10个）以保证性能
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Button 
              onClick={handleTokenize} 
              disabled={chunks.length === 0 || loading}
            >
              {loading ? "分词中..." : "开始分词"}
            </Button>
            <Button 
              onClick={handleGenerateSparseVectors} 
              disabled={chunks.length === 0 || loading}
              variant="outline"
            >
              {loading ? "生成中..." : "生成稀疏向量（全部）"}
            </Button>
          </div>

          {/* 分词预览 */}
          {tokenPreview.length > 0 && (
            <div>
              <div className="font-medium mb-2">分词结果预览:</div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {tokenPreview.slice(0, 10).map((item, idx) => (
                  <div key={idx} className="p-3 border rounded bg-gray-50">
                    <div className="text-xs text-gray-500 mb-1">
                      Chunk {item.index !== undefined ? item.index : idx + 1} | {item.token_count || item.tokens?.length || 0} 个词
                    </div>
                    {item.original && (
                      <div className="text-sm text-gray-600 mb-1">
                        原文: {item.original}
                      </div>
                    )}
                    {item.tokens && (
                      <div className="text-sm">
                        分词: {item.tokens.join(" / ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {tokenPreview.length > 10 && (
                <div className="text-sm text-gray-500 mt-2">
                  ...还有 {tokenPreview.length - 10} 个分块的分词结果
                </div>
              )}
            </div>
          )}

          {tokens.length > 0 && (
            <div className="p-3 bg-green-50 rounded">
              <div className="text-sm text-green-800">
                ✓ 分词完成！共处理 {tokens.length} 个分块
                {tokens.length > 0 && tokens[0] && (
                  <span>，平均每块 {Math.round(tokens.reduce((sum, t) => sum + t.length, 0) / tokens.length)} 个词</span>
                )}
              </div>
            </div>
          )}

          {/* 稀疏向量预览 */}
          {sparseVectorPreview.length > 0 && (
            <div>
              <div className="font-medium mb-2">稀疏向量结果预览（前10个）:</div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {sparseVectorPreview.slice(0, 10).map((item, idx) => (
                  <div key={idx} className="p-3 border rounded bg-gray-50">
                    <div className="text-xs text-gray-500 mb-1">
                      Chunk {item.index !== undefined ? item.index + 1 : idx + 1}
                    </div>
                    {item.original && (
                      <div className="text-sm text-gray-600 mb-1">
                        原文: {item.original.substring(0, 50)}...
                      </div>
                    )}
                    {item.error ? (
                      <div className="text-sm text-red-600">
                        错误: {item.error}
                      </div>
                    ) : (
                      <>
                        <div className="text-sm">
                          非零元素数: {item.sparsity || 0}
                        </div>
                        {item.sparse_vector && (
                          <div className="text-xs text-gray-500 mt-1">
                            稀疏向量示例: {JSON.stringify(Object.entries(item.sparse_vector).slice(0, 3))}...
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
              {sparseVectorPreview.length > 10 && (
                <div className="text-sm text-gray-500 mt-2">
                  ...还有 {sparseVectorPreview.length - 10} 个分块的稀疏向量结果
                </div>
              )}
            </div>
          )}

          {sparseVectors.length > 0 && (
            <div className="p-3 bg-green-50 rounded">
              <div className="text-sm text-green-800">
                ✓ 稀疏向量生成完成！共处理 {sparseVectors.length} 个分块
                {sparseVectors.length > 0 && sparseVectors[0] && sparseVectors[0].sparsity && (
                  <span>，平均每块 {Math.round(sparseVectors.reduce((sum: number, v: any) => sum + (v.sparsity || 0), 0) / sparseVectors.length)} 个非零元素</span>
                )}
              </div>
            </div>
          )}

          {/* 保存/加载功能 */}
          <div className="border-t pt-4 space-y-4">
            <div className="font-medium mb-2">保存/加载结果</div>
            
            {/* 保存当前结果 */}
            <div className="flex gap-2">
              <input
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="输入保存名称（可选）"
                className="flex-1 p-2 border rounded text-sm"
              />
              <Button onClick={handleSaveTokens} disabled={tokens.length === 0} variant="outline">
                保存分词结果
              </Button>
              <Button onClick={handleSaveSparseVectors} disabled={sparseVectors.length === 0} variant="outline">
                保存稀疏向量
              </Button>
              <Button onClick={handleExportTokens} disabled={tokens.length === 0} variant="outline">
                导出分词JSON
              </Button>
              <Button onClick={handleExportSparseVectors} disabled={sparseVectors.length === 0} variant="outline">
                导出稀疏向量JSON
              </Button>
            </div>

            {/* 从已保存结果加载 */}
            <div>
              <label className="block text-sm font-medium mb-2">从已保存结果加载</label>
              <div className="flex gap-2 mb-2">
                <select
                  value={selectedTokenId}
                  onChange={(e) => setSelectedTokenId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的tokens结果...</option>
                  {savedTokens.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} ({new Date(result.timestamp).toLocaleString()}) - {result.metadata?.token_count || 0}个分块
                    </option>
                  ))}
                </select>
                <Button onClick={handleLoadTokens} disabled={!selectedTokenId} variant="outline">
                  加载分词
                </Button>
              </div>
              <div className="flex gap-2">
                <select
                  value={selectedSparseVectorId}
                  onChange={(e) => setSelectedSparseVectorId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的稀疏向量结果...</option>
                  {savedSparseVectors.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} ({new Date(result.timestamp).toLocaleString()}) - {result.metadata?.vector_count || 0}个分块
                    </option>
                  ))}
                </select>
                <Button onClick={handleLoadSparseVectors} disabled={!selectedSparseVectorId} variant="outline">
                  加载稀疏向量
                </Button>
              </div>
              <div className="flex gap-2 mt-2">
                <Button onClick={loadSavedTokens} variant="outline" size="sm">
                  刷新分词列表
                </Button>
                <Button onClick={loadSavedSparseVectors} variant="outline" size="sm">
                  刷新稀疏向量列表
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}