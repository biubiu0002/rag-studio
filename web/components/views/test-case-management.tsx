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
import { testAPI, TestSet, TestCase } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function TestCaseManagementView() {
  const [loading, setLoading] = useState(false)
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [selectedTestSetId, setSelectedTestSetId] = useState<string>("")
  const [testCases, setTestCases] = useState<TestCase[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 对话框状态
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null)
  
  // 表单数据
  const [formData, setFormData] = useState({
    query: "",
    expected_chunks: [] as string[],
    expected_answer: "",
    metadata: {} as Record<string, any>,
  })

  // 临时输入（用于expected_chunks）
  const [chunksInput, setChunksInput] = useState("")

  // 加载测试集列表
  useEffect(() => {
    loadTestSets()
  }, [])

  // 加载测试用例列表
  useEffect(() => {
    if (selectedTestSetId) {
      loadTestCases()
    }
  }, [selectedTestSetId, page])

  const loadTestSets = async () => {
    try {
      const result = await testAPI.listTestSets(undefined, undefined, 1, 100)
      setTestSets(result.data)
    } catch (error) {
      console.error("加载测试集失败:", error)
      showToast("加载测试集失败", "error")
    }
  }

  const loadTestCases = async () => {
    if (!selectedTestSetId) return

    try {
      setLoading(true)
      const result = await testAPI.listTestCases(selectedTestSetId, page, pageSize)
      setTestCases(result.data)
      setTotal(result.total)
    } catch (error) {
      console.error("加载测试用例失败:", error)
      showToast("加载测试用例失败", "error")
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!selectedTestSetId || !formData.query) {
      showToast("请填写必填字段", "error")
      return
    }

    try {
      setLoading(true)
      await testAPI.createTestCase({
        test_set_id: selectedTestSetId,
        query: formData.query,
        expected_chunks: formData.expected_chunks.length > 0 ? formData.expected_chunks : undefined,
        expected_answer: formData.expected_answer || undefined,
        metadata: Object.keys(formData.metadata).length > 0 ? formData.metadata : undefined,
      })
      showToast("测试用例创建成功", "success")
      setCreateDialogOpen(false)
      setFormData({ query: "", expected_chunks: [], expected_answer: "", metadata: {} })
      setChunksInput("")
      loadTestCases()
    } catch (error) {
      console.error("创建测试用例失败:", error)
      showToast("创建测试用例失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedTestCase || !formData.query) {
      showToast("请填写必填字段", "error")
      return
    }

    try {
      setLoading(true)
      await testAPI.updateTestCase(selectedTestCase.id, {
        query: formData.query,
        expected_chunks: formData.expected_chunks.length > 0 ? formData.expected_chunks : undefined,
        expected_answer: formData.expected_answer || undefined,
        metadata: Object.keys(formData.metadata).length > 0 ? formData.metadata : undefined,
      })
      showToast("测试用例更新成功", "success")
      setEditDialogOpen(false)
      setSelectedTestCase(null)
      loadTestCases()
    } catch (error) {
      console.error("更新测试用例失败:", error)
      showToast("更新测试用例失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedTestCase) return

    try {
      setLoading(true)
      await testAPI.deleteTestCase(selectedTestCase.id)
      showToast("测试用例删除成功", "success")
      setDeleteDialogOpen(false)
      setSelectedTestCase(null)
      loadTestCases()
    } catch (error) {
      console.error("删除测试用例失败:", error)
      showToast("删除测试用例失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const openEditDialog = (testCase: TestCase) => {
    setSelectedTestCase(testCase)
    setFormData({
      query: testCase.query,
      expected_chunks: testCase.expected_chunks || [],
      expected_answer: testCase.expected_answer || "",
      metadata: testCase.metadata || {},
    })
    setChunksInput((testCase.expected_chunks || []).join(", "))
    setEditDialogOpen(true)
  }

  const openDeleteDialog = (testCase: TestCase) => {
    setSelectedTestCase(testCase)
    setDeleteDialogOpen(true)
  }

  const handleChunksInputChange = (value: string) => {
    setChunksInput(value)
    const chunks = value
      .split(",")
      .map((c) => c.trim())
      .filter((c) => c.length > 0)
    setFormData({ ...formData, expected_chunks: chunks })
  }

  const selectedTestSet = testSets.find((ts) => ts.id === selectedTestSetId)

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">测试用例管理</h2>
        <p className="text-sm text-gray-500 mt-1">
          管理测试用例，支持手动创建和编辑
        </p>
      </div>

      {/* 测试集选择 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-2">选择测试集 *</label>
              <Select value={selectedTestSetId} onValueChange={setSelectedTestSetId}>
                <SelectTrigger>
                  <SelectValue placeholder="选择测试集" />
                </SelectTrigger>
                <SelectContent>
                  {testSets.map((ts) => (
                    <SelectItem key={ts.id} value={ts.id}>
                      {ts.name} ({ts.test_type === "retrieval" ? "检索" : "生成"})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {selectedTestSetId && (
              <Button onClick={() => setCreateDialogOpen(true)}>创建测试用例</Button>
            )}
          </div>
          {selectedTestSet && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="text-sm">
                <div className="font-medium">测试集信息</div>
                <div className="text-gray-600 mt-1">
                  类型: {selectedTestSet.test_type === "retrieval" ? "检索测试" : "生成测试"} | 
                  测试用例数: {selectedTestSet.case_count} | 
                  知识库: {selectedTestSet.kb_id}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 测试用例列表 */}
      {selectedTestSetId && (
        <Card>
          <CardHeader>
            <CardTitle>测试用例列表</CardTitle>
            <CardDescription>共 {total} 个测试用例</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">加载中...</div>
            ) : testCases.length === 0 ? (
              <div className="text-center py-8 text-gray-500">暂无测试用例</div>
            ) : (
              <div className="space-y-4">
                {testCases.map((testCase) => (
                  <div
                    key={testCase.id}
                    className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-lg mb-2">{testCase.query}</div>
                        {testCase.expected_chunks && testCase.expected_chunks.length > 0 && (
                          <div className="text-sm text-gray-600 mb-1">
                            期望分块: {testCase.expected_chunks.join(", ")}
                          </div>
                        )}
                        {testCase.expected_answer && (
                          <div className="text-sm text-gray-600 mb-1">
                            期望答案: {testCase.expected_answer.substring(0, 100)}
                            {testCase.expected_answer.length > 100 ? "..." : ""}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-2">
                          创建时间: {new Date(testCase.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openEditDialog(testCase)}
                        >
                          编辑
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openDeleteDialog(testCase)}
                        >
                          删除
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
      )}

      {/* 创建对话框 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建测试用例</DialogTitle>
            <DialogDescription>创建一个新的测试用例</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">查询问题 *</label>
              <Input
                value={formData.query}
                onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                placeholder="输入测试查询问题"
              />
            </div>
            {selectedTestSet?.test_type === "retrieval" && (
              <div>
                <label className="block text-sm font-medium mb-2">
                  期望检索到的分块ID（逗号分隔）
                </label>
                <Input
                  value={chunksInput}
                  onChange={(e) => handleChunksInputChange(e.target.value)}
                  placeholder="例如: chunk_001, chunk_002"
                />
                <p className="text-xs text-gray-500 mt-1">
                  当前: {formData.expected_chunks.length} 个分块
                </p>
              </div>
            )}
            {selectedTestSet?.test_type === "generation" && (
              <div>
                <label className="block text-sm font-medium mb-2">期望答案</label>
                <textarea
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  value={formData.expected_answer}
                  onChange={(e) => setFormData({ ...formData, expected_answer: e.target.value })}
                  placeholder="输入期望的答案"
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleCreate} disabled={loading}>
              {loading ? "创建中..." : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑对话框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑测试用例</DialogTitle>
            <DialogDescription>修改测试用例信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">查询问题 *</label>
              <Input
                value={formData.query}
                onChange={(e) => setFormData({ ...formData, query: e.target.value })}
              />
            </div>
            {selectedTestSet?.test_type === "retrieval" && (
              <div>
                <label className="block text-sm font-medium mb-2">
                  期望检索到的分块ID（逗号分隔）
                </label>
                <Input
                  value={chunksInput}
                  onChange={(e) => handleChunksInputChange(e.target.value)}
                  placeholder="例如: chunk_001, chunk_002"
                />
              </div>
            )}
            {selectedTestSet?.test_type === "generation" && (
              <div>
                <label className="block text-sm font-medium mb-2">期望答案</label>
                <textarea
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  value={formData.expected_answer}
                  onChange={(e) => setFormData({ ...formData, expected_answer: e.target.value })}
                />
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleEdit} disabled={loading}>
              {loading ? "更新中..." : "更新"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              确定要删除这个测试用例吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={loading}>
              {loading ? "删除中..." : "删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

