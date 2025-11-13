"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
import { testAPI, knowledgeBaseAPI, KnowledgeBase } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { Plus, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react"

interface ImportHistoryItem {
  id: string
  test_set_id: string
  kb_id: string
  imported_at: string
  import_config: Record<string, any>
  kb_deleted: boolean
  test_set_deleted: boolean
  import_task?: {
    id: string
    status: string
    progress: number
    total_docs: number
    imported_docs: number
    failed_docs: number
  }
}

interface TestSetImportHistoryViewProps {
  testSetId: string
}

export default function TestSetImportHistoryView({ testSetId }: TestSetImportHistoryViewProps) {
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<ImportHistoryItem[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 导入对话框状态
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false)
  const [selectedKbId, setSelectedKbId] = useState<string>("")
  const [updateExisting, setUpdateExisting] = useState(true)
  const [previewData, setPreviewData] = useState<any>(null)
  const [importTaskId, setImportTaskId] = useState<string | null>(null)
  const [importProgress, setImportProgress] = useState(0)

  // 加载导入历史
  useEffect(() => {
    loadHistory()
  }, [testSetId, page])

  // 轮询导入进度
  useEffect(() => {
    if (importTaskId) {
      const interval = setInterval(() => {
        checkImportProgress()
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [importTaskId])

  const loadHistory = async () => {
    try {
      setLoading(true)
      const result = await testAPI.getTestSetImportHistory(testSetId, page, pageSize)
      setHistory(result.data)
      setTotal(result.total)
    } catch (error) {
      console.error("加载导入历史失败:", error)
      showToast("加载导入历史失败", "error")
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
      showToast("加载知识库失败", "error")
    }
  }

  const handlePreview = async () => {
    if (!selectedKbId) {
      showToast("请选择知识库", "error")
      return
    }

    try {
      setLoading(true)
      const result = await testAPI.previewTestSetImport(testSetId, selectedKbId)
      setPreviewData(result.data)
      setPreviewDialogOpen(true)
    } catch (error) {
      console.error("预览导入失败:", error)
      showToast("预览导入失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async () => {
    if (!selectedKbId) {
      showToast("请选择知识库", "error")
      return
    }

    try {
      setLoading(true)
      const result = await testAPI.importTestSetToKnowledgeBase(testSetId, {
        kb_id: selectedKbId,
        update_existing: updateExisting,
      })
      setImportTaskId(result.data.id)
      setImportDialogOpen(false)
      setPreviewDialogOpen(false)
      showToast("导入任务已创建", "success")
      loadHistory()
    } catch (error) {
      console.error("创建导入任务失败:", error)
      showToast("创建导入任务失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const checkImportProgress = async () => {
    if (!importTaskId) return

    try {
      const result = await testAPI.getImportTask(importTaskId)
      setImportProgress(result.data.progress)
      
      if (result.data.status === "completed" || result.data.status === "failed") {
        setImportTaskId(null)
        loadHistory()
        if (result.data.status === "completed") {
          showToast("导入完成", "success")
        } else {
          showToast("导入失败: " + (result.data.error_message || "未知错误"), "error")
        }
      }
    } catch (error) {
      console.error("查询导入进度失败:", error)
    }
  }

  const getKbName = (kbId: string) => {
    const kb = knowledgeBases.find(k => k.id === kbId)
    return kb ? kb.name : kbId
  }

  const getStatusIcon = (status?: string) => {
    if (!status) return null
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />
      case "failed":
        return <XCircle className="h-4 w-4 text-red-600" />
      case "running":
        return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
      case "pending":
        return <Clock className="h-4 w-4 text-gray-600" />
      default:
        return null
    }
  }

  const getStatusText = (status?: string) => {
    if (!status) return "未知"
    switch (status) {
      case "completed":
        return "已完成"
      case "failed":
        return "失败"
      case "running":
        return "进行中"
      case "pending":
        return "等待中"
      default:
        return status
    }
  }

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">导入历史</h3>
          <p className="text-sm text-gray-500 mt-1">查看该测试集导入到各个知识库的记录</p>
        </div>
        <Button onClick={() => setImportDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          导入到知识库
        </Button>
      </div>

      {loading && history.length === 0 ? (
        <div className="text-center py-8">加载中...</div>
      ) : history.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-500">
            暂无导入记录，点击"导入到知识库"开始导入
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {history.map((item) => (
            <Card key={item.id}>
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">{getKbName(item.kb_id)}</h4>
                      {item.kb_deleted && (
                        <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-700">
                          知识库已删除
                        </span>
                      )}
                      {item.test_set_deleted && (
                        <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-700">
                          测试集已删除
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>导入时间: {new Date(item.imported_at).toLocaleString()}</span>
                      {item.import_task && (
                        <>
                          <span className="flex items-center gap-1">
                            {getStatusIcon(item.import_task.status)}
                            {getStatusText(item.import_task.status)}
                          </span>
                          {item.import_task.status === "running" && (
                            <span>进度: {Math.round(item.import_task.progress * 100)}%</span>
                          )}
                        </>
                      )}
                    </div>
                    {item.import_task && (
                      <div className="mt-3">
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                          <span>总文档: {item.import_task.total_docs}</span>
                          <span>已导入: {item.import_task.imported_docs}</span>
                          {item.import_task.failed_docs > 0 && (
                            <span className="text-red-600">失败: {item.import_task.failed_docs}</span>
                          )}
                        </div>
                        {item.import_task.status === "running" && (
                          <Progress value={item.import_task.progress * 100} className="h-2" />
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex items-center justify-between">
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

      {/* 导入对话框 */}
      <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>导入到知识库</DialogTitle>
            <DialogDescription>将测试集导入到目标知识库</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">选择知识库 *</label>
              <Select value={selectedKbId} onValueChange={setSelectedKbId}>
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
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="update-existing"
                checked={updateExisting}
                onChange={(e) => setUpdateExisting(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="update-existing" className="text-sm">
                更新已存在的文档
              </label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setImportDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handlePreview} disabled={!selectedKbId || loading}>
              预览
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 预览对话框 */}
      <Dialog open={previewDialogOpen} onOpenChange={setPreviewDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>导入预览</DialogTitle>
            <DialogDescription>预览导入结果</DialogDescription>
          </DialogHeader>
          {previewData && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-500">总答案数</div>
                  <div className="text-2xl font-bold">{previewData.total_answers}</div>
                </div>
                <div className="p-3 bg-blue-50 rounded">
                  <div className="text-sm text-blue-600">将新增文档</div>
                  <div className="text-2xl font-bold text-blue-700">{previewData.new_docs}</div>
                </div>
                <div className="p-3 bg-yellow-50 rounded">
                  <div className="text-sm text-yellow-600">已存在文档</div>
                  <div className="text-2xl font-bold text-yellow-700">{previewData.existing_docs}</div>
                </div>
                <div className="p-3 bg-gray-50 rounded">
                  <div className="text-sm text-gray-500">将跳过文档</div>
                  <div className="text-2xl font-bold">{previewData.skipped_docs}</div>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setPreviewDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleImport} disabled={loading}>
              {loading ? "导入中..." : "确认导入"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 导入进度提示 */}
      {importTaskId && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
              <div className="flex-1">
                <div className="text-sm font-medium text-blue-900">导入进行中...</div>
                <Progress value={importProgress * 100} className="h-2 mt-2" />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

