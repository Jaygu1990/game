"""
修复numpy._core模块缺失问题
在导入paddle之前注入numpy._core兼容模块
"""

import sys
import types
import numpy as np

def create_numpy_core_compat():
    """创建numpy._core兼容模块"""
    if hasattr(np, '_core'):
        # 检查是否已经有multiarray
        if hasattr(np._core, 'multiarray'):
            return np._core
        # 如果没有，继续创建子模块
    else:
        # 创建_core模块
        _core = types.ModuleType('_core')
        np._core = _core
        sys.modules['numpy._core'] = _core
    
    _core = np._core
    
    # 复制numpy的核心功能到_core
    if not hasattr(_core, 'array'):
        _core.array = np.array
        _core.ndarray = np.ndarray
        _core.dtype = np.dtype
        _core.uint8 = np.uint8
        _core.int32 = np.int32
        _core.int64 = np.int64
        _core.float32 = np.float32
        _core.float64 = np.float64
        _core.bool_ = np.bool_
    
    # 创建multiarray子模块（pickle需要）
    if not hasattr(_core, 'multiarray'):
        multiarray = types.ModuleType('multiarray')
        # 将numpy的multiarray功能映射过去
        try:
            import numpy.core.multiarray as np_multiarray
            # 复制所有属性
            for attr in dir(np_multiarray):
                if not attr.startswith('_'):
                    try:
                        setattr(multiarray, attr, getattr(np_multiarray, attr))
                    except:
                        pass
        except ImportError:
            # 如果numpy.core.multiarray不存在，创建基本功能
            multiarray.array = np.array
            multiarray.ndarray = np.ndarray
        
        _core.multiarray = multiarray
        sys.modules['numpy._core.multiarray'] = multiarray
    
    # 创建_multiarray_umath子模块
    if not hasattr(_core, '_multiarray_umath'):
        _multiarray_umath = types.ModuleType('_multiarray_umath')
        _core._multiarray_umath = _multiarray_umath
        sys.modules['numpy._core._multiarray_umath'] = _multiarray_umath
    
    # 创建array_api子模块
    if not hasattr(_core, 'array_api'):
        array_api = types.ModuleType('array_api')
        _core.array_api = array_api
        sys.modules['numpy._core.array_api'] = array_api
    
    return _core

# 自动执行
create_numpy_core_compat()
