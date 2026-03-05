"""
检查服务器运行环境
"""

import sys
import os

print("=" * 70)
print("服务器环境检查")
print("=" * 70)
print(f"Python路径: {sys.executable}")
print(f"Python版本: {sys.version}")
print()

# 检查numpy
try:
    import numpy as np
    print(f"✅ numpy版本: {np.__version__}")
    print(f"   numpy路径: {np.__file__}")
except Exception as e:
    print(f"❌ numpy导入失败: {e}")

print()

# 检查paddle
try:
    import paddle
    print(f"✅ paddle版本: {paddle.__version__}")
except Exception as e:
    print(f"❌ paddle导入失败: {e}")

print()

# 检查opencv
try:
    import cv2
    print(f"✅ opencv版本: {cv2.__version__}")
except Exception as e:
    print(f"❌ opencv导入失败: {e}")

print()

# 检查YOLO
try:
    from ultralytics import YOLO
    print(f"✅ ultralytics导入成功")
except Exception as e:
    print(f"❌ ultralytics导入失败: {e}")

print()

# 检查环境变量
print("环境变量:")
print(f"  CONDA_DEFAULT_ENV: {os.getenv('CONDA_DEFAULT_ENV', '未设置')}")
print(f"  CONDA_PREFIX: {os.getenv('CONDA_PREFIX', '未设置')}")
