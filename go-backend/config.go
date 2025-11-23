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
	QdrantHost   string
	QdrantPort   string
	QdrantAPIKey string
}

func LoadConfig() *Config {
	config := &Config{
		Host:          getEnv("HOST", "0.0.0.0"),
		Port:          getEnv("PORT", "8001"),
		OllamaBaseURL: getEnv("OLLAMA_BASE_URL", "http://localhost:11434"),
		QdrantHost:    getEnv("QDRANT_HOST", "localhost"),
		QdrantPort:    getEnv("QDRANT_PORT", "6333"),
		QdrantAPIKey:  getEnv("QDRANT_API_KEY", ""),
	}
	return config
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
