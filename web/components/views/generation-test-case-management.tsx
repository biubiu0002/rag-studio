"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Label } from "@/components/ui/label"
import { generationTestCaseAPI, testAPI, GenerationTestCase, TestSet } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { Plus, Edit, Trash2, X } from "lucide-react"

export default function GenerationTestCaseManagementView() {
  const [loading, setLoading] = useState(false)
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [selectedTestSetId, setSelectedTestSetId] = useState<string>("")
  const [testCases, setTestCases] = useState<GenerationTestCase[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 对话框状态
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedTestCase, setSelectedTestCase] = useState<GenerationTestCase | null>(null)
  
  // 表单数据
  const [question, setQuestion] = useState("")
  const [answerText, setAnswerText] = useState("")
  const [groundTruth, setGroundTruth] = useState("")
  const [contexts, setContexts] = useState<string[]>([""])
  const [metadata, setMetadata] = useState("")

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
      const result = await testAPI.listTestSets(undefined, "generation", 1, 100)
      setTestSets(result.data)
      if (result.data.length > 0 && !selectedTestSetId) {
        setSelectedTestSetId(result.data[0].id)
      }
    } catch (error) {
      console.error("加载测试集失败:", error)
      showToast("加载测试集失败", "error")
    }
  }

  const loadTestCases = async () => {
    try {
      setLoading(true)
      const result = await generationTestCaseAPI.list(selectedTestSetId, page, pageSize)
      setTestCases(result.data)
      setTotal(result.total)
    } catch (error) {
      console.error("加载测试用例失败:", error)
      showToast("加载测试用例失败", "error")
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setQuestion("")
    setAnswerText("")
    setGroundTruth("")
    setContexts([""])
    setMetadata("")
  }

  const handleCreate = async () => {
    if (!question.trim() || !answerText.trim()) {
      showToast("请填写问题和参考答案", "error")
      return
    }

    try {
      setLoading(true)
      const metadataObj = metadata.trim() ? JSON.parse(metadata) : {}
      const validContexts = contexts.filter(c => c.trim())
      
      await generationTestCaseAPI.create({
        test_set_id: selectedTestSetId,
        question: question.trim(),
        reference_answer: {
          answer_text: answerText.trim(),
          ground_truth: groundTruth.trim() || undefined
        },
        contexts: validContexts.length > 0 ? validContexts : undefined,
        metadata: metadataObj
      })
      showToast("测试用例创建成功", "success")
      setCreateDialogOpen(false)
      resetForm()
      loadTestCases()
    } catch (error) {
      console.error("创建测试用例失败:", error)
      showToast("创建测试用例失败: " + (error as Error).message, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = async () => {
    if (!selectedTestCase || !question.trim() || !answerText.trim()) {
      showToast("请填写问题和参考答案", "error")
      return
    }

    try {
      setLoading(true)
      const metadataObj = metadata.trim() ? JSON.parse(metadata) : {}
      const validContexts = contexts.filter(c => c.trim())
      
      await generationTestCaseAPI.update(selectedTestCase.id, {
        question: question.trim(),
        reference_answer: {
          answer_text: answerText.trim(),
          ground_truth: groundTruth.trim() || undefined
        },
        contexts: validContexts.length > 0 ? validContexts : undefined,
        metadata: metadataObj
      })
      showToast("测试用例更新成功", "success")
      setEditDialogOpen(false)
      setSelectedTestCase(null)
      resetForm()
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
      await generationTestCaseAPI.delete(selectedTestCase.id)
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

  const openEditDialog = (testCase: GenerationTestCase) => {
    setSelectedTestCase(testCase)
    setQuestion(testCase.question)
    setAnswerText(testCase.reference_answer.answer_text)
    setGroundTruth(testCase.reference_answer.ground_truth || "")
    setContexts(testCase.contexts && testCase.contexts.length > 0 ? testCase.contexts : [""])
    setMetadata(JSON.stringify(testCase.metadata || {}, null, 2))
    setEditDialogOpen(true)
  }

  const openDeleteDialog = (testCase: GenerationTestCase) => {
    setSelectedTestCase(testCase)
    setDeleteDialogOpen(true)
  }

  const addContext = () => {
    setContexts([...contexts, ""])
  }

  const updateContext = (index: number, value: string) => {
    const newContexts = [...contexts]
    newContexts[index] = value
    setContexts(newContexts)
  }

  const removeContext = (index: number) => {
    if (contexts.length > 1) {
      setContexts(contexts.filter((_, i) => i !== index))
    }
  }

  const renderContextsForm = () => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>上下文列表（可选）</Label>
          <Button type="button" size="sm" variant="outline" onClick={addContext}>
            <Plus className="h-4 w-4 mr-1" />
            添加上下文
          </Button>
        </div>
        {contexts.map((context, index) => (
          <div key={index} className="flex gap-2">
            <div className="flex-1">
              <Textarea
                value={context}
                onChange={(e) => updateContext(index, e.target.value)}
                placeholder={`上下文 ${index + 1}`}
                rows={2}
              />
            </div>
            {contexts.length > 1 && (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => removeContext(index)}
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="h-full flex gap-6">
      {/* 左侧侧边栏 */}
      <div className="w-64 flex-shrink-0">
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="text-lg">测试集</CardTitle>
            <CardDescription>选择一个生成测试集</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {testSets.map((testSet) => (
                <Button
                  key={testSet.id}
                  variant={selectedTestSetId === testSet.id ? "default" : "outline"}
                  className="w-full justify-start"
                  onClick={() => setSelectedTestSetId(testSet.id)}
                >
                  <div className="text-left truncate">
                    <div className="font-medium">{testSet.name}</div>
                    <div className="text-xs opacity-70">{testSet.case_count} 条用例</div>
                  </div>
                </Button>
              ))}
              {testSets.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">
                  暂无测试集
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 右侧内容区域 */}
      <div className="flex-1">
        <Card className="h-full flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>生成测试用例（RAGAS）</CardTitle>
                <CardDescription>
                  管理问题、参考答案和上下文，用于RAGAS评估
                </CardDescription>
              </div>
              <Button onClick={() => {
                resetForm()
                setCreateDialogOpen(true)
              }}>
                <Plus className="h-4 w-4 mr-2" />
                新建用例
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-auto">
            {selectedTestSetId ? (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[35%]">问题</TableHead>
                      <TableHead className="w-[35%]">参考答案</TableHead>
                      <TableHead className="w-[15%]">上下文数</TableHead>
                      <TableHead className="w-[15%] text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {testCases.map((testCase) => (
                      <TableRow key={testCase.id}>
                        <TableCell className="font-medium">
                          <div className="line-clamp-2">{testCase.question}</div>
                        </TableCell>
                        <TableCell>
                          <div className="line-clamp-2">{testCase.reference_answer.answer_text}</div>
                        </TableCell>
                        <TableCell>{testCase.contexts?.length || 0}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openEditDialog(testCase)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openDeleteDialog(testCase)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                
                {testCases.length === 0 && !loading && (
                  <div className="text-center py-12 text-gray-500">
                    暂无测试用例，点击"新建用例"开始创建
                  </div>
                )}
                
                {/* 分页 */}
                {total > pageSize && (
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-gray-500">
                      共 {total} 条，每页 {pageSize} 条
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}
                      >
                        上一页
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={page * pageSize >= total}
                        onClick={() => setPage(p => p + 1)}
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-12 text-gray-500">
                请先选择一个测试集
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 创建对话框 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>创建生成测试用例</DialogTitle>
            <DialogDescription>
              填写问题、参考答案和上下文，用于RAGAS评估
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="question">问题 *</Label>
              <Textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="输入测试问题"
                rows={3}
              />
            </div>
            
            <div>
              <Label htmlFor="answer">参考答案文本 *</Label>
              <Textarea
                id="answer"
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="输入参考答案"
                rows={4}
              />
            </div>
            
            <div>
              <Label htmlFor="ground-truth">Ground Truth（可选）</Label>
              <Textarea
                id="ground-truth"
                value={groundTruth}
                onChange={(e) => setGroundTruth(e.target.value)}
                placeholder="输入标准答案"
                rows={3}
              />
            </div>
            
            {renderContextsForm()}
            
            <div>
              <Label htmlFor="metadata">元数据（JSON格式，可选）</Label>
              <Textarea
                id="metadata"
                value={metadata}
                onChange={(e) => setMetadata(e.target.value)}
                placeholder='{"key": "value"}'
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setCreateDialogOpen(false)
              resetForm()
            }}>
              取消
            </Button>
            <Button onClick={handleCreate} disabled={loading}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 编辑对话框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>编辑生成测试用例</DialogTitle>
            <DialogDescription>
              修改问题、参考答案和上下文
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="edit-question">问题 *</Label>
              <Textarea
                id="edit-question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="输入测试问题"
                rows={3}
              />
            </div>
            
            <div>
              <Label htmlFor="edit-answer">参考答案文本 *</Label>
              <Textarea
                id="edit-answer"
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="输入参考答案"
                rows={4}
              />
            </div>
            
            <div>
              <Label htmlFor="edit-ground-truth">Ground Truth（可选）</Label>
              <Textarea
                id="edit-ground-truth"
                value={groundTruth}
                onChange={(e) => setGroundTruth(e.target.value)}
                placeholder="输入标准答案"
                rows={3}
              />
            </div>
            
            {renderContextsForm()}
            
            <div>
              <Label htmlFor="edit-metadata">元数据（JSON格式，可选）</Label>
              <Textarea
                id="edit-metadata"
                value={metadata}
                onChange={(e) => setMetadata(e.target.value)}
                placeholder='{"key": "value"}'
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setEditDialogOpen(false)
              setSelectedTestCase(null)
              resetForm()
            }}>
              取消
            </Button>
            <Button onClick={handleEdit} disabled={loading}>
              保存
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除测试用例</DialogTitle>
            <DialogDescription>
              确定要删除这个测试用例吗？此操作不可撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setDeleteDialogOpen(false)
              setSelectedTestCase(null)
            }}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={loading}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
