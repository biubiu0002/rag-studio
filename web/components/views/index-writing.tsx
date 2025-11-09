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
  const [tokensJson, setTokensJson] = useState<string>("")
  const [sparseVectorsJson, setSparseVectorsJson] = useState<string>("")
  
  // 解析后的数据
  const [chunks, setChunks] = useState<any[]>([])
  const [vectors, setVectors] = useState<number[][]>([])
  const [tokensList, setTokensList] = useState<string[][]>([])
  const [sparseVectors, setSparseVectors] = useState<any[]>([])
  
  // 写入结果
  const [indexResult, setIndexResult] = useState<any>(null)
  const jsonFileInputRef = useRef<HTMLInputElement>(null)
  
  // 保存的结果列表
  const [savedChunks, setSavedChunks] = useState<SavedResult[]>([])
  const [savedEmbeddings, setSavedEmbeddings] = useState<SavedResult[]>([])
  const [savedTokens, setSavedTokens] = useState<SavedResult[]>([])
  const [savedSparseVectors, setSavedSparseVectors] = useState<SavedResult[]>([])
  const [selectedChunkId, setSelectedChunkId] = useState<string>("")
  const [selectedEmbeddingId, setSelectedEmbeddingId] = useState<string>("")
  const [selectedTokenId, setSelectedTokenId] = useState<string>("")
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
    const [chunks, embeddings, tokens, sparseVectors] = await Promise.all([
      listResultsByType('chunks'),
      listResultsByType('embeddings'),
      listResultsByType('tokens'),
      listResultsByType('sparse_vectors')
    ])
    setSavedChunks(chunks)
    setSavedEmbeddings(embeddings)
    setSavedTokens(tokens)
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
      
      if (tokensJson) {
        const parsed = JSON.parse(tokensJson)
        if (Array.isArray(parsed)) {
          setTokensList(parsed)
        } else {
          throw new Error("tokens必须是数组格式")
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

  const handleLoadTokens = async () => {
    if (!selectedTokenId) {
      showToast("请选择要加载的tokens结果", "warning")
      return
    }
    try {
      const result = await loadResultFromStorage('tokens', selectedTokenId)
      if (!result || result.type !== 'tokens') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      setTokensList(result.data.tokens || [])
      setTokensJson(JSON.stringify(result.data.tokens, null, 2))
      // 如果tokens中有chunks，也加载
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
      } else if (result.type === 'tokens') {
        setTokensList(result.data.tokens || [])
        setTokensJson(JSON.stringify(result.data.tokens, null, 2))
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

  // 写入向量索引
  const handleWriteVectorIndex = async () => {
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    if (chunks.length === 0 || vectors.length === 0) {
      showToast("请先输入并解析chunks和vectors数据", "warning")
      return
    }
    if (chunks.length !== vectors.length) {
      showToast(`chunks数量(${chunks.length})与vectors数量(${vectors.length})不匹配`, "error")
      return
    }
    
    try {
      setLoading(true)
      
      // 获取schema中定义的向量字段
      let vectorFields: string[] = []
      if (selectedKbSchema && selectedKbSchema.fields) {
        vectorFields = selectedKbSchema.fields
          .filter((field: any) => field.isVectorIndex)
          .map((field: any) => field.name)
      }
      
      const result = await debugAPI.writeVectorIndex({
        kb_id: kbId,
        chunks,
        vectors,
        ...(vectorFields.length > 0 && { fields: vectorFields })
      })
      
      setIndexResult((prev: any) => ({
        ...prev,
        vector: result.data
      }))
      
      showToast("向量索引写入完成！", "success")
    } catch (error) {
      console.error("向量索引写入失败:", error)
      showToast("向量索引写入失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 写入关键词索引
  const handleWriteKeywordIndex = async () => {
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    if (chunks.length === 0 || tokensList.length === 0) {
      showToast("请先输入并解析chunks和tokens数据", "warning")
      return
    }
    if (chunks.length !== tokensList.length) {
      showToast(`chunks数量(${chunks.length})与tokens数量(${tokensList.length})不匹配`, "error")
      return
    }
    
    try {
      setLoading(true)
      
      // 获取schema中定义的关键词字段
      let keywordFields: string[] = []
      if (selectedKbSchema && selectedKbSchema.fields) {
        keywordFields = selectedKbSchema.fields
          .filter((field: any) => field.isKeywordIndex || field.type === "keyword")
          .map((field: any) => field.name)
      }
      
      const result = await debugAPI.writeKeywordIndex({
        kb_id: kbId,
        chunks,
        tokens_list: tokensList,
        ...(keywordFields.length > 0 && { fields: keywordFields })
      })
      
      setIndexResult((prev: any) => ({
        ...prev,
        keyword: result.data
      }))
      
      showToast("关键词索引写入完成！", "success")
    } catch (error) {
      console.error("关键词索引写入失败:", error)
      showToast("关键词索引写入失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 写入稀疏向量索引
  const handleWriteSparseVectorIndex = async () => {
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    if (chunks.length === 0) {
      showToast("请先输入并解析chunks数据", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      // 获取schema中定义的稀疏向量字段
      let sparseVectorFields: string[] = []
      if (selectedKbSchema && selectedKbSchema.fields) {
        sparseVectorFields = selectedKbSchema.fields
          .filter((field: any) => field.isSparseVectorIndex || field.type === "sparse_vector")
          .map((field: any) => field.name)
      }
      
      // 生成稀疏向量（如果还没有提供）
      let sparseVectorsToWrite = sparseVectors
      if (sparseVectorsToWrite.length === 0) {
        // 生成稀疏向量
        sparseVectorsToWrite = []
        for (let i = 0; i < chunks.length; i++) {
          const chunk = chunks[i]
          const textContent = typeof chunk === 'string' ? chunk : chunk.content
          
          try {
            // 获取稀疏向量生成方法
            let method = "bm25"
            if (selectedKbSchema && selectedKbSchema.fields) {
              const sparseField = selectedKbSchema.fields.find((field: any) => field.type === "sparse_vector")
              if (sparseField && sparseField.sparseMethod) {
                method = sparseField.sparseMethod
              }
            }
            
            const result = await debugAPI.generateSparseVector({
              kb_id: kbId,
              text: textContent,
              method: method
            })
            
            // 为稀疏向量添加零向量作为稠密向量（1024维）
            const zeroVector = new Array(1024).fill(0);
            sparseVectorsToWrite.push({
              embedding: zeroVector,
              ...result.data
            });
          } catch (error) {
            console.error(`生成第${i}个分块的稀疏向量失败:`, error)
            // 如果生成失败，添加一个空的稀疏向量和零向量
            const zeroVector = new Array(1024).fill(0);
            sparseVectorsToWrite.push({
              embedding: zeroVector,
              sparse_vector: {},
              qdrant_format: { indices: [], values: [] },
              sparsity: 0
            })
          }
        }
      } else {
        // 如果已经提供了稀疏向量，确保每个都包含稠密向量
        sparseVectorsToWrite = sparseVectors.map((sparseVector, index) => {
          // 如果没有稠密向量，添加一个零向量
          if (!sparseVector.embedding && !sparseVector.dense) {
            const zeroVector = new Array(1024).fill(0);
            return {
              embedding: zeroVector,
              ...sparseVector
            };
          }
          return sparseVector;
        });
      }
      
      // 确保稀疏向量数量与chunks数量一致
      if (chunks.length !== sparseVectorsToWrite.length) {
        showToast(`chunks数量(${chunks.length})与sparse vectors数量(${sparseVectorsToWrite.length})不匹配`, "error")
        return
      }
      
      const result = await debugAPI.writeSparseVectorIndex({
        kb_id: kbId,
        chunks,
        sparse_vectors: sparseVectorsToWrite,
        ...(sparseVectorFields.length > 0 && { fields: sparseVectorFields })
      })
      
      setIndexResult((prev: any) => ({
        ...prev,
        sparse: result.data
      }))
      
      showToast("稀疏向量索引写入完成！", "success")
    } catch (error) {
      console.error("稀疏向量索引写入失败:", error)
      showToast("稀疏向量索引写入失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 同时写入稠密向量和稀疏向量的混合索引
  const handleWriteHybridIndex = async () => {
    if (!kbId) {
      showToast("请选择知识库", "warning")
      return
    }
    if (chunks.length === 0) {
      showToast("请先输入并解析chunks数据", "warning")
      return
    }
    
    try {
      setLoading(true)
      
      const results: any = {}
      
      // 写入稠密向量索引
      if (vectors.length > 0) {
        if (chunks.length !== vectors.length) {
          showToast(`chunks数量(${chunks.length})与vectors数量(${vectors.length})不匹配`, "error")
          return
        }
        
        // 获取schema中定义的向量字段
        let vectorFields: string[] = []
        if (selectedKbSchema && selectedKbSchema.fields) {
          vectorFields = selectedKbSchema.fields
            .filter((field: any) => field.isVectorIndex && field.type !== "sparse_vector")
            .map((field: any) => field.name)
        }
        
        const vectorResult = await debugAPI.writeVectorIndex({
          kb_id: kbId,
          chunks,
          vectors,
          ...(vectorFields.length > 0 && { fields: vectorFields })
        })
        results.vector = vectorResult.data
      }
      
      // 写入稀疏向量索引
      if (sparseVectors.length > 0 || chunks.length > 0) {
        // 获取schema中定义的稀疏向量字段
        let sparseVectorFields: string[] = []
        if (selectedKbSchema && selectedKbSchema.fields) {
          sparseVectorFields = selectedKbSchema.fields
            .filter((field: any) => field.isSparseVectorIndex || field.type === "sparse_vector")
            .map((field: any) => field.name)
        }
        
        // 生成稀疏向量（如果还没有提供）
        let sparseVectorsToWrite = sparseVectors
        if (sparseVectorsToWrite.length === 0) {
          // 生成稀疏向量
          sparseVectorsToWrite = []
          for (let i = 0; i < chunks.length; i++) {
            const chunk = chunks[i]
            const textContent = typeof chunk === 'string' ? chunk : chunk.content
            
            try {
              // 获取稀疏向量生成方法
              let method = "bm25"
              if (selectedKbSchema && selectedKbSchema.fields) {
                const sparseField = selectedKbSchema.fields.find((field: any) => field.type === "sparse_vector")
                if (sparseField && sparseField.sparseMethod) {
                  method = sparseField.sparseMethod
                }
              }
              
              const result = await debugAPI.generateSparseVector({
                kb_id: kbId,
                text: textContent,
                method: method
              })
              
              // 为稀疏向量添加零向量作为稠密向量（1024维）
              const zeroVector = new Array(1024).fill(0);
              sparseVectorsToWrite.push({
                embedding: zeroVector,
                ...result.data
              });
            } catch (error) {
              console.error(`生成第${i}个分块的稀疏向量失败:`, error)
              // 如果生成失败，添加一个空的稀疏向量和零向量
              const zeroVector = new Array(1024).fill(0);
              sparseVectorsToWrite.push({
                embedding: zeroVector,
                sparse_vector: {},
                qdrant_format: { indices: [], values: [] },
                sparsity: 0
              })
            }
          }
        } else {
          // 如果已经提供了稀疏向量，确保每个都包含稠密向量
          sparseVectorsToWrite = sparseVectors.map((sparseVector, index) => {
            // 如果没有稠密向量，添加一个零向量
            if (!sparseVector.embedding && !sparseVector.dense) {
              const zeroVector = new Array(1024).fill(0);
              return {
                embedding: zeroVector,
                ...sparseVector
              };
            }
            return sparseVector;
          });
        }
        
        // 确保稀疏向量数量与chunks数量一致
        if (chunks.length !== sparseVectorsToWrite.length) {
          showToast(`chunks数量(${chunks.length})与sparse vectors数量(${sparseVectorsToWrite.length})不匹配`, "error")
          return
        }
        
        const sparseVectorResult = await debugAPI.writeSparseVectorIndex({
          kb_id: kbId,
          chunks,
          sparse_vectors: sparseVectorsToWrite,
          ...(sparseVectorFields.length > 0 && { fields: sparseVectorFields })
        })
        results.sparse = sparseVectorResult.data
      }
      
      setIndexResult(results)
      
      showToast("混合索引写入完成！", "success")
    } catch (error) {
      console.error("混合索引写入失败:", error)
      showToast("混合索引写入失败: " + (error as Error).message, "error")
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
            <label className="block text-sm font-medium mb-2">Tokens (JSON数组)</label>
            <textarea
              value={tokensJson}
              onChange={(e) => setTokensJson(e.target.value)}
              className="w-full h-32 p-2 border rounded font-mono text-xs"
              placeholder='[["词1", "词2", "词3"], ["词4", "词5"], ...]'
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Sparse Vectors (JSON数组)</label>
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

            {/* 加载Tokens */}
            <div>
              <label className="block text-sm font-medium mb-2">Tokens</label>
              <div className="flex gap-2">
                <select
                  value={selectedTokenId}
                  onChange={(e) => setSelectedTokenId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的tokens...</option>
                  {savedTokens.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} ({new Date(result.timestamp).toLocaleString()})
                    </option>
                  ))}
                </select>
                <Button onClick={handleLoadTokens} disabled={!selectedTokenId} variant="outline" size="sm">
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

          {(chunks.length > 0 || vectors.length > 0 || tokensList.length > 0 || sparseVectors.length > 0) && (
            <div className="p-3 bg-green-50 rounded text-sm">
              <div>✓ Chunks: {chunks.length} 个</div>
              <div>✓ Vectors: {vectors.length} 个</div>
              <div>✓ Tokens: {tokensList.length} 个</div>
              <div>✓ Sparse Vectors: {sparseVectors.length} 个</div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤3: 写入索引</CardTitle>
          <CardDescription>将向量索引和关键词索引写入知识库</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-4 gap-4">
            <Button 
              onClick={handleWriteVectorIndex} 
              disabled={!kbId || chunks.length === 0 || vectors.length === 0 || loading}
              variant="outline"
            >
              {loading ? "写入中..." : "写入向量索引"}
            </Button>
            <Button 
              onClick={handleWriteKeywordIndex} 
              disabled={!kbId || chunks.length === 0 || tokensList.length === 0 || loading}
              variant="outline"
            >
              {loading ? "写入中..." : "写入关键词索引"}
            </Button>
            <Button 
              onClick={handleWriteSparseVectorIndex} 
              disabled={!kbId || chunks.length === 0 || loading}
              variant="outline"
            >
              {loading ? "写入中..." : "写入稀疏向量索引"}
            </Button>
            <Button 
              onClick={handleWriteHybridIndex} 
              disabled={!kbId || chunks.length === 0 || (vectors.length === 0 && sparseVectors.length === 0) || loading}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {loading ? "写入中..." : "写入混合索引"}
            </Button>
          </div>

          {indexResult && (
            <div className="space-y-2">
              {indexResult.vector && (
                <div className="p-3 border rounded bg-green-50">
                  <div className="font-medium text-green-800 mb-2">✅ 向量索引写入完成</div>
                  <div className="text-sm">
                    写入数量: {indexResult.vector.written_count || indexResult.vector.count || "N/A"}
                  </div>
                </div>
              )}
              {indexResult.keyword && (
                <div className="p-3 border rounded bg-green-50">
                  <div className="font-medium text-green-800 mb-2">✅ 关键词索引写入完成</div>
                  <div className="text-sm">
                    唯一词数: {indexResult.keyword.unique_tokens || indexResult.keyword.count || "N/A"}
                  </div>
                </div>
              )}
              {indexResult.sparse && (
                <div className="p-3 border rounded bg-green-50">
                  <div className="font-medium text-green-800 mb-2">✅ 稀疏向量索引写入完成</div>
                  <div className="text-sm">
                    写入数量: {indexResult.sparse.written_count || indexResult.sparse.count || "N/A"}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

