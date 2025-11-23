package main

import (
	"context"
	"fmt"
	"net/url"
	"strconv"

	pb "github.com/qdrant/go-client/qdrant"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// QdrantService Qdrant服务
type QdrantService struct {
	defaultHost   string
	defaultPort   string
	defaultAPIKey string
	connections   map[string]*pb.PointsClient // 缓存连接，key为host:port
}

// NewQdrantService 创建Qdrant服务
func NewQdrantService(host, port, apiKey string) (*QdrantService, error) {
	service := &QdrantService{
		defaultHost:   host,
		defaultPort:   port,
		defaultAPIKey: apiKey,
		connections:   make(map[string]*pb.PointsClient),
	}

	return service, nil
}

// getQdrantConnection 获取或创建Qdrant连接
func (s *QdrantService) getQdrantConnection(kbConfig map[string]interface{}) (*pb.PointsClient, error) {
	var host, port, apiKey string

	// 从知识库配置中读取Qdrant连接信息
	if kbConfig != nil {
		if urlStr, ok := kbConfig["url"].(string); ok && urlStr != "" {
			// 解析URL
			parsedURL, err := url.Parse(urlStr)
			if err == nil {
				host = parsedURL.Hostname()
				if parsedURL.Port() != "" {
					port = parsedURL.Port()
					// 如果端口是标准HTTP端口（6333），转换为gRPC端口（6334）
					if port == "6333" {
						port = "6334"
					}
				} else {
					// 如果没有指定端口，使用默认gRPC端口
					port = "6334"
				}
			}
		} else {
			// 从配置中读取host和port
			if h, ok := kbConfig["host"].(string); ok {
				host = h
			}
			if p, ok := kbConfig["port"]; ok {
				switch v := p.(type) {
				case string:
					port = v
					// 如果端口是标准HTTP端口（6333），转换为gRPC端口（6334）
					if port == "6333" {
						port = "6334"
					}
				case float64:
					portInt := int(v)
					port = strconv.Itoa(portInt)
					// 如果端口是标准HTTP端口（6333），转换为gRPC端口（6334）
					if portInt == 6333 {
						port = "6334"
					}
				case int:
					port = strconv.Itoa(v)
					// 如果端口是标准HTTP端口（6333），转换为gRPC端口（6334）
					if v == 6333 {
						port = "6334"
					}
				}
			}
		}
		if key, ok := kbConfig["api_key"].(string); ok {
			apiKey = key
		}
	}

	// 使用默认值
	if host == "" {
		host = s.defaultHost
	}
	if port == "" {
		port = s.defaultPort
		// 如果默认端口是HTTP端口（6333），转换为gRPC端口（6334）
		if port == "6333" {
			port = "6334"
		}
	} else if port == "6333" {
		// 确保端口不是HTTP端口
		port = "6334"
	}
	if apiKey == "" {
		apiKey = s.defaultAPIKey
	}

	// 构建连接key
	connKey := fmt.Sprintf("%s:%s", host, port)

	// 检查是否已有连接
	if client, ok := s.connections[connKey]; ok {
		return client, nil
	}

	// 创建新的gRPC连接
	address := fmt.Sprintf("%s:%s", host, port)
	conn, err := grpc.Dial(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Qdrant at %s: %w", address, err)
	}

	// 创建Points客户端
	pointsClient := pb.NewPointsClient(conn)
	s.connections[connKey] = &pointsClient

	return &pointsClient, nil
}

// Search 向量检索
func (s *QdrantService) Search(ctx context.Context, collectionName string, queryVector []float32, topK uint64, scoreThreshold float32, kbConfig map[string]interface{}) ([]*RetrievalResult, error) {
	// 获取Qdrant连接
	pointsClient, err := s.getQdrantConnection(kbConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to get Qdrant connection: %w", err)
	}

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
	result, err := (*pointsClient).Search(ctx, searchPoints)
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
