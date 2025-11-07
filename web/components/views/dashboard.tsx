export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">欢迎使用 RAG Studio</h1>
        <p className="text-gray-600 mt-2">开始管理您的知识库和检索增强系统</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { title: "知识库总数", value: "12", color: "bg-blue-50 text-blue-700" },
          { title: "文档处理中", value: "3", color: "bg-amber-50 text-amber-700" },
          { title: "系统运行状态", value: "正常", color: "bg-green-50 text-green-700" },
        ].map((item, index) => (
          <div key={index} className={`rounded-lg p-6 ${item.color}`}>
            <p className="text-sm font-medium opacity-75">{item.title}</p>
            <p className="text-2xl font-bold mt-2">{item.value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
