"""
批量升级所有包以支持numpy 2.0
"""

import subprocess
import sys

packages_to_upgrade = [
    "pandas",
    "torchvision", 
    "ultralytics",
]

print("=" * 70)
print("批量升级包以支持numpy 2.0")
print("=" * 70)

for package in packages_to_upgrade:
    print(f"\n升级 {package}...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--upgrade", "--no-cache-dir"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {package} 升级成功")
        else:
            print(f"⚠️  {package} 升级可能有问题")
            print(result.stderr[:200])
    except Exception as e:
        print(f"❌ {package} 升级失败: {e}")

print("\n" + "=" * 70)
print("升级完成！")
print("=" * 70)
