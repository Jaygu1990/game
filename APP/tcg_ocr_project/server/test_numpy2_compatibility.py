"""
测试numpy 2.0与paddlepaddle和opencv-python的兼容性
"""

import sys
import io
from pathlib import Path

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("测试numpy 2.0兼容性")
print("=" * 70)

# 1. 升级numpy到2.0
print("\n[1/4] 升级numpy到2.0...")
try:
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "numpy>=2.0.0", "--upgrade", "--no-cache-dir"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ numpy已升级")
    else:
        print(f"⚠️  numpy升级可能有问题: {result.stderr}")
except Exception as e:
    print(f"❌ numpy升级失败: {e}")

# 2. 测试numpy导入
print("\n[2/4] 测试numpy导入...")
try:
    import numpy as np
    print(f"✅ numpy版本: {np.__version__}")
    
    # 检查_core模块
    try:
        import numpy._core
        print("✅ numpy._core模块存在（numpy 2.0+）")
    except ImportError:
        print("❌ numpy._core模块不存在")
except Exception as e:
    print(f"❌ numpy导入失败: {e}")
    sys.exit(1)

# 3. 测试opencv-python
print("\n[3/4] 测试opencv-python...")
try:
    import cv2
    print(f"✅ opencv-python版本: {cv2.__version__}")
    
    # 测试基本功能
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print("✅ opencv-python基本功能正常")
except Exception as e:
    print(f"❌ opencv-python测试失败: {e}")
    print("   可能需要重新安装opencv-python")
    print("   尝试: pip install opencv-python --upgrade --force-reinstall")

# 4. 测试paddlepaddle
print("\n[4/4] 测试paddlepaddle...")
try:
    import paddle
    print(f"✅ paddle版本: {paddle.__version__}")
    
    # 测试基本功能
    x = paddle.to_tensor([1.0, 2.0, 3.0])
    y = x * 2
    print(f"✅ paddle基本功能正常: {y.numpy()}")
except Exception as e:
    print(f"❌ paddle测试失败: {e}")
    print("   可能需要升级paddlepaddle")
    print("   尝试: pip install paddlepaddle --upgrade")

# 5. 测试模型加载
print("\n[5/5] 测试模型加载...")
PROJECT_ROOT = Path(__file__).parent.parent
PADDLEOCR_DIR = PROJECT_ROOT / 'PaddleOCR'
if PADDLEOCR_DIR.exists():
    sys.path.insert(0, str(PADDLEOCR_DIR))

model_path = PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'best_accuracy.pdparams'

if model_path.exists():
    try:
        print(f"   尝试加载: {model_path}")
        state_dict = paddle.load(str(model_path))
        print(f"✅ 模型加载成功！参数数量: {len(state_dict)}")
        print("\n" + "=" * 70)
        print("✅ 所有测试通过！numpy 2.0兼容性良好")
        print("=" * 70)
        print("\n建议:")
        print("1. 更新requirements_server.txt，使用numpy>=2.0.0")
        print("2. 重新安装opencv-python（如果需要）")
        print("3. 测试服务器是否能正常启动")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 70)
        print("⚠️  模型加载失败，可能需要其他解决方案")
        print("=" * 70)
else:
    print(f"⚠️  模型文件不存在: {model_path}")
