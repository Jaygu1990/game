# 修复 "Numpy is not available" 错误

## 问题

服务器返回错误：`Numpy is not available`

## 原因

这个错误通常来自YOLO/ultralytics，当它检测到numpy不可用或版本不匹配时会出现。

## 解决方案

### 步骤1：检查服务器运行环境

```bash
# 在TCG环境中运行
python server/check_server_env.py
```

### 步骤2：确保TCG环境有numpy 2.0

```bash
# 激活TCG环境（如果还没激活）
conda activate tcg

# 检查numpy版本
python -c "import numpy; print(numpy.__version__)"

# 如果不是2.0，升级
pip install "numpy>=2.0.0" --upgrade --force-reinstall
```

### 步骤3：升级所有相关依赖

```bash
# 在TCG环境中
pip install opencv-python shapely scikit-image matplotlib scipy pandas pyarrow numexpr bottleneck --upgrade --force-reinstall
```

### 步骤4：重新启动服务器

```bash
# 确保在TCG环境中
conda activate tcg

# 启动服务器
python server/server.py
```

### 步骤5：验证

在另一个终端测试：

```bash
# 可以在任何环境（只需要requests）
python server/example_client.py --image data/sample.jpg
```

## 快速修复脚本

如果问题持续，运行：

```bash
# 在TCG环境中
conda activate tcg

# 运行修复脚本
python -c "
import subprocess
import sys

packages = [
    'numpy>=2.0.0',
    'opencv-python',
    'shapely',
    'scikit-image',
    'matplotlib',
    'scipy',
    'pandas',
    'pyarrow',
    'numexpr',
    'bottleneck'
]

for pkg in packages:
    print(f'升级 {pkg}...')
    subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '--upgrade', '--force-reinstall'])
"
```

## 检查清单

- [ ] TCG环境已激活
- [ ] numpy版本 >= 2.0.0
- [ ] 所有依赖包已升级
- [ ] 服务器在TCG环境中启动
- [ ] 服务器日志显示模型加载成功

## 如果仍然失败

1. 查看服务器启动日志，找到具体错误
2. 检查是否有其他Python环境干扰
3. 尝试创建新的conda环境专门用于服务器
