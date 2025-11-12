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
import { retrieverEvalAPI, testAPI, knowledgeBaseAPI, evaluationAPI, TestSet, EvaluationTask, EvaluationSummary } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function RetrieverEvaluationView() {
  const [loading, setLoading] = useState(false)
  const [statistics, setStatistics] = useState<any>(null)
  const [evaluationResult, setEvaluationResult] = useState<any>(null)
  const [importResult, setImportResult] = useState<any>(null)
  
  // 新增：评估任务相关状态
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [selectedTestSetId, setSelectedTestSetId] = useState<string>("")
  const [currentTask, setCurrentTask] = useState<EvaluationTask | null>(null)
  const [summary, setSummary] = useState<EvaluationSummary | null>(null)
  const [configDialogOpen, setConfigDialogOpen] = useState(false)
  
  // 检索配置
  const [retrievalConfig, setRetrievalConfig] = useState({
    top_k: 10,
    score_threshold: 0.7,
    fusion: "rrf",
    rrf_k: 60,
    vector_weight: 0.7,
    keyword_weight: 0.3,
    embedding_model: "bge-m3:latest",
    sparse_vector_method: "bm25",
  })

  // T2Ranking数据集默认路径（可以改为配置项）
  const defaultPaths = {
    collection: "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/collection.tsv",
    queries: "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/queries.dev.tsv",
    qrels: "/Users/yeruijian/Documents/知识库平台/dataset/T2Ranking/data/qrels.dev.tsv",
  }

  // 加载测试集列表
  useEffect(() => {
    loadTestSets()
  }, [])

  // 轮询任务状态
  useEffect(() => {
    if (currentTask && currentTask.status === "running") {
      const interval = setInterval(() => {
        loadTaskStatus()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [currentTask])

  const loadTestSets = async () => {
    try {
      const result = await testAPI.listTestSets(undefined, "retrieval", 1, 100)
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
        evaluation_type: "retrieval",
        task_name: `检索器评估_${new Date().toLocaleString()}`,
        retrieval_config: retrievalConfig,
      })
      
      showToast("评估任务创建成功", "success")
      setConfigDialogOpen(false)
      
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

  // 获取数据集统计信息
  const handleGetStatistics = async () => {
    try {
      setLoading(true)
      const result = await retrieverEvalAPI.getDatasetStatistics(
        defaultPaths.collection,
        defaultPaths.queries,
        defaultPaths.qrels,
        100, // max_queries
        undefined // max_docs
      )
      setStatistics(result.data)
    } catch (error) {
      console.error("获取统计信息失败:", error)
      showToast("获取统计信息失败，请检查数据集路径", "error")
    } finally {
      setLoading(false)
    }
  }

  // 导入数据集
  const handleImportDataset = async () => {
    try {
      setLoading(true)
      setImportResult(null)
      
      const result = await retrieverEvalAPI.importT2Ranking({
        kb_id: "kb_demo", // 需要选择或创建知识库
        test_set_name: "T2Ranking测试集",
        collection_path: defaultPaths.collection,
        queries_path: defaultPaths.queries,
        qrels_path: defaultPaths.qrels,
        max_queries: 100,
        description: "用于检索器评估的T2Ranking数据集"
      })
      
      setImportResult(result.data)
      showToast(result.message || "数据集导入成功", "success")
    } catch (error) {
      console.error("导入数据集失败:", error)
      showToast("导入数据集失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">检索器评估</h2>
        <p className="text-sm text-gray-500 mt-1">
          基于T2Ranking数据集评估检索器性能
        </p>
      </div>

      {/* 数据集统计卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>T2Ranking数据集统计</CardTitle>
          <CardDescription>
            查看数据集的基本统计信息
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button 
            onClick={handleGetStatistics} 
            disabled={loading}
          >
            {loading ? "加载中..." : "获取数据集统计"}
          </Button>

          {statistics && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-700">
                  {statistics.total_documents.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">总文档数</div>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-700">
                  {statistics.total_queries}
                </div>
                <div className="text-sm text-gray-600">总查询数</div>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-700">
                  {statistics.avg_relevant_docs_per_query.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">平均相关文档数</div>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-700">
                  {statistics.queries_with_relevant_docs}
                </div>
                <div className="text-sm text-gray-600">有标注的查询数</div>
              </div>
              <div className="p-4 bg-pink-50 rounded-lg">
                <div className="text-2xl font-bold text-pink-700">
                  {statistics.max_relevant_docs}
                </div>
                <div className="text-sm text-gray-600">最大相关文档数</div>
              </div>
              <div className="p-4 bg-indigo-50 rounded-lg">
                <div className="text-2xl font-bold text-indigo-700">
                  {statistics.min_relevant_docs}
                </div>
                <div className="text-sm text-gray-600">最小相关文档数</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 数据集导入卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>导入T2Ranking数据集</CardTitle>
          <CardDescription>
            将数据集导入到知识库并创建测试集
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="text-sm text-gray-600">
              <p className="font-semibold mb-2">数据集路径配置：</p>
              <ul className="space-y-1 ml-4 list-disc">
                <li>文档集合: {defaultPaths.collection}</li>
                <li>查询集: {defaultPaths.queries}</li>
                <li>相关性标注: {defaultPaths.qrels}</li>
              </ul>
            </div>
            <Button 
              onClick={handleImportDataset} 
              disabled={loading}
              variant="outline"
              className="w-full"
            >
              {loading ? "导入中..." : "导入数据集到知识库"}
            </Button>

            {/* 导入结果显示 */}
            {importResult && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="font-semibold text-green-800 mb-3">✅ 导入完成</div>
                
                {/* 知识库信息 */}
                <div className="mb-3">
                  <div className="text-sm font-medium text-gray-700">知识库</div>
                  <div className="text-sm text-gray-600">ID: {importResult.kb_id}</div>
                </div>

                {/* 文档导入结果 */}
                <div className="mb-3">
                  <div className="text-sm font-medium text-gray-700">文档导入</div>
                  <div className="grid grid-cols-3 gap-2 mt-1">
                    <div className="text-center p-2 bg-white rounded">
                      <div className="text-lg font-bold text-blue-600">
                        {importResult.documents?.total || 0}
                      </div>
                      <div className="text-xs text-gray-500">总数</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded">
                      <div className="text-lg font-bold text-green-600">
                        {importResult.documents?.created || 0}
                      </div>
                      <div className="text-xs text-gray-500">成功</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded">
                      <div className="text-lg font-bold text-red-600">
                        {importResult.documents?.failed || 0}
                      </div>
                      <div className="text-xs text-gray-500">失败</div>
                    </div>
                  </div>
                </div>

                {/* 测试集信息 */}
                <div className="mb-3">
                  <div className="text-sm font-medium text-gray-700">测试集</div>
                  <div className="text-sm text-gray-600">
                    <div>名称: {importResult.test_set?.name}</div>
                    <div>ID: {importResult.test_set?.id}</div>
                    <div>测试用例: {importResult.test_set?.case_count || 0} 个</div>
                  </div>
                </div>

                {/* 测试用例导入结果 */}
                <div>
                  <div className="text-sm font-medium text-gray-700">测试用例导入</div>
                  <div className="grid grid-cols-3 gap-2 mt-1">
                    <div className="text-center p-2 bg-white rounded">
                      <div className="text-lg font-bold text-blue-600">
                        {importResult.test_cases?.total || 0}
                      </div>
                      <div className="text-xs text-gray-500">总数</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded">
                      <div className="text-lg font-bold text-green-600">
                        {importResult.test_cases?.created || 0}
                      </div>
                      <div className="text-xs text-gray-500">成功</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded">
                      <div className="text-lg font-bold text-red-600">
                        {importResult.test_cases?.failed || 0}
                      </div>
                      <div className="text-xs text-gray-500">失败</div>
                    </div>
                  </div>
                </div>

                {/* 下一步提示 */}
                <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
                  💡 下一步：文档向量化（功能开发中）
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 评估指标说明 */}
      <Card>
        <CardHeader>
          <CardTitle>评估指标说明</CardTitle>
          <CardDescription>
            系统支持的7个核心评估指标
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">Precision@K</div>
              <div className="text-xs text-gray-600">检索结果中相关文档的比例</div>
            </div>
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">Recall@K</div>
              <div className="text-xs text-gray-600">相关文档被检索到的比例</div>
            </div>
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">F1-Score</div>
              <div className="text-xs text-gray-600">精确率和召回率的调和平均</div>
            </div>
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">MRR</div>
              <div className="text-xs text-gray-600">第一个相关文档的排名倒数</div>
            </div>
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">MAP</div>
              <div className="text-xs text-gray-600">所有相关文档位置的平均精度</div>
            </div>
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">NDCG</div>
              <div className="text-xs text-gray-600">考虑排序位置的综合指标</div>
            </div>
            <div className="p-3 border rounded-lg">
              <div className="font-semibold text-sm mb-1">Hit Rate</div>
              <div className="text-xs text-gray-600">至少检索到一个相关文档的比例</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 评估任务管理 */}
      <Card>
        <CardHeader>
          <CardTitle>创建评估任务</CardTitle>
          <CardDescription>基于测试集创建检索器评估任务</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
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
          </div>
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
            
            {summary.overall_retrieval_metrics && (
              <div className="space-y-2 mb-4">
                <h3 className="font-semibold">基础检索指标</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(summary.overall_retrieval_metrics).map(([key, value]) => (
                    <div key={key} className="p-3 bg-gray-50 rounded">
                      <div className="text-xs text-gray-500">{key}</div>
                      <div className="text-lg font-semibold">{(value * 100).toFixed(2)}%</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {summary.overall_ragas_retrieval_metrics && (
              <div className="space-y-2">
                <h3 className="font-semibold">RAGAS检索指标</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(summary.overall_ragas_retrieval_metrics).map(([key, value]) => (
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
            <DialogTitle>创建检索器评估任务</DialogTitle>
            <DialogDescription>配置检索器评估参数</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Top K</label>
                <Input
                  type="number"
                  value={retrievalConfig.top_k}
                  onChange={(e) =>
                    setRetrievalConfig({ ...retrievalConfig, top_k: parseInt(e.target.value) || 10 })
                  }
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Score Threshold</label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={retrievalConfig.score_threshold}
                  onChange={(e) =>
                    setRetrievalConfig({ ...retrievalConfig, score_threshold: parseFloat(e.target.value) || 0.7 })
                  }
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Fusion方法</label>
              <Select
                value={retrievalConfig.fusion}
                onValueChange={(value) =>
                  setRetrievalConfig({ ...retrievalConfig, fusion: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="rrf">RRF</SelectItem>
                  <SelectItem value="dbsf">DBSF</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Embedding模型</label>
              <Input
                value={retrievalConfig.embedding_model}
                onChange={(e) =>
                  setRetrievalConfig({ ...retrievalConfig, embedding_model: e.target.value })
                }
                placeholder="例如: bge-m3:latest"
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

      {/* 快速开始指南 */}
      <Card>
        <CardHeader>
          <CardTitle>快速开始</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-600">
            <p className="font-semibold">使用步骤：</p>
            <ol className="list-decimal ml-4 space-y-1">
              <li>点击"获取数据集统计"查看T2Ranking数据集信息</li>
              <li>创建或选择一个知识库</li>
              <li>导入数据集到知识库（需要先配置向量化）</li>
              <li>创建测试集并添加测试用例</li>
              <li>执行检索器评估，查看评估指标</li>
            </ol>
            <p className="mt-4 text-xs text-gray-500">
              💡 提示：建议从100个查询开始测试，完整文档请参考后端 README_RETRIEVER_EVAL.md
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


