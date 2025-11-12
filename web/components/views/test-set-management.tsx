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
import { testAPI, knowledgeBaseAPI, TestSet, KnowledgeBase } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function TestSetManagementView() {
  const [loading, setLoading] = useState(false)
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [selectedKbId, setSelectedKbId] = useState<string>("")
  const [testType, setTestType] = useState<string>("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 对话框状态
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedTestSet, setSelectedTestSet] = useState<TestSet | null>(null)
  
  // 表单数据
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    kb_id: "",
    test_type: "retrieval" as "retrieval" | "generation",
  })

  // 加载知识库列表
  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  // 加载测试集列表
  useEffect(() => {
    loadTestSets()
  }, [selectedKbId, testType, page])

  const loadKnowledgeBases = async () => {
    try {
      const result = await knowledgeBaseAPI.list(1, 100)
      setKnowledgeBases(result.data)
    } catch (error) {
      console.error("加载知识库失败:", error)
      showToast("加载知识库失败", "error")
    }
  }

  const loadTestSets = async () => {
    try {
      setLoading(true)
      const result = await testAPI.listTestSets(
        selectedKbId && selectedKbId !== "all" ? selectedKbId : undefined,
        testType && testType !== "all" ? testType : undefined,
        page,
        pageSize
      )
      setTestSets(result.data)
      setTotal(result.total)
    } catch (error) {
      console.error("加载测试集失败:", error)
      showToast("加载测试集失败", "error")
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formData.name || !formData.kb_id) {
      showToast("请填写必填字段", "error")
      return
    }

    try {
      setLoading(true)
      await testAPI.createTestSet(formData)
      showToast("测试集创建成功", "success")
      setCreateDialogOpen(false)
      setFormData({ name: "", description: "", kb_id: "", test_type: "retrieval" })
      loadTestSets()
    } catch (error) {
      console.error("创建测试集失败:", error)
      showToast("创建测试集失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedTestSet || !formData.name) {
      showToast("请填写必填字段", "error")
      return
    }

    try {
      setLoading(true)
      await testAPI.updateTestSet(selectedTestSet.id, {
        name: formData.name,
        description: formData.description,
      })
      showToast("测试集更新成功", "success")
      setEditDialogOpen(false)
      setSelectedTestSet(null)
      loadTestSets()
    } catch (error) {
      console.error("更新测试集失败:", error)
      showToast("更新测试集失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!selectedTestSet) return

    try {
      setLoading(true)
      await testAPI.deleteTestSet(selectedTestSet.id)
      showToast("测试集删除成功", "success")
      setDeleteDialogOpen(false)
      setSelectedTestSet(null)
      loadTestSets()
    } catch (error) {
      console.error("删除测试集失败:", error)
      showToast("删除测试集失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const openEditDialog = (testSet: TestSet) => {
    setSelectedTestSet(testSet)
    setFormData({
      name: testSet.name,
      description: testSet.description || "",
      kb_id: testSet.kb_id,
      test_type: testSet.test_type,
    })
    setEditDialogOpen(true)
  }

  const openDeleteDialog = (testSet: TestSet) => {
    setSelectedTestSet(testSet)
    setDeleteDialogOpen(true)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">测试集管理</h2>
        <p className="text-sm text-gray-500 mt-1">
          管理测试集，支持检索和生成两种类型的测试
        </p>
      </div>

      {/* 筛选和操作栏 */}
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

            <Select value={testType || "all"} onValueChange={(value) => setTestType(value === "all" ? "" : value)}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="测试类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="retrieval">检索测试</SelectItem>
                <SelectItem value="generation">生成测试</SelectItem>
              </SelectContent>
            </Select>

            <Button onClick={() => setCreateDialogOpen(true)}>创建测试集</Button>
          </div>
        </CardContent>
      </Card>

      {/* 测试集列表 */}
      <Card>
        <CardHeader>
          <CardTitle>测试集列表</CardTitle>
          <CardDescription>共 {total} 个测试集</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">加载中...</div>
          ) : testSets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">暂无测试集</div>
          ) : (
            <div className="space-y-4">
              {testSets.map((testSet) => (
                <div
                  key={testSet.id}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">{testSet.name}</h3>
                        <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">
                          {testSet.test_type === "retrieval" ? "检索" : "生成"}
                        </span>
                      </div>
                      {testSet.description && (
                        <p className="text-sm text-gray-600 mt-1">{testSet.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span>知识库: {testSet.kb_id}</span>
                        <span>测试用例: {testSet.case_count}</span>
                        <span>创建时间: {new Date(testSet.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(testSet)}
                      >
                        编辑
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDeleteDialog(testSet)}
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

      {/* 创建对话框 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建测试集</DialogTitle>
            <DialogDescription>创建一个新的测试集</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">测试集名称 *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="例如: t2ranking_seed42_1000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">描述</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="测试集描述"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">知识库 *</label>
              <Select
                value={formData.kb_id}
                onValueChange={(value) => setFormData({ ...formData, kb_id: value })}
              >
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
            <div>
              <label className="block text-sm font-medium mb-2">测试类型 *</label>
              <Select
                value={formData.test_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, test_type: value as "retrieval" | "generation" })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="retrieval">检索测试</SelectItem>
                  <SelectItem value="generation">生成测试</SelectItem>
                </SelectContent>
              </Select>
            </div>
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>编辑测试集</DialogTitle>
            <DialogDescription>修改测试集信息</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">测试集名称 *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">描述</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
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
              确定要删除测试集 "{selectedTestSet?.name}" 吗？此操作将同时删除该测试集下的所有测试用例。
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

