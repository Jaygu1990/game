"""
测试模型加载，诊断numpy._core错误
"""

import sys
import io
from pathlib import Path

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加PaddleOCR路径
PROJECT_ROOT = Path(__file__).parent.parent
PADDLEOCR_DIR = PROJECT_ROOT / 'PaddleOCR'
if PADDLEOCR_DIR.exists():
    sys.path.insert(0, str(PADDLEOCR_DIR))

# 注意：使用numpy 2.0以兼容用numpy 2.0训练的模型文件
# 不再需要兼容性修复

print("=" * 70)
print("测试模型加载")
print("=" * 70)

# 1. 检查numpy版本
print("\n[1/4] 检查numpy版本...")
try:
    import numpy
    print(f"✅ numpy版本: {numpy.__version__}")
    
    # 检查是否有_core模块
    try:
        import numpy._core
        print("⚠️  警告: 检测到numpy._core模块")
    except ImportError:
        print("✅ 未检测到numpy._core模块（正常）")
except Exception as e:
    print(f"❌ numpy导入失败: {e}")
    sys.exit(1)

# 2. 检查paddlepaddle
print("\n[2/4] 检查paddlepaddle...")
try:
    import paddle
    print(f"✅ paddle版本: {paddle.__version__}")
except Exception as e:
    print(f"❌ paddle导入失败: {e}")
    sys.exit(1)

# 3. 查找模型文件
print("\n[3/4] 查找模型文件...")
possible_ocr_paths = [
    PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'best_accuracy.pdparams',
    PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'latest.pdparams',
    PROJECT_ROOT / 'models' / 'OCR_code' / 'best_accuracy.pdparams',
    PROJECT_ROOT / 'models' / 'OCR_code' / 'latest.pdparams',
]

ocr_model_path = None
for path in possible_ocr_paths:
    if path.exists():
        ocr_model_path = path
        print(f"✅ 找到模型文件: {ocr_model_path}")
        print(f"   文件大小: {path.stat().st_size / 1024 / 1024:.2f} MB")
        break

if not ocr_model_path:
    print("❌ 未找到模型文件")
    sys.exit(1)

# 4. 尝试加载模型
print("\n[4/4] 尝试加载模型...")
try:
    print(f"   加载: {ocr_model_path}")
    
    # 方法1: 直接使用paddle.load
    print("   方法1: 使用paddle.load...")
    state_dict = paddle.load(str(ocr_model_path))
    print(f"✅ 模型加载成功！")
    print(f"   参数数量: {len(state_dict)}")
    
    # 显示前几个参数名
    print("\n   前5个参数名:")
    for i, key in enumerate(list(state_dict.keys())[:5]):
        print(f"     {i+1}. {key}: {state_dict[key].shape if hasattr(state_dict[key], 'shape') else type(state_dict[key])}")
    
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    
    # 尝试诊断问题
    print("\n" + "=" * 70)
    print("诊断信息:")
    print("=" * 70)
    
    # 检查是否是pickle问题
    if "pickle" in str(e).lower() or "_core" in str(e).lower():
        print("\n⚠️  这可能是模型文件兼容性问题:")
        print("   1. 模型文件可能是用numpy 2.0保存的")
        print("   2. 或者paddlepaddle版本不兼容")
        print("\n建议:")
        print("   1. 检查模型文件是在哪个环境下训练的")
        print("   2. 尝试重新训练模型（使用numpy 1.x）")
        print("   3. 或者升级paddlepaddle到最新版本")
    
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ 所有测试通过！")
print("=" * 70)
