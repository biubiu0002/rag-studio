"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { evaluationAPI, testAPI, knowledgeBaseAPI, EvaluationTask, EvaluationSummary, EvaluationCaseResult } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function EvaluationHistoryView() {
  const [loading, setLoading] = useState(false)
  const [tasks, setTasks] = useState<EvaluationTask[]>([])
  const [selectedTask, setSelectedTask] = useState<EvaluationTask | null>(null)
  const [summary, setSummary] = useState<EvaluationSummary | null>(null)
  const [caseResults, setCaseResults] = useState<EvaluationCaseResult[]>([])
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedResult, setSelectedResult] = useState<EvaluationCaseResult | null>(null)
  
  // 筛选条件
  const [testSetId, setTestSetId] = useState<string>("")
  const [kbId, setKbId] = useState<string>("")
  const [status, setStatus] = useState<string>("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  const [testSets, setTestSets] = useState<any[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([])

  useEffect(() => {
    loadTestSets()
    loadKnowledgeBases()
    loadTasks()
  }, [testSetId, kbId, status, page])

  const loadTestSets = async () => {
    try {
      const result = await testAPI.listTestSets(undefined, undefined, 1, 100)
      setTestSets(result.data)
    } catch (error) {
      console.error("加载测试集失败:", error)
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

  const loadTasks = async () => {
    try {
      setLoading(true)
      const result = await evaluationAPI.listTasks(
        testSetId && testSetId !== "all" ? testSetId : undefined,
        kbId && kbId !== "all" ? kbId : undefined,
        status && status !== "all" ? status : undefined,
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

  const handleViewDetails = async (task: EvaluationTask) => {
    setSelectedTask(task)
    try {
      // 加载汇总
      const summaryResult = await evaluationAPI.getSummary(task.id)
      setSummary(summaryResult.data)
      
      // 加载用例结果
      const resultsResult = await evaluationAPI.listCaseResults(task.id, 1, 20)
      setCaseResults(resultsResult.data)
    } catch (error) {
      console.error("加载任务详情失败:", error)
    }
  }

  const handleViewCaseResult = async (resultId: string) => {
    if (!selectedTask) return
    
    try {
      const result = await evaluationAPI.getCaseResult(selectedTask.id, resultId)
      setSelectedResult(result.data)
      setDetailDialogOpen(true)
    } catch (error) {
      console.error("加载用例结果失败:", error)
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">评估历史</h2>
        <p className="text-sm text-gray-500 mt-1">
          查看历史评估任务和结果
        </p>
      </div>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Select value={testSetId || "all"} onValueChange={(value) => setTestSetId(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="测试集" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部测试集</SelectItem>
                {testSets.map((ts) => (
                  <SelectItem key={ts.id} value={ts.id}>
                    {ts.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={kbId || "all"} onValueChange={(value) => setKbId(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="知识库" />
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

            <Select value={status || "all"} onValueChange={(value) => setStatus(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="pending">待执行</SelectItem>
                <SelectItem value="running">执行中</SelectItem>
                <SelectItem value="completed">已完成</SelectItem>
                <SelectItem value="failed">失败</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 任务列表 */}
      <Card>
        <CardHeader>
          <CardTitle>评估任务列表</CardTitle>
          <CardDescription>共 {total} 个任务</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无评估任务</div>
          ) : (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">{task.task_name || task.id}</h3>
                        <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">
                          {task.evaluation_type === "retrieval" ? "检索" : "生成"}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded ${
                          task.status === "completed" ? "bg-green-100 text-green-700" :
                          task.status === "running" ? "bg-blue-100 text-blue-700" :
                          task.status === "failed" ? "bg-red-100 text-red-700" :
                          "bg-gray-100 text-gray-700"
                        }`}>
                          {task.status === "completed" ? "已完成" :
                           task.status === "running" ? "执行中" :
                           task.status === "failed" ? "失败" : "待执行"}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span>测试集: {task.test_set_id}</span>
                        <span>知识库: {task.kb_id}</span>
                        <span>进度: {task.completed_cases} / {task.total_cases}</span>
                        <span>创建时间: {new Date(task.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleViewDetails(task)}
                      >
                        查看详情
                      </Button>
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

      {/* 任务详情对话框 */}
      {selectedTask && (
        <Dialog open={!!selectedTask} onOpenChange={() => setSelectedTask(null)}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>评估任务详情</DialogTitle>
              <DialogDescription>
                {selectedTask.task_name || selectedTask.id}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              {/* 任务信息 */}
              <div>
                <h3 className="font-semibold mb-2">任务信息</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>类型: {selectedTask.evaluation_type === "retrieval" ? "检索" : "生成"}</div>
                  <div>状态: {selectedTask.status}</div>
                  <div>总用例: {selectedTask.total_cases}</div>
                  <div>已完成: {selectedTask.completed_cases}</div>
                  <div>失败: {selectedTask.failed_cases}</div>
                  <div>创建时间: {new Date(selectedTask.created_at).toLocaleString()}</div>
                </div>
              </div>

              {/* 评估汇总 */}
              {summary && (
                <div>
                  <h3 className="font-semibold mb-2">评估汇总</h3>
                  {summary.overall_ragas_score !== undefined && (
                    <div className="mb-2 p-3 bg-blue-50 rounded">
                      <div className="text-sm text-gray-600">RAGAS综合评分</div>
                      <div className="text-2xl font-bold text-blue-700">
                        {(summary.overall_ragas_score * 100).toFixed(2)}%
                      </div>
                    </div>
                  )}
                  
                  {summary.overall_retrieval_metrics && (
                    <div className="mb-2">
                      <div className="text-sm font-medium mb-1">基础检索指标</div>
                      <div className="grid grid-cols-4 gap-2 text-sm">
                        {Object.entries(summary.overall_retrieval_metrics).map(([key, value]) => (
                          <div key={key} className="p-2 bg-gray-50 rounded">
                            <div className="text-xs text-gray-500">{key}</div>
                            <div className="font-semibold">{(value * 100).toFixed(2)}%</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {summary.overall_ragas_retrieval_metrics && (
                    <div className="mb-2">
                      <div className="text-sm font-medium mb-1">RAGAS检索指标</div>
                      <div className="grid grid-cols-4 gap-2 text-sm">
                        {Object.entries(summary.overall_ragas_retrieval_metrics).map(([key, value]) => (
                          <div key={key} className="p-2 bg-gray-50 rounded">
                            <div className="text-xs text-gray-500">{key}</div>
                            <div className="font-semibold">{(value * 100).toFixed(2)}%</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {summary.overall_ragas_generation_metrics && (
                    <div>
                      <div className="text-sm font-medium mb-1">RAGAS生成指标</div>
                      <div className="grid grid-cols-4 gap-2 text-sm">
                        {Object.entries(summary.overall_ragas_generation_metrics).map(([key, value]) => (
                          <div key={key} className="p-2 bg-gray-50 rounded">
                            <div className="text-xs text-gray-500">{key}</div>
                            <div className="font-semibold">{(value * 100).toFixed(2)}%</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* 用例结果列表 */}
              {caseResults.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">用例结果（前20条）</h3>
                  <div className="space-y-2 max-h-[300px] overflow-y-auto">
                    {caseResults.map((result) => (
                      <div
                        key={result.id}
                        className="p-2 border rounded hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleViewCaseResult(result.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="text-sm font-medium">{result.query.substring(0, 50)}...</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {result.ragas_score !== undefined && (
                                <span>RAGAS: {(result.ragas_score * 100).toFixed(2)}%</span>
                              )}
                              {result.status === "failed" && (
                                <span className="text-red-600 ml-2">失败</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* 用例结果详情对话框 */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>用例结果详情</DialogTitle>
            <DialogDescription>查看单个测试用例的详细评估结果</DialogDescription>
          </DialogHeader>
          
          {selectedResult && (
            <div className="space-y-4">
              <div>
                <div className="text-sm font-medium mb-1">查询</div>
                <div className="p-2 bg-gray-50 rounded">{selectedResult.query}</div>
              </div>

              {selectedResult.generated_answer && (
                <div>
                  <div className="text-sm font-medium mb-1">生成的答案</div>
                  <div className="p-2 bg-gray-50 rounded max-h-[200px] overflow-y-auto">
                    {selectedResult.generated_answer}
                  </div>
                </div>
              )}

              {selectedResult.retrieval_metrics && (
                <div>
                  <div className="text-sm font-medium mb-2">基础检索指标</div>
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(selectedResult.retrieval_metrics).map(([key, value]) => (
                      <div key={key} className="p-2 bg-gray-50 rounded text-sm">
                        <div className="text-xs text-gray-500">{key}</div>
                        <div className="font-semibold">{(value * 100).toFixed(2)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedResult.ragas_retrieval_metrics && (
                <div>
                  <div className="text-sm font-medium mb-2">RAGAS检索指标</div>
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(selectedResult.ragas_retrieval_metrics).map(([key, value]) => (
                      <div key={key} className="p-2 bg-gray-50 rounded text-sm">
                        <div className="text-xs text-gray-500">{key}</div>
                        <div className="font-semibold">{(value * 100).toFixed(2)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedResult.ragas_generation_metrics && (
                <div>
                  <div className="text-sm font-medium mb-2">RAGAS生成指标</div>
                  <div className="grid grid-cols-4 gap-2">
                    {Object.entries(selectedResult.ragas_generation_metrics).map(([key, value]) => (
                      <div key={key} className="p-2 bg-gray-50 rounded text-sm">
                        <div className="text-xs text-gray-500">{key}</div>
                        <div className="font-semibold">{(value * 100).toFixed(2)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedResult.ragas_score !== undefined && (
                <div className="p-3 bg-blue-50 rounded">
                  <div className="text-sm text-gray-600">RAGAS综合评分</div>
                  <div className="text-2xl font-bold text-blue-700">
                    {(selectedResult.ragas_score * 100).toFixed(2)}%
                  </div>
                </div>
              )}

              {selectedResult.error_message && (
                <div className="p-3 bg-red-50 rounded">
                  <div className="text-sm font-medium text-red-700">错误信息</div>
                  <div className="text-sm text-red-600 mt-1">{selectedResult.error_message}</div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

