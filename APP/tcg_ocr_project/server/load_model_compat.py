"""
兼容性加载模型文件的workaround
尝试解决numpy._core错误
"""

import sys
import io
from pathlib import Path
import pickle

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加PaddleOCR路径
PROJECT_ROOT = Path(__file__).parent.parent
PADDLEOCR_DIR = PROJECT_ROOT / 'PaddleOCR'
if PADDLEOCR_DIR.exists():
    sys.path.insert(0, str(PADDLEOCR_DIR))

import paddle
import numpy as np

def load_model_compat(model_path):
    """
    兼容性加载模型，尝试解决numpy._core错误
    
    方法1: 创建一个假的numpy._core模块
    方法2: 使用pickle的兼容模式
    """
    print("=" * 70)
    print("尝试兼容性加载模型...")
    print("=" * 70)
    
    # 方法1: 创建假的numpy._core模块
    print("\n[方法1] 创建numpy._core兼容模块...")
    try:
        import types
        # 创建一个假的_core模块
        fake_core = types.ModuleType('_core')
        # 将numpy的主要功能映射到_core
        fake_core.array = np.array
        fake_core.ndarray = np.ndarray
        fake_core.dtype = np.dtype
        
        # 尝试注入到numpy中
        if not hasattr(np, '_core'):
            np._core = fake_core
            print("✅ 已创建numpy._core兼容模块")
        else:
            print("⚠️  numpy._core已存在")
    except Exception as e:
        print(f"⚠️  创建兼容模块失败: {e}")
    
    # 方法2: 直接使用pickle加载
    print("\n[方法2] 尝试直接加载...")
    try:
        state_dict = paddle.load(str(model_path))
        print("✅ 模型加载成功！")
        return state_dict
    except Exception as e:
        print(f"❌ 加载失败: {e}")
    
    # 方法3: 使用pickle直接加载
    print("\n[方法3] 使用pickle直接加载...")
    try:
        with open(model_path, 'rb') as f:
            # 尝试不同的编码
            for encoding in ['latin1', 'utf-8', 'ascii']:
                try:
                    f.seek(0)
                    state_dict = pickle.load(f, encoding=encoding)
                    print(f"✅ 使用{encoding}编码加载成功！")
                    return state_dict
                except Exception as e:
                    print(f"   {encoding}编码失败: {type(e).__name__}")
                    continue
    except Exception as e:
        print(f"❌ pickle直接加载失败: {e}")
    
    print("\n" + "=" * 70)
    print("❌ 所有方法都失败了")
    print("=" * 70)
    print("\n建议:")
    print("1. 重新训练模型（使用numpy 1.x环境）")
    print("2. 或者在训练环境中导出模型为ONNX格式")
    print("3. 或者升级到支持numpy 2.0的paddlepaddle版本")
    
    return None

if __name__ == "__main__":
    model_path = PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'best_accuracy.pdparams'
    
    if not model_path.exists():
        print(f"❌ 模型文件不存在: {model_path}")
        sys.exit(1)
    
    state_dict = load_model_compat(model_path)
    
    if state_dict:
        print(f"\n✅ 成功加载模型，参数数量: {len(state_dict)}")
