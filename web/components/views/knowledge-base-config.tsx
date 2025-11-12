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

// Schema字段类型 - 对应Qdrant的Payload类型和向量类型
type FieldType = 
  | "text"           // 文本字段（Qdrant Payload）
  | "keyword"        // 关键词字段（Qdrant Payload）
  | "integer"        // 整数字段（Qdrant Payload）
  | "float"          // 浮点数字段（Qdrant Payload）
  | "boolean"        // 布尔字段（Qdrant Payload）
  | "dense_vector"   // 稠密向量（Qdrant Named Vector）
  | "sparse_vector"  // 稀疏向量（Qdrant Sparse Vector）

// Qdrant距离度量类型
type DistanceMetric = "Cosine" | "Euclid" | "Dot" | "Manhattan"

// 稀疏向量生成方法类型
type SparseMethod = "bm25" | "tf-idf" | "simple" | "splade"

// HNSW索引配置
interface HNSWConfig {
  m?: number // 连接数，默认16
  ef_construct?: number // 构建时的搜索宽度，默认100
  full_scan_threshold?: number // 全扫描阈值，默认10000
  on_disk?: boolean // 是否使用磁盘索引
}

// 向量量化配置
interface QuantizationConfig {
  type?: "scalar" | "product" | "binary" // 量化类型
  always_ram?: boolean // 是否始终保持在内存中
}

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
  sparseMethod?: SparseMethod // 稀疏向量生成方法
  // Qdrant向量配置
  distance?: DistanceMetric // 距离度量类型
  hnsw?: HNSWConfig // HNSW索引配置
  quantization?: QuantizationConfig // 量化配置
  on_disk?: boolean // 是否使用磁盘存储（向量数据）
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
  const [vectorDbConfig, setVectorDbConfig] = useState<Record<string, any>>({})
  const [vectorDbConfigModified, setVectorDbConfigModified] = useState<Record<string, boolean>>({}) // 标记哪些字段被修改过
  const [vectorDbConfigExists, setVectorDbConfigExists] = useState<Record<string, boolean>>({}) // 标记哪些敏感字段已存在（但不存储值）
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
      
      // 加载配置，但不加载敏感字段（密码、API密钥）
      const config = kb.vector_db_config || {}
      const safeConfig: Record<string, any> = {}
      const existsFlags: Record<string, boolean> = {}
      
      // 只加载非敏感字段（明确检查，避免undefined）
      if (config.host && config.host.trim()) safeConfig.host = config.host
      if (config.port !== undefined && config.port !== null) safeConfig.port = config.port
      if (config.url && config.url.trim()) safeConfig.url = config.url
      if (config.user && config.user.trim()) safeConfig.user = config.user
      
      // 标记敏感字段是否存在（但不存储实际值）
      if (config.api_key && config.api_key.trim()) existsFlags.api_key = true
      if (config.password && config.password.trim()) existsFlags.password = true
      
      // 确保新建知识库时所有字段都是空的
      setVectorDbConfig(safeConfig)
      setVectorDbConfigExists(existsFlags)
      setVectorDbConfigModified({}) // 重置修改标记
      
      // 尝试加载已保存的schema配置
      try {
        const schemaResponse = await knowledgeBaseAPI.getSchema(kb.id)
        if (schemaResponse.data) {
          const schema = schemaResponse.data
          if (schema.fields && Array.isArray(schema.fields)) {
            // 转换旧格式到新格式（一次性迁移）
            const migratedFields = schema.fields.map((field: any) => {
              // array + isVectorIndex → dense_vector
              if (field.type === "array" && field.isVectorIndex) {
                return { 
                  ...field, 
                  type: "dense_vector",
                  dimension: field.dimension || 1024,
                  distance: field.distance || "Cosine",
                  hnsw: field.hnsw || {
                    m: 16,
                    ef_construct: 100,
                    full_scan_threshold: 10000,
                    on_disk: false
                  }
                }
              }
              // number → integer
              if (field.type === "number") {
                return { ...field, type: "integer" }
              }
              return field
            })
            setSchemaFields(migratedFields)
          }
          if (schema.vector_db_type) {
            setVectorDbType(schema.vector_db_type)
          }
        } else {
          // 如果没有schema，使用默认值（包含稀疏向量字段和Qdrant配置）
          const defaultFields: SchemaField[] = [
            { 
              name: "content", 
              type: "text", 
              isIndexed: true, 
              isVectorIndex: false 
            },
            { 
              name: "embedding", 
              type: "dense_vector", 
              isIndexed: true, 
              isVectorIndex: true, 
              dimension: 1024,
              distance: "Cosine",
              on_disk: false,
              hnsw: {
                m: 16,
                ef_construct: 100,
                full_scan_threshold: 10000,
                on_disk: false
              }
            },
            { 
              name: "sparse_vector", 
              type: "sparse_vector", 
              isIndexed: true, 
              isSparseVectorIndex: true, 
              sparseMethod: "bm25" 
            }
          ]
          setSchemaFields(defaultFields)
        }
      } catch (schemaErr: any) {
        // 如果获取schema失败，使用默认值（包含稀疏向量字段和Qdrant配置）
        const defaultFields: SchemaField[] = [
          { 
            name: "content", 
            type: "text", 
            isIndexed: true, 
            isVectorIndex: false 
          },
          { 
            name: "embedding", 
            type: "dense_vector", 
            isIndexed: true, 
            isVectorIndex: true, 
            dimension: 1024,
            distance: "Cosine",
            on_disk: false,
            hnsw: {
              m: 16,
              ef_construct: 100,
              full_scan_threshold: 10000,
              on_disk: false
            }
          },
          { 
            name: "sparse_vector", 
            type: "sparse_vector", 
            isIndexed: true, 
            isSparseVectorIndex: true, 
            sparseMethod: "bm25" 
          }
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

  // 处理字段类型切换，初始化默认配置
  const handleFieldTypeChange = (newType: FieldType) => {
    if (!editingField) return
    
    const baseField = { ...editingField, type: newType }
    
    // 如果切换到稠密向量类型，初始化默认配置
    if (newType === "dense_vector") {
      setEditingField({
        ...baseField,
        isVectorIndex: true,
        dimension: editingField.dimension || 1024,
        distance: editingField.distance || "Cosine",
        on_disk: editingField.on_disk ?? false,
        hnsw: editingField.hnsw || {
          m: 16,
          ef_construct: 100,
          full_scan_threshold: 10000,
          on_disk: false
        },
        quantization: editingField.quantization || undefined
      })
    }
    // 如果切换到稀疏向量类型，初始化默认配置
    else if (newType === "sparse_vector") {
      setEditingField({
        ...baseField,
        isSparseVectorIndex: true,
        sparseMethod: editingField.sparseMethod || "bm25"
      })
    }
    // 其他类型，清除向量相关配置
    else {
      setEditingField({
        ...baseField,
        isVectorIndex: false,
        isSparseVectorIndex: false,
        isKeywordIndex: newType === "keyword" ? false : undefined,
        dimension: undefined,
        distance: undefined,
        hnsw: undefined,
        quantization: undefined,
        on_disk: undefined,
        sparseMethod: undefined
      })
    }
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
      
      // 构建安全的配置对象：只包含非敏感字段或用户修改过的字段
      const safeConfig: Record<string, any> = {}
      
      // 添加非敏感字段
      if (vectorDbConfig.host) safeConfig.host = vectorDbConfig.host
      if (vectorDbConfig.port) safeConfig.port = vectorDbConfig.port
      if (vectorDbConfig.url) safeConfig.url = vectorDbConfig.url
      if (vectorDbConfig.user) safeConfig.user = vectorDbConfig.user
      
      // 只有用户修改过的敏感字段才包含
      if (vectorDbConfigModified.api_key) {
        if (vectorDbConfig.api_key) {
          safeConfig.api_key = vectorDbConfig.api_key
        }
        // 如果用户清空了字段，不发送该字段（保持原值）
      } else if (vectorDbConfigExists.api_key) {
        // 用户没有修改，保持原值，不发送该字段
      }
      
      if (vectorDbConfigModified.password) {
        if (vectorDbConfig.password) {
          safeConfig.password = vectorDbConfig.password
        }
        // 如果用户清空了字段，不发送该字段（保持原值）
      } else if (vectorDbConfigExists.password) {
        // 用户没有修改，保持原值，不发送该字段
      }
      
      // 直接更新知识库的schema配置
      await knowledgeBaseAPI.updateSchema(
        selectedKb.id,
        schemaFields,
        vectorDbType,
        safeConfig
      )
      
      showToast("Schema保存成功", "success")
      // 保存后更新存在标记并清除修改标记
      if (vectorDbConfigModified.api_key && vectorDbConfig.api_key) {
        setVectorDbConfigExists({ ...vectorDbConfigExists, api_key: true })
      }
      if (vectorDbConfigModified.password && vectorDbConfig.password) {
        setVectorDbConfigExists({ ...vectorDbConfigExists, password: true })
      }
      setVectorDbConfigModified({})
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
      
      // 转换旧格式到新格式（一次性迁移）
      let migratedFields: any[] = []
      if (schemaData.fields && Array.isArray(schemaData.fields)) {
        migratedFields = schemaData.fields.map((field: any) => {
          // array + isVectorIndex → dense_vector
          if (field.type === "array" && field.isVectorIndex) {
            return { 
              ...field, 
              type: "dense_vector",
              dimension: field.dimension || 1024,
              distance: field.distance || "Cosine",
              hnsw: field.hnsw || {
                m: 16,
                ef_construct: 100,
                full_scan_threshold: 10000,
                on_disk: false
              }
            }
          }
          // number → integer
          if (field.type === "number") {
            return { ...field, type: "integer" }
          }
          return field
        })
        setSchemaFields(migratedFields)
      }
      if (schemaData.vector_db_type) {
        setVectorDbType(schemaData.vector_db_type)
      }
      
      // 直接保存到当前知识库（使用转换后的字段）
      await knowledgeBaseAPI.updateSchema(
        selectedKb.id,
        migratedFields,
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
                {/* Qdrant配置摘要卡片 */}
                {vectorDbType === "qdrant" && schemaFields.length > 0 && (
                  <Card className="bg-linear-to-r from-blue-50 to-indigo-50 border-blue-200">
                    <CardHeader>
                      <CardTitle className="text-sm font-medium text-blue-900 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Qdrant向量配置摘要
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                        {schemaFields.filter(f => f.type === "dense_vector").map(field => (
                          <div key={field.name} className="bg-white p-3 rounded border border-blue-100">
                            <div className="font-medium text-gray-900 mb-2">🔷 {field.name}</div>
                            <div className="space-y-1 text-xs text-gray-600">
                              <div>• 维度: {field.dimension || "未设置"}</div>
                              <div>• 距离: {field.distance || "Cosine"}</div>
                              <div>• HNSW-m: {field.hnsw?.m || 16}</div>
                              <div>• HNSW-ef: {field.hnsw?.ef_construct || 100}</div>
                              <div>• 量化: {field.quantization?.type ? field.quantization.type.toUpperCase() : "无"}</div>
                              <div>• 磁盘: {field.on_disk ? "是" : "否"}</div>
                            </div>
                          </div>
                        ))}
                        {schemaFields.filter(f => f.type === "sparse_vector").map(field => (
                          <div key={field.name} className="bg-white p-3 rounded border border-purple-100">
                            <div className="font-medium text-gray-900 mb-2">⚡ {field.name}</div>
                            <div className="space-y-1 text-xs text-gray-600">
                              <div>• 类型: 稀疏向量</div>
                              <div>• 方法: {field.sparseMethod?.toUpperCase() || "BM25"}</div>
                              <div>• 用途: 混合检索</div>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 text-xs text-blue-700">
                        💡 提示: 点击"编辑"按钮可调整HNSW、量化、距离度量等高级配置
                      </div>
                    </CardContent>
                  </Card>
                )}

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

                {/* 向量数据库服务地址配置 */}
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">向量数据库服务地址配置</h4>
                  <form autoComplete="off" onSubmit={(e) => e.preventDefault()}>
                  {vectorDbType === "qdrant" && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">服务地址（可选，留空使用默认配置）</label>
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            autoComplete="off"
                            name={`${vectorDbType}-host-${selectedKb?.id || 'new'}`}
                            id={`${vectorDbType}-host-${selectedKb?.id || 'new'}`}
                            placeholder="主机地址（如：localhost）"
                            value={vectorDbConfig.host || ""}
                            onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, host: e.target.value })}
                            disabled={isDataWritten}
                          />
                          <Input
                            type="number"
                            autoComplete="off"
                            name={`${vectorDbType}-port-${selectedKb?.id || 'new'}`}
                            id={`${vectorDbType}-port-${selectedKb?.id || 'new'}`}
                            placeholder="端口（如：6333）"
                            value={vectorDbConfig.port || ""}
                            onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, port: e.target.value ? parseInt(e.target.value) : undefined })}
                            disabled={isDataWritten}
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">或使用完整URL</label>
                        <Input
                          autoComplete="url"
                          name={`qdrant-url-${selectedKb?.id || 'new'}`}
                          id={`qdrant-url-${selectedKb?.id || 'new'}`}
                          placeholder="http://localhost:6333 或 localhost:6333"
                          value={vectorDbConfig.url || ""}
                          onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, url: e.target.value })}
                          disabled={isDataWritten}
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">API密钥（可选）</label>
                        <Input
                          type="password"
                          autoComplete="new-password"
                          name="qdrant-api-key"
                          id={`qdrant-api-key-${selectedKb?.id || 'new'}`}
                          placeholder={vectorDbConfigModified.api_key ? "" : (vectorDbConfigExists.api_key ? "已配置（留空不修改，输入新值覆盖）" : "API密钥（可选）")}
                          value={vectorDbConfigModified.api_key ? (vectorDbConfig.api_key || "") : ""}
                          onChange={(e) => {
                            setVectorDbConfig({ ...vectorDbConfig, api_key: e.target.value })
                            setVectorDbConfigModified({ ...vectorDbConfigModified, api_key: true })
                          }}
                          disabled={isDataWritten}
                        />
                        {!vectorDbConfigModified.api_key && vectorDbConfigExists.api_key && (
                          <p className="text-xs text-gray-400 mt-1">当前已配置，输入新值可覆盖</p>
                        )}
                      </div>
                      <p className="text-xs text-gray-500">
                        💡 提示：如果留空，将使用系统默认配置（从环境变量读取）
                      </p>
                    </div>
                  )}
                  {vectorDbType === "elasticsearch" && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">服务地址（可选）</label>
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            autoComplete="off"
                            placeholder="主机地址"
                            value={vectorDbConfig.host || ""}
                            onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, host: e.target.value })}
                            disabled={isDataWritten}
                          />
                          <Input
                            type="number"
                            autoComplete="off"
                            placeholder="端口（如：9200）"
                            value={vectorDbConfig.port || ""}
                            onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, port: e.target.value ? parseInt(e.target.value) : undefined })}
                            disabled={isDataWritten}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          autoComplete="off"
                          name={`${vectorDbType}-user-${selectedKb?.id || 'new'}`}
                          id={`${vectorDbType}-user-${selectedKb?.id || 'new'}`}
                          placeholder="用户名（可选）"
                          value={vectorDbConfig.user || ""}
                          onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, user: e.target.value })}
                          disabled={isDataWritten}
                        />
                        <Input
                          type="password"
                          autoComplete="new-password"
                          name={`${vectorDbType}-password-${selectedKb?.id || 'new'}`}
                          id={`${vectorDbType}-password-${selectedKb?.id || 'new'}`}
                          placeholder={vectorDbConfigModified.password ? "密码（可选）" : (vectorDbConfigExists.password ? "已配置（留空不修改，输入新值覆盖）" : "密码（可选）")}
                          value={vectorDbConfigModified.password ? (vectorDbConfig.password || "") : ""}
                          onChange={(e) => {
                            setVectorDbConfig({ ...vectorDbConfig, password: e.target.value })
                            setVectorDbConfigModified({ ...vectorDbConfigModified, password: true })
                          }}
                          disabled={isDataWritten}
                        />
                        {!vectorDbConfigModified.password && vectorDbConfigExists.password && (
                          <p className="text-xs text-gray-400 mt-1">当前已配置，输入新值可覆盖</p>
                        )}
                      </div>
                    </div>
                  )}
                  {vectorDbType === "milvus" && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">服务地址（可选）</label>
                        <div className="grid grid-cols-2 gap-2">
                          <Input
                            placeholder="主机地址"
                            value={vectorDbConfig.host || ""}
                            onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, host: e.target.value })}
                            disabled={isDataWritten}
                          />
                          <Input
                            type="number"
                            placeholder="端口（如：19530）"
                            value={vectorDbConfig.port || ""}
                            onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, port: e.target.value ? parseInt(e.target.value) : undefined })}
                            disabled={isDataWritten}
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <Input
                          autoComplete="off"
                          name={`${vectorDbType}-user-${selectedKb?.id || 'new'}`}
                          id={`${vectorDbType}-user-${selectedKb?.id || 'new'}`}
                          placeholder="用户名（可选）"
                          value={vectorDbConfig.user || ""}
                          onChange={(e) => setVectorDbConfig({ ...vectorDbConfig, user: e.target.value })}
                          disabled={isDataWritten}
                        />
                        <Input
                          type="password"
                          autoComplete="new-password"
                          name={`${vectorDbType}-password-${selectedKb?.id || 'new'}`}
                          id={`${vectorDbType}-password-${selectedKb?.id || 'new'}`}
                          placeholder={vectorDbConfigModified.password ? "密码（可选）" : (vectorDbConfigExists.password ? "已配置（留空不修改，输入新值覆盖）" : "密码（可选）")}
                          value={vectorDbConfigModified.password ? (vectorDbConfig.password || "") : ""}
                          onChange={(e) => {
                            setVectorDbConfig({ ...vectorDbConfig, password: e.target.value })
                            setVectorDbConfigModified({ ...vectorDbConfigModified, password: true })
                          }}
                          disabled={isDataWritten}
                        />
                        {!vectorDbConfigModified.password && vectorDbConfigExists.password && (
                          <p className="text-xs text-gray-400 mt-1">当前已配置，输入新值可覆盖</p>
                        )}
                      </div>
                    </div>
                  )}
                  {!vectorDbType && (
                    <p className="text-sm text-gray-500">请先选择向量数据库类型</p>
                  )}
                  </form>
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
                              : field.type === "keyword"
                              ? "关键词"
                              : field.type === "integer"
                              ? "整数"
                              : field.type === "float"
                              ? "浮点数"
                              : field.type === "boolean"
                              ? "布尔"
                              : field.type === "dense_vector"
                              ? "稠密向量"
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
            <DialogContent className="max-h-[90vh] flex flex-col max-w-2xl">
              <DialogHeader>
                <DialogTitle>
                  {schemaFields.includes(editingField) ? "编辑字段" : "添加字段"}
                </DialogTitle>
                <DialogDescription>
                  配置字段的名称、类型和索引选项
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4 overflow-y-auto flex-1 max-h-[60vh]">
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
                    onValueChange={(value: FieldType) => handleFieldTypeChange(value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">文本 (Payload)</SelectItem>
                      <SelectItem value="keyword">关键词 (Payload)</SelectItem>
                      <SelectItem value="integer">整数 (Payload)</SelectItem>
                      <SelectItem value="float">浮点数 (Payload)</SelectItem>
                      <SelectItem value="boolean">布尔 (Payload)</SelectItem>
                      <SelectItem value="dense_vector">稠密向量 (Named Vector)</SelectItem>
                      <SelectItem value="sparse_vector">稀疏向量 (Sparse Vector)</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500 mt-1">
                    Payload字段存储元数据，向量字段用于相似度搜索
                  </p>
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
                  {editingField.type === "dense_vector" && (
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={editingField.isVectorIndex ?? true}
                        onChange={(e) => {
                          setEditingField({
                            ...editingField,
                            isVectorIndex: e.target.checked,
                          });
                        }}
                        className="rounded border-gray-300"
                      />
                      <span className="text-sm text-gray-700">向量索引（推荐）</span>
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
                  {editingField.type === "dense_vector" && (
                    <>
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

                      <div className="mt-2">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          距离度量
                        </label>
                        <Select
                          value={editingField.distance || "Cosine"}
                          onValueChange={(value: any) =>
                            setEditingField({ 
                              ...editingField, 
                              distance: value
                            })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Cosine">余弦距离 (Cosine)</SelectItem>
                            <SelectItem value="Euclid">欧几里得距离 (Euclid)</SelectItem>
                            <SelectItem value="Dot">点积 (Dot)</SelectItem>
                            <SelectItem value="Manhattan">曼哈顿距离 (Manhattan)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="mt-2">
                        <label className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={editingField.on_disk || false}
                            onChange={(e) =>
                              setEditingField({
                                ...editingField,
                                on_disk: e.target.checked,
                              })
                            }
                            className="rounded border-gray-300"
                          />
                          <span className="text-sm text-gray-700">使用磁盘存储（适用于大规模向量）</span>
                        </label>
                      </div>

                      {/* HNSW配置 */}
                      <div className="mt-3 p-3 border rounded space-y-2">
                        <div className="font-medium text-sm text-gray-700 mb-2">HNSW索引配置</div>
                        
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">
                            连接数 (m) - 默认16，范围4-64
                          </label>
                          <Input
                            type="number"
                            value={editingField.hnsw?.m || 16}
                            onChange={(e) =>
                              setEditingField({ 
                                ...editingField, 
                                hnsw: {
                                  ...editingField.hnsw,
                                  m: parseInt(e.target.value) || 16
                                }
                              })
                            }
                            placeholder="16"
                            min={4}
                            max={64}
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-600 mb-1">
                            构建时搜索宽度 (ef_construct) - 默认100
                          </label>
                          <Input
                            type="number"
                            value={editingField.hnsw?.ef_construct || 100}
                            onChange={(e) =>
                              setEditingField({ 
                                ...editingField, 
                                hnsw: {
                                  ...editingField.hnsw,
                                  ef_construct: parseInt(e.target.value) || 100
                                }
                              })
                            }
                            placeholder="100"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-600 mb-1">
                            全扫描阈值 (full_scan_threshold) - 默认10000
                          </label>
                          <Input
                            type="number"
                            value={editingField.hnsw?.full_scan_threshold || 10000}
                            onChange={(e) =>
                              setEditingField({ 
                                ...editingField, 
                                hnsw: {
                                  ...editingField.hnsw,
                                  full_scan_threshold: parseInt(e.target.value) || 10000
                                }
                              })
                            }
                            placeholder="10000"
                          />
                        </div>

                        <div>
                          <label className="flex items-center space-x-2">
                            <input
                              type="checkbox"
                              checked={editingField.hnsw?.on_disk || false}
                              onChange={(e) =>
                                setEditingField({
                                  ...editingField,
                                  hnsw: {
                                    ...editingField.hnsw,
                                    on_disk: e.target.checked,
                                  }
                                })
                              }
                              className="rounded border-gray-300"
                            />
                            <span className="text-xs text-gray-600">HNSW索引使用磁盘存储</span>
                          </label>
                        </div>
                      </div>

                      {/* 量化配置 */}
                      <div className="mt-3 p-3 border rounded space-y-2">
                        <div className="font-medium text-sm text-gray-700 mb-2">向量量化配置（可选）</div>
                        
                        <div>
                          <label className="block text-xs text-gray-600 mb-1">
                            量化类型
                          </label>
                          <Select
                            value={editingField.quantization?.type || "none"}
                            onValueChange={(value: any) =>
                              setEditingField({ 
                                ...editingField, 
                                quantization: value === "none" ? undefined : {
                                  ...editingField.quantization,
                                  type: value
                                }
                              })
                            }
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="选择量化类型" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">不使用量化</SelectItem>
                              <SelectItem value="scalar">标量量化 (Scalar) - 4倍压缩</SelectItem>
                              <SelectItem value="product">乘积量化 (Product) - 8-32倍压缩</SelectItem>
                              <SelectItem value="binary">二值量化 (Binary) - 32倍压缩</SelectItem>
                            </SelectContent>
                          </Select>
                          <p className="text-xs text-gray-500 mt-1">
                            量化可减少内存占用，但会损失一定精度
                          </p>
                        </div>

                        {editingField.quantization?.type && (
                          <div>
                            <label className="flex items-center space-x-2">
                              <input
                                type="checkbox"
                                checked={editingField.quantization?.always_ram || false}
                                onChange={(e) =>
                                  setEditingField({
                                    ...editingField,
                                    quantization: {
                                      ...editingField.quantization,
                                      always_ram: e.target.checked,
                                    }
                                  })
                                }
                                className="rounded border-gray-300"
                              />
                              <span className="text-xs text-gray-600">始终保持在内存中</span>
                            </label>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                  {editingField.type === "sparse_vector" && (
                    <div className="mt-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        稀疏向量生成方法
                      </label>
                      <Select
                        value={editingField.sparseMethod || "bm25"}
                        onValueChange={(value: "bm25" | "tf-idf" | "simple" | "splade") =>
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
                          <SelectItem value="simple">简单词频</SelectItem>
                          <SelectItem value="splade">SPLADE</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              </div>
              <DialogFooter className="shrink-0">
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
                    <div className="px-2 py-1.5 text-sm text-gray-500">暂无已保存的Schema</div>
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
