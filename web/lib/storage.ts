/**
 * 调试结果存储工具
 * 使用后端API保存和加载JSON格式的处理结果
 */

import { debugAPI } from './api'

export interface SavedResult {
  id: string
  name: string
  type: 'chunks' | 'embeddings' | 'tokens' | 'index_data' | 'schemas' | 'sparse_vectors' | 'retrieval_results' | 'generation_results'
  data: any
  timestamp: number
  metadata?: Record<string, any>
}

/**
 * 保存结果到后端存储
 */
export async function saveResultToStorage(result: Omit<SavedResult, 'id' | 'timestamp'>): Promise<string> {
  try {
    const response = await debugAPI.saveDebugResult({
      name: result.name,
      type: result.type,
      data: result.data,
      metadata: result.metadata
    })
    return response.data.id
  } catch (error) {
    console.error('保存结果失败:', error)
    throw error
  }
}

/**
 * 从后端存储加载结果
 */
export async function loadResultFromStorage(resultType: SavedResult['type'], id: string): Promise<SavedResult | null> {
  try {
    const response = await debugAPI.loadDebugResult(resultType, id)
    return response.data
  } catch (error) {
    console.error('加载结果失败:', error)
    return null
  }
}

/**
 * 获取指定类型的所有结果列表
 */
export async function listResultsByType(type: SavedResult['type']): Promise<SavedResult[]> {
  try {
    const response = await debugAPI.listDebugResults(type)
    // 将索引数据转换为SavedResult格式
    return response.data.map(item => ({
      id: item.id,
      name: item.name,
      type: type,
      data: {}, // 列表不包含完整数据
      timestamp: item.timestamp,
      metadata: item.metadata
    }))
  } catch (error) {
    console.error('列出结果失败:', error)
    return []
  }
}

/**
 * 删除结果
 */
export async function deleteResult(resultType: SavedResult['type'], id: string): Promise<void> {
  try {
    await debugAPI.deleteDebugResult(resultType, id)
  } catch (error) {
    console.error('删除结果失败:', error)
    throw error
  }
}

/**
 * 导出结果为JSON文件
 */
export function exportResultToFile(result: SavedResult, filename?: string): void {
  const dataStr = JSON.stringify(result, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename || `${result.type}_${result.id}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * 从JSON文件导入结果
 */
export function importResultFromFile(file: File): Promise<SavedResult> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const result = JSON.parse(e.target?.result as string) as SavedResult
        // 验证结果格式
        if (!result.type || !result.data) {
          reject(new Error('无效的JSON格式'))
          return
        }
        resolve(result)
      } catch (error) {
        reject(new Error('解析JSON文件失败: ' + (error as Error).message))
      }
    }
    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsText(file)
  })
}