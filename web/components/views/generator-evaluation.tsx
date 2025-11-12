"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { evaluationAPI, testAPI, knowledgeBaseAPI, TestSet, KnowledgeBase, EvaluationTask, EvaluationSummary } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function GeneratorEvaluationView() {
  const [loading, setLoading] = useState(false)
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedTestSetId, setSelectedTestSetId] = useState<string>("")
  const [currentTask, setCurrentTask] = useState<EvaluationTask | null>(null)
  const [summary, setSummary] = useState<EvaluationSummary | null>(null)
  
  // 配置对话框
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  
  // 生成配置
  const [generationConfig, setGenerationConfig] = useState({
    llm_provider: "ollama",
    llm_model: "deepseek-r1:1.5b",
    temperature: 0.7,
    max_tokens: 2000,
    prompt_template: "",
    retrieval_config: {
      top_k: 10,
      score_threshold: 0.7,
      fusion: "rrf",
    },
  })

  // 加载数据
  useEffect(() => {
    loadKnowledgeBases()
    loadTestSets()
  }, [])

  // 轮询任务状态
  useEffect(() => {
    if (currentTask && currentTask.status === "running") {
      const interval = setInterval(() => {
        loadTaskStatus()
      }, 2000) // 每2秒轮询一次
      return () => clearInterval(interval)
    }
  }, [currentTask])

  const loadKnowledgeBases = async () => {
    try {
      const result = await knowledgeBaseAPI.list(1, 100)
      setKnowledgeBases(result.data)
    } catch (error) {
      console.error("加载知识库失败:", error)
    }
  }

  const loadTestSets = async () => {
    try {
      const result = await testAPI.listTestSets(undefined, "generation", 1, 100)
      setTestSets(result.data)
    } catch (error) {
      console.error("加载测试集失败:", error)
    }
  }

  const loadTaskStatus = async () => {
    if (!currentTask) return

    try {
      const result = await evaluationAPI.getTask(currentTask.id)
      setCurrentTask(result.data)
      
      // 如果任务完成，加载汇总
      if (result.data.status === "completed" && !summary) {
        loadSummary(result.data.id)
      }
    } catch (error) {
      console.error("加载任务状态失败:", error)
    }
  }

  const loadSummary = async (taskId: string) => {
    try {
      const result = await evaluationAPI.getSummary(taskId)
      setSummary(result.data)
    } catch (error) {
      console.error("加载评估汇总失败:", error)
    }
  }

  const handleCreateTask = async () => {
    if (!selectedTestSetId) {
      showToast("请选择测试集", "error")
      return
    }

    try {
      setLoading(true)
      const result = await evaluationAPI.createTask({
        test_set_id: selectedTestSetId,
        evaluation_type: "generation",
        task_name: `生成器评估_${new Date().toLocaleString()}`,
        generation_config: generationConfig,
      })
      
      showToast("评估任务创建成功", "success")
      setConfigDialogOpen(false)
      
      // 加载任务详情
      const taskResult = await evaluationAPI.getTask(result.data.id)
      setCurrentTask(taskResult.data)
    } catch (error) {
      console.error("创建评估任务失败:", error)
      showToast("创建评估任务失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleExecuteTask = async () => {
    if (!currentTask) return

    try {
      setLoading(true)
      const result = await evaluationAPI.executeTask(currentTask.id, true)
      setCurrentTask(result.data)
      showToast("评估任务已开始执行", "success")
    } catch (error) {
      console.error("执行评估任务失败:", error)
      showToast("执行评估任务失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const selectedTestSet = testSets.find((ts) => ts.id === selectedTestSetId)

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">生成器评估</h2>
        <p className="text-sm text-gray-500 mt-1">
          基于RAGAS评估生成器的性能
        </p>
      </div>

      {/* 测试集选择 */}
      <Card>
        <CardHeader>
          <CardTitle>选择测试集</CardTitle>
          <CardDescription>选择一个生成测试集进行评估</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Select value={selectedTestSetId} onValueChange={setSelectedTestSetId}>
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="选择测试集" />
              </SelectTrigger>
              <SelectContent>
                {testSets.map((ts) => (
                  <SelectItem key={ts.id} value={ts.id}>
                    {ts.name} ({ts.case_count} 个用例)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {selectedTestSetId && (
              <Button onClick={() => setConfigDialogOpen(true)}>
                创建评估任务
              </Button>
            )}
          </div>
          {selectedTestSet && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="text-sm">
                <div className="font-medium">{selectedTestSet.name}</div>
                <div className="text-gray-600 mt-1">
                  测试用例数: {selectedTestSet.case_count} | 
                  知识库: {selectedTestSet.kb_id}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 当前任务状态 */}
      {currentTask && (
        <Card>
          <CardHeader>
            <CardTitle>评估任务</CardTitle>
            <CardDescription>
              任务状态: 
              <span className={`ml-2 px-2 py-1 rounded text-xs ${
                currentTask.status === "completed" ? "bg-green-100 text-green-700" :
                currentTask.status === "running" ? "bg-blue-100 text-blue-700" :
                currentTask.status === "failed" ? "bg-red-100 text-red-700" :
                "bg-gray-100 text-gray-700"
              }`}>
                {currentTask.status === "completed" ? "已完成" :
                 currentTask.status === "running" ? "执行中" :
                 currentTask.status === "failed" ? "失败" : "待执行"}
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-gray-500">总用例数</div>
                <div className="text-2xl font-bold">{currentTask.total_cases}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">已完成</div>
                <div className="text-2xl font-bold text-green-600">{currentTask.completed_cases}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">失败</div>
                <div className="text-2xl font-bold text-red-600">{currentTask.failed_cases}</div>
              </div>
            </div>
            
            {currentTask.status === "pending" && (
              <Button onClick={handleExecuteTask} disabled={loading}>
                {loading ? "执行中..." : "开始执行"}
              </Button>
            )}
            
            {currentTask.status === "running" && (
              <div className="text-sm text-gray-600">
                进度: {currentTask.completed_cases} / {currentTask.total_cases} 
                ({Math.round((currentTask.completed_cases / currentTask.total_cases) * 100)}%)
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 评估汇总 */}
      {summary && (
        <Card>
          <CardHeader>
            <CardTitle>评估汇总</CardTitle>
            <CardDescription>RAGAS评估指标汇总</CardDescription>
          </CardHeader>
          <CardContent>
            {summary.overall_ragas_score !== undefined && (
              <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                <div className="text-sm text-gray-600">RAGAS综合评分</div>
                <div className="text-3xl font-bold text-blue-700">
                  {(summary.overall_ragas_score * 100).toFixed(2)}%
                </div>
              </div>
            )}
            
            {summary.overall_ragas_generation_metrics && (
              <div className="space-y-2">
                <h3 className="font-semibold">生成指标</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(summary.overall_ragas_generation_metrics).map(([key, value]) => (
                    <div key={key} className="p-3 bg-gray-50 rounded">
                      <div className="text-xs text-gray-500">{key}</div>
                      <div className="text-lg font-semibold">{(value * 100).toFixed(2)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 配置对话框 */}
      <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建生成器评估任务</DialogTitle>
            <DialogDescription>配置生成器评估参数</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">LLM提供商</label>
              <Select
                value={generationConfig.llm_provider}
                onValueChange={(value) =>
                  setGenerationConfig({ ...generationConfig, llm_provider: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ollama">Ollama</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">LLM模型</label>
              <Input
                value={generationConfig.llm_model}
                onChange={(e) =>
                  setGenerationConfig({ ...generationConfig, llm_model: e.target.value })
                }
                placeholder="例如: deepseek-r1:1.5b"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Temperature</label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={generationConfig.temperature}
                  onChange={(e) =>
                    setGenerationConfig({
                      ...generationConfig,
                      temperature: parseFloat(e.target.value),
                    })
                  }
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Max Tokens</label>
                <Input
                  type="number"
                  value={generationConfig.max_tokens}
                  onChange={(e) =>
                    setGenerationConfig({
                      ...generationConfig,
                      max_tokens: parseInt(e.target.value) || undefined,
                    })
                  }
                  placeholder="可选"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">检索配置 - Top K</label>
              <Input
                type="number"
                value={generationConfig.retrieval_config.top_k}
                onChange={(e) =>
                  setGenerationConfig({
                    ...generationConfig,
                    retrieval_config: {
                      ...generationConfig.retrieval_config,
                      top_k: parseInt(e.target.value) || 10,
                    },
                  })
                }
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Prompt模板（可选）</label>
              <textarea
                className="w-full p-2 border rounded-md min-h-[150px] font-mono text-sm"
                value={generationConfig.prompt_template}
                onChange={(e) =>
                  setGenerationConfig({ ...generationConfig, prompt_template: e.target.value })
                }
                placeholder="留空使用默认模板"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleCreateTask} disabled={loading}>
              {loading ? "创建中..." : "创建任务"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
