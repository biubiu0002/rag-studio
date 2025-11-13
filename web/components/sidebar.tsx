"use client"

import { useState } from "react"
import { ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface SidebarProps {
  onNavigate: (view: string, path: string[]) => void
  currentView: string
}

interface MenuItem {
  id: string
  label: string
  icon?: string
  children?: MenuItem[]
}

const MENU_ITEMS: MenuItem[] = [
  {
    id: "knowledge-base",
    label: "知识库管理",
    children: [
      { id: "knowledge-base-list", label: "知识库列表" },
    ],
  },
  {
    id: "pipeline",
    label: "链路调试",
    children: [
      { id: "knowledge-base-config", label: "知识库配置" },
      { id: "document-processing", label: "文档处理" },
      { id: "document-embedding", label: "文档嵌入" },
      { id: "document-tokenization", label: "文档分词" },
      { id: "index-writing", label: "索引写入" },
      { id: "retrieval", label: "检索" },
      { id: "generation-test", label: "生成" },
    ],
  },
  {
    id: "test-management",
    label: "测试管理",
    children: [
      { id: "test-set-management", label: "测试集" },
      { id: "evaluation-tasks", label: "评估任务" },
    ],
  },
]

export default function Sidebar({ onNavigate, currentView }: SidebarProps) {
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(
    new Set(["knowledge-base", "pipeline", "test-management"]),
  )

  const toggleMenu = (menuId: string) => {
    const newExpanded = new Set(expandedMenus)
    if (newExpanded.has(menuId)) {
      newExpanded.delete(menuId)
    } else {
      newExpanded.add(menuId)
    }
    setExpandedMenus(newExpanded)
  }

  const handleMenuItemClick = (itemId: string, label: string) => {
    onNavigate(itemId, ["RAG Studio", label])
  }

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col overflow-y-auto">
      {/* Menu Items */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {MENU_ITEMS.map((menuItem) => (
          <div key={menuItem.id}>
            {/* First Level Menu */}
            <button
              onClick={() => toggleMenu(menuItem.id)}
              className={cn(
                "w-full px-3 py-2 rounded-md flex items-center justify-between text-sm font-medium transition-colors",
                "text-gray-700 hover:bg-gray-100",
              )}
            >
              <span>{menuItem.label}</span>
              <ChevronDown
                size={16}
                className={cn("transition-transform", expandedMenus.has(menuItem.id) && "rotate-180")}
              />
            </button>

            {/* Second Level Menu */}
            {expandedMenus.has(menuItem.id) && menuItem.children && (
              <div className="mt-1 ml-2 space-y-1">
                {menuItem.children.map((child) => (
                  <button
                    key={child.id}
                    onClick={() => handleMenuItemClick(child.id, child.label)}
                    className={cn(
                      "w-full px-3 py-2 rounded-md text-sm text-left transition-colors border-l-2",
                      currentView === child.id
                        ? "bg-blue-50 text-blue-700 border-l-blue-600"
                        : "text-gray-700 border-l-transparent hover:bg-gray-50",
                    )}
                  >
                    {child.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  )
}
