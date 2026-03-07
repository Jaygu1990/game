# Render 内存不足问题解决方案

## 🔴 问题

```
Instance failed: 8bn55
Ran out of memory (used over 512MB) while running your code.
```

**原因**：Render Free Plan 只有 **512MB 内存限制**

## 📊 内存使用分析

### 当前内存占用：
1. **PaddlePaddle 框架**：~150-200MB
2. **PyTorch (YOLO)**：~100-150MB
3. **OCR 模型加载**：~65MB（模型文件）+ ~100MB（运行时内存）
4. **YOLO 模型加载**：~50MB（模型文件）+ ~50MB（运行时内存）
5. **其他依赖**：~50-100MB

**总计**：约 **565-710MB**，超过 512MB 限制

### 模型文件大小：
- `best_accuracy.pdparams`: 65.67 MB
- `latest.pdopt`: 115.78 MB（优化器状态，**不需要加载**）
- `latest.pdparams`: 65.44 MB

## ✅ 解决方案

### 方案 1：优化内存使用（推荐先试）

#### 1.1 只加载必要的模型文件
- ✅ 只加载 `best_accuracy.pdparams`（65MB）
- ❌ 不加载 `latest.pdopt`（115MB，优化器状态，推理不需要）

#### 1.2 延迟加载模型
- 启动时不加载模型
- 首次请求时再加载（已有实现）

#### 1.3 减少并发线程数
- 将 `MAX_WORKERS` 从 4 降到 2

### 方案 2：升级到付费计划

Render 付费计划内存限制：
- **Starter Plan**: $7/月，512MB RAM（和 Free 一样）
- **Standard Plan**: $25/月，**2GB RAM** ✅ 推荐
- **Pro Plan**: $85/月，4GB RAM

## 🔧 立即优化（方案 1）

### 步骤 1：确保只加载 best_accuracy.pdparams

检查代码是否优先加载 `best_accuracy.pdparams`（已在代码中实现）

### 步骤 2：减少 MAX_WORKERS

在 `render.yaml` 中设置：
```yaml
envVars:
  - key: MAX_WORKERS
    value: 2  # 从 4 降到 2
```

### 步骤 3：优化 PaddlePaddle 内存使用

在模型加载时设置：
```python
# 设置 PaddlePaddle 使用更少内存
paddle.set_device('cpu')
# 禁用一些不必要的功能
os.environ['FLAGS_allocator_strategy'] = 'auto_growth'
```

## 📍 如何查看 Render 日志

### 方法 1：Render Dashboard
1. 登录 [Render Dashboard](https://dashboard.render.com)
2. 点击你的服务（`tcg-yolo-ocr-api`）
3. 点击 **"Logs"** 标签页
4. 查看实时日志和错误信息

### 方法 2：Events 页面
1. 在服务页面，点击 **"Events"** 标签页
2. 查看部署历史和错误信息
3. 点击失败的部署查看详细错误

### 方法 3：API 日志
在服务页面可以看到：
- **实时日志**：显示当前运行状态
- **历史日志**：查看之前的错误
- **内存使用**：如果升级到付费计划，可以看到内存使用图表

## 🚀 快速修复步骤

1. **检查日志**：在 Render Dashboard 查看详细错误
2. **减少 MAX_WORKERS**：修改 `render.yaml`
3. **重新部署**：推送更改
4. **如果仍然失败**：考虑升级到 Standard Plan（$25/月，2GB RAM）

## 💡 建议

对于深度学习模型服务：
- **Free Plan (512MB)**：通常不够用
- **Standard Plan (2GB)**：✅ 推荐，足够运行模型
- **Pro Plan (4GB)**：如果处理大量并发请求

## 📝 下一步

1. 先尝试优化（减少 MAX_WORKERS）
2. 如果还是失败，升级到 Standard Plan
3. 或者考虑使用其他平台（如 Railway、Fly.io 等）
