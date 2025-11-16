"use client"

import { useState, useEffect } from "react"
import Sidebar from "@/components/sidebar"
import Header from "@/components/header"
import KnowledgeBaseList from "@/components/views/knowledge-base-list"
import KnowledgeBaseConfig from "@/components/views/knowledge-base-config"
import DocumentProcessing from "@/components/views/document-processing"
import DocumentEmbeddingView from "@/components/views/document-embedding"
import DocumentTokenizationView from "@/components/views/document-tokenization"
import IndexWritingView from "@/components/views/index-writing"
import RetrievalView from "@/components/views/retrieval"
import GenerationTestView from "@/components/views/generation-test"
import TestSetManagementView from "@/components/views/test-set-management"
import EvaluationHistoryView from "@/components/views/evaluation-history"
import EvaluationTasksView from "@/components/views/evaluation-tasks"
import Dashboard from "@/components/views/dashboard"

type ContentView =
  | "dashboard"
  | "knowledge-base-list"
  | "knowledge-base-config"
  | "document-processing"
  | "document-embedding"
  | "document-tokenization"
  | "index-writing"
  | "pipeline-debug"
  | "retrieval"
  | "generation-test"
  | "test-set-management"
  | "retriever-evaluation"
  | "generator-evaluation"
  | "evaluation-history"
  | "evaluation-tasks"

export default function Home() {
  const [currentView, setCurrentView] = useState<ContentView>("dashboard")
  const [breadcrumbs, setBreadcrumbs] = useState(["Dashboard"])

  const handleNavigate = (view: string, path: string[]) => {
    setCurrentView(view as ContentView)
    setBreadcrumbs(path)
  }

  // 监听自定义导航事件
  useEffect(() => {
    const handleNavigation = (event: CustomEvent) => {
      const { view, path } = event.detail
      if (view) {
        setCurrentView(view as ContentView)
      }
      if (path) {
        setBreadcrumbs(path)
      }
    }

    window.addEventListener('navigate', handleNavigation as EventListener)
    return () => {
      window.removeEventListener('navigate', handleNavigation as EventListener)
    }
  }, [])

  const renderContent = () => {
    switch (currentView) {
      case "knowledge-base-list":
        return <KnowledgeBaseList />
      case "knowledge-base-config":
        return <KnowledgeBaseConfig />
      case "document-processing":
        return <DocumentProcessing />
      case "document-embedding":
        return <DocumentEmbeddingView />
      case "document-tokenization":
        return <DocumentTokenizationView />
      case "index-writing":
        return <IndexWritingView />

      case "retrieval":
        return <RetrievalView />
      case "generation-test":
        return <GenerationTestView />
      case "test-set-management":
        return <TestSetManagementView />
      case "evaluation-history":
        return <EvaluationHistoryView />
      case "evaluation-tasks":
        return <EvaluationTasksView />
      case "dashboard":
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Top Header Row - Unified */}
      <div className="flex border-b border-gray-200 shrink-0 items-stretch">
        <div className="w-64 bg-white border-r border-gray-200 px-6 py-4 flex items-center min-h-[73px]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">RAG</span>
            </div>
            <h1 className="text-lg font-bold text-gray-900">RAG Studio</h1>
          </div>
        </div>
        <div className="flex-1">
          <Header breadcrumbs={breadcrumbs} />
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar onNavigate={handleNavigate} currentView={currentView} />
        <main className="flex-1 overflow-auto bg-background p-6">{renderContent()}</main>
      </div>
    </div>
  )
}