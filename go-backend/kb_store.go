package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// KnowledgeBaseStore 知识库存储
type KnowledgeBaseStore struct {
	storagePath string
	kbs         map[string]*KnowledgeBase
}

// NewKnowledgeBaseStore 创建知识库存储
func NewKnowledgeBaseStore(storagePath string) (*KnowledgeBaseStore, error) {
	store := &KnowledgeBaseStore{
		storagePath: storagePath,
		kbs:         make(map[string]*KnowledgeBase),
	}

	// 加载知识库配置
	if err := store.loadKnowledgeBases(); err != nil {
		return nil, fmt.Errorf("load knowledge bases failed: %w", err)
	}

	return store, nil
}

// loadKnowledgeBases 从JSON文件加载知识库配置
func (s *KnowledgeBaseStore) loadKnowledgeBases() error {
	kbFile := filepath.Join(s.storagePath, "knowledge_bases.json")

	data, err := os.ReadFile(kbFile)
	if err != nil {
		return fmt.Errorf("read knowledge bases file failed: %w", err)
	}

	var kbs []*KnowledgeBase
	if err := json.Unmarshal(data, &kbs); err != nil {
		return fmt.Errorf("unmarshal knowledge bases failed: %w", err)
	}

	// 构建索引
	for _, kb := range kbs {
		s.kbs[kb.ID] = kb
	}

	return nil
}

// GetKnowledgeBase 获取知识库配置
func (s *KnowledgeBaseStore) GetKnowledgeBase(kbID string) (*KnowledgeBase, error) {
	kb, ok := s.kbs[kbID]
	if !ok {
		return nil, fmt.Errorf("knowledge base not found: %s", kbID)
	}
	return kb, nil
}
