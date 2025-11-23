"use client";

import { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { debugAPI } from "@/lib/api";
import {
  saveResultToStorage,
  listResultsByType,
  loadResultFromStorage,
  exportResultToFile,
  importResultFromFile,
  SavedResult,
} from "@/lib/storage";
import { showToast } from "@/lib/toast";

export default function DocumentEmbeddingView() {
  const [loading, setLoading] = useState(false);
  const [chunksText, setChunksText] = useState<string>("");
  const [chunks, setChunks] = useState<string[]>([]);
  const [embeddings, setEmbeddings] = useState<any>(null);
  const [embeddingPreview, setEmbeddingPreview] = useState<any[]>([]);
  const [embeddingConfig, setEmbeddingConfig] = useState({
    model: "bge-m3:latest",
    provider: "ollama",
    service_url: "", // 自定义服务地址
    api_key: "", // API密钥
  });
  const [expandAdvanced, setExpandAdvanced] = useState(false); // 展开高级选项
  const [availableModels, setAvailableModels] = useState<string[]>([]); // 可用的embedding模型列表
  const jsonFileInputRef = useRef<HTMLInputElement>(null); // 文件输入引用

  // 保存的结果列表
  const [savedChunks, setSavedChunks] = useState<SavedResult[]>([]);
  const [savedEmbeddings, setSavedEmbeddings] = useState<SavedResult[]>([]);
  const [selectedChunkId, setSelectedChunkId] = useState<string>("");
  const [selectedEmbeddingId, setSelectedEmbeddingId] = useState<string>("");
  const [saveName, setSaveName] = useState<string>("");

  // 加载已保存的结果列表
  useEffect(() => {
    loadSavedChunks().catch(console.error);
    loadSavedEmbeddings().catch(console.error);
  }, []);

  const loadSavedChunks = async () => {
    const results = await listResultsByType("chunks");
    setSavedChunks(results);
  };

  const loadSavedEmbeddings = async () => {
    const results = await listResultsByType("embeddings");
    setSavedEmbeddings(results);
  };

  // 加载可用模型
  const loadModels = async () => {
    try {
      const result = await debugAPI.getEmbeddingModels();
      setAvailableModels(result.data || []);
    } catch (error) {
      console.error("加载模型列表失败:", error);
    }
  };

  // 执行向量化
  const handleEmbed = async () => {
    if (chunks.length === 0) {
      showToast("请先从文档处理结果加载或导入JSON文件", "warning");
      return;
    }

    try {
      setLoading(true);

      const result = await debugAPI.embedDocuments({
        texts: chunks,
        model: embeddingConfig.model,
        provider: embeddingConfig.provider,
        service_url: embeddingConfig.service_url || undefined, // 传递自定义服务地址
        api_key: embeddingConfig.api_key || undefined, // 传递API密钥
      });

      setEmbeddings(result.data.vectors);
      setEmbeddingPreview(result.data.preview || []);

      showToast(`向量化完成！共处理 ${chunks.length} 个分块`, "success");
    } catch (error) {
      console.error("向量化失败:", error);
      showToast("向量化失败: " + (error as Error).message, "error");
    } finally {
      setLoading(false);
    }
  };

  // 从chunks结果加载
  const handleLoadChunks = async () => {
    if (!selectedChunkId) {
      showToast("请选择要加载的chunks结果", "warning");
      return;
    }

    try {
      const result = await loadResultFromStorage("chunks", selectedChunkId);
      if (!result || result.type !== "chunks") {
        showToast("加载失败：无效的结果", "error");
        return;
      }

      const chunksData = result.data.chunks || [];
      const texts = chunksData.map((chunk: any) => chunk.content || chunk);
      setChunks(texts);
      setChunksText(texts.join("\n"));

      showToast(
        `加载成功！${result.name}，共 ${texts.length} 个分块`,
        "success"
      );
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error");
    }
  };

  // 保存embeddings结果
  const handleSaveEmbeddings = async () => {
    if (!embeddings || embeddings.length === 0) {
      showToast("没有可保存的向量数据", "warning");
      return;
    }

    try {
      const name =
        saveName.trim() || `向量化结果_${new Date().toLocaleString()}`;
      const id = await saveResultToStorage({
        name,
        type: "embeddings",
        data: {
          vectors: embeddings,
          preview: embeddingPreview,
          chunks: chunks,
          config: embeddingConfig,
        },
        metadata: {
          vector_count: embeddings.length,
          dimension: embeddings[0]?.length || 0,
          model: embeddingConfig.model,
        },
      });

      showToast(`保存成功！ID: ${id}`, "success");
      setSaveName("");
      await loadSavedEmbeddings();
    } catch (error) {
      showToast("保存失败: " + (error as Error).message, "error");
    }
  };

  // 加载已保存的embeddings
  const handleLoadEmbeddings = async () => {
    if (!selectedEmbeddingId) {
      showToast("请选择要加载的结果", "warning");
      return;
    }

    try {
      const result = await loadResultFromStorage(
        "embeddings",
        selectedEmbeddingId
      );
      if (!result || result.type !== "embeddings") {
        showToast("加载失败：无效的结果", "error");
        return;
      }

      setEmbeddings(result.data.vectors || []);
      setEmbeddingPreview(result.data.preview || []);
      if (result.data.chunks) {
        setChunks(result.data.chunks);
        setChunksText(result.data.chunks.join("\n"));
      }
      if (result.data.config) {
        setEmbeddingConfig(result.data.config);
      }

      showToast(`加载成功！${result.name}`, "success");
    } catch (error) {
      showToast("加载失败: " + (error as Error).message, "error");
    }
  };

  // 导入JSON文件
  const handleImportJson = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const result = await importResultFromFile(file);
      if (result.type === "chunks") {
        // 如果是chunks类型，提取文本
        const chunksData = result.data.chunks || [];
        const texts = chunksData.map((chunk: any) => chunk.content || chunk);
        setChunks(texts);
        setChunksText(texts.join("\n"));
        showToast(
          `导入成功！${result.name}，共 ${texts.length} 个分块`,
          "success"
        );
      } else if (result.type === "embeddings") {
        setEmbeddings(result.data.vectors || []);
        setEmbeddingPreview(result.data.preview || []);
        if (result.data.chunks) {
          setChunks(result.data.chunks);
          setChunksText(result.data.chunks.join("\n"));
        }
        showToast(`导入成功！${result.name}`, "success");
      } else {
        showToast("文件类型不匹配，需要chunks或embeddings类型", "error");
      }
    } catch (error) {
      showToast("导入失败: " + (error as Error).message, "error");
    } finally {
      if (jsonFileInputRef.current) {
        jsonFileInputRef.current.value = "";
      }
    }
  };

  // 导出为JSON文件
  const handleExportEmbeddings = () => {
    if (!embeddings || embeddings.length === 0) {
      showToast("没有可导出的向量数据", "warning");
      return;
    }

    const result: SavedResult = {
      id: "",
      name: saveName.trim() || `向量化结果_${new Date().toLocaleString()}`,
      type: "embeddings",
      data: {
        vectors: embeddings,
        preview: embeddingPreview,
        chunks: chunks,
        config: embeddingConfig,
      },
      timestamp: Date.now(),
      metadata: {
        vector_count: embeddings.length,
        dimension: embeddings[0]?.length || 0,
        model: embeddingConfig.model,
      },
    };

    exportResultToFile(result);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">文档嵌入</h2>
        <p className="text-sm text-gray-500 mt-1">
          使用Embedding模型对文档分块进行向量化
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>步骤1: 选择文档</CardTitle>
          <CardDescription>
            从文档处理结果或JSON文件加载需要向量化的文档分块
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 从已保存的chunks加载 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              从文档处理结果加载
            </label>
            <div className="flex gap-2">
              <select
                value={selectedChunkId}
                onChange={(e) => setSelectedChunkId(e.target.value)}
                className="flex-1 p-2 border rounded text-sm"
              >
                <option value="">选择已保存的chunks结果...</option>
                {savedChunks.map((result) => (
                  <option key={result.id} value={result.id}>
                    {result.name} ({new Date(result.timestamp).toLocaleString()}
                    ) - {result.metadata?.chunk_count || 0}个分块
                  </option>
                ))}
              </select>
              <Button
                onClick={handleLoadChunks}
                disabled={!selectedChunkId}
                variant="outline"
              >
                加载
              </Button>
              <Button onClick={loadSavedChunks} variant="outline" size="sm">
                刷新
              </Button>
            </div>
          </div>

          {/* 从JSON文件导入 */}
          <div>
            <label className="block text-sm font-medium mb-2">
              从JSON文件导入
            </label>
            <input
              ref={jsonFileInputRef}
              type="file"
              accept=".json"
              onChange={handleImportJson}
              className="hidden"
            />
            <Button
              onClick={() => jsonFileInputRef.current?.click()}
              variant="outline"
              className="w-full"
            >
              选择JSON文件导入
            </Button>
          </div>

          {/* 文档展示 */}
          <div className="border-t pt-4">
            <label className="block text-sm font-medium mb-2">文档展示</label>
            <textarea
              value={chunksText}
              readOnly
              className="w-full h-48 p-2 border rounded bg-gray-50"
              placeholder="请从文档处理结果加载或导入JSON文件..."
            />
            <div className="text-sm text-gray-500 mt-1">
              共 {chunks.length} 个分块
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤2: 配置向量化参数</CardTitle>
          <CardDescription>选择Embedding模型和提供商</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">提供商</label>
              <select
                value={embeddingConfig.provider}
                onChange={(e) => {
                  setEmbeddingConfig({
                    ...embeddingConfig,
                    provider: e.target.value,
                  });
                  loadModels();
                }}
                className="w-full p-2 border rounded"
              >
                <option value="ollama">Ollama</option>
                <option value="openai">OpenAI</option>
                <option value="huggingface">HuggingFace</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">模型</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={embeddingConfig.model}
                  onChange={(e) =>
                    setEmbeddingConfig({
                      ...embeddingConfig,
                      model: e.target.value,
                    })
                  }
                  placeholder="输入模型名称，如：bge-m3:latest"
                  className="flex-1 p-2 border rounded"
                  list="available-models"
                />
                <datalist id="available-models">
                  {availableModels.map((model: string) => (
                    <option key={model} value={model} />
                  ))}
                </datalist>
                <Button onClick={loadModels} variant="outline" size="sm">
                  刷新
                </Button>
              </div>
            </div>
          </div>

          {/* 高级选项 */}
          <div className="border-t pt-4">
            <button
              onClick={() => setExpandAdvanced(!expandAdvanced)}
              className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              {expandAdvanced ? "▼" : "▶"} 高级选项 (自定义服务地址)
            </button>

            {expandAdvanced && (
              <div className="mt-4 space-y-3 p-3 bg-gray-50 rounded">
                {embeddingConfig.provider === "ollama" && (
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Ollama服务地址
                    </label>
                    <input
                      type="text"
                      value={embeddingConfig.service_url}
                      onChange={(e) =>
                        setEmbeddingConfig({
                          ...embeddingConfig,
                          service_url: e.target.value,
                        })
                      }
                      placeholder="http://localhost:11434"
                      className="w-full p-2 border rounded text-sm"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      保留为空时使用系统默认地址
                    </p>
                  </div>
                )}

                {embeddingConfig.provider !== "ollama" && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        服务地址
                      </label>
                      <input
                        type="text"
                        value={embeddingConfig.service_url}
                        onChange={(e) =>
                          setEmbeddingConfig({
                            ...embeddingConfig,
                            service_url: e.target.value,
                          })
                        }
                        placeholder="https://api.example.com"
                        className="w-full p-2 border rounded text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        API密钥
                      </label>
                      <input
                        type="password"
                        value={embeddingConfig.api_key}
                        onChange={(e) =>
                          setEmbeddingConfig({
                            ...embeddingConfig,
                            api_key: e.target.value,
                          })
                        }
                        placeholder="输入API密钥"
                        className="w-full p-2 border rounded text-sm"
                      />
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>步骤3: 执行向量化</CardTitle>
          <CardDescription>对分块文本进行向量化处理</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 bg-blue-50 rounded">
            <div className="text-sm text-blue-800">
              待向量化分块: {chunks.length} 个
            </div>
          </div>

          <Button
            onClick={handleEmbed}
            disabled={chunks.length === 0 || loading}
            className="w-full"
          >
            {loading ? "向量化中..." : "开始向量化"}
          </Button>

          {/* 向量化预览 */}
          {embeddingPreview.length > 0 && (
            <div>
              <div className="font-medium mb-2">向量化结果预览:</div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {embeddingPreview.map((item, idx) => (
                  <div key={idx} className="p-3 border rounded bg-gray-50">
                    <div className="text-xs text-gray-500 mb-1">
                      Chunk {item.index || idx + 1} | 维度: {item.dimension}
                    </div>
                    {item.preview && (
                      <div className="text-xs font-mono mb-1">
                        前5维: [
                        {item.preview
                          .map((v: number) => v.toFixed(3))
                          .join(", ")}
                        ...]
                      </div>
                    )}
                    {item.norm !== undefined && (
                      <div className="text-xs text-gray-500">
                        模长: {item.norm.toFixed(3)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {embeddings && (
            <div className="p-3 bg-green-50 rounded">
              <div className="text-sm text-green-800">
                ✓ 向量化完成！共生成 {embeddings.length} 个向量
                {embeddings[0] && `，每个向量维度: ${embeddings[0].length}`}
              </div>
            </div>
          )}

          {/* 保存/加载功能 - 常显 */}
          <div className="border-t pt-4 space-y-4">
            <div className="font-medium mb-2">保存/加载结果</div>

            {/* 保存当前结果 - 仅在有待保存结果时显示 */}
            {embeddings && embeddings.length > 0 && (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="输入保存名称（可选）"
                  className="flex-1 p-2 border rounded text-sm"
                />
                <Button onClick={handleSaveEmbeddings} variant="outline">
                  保存到本地
                </Button>
                <Button onClick={handleExportEmbeddings} variant="outline">
                  导出JSON
                </Button>
              </div>
            )}

            {/* 从已保存结果加载 - 常显 */}
            <div>
              <label className="block text-sm font-medium mb-2">
                从已保存结果加载
              </label>
              <div className="flex gap-2">
                <select
                  value={selectedEmbeddingId}
                  onChange={(e) => setSelectedEmbeddingId(e.target.value)}
                  className="flex-1 p-2 border rounded text-sm"
                >
                  <option value="">选择已保存的embeddings结果...</option>
                  {savedEmbeddings.map((result) => (
                    <option key={result.id} value={result.id}>
                      {result.name} (
                      {new Date(result.timestamp).toLocaleString()}) -{" "}
                      {result.metadata?.vector_count || 0}个向量
                    </option>
                  ))}
                </select>
                <Button
                  onClick={handleLoadEmbeddings}
                  disabled={!selectedEmbeddingId}
                  variant="outline"
                >
                  加载
                </Button>
                <Button
                  onClick={loadSavedEmbeddings}
                  variant="outline"
                  size="sm"
                >
                  刷新
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
