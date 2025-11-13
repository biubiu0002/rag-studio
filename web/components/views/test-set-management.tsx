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
import { testAPI, TestSet } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { ArrowLeft, Plus, Edit, Trash2 } from "lucide-react"
import RetrieverTestCaseManagementView from "./retriever-test-case-management"
import GenerationTestCaseManagementView from "./generation-test-case-management"
import TestSetImportHistoryView from "./test-set-import-history"

type ViewMode = "list" | "detail"
type DetailTab = "retriever-cases" | "generation-cases" | "import-history"

export default function TestSetManagementView() {
  const [loading, setLoading] = useState(false)
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [testType, setTestType] = useState<string>("")
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 视图状态
  const [viewMode, setViewMode] = useState<ViewMode>("list")
  const [selectedTestSet, setSelectedTestSet] = useState<TestSet | null>(null)
  const [activeTab, setActiveTab] = useState<DetailTab>("retriever-cases")
  
  // 对话框状态
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  
  // 表单数据
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    test_type: "retrieval" as "retrieval" | "generation",
  })

  // 加载测试集列表
  useEffect(() => {
    if (viewMode === "list") {
      loadTestSets()
    }
  }, [testType, page, viewMode])

  const loadTestSets = async () => {
    try {
      setLoading(true)
      const result = await testAPI.listTestSets(
        undefined, // 不再按知识库筛选
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
    if (!formData.name) {
      showToast("请填写测试集名称", "error")
      return
    }

    try {
      setLoading(true)
      await testAPI.createTestSet({
        name: formData.name,
        description: formData.description,
        test_type: formData.test_type,
      })
      showToast("测试集创建成功", "success")
      setCreateDialogOpen(false)
      setFormData({ name: "", description: "", test_type: "retrieval" })
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
      showToast("请填写测试集名称", "error")
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
      const errorMessage = (error as Error).message
      if (errorMessage.includes("已导入到知识库")) {
        showToast("删除失败: " + errorMessage, "error")
      } else {
        showToast("删除测试集失败: " + errorMessage, "error")
      }
    } finally {
      setLoading(false)
    }
  }

  const openEditDialog = (testSet: TestSet) => {
    setSelectedTestSet(testSet)
    setFormData({
      name: testSet.name,
      description: testSet.description || "",
      test_type: testSet.test_type,
    })
    setEditDialogOpen(true)
  }

  const openDeleteDialog = (testSet: TestSet) => {
    setSelectedTestSet(testSet)
    setDeleteDialogOpen(true)
  }

  const handleTestSetClick = (testSet: TestSet) => {
    setSelectedTestSet(testSet)
    setViewMode("detail")
    // 根据测试类型设置默认tab
    if (testSet.test_type === "retrieval") {
      setActiveTab("retriever-cases")
    } else {
      setActiveTab("generation-cases")
    }
  }

  const handleBackToList = () => {
    setViewMode("list")
    setSelectedTestSet(null)
    setActiveTab("retriever-cases")
  }

  // 详情视图
  if (viewMode === "detail" && selectedTestSet) {
    return (
      <div className="flex h-full gap-6">
        {/* 左侧Sidebar */}
        <div className="w-48 border-r bg-white p-4">
          <div className="mb-4">
            <Button
              variant="ghost"
              onClick={handleBackToList}
              className="w-full justify-start"
            >
              <ArrowLeft size={16} className="mr-2" />
              返回列表
            </Button>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900 mb-2">管理项</h3>
            {selectedTestSet.test_type === "retrieval" && (
              <button
                onClick={() => setActiveTab("retriever-cases")}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors border-l-2 ${
                  activeTab === "retriever-cases"
                    ? "bg-blue-50 text-blue-700 border-l-blue-600"
                    : "text-gray-700 border-l-transparent hover:bg-gray-50"
                }`}
              >
                检索器用例
              </button>
            )}
            {selectedTestSet.test_type === "generation" && (
              <button
                onClick={() => setActiveTab("generation-cases")}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors border-l-2 ${
                  activeTab === "generation-cases"
                    ? "bg-blue-50 text-blue-700 border-l-blue-600"
                    : "text-gray-700 border-l-transparent hover:bg-gray-50"
                }`}
              >
                生成用例
              </button>
            )}
            <button
              onClick={() => setActiveTab("import-history")}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors border-l-2 ${
                activeTab === "import-history"
                  ? "bg-blue-50 text-blue-700 border-l-blue-600"
                  : "text-gray-700 border-l-transparent hover:bg-gray-50"
              }`}
            >
              导入历史
            </button>
          </div>
        </div>

        {/* 右侧内容区域 */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="space-y-6">
            {/* 测试集基本信息 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{selectedTestSet.name}</h2>
              {selectedTestSet.description && (
                <p className="text-gray-600 mt-1">{selectedTestSet.description}</p>
              )}
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                <span className="px-2 py-1 rounded bg-blue-100 text-blue-700">
                  {selectedTestSet.test_type === "retrieval" ? "检索测试" : "生成测试"}
                </span>
                <span>用例数量: {selectedTestSet.case_count}</span>
                <span>创建时间: {new Date(selectedTestSet.created_at).toLocaleString()}</span>
              </div>
            </div>

            {/* 根据选中的tab显示对应内容 */}
            {activeTab === "retriever-cases" && selectedTestSet.test_type === "retrieval" && (
              <RetrieverTestCaseManagementView testSetId={selectedTestSet.id} />
            )}
            {activeTab === "generation-cases" && selectedTestSet.test_type === "generation" && (
              <GenerationTestCaseManagementView testSetId={selectedTestSet.id} />
            )}
            {activeTab === "import-history" && (
              <TestSetImportHistoryView testSetId={selectedTestSet.id} />
            )}
          </div>
        </div>
      </div>
    )
  }

  // 列表视图
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">测试集</h2>
        <p className="text-sm text-gray-500 mt-1">
          管理测试集，支持检索和生成两种类型的测试
        </p>
      </div>

      {/* 筛选和操作栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
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

            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              新建测试集
            </Button>
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
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => handleTestSetClick(testSet)}
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
                        <span>用例数量: {testSet.case_count}</span>
                        <span>创建时间: {new Date(testSet.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(testSet)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDeleteDialog(testSet)}
                      >
                        <Trash2 className="h-4 w-4" />
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
