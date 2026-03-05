# NumPy版本问题快速修复指南

## 问题症状

如果遇到以下错误：
- `ModuleNotFoundError: No module named 'numpy._core'`
- `AttributeError: _ARRAY_API not found`
- `ImportError: numpy.core.multiarray failed to import`
- `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x`

## 快速修复

### 1. 检查当前numpy版本

```bash
python -c "import numpy; print(numpy.__version__)"
```

如果版本 >= 2.0.0，需要降级。

### 2. 降级numpy到1.x

```bash
python -m pip install "numpy<2.0.0" --force-reinstall --no-cache-dir
```

### 3. 重新安装opencv-python（如果需要）

```bash
python -m pip uninstall opencv-python opencv-python-headless -y
python -m pip install opencv-python==4.8.1.78 --no-cache-dir
```

### 4. 验证修复

```bash
python -c "import cv2; import numpy; print('opencv:', cv2.__version__); print('numpy:', numpy.__version__)"
```

应该显示：
- opencv: 4.8.1
- numpy: 1.x.x（< 2.0.0）

## 预防措施

### 在requirements_server.txt中

已设置：
```
numpy>=1.19.0,<2.0.0
```

### 安装依赖时

```bash
pip install -r requirements_server.txt
```

如果numpy仍然升级到2.x，手动降级：
```bash
pip install "numpy<2.0.0" --force-reinstall
```

## 为什么需要numpy < 2.0？

1. **paddlepaddle兼容性**：paddlepaddle 2.6.2需要numpy 1.x
2. **opencv-python兼容性**：opencv-python 4.8.1.78用numpy 1.x编译
3. **模型文件兼容性**：如果模型用numpy 1.x训练，需要用numpy 1.x加载

## 部署到Render时

确保在`render.yaml`或环境变量中明确指定numpy版本：

```yaml
envVars:
  - key: NUMPY_VERSION
    value: "<2.0.0"
```

或在构建命令中：
```bash
pip install -r requirements_server.txt && pip install "numpy<2.0.0" --force-reinstall
```
