# 🚀 快速部署到Render

## 步骤1：提交代码到GitHub

### 1. 添加必要文件

```bash
# 添加server目录（已添加）
git add server/

# 添加模型文件（如果存在）
git add models/
git add data/ocr_train/
git add PaddleOCR/

# 添加其他必要文件
git add .gitignore
git add colab_train_code_ocr.ipynb
git add DEPLOY_CHECKLIST.md
```

### 2. 提交

```bash
git commit -m "Add OCR API server for Render deployment"
```

### 3. 推送到GitHub

```bash
# 如果还没有远程仓库
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送到GitHub
git push -u origin main
```

## 步骤2：在Render部署

### 1. 登录Render
访问 [https://render.com](https://render.com)，用GitHub账号登录

### 2. 创建Web Service
1. 点击 **"New"** → **"Web Service"**
2. 选择你的GitHub仓库
3. 选择分支 `main`

### 3. 配置（Render会自动读取render.yaml）
- **Name**: `tcg-ocr-api`
- **Environment**: `Python 3`
- **Region**: 选择最近的（如 `Singapore`）

### 4. Plan选择
- **Free**: 测试用（会休眠）
- **Starter ($7/月)**: 推荐，无休眠

### 5. 点击 "Create Web Service"

Render会自动：
- 安装依赖
- 启动服务
- 提供URL

## 步骤3：测试

部署成功后，你会得到一个URL，例如：
```
https://tcg-ocr-api.onrender.com
```

### 健康检查
```bash
curl https://tcg-ocr-api.onrender.com/health
```

### 测试OCR
```bash
curl -X POST "https://tcg-ocr-api.onrender.com/ocr" \
  -F "file=@your_image.jpg"
```

## ⚠️ 重要提示

1. **模型文件大小**：如果模型文件>100MB，GitHub可能拒绝。考虑使用Git LFS
2. **首次部署**：可能需要5-10分钟
3. **Free Plan**：15分钟无活动会休眠，首次访问会慢
4. **查看日志**：在Render Dashboard的"Logs"标签页查看部署进度

## 📄 详细文档

- 完整部署指南：`server/DEPLOY_TO_RENDER.md`
- 检查清单：`DEPLOY_CHECKLIST.md`
