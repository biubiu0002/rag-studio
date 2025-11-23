package main

import (
	"os"
)

type Config struct {
	// Server配置
	Host string
	Port string

	// Ollama配置
	OllamaBaseURL string

	// Qdrant配置
	QdrantHost     string
	QdrantHTTPPort string // HTTP端口 (6333)
	QdrantGRPCPort string // gRPC端口 (6334)
	QdrantAPIKey   string
}

func LoadConfig() *Config {
	config := &Config{
		Host:           getEnv("HOST", "0.0.0.0"),
		Port:           getEnv("PORT", "8010"),
		OllamaBaseURL:  getEnv("OLLAMA_BASE_URL", "http://192.168.0.60:11434"),
		QdrantHost:     getEnv("QDRANT_HOST", "192.168.0.60"),
		QdrantHTTPPort: getEnv("QDRANT_HTTP_PORT", "6333"),
		QdrantGRPCPort: getEnv("QDRANT_GRPC_PORT", "6334"),
		QdrantAPIKey:   getEnv("QDRANT_API_KEY", ""),
	}
	return config
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
