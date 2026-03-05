# Render部署指南

## 📦 文件清单

server文件夹包含以下文件：

```
server/
├── server.py                 # FastAPI服务器主文件
├── requirements_server.txt    # Python依赖包
├── render.yaml               # Render部署配置
├── Procfile                  # Render启动命令（可选）
├── test_api.py               # API测试脚本
├── README.md                 # 详细说明文档
├── DEPLOYMENT_GUIDE.md       # 本部署指南
└── .gitignore               # Git忽略文件
```

## 🚀 快速部署步骤

### 1. 准备Git仓库

```bash
# 确保所有文件都在Git仓库中
git add server/
git commit -m "Add API server for Render deployment"
git push
```

### 2. 在Render创建服务

1. 登录 [Render](https://render.com)
2. 点击 "New" -> "Web Service"
3. 连接你的Git仓库
4. 选择仓库和分支

### 3. 配置服务

**基本配置：**
- **Name**: `tcg-ocr-api`
- **Environment**: `Python 3`
- **Region**: 选择离你最近的区域（如 `Singapore`）

**构建和启动命令：**
- **Build Command**: `cd server && pip install -r requirements_server.txt`
- **Start Command**: `cd server && python server.py`

**或者使用render.yaml（推荐）：**
- Render会自动读取 `render.yaml` 配置
- 无需手动设置，只需确认配置正确

### 4. 环境变量（可选）

如果render.yaml中的配置不够，可以手动添加：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | 8000 | Render会自动设置，无需修改 |
| `MAX_WORKERS` | 4 | 并发处理线程数 |
| `MAX_QUEUE_SIZE` | 100 | 队列最大长度 |
| `REQUEST_TIMEOUT` | 60 | 单个请求超时时间（秒） |
| `QUEUE_WAIT_TIMEOUT` | 300 | 队列等待超时（秒） |
| `USE_GPU` | false | 是否使用GPU |
| `UVICORN_WORKERS` | 1 | Uvicorn worker数量 |

### 5. 部署

点击 "Create Web Service"，Render会自动：
1. 构建环境
2. 安装依赖
3. 启动服务

**首次部署可能需要5-10分钟**（包括模型加载时间）

## ✅ 验证部署

### 1. 检查服务状态

在Render Dashboard查看服务状态，应该显示 "Live"

### 2. 测试健康检查

```bash
curl https://your-service-name.onrender.com/health
```

应该返回JSON响应，包含服务状态信息。

### 3. 测试OCR接口

```bash
curl -X POST "https://your-service-name.onrender.com/ocr" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/image.jpg"
```

### 4. 使用测试脚本

```bash
cd server
python test_api.py --url https://your-service-name.onrender.com --image ../data/sample.jpg
```

## 🔧 常见问题

### Q: 模型文件太大，Git仓库放不下？

**A:** 有几种解决方案：

1. **使用Git LFS**（推荐）：
   ```bash
   git lfs install
   git lfs track "*.pdparams"
   git lfs track "*.pt"
   git add .gitattributes
   git add models/
   git commit -m "Add model files with LFS"
   ```

2. **上传到云存储**：
   - 将模型文件上传到AWS S3、Google Cloud Storage等
   - 在启动时下载模型文件
   - 修改 `server.py` 的 `load_models()` 函数

3. **使用Render的持久化磁盘**：
   - Render的Standard套餐支持持久化磁盘
   - 将模型文件放在持久化磁盘上

### Q: 内存不足？

**A:** 
- Render免费套餐内存有限（512MB）
- 建议升级到Starter套餐（512MB-2GB）或Standard套餐（2GB+）
- 模型加载需要约500MB-1GB内存

### Q: 启动时间太长？

**A:**
- 首次启动需要加载模型，可能需要1-2分钟
- Render会在服务无请求15分钟后休眠（免费套餐）
- 休眠后首次请求需要重新启动，可能需要30秒-1分钟
- 升级到付费套餐可以避免自动休眠

### Q: 如何查看日志？

**A:**
- 在Render Dashboard点击服务名称
- 点击 "Logs" 标签页
- 可以看到实时日志和错误信息

### Q: 如何更新代码？

**A:**
- 推送代码到Git仓库
- Render会自动检测并重新部署
- 或者在Dashboard点击 "Manual Deploy"

## 📊 性能优化

### 1. 增加Workers

如果并发请求多，增加 `MAX_WORKERS`：

```yaml
envVars:
  - key: MAX_WORKERS
    value: 8
```

### 2. 使用GPU（如果可用）

如果Render支持GPU（需要联系客服）：

```yaml
envVars:
  - key: USE_GPU
    value: true
```

### 3. 调整队列大小

如果请求量大，增加 `MAX_QUEUE_SIZE`：

```yaml
envVars:
  - key: MAX_QUEUE_SIZE
    value: 200
```

### 4. 监控性能

定期查看 `/health` 接口的统计信息：
- `queue_size`: 当前队列大小
- `max_queue_size_reached`: 历史最大队列大小
- `successful_requests`: 成功请求数
- `failed_requests`: 失败请求数

## 💰 成本估算

### Render免费套餐：
- ✅ 免费
- ⚠️ 服务会在15分钟无请求后休眠
- ⚠️ 内存限制512MB（可能不够）

### Render Starter套餐：
- 💰 约 $7/月
- ✅ 不休眠
- ✅ 512MB-2GB内存
- ✅ 适合中小型应用

### Render Standard套餐：
- 💰 约 $25/月
- ✅ 不休眠
- ✅ 2GB+内存
- ✅ 支持持久化磁盘
- ✅ 适合中大型应用

## 📝 注意事项

1. **模型文件路径**：确保模型文件路径正确，`server.py` 中使用的是相对路径
2. **CORS设置**：当前允许所有来源，生产环境建议限制具体域名
3. **文件大小限制**：当前限制10MB，可在代码中修改
4. **超时设置**：根据实际需求调整 `REQUEST_TIMEOUT` 和 `QUEUE_WAIT_TIMEOUT`
5. **日志级别**：生产环境建议设置为 `WARNING` 或 `ERROR`

## 🆘 获取帮助

如果遇到问题：
1. 查看Render Dashboard的日志
2. 检查模型文件是否存在
3. 验证环境变量配置
4. 查看 `README.md` 中的详细说明
