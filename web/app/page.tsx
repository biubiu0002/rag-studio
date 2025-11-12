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
import RetrieverEvaluationView from "@/components/views/retriever-evaluation"
import TestSetManagementView from "@/components/views/test-set-management"
import TestCaseManagementView from "@/components/views/test-case-management"
import GeneratorEvaluationView from "@/components/views/generator-evaluation"
import EvaluationHistoryView from "@/components/views/evaluation-history"
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
  | "test-case-management"
  | "retriever-evaluation"
  | "generator-evaluation"
  | "evaluation-history"

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
      case "test-case-management":
        return <TestCaseManagementView />
      case "retriever-evaluation":
        return <RetrieverEvaluationView />
      case "generator-evaluation":
        return <GeneratorEvaluationView />
      case "evaluation-history":
        return <EvaluationHistoryView />
      case "dashboard":
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar onNavigate={handleNavigate} currentView={currentView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header breadcrumbs={breadcrumbs} />
        <main className="flex-1 overflow-auto bg-background p-6">{renderContent()}</main>
      </div>
    </div>
  )
}