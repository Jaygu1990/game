"""
最终测试脚本
"""
import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("最终测试")
print("=" * 70)

# 1. 测试pathlib
print("\n[1/4] 测试pathlib...")
try:
    from pathlib import Path
    print("✅ pathlib导入成功")
except Exception as e:
    print(f"❌ pathlib导入失败: {e}")
    sys.exit(1)

# 2. 测试torch
print("\n[2/4] 测试torch...")
try:
    import torch
    print(f"✅ torch导入成功，版本: {torch.__version__}")
except Exception as e:
    print(f"❌ torch导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试albumentations
print("\n[3/4] 测试albumentations...")
try:
    import albumentations as A
    print("✅ albumentations导入成功")
except Exception as e:
    print(f"❌ albumentations导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 测试服务器模块导入
print("\n[4/4] 测试服务器模块导入...")
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
