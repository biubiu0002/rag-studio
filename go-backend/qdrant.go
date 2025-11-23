package main

import (
	"context"
	"fmt"

	pb "github.com/qdrant/go-client/qdrant"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// QdrantService Qdrant服务
type QdrantService struct {
	pointsClient *pb.PointsClient
}

// NewQdrantService 创建Qdrant服务
func NewQdrantService(host, port, apiKey string) (*QdrantService, error) {
	address := fmt.Sprintf("%s:%s", host, port)

	// 创建gRPC连接
	conn, err := grpc.Dial(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Qdrant: %w", err)
	}

	// 创建Points客户端
	pointsClient := pb.NewPointsClient(conn)

	service := &QdrantService{
		pointsClient: &pointsClient,
	}

	return service, nil
}

// Search 向量检索
func (s *QdrantService) Search(ctx context.Context, collectionName string, queryVector []float32, topK uint64, scoreThreshold float32) ([]*RetrievalResult, error) {
	// 构建搜索请求
	searchPoints := &pb.SearchPoints{
		CollectionName: collectionName,
		Vector:         queryVector,
		Limit:          topK,
		ScoreThreshold: &scoreThreshold,
		WithPayload: &pb.WithPayloadSelector{
			SelectorOptions: &pb.WithPayloadSelector_Enable{
				Enable: true,
			},
		},
	}

	// 执行搜索
	result, err := (*s.pointsClient).Search(ctx, searchPoints)
	if err != nil {
		return nil, fmt.Errorf("search failed: %w", err)
	}

	// 转换结果
	results := make([]*RetrievalResult, 0, len(result.Result))
	for rank, point := range result.Result {
		payload := point.Payload

		// 提取文档信息
		docID := extractStringFromPayload(payload, "doc_id")
		chunkID := extractStringFromPayload(payload, "chunk_id")
		content := extractStringFromPayload(payload, "content")

		// 如果没有chunk_id，使用point ID
		if chunkID == "" {
			chunkID = fmt.Sprintf("%v", point.Id)
		}

		// 构建metadata
		metadata := make(map[string]interface{})
		if payload != nil {
			for key, value := range payload {
				metadata[key] = extractValueFromQdrantValue(value)
			}
		}

		results = append(results, &RetrievalResult{
			DocID:    docID,
			ChunkID:  chunkID,
			Content:  content,
			Score:    float64(point.Score),
			Rank:     rank + 1,
			Source:   "vector",
			Metadata: metadata,
		})
	}

	return results, nil
}

// extractStringFromPayload 从payload中提取字符串值
func extractStringFromPayload(payload map[string]*pb.Value, key string) string {
	if payload == nil {
		return ""
	}

	value, ok := payload[key]
	if !ok || value == nil {
		return ""
	}

	return extractValueFromQdrantValue(value)
}

// extractValueFromQdrantValue 从Qdrant Value中提取值
func extractValueFromQdrantValue(value *pb.Value) string {
	if value == nil {
		return ""
	}

	switch v := value.Kind.(type) {
	case *pb.Value_StringValue:
		return v.StringValue
	case *pb.Value_IntegerValue:
		return fmt.Sprintf("%d", v.IntegerValue)
	case *pb.Value_DoubleValue:
		return fmt.Sprintf("%f", v.DoubleValue)
	case *pb.Value_BoolValue:
		return fmt.Sprintf("%t", v.BoolValue)
	default:
		return fmt.Sprintf("%v", value)
	}
}

// float64ToFloat32 将[]float64转换为[]float32
func float64ToFloat32(v []float64) []float32 {
	result := make([]float32, len(v))
	for i, val := range v {
		result[i] = float32(val)
	}
	return result
}
