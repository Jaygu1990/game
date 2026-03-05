"""
调试服务器启动问题
"""
import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("调试服务器启动")
print("=" * 70)

# 1. 测试torch
print("\n[1/5] 测试torch...")
try:
    import torch
    print(f"✅ torch导入成功: {torch.__version__}")
except Exception as e:
    print(f"❌ torch导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试albumentations
print("\n[2/5] 测试albumentations...")
try:
    import albumentations as A
    print("✅ albumentations导入成功")
except Exception as e:
    print(f"❌ albumentations导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试PaddleOCR导入
print("\n[3/5] 测试PaddleOCR导入...")
try:
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).parent.parent
    PADDLEOCR_DIR = PROJECT_ROOT / 'PaddleOCR'
    if PADDLEOCR_DIR.exists():
        sys.path.insert(0, str(PADDLEOCR_DIR))
    
    from ppocr.data import create_operators, transform
    print("✅ PaddleOCR data导入成功")
except Exception as e:
    print(f"❌ PaddleOCR data导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试YOLO
print("\n[4/5] 测试YOLO...")
try:
    from ultralytics import YOLO
    print("✅ YOLO导入成功")
except Exception as e:
    print(f"❌ YOLO导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 测试服务器模块导入
print("\n[5/5] 测试服务器模块导入...")
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
print("✅ 所有测试通过！")
print("=" * 70)
