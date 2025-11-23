package main

import (
	"context"
	"fmt"
)

// RetrievalService 检索服务
type RetrievalService struct {
	embeddingService *EmbeddingService
	qdrantService    *QdrantService
	kbStore          *KnowledgeBaseStore
}

// NewRetrievalService 创建检索服务
func NewRetrievalService(embeddingService *EmbeddingService, qdrantService *QdrantService, kbStore *KnowledgeBaseStore) *RetrievalService {
	return &RetrievalService{
		embeddingService: embeddingService,
		qdrantService:    qdrantService,
		kbStore:          kbStore,
	}
}

// UnifiedSearch 统一检索接口
func (s *RetrievalService) UnifiedSearch(ctx context.Context, req *UnifiedSearchRequest) (*UnifiedSearchResponse, error) {
	// 获取知识库配置
	kb, err := s.kbStore.GetKnowledgeBase(req.KBID)
	if err != nil {
		return nil, fmt.Errorf("knowledge base not found: %w", err)
	}

	// 设置默认值
	if req.TopK == 0 {
		req.TopK = 10
	}
	if req.RetrievalMode == "" {
		req.RetrievalMode = "semantic"
	}

	// 根据检索模式执行检索
	var results []*RetrievalResult
	var err2 error

	switch req.RetrievalMode {
	case "semantic":
		results, err2 = s.semanticSearch(ctx, kb, req)
	case "keyword":
		return nil, fmt.Errorf("keyword search not implemented yet")
	case "hybrid":
		return nil, fmt.Errorf("hybrid search not implemented yet")
	default:
		return nil, fmt.Errorf("unsupported retrieval mode: %s", req.RetrievalMode)
	}

	if err2 != nil {
		return nil, err2
	}

	// 转换为响应格式
	retrievalResults := make([]RetrievalResult, len(results))
	for i, r := range results {
		retrievalResults[i] = *r
	}

	response := &UnifiedSearchResponse{
		Query:   req.Query,
		Results: retrievalResults,
		Config: SearchConfig{
			RetrievalMode:  req.RetrievalMode,
			TopK:           req.TopK,
			FusionMethod:   req.FusionMethod,
			RRFK:           req.RRFK,
			SemanticWeight: req.SemanticWeight,
			KeywordWeight:  req.KeywordWeight,
		},
		Message: fmt.Sprintf("%s检索完成: %d 个结果", req.RetrievalMode, len(results)),
	}

	return response, nil
}

// semanticSearch 语义向量检索
func (s *RetrievalService) semanticSearch(ctx context.Context, kb *KnowledgeBase, req *UnifiedSearchRequest) ([]*RetrievalResult, error) {
	// 1. 生成查询向量
	queryVector, err := s.embeddingService.EmbedText(kb.EmbeddingModel, req.Query)
	if err != nil {
		return nil, fmt.Errorf("embedding failed: %w", err)
	}

	// 2. 转换为float32
	queryVectorFloat32 := float64ToFloat32(queryVector)

	// 3. 设置score_threshold
	scoreThreshold := float32(req.ScoreThreshold)

	// 4. 执行向量检索
	results, err := s.qdrantService.Search(ctx, req.KBID, queryVectorFloat32, uint64(req.TopK), scoreThreshold)
	if err != nil {
		return nil, fmt.Errorf("vector search failed: %w", err)
	}

	return results, nil
}
