"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { debugAPI } from "@/lib/api"
import { knowledgeBaseAPI } from "@/lib/api"
import { listResultsByType, loadResultFromStorage, exportResultToFile, importResultFromFile, SavedResult } from "@/lib/storage"
import { showToast } from "@/lib/toast"

export default function IndexWritingView() {
  const [loading, setLoading] = useState(false)
  const [kbId, setKbId] = useState<string>("")
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])
  const [selectedKbSchema, setSelectedKbSchema] = useState<any>(null) // 新增：存储选中知识库的schema
  
  // 输入数据
  const [chunksJson, setChunksJson] = useState<string>("")
  const [vectorsJson, setVectorsJson] = useState<string>("")
  const [sparseVectorsJson, setSparseVectorsJson] = useState<string>("")
  
  // 解析后的数据
  const [chunks, setChunks] = useState<any[]>([])
  const [vectors, setVectors] = useState<number[][]>([])
  const [sparseVectors, setSparseVectors] = useState<any[]>([])
  
  // 写入结果
  const [indexResult, setIndexResult] = useState<any>(null)
  const jsonFileInputRef = useRef<HTMLInputElement>(null)
  
  // 保存的结果列表
  const [savedChunks, setSavedChunks] = useState<SavedResult[]>([])
  const [savedEmbeddings, setSavedEmbeddings] = useState<SavedResult[]>([])
  const [savedSparseVectors, setSavedSparseVectors] = useState<SavedResult[]>([])
  const [selectedChunkId, setSelectedChunkId] = useState<string>("")
  const [selectedEmbeddingId, setSelectedEmbeddingId] = useState<string>("")
  const [selectedSparseVectorId, setSelectedSparseVectorId] = useState<string>("")

  // 加载已保存的结果列表
  useEffect(() => {
    loadSavedResults().catch(console.error)
  }, [])

  // 组件挂载时自动加载知识库列表
  useEffect(() => {
    loadKnowledgeBases().catch(console.error)
  }, [])

  const loadSavedResults = async () => {
    const [chunks, embeddings, sparseVectors] = await Promise.all([
      listResultsByType('chunks'),
      listResultsByType('embeddings'),
      listResultsByType('sparse_vectors')
    ])
    setSavedChunks(chunks)
    setSavedEmbeddings(embeddings)
    setSavedSparseVectors(sparseVectors)
  }

  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    try {
      const result = await knowledgeBaseAPI.list(1, 100)
      setKnowledgeBases(result.data || [])
      if (result.data && result.data.length > 0 && !kbId) {
        setKbId(result.data[0].id)
        // 加载第一个知识库的schema
        loadKnowledgeBaseSchema(result.data[0].id)
      }
    } catch (error: any) {
      console.error("加载知识库列表失败:", error)
      showToast(`加载知识库列表失败: ${error.message}`, "error")
    }
  }

  // 加载知识库schema
  const loadKnowledgeBaseSchema = async (id: string) => {
    try {
      const result = await knowledgeBaseAPI.getSchema(id)
      setSelectedKbSchema(result.data)
    } catch (error: any) {
      console.error("加载知识库schema失败:", error)
      setSelectedKbSchema(null)
    }
  }

  // 解析JSON数据
  const handleParseData = () => {
    try {
      if (chunksJson) {
        const parsed = JSON.parse(chunksJson)
        if (Array.isArray(parsed)) {
          setChunks(parsed)
        } else {
          throw new Error("chunks必须是数组格式")
        }
      }
      
      if (vectorsJson) {
        const parsed = JSON.parse(vectorsJson)
        if (Array.isArray(parsed)) {
          setVectors(parsed)
        } else {
          throw new Error("vectors必须是数组格式")
        }
      }
      
      if (sparseVectorsJson) {
        const parsed = JSON.parse(sparseVectorsJson)
        if (Array.isArray(parsed)) {
          setSparseVectors(parsed)
        } else {
          throw new Error("sparseVectors必须是数组格式")
        }
      }
      
      showToast("数据解析成功！", "success")
    } catch (error) {
      showToast("数据解析失败: " + (error as Error).message, "error")
    }
  }

  // 从已保存结果加载
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
      setChunks(result.data.chunks || [])
      setChunksJson(JSON.stringify(result.data.chunks, null, 2))
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  const handleLoadEmbeddings = async () => {
    if (!selectedEmbeddingId) {
      showToast("请选择要加载的embeddings结果", "warning")
      return
    }
    try {
      const result = await loadResultFromStorage('embeddings', selectedEmbeddingId)
      if (!result || result.type !== 'embeddings') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      setVectors(result.data.vectors || [])
      setVectorsJson(JSON.stringify(result.data.vectors, null, 2))
      // 如果embeddings中有chunks，也加载
      if (result.data.chunks && chunks.length === 0) {
        const chunksData = result.data.chunks.map((c: any) => typeof c === 'string' ? { content: c } : c)
        setChunks(chunksData)
        setChunksJson(JSON.stringify(chunksData, null, 2))
      }
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  const handleLoadSparseVectors = async () => {
    if (!selectedSparseVectorId) {
      showToast("请选择要加载的sparse vectors结果", "warning")
      return
    }
    try {
      const result = await loadResultFromStorage('sparse_vectors', selectedSparseVectorId)
      if (!result || result.type !== 'sparse_vectors') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      setSparseVectors(result.data.vectors || [])
      setSparseVectorsJson(JSON.stringify(result.data.vectors, null, 2))
      // 如果sparse vectors中有chunks，也加载
      if (result.data.chunks && chunks.length === 0) {
        const chunksData = result.data.chunks.map((c: any) => typeof c === 'string' ? { content: c } : c)
        setChunks(chunksData)
        setChunksJson(JSON.stringify(chunksData, null, 2))
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
        setChunks(result.data.chunks || [])
        setChunksJson(JSON.stringify(result.data.chunks, null, 2))
        showToast(`导入成功！${result.name}`, "success")
      } else if (result.type === 'embeddings') {
        setVectors(result.data.vectors || [])
        setVectorsJson(JSON.stringify(result.data.vectors, null, 2))
        if (result.data.chunks) {
          const chunksData = result.data.chunks.map((c: any) => typeof c === 'string' ? { content: c } : c)
          setChunks(chunksData)
          setChunksJson(JSON.stringify(chunksData, null, 2))
        }
        showToast(`导入成功！${result.name}`, "success")
      } else if (result.type === 'sparse_vectors') {
        setSparseVectors(result.data.vectors || [])
        setSparseVectorsJson(JSON.stringify(result.data.vectors, null, 2))
        if (result.data.chunks) {
          const chunksData = result.data.chunks.map((c: any) => typeof c === 'string' ? { content: c } : c)
          setChunks(chunksData)
          setChunksJson(JSON.stringify(chunksData, null, 2))
        }
        showToast(`导入成功！${result.name}`, "success")
      } else {
        showToast("文件类型不匹配", "error")
      }
    } catch (error) {
      showToast("导入失败: " + (error as Error).message, "error")
    } finally {
      if (jsonFileInputRef.current) {
        jsonFileInputRef.current.value = ''
      }
    }
  }

  // 统一的写入索引接口 - 支持同时写入稠密向量和稀疏向量
  const handleWriteIndex = async () => {
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    if (chunks.length === 0) {
      showToast("请先输入并解析chunks数据", "warning")
      return
    }
    if (vectors.length === 0 && sparseVectors.length === 0) {
      showToast("请至少提供稠密向量或稀疏向量中的一种", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      // 验证数量一致性
      if (vectors.length > 0 && chunks.length !== vectors.length) {
        showToast(`chunks数量(${chunks.length})与vectors数量(${vectors.length})不匹配`, "error")
        return
      }
      
      // 准备稀疏向量
      let sparseVectorsToWrite = sparseVectors
      
      // 如果没有提供稀疏向量但有schema定义稀疏向量字段，则自动生成
      const hasSparseVectorField = selectedKbSchema?.fields?.some((field: any) => field.type === "sparse_vector")
      if (sparseVectorsToWrite.length === 0 && hasSparseVectorField) {
        showToast("正在生成稀疏向量...", "info")
        sparseVectorsToWrite = []
        
        for (let i = 0; i < chunks.length; i++) {
          const chunk = chunks[i]
          const textContent = typeof chunk === 'string' ? chunk : chunk.content
          
          try {
            // 获取稀疏向量生成方法
            let method: "bm25" | "tf-idf" | "simple" | "splade" = "bm25"
            if (selectedKbSchema && selectedKbSchema.fields) {
              const sparseField = selectedKbSchema.fields.find((field: any) => field.type === "sparse_vector")
              if (sparseField && sparseField.sparseMethod) {
                method = sparseField.sparseMethod as "bm25" | "tf-idf" | "simple" | "splade"
              }
            }
            
            const result = await debugAPI.generateSparseVector({
              kb_id: kbId,
              text: textContent,
              method: method
            })
            
            sparseVectorsToWrite.push(result.data)
          } catch (error) {
            console.error(`生成第${i}个分块的稀疏向量失败:`, error)
            // 如果生成失败，添加一个空的稀疏向量
            sparseVectorsToWrite.push({
              sparse_vector: {},
              qdrant_format: { indices: [], values: [] },
              sparsity: 0
            })
          }
        }
      }
      
      // 验证稀疏向量数量
      if (sparseVectorsToWrite.length > 0 && chunks.length !== sparseVectorsToWrite.length) {
        showToast(`chunks数量(${chunks.length})与sparse vectors数量(${sparseVectorsToWrite.length})不匹配`, "error")
        return
      }
      
      // 获取schema中定义的字段
      let fields: string[] = []
      if (selectedKbSchema && selectedKbSchema.fields) {
        fields = selectedKbSchema.fields.map((field: any) => field.name)
      }
      
      // 一次性写入混合索引
      const result = await debugAPI.writeHybridIndex({
        kb_id: kbId,
        chunks,
        dense_vectors: vectors.length > 0 ? vectors : undefined,
        sparse_vectors: sparseVectorsToWrite.length > 0 ? sparseVectorsToWrite : undefined,
        ...(fields.length > 0 && { fields })
      })
      
      setIndexResult({
        written_count: result.data.written_count,
        has_dense: result.data.has_dense,
        has_sparse: result.data.has_sparse
      })
      
      showToast("索引写入完成！", "success")
    } catch (error) {
      console.error("索引写入失败:", error)
      showToast("索引写入失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">索引写入</h2>
        <p className="text-sm text-gray-500 mt-1">
          将向量和关键词索引写入知识库
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>步骤1: 选择知识库</CardTitle>
          <CardDescription>选择要写入索引的目标知识库</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select
              value={kbId}
              onChange={(e) => {
                setKbId(e.target.value)
                if (e.target.value) {
                  loadKnowledgeBaseSchema(e.target.value)
                } else {
                  setSelectedKbSchema(null)
                }
              }}
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
              {selectedKbSchema && (
                <div className="mt-2">
                  <div>向量数据库: {selectedKbSchema.vector_db_type}</div>
                  <div>字段数: {selectedKbSchema.fields?.length || 0}</div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤2: 输入索引数据</CardTitle>
          <CardDescription>输入chunks、vectors和tokens的JSON数据</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Chunks (JSON数组)</label>
            <textarea
              value={chunksJson}
              onChange={(e) => setChunksJson(e.target.value)}
              className="w-full h-32 p-2 border rounded font-mono text-xs"
              placeholder='[{"index": 1, "content": "文本内容", "char_count": 100}, ...]'
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Vectors (JSON数组)</label>
            <textarea
              value={vectorsJson}
              onChange={(e) => setVectorsJson(e.target.value)}
              className="w-full h-32 p-2 border rounded font-mono text-xs"
              placeholder='[[0.1, 0.2, 0.3, ...], [0.4, 0.5, 0.6, ...], ...]'
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Sparse Vectors (JSON数组，可选)</label>
            <textarea
              value={sparseVectorsJson}
              onChange={(e) => setSparseVectorsJson(e.target.value)}
              className="w-full h-32 p-2 border rounded font-mono text-xs"
              placeholder='[{"indices": [1, 5, 10], "values": [0.1, 0.5, 0.3]}, ...]'
            />
          </div>

          <Button onClick={handleParseData} className="w-full">
            解析数据
          </Button>

          {/* 从已保存结果加载 */}
          <div className="border-t pt-4 space-y-4">
            <div className="font-medium mb-2">从已保存结果加载</div>
            
            {/* 加载Chunks */}
            <div>
              <label className="block text-sm font-medium mb-2">Chunks</label>
              <div className="flex gap-2">
                <select
                  value={selectedChunkId}
                  onChange={(e) => setSelectedChunkId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的chunks...</option>
                  {savedChunks.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} ({new Date(result.timestamp).toLocaleString()})
                    </option>
                  ))}
                </select>
                <Button onClick={handleLoadChunks} disabled={!selectedChunkId} variant="outline" size="sm">
                  加载
                </Button>
              </div>
            </div>

            {/* 加载Embeddings */}
            <div>
              <label className="block text-sm font-medium mb-2">Vectors (Embeddings)</label>
              <div className="flex gap-2">
                <select
                  value={selectedEmbeddingId}
                  onChange={(e) => setSelectedEmbeddingId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的embeddings...</option>
                  {savedEmbeddings.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} ({new Date(result.timestamp).toLocaleString()})
                    </option>
                  ))}
                </select>
                <Button onClick={handleLoadEmbeddings} disabled={!selectedEmbeddingId} variant="outline" size="sm">
                  加载
                </Button>
              </div>
            </div>

            {/* 加载Sparse Vectors */}
            <div>
              <label className="block text-sm font-medium mb-2">Sparse Vectors</label>
              <div className="flex gap-2">
                <select
                  value={selectedSparseVectorId}
                  onChange={(e) => setSelectedSparseVectorId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的sparse vectors...</option>
                  {savedSparseVectors.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} ({new Date(result.timestamp).toLocaleString()})
                    </option>
                  ))}
                </select>
                <Button onClick={handleLoadSparseVectors} disabled={!selectedSparseVectorId} variant="outline" size="sm">
                  加载
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

            <Button onClick={loadSavedResults} variant="outline" className="w-full">
              刷新已保存结果列表
            </Button>
          </div>

          {(chunks.length > 0 || vectors.length > 0 || sparseVectors.length > 0) && (
            <div className="p-3 bg-green-50 rounded text-sm">
              <div>✓ Chunks: {chunks.length} 个</div>
              <div>✓ Dense Vectors: {vectors.length} 个</div>
              <div>✓ Sparse Vectors: {sparseVectors.length} 个</div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤3: 写入索引</CardTitle>
          <CardDescription>将稠密向量和/或稀疏向量索引写入知识库</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={handleWriteIndex} 
            disabled={!kbId || chunks.length === 0 || (vectors.length === 0 && sparseVectors.length === 0) || loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {loading ? "写入中..." : "写入索引"}
          </Button>
          <div className="text-sm text-gray-600">
            <div>• 如果提供了稠密向量(Dense Vectors)，将写入稠密向量索引</div>
            <div>• 如果提供了稀疏向量(Sparse Vectors)，将写入稀疏向量索引</div>
            <div>• 可以同时提供两种向量，实现混合索引</div>
            <div>• 如果未提供稀疏向量，系统将自动生成</div>
          </div>

          {indexResult && (
            <div className="p-3 border rounded bg-green-50">
              <div className="font-medium text-green-800 mb-2">✅ 索引写入完成</div>
              <div className="text-sm space-y-1">
                <div>写入数量: {indexResult.written_count} 个点</div>
                {indexResult.has_dense && <div>✓ 包含稠密向量</div>}
                {indexResult.has_sparse && <div>✓ 包含稀疏向量</div>}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

