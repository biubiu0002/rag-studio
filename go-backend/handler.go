package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// Handler HTTP处理器
type Handler struct {
	retrievalService *RetrievalService
}

// NewHandler 创建HTTP处理器
func NewHandler(retrievalService *RetrievalService) *Handler {
	return &Handler{
		retrievalService: retrievalService,
	}
}

// UnifiedSearch 统一检索接口
func (h *Handler) UnifiedSearch(c *gin.Context) {
	var req UnifiedSearchRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "invalid request",
			"message": err.Error(),
		})
		return
	}

	// 执行检索
	response, err := h.retrievalService.UnifiedSearch(c.Request.Context(), &req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"error":   "retrieval failed",
			"message": err.Error(),
		})
		return
	}

	// 返回成功响应
	c.JSON(http.StatusOK, gin.H{
		"code":    0,
		"message": response.Message,
		"data":    response,
	})
}

// HealthCheck 健康检查
func (h *Handler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status": "ok",
	})
}
