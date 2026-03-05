# 🚀 部署到Render完整指南

## 📋 前置准备

### 1. 确保模型文件在仓库中

**重要：** 确保以下文件在Git仓库中：

```
models/detector_yolo/detector_yolov8s_best.pt  (YOLO模型)
data/ocr_train/code/models/best_accuracy.pdparams  (OCR模型)
data/ocr_train/code/config.yml  (OCR配置)
PaddleOCR/  (PaddleOCR源码目录)
```

**如果模型文件太大（>100MB）：**
- GitHub免费账户限制单个文件100MB
- 如果超过，需要：
  1. 使用Git LFS（Large File Storage）
  2. 或者部署后手动上传模型文件到Render

### 2. 检查requirements_server.txt

根据你的模型训练版本选择：

- **如果模型用numpy 2.0训练**：使用 `requirements_server.txt`（当前）
- **如果模型用numpy 1.x训练**：将 `requirements_server_numpy1.txt` 重命名为 `requirements_server.txt`

## 🔧 步骤1：提交代码到GitHub

### 1.1 检查Git状态

```bash
git status
```

### 1.2 添加文件

```bash
# 添加server目录
git add server/

# 添加必要的项目文件
git add .gitignore
git add colab_train_code_ocr.ipynb

# 如果模型文件在仓库中，添加它们
git add models/
git add data/ocr_train/
git add PaddleOCR/
```

### 1.3 提交

```bash
git commit -m "Add OCR API server for Render deployment"
```

### 1.4 推送到GitHub

```bash
# 如果还没有远程仓库，先添加
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 推送到GitHub
git push -u origin main
```

## 🌐 步骤2：在Render部署

### 2.1 登录Render

1. 访问 [Render](https://render.com)
2. 使用GitHub账号登录
3. 授权Render访问你的GitHub仓库

### 2.2 创建Web Service

1. 点击 **"New"** → **"Web Service"**
2. 选择你的GitHub仓库
3. 选择分支（通常是 `main`）

### 2.3 配置服务

**基本设置：**
- **Name**: `tcg-ocr-api`（或你喜欢的名字）
- **Environment**: `Python 3`
- **Region**: 选择离你最近的区域（如 `Singapore` 或 `Oregon`）

**构建和启动命令：**

Render会自动读取 `server/render.yaml`，但也可以手动设置：

- **Build Command**: `cd server && pip install -r requirements_server.txt`
- **Start Command**: `cd server && python server.py`

**Plan选择：**
- **Free**: 适合测试（有休眠限制）
- **Starter ($7/月)**: 推荐，无休眠，512MB RAM
- **Standard ($25/月)**: 如果需要更多资源

### 2.4 环境变量（可选）

Render会自动从 `render.yaml` 读取环境变量，但也可以手动添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `PORT` | `8000` | Render会自动设置，无需修改 |
| `MAX_WORKERS` | `4` | 并发处理线程数 |
| `MAX_QUEUE_SIZE` | `100` | 队列最大长度 |
| `USE_GPU` | `false` | Render不支持GPU，设为false |

### 2.5 部署

1. 点击 **"Create Web Service"**
2. Render会自动：
   - 克隆代码
   - 安装依赖
   - 启动服务

### 2.6 查看日志

部署过程中，在Render Dashboard查看 **"Logs"** 标签页：

**成功标志：**
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
[INFO] 开始加载模型...
[INFO] ✅ YOLO模型加载成功
[INFO] ✅ OCR模型加载完成
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

**如果看到错误：**
- 检查模型文件路径是否正确
- 检查依赖是否安装成功
- 查看完整错误日志

## ✅ 步骤3：测试部署

### 3.1 获取服务URL

部署成功后，Render会提供一个URL，例如：
```
https://tcg-ocr-api.onrender.com
```

### 3.2 健康检查

```bash
curl https://tcg-ocr-api.onrender.com/health
```

应该返回：
```json
{
  "status": "ok",
  "models_loaded": true,
  "queue_size": 0,
  "max_queue_size": 100,
  "active_workers": 4
}
```

### 3.3 测试OCR

```bash
curl -X POST "https://tcg-ocr-api.onrender.com/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_image.jpg"
```

## 🔍 常见问题

### Q1: 模型文件太大，无法上传到GitHub

**解决方案：**
1. 使用Git LFS：
   ```bash
   git lfs install
   git lfs track "*.pdparams"
   git lfs track "*.pt"
   git add .gitattributes
   git commit -m "Add Git LFS for model files"
   ```

2. 或者部署后手动上传：
   - 使用Render的持久化磁盘
   - 或使用云存储（S3等）并在启动时下载

### Q2: 部署失败，找不到模型文件

**检查：**
1. 确认模型文件在Git仓库中
2. 检查文件路径是否正确
3. 查看Render日志中的错误信息

### Q3: 依赖安装失败

**解决方案：**
1. 检查 `requirements_server.txt` 中的版本
2. 确保所有依赖都兼容
3. 查看构建日志中的具体错误

### Q4: 服务启动后立即崩溃

**可能原因：**
1. 模型文件路径错误
2. 依赖版本不兼容
3. 内存不足（Free plan只有512MB）

**解决方案：**
1. 检查日志中的错误信息
2. 升级到Starter plan（更多内存）
3. 优化模型加载（延迟加载等）

### Q5: 服务休眠（Free plan）

Free plan的服务在15分钟无活动后会休眠。

**解决方案：**
1. 升级到Starter plan（$7/月，无休眠）
2. 或使用外部监控服务定期ping你的API

## 📝 更新部署

每次推送代码到GitHub，Render会自动重新部署：

```bash
git add .
git commit -m "Update server code"
git push
```

Render会自动检测并重新部署。

## 🎯 下一步

部署成功后：
1. 保存服务URL
2. 在Flutter APP中使用此URL
3. 监控服务性能和错误日志
4. 根据需要调整配置（workers数量等）

## 📞 获取帮助

如果遇到问题：
1. 查看Render Dashboard的日志
2. 检查 `server/DEPLOYMENT_GUIDE.md`
3. 查看 `server/LOCAL_VS_RENDER.md` 了解环境差异
