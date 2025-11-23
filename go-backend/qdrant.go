package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"

	pb "github.com/qdrant/go-client/qdrant"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// QdrantService Qdrant服务（同时支持HTTP和gRPC）
type QdrantService struct {
	pointsClient *pb.PointsClient // gRPC客户端
	httpClient   *http.Client     // HTTP客户端
	httpBaseURL  string           // HTTP基础URL
	apiKey       string           // API密钥
	useHTTP      bool             // 是否优先使用HTTP
}

// NewQdrantService 创建Qdrant服务（同时支持HTTP和gRPC）
func NewQdrantService(host, httpPort, grpcPort, apiKey string) (*QdrantService, error) {
	// 创建HTTP客户端
	httpBaseURL := fmt.Sprintf("http://%s:%s", host, httpPort)
	httpClient := &http.Client{}

	// 创建gRPC连接
	grpcAddress := fmt.Sprintf("%s:%s", host, grpcPort)
	conn, err := grpc.Dial(grpcAddress, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Qdrant gRPC: %w", err)
	}

	// 创建Points客户端
	pointsClient := pb.NewPointsClient(conn)

	service := &QdrantService{
		pointsClient: &pointsClient,
		httpClient:   httpClient,
		httpBaseURL:  httpBaseURL,
		apiKey:       apiKey,
		useHTTP:      true, // 默认使用HTTP
	}

	return service, nil
}

// SetUseHTTP 设置是否使用HTTP（否则使用gRPC）
func (s *QdrantService) SetUseHTTP(useHTTP bool) {
	s.useHTTP = useHTTP
}

// IsUsingHTTP 检查当前是否使用HTTP
func (s *QdrantService) IsUsingHTTP() bool {
	return s.useHTTP
}

// Search 向量检索（自动选择HTTP或gRPC）
func (s *QdrantService) Search(ctx context.Context, collectionName string, queryVector []float32, topK uint64, scoreThreshold float32) ([]*RetrievalResult, error) {
	if s.useHTTP {
		return s.SearchHTTP(ctx, collectionName, queryVector, topK, scoreThreshold)
	}
	return s.SearchGRPC(ctx, collectionName, queryVector, topK, scoreThreshold)
}

// SearchHTTP 使用HTTP API进行向量检索
func (s *QdrantService) SearchHTTP(ctx context.Context, collectionName string, queryVector []float32, topK uint64, scoreThreshold float32) ([]*RetrievalResult, error) {
	// 构建搜索请求
	reqBody := map[string]interface{}{
		"query":         queryVector,
		"using":         "embedding",
		"limit":         topK,
		"with_payload":  true,
	}
	
	if scoreThreshold >= 0 {
		reqBody["score_threshold"] = scoreThreshold
	}

	// 序列化请求
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// 构建URL - 使用新版 Query API
	url := fmt.Sprintf("%s/collections/%s/points/query", s.httpBaseURL, collectionName)

	// 创建HTTP请求
	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if s.apiKey != "" {
		req.Header.Set("api-key", s.apiKey)
	}

	// 发送请求
	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("search failed with status %d: %s", resp.StatusCode, string(body))
	}

	// 解析响应
	var searchResp QdrantQueryResponse
	if err := json.Unmarshal(body, &searchResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %w, body: %s", err, string(body))
	}

	// 转换结果
	var results []*RetrievalResult
	if len(searchResp.Result) > 0 {
		// 尝试解析 result 字段
		var queryResp struct {
			Points []QdrantPoint `json:"points"`
		}
		// 先尝试作为 query response 解析
		if err := json.Unmarshal(searchResp.Result, &queryResp); err == nil && len(queryResp.Points) > 0 {
			points := queryResp.Points
			results = make([]*RetrievalResult, 0, len(points))
			for rank, point := range points {
				// 提取文档信息
				docID := extractStringFromMap(point.Payload, "document_id")
				if docID == "" {
					docID = extractStringFromMap(point.Payload, "doc_id")
				}
				chunkID := extractStringFromMap(point.Payload, "chunk_id")
				content := extractStringFromMap(point.Payload, "content")

				// 如果没有chunk_id，使用point ID
				if chunkID == "" {
					chunkID = fmt.Sprintf("%v", point.ID)
				}

				results = append(results, &RetrievalResult{
					DocID:    docID,
					ChunkID:  chunkID,
					Content:  content,
					Score:    float64(point.Score),
					Rank:     rank + 1,
					Source:   "vector",
					Metadata: point.Payload,
				})
			}
		} else {
			// 尝试直接作为数组解析
			var points []QdrantPoint
			if err := json.Unmarshal(searchResp.Result, &points); err != nil {
				// 如果是对象，尝试作为单个点处理
				var point QdrantPoint
				if err := json.Unmarshal(searchResp.Result, &point); err != nil {
					return nil, fmt.Errorf("failed to parse result: %w", err)
				}
				points = []QdrantPoint{point}
			}

			results = make([]*RetrievalResult, 0, len(points))
			for rank, point := range points {
				// 提取文档信息
				docID := extractStringFromMap(point.Payload, "document_id")
				if docID == "" {
					docID = extractStringFromMap(point.Payload, "doc_id")
				}
				chunkID := extractStringFromMap(point.Payload, "chunk_id")
				content := extractStringFromMap(point.Payload, "content")

				// 如果没有chunk_id，使用point ID
				if chunkID == "" {
					chunkID = fmt.Sprintf("%v", point.ID)
				}

				results = append(results, &RetrievalResult{
					DocID:    docID,
					ChunkID:  chunkID,
					Content:  content,
					Score:    float64(point.Score),
					Rank:     rank + 1,
					Source:   "vector",
					Metadata: point.Payload,
				})
			}
		}
	} else {
		results = make([]*RetrievalResult, 0)
	}

	return results, nil
}

// SearchGRPC 使用gRPC进行向量检索
func (s *QdrantService) SearchGRPC(ctx context.Context, collectionName string, queryVector []float32, topK uint64, scoreThreshold float32) ([]*RetrievalResult, error) {
	// 构建搜索请求
	vectorName := "embedding" // 指定向量字段名称
	searchPoints := &pb.SearchPoints{
		CollectionName: collectionName,
		VectorName:     &vectorName,
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

// QdrantSearchResponse Qdrant HTTP搜索响应
type QdrantSearchResponse struct {
	Result []QdrantPoint `json:"result"`
	Status interface{}   `json:"status"`
	Time   float64       `json:"time"`
}

// QdrantQueryResponse Qdrant Query API响应 - 灵活处理result字段可能是数组或对象
type QdrantQueryResponse struct {
	Result json.RawMessage `json:"result"`
	Status interface{}     `json:"status"`
	Time   float64        `json:"time"`
}

// QdrantPoint Qdrant点数据
type QdrantPoint struct {
	ID      interface{}            `json:"id"`
	Version int64                  `json:"version"`
	Score   float32                `json:"score"`
	Payload map[string]interface{} `json:"payload"`
	Vector  interface{}            `json:"vector,omitempty"`
}

// extractStringFromMap 从map中提取字符串值 - 支持嵌套对象格式
func extractStringFromMap(m map[string]interface{}, key string) string {
	if m == nil {
		return ""
	}

	value, ok := m[key]
	if !ok || value == nil {
		return ""
	}

	// 递归处理嵌套对象
	return extractValue(value)
}

// extractValue 从各种格式的值中提取字符串
func extractValue(value interface{}) string {
	if value == nil {
		return ""
	}

	switch v := value.(type) {
	case string:
		return v
	case float64:
		// 检查是否是整数
		if v == float64(int64(v)) {
			return fmt.Sprintf("%d", int64(v))
		}
		return fmt.Sprintf("%f", v)
	case int:
		return fmt.Sprintf("%d", v)
	case int64:
		return fmt.Sprintf("%d", v)
	case bool:
		return fmt.Sprintf("%t", v)
	case map[string]interface{}:
		// 处理嵌套对象 - 尝试多种可能的字段名
		possibleFields := []string{"stringValue", "string", "value", "integerValue", "doubleValue", "boolValue"}
		for _, field := range possibleFields {
			if val, exists := v[field]; exists {
				return extractValue(val)
			}
		}
		// 如果以上都没找到，返回整个对象的JSON表示
		if data, err := json.Marshal(v); err == nil {
			return string(data)
		}
		return fmt.Sprintf("%v", v)
	default:
		if data, err := json.Marshal(value); err == nil {
			return string(data)
		}
		return fmt.Sprintf("%v", value)
	}
}
