"""
修复numpy版本兼容性问题
"""

import subprocess
import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def fix_numpy():
    """重新安装兼容的numpy版本"""
    print("=" * 70)
    print("修复numpy版本兼容性问题")
    print("=" * 70)
    
    print("\n[1/3] 卸载当前numpy...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "numpy", "-y"])
        print("✅ numpy已卸载")
    except Exception as e:
        print(f"⚠️  卸载numpy时出错（可能未安装）: {e}")
    
    print("\n[2/3] 安装兼容的numpy版本（1.24.3）...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "numpy>=1.19.0,<2.0.0", "--no-cache-dir"
        ])
        print("✅ numpy已安装")
    except Exception as e:
        print(f"❌ 安装numpy失败: {e}")
        return False
    
    print("\n[3/3] 验证numpy安装...")
    try:
        import numpy
        print(f"✅ numpy版本: {numpy.__version__}")
        
        # 测试基本功能
        arr = numpy.array([1, 2, 3])
        print(f"✅ numpy基本功能正常")
        
        # 检查是否有_core模块（不应该有）
        try:
            import numpy._core
            print("⚠️  警告: 检测到numpy._core模块（numpy 2.0+特性）")
            print("   这可能导致paddlepaddle兼容性问题")
        except ImportError:
            print("✅ 未检测到numpy._core模块（正常）")
        
        return True
    except Exception as e:
        print(f"❌ numpy验证失败: {e}")
        return False

if __name__ == "__main__":
    success = fix_numpy()
    if success:
        print("\n" + "=" * 70)
        print("✅ numpy修复完成！")
        print("=" * 70)
        print("\n请重新启动服务器:")
        print("  python server.py")
    else:
        print("\n" + "=" * 70)
        print("❌ numpy修复失败，请手动检查")
        print("=" * 70)
        sys.exit(1)
