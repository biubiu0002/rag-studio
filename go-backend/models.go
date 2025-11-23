package main

// UnifiedSearchRequest 统一检索请求
type UnifiedSearchRequest struct {
	KBID           string  `json:"kb_id" binding:"required"`
	Query          string  `json:"query" binding:"required"`
	RetrievalMode  string  `json:"retrieval_mode"` // semantic, keyword, hybrid
	TopK           int     `json:"top_k"`
	ScoreThreshold float64 `json:"score_threshold"`
	FusionMethod   string  `json:"fusion_method"` // rrf, weighted
	SemanticWeight float64 `json:"semantic_weight"`
	KeywordWeight  float64 `json:"keyword_weight"`
	RRFK           int     `json:"rrf_k"`
}

// RetrievalResult 检索结果
type RetrievalResult struct {
	DocID    string                 `json:"doc_id"`
	ChunkID  string                 `json:"chunk_id"`
	Content  string                 `json:"content"`
	Score    float64                `json:"score"`
	Rank     int                    `json:"rank"`
	Source   string                 `json:"source"`
	Metadata map[string]interface{} `json:"metadata"`
}

// UnifiedSearchResponse 统一检索响应
type UnifiedSearchResponse struct {
	Query   string            `json:"query"`
	Results []RetrievalResult `json:"results"`
	Config  SearchConfig      `json:"config"`
	Message string            `json:"message"`
}

// SearchConfig 检索配置
type SearchConfig struct {
	RetrievalMode  string  `json:"retrieval_mode"`
	TopK           int     `json:"top_k"`
	FusionMethod   string  `json:"fusion_method"`
	RRFK           int     `json:"rrf_k"`
	SemanticWeight float64 `json:"semantic_weight"`
	KeywordWeight  float64 `json:"keyword_weight"`
}

// KnowledgeBase 知识库配置（简化版，只包含检索需要的字段）
type KnowledgeBase struct {
	ID                 string                 `json:"id"`
	EmbeddingProvider  string                 `json:"embedding_provider"`
	EmbeddingModel     string                 `json:"embedding_model"`
	EmbeddingDimension int                    `json:"embedding_dimension"`
	VectorDBType       string                 `json:"vector_db_type"`
	VectorDBConfig     map[string]interface{} `json:"vector_db_config"`
}

// OllamaEmbeddingRequest Ollama embedding请求
type OllamaEmbeddingRequest struct {
	Model  string `json:"model"`
	Prompt string `json:"prompt"`
}

// OllamaEmbeddingResponse Ollama embedding响应
type OllamaEmbeddingResponse struct {
	Embedding []float64 `json:"embedding"`
}
