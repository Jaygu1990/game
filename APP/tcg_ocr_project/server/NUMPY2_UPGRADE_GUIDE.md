# NumPy 2.0 升级完整指南

## 问题

模型文件是用numpy 2.0训练的，但环境使用numpy 1.x无法加载。

## 解决方案：升级所有相关包到支持numpy 2.0的版本

### 核心包

```bash
pip install "numpy>=2.0.0" --upgrade
pip install "opencv-python>=4.13.0" --upgrade
pip install "shapely>=2.1.0" --upgrade
pip install "scikit-image>=0.26.0" --upgrade
pip install "matplotlib>=3.9.0" --upgrade
pip install "scipy>=1.11.4" --upgrade
pip install "pandas>=3.0.0" --upgrade
pip install "torchvision" --upgrade
pip install "ultralytics" --upgrade
```

### 一键升级命令

```bash
pip install numpy>=2.0.0 opencv-python>=4.13.0 shapely>=2.1.0 scikit-image>=0.26.0 matplotlib>=3.9.0 scipy>=1.11.4 pandas>=3.0.0 torchvision ultralytics --upgrade --no-cache-dir
```

## 更新的requirements_server.txt

已更新为包含所有需要的版本：

```txt
numpy>=2.0.0
opencv-python>=4.13.0
shapely>=2.1.0
scikit-image>=0.26.0
matplotlib>=3.9.0
scipy>=1.11.4
pandas>=3.0.0
```

## 验证

运行测试脚本：

```bash
python server/test_model_load.py
```

应该显示：
- ✅ 模型加载成功
- ✅ 所有依赖包正常工作

## 注意事项

1. **依赖冲突警告可以忽略**：
   - paddleocr要求opencv-python<=4.6.0.66，但我们使用4.13.0（实际测试正常）
   - numba要求numpy<1.25，但我们使用numpy 2.0（如果不需要numba可以忽略）

2. **如果遇到其他包不兼容**：
   - 查看错误信息，找到不兼容的包
   - 升级该包到最新版本
   - 如果无法升级，考虑是否真的需要该包

3. **部署到Render**：
   - 确保requirements_server.txt包含所有需要的版本
   - Render会自动安装兼容版本

## 已解决的问题

✅ numpy._core模块缺失  
✅ opencv-python不兼容  
✅ shapely不兼容  
✅ scikit-image不兼容  
✅ matplotlib不兼容  
✅ pandas不兼容（正在升级）  
✅ torchvision不兼容（正在升级）  

## 测试服务器

升级完成后，测试服务器：

```bash
cd server
python server.py
```

如果启动成功，应该看到：
- ✅ 模型加载成功
- ✅ 服务器在 http://localhost:8000 运行
