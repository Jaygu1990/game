# 重新训练OCR模型指南

## ✅ 只需要重新训练OCR模型

**YOLO模型不需要重新训练**，因为：
- YOLO模型是`.pt`格式（PyTorch格式）
- 不依赖numpy版本
- 当前YOLO模型工作正常

**只需要重新训练OCR模型**，因为：
- OCR模型是`.pdparams`格式（PaddlePaddle格式）
- 当前模型用numpy 2.0训练，无法在numpy 1.x环境加载

## 📋 训练步骤

### 1. 打开Colab Notebook

打开 `colab_train_code_ocr.ipynb`（已修改，确保使用numpy 1.x）

### 2. 检查Cell 2（安装依赖）

应该显示：
```python
# ⚠️ 重要：先确保使用numpy 1.x（避免模型加载问题）
!pip install "numpy<2.0.0" --force-reinstall -q

# 验证numpy版本
import numpy as np
print(f"✅ NumPy版本: {np.__version__}")
if not np.__version__.startswith('1.'):
    raise RuntimeError(f"❌ 错误：必须使用numpy 1.x，当前版本: {np.__version__}")

# 安装PaddleOCR
!pip install paddlepaddle-gpu -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple -q
!pip install imgaug -i https://pypi.tuna.tsinghua.edu.cn/simple -q

print("✅ 所有依赖安装完成")
```

### 3. 运行所有Cell

按照notebook的顺序运行所有cell：
1. ✅ Cell 1: 安装依赖（已修改，使用numpy 1.x）
2. ✅ Cell 2: 上传数据
3. ✅ Cell 3: 准备训练数据
4. ✅ Cell 4: 开始训练
5. ✅ Cell 5: 下载模型

### 4. 验证numpy版本

运行Cell 1后，应该看到：
```
✅ NumPy版本: 1.26.4
✅ 所有依赖安装完成
```

如果看到numpy 2.x，说明安装失败，需要重新运行Cell 1。

### 5. 下载训练好的模型

训练完成后，下载 `best_accuracy.pdparams` 文件。

### 6. 替换本地模型

将下载的模型文件替换到：
```
data/ocr_train/code/models/best_accuracy.pdparams
```

## 🎯 训练时间

根据之前的训练记录：
- **训练时间**：约1-2小时（取决于epochs和GPU）
- **但可以永久解决numpy兼容性问题**

## ✅ 训练后的优势

训练完成后，本地环境：
- ✅ 不需要升级任何包
- ✅ 不需要修改代码
- ✅ 不需要处理DLL问题
- ✅ 直接使用，完全兼容

## 📝 注意事项

1. **确保numpy版本是1.x**：训练前必须验证
2. **使用相同的配置**：字符字典、use_space_char等配置保持一致
3. **保存训练日志**：方便后续调试

## 🔍 验证训练结果

训练完成后，在本地测试：
```bash
python test_single_image_code.py
```

应该能正常加载模型并识别。
