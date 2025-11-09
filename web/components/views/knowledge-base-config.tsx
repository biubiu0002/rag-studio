"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
import { Plus, Search, Edit, Trash2, Loader2, ArrowLeft, Save, Download } from "lucide-react"
import { knowledgeBaseAPI, type KnowledgeBase } from "@/lib/api"
import { showToast } from "@/lib/toast"
import { saveResultToStorage, loadResultFromStorage, listResultsByType, type SavedResult } from "@/lib/storage"

// Schema字段类型
type FieldType = "text" | "array" | "number" | "boolean" | "keyword" | "sparse_vector"

interface SchemaField {
  name: string
  type: FieldType
  isIndexed: boolean
  isVectorIndex?: boolean
  isKeywordIndex?: boolean
  isSparseVectorIndex?: boolean
  dimension?: number // 用于向量字段
  description?: string // 字段描述
  // 添加稀疏向量特定属性
  sparseMethod?: "bm25" | "tf-idf" | "splade" // 稀疏向量生成方法
}

export default function KnowledgeBaseConfig() {
  // 知识库列表相关
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [filteredBases, setFilteredBases] = useState<KnowledgeBase[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(true)
  
  // 创建知识库对话框
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newKbName, setNewKbName] = useState("")
  const [creating, setCreating] = useState(false)
  
  // 知识库详情相关
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null)
  const [activeConfigTab, setActiveConfigTab] = useState<string>("schema")
  const [schemaFields, setSchemaFields] = useState<SchemaField[]>([])
  const [vectorDbType, setVectorDbType] = useState<string>("")
  const [isDataWritten, setIsDataWritten] = useState(false)
  const [editingField, setEditingField] = useState<SchemaField | null>(null)
  
  // Schema保存和加载相关
  const [savedSchemas, setSavedSchemas] = useState<SavedResult[]>([])
  const [savingSchema, setSavingSchema] = useState(false)
  const [loadSchemaDialogOpen, setLoadSchemaDialogOpen] = useState(false)
  const [selectedSchemaId, setSelectedSchemaId] = useState<string>("")

  // 配置项列表
  const configTabs = [
    { id: "schema", label: "Schema定义" },
    // 未来可以添加更多配置项
  ]

  // 加载知识库列表
  const loadKnowledgeBases = async () => {
    try {
      setLoading(true)
      const response = await knowledgeBaseAPI.list(1, 100)
      setKnowledgeBases(response.data)
      setFilteredBases(response.data)
    } catch (err: any) {
      showToast(`加载失败: ${err.message}`, "error")
      console.error("加载知识库列表失败:", err)
    } finally {
      setLoading(false)
    }
  }

  // 搜索知识库
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredBases(knowledgeBases)
    } else {
      const filtered = knowledgeBases.filter(
        (kb) =>
          kb.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (kb.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false)
      )
      setFilteredBases(filtered)
    }
  }, [searchQuery, knowledgeBases])

  // 创建知识库
  const handleCreateKnowledgeBase = async () => {
    if (!newKbName.trim()) {
      showToast("请输入知识库名称", "warning")
      return
    }

    try {
      setCreating(true)
      // 使用默认配置创建知识库
      await knowledgeBaseAPI.create({
        name: newKbName.trim(),
        embedding_model: "bge-m3:latest",
        vector_db_type: "qdrant",
        embedding_dimension: 1024, // bge-m3模型的维度是1024
      })
      showToast("知识库创建成功", "success")
      setCreateDialogOpen(false)
      setNewKbName("")
      loadKnowledgeBases()
    } catch (err: any) {
      showToast(`创建失败: ${err.message}`, "error")
    } finally {
      setCreating(false)
    }
  }

  // 加载已保存的schemas列表
  const loadSavedSchemas = async () => {
    try {
      const schemas = await listResultsByType('schemas')
      setSavedSchemas(schemas)
    } catch (error) {
      console.error("加载已保存schemas失败:", error)
    }
  }

  // 加载知识库详情
  const loadKnowledgeBaseDetail = async (kb: KnowledgeBase) => {
    try {
      setSelectedKb(kb)
      setIsDataWritten(kb.document_count > 0 || kb.chunk_count > 0)
      setVectorDbType(kb.vector_db_type)
      
      // 尝试加载已保存的schema配置
      try {
        const schemaResponse = await knowledgeBaseAPI.getSchema(kb.id)
        if (schemaResponse.data) {
          const schema = schemaResponse.data
          if (schema.fields && Array.isArray(schema.fields)) {
            setSchemaFields(schema.fields)
          }
          if (schema.vector_db_type) {
            setVectorDbType(schema.vector_db_type)
          }
        } else {
          // 如果没有schema，使用默认值（包含稀疏向量字段）
          const defaultFields: SchemaField[] = [
            { name: "content", type: "text", isIndexed: true, isVectorIndex: false },
            { name: "embedding", type: "array", isIndexed: true, isVectorIndex: true, dimension: 1024 },
            { name: "sparse_vector", type: "sparse_vector", isIndexed: true, isSparseVectorIndex: true, sparseMethod: "bm25" }
          ]
          setSchemaFields(defaultFields)
        }
      } catch (schemaErr: any) {
        // 如果获取schema失败，使用默认值（包含稀疏向量字段）
        const defaultFields: SchemaField[] = [
          { name: "content", type: "text", isIndexed: true, isVectorIndex: false },
          { name: "embedding", type: "array", isIndexed: true, isVectorIndex: true, dimension: 1024 },
          { name: "sparse_vector", type: "sparse_vector", isIndexed: true, isSparseVectorIndex: true, sparseMethod: "bm25" }
        ]
        setSchemaFields(defaultFields)
      }
      
      // 加载已保存的schemas列表（用于从其他知识库加载schema）
      loadSavedSchemas()
    } catch (err: any) {
      showToast(`加载详情失败: ${err.message}`, "error")
    }
  }

  // 添加schema字段
  const handleAddField = () => {
    const newField: SchemaField = {
      name: "",
      type: "text",
      isIndexed: false,
      isVectorIndex: false,
    }
    setEditingField(newField)
  }

  // 保存字段编辑
  const handleSaveField = () => {
    if (!editingField) return
    
    if (!editingField.name.trim()) {
      showToast("请输入字段名称", "warning")
      return
    }

    // 检查字段名是否已存在
    if (
      schemaFields.some(
        (f) => f.name === editingField.name && f !== editingField
      )
    ) {
      showToast("字段名称已存在", "warning")
      return
    }

    // 如果是新字段，添加到列表；否则更新现有字段
    if (schemaFields.includes(editingField)) {
      setSchemaFields([...schemaFields])
    } else {
      setSchemaFields([...schemaFields, editingField])
    }
    setEditingField(null)
  }

  // 删除字段
  const handleDeleteField = (fieldName: string) => {
    if (fieldName === "content" || fieldName === "embedding") {
      showToast("不能删除默认字段", "warning")
      return
    }
    setSchemaFields(schemaFields.filter((f) => f.name !== fieldName))
  }

  // 保存schema（直接保存到知识库配置中）
  const handleSaveSchema = async () => {
    if (!selectedKb) {
      showToast("请先选择知识库", "warning")
      return
    }

    try {
      setSavingSchema(true)
      
      // 直接更新知识库的schema配置
      await knowledgeBaseAPI.updateSchema(
        selectedKb.id,
        schemaFields,
        vectorDbType
      )
      
      showToast("Schema保存成功", "success")
    } catch (err: any) {
      showToast(`保存失败: ${err.message}`, "error")
    } finally {
      setSavingSchema(false)
    }
  }

  // 加载schema（从已保存的schemas或从其他知识库加载）
  const handleLoadSchema = async () => {
    if (!selectedSchemaId) {
      showToast("请选择要加载的schema", "warning")
      return
    }
    if (!selectedKb) {
      showToast("请先选择知识库", "warning")
      return
    }

    try {
      // 从已保存的schemas中加载
      const result = await loadResultFromStorage('schemas', selectedSchemaId)
      if (!result || result.type !== 'schemas') {
        showToast("加载失败：无效的schema", "error")
        return
      }

      const schemaData = result.data
      if (schemaData.fields && Array.isArray(schemaData.fields)) {
        setSchemaFields(schemaData.fields)
      }
      if (schemaData.vector_db_type) {
        setVectorDbType(schemaData.vector_db_type)
      }
      
      // 直接保存到当前知识库
      await knowledgeBaseAPI.updateSchema(
        selectedKb.id,
        schemaData.fields || [],
        schemaData.vector_db_type
      )
      
      showToast(`加载并保存成功！${result.name}`, "success")
      setLoadSchemaDialogOpen(false)
      setSelectedSchemaId("")
    } catch (err: any) {
      showToast(`加载失败: ${err.message}`, "error")
    }
  }

  // 删除知识库
  const handleDeleteKnowledgeBase = async (id: string, name: string) => {
    if (!confirm(`确定要删除知识库"${name}"吗？此操作不可恢复。`)) {
      return
    }

    try {
      await knowledgeBaseAPI.delete(id)
      showToast("删除成功", "success")
      if (selectedKb?.id === id) {
        setSelectedKb(null)
      }
      loadKnowledgeBases()
    } catch (err: any) {
      showToast(`删除失败: ${err.message}`, "error")
    }
  }

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  // 如果选择了知识库，显示详情页面
  if (selectedKb) {
    return (
      <div className="flex h-full">
        {/* 左侧Sidebar */}
        <div className="w-48 border-r bg-white p-4">
          <div className="mb-4">
            <Button
              variant="ghost"
              onClick={() => setSelectedKb(null)}
              className="w-full justify-start"
            >
              <ArrowLeft size={16} className="mr-2" />
              返回列表
            </Button>
          </div>
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900 mb-2">配置项</h3>
            {configTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveConfigTab(tab.id)}
                className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors border-l-2 ${
                  activeConfigTab === tab.id
                    ? "bg-blue-50 text-blue-700 border-l-blue-600"
                    : "text-gray-700 border-l-transparent hover:bg-gray-50"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* 右侧Content */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{selectedKb.name}</h2>
              {selectedKb.description && (
                <p className="text-gray-600 mt-1">{selectedKb.description}</p>
              )}
            </div>

            {/* Schema管理 - 去掉Card包装 */}
            {activeConfigTab === "schema" && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Schema定义</h3>
                  <div className="flex items-center gap-2">
                    <Button 
                      onClick={() => setLoadSchemaDialogOpen(true)} 
                      size="sm" 
                      variant="outline"
                    >
                      <Download size={16} className="mr-2" />
                      加载Schema
                    </Button>
                    <Button 
                      onClick={handleSaveSchema} 
                      size="sm" 
                      variant="outline"
                      disabled={savingSchema}
                    >
                      <Save size={16} className="mr-2" />
                      {savingSchema ? "保存中..." : "保存Schema"}
                    </Button>
                    {!isDataWritten && (
                      <Button onClick={handleAddField} size="sm" className="bg-black text-white hover:bg-gray-800">
                        <Plus size={16} className="mr-2" />
                        添加字段
                      </Button>
                    )}
                  </div>
                </div>

                {/* 向量数据库类型选择 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    向量数据库类型
                  </label>
                  <Select
                    value={vectorDbType}
                    onValueChange={setVectorDbType}
                    disabled={isDataWritten}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="选择向量数据库类型" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="qdrant">Qdrant</SelectItem>
                      <SelectItem value="elasticsearch">Elasticsearch</SelectItem>
                      <SelectItem value="milvus">Milvus</SelectItem>
                    </SelectContent>
                  </Select>
                  {isDataWritten && (
                    <p className="text-sm text-gray-500 mt-2">
                      已写入数据，无法修改向量数据库类型
                    </p>
                  )}
                </div>

                {/* Schema字段表格 */}
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          字段名称
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          类型
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          索引
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          操作
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {schemaFields.map((field) => (
                        <tr key={field.name}>
                          <td className="px-4 py-3 text-sm text-gray-900">
                            {field.name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {field.type === "text"
                              ? "文本"
                              : field.type === "array"
                              ? "数组"
                              : field.type === "number"
                              ? "数字"
                              : field.type === "boolean"
                              ? "布尔"
                              : field.type === "keyword"
                              ? "关键词"
                              : "稀疏向量"}
                            {field.isVectorIndex && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                向量索引
                              </span>
                            )}
                            {field.isKeywordIndex && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded">
                                关键词索引
                              </span>
                            )}
                            {field.isSparseVectorIndex && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                                稀疏向量索引
                              </span>
                            )}
                            {field.type === "sparse_vector" && field.sparseMethod && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">
                                {field.sparseMethod.toUpperCase()}
                              </span>
                            )}
                            {field.dimension && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                                {field.dimension}维
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {field.isIndexed ? "是" : "否"}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              {!isDataWritten && (
                                <>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setEditingField(field)}
                                  >
                                    <Edit size={14} />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDeleteField(field.name)}
                                  >
                                    <Trash2 size={14} className="text-red-600" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 编辑字段对话框 */}
        {editingField && (
          <Dialog open={!!editingField} onOpenChange={() => setEditingField(null)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  {schemaFields.includes(editingField) ? "编辑字段" : "添加字段"}
                </DialogTitle>
                <DialogDescription>
                  配置字段的名称、类型和索引选项
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    字段名称
                  </label>
                  <Input
                    value={editingField.name}
                    onChange={(e) =>
                      setEditingField({ ...editingField, name: e.target.value })
                    }
                    placeholder="输入字段名称"
                    disabled={schemaFields.includes(editingField)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    字段类型
                  </label>
                  <Select
                    value={editingField.type}
                    onValueChange={(value: FieldType) =>
                      setEditingField({ ...editingField, type: value })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">文本</SelectItem>
                      <SelectItem value="array">数组</SelectItem>
                      <SelectItem value="number">数字</SelectItem>
                      <SelectItem value="boolean">布尔</SelectItem>
                      <SelectItem value="keyword">关键词</SelectItem>
                      <SelectItem value="sparse_vector">稀疏向量</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    字段描述
                  </label>
                  <Input
                    value={editingField.description || ""}
                    onChange={(e) =>
                      setEditingField({ ...editingField, description: e.target.value })
                    }
                    placeholder="输入字段描述"
                  />
                </div>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={editingField.isIndexed}
                      onChange={(e) =>
                        setEditingField({
                          ...editingField,
                          isIndexed: e.target.checked,
                        })
                      }
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm text-gray-700">创建索引</span>
                  </label>
                  {editingField.type === "array" && (
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={editingField.isVectorIndex}
                        onChange={(e) => {
                          const newEditingField = {
                            ...editingField,
                            isVectorIndex: e.target.checked,
                          };
                          // 如果选中向量索引，确保类型为array
                          if (e.target.checked) {
                            newEditingField.type = "array";
                          }
                          setEditingField(newEditingField);
                        }}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">向量索引</span>
                    </label>
                  )}
                  {editingField.type === "keyword" && (
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={editingField.isKeywordIndex}
                        onChange={(e) =>
                          setEditingField({
                            ...editingField,
                            isKeywordIndex: e.target.checked,
                          })
                        }
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">关键词索引</span>
                    </label>
                  )}
                  {editingField.type === "sparse_vector" && (
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={editingField.isSparseVectorIndex}
                        onChange={(e) =>
                          setEditingField({
                            ...editingField,
                            isSparseVectorIndex: e.target.checked,
                          })
                        }
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">稀疏向量索引</span>
                    </label>
                  )}
                  {(editingField.type === "array" && editingField.isVectorIndex) && (
                    <div className="mt-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        向量维度
                      </label>
                      <Input
                        type="number"
                        value={editingField.dimension || ""}
                        onChange={(e) =>
                          setEditingField({ 
                            ...editingField, 
                            dimension: parseInt(e.target.value) || undefined 
                          })
                        }
                        placeholder="输入向量维度"
                      />
                    </div>
                  )}
                  {editingField.type === "sparse_vector" && editingField.isSparseVectorIndex && (
                    <div className="mt-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        稀疏向量生成方法
                      </label>
                      <Select
                        value={editingField.sparseMethod || "bm25"}
                        onValueChange={(value: "bm25" | "tf-idf" | "splade") =>
                          setEditingField({ 
                            ...editingField, 
                            sparseMethod: value
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="bm25">BM25</SelectItem>
                          <SelectItem value="tf-idf">TF-IDF</SelectItem>
                          <SelectItem value="splade">SPLADE</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditingField(null)}>
                  取消
                </Button>
                <Button onClick={handleSaveField}>保存</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}


        {/* 加载Schema对话框 */}
        <Dialog open={loadSchemaDialogOpen} onOpenChange={setLoadSchemaDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>加载Schema</DialogTitle>
              <DialogDescription>
                从已保存的Schema配置中选择一个加载
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择Schema
              </label>
              <Select
                value={selectedSchemaId}
                onValueChange={setSelectedSchemaId}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择要加载的Schema" />
                </SelectTrigger>
                <SelectContent>
                  {savedSchemas.length === 0 ? (
                    <SelectItem value="" disabled>暂无已保存的Schema</SelectItem>
                  ) : (
                    savedSchemas.map((schema) => (
                      <SelectItem key={schema.id} value={schema.id}>
                        {schema.name} ({new Date(schema.timestamp).toLocaleString()})
                        {schema.metadata?.kb_name && ` - ${schema.metadata.kb_name}`}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {selectedSchemaId && (
                <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
                  {(() => {
                    const selected = savedSchemas.find(s => s.id === selectedSchemaId)
                    if (selected?.metadata) {
                      return (
                        <div>
                          <div>知识库: {selected.metadata.kb_name || 'N/A'}</div>
                          <div>向量数据库: {selected.metadata.vector_db_type || 'N/A'}</div>
                          <div>字段数: {selected.metadata.field_count || 'N/A'}</div>
                        </div>
                      )
                    }
                    return null
                  })()}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setLoadSchemaDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleLoadSchema} disabled={!selectedSchemaId}>
                加载
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  // 知识库列表页面
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">知识库配置</h2>
        <Button
          onClick={() => setCreateDialogOpen(true)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus size={16} className="mr-2" />
          创建知识库
        </Button>
      </div>

      {/* 搜索框 */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <Input
              placeholder="搜索知识库..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* 知识库列表表格 */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      ) : filteredBases.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-gray-500 mb-4">
            {searchQuery ? "没有找到匹配的知识库" : "还没有创建知识库"}
          </p>
          {!searchQuery && (
            <Button
              onClick={() => setCreateDialogOpen(true)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus size={16} className="mr-2" />
              创建第一个知识库
            </Button>
          )}
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      知识库名称
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      描述
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      向量数据库
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      文档数
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      状态
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredBases.map((kb) => (
                    <tr key={kb.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => loadKnowledgeBaseDetail(kb)}
                          className="text-sm font-medium text-gray-900 hover:text-blue-600 cursor-pointer text-left"
                        >
                          {kb.name}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-500">
                          {kb.description || "-"}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{kb.vector_db_type}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600">{kb.document_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            kb.is_active
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {kb.is_active ? "激活" : "未激活"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => loadKnowledgeBaseDetail(kb)}
                          >
                            <Edit size={16} />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteKnowledgeBase(kb.id, kb.name)}
                          >
                            <Trash2 size={16} className="text-red-600" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 创建知识库对话框 */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>创建知识库</DialogTitle>
            <DialogDescription>
              输入知识库名称以创建新的知识库
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              知识库名称
            </label>
            <Input
              value={newKbName}
              onChange={(e) => setNewKbName(e.target.value)}
              placeholder="输入知识库名称"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleCreateKnowledgeBase()
                }
              }}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleCreateKnowledgeBase}
              disabled={creating}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {creating ? (
                <>
                  <Loader2 size={16} className="mr-2 animate-spin" />
                  创建中...
                </>
              ) : (
                "创建"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
