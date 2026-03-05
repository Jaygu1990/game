"""
测试YOLO和numpy的交互
"""

import sys
import io
from pathlib import Path

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("测试YOLO和numpy交互")
print("=" * 70)

# 1. 检查numpy
print("\n[1/3] 检查numpy...")
try:
    import numpy as np
    print(f"✅ numpy版本: {np.__version__}")
    print(f"   numpy路径: {np.__file__}")
    
    # 测试基本功能
    arr = np.array([1, 2, 3])
    print(f"✅ numpy基本功能正常")
except Exception as e:
    print(f"❌ numpy导入失败: {e}")
    sys.exit(1)

# 2. 检查YOLO
print("\n[2/3] 检查YOLO...")
try:
    from ultralytics import YOLO
    print("✅ ultralytics导入成功")
except Exception as e:
    print(f"❌ ultralytics导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试YOLO模型加载和推理
print("\n[3/3] 测试YOLO模型...")
PROJECT_ROOT = Path(__file__).parent.parent
yolo_path = PROJECT_ROOT / 'models' / 'detector_yolo' / 'detector_yolov8s_best.pt'

if not yolo_path.exists():
    print(f"❌ YOLO模型文件不存在: {yolo_path}")
    sys.exit(1)

try:
    print(f"   加载模型: {yolo_path}")
    model = YOLO(str(yolo_path))
    print("✅ YOLO模型加载成功")
    
    # 测试推理（使用测试图片）
    test_image = PROJECT_ROOT / 'data' / 'sample.jpg'
    if test_image.exists():
        print(f"   测试图片: {test_image}")
        results = model(str(test_image), verbose=False)
        print(f"✅ YOLO推理成功，检测到 {len(results[0].boxes)} 个框")
    else:
        print(f"⚠️  测试图片不存在: {test_image}")
        print("   跳过推理测试")
    
except Exception as e:
    print(f"❌ YOLO测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有测试通过！")
print("=" * 70)
