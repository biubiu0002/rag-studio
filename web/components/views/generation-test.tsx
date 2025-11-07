import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function GenerationTestView() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">生成测试</h2>

      <Card className="p-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">输入提示</label>
            <textarea
              placeholder="输入生成提示..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
            />
          </div>

          <Button className="bg-blue-600 hover:bg-blue-700 w-full">执行生成测试</Button>
        </div>
      </Card>

      <Card className="p-6 bg-gray-50">
        <h3 className="font-semibold text-gray-900 mb-4">生成结果</h3>
        <div className="text-gray-600">
          <p className="text-sm">生成内容将在此显示...</p>
        </div>
      </Card>
    </div>
  )
}
