"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Edit, Trash2, Loader2 } from "lucide-react"
import { knowledgeBaseAPI, type KnowledgeBase } from "@/lib/api"
import { showToast } from "@/lib/toast"

export default function KnowledgeBaseList() {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await knowledgeBaseAPI.list()
      setKnowledgeBases(response.data)
    } catch (err: any) {
      setError(err.message || "加载失败")
      console.error("加载知识库列表失败:", err)
    } finally {
      setLoading(false)
    }
  }

  // 删除知识库
  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`确定要删除知识库"${name}"吗？此操作不可恢复。`)) {
      return
    }

    try {
      await knowledgeBaseAPI.delete(id)
      // 重新加载列表
      loadKnowledgeBases()
    } catch (err: any) {
      showToast(`删除失败: ${err.message}`, "error")
    }
  }

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">知识库列表</h2>
        </div>
        <Card className="p-6 bg-red-50 border-red-200">
          <p className="text-red-600">加载失败: {error}</p>
          <Button onClick={loadKnowledgeBases} className="mt-4" variant="outline">
            重试
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">知识库列表</h2>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus size={16} className="mr-2" />
          新建知识库
        </Button>
      </div>

      {knowledgeBases.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500 mb-4">还没有创建知识库</p>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus size={16} className="mr-2" />
            创建第一个知识库
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4">
          {knowledgeBases.map((kb) => (
            <Card key={kb.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{kb.name}</h3>
                  {kb.description && (
                    <p className="text-sm text-gray-500 mt-1">{kb.description}</p>
                  )}
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                    <span>文档数: {kb.document_count}</span>
                    <span>分块数: {kb.chunk_count}</span>
                    <span>模型: {kb.embedding_model}</span>
                    <span>向量库: {kb.vector_db_type}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      kb.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {kb.is_active ? "激活" : "未激活"}
                  </span>
                  <Button variant="ghost" size="sm">
                    <Edit size={16} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(kb.id, kb.name)}
                  >
                    <Trash2 size={16} className="text-red-600" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
