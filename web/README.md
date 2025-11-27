This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### 环境变量配置

在运行项目之前，需要配置 API 基础 URL：

#### 开发环境

1. **创建 `.env.local` 文件**（在 `web` 目录下）：
```bash
# 推荐使用 API_BASE_URL（运行时配置）
API_BASE_URL=http://localhost:8000/api/v1

# 或者使用 NEXT_PUBLIC_API_URL（向后兼容）
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

#### 生产环境（容器部署）

**运行时配置（推荐）**：
- 使用 `API_BASE_URL` 环境变量，在容器启动时注入
- **优势**：无需重新构建镜像，同一镜像可用于不同环境
- **示例**：
  ```bash
  docker run -e API_BASE_URL=http://api.example.com/api/v1 ...
  ```

**构建时配置（向后兼容）**：
- 使用 `NEXT_PUBLIC_API_URL` 环境变量
- 需要在构建时设置，修改后需重新构建

#### 配置优先级

1. `window.__APP_CONFIG__.API_BASE_URL`（运行时注入，容器环境变量）
2. `process.env.NEXT_PUBLIC_API_URL`（构建时环境变量，向后兼容）
3. 默认值：`http://localhost:8000/api/v1`

#### 生命周期说明

- **运行时获取**：配置在容器启动时通过环境变量注入到 HTML 中
- **无需重新构建**：修改环境变量后重启容器即可生效
- **适合容器化部署**：同一镜像可以在不同环境使用不同配置

### 运行开发服务器

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
