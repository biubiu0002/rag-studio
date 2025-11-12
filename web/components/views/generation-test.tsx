"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { debugAPI } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { saveResultToStorage, listResultsByType, loadResultFromStorage, exportResultToFile, importResultFromFile, SavedResult } from "@/lib/storage"

export default function GenerationTestView() {
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [query, setQuery] = useState<string>("")
  const [context, setContext] = useState<string>("")
  const [generationResult, setGenerationResult] = useState<any>(null)
  const [saveName, setSaveName] = useState<string>("")
  
  // 配置状态
  const [llmConfig, setLlmConfig] = useState({
    provider: "ollama" as "ollama",
    model: "deepseek-r1:1.5b",
    temperature: 0.7,
    max_tokens: 2000,
    stream: true
  })
  
  // 检索结果相关状态
  const [savedRetrieverResults, setSavedRetrieverResults] = useState<SavedResult[]>([])
  const [selectedResultId, setSelectedResultId] = useState<string>("")
  const [loadedRetrieverResult, setLoadedRetrieverResult] = useState<any>(null)
  
  // 生成结果保存/加载状态
  const [savedGenerationResults, setSavedGenerationResults] = useState<SavedResult[]>([])
  const [selectedGenerationResultId, setSelectedGenerationResultId] = useState<string>("")
  
  const jsonFileInputRef = useRef<HTMLInputElement>(null)
  useEffect(() => {
    loadRetrieverResults()
    loadGenerationResults()
  }, [])

  // 加载已保存的检索结果
  const loadRetrieverResults = async () => {
    try {
      const results = await listResultsByType('retrieval_results')
      setSavedRetrieverResults(results)
    } catch (error) {
      console.error("加载已保存的检索结果失败:", error)
    }
  }

  // 加载已保存的生成结果
  const loadGenerationResults = async () => {
    try {
      const results = await listResultsByType('generation_results')
      setSavedGenerationResults(results)
    } catch (error) {
      console.error("加载已保存的生成结果失败:", error)
    }
  }

  // 从已保存的检索结果加载上下文
  const handleLoadRetrieverResult = async () => {
    if (!selectedResultId) {
      showToast("请选择要加载的检索结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('retrieval_results', selectedResultId)
      if (!result || result.type !== 'retrieval_results') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      setLoadedRetrieverResult(result.data)
      
      // 加载检索结果中的查询问题
      if (result.data.query) {
        setQuery(result.data.query)
      }
      
      // 构建上下文文本
      // result.data.results 可能是数组或对象，需要兼容两种格式
      let retrievalResults = []
      if (Array.isArray(result.data.results)) {
        // 检索结果直接是数组
        retrievalResults = result.data.results
      } else if (result.data.results && result.data.results.results && Array.isArray(result.data.results.results)) {
        // 检索结果被包装在对象中
        retrievalResults = result.data.results.results
      }
      
      const contextText = retrievalResults
        .map((r: any) => r.content)
        .join("\n\n")
      setContext(contextText)
      
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  // 执行生成测试
  const handleGenerate = async () => {
    if (!query.trim()) {
      showToast("请输入查询问题", "warning")
      return
    }
    
    try {
      setGenerating(true)
      
      const result = await debugAPI.generate({
        query: query,
        context: context || undefined,
        llm_provider: llmConfig.provider,
        llm_model: llmConfig.model,
        temperature: llmConfig.temperature,
        max_tokens: llmConfig.max_tokens,
        stream: llmConfig.stream
      })
      
      if (result.success && result.data) {
        setGenerationResult(result.data)
        showToast("生成完成！", "success")
      } else {
        showToast("生成失败", "error")
      }
    } catch (error) {
      console.error("生成失败:", error)
      showToast("生成失败: " + (error as Error).message, "error")
    } finally {
      setGenerating(false)
    }
  }

  // 保存生成结果
  const handleSaveResult = async () => {
    if (!generationResult) {
      showToast("没有可保存的生成结果", "warning")
      return
    }
    
    try {
      const name = saveName.trim() || `生成结果_${new Date().toLocaleString()}`
      const id = await saveResultToStorage({
        name,
        type: 'generation_results',
        data: {
          query: generationResult.query,
          context: generationResult.context,
          answer: generationResult.answer,
          prompt: generationResult.prompt,  // 保存完整prompt
          llm_model: generationResult.llm_model,
          generation_time: generationResult.generation_time,
          config: generationResult.config
        },
        metadata: {
          query: generationResult.query,
          llm_model: generationResult.llm_model,
          generation_time: generationResult.generation_time
        }
      })
      
      showToast(`保存成功！ID: ${id}`, "success")
      setSaveName("")
      await loadGenerationResults()
    } catch (error) {
      showToast("保存失败: " + (error as Error).message, "error")
    }
  }

  // 加载已保存的生成结果
  const handleLoadGenerationResult = async () => {
    if (!selectedGenerationResultId) {
      showToast("请选择要加载的生成结果", "warning")
      return
    }
    
    try {
      const result = await loadResultFromStorage('generation_results', selectedGenerationResultId)
      if (!result || result.type !== 'generation_results') {
        showToast("加载失败：无效的结果", "error")
        return
      }
      
      setGenerationResult(result.data)
      setQuery(result.data.query || "")
      setContext(result.data.context || "")
      
      showToast(`加载成功！${result.name}`, "success")
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error")
    }
  }

  // 导出生成结果
  const handleExportResult = () => {
    if (!generationResult) {
      showToast("没有可导出的结果", "warning")
      return
    }
    
    const result: SavedResult = {
      id: '',
      name: saveName.trim() || `生成结果_${new Date().toLocaleString()}`,
      type: 'generation_results',
      data: generationResult,
      timestamp: Date.now(),
      metadata: {
        query: generationResult.query,
        llm_model: generationResult.llm_model,
        generation_time: generationResult.generation_time
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
      if (result.type === 'generation_results') {
        setGenerationResult(result.data)
        setQuery(result.data.query || "")
        setContext(result.data.context || "")
        showToast(`导入成功！${result.name}`, "success")
      } else {
        showToast("文件类型不匹配，需要generation_results类型", "error")
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
        <h2 className="text-2xl font-bold text-gray-900">生成测试</h2>
        <p className="text-sm text-gray-500 mt-1">
          基于检索结果或自定义上下文进行RAG生成测试
        </p>
      </div>

      {/* 步骤1: 加载检索结果 */}
      <Card>
        <CardHeader>
          <CardTitle>步骤1: 加载检索结果</CardTitle>
          <CardDescription>从已保存的检索结果加载上下文</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <select
              value={selectedResultId}
              onChange={(e) => setSelectedResultId(e.target.value)}
              className="flex-1 p-2 border rounded text-sm"
            >
              <option value="">选择已保存的检索结果...</option>
              {savedRetrieverResults.map((result) => (
                <option key={result.id} value={result.id}>
                  {result.name} ({new Date(result.timestamp).toLocaleString()})
                </option>
              ))}
            </select>
            <Button onClick={handleLoadRetrieverResult} disabled={!selectedResultId} variant="outline" size="sm">
              加载
            </Button>
            <Button onClick={loadRetrieverResults} variant="outline" size="sm">
              刷新
            </Button>
          </div>
          
          {loadedRetrieverResult && (
            <div className="p-3 bg-blue-50 rounded text-sm text-blue-800">
              已加载检索结果: {loadedRetrieverResult.results?.length || 0} 个相关文档
            </div>
          )}
        </CardContent>
      </Card>

      {/* 步骤2: 配置LLM参数 */}
      <Card>
        <CardHeader>
          <CardTitle>步骤2: 配置生成参数</CardTitle>
          <CardDescription>设置LLM模型和生成参数</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">对话服务商</label>
              <select
                value={llmConfig.provider}
                onChange={(e) => setLlmConfig({ ...llmConfig, provider: e.target.value as "ollama" })}
                className="w-full p-2 border rounded text-sm"
              >
                <option value="ollama">Ollama</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">对话模型</label>
              <input
                type="text"
                value={llmConfig.model}
                onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
                className="w-full p-2 border rounded text-sm"
                placeholder="deepseek-v3"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">温度 (Temperature)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={llmConfig.temperature}
                onChange={(e) => setLlmConfig({ ...llmConfig, temperature: parseFloat(e.target.value) || 0.7 })}
                className="w-full p-2 border rounded text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">最大Token数</label>
              <input
                type="number"
                value={llmConfig.max_tokens}
                onChange={(e) => setLlmConfig({ ...llmConfig, max_tokens: parseInt(e.target.value) || 2000 })}
                className="w-full p-2 border rounded text-sm"
                min="1"
                max="10000"
              />
            </div>
          </div>
          
          <div className="border-t pt-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={llmConfig.stream}
                onChange={(e) => setLlmConfig({ ...llmConfig, stream: e.target.checked })}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium">启用流式输出</span>
            </label>
          </div>
        </CardContent>
      </Card>

      {/* 步骤3: 输入查询和上下文 */}
      <Card>
        <CardHeader>
          <CardTitle>步骤3: 输入查询和上下文</CardTitle>
          <CardDescription>输入查询问题和可选的上下文信息</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">查询问题</label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="输入您的查询问题..."
              className="w-full h-20 p-2 border rounded text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">上下文（可选）</label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="输入上下文或从检索结果中加载..."
              className="w-full h-24 p-2 border rounded text-sm"
            />
          </div>
          
          <Button 
            onClick={handleGenerate} 
            disabled={!query.trim() || generating}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {generating ? "生成中..." : "执行生成"}
          </Button>
        </CardContent>
      </Card>

      {/* 步骤4: 显示生成结果 */}
      {generationResult && (
        <Card>
          <CardHeader>
            <CardTitle>生成结果</CardTitle>
            <CardDescription>LLM生成的答案与提示词</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 问题 */}
            <div>
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-semibold">Q</span>
                <span>问题</span>
              </h4>
              <div className="p-3 bg-blue-50 rounded text-sm border border-blue-200">
                {generationResult.query}
              </div>
            </div>
            
            {/* 上下文 */}
            {generationResult.context && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <span className="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs font-semibold">CTX</span>
                  <span>检索上下文</span>
                </h4>
                <div className="p-3 bg-purple-50 rounded text-sm max-h-40 overflow-y-auto border border-purple-200">
                  {generationResult.context.substring(0, 500)}
                  {generationResult.context.length > 500 && "..."}
                </div>
              </div>
            )}
            
            {/* Prompt */}
            {generationResult.prompt && (
              <div>
                <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                  <span className="bg-yellow-100 text-yellow-700 px-2 py-1 rounded text-xs font-semibold">PROMPT</span>
                  <span>提示词</span>
                </h4>
                <details className="border rounded bg-yellow-50 border-yellow-200">
                  <summary className="p-3 cursor-pointer font-medium text-sm hover:bg-yellow-100">
                    点击查看完整prompt
                  </summary>
                  <div className="p-3 border-t border-yellow-200 text-sm whitespace-pre-wrap overflow-x-auto max-h-60 overflow-y-auto bg-white font-mono text-xs">
                    {generationResult.prompt}
                  </div>
                </details>
              </div>
            )}
            
            {/* 答案 */}
            <div>
              <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-semibold">A</span>
                <span>答案</span>
              </h4>
              <div className="p-3 bg-green-50 rounded text-sm border border-green-200 min-h-20 max-h-48 overflow-y-auto">
                {generationResult.answer}
              </div>
            </div>
            
            {/* 所用配置 */}
            <div className="border-t pt-4 grid grid-cols-2 gap-4 text-sm">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-gray-600 font-medium">LLM模型</div>
                <div className="text-gray-900">{generationResult.llm_model}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-gray-600 font-medium">生成耗时</div>
                <div className="text-gray-900">{generationResult.generation_time?.toFixed(2) || "N/A"}s</div>
              </div>
              {generationResult.config && (
                <>
                  <div className="bg-gray-50 p-3 rounded">
                    <div className="text-gray-600 font-medium">温度</div>
                    <div className="text-gray-900">{generationResult.config.temperature}</div>
                  </div>
                  <div className="bg-gray-50 p-3 rounded">
                    <div className="text-gray-600 font-medium">Max Tokens</div>
                    <div className="text-gray-900">{generationResult.config.max_tokens || "N/A"}</div>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 步骤5: 保存/加载生成结果 */}
      <Card>
        <CardHeader>
          <CardTitle>步骤5: 保存/加载生成结果</CardTitle>
          <CardDescription>管理生成结果的保存和加载</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {generationResult && (
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
                <Button onClick={handleSaveResult} variant="outline" size="sm">
                  保存
                </Button>
                <Button onClick={handleExportResult} variant="outline" size="sm">
                  导出JSON
                </Button>
              </div>
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium mb-2">从已保存结果加载</label>
            <div className="flex gap-2">
              <select
                value={selectedGenerationResultId}
                onChange={(e) => setSelectedGenerationResultId(e.target.value)}
                className="flex-1 p-2 border rounded text-sm"
              >
                <option value="">选择已保存的生成结果...</option>
                {savedGenerationResults.map((result) => (
                  <option key={result.id} value={result.id}>
                    {result.name} ({new Date(result.timestamp).toLocaleString()})
                  </option>
                ))}
              </select>
              <Button onClick={handleLoadGenerationResult} disabled={!selectedGenerationResultId} variant="outline" size="sm">
                加载
              </Button>
              <Button onClick={loadGenerationResults} variant="outline" size="sm">
                刷新
              </Button>
            </div>
          </div>
          
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
