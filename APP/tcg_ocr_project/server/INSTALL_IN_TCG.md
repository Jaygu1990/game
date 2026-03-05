# 在TCG环境中安装服务器依赖

## 问题

在TCG环境中运行服务器时提示：`ModuleNotFoundError: No module named 'fastapi'`

## 解决方案

### 方法1：直接安装（推荐）

```bash
# 确保在TCG环境中（提示符应该显示 (TCG)）
conda activate tcg

# 安装服务器依赖
pip install -r server/requirements_server.txt
```

### 方法2：如果pip安装到错误的环境

```bash
# 确保在TCG环境中
conda activate tcg

# 使用python -m pip确保使用当前环境的pip
python -m pip install -r server/requirements_server.txt
```

### 方法3：检查环境

```bash
# 检查当前Python路径
python -c "import sys; print(sys.executable)"

# 应该显示类似：
# D:\Anaconda3\envs\tcg\python.exe
# 而不是：
# D:\Anaconda3\python.exe
```

### 验证安装

```bash
# 在TCG环境中
python -c "import fastapi; print('fastapi版本:', fastapi.__version__)"
```

如果成功，应该显示fastapi版本号。

### 启动服务器

```bash
# 确保在TCG环境中
conda activate tcg

# 启动服务器
python server/server.py
```

## 如果仍然失败

1. **确认环境激活**：
   ```bash
   conda info --envs  # 查看所有环境
   conda activate tcg  # 激活TCG环境
   ```

2. **检查Python路径**：
   ```bash
   which python  # Linux/Mac
   where python  # Windows
   ```

3. **手动安装fastapi**：
   ```bash
   python -m pip install fastapi uvicorn python-multipart
   ```
