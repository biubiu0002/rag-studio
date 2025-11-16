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
import { Progress } from "@/components/ui/progress"
import { evaluationAPI, knowledgeBaseAPI, testAPI, EvaluationTask, KnowledgeBase, TestSet, EvaluationSummary, EvaluationCaseResult } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { Plus, Eye, Archive, Loader2, CheckCircle2, XCircle, Clock, GitCompare } from "lucide-react"
import RetrievalConfigComponent, { defaultRetrievalConfig, RetrievalConfig } from "@/components/ui/retrieval-config"

type ViewMode = "list" | "create" | "detail" | "compare"
type CreateStep = "config" | "cases"

export default function EvaluationTasksView() {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<EvaluationTask[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKbId, setSelectedKbId] = useState<string>("")
  const [selectedStatus, setSelectedStatus] = useState<string>("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 视图状态
  const [viewMode, setViewMode] = useState<ViewMode>("list")
  const [selectedTask, setSelectedTask] = useState<EvaluationTask | null>(null)
  const [createStep, setCreateStep] = useState<CreateStep>("config")
  
  // 创建任务相关状态
  const [selectedKbForCreate, setSelectedKbForCreate] = useState<string>("")
  const [selectedTestSetForCreate, setSelectedTestSetForCreate] = useState<string>("")
  const [evaluationType, setEvaluationType] = useState<"retrieval" | "generation">("retrieval")
  const [taskName, setTaskName] = useState("")
  const [retrievalConfig, setRetrievalConfig] = useState<RetrievalConfig>(defaultRetrievalConfig)
  const [testSetsForKb, setTestSetsForKb] = useState<TestSet[]>([])
  
  // 评估结果相关状态
  const [evaluationSummary, setEvaluationSummary] = useState<EvaluationSummary | null>(null)
  const [caseResults, setCaseResults] = useState<EvaluationCaseResult[]>([])
  const [caseResultsPage, setCaseResultsPage] = useState(1)
  const [caseResultsTotal, setCaseResultsTotal] = useState(0)
  const [loadingResults, setLoadingResults] = useState(false)
  const [selectedResult, setSelectedResult] = useState<EvaluationCaseResult | null>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  
  // 任务对比相关状态
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set())
  const [compareSummaries, setCompareSummaries] = useState<Map<string, EvaluationSummary>>(new Map())
  const [loadingCompare, setLoadingCompare] = useState(false)

  // 加载任务列表
  useEffect(() => {
    if (viewMode === "list") {
      loadTasks()
    }
  }, [selectedKbId, selectedStatus, page, viewMode])

  // 清理不在当前任务列表中的选中任务
  useEffect(() => {
    if (tasks.length > 0 && selectedTaskIds.size > 0) {
      const currentTaskIds = new Set(tasks.map(t => t.id))
      const newSelected = new Set(Array.from(selectedTaskIds).filter(id => currentTaskIds.has(id)))
      if (newSelected.size !== selectedTaskIds.size) {
        setSelectedTaskIds(newSelected)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tasks])
  
  const loadEvaluationResults = async () => {
    if (!selectedTask) return
    
    try {
      setLoadingResults(true)
      
      // 加载评估汇总
      try {
        const summaryResult = await evaluationAPI.getSummary(selectedTask.id)
        setEvaluationSummary(summaryResult.data)
      } catch (error) {
        // 汇总可能不存在，忽略错误
        console.log("评估汇总不存在或未生成")
      }
      
      // 加载用例结果列表
      const resultsResult = await evaluationAPI.listCaseResults(selectedTask.id, caseResultsPage, 20)
      setCaseResults(resultsResult.data)
      setCaseResultsTotal(resultsResult.total)
    } catch (error) {
      console.error("加载评估结果失败:", error)
      showToast("加载评估结果失败", "error")
    } finally {
      setLoadingResults(false)
    }
  }

  // 加载评估结果
  useEffect(() => {
    if (viewMode === "detail" && selectedTask && selectedTask.status === "completed") {
      loadEvaluationResults()
    }
  }, [viewMode, selectedTask?.id, selectedTask?.status, caseResultsPage])

  // 轮询运行中的任务
  useEffect(() => {
    const runningTasks = tasks.filter(t => t.status === "running")
    if (runningTasks.length > 0) {
      const interval = setInterval(() => {
        loadTasks()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [tasks])

  const loadTasks = async () => {
    try {
      setLoading(true)
      const result = await evaluationAPI.listTasks(
        undefined, // testSetId
        selectedKbId && selectedKbId !== "all" ? selectedKbId : undefined,
        selectedStatus && selectedStatus !== "all" ? selectedStatus : undefined,
        page,
        pageSize
      )
      setTasks(result.data)
      setTotal(result.total)
    } catch (error) {
      console.error("加载评估任务失败:", error)
      showToast("加载评估任务失败", "error")
    } finally {
      setLoading(false)
    }
  }

  const loadKnowledgeBases = async () => {
    try {
      const result = await knowledgeBaseAPI.list(1, 100)
      setKnowledgeBases(result.data)
    } catch (error) {
      console.error("加载知识库失败:", error)
    }
  }

  const loadTestSetsForKb = async (kbId: string) => {
    try {
      const result = await testAPI.getKnowledgeBaseTestSets(kbId, 1, 100)
      setTestSetsForKb(result.data.map(item => item.test_set))
    } catch (error) {
      console.error("加载知识库测试集失败:", error)
      showToast("加载测试集失败", "error")
    }
  }

  const handleKbSelectForCreate = async (kbId: string) => {
    setSelectedKbForCreate(kbId)
    if (kbId) {
      await loadTestSetsForKb(kbId)
    } else {
      setTestSetsForKb([])
    }
  }

  const handleCreateTaskStep1 = () => {
    if (!selectedKbForCreate) {
      showToast("请选择知识库", "error")
      return
    }
    if (!selectedTestSetForCreate) {
      showToast("请选择测试集", "error")
      return
    }
    setCreateStep("cases")
  }

  const handleCreateTask = async () => {
    if (!selectedKbForCreate || !selectedTestSetForCreate) {
      showToast("请完成配置", "error")
      return
    }

    try {
      setLoading(true)
      const result = await evaluationAPI.createTask({
        test_set_id: selectedTestSetForCreate,
        kb_id: selectedKbForCreate,
        evaluation_type: evaluationType,
        task_name: taskName || `${evaluationType === "retrieval" ? "检索器" : "生成器"}评估_${new Date().toLocaleString()}`,
        retrieval_config: evaluationType === "retrieval" ? retrievalConfig : undefined,
      })
      
      showToast("评估任务创建成功", "success")
      setViewMode("list")
      resetCreateForm()
      loadTasks()
    } catch (error) {
      console.error("创建评估任务失败:", error)
      showToast("创建评估任务失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleArchiveTask = async (taskId: string) => {
    try {
      setLoading(true)
      // TODO: 实现归档API
      showToast("任务已归档", "success")
      loadTasks()
    } catch (error) {
      console.error("归档任务失败:", error)
      showToast("归档任务失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleExecuteTask = async (taskId: string) => {
    try {
      setLoading(true)
      await evaluationAPI.executeTask(taskId, true)
      showToast("评估任务已开始执行", "success")
      loadTasks()
    } catch (error) {
      console.error("执行评估任务失败:", error)
      showToast("执行评估任务失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const resetCreateForm = () => {
    setSelectedKbForCreate("")
    setSelectedTestSetForCreate("")
    setEvaluationType("retrieval")
    setTaskName("")
    setCreateStep("config")
    setTestSetsForKb([])
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case "pending":
        return <Clock className="h-4 w-4 text-gray-600" />
      case "archived":
        return <Archive className="h-4 w-4 text-gray-400" />
      default:
        return null
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "已完成"
      case "failed":
        return "失败"
      case "running":
        return "运行中"
      case "pending":
        return "待执行"
      case "archived":
        return "已归档"
      default:
        return status
    }
  }

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  // 加载对比任务的评估汇总
  const loadCompareSummaries = async (taskIds: string[]) => {
    try {
      setLoadingCompare(true)
      const summaries = new Map<string, EvaluationSummary>()
      
      await Promise.all(
        taskIds.map(async (taskId) => {
          try {
            const result = await evaluationAPI.getSummary(taskId)
            summaries.set(taskId, result.data)
          } catch (error) {
            console.log(`任务 ${taskId} 的评估汇总不存在或未生成`)
          }
        })
      )
      
      setCompareSummaries(summaries)
    } catch (error) {
      console.error("加载对比数据失败:", error)
      showToast("加载对比数据失败", "error")
    } finally {
      setLoadingCompare(false)
    }
  }

  // 切换任务选中状态
  const toggleTaskSelection = (taskId: string) => {
    const newSelected = new Set(selectedTaskIds)
    if (newSelected.has(taskId)) {
      newSelected.delete(taskId)
    } else {
      newSelected.add(taskId)
    }
    setSelectedTaskIds(newSelected)
  }

  // 全选/取消全选
  const toggleSelectAll = () => {
    const completedTasks = tasks.filter(t => t.status === "completed")
    if (selectedTaskIds.size === completedTasks.length) {
      setSelectedTaskIds(new Set())
    } else {
      setSelectedTaskIds(new Set(completedTasks.map(t => t.id)))
    }
  }

  // 进入对比视图
  const handleCompare = async () => {
    const taskIds = Array.from(selectedTaskIds)
    if (taskIds.length < 2) {
      showToast("请至少选择2个已完成的任务进行对比", "error")
      return
    }
    
    // 验证选中的任务都是已完成状态
    const selectedTasks = tasks.filter(t => taskIds.includes(t.id))
    const incompleteTasks = selectedTasks.filter(t => t.status !== "completed")
    if (incompleteTasks.length > 0) {
      showToast("只能对比已完成的任务", "error")
      return
    }
    
    setViewMode("compare")
    await loadCompareSummaries(taskIds)
  }

  // 计算热力图颜色（使用绿色系渐变，数值越大颜色越深）
  const getHeatmapColor = (value: number, min: number, max: number): string => {
    if (min === max) return "bg-green-100"
    
    // 计算归一化值 (0-1)
    const normalized = (value - min) / (max - min)
    
    // 使用绿色系渐变：从浅绿到深绿，分为5个等级
    if (normalized < 0.2) {
      return "bg-green-50"
    } else if (normalized < 0.4) {
      return "bg-green-100"
    } else if (normalized < 0.6) {
      return "bg-green-200"
    } else if (normalized < 0.8) {
      return "bg-green-300"
    } else {
      return "bg-green-400"
    }
  }

  // 计算一行中所有数值的范围
  const getRowValueRange = (
    metric: string,
    metricsData: Record<string, Record<string, number>>,
    tasks: EvaluationTask[]
  ): { min: number; max: number } => {
    const values: number[] = []
    tasks.forEach(task => {
      const value = metricsData[task.id]?.[metric]
      if (value !== undefined && typeof value === 'number') {
        values.push(value)
      }
    })
    
    if (values.length === 0) {
      return { min: 0, max: 1 }
    }
    
    return {
      min: Math.min(...values),
      max: Math.max(...values)
    }
  }

  // 创建任务视图 - 步骤1：配置
  if (viewMode === "create" && createStep === "config") {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">创建评估任务</h2>
            <p className="text-sm text-gray-500 mt-1">步骤1/2：确认检索配置</p>
          </div>
          <Button variant="outline" onClick={() => {
            setViewMode("list")
            resetCreateForm()
          }}>
            取消
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>选择知识库和测试集</CardTitle>
            <CardDescription>选择要评估的知识库和已导入的测试集</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">知识库 *</label>
              <Select value={selectedKbForCreate} onValueChange={handleKbSelectForCreate}>
                <SelectTrigger>
                  <SelectValue placeholder="选择知识库" />
                </SelectTrigger>
                <SelectContent>
                  {knowledgeBases.map((kb) => (
                    <SelectItem key={kb.id} value={kb.id}>
                      {kb.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedKbForCreate && (
              <div>
                <label className="block text-sm font-medium mb-2">测试集 *</label>
                {testSetsForKb.length === 0 ? (
                  <div className="p-4 border rounded-lg bg-yellow-50">
                    <p className="text-sm text-yellow-800 mb-2">
                      该知识库暂无已导入的测试集
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        // 导航到测试集管理页面
                        window.dispatchEvent(new CustomEvent('navigate', {
                          detail: { view: 'test-set-management', path: ['RAG Studio', '测试集'] }
                        }))
                      }}
                    >
                      前往导入测试集
                    </Button>
                  </div>
                ) : (
                  <Select value={selectedTestSetForCreate} onValueChange={setSelectedTestSetForCreate}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择测试集" />
                    </SelectTrigger>
                    <SelectContent>
                      {testSetsForKb.map((ts) => (
                        <SelectItem key={ts.id} value={ts.id}>
                          {ts.name} ({ts.case_count} 条用例)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">评估类型 *</label>
              <Select value={evaluationType} onValueChange={(value) => setEvaluationType(value as "retrieval" | "generation")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="retrieval">检索器评估</SelectItem>
                  <SelectItem value="generation">生成器评估</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {evaluationType === "retrieval" && (
              <div className="space-y-4 pt-4 border-t">
                <h3 className="font-medium">检索配置</h3>
                <RetrievalConfigComponent value={retrievalConfig} onChange={setRetrievalConfig} />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium mb-2">任务名称（可选）</label>
              <Input
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                placeholder="留空将自动生成"
              />
            </div>
          </CardContent>
          <CardContent className="pt-0">
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => {
                setViewMode("list")
                resetCreateForm()
              }}>
                取消
              </Button>
              <Button onClick={handleCreateTaskStep1} disabled={!selectedKbForCreate || !selectedTestSetForCreate}>
                下一步：查看/编辑用例
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // 创建任务视图 - 步骤2：用例
  if (viewMode === "create" && createStep === "cases") {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">创建评估任务</h2>
            <p className="text-sm text-gray-500 mt-1">步骤2/2：查看/编辑用例</p>
          </div>
          <Button variant="outline" onClick={() => setCreateStep("config")}>
            上一步
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>测试用例</CardTitle>
            <CardDescription>
              可以查看用例详情，也可以新增或编辑用例（仅影响本次评估任务）
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-gray-500">
              <p>用例列表功能待实现</p>
              <p className="text-sm mt-2">当前将使用测试集中的所有用例进行评估</p>
            </div>
          </CardContent>
          <CardContent className="pt-0">
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCreateStep("config")}>
                上一步
              </Button>
              <Button onClick={handleCreateTask} disabled={loading}>
                {loading ? "创建中..." : "创建评估任务"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // 任务详情视图
  if (viewMode === "detail" && selectedTask) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{selectedTask.task_name || "评估任务详情"}</h2>
            <div className="flex items-center gap-2 mt-2">
              {getStatusIcon(selectedTask.status)}
              <span className="text-sm text-gray-500">{getStatusText(selectedTask.status)}</span>
            </div>
          </div>
          <Button variant="outline" onClick={() => {
            setViewMode("list")
            setSelectedTask(null)
          }}>
            返回列表
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>任务信息</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">测试集ID</div>
                <div className="font-medium">{selectedTask.test_set_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">知识库ID</div>
                <div className="font-medium">{selectedTask.kb_id}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">评估类型</div>
                <div className="font-medium">
                  {selectedTask.evaluation_type === "retrieval" ? "检索器评估" : "生成器评估"}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-500">总用例数</div>
                <div className="font-medium">{selectedTask.total_cases}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">已完成</div>
                <div className="font-medium">{selectedTask.completed_cases}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">失败</div>
                <div className="font-medium text-red-600">{selectedTask.failed_cases}</div>
              </div>
            </div>

            {selectedTask.status === "running" && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">执行进度</span>
                  <span className="text-sm font-medium">
                    {Math.round((selectedTask.completed_cases / selectedTask.total_cases) * 100)}%
                  </span>
                </div>
                <Progress value={(selectedTask.completed_cases / selectedTask.total_cases) * 100} />
              </div>
            )}

            {selectedTask.status === "pending" && (
              <Button onClick={() => handleExecuteTask(selectedTask.id)} disabled={loading}>
                执行任务
              </Button>
            )}
          </CardContent>
        </Card>

        {/* 评估汇总结果 */}
        {selectedTask.status === "completed" && (
          <>
            {evaluationSummary && (
              <Card>
                <CardHeader>
                  <CardTitle>评估汇总指标</CardTitle>
                  <CardDescription>整体评估结果统计</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* 检索指标 */}
                    {evaluationSummary.overall_retrieval_metrics && (
                      <div>
                        <h3 className="font-semibold mb-2">检索指标</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(evaluationSummary.overall_retrieval_metrics).map(([key, value]) => (
                            <div key={key} className="p-3 bg-gray-50 rounded">
                              <div className="text-sm text-gray-500">{key}</div>
                              <div className="text-lg font-bold">{typeof value === 'number' ? value.toFixed(4) : value}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* RAGAS检索指标 */}
                    {evaluationSummary.overall_ragas_retrieval_metrics && (
                      <div>
                        <h3 className="font-semibold mb-2">RAGAS检索指标</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(evaluationSummary.overall_ragas_retrieval_metrics).map(([key, value]) => (
                            <div key={key} className="p-3 bg-blue-50 rounded">
                              <div className="text-sm text-blue-600">{key}</div>
                              <div className="text-lg font-bold text-blue-700">{typeof value === 'number' ? value.toFixed(4) : value}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* RAGAS生成指标 */}
                    {evaluationSummary.overall_ragas_generation_metrics && (
                      <div>
                        <h3 className="font-semibold mb-2">RAGAS生成指标</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(evaluationSummary.overall_ragas_generation_metrics).map(([key, value]) => (
                            <div key={key} className="p-3 bg-green-50 rounded">
                              <div className="text-sm text-green-600">{key}</div>
                              <div className="text-lg font-bold text-green-700">{typeof value === 'number' ? value.toFixed(4) : value}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* 总体RAGAS分数 */}
                    {evaluationSummary.overall_ragas_score !== undefined && (
                      <div className="p-4 bg-purple-50 rounded-lg border-2 border-purple-200">
                        <div className="text-sm text-purple-600">总体RAGAS分数</div>
                        <div className="text-3xl font-bold text-purple-700 mt-1">
                          {evaluationSummary.overall_ragas_score.toFixed(4)}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* 用例结果列表 */}
            <Card>
              <CardHeader>
                <CardTitle>用例评估结果</CardTitle>
                <CardDescription>共 {caseResultsTotal} 个用例结果</CardDescription>
              </CardHeader>
              <CardContent>
                {loadingResults ? (
                  <div className="text-center py-8">加载中...</div>
                ) : caseResults.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">暂无用例结果</div>
                ) : (
                  <div className="space-y-4">
                    {caseResults.map((result) => (
                      <div key={result.id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium mb-2">{result.query}</div>
                            <div className="flex items-center gap-4 text-sm flex-wrap">
                              {result.status === "completed" && (
                                <>
                                  {result.retrieval_metrics && (
                                    <div className="flex flex-wrap gap-3">
                                      {Object.entries(result.retrieval_metrics).map(([key, value]) => (
                                        <div key={key} className="text-gray-600">
                                          <span className="font-medium">{key}:</span> {typeof value === 'number' ? value.toFixed(4) : value}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                  {result.ragas_score !== undefined && (
                                    <div className="px-3 py-1 bg-purple-100 text-purple-700 rounded">
                                      RAGAS: {result.ragas_score.toFixed(4)}
                                    </div>
                                  )}
                                  {result.retrieval_time !== undefined && (
                                    <div className="text-gray-500">
                                      检索耗时: {result.retrieval_time.toFixed(3)}s
                                    </div>
                                  )}
                                </>
                              )}
                              {result.status === "failed" && (
                                <div className="text-red-600">
                                  失败: {result.error_message || "未知错误"}
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="ml-4 flex items-center gap-2">
                            {result.status === "completed" && (
                              <CheckCircle2 className="h-5 w-5 text-green-600" />
                            )}
                            {result.status === "failed" && (
                              <XCircle className="h-5 w-5 text-red-600" />
                            )}
                            {result.status === "completed" && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedResult(result)
                                  setDetailDialogOpen(true)
                                }}
                                className="flex items-center gap-1"
                              >
                                <Eye className="h-4 w-4" />
                                <span>查看详情</span>
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {/* 分页 */}
                {caseResultsTotal > 20 && (
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-gray-500">
                      第 {caseResultsPage} 页，共 {Math.ceil(caseResultsTotal / 20)} 页
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={caseResultsPage === 1}
                        onClick={() => setCaseResultsPage(caseResultsPage - 1)}
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={caseResultsPage >= Math.ceil(caseResultsTotal / 20)}
                        onClick={() => setCaseResultsPage(caseResultsPage + 1)}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
        
        {/* 详情弹窗 */}
        <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>用例评估详情</DialogTitle>
              <DialogDescription>
                {selectedResult?.query}
              </DialogDescription>
            </DialogHeader>
            
            {selectedResult && (
              <div className="space-y-6 mt-4">
                {/* 检索结果详情 */}
                {selectedResult.retrieved_chunks && selectedResult.retrieved_chunks.length > 0 ? (
                  <div>
                    <div className="mb-4 font-semibold text-base text-gray-900">
                      检索结果 ({selectedResult.retrieved_chunks.length} 条)
                    </div>
                    <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                      {(() => {
                        // 按得分排序（降序）
                        const sortedChunks = [...selectedResult.retrieved_chunks].sort((a: any, b: any) => {
                          const scoreA = a.score ?? 0
                          const scoreB = b.score ?? 0
                          return scoreB - scoreA
                        })
                        
                        // 构建期望答案的映射（优先使用external_id，如果没有则使用chunk_id）
                        const expectedMap = new Map<string, number>() // key: external_id 或 chunk_id, value: relevance_score
                        if (selectedResult.expected_answers && Array.isArray(selectedResult.expected_answers)) {
                          selectedResult.expected_answers.forEach((answer: any) => {
                            const relevanceScore = answer.relevance_score ?? 0
                            // 优先使用external_id
                            if (answer.external_id) {
                              expectedMap.set(answer.external_id, relevanceScore)
                            }
                            // 如果有chunk_id，也添加到映射中
                            if (answer.chunk_id) {
                              const chunkId = String(answer.chunk_id).trim()
                              expectedMap.set(chunkId, relevanceScore)
                              expectedMap.set(chunkId.toLowerCase(), relevanceScore)
                            }
                          })
                        }
                        
                        return sortedChunks.map((chunk: any, index: number) => {
                          // 尝试通过external_id匹配（优先）
                          let isExpected = false
                          let relevanceScore: number | undefined = undefined
                          
                          // 从metadata中获取external_id
                          const chunkMetadata = chunk.metadata || {}
                          const externalId = chunkMetadata.external_id
                          
                          if (externalId && expectedMap.has(externalId)) {
                            isExpected = true
                            relevanceScore = expectedMap.get(externalId)
                          } else if (chunk.chunk_id) {
                            // 如果没有external_id，尝试通过chunk_id匹配
                            const chunkId = String(chunk.chunk_id).trim()
                            if (expectedMap.has(chunkId)) {
                              isExpected = true
                              relevanceScore = expectedMap.get(chunkId)
                            } else {
                              const chunkIdLower = chunkId.toLowerCase()
                              if (expectedMap.has(chunkIdLower)) {
                                isExpected = true
                                relevanceScore = expectedMap.get(chunkIdLower)
                              }
                            }
                          }
                          
                          return (
                            <div
                              key={`chunk-${chunk.chunk_id || chunk.id || index}-${index}`}
                              className={`bg-white p-4 rounded-lg border-2 transition-colors ${
                                isExpected 
                                  ? 'border-green-300 bg-green-50' 
                                  : 'border-gray-200 hover:border-blue-300'
                              }`}
                            >
                              <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-3 flex-1">
                                  <div className={`flex items-center justify-center w-10 h-10 rounded-full font-semibold text-sm ${
                                    isExpected
                                      ? 'bg-green-200 text-green-800'
                                      : 'bg-blue-100 text-blue-700'
                                  }`}>
                                    #{index + 1}
                                  </div>
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                                      <span className="text-xs font-medium text-gray-500">
                                        分块ID: {chunk.chunk_id || 'N/A'}
                                      </span>
                                      {isExpected && (
                                        <span className="px-2 py-1 bg-green-200 text-green-800 rounded text-xs font-semibold">
                                          期望答案
                                        </span>
                                      )}
                                      {chunk.source && (
                                        <span className={`text-xs px-2 py-0.5 rounded ${
                                          chunk.source === 'vector' ? 'bg-green-100 text-green-700' :
                                          chunk.source === 'keyword' ? 'bg-yellow-100 text-yellow-700' :
                                          'bg-purple-100 text-purple-700'
                                        }`}>
                                          {chunk.source === 'vector' ? '向量' :
                                           chunk.source === 'keyword' ? '关键词' :
                                           chunk.source === 'hybrid' ? '混合' : chunk.source}
                                        </span>
                                      )}
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                                      {chunk.score !== undefined && (
                                        <div>
                                          检索相似度: <span className="font-medium text-blue-600">{chunk.score.toFixed(4)}</span>
                                        </div>
                                      )}
                                      {isExpected && relevanceScore !== undefined && (
                                        <div className="flex items-center gap-1">
                                          <span className="text-green-700 font-semibold">期望关联度:</span>
                                          <span className="px-2 py-0.5 bg-green-200 text-green-800 rounded font-bold text-sm">
                                            {relevanceScore.toFixed(2)}
                                          </span>
                                        </div>
                                      )}
                                      {chunk.rank && (
                                        <div>
                                          原始排名: <span className="font-medium">#{chunk.rank}</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                              <div className="mt-3 p-3 bg-white rounded text-sm text-gray-700 whitespace-pre-wrap break-words border border-gray-200">
                                {chunk.content || '无内容'}
                              </div>
                              {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                                <details className="mt-2">
                                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                    查看元数据
                                  </summary>
                                  <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                                    {JSON.stringify(chunk.metadata, null, 2)}
                                  </pre>
                                </details>
                              )}
                            </div>
                          )
                        })
                      })()}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 py-4">
                    暂无检索结果
                  </div>
                )}
                
                {/* 期望答案列表 */}
                {selectedResult.expected_answers && selectedResult.expected_answers.length > 0 && (
                  <div>
                    <div className="mb-4 font-semibold text-base text-gray-900">
                      期望答案 ({selectedResult.expected_answers.length} 条)
                    </div>
                    <div className="space-y-2">
                      {selectedResult.expected_answers.map((answer: any, index: number) => (
                        <div key={index} className="bg-green-50 p-3 rounded-lg border border-green-200">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-medium text-green-700">
                              答案 #{index + 1}
                            </span>
                            <span className="text-xs font-semibold text-green-800">
                              关联度: {(answer.relevance_score ?? 0).toFixed(2)}
                            </span>
                          </div>
                          <div className="text-sm text-gray-700">
                            {answer.answer_text}
                          </div>
                          {answer.chunk_id && (
                            <div className="text-xs text-gray-500 mt-1">
                              分块ID: <span className="font-mono">{answer.chunk_id}</span>
                            </div>
                          )}
                          {answer.external_id && (
                            <div className="text-xs text-gray-500 mt-1">
                              External ID: <span className="font-mono">{answer.external_id}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* 生成结果详情 */}
                {selectedResult.generated_answer && (
                  <div>
                    <div className="mb-4 font-semibold text-base text-gray-900">
                      生成结果
                      {selectedResult.generation_time !== undefined && (
                        <span className="ml-2 text-sm font-normal text-gray-500">
                          (耗时: {selectedResult.generation_time.toFixed(3)}s)
                        </span>
                      )}
                    </div>
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <div className="text-sm text-gray-700 whitespace-pre-wrap break-words">
                        {selectedResult.generated_answer}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>
                关闭
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  // 对比视图
  if (viewMode === "compare") {
    const compareTaskIds = Array.from(selectedTaskIds)
    const compareTasks = tasks.filter(t => compareTaskIds.includes(t.id))
    
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">任务对比</h2>
            <p className="text-sm text-gray-500 mt-1">对比评估汇总指标</p>
          </div>
          <Button variant="outline" onClick={() => {
            setViewMode("list")
            setSelectedTaskIds(new Set())
            setCompareSummaries(new Map())
          }}>
            返回列表
          </Button>
        </div>

        {loadingCompare ? (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">加载对比数据中...</div>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* 任务信息对比表 */}
            <Card>
              <CardHeader>
                <CardTitle>任务信息</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2 font-medium">任务名称</th>
                        {compareTasks.map((task) => (
                          <th key={task.id} className="text-left p-2 font-medium border-l">
                            {task.task_name || "未命名任务"}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b">
                        <td className="p-2 text-sm text-gray-500">测试集ID</td>
                        {compareTasks.map((task) => (
                          <td key={task.id} className="p-2 border-l text-sm">
                            {task.test_set_id}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 text-sm text-gray-500">知识库ID</td>
                        {compareTasks.map((task) => (
                          <td key={task.id} className="p-2 border-l text-sm">
                            {task.kb_id}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 text-sm text-gray-500">评估类型</td>
                        {compareTasks.map((task) => (
                          <td key={task.id} className="p-2 border-l text-sm">
                            {task.evaluation_type === "retrieval" ? "检索器评估" : "生成器评估"}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 text-sm text-gray-500">总用例数</td>
                        {compareTasks.map((task) => (
                          <td key={task.id} className="p-2 border-l text-sm">
                            {task.total_cases}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="p-2 text-sm text-gray-500">创建时间</td>
                        {compareTasks.map((task) => (
                          <td key={task.id} className="p-2 border-l text-sm">
                            {new Date(task.created_at).toLocaleString()}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* 检索指标对比 */}
            {compareTasks.some(t => {
              const summary = compareSummaries.get(t.id)
              return summary?.overall_retrieval_metrics
            }) && (
              <Card>
                <CardHeader>
                  <CardTitle>检索指标对比</CardTitle>
                  <CardDescription>整体检索评估结果（颜色越深表示数值越大）</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-medium">指标</th>
                          {compareTasks.map((task) => (
                            <th key={task.id} className="text-left p-2 font-medium border-l">
                              {task.task_name || "未命名任务"}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          // 收集所有指标名称
                          const allMetrics = new Set<string>()
                          compareTasks.forEach(task => {
                            const summary = compareSummaries.get(task.id)
                            if (summary?.overall_retrieval_metrics) {
                              Object.keys(summary.overall_retrieval_metrics).forEach(key => allMetrics.add(key))
                            }
                          })
                          
                          // 构建指标数据映射
                          const metricsData: Record<string, Record<string, number>> = {}
                          compareTasks.forEach(task => {
                            const summary = compareSummaries.get(task.id)
                            if (summary?.overall_retrieval_metrics) {
                              metricsData[task.id] = summary.overall_retrieval_metrics
                            }
                          })
                          
                          return Array.from(allMetrics).map(metric => {
                            const range = getRowValueRange(metric, metricsData, compareTasks)
                            return (
                              <tr key={metric} className="border-b">
                                <td className="p-2 text-sm font-medium">{metric}</td>
                                {compareTasks.map((task) => {
                                  const summary = compareSummaries.get(task.id)
                                  const value = summary?.overall_retrieval_metrics?.[metric]
                                  const isNumber = value !== undefined && typeof value === 'number'
                                  const bgColor = isNumber ? getHeatmapColor(value, range.min, range.max) : ""
                                  
                                  return (
                                    <td 
                                      key={task.id} 
                                      className={`p-2 border-l text-sm ${bgColor} transition-colors`}
                                    >
                                      {isNumber ? (
                                        <span className="font-medium">{value.toFixed(4)}</span>
                                      ) : value !== undefined ? (
                                        String(value)
                                      ) : (
                                        <span className="text-gray-400">-</span>
                                      )}
                                    </td>
                                  )
                                })}
                              </tr>
                            )
                          })
                        })()}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* RAGAS检索指标对比 */}
            {compareTasks.some(t => {
              const summary = compareSummaries.get(t.id)
              return summary?.overall_ragas_retrieval_metrics
            }) && (
              <Card>
                <CardHeader>
                  <CardTitle>RAGAS检索指标对比</CardTitle>
                  <CardDescription>RAGAS检索评估结果（颜色越深表示数值越大）</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-medium">指标</th>
                          {compareTasks.map((task) => (
                            <th key={task.id} className="text-left p-2 font-medium border-l">
                              {task.task_name || "未命名任务"}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const allMetrics = new Set<string>()
                          compareTasks.forEach(task => {
                            const summary = compareSummaries.get(task.id)
                            if (summary?.overall_ragas_retrieval_metrics) {
                              Object.keys(summary.overall_ragas_retrieval_metrics).forEach(key => allMetrics.add(key))
                            }
                          })
                          
                          // 构建指标数据映射
                          const metricsData: Record<string, Record<string, number>> = {}
                          compareTasks.forEach(task => {
                            const summary = compareSummaries.get(task.id)
                            if (summary?.overall_ragas_retrieval_metrics) {
                              metricsData[task.id] = summary.overall_ragas_retrieval_metrics
                            }
                          })
                          
                          return Array.from(allMetrics).map(metric => {
                            const range = getRowValueRange(metric, metricsData, compareTasks)
                            return (
                              <tr key={metric} className="border-b">
                                <td className="p-2 text-sm font-medium">{metric}</td>
                                {compareTasks.map((task) => {
                                  const summary = compareSummaries.get(task.id)
                                  const value = summary?.overall_ragas_retrieval_metrics?.[metric]
                                  const isNumber = value !== undefined && typeof value === 'number'
                                  const bgColor = isNumber ? getHeatmapColor(value, range.min, range.max) : ""
                                  
                                  return (
                                    <td 
                                      key={task.id} 
                                      className={`p-2 border-l text-sm ${bgColor} transition-colors`}
                                    >
                                      {isNumber ? (
                                        <span className="font-medium">{value.toFixed(4)}</span>
                                      ) : value !== undefined ? (
                                        String(value)
                                      ) : (
                                        <span className="text-gray-400">-</span>
                                      )}
                                    </td>
                                  )
                                })}
                              </tr>
                            )
                          })
                        })()}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* RAGAS生成指标对比 */}
            {compareTasks.some(t => {
              const summary = compareSummaries.get(t.id)
              return summary?.overall_ragas_generation_metrics
            }) && (
              <Card>
                <CardHeader>
                  <CardTitle>RAGAS生成指标对比</CardTitle>
                  <CardDescription>RAGAS生成评估结果（颜色越深表示数值越大）</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-medium">指标</th>
                          {compareTasks.map((task) => (
                            <th key={task.id} className="text-left p-2 font-medium border-l">
                              {task.task_name || "未命名任务"}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const allMetrics = new Set<string>()
                          compareTasks.forEach(task => {
                            const summary = compareSummaries.get(task.id)
                            if (summary?.overall_ragas_generation_metrics) {
                              Object.keys(summary.overall_ragas_generation_metrics).forEach(key => allMetrics.add(key))
                            }
                          })
                          
                          // 构建指标数据映射
                          const metricsData: Record<string, Record<string, number>> = {}
                          compareTasks.forEach(task => {
                            const summary = compareSummaries.get(task.id)
                            if (summary?.overall_ragas_generation_metrics) {
                              metricsData[task.id] = summary.overall_ragas_generation_metrics
                            }
                          })
                          
                          return Array.from(allMetrics).map(metric => {
                            const range = getRowValueRange(metric, metricsData, compareTasks)
                            return (
                              <tr key={metric} className="border-b">
                                <td className="p-2 text-sm font-medium">{metric}</td>
                                {compareTasks.map((task) => {
                                  const summary = compareSummaries.get(task.id)
                                  const value = summary?.overall_ragas_generation_metrics?.[metric]
                                  const isNumber = value !== undefined && typeof value === 'number'
                                  const bgColor = isNumber ? getHeatmapColor(value, range.min, range.max) : ""
                                  
                                  return (
                                    <td 
                                      key={task.id} 
                                      className={`p-2 border-l text-sm ${bgColor} transition-colors`}
                                    >
                                      {isNumber ? (
                                        <span className="font-medium">{value.toFixed(4)}</span>
                                      ) : value !== undefined ? (
                                        String(value)
                                      ) : (
                                        <span className="text-gray-400">-</span>
                                      )}
                                    </td>
                                  )
                                })}
                              </tr>
                            )
                          })
                        })()}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* 总体RAGAS分数对比 */}
            {compareTasks.some(t => {
              const summary = compareSummaries.get(t.id)
              return summary?.overall_ragas_score !== undefined
            }) && (
              <Card>
                <CardHeader>
                  <CardTitle>总体RAGAS分数对比</CardTitle>
                  <CardDescription>整体RAGAS评估分数（颜色越深表示数值越大）</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2 font-medium">任务名称</th>
                          {compareTasks.map((task) => (
                            <th key={task.id} className="text-left p-2 font-medium border-l">
                              {task.task_name || "未命名任务"}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          // 计算分数范围
                          const scores = compareTasks
                            .map(task => {
                              const summary = compareSummaries.get(task.id)
                              return summary?.overall_ragas_score
                            })
                            .filter((score): score is number => score !== undefined)
                          
                          const minScore = scores.length > 0 ? Math.min(...scores) : 0
                          const maxScore = scores.length > 0 ? Math.max(...scores) : 1
                          
                          return (
                            <tr>
                              <td className="p-2 text-sm font-medium">总体RAGAS分数</td>
                              {compareTasks.map((task) => {
                                const summary = compareSummaries.get(task.id)
                                const score = summary?.overall_ragas_score
                                const bgColor = score !== undefined ? getHeatmapColor(score, minScore, maxScore) : ""
                                
                                return (
                                  <td key={task.id} className={`p-2 border-l ${bgColor} transition-colors`}>
                                    {score !== undefined ? (
                                      <div className="text-lg font-bold text-purple-700">
                                        {score.toFixed(4)}
                                      </div>
                                    ) : (
                                      <span className="text-gray-400">-</span>
                                    )}
                                  </td>
                                )
                              })}
                            </tr>
                          )
                        })()}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {compareTasks.every(t => {
              const summary = compareSummaries.get(t.id)
              return !summary || (
                !summary.overall_retrieval_metrics &&
                !summary.overall_ragas_retrieval_metrics &&
                !summary.overall_ragas_generation_metrics &&
                summary.overall_ragas_score === undefined
              )
            }) && (
              <Card>
                <CardContent className="py-12">
                  <div className="text-center text-gray-500">
                    选中的任务暂无评估汇总数据
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    )
  }

  // 列表视图
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">评估任务</h2>
          <p className="text-sm text-gray-500 mt-1">管理所有评估任务</p>
        </div>
        <div className="flex items-center gap-2">
          {selectedTaskIds.size > 0 && (
            <Button
              variant="outline"
              onClick={handleCompare}
              disabled={selectedTaskIds.size < 2}
            >
              <GitCompare className="h-4 w-4 mr-2" />
              对比 ({selectedTaskIds.size})
            </Button>
          )}
          <Button onClick={() => {
            resetCreateForm()
            setViewMode("create")
          }}>
            <Plus className="h-4 w-4 mr-2" />
            新建评估任务
          </Button>
        </div>
      </div>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Select value={selectedKbId || "all"} onValueChange={(value) => setSelectedKbId(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="选择知识库" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部知识库</SelectItem>
                {knowledgeBases.map((kb) => (
                  <SelectItem key={kb.id} value={kb.id}>
                    {kb.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedStatus || "all"} onValueChange={(value) => setSelectedStatus(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="running">运行中</SelectItem>
                <SelectItem value="completed">已完成</SelectItem>
                <SelectItem value="failed">失败异常</SelectItem>
                <SelectItem value="pending">待执行</SelectItem>
                <SelectItem value="archived">已归档</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 任务列表 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>任务列表</CardTitle>
              <CardDescription>共 {total} 个评估任务</CardDescription>
            </div>
            {tasks.filter(t => t.status === "completed").length > 0 && (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={(() => {
                    const completedTasks = tasks.filter(t => t.status === "completed")
                    return completedTasks.length > 0 && selectedTaskIds.size === completedTasks.length
                  })()}
                  onChange={toggleSelectAll}
                  className="w-4 h-4 cursor-pointer"
                />
                <span className="text-sm text-gray-600">全选已完成任务</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {loading && tasks.length === 0 ? (
            <div className="text-center py-8">加载中...</div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无评估任务</div>
          ) : (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className={`p-4 border rounded-lg hover:bg-gray-50 transition-colors ${
                    task.status === "archived" ? "opacity-60" : ""
                  } ${selectedTaskIds.has(task.id) ? "bg-blue-50 border-blue-300" : ""}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      {task.status === "completed" && (
                        <input
                          type="checkbox"
                          checked={selectedTaskIds.has(task.id)}
                          onChange={() => toggleTaskSelection(task.id)}
                          className="mt-1 w-4 h-4 cursor-pointer"
                        />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-lg">{task.task_name || "未命名任务"}</h3>
                        <span className="flex items-center gap-1">
                          {getStatusIcon(task.status)}
                          {getStatusText(task.status)}
                        </span>
                        {task.status === "archived" && (
                          <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-600">
                            已归档
                          </span>
                        )}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                          <span>测试集: {task.test_set_id}</span>
                          <span>知识库: {task.kb_id}</span>
                          <span>类型: {task.evaluation_type === "retrieval" ? "检索" : "生成"}</span>
                          <span>用例数: {task.total_cases}</span>
                          <span>创建时间: {new Date(task.created_at).toLocaleString()}</span>
                        </div>
                        {task.status === "running" && (
                          <div className="mt-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-gray-600">执行进度</span>
                              <span className="text-sm font-medium">
                                {task.completed_cases}/{task.total_cases} ({Math.round((task.completed_cases / task.total_cases) * 100)}%)
                              </span>
                            </div>
                            <Progress value={(task.completed_cases / task.total_cases) * 100} />
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedTask(task)
                          setViewMode("detail")
                        }}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        查看
                      </Button>
                      {task.status !== "archived" && task.status !== "running" && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleArchiveTask(task.id)}
                        >
                          <Archive className="h-4 w-4 mr-1" />
                          归档
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 分页 */}
          {total > pageSize && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-gray-500">
                第 {page} 页，共 {Math.ceil(total / pageSize)} 页
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  上一页
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= Math.ceil(total / pageSize)}
                  onClick={() => setPage(page + 1)}
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

