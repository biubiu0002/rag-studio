"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { debugAPI } from "@/lib/api"
import { saveResultToStorage, listResultsByType, loadResultFromStorage, exportResultToFile, importResultFromFile, SavedResult } from "@/lib/storage"
import { showToast } from "@/lib/toast"

export default function DocumentProcessing() {
  const [loading, setLoading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [parsedText, setParsedText] = useState<string>("")
  const [chunks, setChunks] = useState<Array<{ index: number; content: string; char_count: number }>>([])
  const [chunkStats, setChunkStats] = useState<{ avg_char_count?: number; max_char_count?: number; min_char_count?: number } | null>(null)
  const [chunkConfig, setChunkConfig] = useState({
    method: "fixed_size",
    chunk_size: 500,
    chunk_overlap: 50
  })
  const fileInputRef = useRef<HTMLInputElement>(null)
  const jsonFileInputRef = useRef<HTMLInputElement>(null)
  
  // 保存的结果列表
  const [savedChunks, setSavedChunks] = useState<SavedResult[]>([])
  const [selectedChunkId, setSelectedChunkId] = useState<string>("")
  const [saveName, setSaveName] = useState<string>("")

  // 加载已保存的结果列表
  useEffect(() => {
    loadSavedChunks().catch(console.error)
  }, [])

  const loadSavedChunks = async () => {
    const results = await listResultsByType('chunks')
    setSavedChunks(results)
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadedFile(file)
      // 重置后续步骤的数据
      setParsedText("")
      setChunks([])
      setChunkStats(null)
    }
  }

  const handleUploadAndParse = async () => {
    if (!uploadedFile) return
    
    try {
      setLoading(true)
      
      // 1. 上传文件
      const uploadResult = await debugAPI.uploadDocument(uploadedFile)
      const tempPath = uploadResult.data.temp_path
      
      // 2. 解析文件
      const parseResult = await debugAPI.parseDocument(tempPath)
      setParsedText(parseResult.data.text)
      
      showToast("文件上传和解析成功！", "success")
    } catch (error) {
      console.error("上传解析失败:", error)
      showToast("上传解析失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleChunk = async () => {
    if (!parsedText) return
    
    try {
      setLoading(true)
      
      const result = await debugAPI.chunkDocument({
        text: parsedText,
        method: chunkConfig.method,
        chunk_size: chunkConfig.chunk_size,
        chunk_overlap: chunkConfig.chunk_overlap
      })
      
      setChunks(result.data.chunks)
      setChunkStats(result.data.statistics)
      
      showToast(`分块完成！共${result.data.chunks.length}个分块`, "success")
    } catch (error) {
      console.error("分块失败:", error)
      showToast("分块失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  // 保存chunks结果
  const handleSaveChunks = async () => {
    if (chunks.length === 0) {
      showToast("没有可保存的分块数据", "warning")
      return
    }
    
    try {
      const name = saveName.trim() || `分块结果_${new Date().toLocaleString()}`
      const id = await saveResultToStorage({
        name,
        type: 'chunks',
        data: {
          chunks,
          statistics: chunkStats,
          config: chunkConfig
        },
        metadata: {
          chunk_count: chunks.length,
          method: chunkConfig.method
        }
      })
      
      showToast(`保存成功！ID: ${id}`, "success")
      setSaveName("")
      await loadSavedChunks()
    } catch (error) {
      showToast("保存失败: " + (error as Error).message, "error")
    }
  }

  // 加载已保存的chunks
  const handleLoadChunks = async () => {
    if (!selectedChunkId) {
      showToast("请选择要加载的结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('chunks', selectedChunkId)
      if (!result || result.type !== 'chunks') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      setChunks(result.data.chunks || [])
      setChunkStats(result.data.statistics || null)
      if (result.data.config) {
        setChunkConfig(result.data.config)
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
      if (result.type !== 'chunks') {
        showToast("文件类型不匹配，需要chunks类型", "error")
        return
      }
      
      setChunks(result.data.chunks || [])
      setChunkStats(result.data.statistics || null)
      if (result.data.config) {
        setChunkConfig(result.data.config)
      }
      
      showToast(`导入成功！${result.name}`, "success")
    } catch (error) {
      showToast("导入失败: " + (error as Error).message, "error")
    } finally {
      if (jsonFileInputRef.current) {
        jsonFileInputRef.current.value = ''
      }
    }
  }

  // 导出为JSON文件
  const handleExportChunks = () => {
    if (chunks.length === 0) {
      showToast("没有可导出的分块数据", "warning")
      return
    }
    
    const result: SavedResult = {
      id: '',
      name: saveName.trim() || `分块结果_${new Date().toLocaleString()}`,
      type: 'chunks',
      data: {
        chunks,
        statistics: chunkStats,
        config: chunkConfig
      },
      timestamp: Date.now(),
      metadata: {
        chunk_count: chunks.length,
        method: chunkConfig.method
      }
    }
    
    exportResultToFile(result)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">文档处理</h2>
        <p className="text-sm text-gray-500 mt-1">
          上传文档、解析文本内容、进行分块处理
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>步骤1: 文件上传与解析</CardTitle>
          <CardDescription>上传文档文件并解析为文本内容</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 文件上传 */}
          <div>
            <label className="block text-sm font-medium mb-2">选择文档文件</label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="flex items-center gap-4">
              <Button onClick={() => fileInputRef.current?.click()}>
                选择文件
              </Button>
              {uploadedFile && (
                <span className="text-sm text-gray-600">
                  {uploadedFile.name} ({(uploadedFile.size / 1024).toFixed(2)} KB)
                </span>
              )}
            </div>
          </div>

          <Button 
            onClick={handleUploadAndParse} 
            disabled={!uploadedFile || loading}
            className="w-full"
          >
            {loading ? "处理中..." : "上传并解析"}
          </Button>

          {/* 解析结果 */}
          {parsedText && (
            <div>
              <div className="font-medium mb-2">解析结果:</div>
              <textarea
                value={parsedText}
                onChange={(e) => setParsedText(e.target.value)}
                className="w-full h-48 p-2 border rounded"
                placeholder="解析后的文本内容..."
              />
              <div className="text-sm text-gray-500 mt-1">
                字符数: {parsedText.length}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤2: 文档分块</CardTitle>
          <CardDescription>将解析后的文本切分为多个分块</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 分块配置 */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">分块方法</label>
              <select
                value={chunkConfig.method}
                onChange={(e) => setChunkConfig({ ...chunkConfig, method: e.target.value })}
                className="w-full p-2 border rounded"
              >
                <option value="fixed_size">固定大小</option>
                <option value="sentence">按句子</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">分块大小</label>
              <input
                type="number"
                value={chunkConfig.chunk_size}
                onChange={(e) => setChunkConfig({ ...chunkConfig, chunk_size: parseInt(e.target.value) || 500 })}
                className="w-full p-2 border rounded"
                min="100"
                max="2000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">重叠大小</label>
              <input
                type="number"
                value={chunkConfig.chunk_overlap}
                onChange={(e) => setChunkConfig({ ...chunkConfig, chunk_overlap: parseInt(e.target.value) || 50 })}
                className="w-full p-2 border rounded"
                min="0"
                max="200"
              />
            </div>
          </div>

          <Button 
            onClick={handleChunk} 
            disabled={!parsedText || loading}
            className="w-full"
          >
            {loading ? "分块中..." : "开始分块"}
          </Button>

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
              <Button onClick={handleSaveChunks} disabled={chunks.length === 0} variant="outline">
                保存到本地
              </Button>
              <Button onClick={handleExportChunks} disabled={chunks.length === 0} variant="outline">
                导出JSON
              </Button>
            </div>

            {/* 从已保存结果加载 */}
            <div>
              <label className="block text-sm font-medium mb-2">从已保存结果加载</label>
              <div className="flex gap-2">
                <select
                  value={selectedChunkId}
                  onChange={(e) => setSelectedChunkId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的结果...</option>
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
          </div>

          {/* 分块结果 */}
          {chunks.length > 0 && (
            <div>
              <div className="font-medium mb-2">
                分块结果: 共 {chunks.length} 个分块
              </div>
              {chunkStats && (
                <div className="mb-4 p-3 bg-gray-50 rounded text-sm">
                  <div>平均字符数: {chunkStats.avg_char_count?.toFixed(0)}</div>
                  <div>最大字符数: {chunkStats.max_char_count}</div>
                  <div>最小字符数: {chunkStats.min_char_count}</div>
                </div>
              )}
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {chunks.slice(0, 10).map((chunk, idx) => (
                  <div key={idx} className="p-3 border rounded bg-gray-50">
                    <div className="text-xs text-gray-500 mb-1">
                      Chunk {chunk.index} | {chunk.char_count} 字符
                    </div>
                    <div className="text-sm">
                      {chunk.content.substring(0, 150)}...
                    </div>
                  </div>
                ))}
              </div>
              {chunks.length > 10 && (
                <div className="text-sm text-gray-500 mt-2">
                  ...还有 {chunks.length - 10} 个分块
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
