"""
测试torch导入
"""
import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("测试torch导入...")
try:
    import torch
    print(f"✅ torch导入成功，版本: {torch.__version__}")
    x = torch.tensor([1, 2, 3])
    print(f"✅ torch基本功能正常: {x}")
except Exception as e:
    print(f"❌ torch导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("✅ 所有测试通过！")
