# TCG OCR API Server

TCG卡片Code区域OCR识别API服务，支持多线程处理和请求排队。

## 📁 文件说明

- `server.py` - FastAPI服务器主文件
- `requirements_server.txt` - Python依赖包
- `render.yaml` - Render部署配置文件
- `Procfile` - Render启动命令（可选）
- `README.md` - 本说明文件

## 🚀 本地测试

### 1. 安装依赖

```bash
cd server
pip install -r requirements_server.txt
```

### 2. 确保模型文件存在

确保以下文件存在：
- `models/detector_yolo/detector_yolov8s_best.pt` (YOLO模型)
- `data/ocr_train/code/models/best_accuracy.pdparams` (OCR模型)
- `data/ocr_train/code/config.yml` (OCR配置)

### 3. 启动服务器

```bash
python server.py
```

服务器将在 `http://localhost:8000` 启动。

### 4. 测试API

#### 健康检查
```bash
curl http://localhost:8000/health
```

#### OCR识别（带排队）
```bash
curl -X POST "http://localhost:8000/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@../data/sample.jpg"
```

#### OCR识别（直接处理，不排队）
```bash
curl -X POST "http://localhost:8000/ocr-direct" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@../data/sample.jpg"
```

## 🌐 部署到Render

### 1. 准备工作

1. 将整个项目（包括`server`文件夹）推送到Git仓库
2. 确保模型文件也在仓库中（或通过其他方式上传到Render）

### 2. 在Render创建服务

1. 登录 [Render](https://render.com)
2. 点击 "New" -> "Web Service"
3. 连接你的Git仓库
4. 配置如下：
   - **Name**: `tcg-ocr-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r server/requirements_server.txt`
   - **Start Command**: `cd server && python server.py`
   - **Plan**: 选择适合的套餐（建议Starter或Standard）

### 3. 环境变量（可选，Render会自动读取render.yaml）

如果手动设置，添加以下环境变量：
- `PORT=8000` (Render会自动设置)
- `MAX_WORKERS=4` (并发处理线程数)
- `MAX_QUEUE_SIZE=100` (队列最大长度)
- `REQUEST_TIMEOUT=60` (单个请求超时时间，秒)
- `QUEUE_WAIT_TIMEOUT=300` (队列等待超时，秒)
- `USE_GPU=false` (是否使用GPU)
- `UVICORN_WORKERS=1` (Uvicorn worker数量，建议1个)

### 4. 部署

点击 "Create Web Service"，Render会自动构建和部署。

## ⚙️ 配置说明

### Workers数量（MAX_WORKERS）

**默认值：4**

**4个workers够用吗？**

- ✅ **对于中小型应用（<1000用户/天）**：4个workers通常足够
- ✅ **每个worker处理一个请求**：4个workers = 4个并发请求
- ✅ **如果单个请求处理时间约200-500ms**：
  - 4个workers每秒可处理 **8-20个请求**
  - 每天可处理 **69万-172万个请求**

**实际场景估算：**
- 假设每个用户每天使用10次，1000用户 = 10,000次/天
- 4个workers每秒处理10个请求 = 86.4万次/天
- **结论：4个workers对于1000用户完全够用**

**什么时候需要增加？**

- 如果请求处理时间较长（>1秒），考虑增加到 **8个workers**
- 如果并发请求数经常超过4个，考虑增加到 **8-16个workers**
- 如果用户数超过5000，考虑增加到 **8-16个workers**
- Render的Standard套餐通常支持更多workers

**如何调整？**

在Render的环境变量中设置 `MAX_WORKERS=8`（或你需要的数量）

### 队列机制

**队列满的定义：**
- 队列满 = `request_queue.qsize() >= MAX_QUEUE_SIZE`
- 默认 `MAX_QUEUE_SIZE=100`，即最多100个请求在队列中等待
- **注意**：队列大小 ≠ Workers数量
  - Workers数量（4）= 同时处理的请求数
  - 队列大小（100）= 等待处理的请求数

**等待机制：**
- ✅ **队列满时不会返回503**，而是**等待**直到有空位
- ✅ 最多等待 `QUEUE_WAIT_TIMEOUT` 秒（默认300秒=5分钟）
- ✅ 如果等待超时，才会返回503错误
- ✅ 使用信号量（Semaphore）自动管理并发，达到最大并发数时会自动等待

**队列工作流程：**
1. 请求到达 → 检查队列是否有空位（如果满则等待）
2. 放入队列占位符 → 等待Worker空闲（信号量控制）
3. Worker空闲 → 从队列取任务 → 处理图片
4. 处理完成 → 返回结果

**示例场景：**
- **正常情况**：
  - 4个workers正在处理4个请求
  - 第5个请求到达 → 立即获得信号量，开始处理（如果worker空闲）
  - 如果所有worker都忙 → 等待直到有worker空闲
  
- **高并发情况**：
  - 4个workers正在处理4个请求
  - 第5-104个请求到达 → 都在队列中等待（共100个）
  - 第105个请求到达 → 队列满，等待最多5分钟
  - 如果5分钟内队列仍满 → 返回503错误

**如何判断队列满？**
- 查看 `/health` 接口的 `queue_size` 字段
- 如果 `queue_size` 接近 `max_queue_size`（100），说明队列快满了
- 如果经常队列满，考虑：
  1. 增加 `MAX_WORKERS`（更多并发处理）
  2. 增加 `MAX_QUEUE_SIZE`（更大的队列）
  3. 优化处理速度（使用GPU等）

## 📊 API接口

### GET `/` 或 `/health`

健康检查，返回服务状态和统计信息。

**响应示例：**
```json
{
  "status": "ok",
  "models_loaded": true,
  "queue_size": 5,
  "max_queue_size": 100,
  "active_workers": 4,
  "stats": {
    "total_requests": 100,
    "successful_requests": 95,
    "failed_requests": 5,
    "current_queue_size": 5,
    "max_queue_size_reached": 10
  }
}
```

### POST `/ocr`

OCR识别接口（带排队和等待机制）。

**请求：**
- `file`: 图片文件（multipart/form-data）
- 最大文件大小：10MB

**响应示例：**
```json
{
  "success": true,
  "text": "088/063",
  "confidence": 0.95,
  "bbox": [100, 200, 300, 250],
  "processing_time": 0.35,
  "queue_wait_time": 0.12
}
```

### POST `/ocr-direct`

OCR识别接口（直接处理，不排队）。

适用于低并发场景或测试。

## 🔧 性能优化建议

1. **增加Workers**：如果并发高，增加 `MAX_WORKERS`
2. **调整队列大小**：如果请求量大，增加 `MAX_QUEUE_SIZE`
3. **使用GPU**：如果有GPU，设置 `USE_GPU=true`
4. **监控统计**：定期查看 `/health` 接口的统计信息

## 🐛 常见问题

### Q: 模型加载失败？

A: 确保模型文件路径正确，检查 `server.py` 中的路径配置。

### Q: 请求超时？

A: 增加 `REQUEST_TIMEOUT` 环境变量（默认60秒）。

### Q: 队列总是满？

A: 
1. 增加 `MAX_WORKERS`（更多并发处理）
2. 增加 `MAX_QUEUE_SIZE`（更大的队列）
3. 检查是否有请求处理时间过长

### Q: 内存不足？

A: Render的免费套餐内存有限，建议升级到Starter或Standard套餐。

## 📝 注意事项

1. **模型文件大小**：YOLO和OCR模型文件较大（几百MB），确保Render有足够空间
2. **启动时间**：首次启动需要加载模型，可能需要1-2分钟
3. **CORS**：当前允许所有来源，生产环境建议限制具体域名
4. **文件大小限制**：当前限制10MB，可在代码中修改
