package main

import (
	"fmt"
	"log"
	"path/filepath"

	"github.com/gin-gonic/gin"
)

func main() {
	// 加载配置
	config := LoadConfig()

	// 初始化服务
	embeddingService := NewEmbeddingService(config.OllamaBaseURL)

	qdrantService, err := NewQdrantService(config.QdrantHost, config.QdrantPort, config.QdrantAPIKey)
	if err != nil {
		log.Fatalf("Failed to create Qdrant service: %v", err)
	}

	// 获取storage路径（相对于backend目录）
	storagePath := filepath.Join("..", "backend", "storage")
	kbStore, err := NewKnowledgeBaseStore(storagePath)
	if err != nil {
		log.Fatalf("Failed to create knowledge base store: %v", err)
	}

	retrievalService := NewRetrievalService(embeddingService, qdrantService, kbStore)

	// 创建HTTP处理器
	handler := NewHandler(retrievalService)

	// 设置Gin模式
	gin.SetMode(gin.ReleaseMode)

	// 创建路由
	router := gin.Default()

	// 添加CORS中间件
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, accept, origin, Cache-Control, X-Requested-With")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT, DELETE")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// 注册路由
	api := router.Group("/api/v1/debug")
	{
		api.POST("/retrieve/unified", handler.UnifiedSearch)
		api.GET("/health", handler.HealthCheck)
	}

	// 启动服务器
	addr := fmt.Sprintf("%s:%s", config.Host, config.Port)
	log.Printf("Server starting on %s", addr)
	log.Printf("Ollama URL: %s", config.OllamaBaseURL)
	log.Printf("Qdrant: %s:%s", config.QdrantHost, config.QdrantPort)

	if err := router.Run(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
