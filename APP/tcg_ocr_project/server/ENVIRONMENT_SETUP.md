# 服务器环境设置指南

## 问题

错误 "Numpy is not available" 通常是因为：
1. 服务器和客户端运行在不同的Python环境中
2. 服务器环境缺少numpy或numpy版本不匹配

## 解决方案

### 方案1：在TCG环境中运行服务器（推荐）

如果TCG环境有numpy 1.26.4，需要升级到numpy 2.0以匹配模型：

```bash
# 激活TCG环境
conda activate tcg

# 升级numpy到2.0
pip install "numpy>=2.0.0" --upgrade

# 升级其他依赖
pip install opencv-python shapely scikit-image matplotlib scipy pandas --upgrade

# 启动服务器
python server/server.py
```

### 方案2：在base环境中运行服务器

如果base环境已经有numpy 2.0：

```bash
# 退出TCG环境（如果已激活）
conda deactivate

# 启动服务器
python server/server.py
```

### 方案3：创建专用服务器环境

```bash
# 创建新环境
conda create -n ocr_server python=3.11

# 激活环境
conda activate ocr_server

# 安装依赖
cd server
pip install -r requirements_server.txt

# 启动服务器
python server.py
```

## 检查环境

运行检查脚本：

```bash
python server/check_server_env.py
```

应该显示：
- ✅ numpy版本: 2.x.x
- ✅ 所有依赖包正常

## 验证

1. 确保服务器在正确的环境中运行
2. 检查服务器日志，确认模型加载成功
3. 使用客户端测试：

```bash
python server/example_client.py --image data/sample.jpg
```

## 常见问题

### Q: 如何知道服务器在哪个环境运行？

A: 查看服务器启动时的Python路径，或运行：
```bash
python server/check_server_env.py
```

### Q: 服务器和客户端必须在同一环境吗？

A: 不需要。服务器和客户端可以运行在不同的环境中，只要：
- 服务器环境有numpy 2.0和所有依赖
- 客户端只需要requests库

### Q: 如何确保服务器使用正确的环境？

A: 在启动服务器前，确保激活了正确的conda环境，或使用完整路径：
```bash
# 使用完整路径
D:\Anaconda3\envs\tcg\python.exe server/server.py
```
