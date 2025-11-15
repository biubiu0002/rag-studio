"use client"

import { Input } from "@/components/ui/input"

export interface RetrievalConfig {
  retrieval_mode: "semantic" | "keyword" | "hybrid"
  top_k: number
  score_threshold: number
  fusion_method: "rrf" | "weighted"
  rrf_k: number
  semantic_weight: number
  keyword_weight: number
}

export const defaultRetrievalConfig: RetrievalConfig = {
  retrieval_mode: "hybrid",
  top_k: 10,
  score_threshold: 0.0,
  fusion_method: "rrf",
  rrf_k: 60,
  semantic_weight: 0.7,
  keyword_weight: 0.3
}

interface RetrievalConfigProps {
  value: RetrievalConfig
  onChange: (config: RetrievalConfig) => void
}

export default function RetrievalConfigComponent({ value, onChange }: RetrievalConfigProps) {
  const updateConfig = (updates: Partial<RetrievalConfig>) => {
    onChange({ ...value, ...updates })
  }

  return (
    <div className="space-y-4">
      {/* 检索模式选择 */}
      <div>
        <label className="block text-sm font-medium mb-2">检索模式</label>
        <div className="grid grid-cols-3 gap-3">
          <button
            type="button"
            onClick={() => updateConfig({ retrieval_mode: "semantic" })}
            className={`p-3 border rounded text-center transition-colors ${
              value.retrieval_mode === "semantic"
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-300 hover:border-blue-300"
            }`}
          >
            <div className="font-medium">语义向量检索</div>
            <div className="text-xs text-gray-500 mt-1">基于稠密向量的语义相似度</div>
          </button>
          <button
            type="button"
            onClick={() => updateConfig({ retrieval_mode: "keyword" })}
            className={`p-3 border rounded text-center transition-colors ${
              value.retrieval_mode === "keyword"
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-300 hover:border-blue-300"
            }`}
          >
            <div className="font-medium">关键词检索</div>
            <div className="text-xs text-gray-500 mt-1">基于稀疏向量的关键词匹配</div>
          </button>
          <button
            type="button"
            onClick={() => updateConfig({ retrieval_mode: "hybrid" })}
            className={`p-3 border rounded text-center transition-colors ${
              value.retrieval_mode === "hybrid"
                ? "border-blue-500 bg-blue-50 text-blue-700"
                : "border-gray-300 hover:border-blue-300"
            }`}
          >
            <div className="font-medium">混合检索</div>
            <div className="text-xs text-gray-500 mt-1">语义+关键词融合</div>
          </button>
        </div>
      </div>

      {/* 基础参数 */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-2">返回结果数 (top_k)</label>
          <Input
            type="number"
            value={value.top_k}
            onChange={(e) => updateConfig({ top_k: parseInt(e.target.value) || 10 })}
            min="1"
            max="50"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">分数阈值 (score_threshold)</label>
          <Input
            type="number"
            step="0.01"
            value={value.score_threshold}
            onChange={(e) => {
              const val = e.target.value === '' ? 0.0 : parseFloat(e.target.value)
              updateConfig({ score_threshold: isNaN(val) ? 0.0 : val })
            }}
            min="0"
            max="1"
          />
          <p className="text-xs text-gray-500 mt-1">只返回分数大于等于此阈值的结果 (0.0-1.0)</p>
        </div>
      </div>

      {/* 混合检索专用参数 */}
      {value.retrieval_mode === "hybrid" && (
        <div className="border-t pt-4 space-y-4">
          <h3 className="text-sm font-medium">混合检索融合策略</h3>
          
          {/* 融合方法选择 */}
          <div>
            <label className="block text-sm font-medium mb-2">融合方法</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => updateConfig({ fusion_method: "rrf" })}
                className={`p-2 border rounded text-center transition-colors ${
                  value.fusion_method === "rrf"
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-300 hover:border-blue-300"
                }`}
              >
                <div className="font-medium">RRF融合</div>
                <div className="text-xs text-gray-500 mt-1">基于排名的倒数融合</div>
              </button>
              <button
                type="button"
                onClick={() => updateConfig({ fusion_method: "weighted" })}
                className={`p-2 border rounded text-center transition-colors ${
                  value.fusion_method === "weighted"
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-300 hover:border-blue-300"
                }`}
              >
                <div className="font-medium">加权平均</div>
                <div className="text-xs text-gray-500 mt-1">基于分数的加权融合</div>
              </button>
            </div>
          </div>

          {/* RRF参数 */}
          {value.fusion_method === "rrf" && (
            <div>
              <label className="block text-sm font-medium mb-2">RRF参数 (k)</label>
              <Input
                type="number"
                value={value.rrf_k}
                onChange={(e) => updateConfig({ rrf_k: parseInt(e.target.value) || 60 })}
                min="1"
                max="100"
              />
              <p className="text-xs text-gray-500 mt-1">RRF公式: 1/(k + rank)，k值越大，排名差异的影响越小</p>
            </div>
          )}

          {/* 加权平均参数 */}
          {value.fusion_method === "weighted" && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">语义向量权重</label>
                <Input
                  type="number"
                  step="0.1"
                  value={value.semantic_weight}
                  onChange={(e) => {
                    const val = e.target.value === '' ? 0.7 : parseFloat(e.target.value)
                    const roundedVal = Math.round(val * 100) / 100
                    const complementVal = Math.round((1 - roundedVal) * 100) / 100
                    updateConfig({ 
                      semantic_weight: roundedVal,
                      keyword_weight: complementVal
                    })
                  }}
                  min="0"
                  max="1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">关键词权重</label>
                <Input
                  type="number"
                  step="0.1"
                  value={value.keyword_weight}
                  onChange={(e) => {
                    const val = e.target.value === '' ? 0.3 : parseFloat(e.target.value)
                    const roundedVal = Math.round(val * 100) / 100
                    const complementVal = Math.round((1 - roundedVal) * 100) / 100
                    updateConfig({ 
                      keyword_weight: roundedVal,
                      semantic_weight: complementVal
                    })
                  }}
                  min="0"
                  max="1"
                />
              </div>
              <div className="col-span-2">
                <p className="text-xs text-gray-500">权重总和: {(value.semantic_weight + value.keyword_weight).toFixed(2)}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

