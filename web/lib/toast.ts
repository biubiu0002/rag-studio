import { toast } from "sonner"

/**
 * 显示成功提示
 */
export const showSuccess = (message: string) => {
  toast.success(message)
}

/**
 * 显示错误提示
 */
export const showError = (message: string) => {
  toast.error(message)
}

/**
 * 显示信息提示
 */
export const showInfo = (message: string) => {
  toast.info(message)
}

/**
 * 显示警告提示
 */
export const showWarning = (message: string) => {
  toast.warning(message)
}

/**
 * 统一的提示函数，根据消息类型自动选择样式
 * 如果消息包含"成功"、"完成"等关键词，使用成功样式
 * 如果消息包含"失败"、"错误"等关键词，使用错误样式
 * 否则使用信息样式
 */
export const showToast = (message: string, type?: "success" | "error" | "info" | "warning") => {
  if (type) {
    switch (type) {
      case "success":
        showSuccess(message)
        break
      case "error":
        showError(message)
        break
      case "warning":
        showWarning(message)
        break
      default:
        showInfo(message)
    }
    return
  }

  // 自动判断类型
  const lowerMessage = message.toLowerCase()
  if (lowerMessage.includes("成功") || lowerMessage.includes("完成") || lowerMessage.includes("已")) {
    showSuccess(message)
  } else if (lowerMessage.includes("失败") || lowerMessage.includes("错误") || lowerMessage.includes("无效")) {
    showError(message)
  } else if (lowerMessage.includes("警告") || lowerMessage.includes("注意")) {
    showWarning(message)
  } else {
    showInfo(message)
  }
}

