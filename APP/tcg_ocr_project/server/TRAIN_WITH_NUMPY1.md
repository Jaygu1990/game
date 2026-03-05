# 用numpy 1.x重新训练模型（最简单方案）

## 快速修改Colab训练notebook

### 修改第2个Cell（安装依赖）

**原来的代码：**
```python
# 安装PaddleOCR
!pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install imgaug -i https://pypi.tuna.tsinghua.edu.cn/simple -q
```

**修改为：**
```python
# ⚠️ 重要：先确保使用numpy 1.x
!pip install "numpy<2.0.0" --force-reinstall -q

# 验证numpy版本
import numpy as np
print(f"✅ NumPy版本: {np.__version__}")
assert np.__version__.startswith('1.'), f"错误：必须使用numpy 1.x，当前版本: {np.__version__}"

# 安装PaddleOCR
!pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install imgaug -i https://pypi.tuna.tsinghua.edu.cn/simple -q
```

### 完整修改后的Cell

```python
## 1. 安装依赖

# ⚠️ 重要：先确保使用numpy 1.x（避免模型加载问题）
!pip install "numpy<2.0.0" --force-reinstall -q

# 验证numpy版本
import numpy as np
print(f"✅ NumPy版本: {np.__version__}")
if not np.__version__.startswith('1.'):
    raise RuntimeError(f"错误：必须使用numpy 1.x，当前版本: {np.__version__}")

# 安装PaddleOCR
!pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install imgaug -i https://pypi.tuna.tsinghua.edu.cn/simple -q

print("✅ 所有依赖安装完成")
```

## 训练步骤

1. **打开Colab notebook**
2. **修改第2个Cell**（如上所示）
3. **运行所有Cell**（正常训练流程）
4. **下载训练好的模型**（`best_accuracy.pdparams`）
5. **替换本地模型文件**

## 训练后

训练完成后，本地环境不需要任何修改：
- ✅ numpy 1.26.4（已安装，兼容）
- ✅ opencv-python（已安装，兼容）
- ✅ torch（不需要升级）
- ✅ 所有依赖都兼容

## 优势

- ✅ **一次训练，永久解决**
- ✅ **避免所有环境问题**
- ✅ **部署更简单**
- ✅ **不需要调试DLL问题**

## 训练时间

根据之前的训练记录：
- **训练时间**：约1-2小时（取决于epochs）
- **但可以避免数小时的调试时间**
