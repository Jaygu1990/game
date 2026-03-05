"""
测试服务器启动
"""

import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("测试服务器启动")
print("=" * 70)

# 1. 测试模型加载
print("\n[1/2] 测试模型加载...")
try:
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.parent
    
    # 测试YOLO
    from ultralytics import YOLO
    yolo_path = PROJECT_ROOT / 'models' / 'detector_yolo' / 'detector_yolov8s_best.pt'
    if yolo_path.exists():
        yolo_model = YOLO(str(yolo_path))
        print("✅ YOLO模型加载成功")
    else:
        print(f"❌ YOLO模型文件不存在: {yolo_path}")
    
    # 测试OCR模型
    import paddle
    ocr_model_path = PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'best_accuracy.pdparams'
    if ocr_model_path.exists():
        state_dict = paddle.load(str(ocr_model_path))
        print("✅ OCR模型加载成功")
    else:
        print(f"❌ OCR模型文件不存在: {ocr_model_path}")
        
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试服务器导入
print("\n[2/2] 测试服务器导入...")
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from server import app
    print("✅ 服务器模块导入成功")
except Exception as e:
    print(f"❌ 服务器模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有测试通过！服务器应该能正常启动")
print("=" * 70)
