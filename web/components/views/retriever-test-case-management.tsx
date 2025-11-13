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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { retrieverTestCaseAPI, testAPI, RetrieverTestCase, ExpectedAnswer, TestSet } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { Plus, Edit, Trash2, X } from "lucide-react"

export default function RetrieverTestCaseManagementView() {
  const [loading, setLoading] = useState(false)
  const [testSets, setTestSets] = useState<TestSet[]>([])
  const [selectedTestSetId, setSelectedTestSetId] = useState<string>("")
  const [testCases, setTestCases] = useState<RetrieverTestCase[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(20)
  
  // 对话框状态
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [selectedTestCase, setSelectedTestCase] = useState<RetrieverTestCase | null>(null)
  
  // 表单数据
  const [question, setQuestion] = useState("")
  const [expectedAnswers, setExpectedAnswers] = useState<ExpectedAnswer[]>([
    { answer_text: "", chunk_id: "", relevance_score: 1.0 }
  ])
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
      const result = await testAPI.listTestSets(undefined, "retrieval", 1, 100)
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
      const result = await retrieverTestCaseAPI.list(selectedTestSetId, page, pageSize)
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
    setExpectedAnswers([{ answer_text: "", chunk_id: "", relevance_score: 1.0 }])
    setMetadata("")
  }

  const handleCreate = async () => {
    if (!question.trim() || expectedAnswers.length === 0) {
      showToast("请填写问题和至少一个期望答案", "error")
      return
    }

    // 验证期望答案
    const validAnswers = expectedAnswers.filter(a => a.answer_text.trim())
    if (validAnswers.length === 0) {
      showToast("请至少填写一个有效的期望答案", "error")
      return
    }

    try {
      setLoading(true)
      const metadataObj = metadata.trim() ? JSON.parse(metadata) : {}
      await retrieverTestCaseAPI.create({
        test_set_id: selectedTestSetId,
        question: question.trim(),
        expected_answers: validAnswers.map(a => ({
          answer_text: a.answer_text.trim(),
          chunk_id: a.chunk_id?.trim() || undefined,
          relevance_score: a.relevance_score
        })),
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
    if (!selectedTestCase || !question.trim() || expectedAnswers.length === 0) {
      showToast("请填写问题和至少一个期望答案", "error")
      return
    }

    const validAnswers = expectedAnswers.filter(a => a.answer_text.trim())
    if (validAnswers.length === 0) {
      showToast("请至少填写一个有效的期望答案", "error")
      return
    }

    try {
      setLoading(true)
      const metadataObj = metadata.trim() ? JSON.parse(metadata) : {}
      await retrieverTestCaseAPI.update(selectedTestCase.id, {
        question: question.trim(),
        expected_answers: validAnswers.map(a => ({
          answer_text: a.answer_text.trim(),
          chunk_id: a.chunk_id?.trim() || undefined,
          relevance_score: a.relevance_score
        })),
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
      await retrieverTestCaseAPI.delete(selectedTestCase.id)
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

  const openEditDialog = (testCase: RetrieverTestCase) => {
    setSelectedTestCase(testCase)
    setQuestion(testCase.question)
    setExpectedAnswers(testCase.expected_answers.length > 0 
      ? testCase.expected_answers 
      : [{ answer_text: "", chunk_id: "", relevance_score: 1.0 }]
    )
    setMetadata(JSON.stringify(testCase.metadata || {}, null, 2))
    setEditDialogOpen(true)
  }

  const openDeleteDialog = (testCase: RetrieverTestCase) => {
    setSelectedTestCase(testCase)
    setDeleteDialogOpen(true)
  }

  const addExpectedAnswer = () => {
    setExpectedAnswers([...expectedAnswers, { answer_text: "", chunk_id: "", relevance_score: 1.0 }])
  }

  const updateExpectedAnswer = (index: number, field: keyof ExpectedAnswer, value: string | number) => {
    const newAnswers = [...expectedAnswers]
    newAnswers[index] = { ...newAnswers[index], [field]: value }
    setExpectedAnswers(newAnswers)
  }

  const removeExpectedAnswer = (index: number) => {
    if (expectedAnswers.length > 1) {
      setExpectedAnswers(expectedAnswers.filter((_, i) => i !== index))
    }
  }

  const renderExpectedAnswersForm = () => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>期望答案列表</Label>
          <Button type="button" size="sm" variant="outline" onClick={addExpectedAnswer}>
            <Plus className="h-4 w-4 mr-1" />
            添加答案
          </Button>
        </div>
        {expectedAnswers.map((answer, index) => (
          <div key={index} className="border rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">答案 {index + 1}</span>
              {expectedAnswers.length > 1 && (
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => removeExpectedAnswer(index)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
            <div>
              <Label className="text-xs">答案文本 *</Label>
              <Textarea
                value={answer.answer_text}
                onChange={(e) => updateExpectedAnswer(index, "answer_text", e.target.value)}
                placeholder="输入期望答案文本"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label className="text-xs">Chunk ID（可选）</Label>
                <Input
                  value={answer.chunk_id || ""}
                  onChange={(e) => updateExpectedAnswer(index, "chunk_id", e.target.value)}
                  placeholder="chunk-xxx"
                />
              </div>
              <div>
                <Label className="text-xs">关联度分数 (0-1)</Label>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={answer.relevance_score}
                  onChange={(e) => updateExpectedAnswer(index, "relevance_score", parseFloat(e.target.value))}
                />
              </div>
            </div>
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
            <CardDescription>选择一个检索器测试集</CardDescription>
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
                <CardTitle>检索器测试用例</CardTitle>
                <CardDescription>
                  管理问题及其期望答案
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
                      <TableHead className="w-[40%]">问题</TableHead>
                      <TableHead className="w-[20%]">答案数量</TableHead>
                      <TableHead className="w-[20%]">创建时间</TableHead>
                      <TableHead className="w-[20%] text-right">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {testCases.map((testCase) => (
                      <TableRow key={testCase.id}>
                        <TableCell className="font-medium">
                          <div className="line-clamp-2">{testCase.question}</div>
                        </TableCell>
                        <TableCell>{testCase.expected_answers.length}</TableCell>
                        <TableCell>
                          {new Date(testCase.created_at).toLocaleDateString()}
                        </TableCell>
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
            <DialogTitle>创建检索器测试用例</DialogTitle>
            <DialogDescription>
              填写问题及其期望答案列表
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
            
            {renderExpectedAnswersForm()}
            
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
            <DialogTitle>编辑检索器测试用例</DialogTitle>
            <DialogDescription>
              修改问题及其期望答案列表
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
            
            {renderExpectedAnswersForm()}
            
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
