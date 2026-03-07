"""
TCG OCR API Server for Render
支持多线程处理和请求排队（等待机制）
"""

import sys
import os
from pathlib import Path
import cv2
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import tempfile
import threading
from typing import Optional, Dict, Tuple
from contextlib import asynccontextmanager
import logging

# FastAPI
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 项目根目录（server 文件夹的父目录）
PROJECT_ROOT = Path(__file__).parent.parent

# 初始化日志（用于调试）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger_temp = logging.getLogger(__name__)

# 添加PaddleOCR路径（确保ppocr模块可以被导入）
PADDLEOCR_DIR = PROJECT_ROOT / 'PaddleOCR'
ppocr_found = False

logger_temp.info("=" * 70)
logger_temp.info("开始检查 ppocr 模块路径...")
logger_temp.info(f"项目根目录: {PROJECT_ROOT}")
logger_temp.info(f"PaddleOCR目录路径: {PADDLEOCR_DIR}")
logger_temp.info(f"PaddleOCR目录存在: {PADDLEOCR_DIR.exists()}")

# 检查本地PaddleOCR目录（必须存在于仓库中）
if PADDLEOCR_DIR.exists():
    ppocr_local = PADDLEOCR_DIR / 'ppocr'
    modeling_local = ppocr_local / 'modeling'
    logger_temp.info(f"检查本地PaddleOCR目录: {PADDLEOCR_DIR}")
    logger_temp.info(f"  ppocr目录路径: {ppocr_local}")
    logger_temp.info(f"  ppocr目录存在: {ppocr_local.exists()}")
    logger_temp.info(f"  ppocr.modeling目录路径: {modeling_local}")
    logger_temp.info(f"  ppocr.modeling目录存在: {modeling_local.exists()}")
    
    # 检查目录是否为空
    try:
        contents = list(PADDLEOCR_DIR.iterdir())
        logger_temp.info(f"  PaddleOCR目录内容数量: {len(contents)}")
        
        if len(contents) == 0:
            logger_temp.error("=" * 70)
            logger_temp.error("❌ PaddleOCR目录为空！")
            logger_temp.error("   请确保 PaddleOCR 目录已正确添加到 Git 仓库中")
            logger_temp.error("   目录路径: " + str(PADDLEOCR_DIR))
            logger_temp.error("=" * 70)
        elif modeling_local.exists():
            sys.path.insert(0, str(PADDLEOCR_DIR))
            logger_temp.info(f"✅ 使用本地PaddleOCR目录: {PADDLEOCR_DIR}")
            ppocr_found = True
        else:
            logger_temp.error("=" * 70)
            logger_temp.error("❌ PaddleOCR目录存在但ppocr.modeling不存在")
            logger_temp.error("   请确保 PaddleOCR 目录完整，包含 ppocr/modeling 子目录")
            logger_temp.error(f"  PaddleOCR目录内容（前20项）: {[str(c.name) for c in contents[:20]]}")
            if ppocr_local.exists():
                ppocr_contents = list(ppocr_local.iterdir())[:20]
                logger_temp.error(f"  ppocr目录内容（前20项）: {[str(c.name) for c in ppocr_contents]}")
            logger_temp.error("=" * 70)
    except Exception as e:
        logger_temp.error(f"  无法列出目录内容: {e}")
        import traceback
        logger_temp.error(traceback.format_exc())
else:
    logger_temp.error("=" * 70)
    logger_temp.error("❌ PaddleOCR目录不存在！")
    logger_temp.error("   请确保 PaddleOCR 目录已添加到 Git 仓库中")
    logger_temp.error("   期望路径: " + str(PADDLEOCR_DIR))
    logger_temp.error("   正确结构应该是:")
    logger_temp.error("     APP/tcg_ocr_project/PaddleOCR/")
    logger_temp.error("=" * 70)

# 如果本地没有，尝试从paddleocr包中找到
if not ppocr_found:
    logger_temp.info("尝试从paddleocr包中查找ppocr模块...")
    try:
        import paddleocr
        import os
        paddleocr_path = os.path.dirname(paddleocr.__file__)
        logger_temp.info(f"  找到paddleocr包路径: {paddleocr_path}")
        
        # 检查ppocr目录是否存在
        ppocr_dir = os.path.join(paddleocr_path, 'ppocr')
        logger_temp.info(f"  检查ppocr目录: {ppocr_dir}, 存在: {os.path.exists(ppocr_dir)}")
        
        if os.path.exists(ppocr_dir):
            # 检查ppocr.modeling是否存在
            modeling_dir = os.path.join(ppocr_dir, 'modeling')
            logger_temp.info(f"  检查ppocr.modeling目录: {modeling_dir}, 存在: {os.path.exists(modeling_dir)}")
            
            if os.path.exists(modeling_dir):
                # 将paddleocr包的目录添加到路径
                sys.path.insert(0, paddleocr_path)
                logger_temp.info(f"✅ 已添加paddleocr路径: {paddleocr_path}")
                ppocr_found = True
            else:
                logger_temp.error(f"❌ ppocr.modeling目录不存在: {modeling_dir}")
        else:
            logger_temp.error(f"❌ ppocr目录不存在: {ppocr_dir}")
    except Exception as e:
        logger_temp.error(f"❌ 无法设置paddleocr路径: {e}")
        import traceback
        logger_temp.error(traceback.format_exc())

# 如果都找不到，给出明确的错误提示
if not ppocr_found:
    logger_temp.error("=" * 70)
    logger_temp.error("❌ 无法找到ppocr.modeling模块！")
    logger_temp.error("   请确保：")
    logger_temp.error("   1. PaddleOCR源码目录已正确克隆到项目根目录")
    logger_temp.error("   2. 或者paddleocr包包含完整的ppocr模块")
    logger_temp.error("=" * 70)

# 注意：使用numpy 2.0以兼容用numpy 2.0训练的模型文件
# 不再需要兼容性修复，因为环境已升级到numpy 2.0

# 延迟导入重型库（在函数内部导入，避免阻塞服务器启动）
# 这些库会在 load_models() 函数中导入
paddle = None
build_model = None
build_post_process = None
create_operators = None
transform = None
yaml = None
YOLO = None

def _import_heavy_libraries():
    """延迟导入重型库（在需要时才导入）"""
    global paddle, build_model, build_post_process, create_operators, transform, yaml, YOLO
    
    if paddle is not None:
        # 已经导入过了
        logger.info("✅ 重型库已导入，跳过")
        return
    
    logger.info("=" * 70)
    logger.info("步骤 1/2: 开始导入重型库...")
    logger.info("=" * 70)
    start_time = time.time()
    
    try:
        # 1.1 导入 paddle
        logger.info("[1.1/4] 导入 paddle（这可能需要 30-60 秒，请耐心等待）...")
        logger.info("  - 正在导入 paddle 模块...")
        sys.stdout.flush()  # 强制刷新输出
        paddle_start = time.time()
        
        # 在导入过程中定期输出进度（每30秒）
        progress_stop = threading.Event()
        def log_progress():
            elapsed = 0
            while not progress_stop.is_set():
                time.sleep(30)  # 每30秒输出一次
                if not progress_stop.is_set():
                    elapsed += 30
                    logger.info(f"  ⏳ paddle 导入中...（已等待 {elapsed} 秒，Render Free Plan 可能较慢）")
                    sys.stdout.flush()
        
        progress_thread = threading.Thread(target=log_progress, daemon=True)
        progress_thread.start()
        
        try:
            import paddle as _paddle
            paddle = _paddle
        finally:
            progress_stop.set()
            progress_thread.join(timeout=1)
        
        paddle_elapsed = time.time() - paddle_start
        logger.info(f"  ✅ paddle 导入成功（耗时 {paddle_elapsed:.1f} 秒）")
        logger.info(f"  - paddle 版本: {paddle.__version__ if hasattr(paddle, '__version__') else '未知'}")
        sys.stdout.flush()
        
        # 1.2 导入 ppocr 模块
        logger.info("[1.2/4] 导入 ppocr 模块...")
        logger.info("  - 正在导入 ppocr.modeling.architectures...")
        ppocr_start = time.time()
        from ppocr.modeling.architectures import build_model as _build_model
        logger.info("  - 正在导入 ppocr.postprocess...")
        from ppocr.postprocess import build_post_process as _build_post_process
        logger.info("  - 正在导入 ppocr.data...")
        from ppocr.data import create_operators as _create_operators, transform as _transform
        build_model = _build_model
        build_post_process = _build_post_process
        create_operators = _create_operators
        transform = _transform
        ppocr_elapsed = time.time() - ppocr_start
        logger.info(f"  ✅ ppocr 模块导入成功（耗时 {ppocr_elapsed:.1f} 秒）")
        
        # 1.3 导入 yaml
        logger.info("[1.3/4] 导入 yaml...")
        logger.info("  - 正在导入 yaml 模块...")
        yaml_start = time.time()
        import yaml as _yaml
        yaml = _yaml
        yaml_elapsed = time.time() - yaml_start
        logger.info(f"  ✅ yaml 导入成功（耗时 {yaml_elapsed:.1f} 秒）")
        
        # 1.4 导入 ultralytics
        logger.info("[1.4/4] 导入 ultralytics...")
        logger.info("  - 正在导入 ultralytics.YOLO...")
        ultralytics_start = time.time()
        from ultralytics import YOLO as _YOLO
        YOLO = _YOLO
        ultralytics_elapsed = time.time() - ultralytics_start
        logger.info(f"  ✅ ultralytics 导入成功（耗时 {ultralytics_elapsed:.1f} 秒）")
        
        total_elapsed = time.time() - start_time
        logger.info("=" * 70)
        logger.info(f"✅ 所有库导入完成（总耗时 {total_elapsed:.1f} 秒）")
        logger.info("=" * 70)
    except ImportError as e:
        elapsed = time.time() - start_time
        logger.error("=" * 70)
        logger.error(f"❌ 导入错误（耗时 {elapsed:.1f} 秒）")
        logger.error(f"   错误类型: ImportError")
        logger.error(f"   错误信息: {e}")
        logger.error(f"   可能原因: 缺少依赖包或模块路径错误")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        raise
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error("=" * 70)
        logger.error(f"❌ 导入重型库失败（耗时 {elapsed:.1f} 秒）")
        logger.error(f"   错误类型: {type(e).__name__}")
        logger.error(f"   错误信息: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        raise

# ===== 配置 =====
# 日志已在上面初始化，这里复用
logger = logging.getLogger(__name__)

# 模型路径配置
YOLO_MODEL_DIR = PROJECT_ROOT / 'models' / 'detector_yolo'
OCR_CONFIG_FILE = PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'config.yml'

# 尝试多个可能的模型路径
possible_yolo_paths = [
    YOLO_MODEL_DIR / 'detector_yolov8s_best.pt',
    YOLO_MODEL_DIR / 'best.pt',
    PROJECT_ROOT / 'models' / 'detector' / 'best.pt',
]

possible_ocr_paths = [
    PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'best_accuracy.pdparams',
    PROJECT_ROOT / 'data' / 'ocr_train' / 'code' / 'models' / 'latest.pdparams',
    PROJECT_ROOT / 'models' / 'OCR_code' / 'best_accuracy.pdparams',
    PROJECT_ROOT / 'models' / 'OCR_code' / 'latest.pdparams',
]

# 全局模型变量
yolo_model = None
ocr_model = None
post_process_class = None
eval_ops = None
config = None

# 线程池和队列配置
MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))  # 并发处理线程数
MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '100'))  # 队列最大长度
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '60'))  # 请求超时时间（秒）
QUEUE_WAIT_TIMEOUT = int(os.getenv('QUEUE_WAIT_TIMEOUT', '300'))  # 队列等待超时（秒）

# 使用信号量控制并发数（达到最大并发数时会自动等待）
concurrency_semaphore = asyncio.Semaphore(MAX_WORKERS)
# 队列用于统计和等待（当所有worker都在忙时，新请求会在这里等待）
request_queue = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# 统计信息
stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'current_queue_size': 0,
    'max_queue_size_reached': 0,
}

# ===== FastAPI 应用 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（启动和关闭）"""
    # 启动时执行 - 加载模型
    logger.info("=" * 70)
    logger.info("🚀 服务器启动中...")
    logger.info("=" * 70)
    logger.info(f"服务器配置:")
    logger.info(f"  - MAX_WORKERS: {MAX_WORKERS}")
    logger.info(f"  - MAX_QUEUE_SIZE: {MAX_QUEUE_SIZE}")
    logger.info(f"  - REQUEST_TIMEOUT: {REQUEST_TIMEOUT} 秒")
    logger.info(f"  - QUEUE_WAIT_TIMEOUT: {QUEUE_WAIT_TIMEOUT} 秒")
    logger.info("=" * 70)
    logger.info("开始后台加载模型（这可能需要 1-3 分钟，请耐心等待）...")
    logger.info("服务器将立即启动，模型在后台加载")
    logger.info("=" * 70)
    
    global models_loading, models_loaded
    
    # 在后台任务中加载模型，不阻塞服务器启动
    async def load_models_background():
        global models_loading, models_loaded
        models_loading = True
        startup_start = time.time()
        try:
            logger.info("正在后台线程中加载模型...")
            logger.info("注意：Render Free Plan 资源有限，模型加载可能需要 5-10 分钟")
            logger.info("服务器已启动，可以响应请求，但 OCR 功能需等待模型加载完成")
            loop = asyncio.get_event_loop()
            # 增加超时时间到10分钟（Render Free Plan 可能较慢）
            await asyncio.wait_for(
                loop.run_in_executor(executor, load_models),
                timeout=600.0  # 10分钟超时
            )
            models_loaded = True
            startup_elapsed = time.time() - startup_start
            logger.info("=" * 70)
            logger.info(f"✅ 模型加载完成，服务器就绪（总耗时 {startup_elapsed:.1f} 秒）")
            logger.info("=" * 70)
        except asyncio.TimeoutError:
            startup_elapsed = time.time() - startup_start
            logger.warning("=" * 70)
            logger.warning(f"⚠️  模型加载超时（超过10分钟，已耗时 {startup_elapsed:.1f} 秒）")
            logger.warning("服务器将继续运行，但模型未加载")
            logger.warning("首次 OCR 请求时会自动重试加载模型（无超时限制）")
            logger.warning("=" * 70)
            models_loaded = False
        except Exception as e:
            startup_elapsed = time.time() - startup_start
            logger.error("=" * 70)
            logger.error(f"❌ 模型加载失败（已耗时 {startup_elapsed:.1f} 秒）")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            logger.error("服务器将继续运行，但模型未加载")
            logger.error("首次请求时会自动重试加载模型")
            logger.error("=" * 70)
            import traceback
            traceback.print_exc()
            models_loaded = False
        finally:
            models_loading = False
    
    # 启动后台任务，不等待完成
    asyncio.create_task(load_models_background())
    logger.info("✅ 模型加载任务已启动（后台运行）")
    
    yield
    
    # 关闭时执行（如果需要清理资源）
    logger.info("=" * 70)
    logger.info("服务器正在关闭...")
    logger.info("=" * 70)

app = FastAPI(
    title="TCG OCR API",
    version="1.0.0",
    description="TCG卡片Code区域OCR识别API服务",
    lifespan=lifespan
)

# CORS 配置（允许跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 响应模型 =====
class OCRResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    confidence: Optional[float] = None
    bbox: Optional[Tuple[int, int, int, int]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    queue_wait_time: Optional[float] = None

class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    queue_size: int
    max_queue_size: int
    active_workers: int
    stats: Dict

# ===== 模型加载函数 =====
def preprocess_code_region(image, min_height=64, min_width=128, padding=5):
    """预处理code区域（与训练时一致）"""
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    if padding > 0:
        gray = cv2.copyMakeBorder(gray, padding, padding, padding, padding, 
                                  cv2.BORDER_CONSTANT, value=255)
    
    h, w = gray.shape
    scale_h = max(1.0, min_height / h) if h > 0 else 4.0
    scale_w = max(1.0, min_width / w) if w > 0 else 4.0
    scale = max(scale_h, scale_w, 3.0)
    
    if scale > 1.0:
        new_h, new_w = int(h * scale), int(w * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    kernel_sharpen = np.array([[-1, -1, -1],
                               [-1,  9, -1],
                               [-1, -1, -1]])
    gray = cv2.filter2D(gray, -1, kernel_sharpen)
    
    gray = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=5, searchWindowSize=15)
    
    h, w = gray.shape
    if h < min_height or w < min_width:
        scale_final = max(min_height / h, min_width / w) if h > 0 and w > 0 else 2.0
        new_h, new_w = int(h * scale_final), int(w * scale_final)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    return gray

def load_models():
    """加载YOLO和OCR模型（启动时调用一次）"""
    global yolo_model, ocr_model, post_process_class, eval_ops, config
    
    # 延迟导入重型库（在需要时才导入）
    _import_heavy_libraries()
    
    logger.info("=" * 70)
    logger.info("步骤 2/2: 开始加载模型...")
    logger.info("=" * 70)
    
    # 1. 加载 YOLO 模型
    logger.info("[2.1/3] 加载 YOLO 模型...")
    logger.info("  - 正在查找 YOLO 模型文件...")
    yolo_path = None
    for i, path in enumerate(possible_yolo_paths, 1):
        logger.info(f"    [{i}/{len(possible_yolo_paths)}] 检查路径: {path}")
        if path.exists():
            yolo_path = path
            file_size = path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"  ✅ 找到 YOLO 模型: {yolo_path}")
            logger.info(f"  - 文件大小: {file_size:.2f} MB")
            break
        else:
            logger.info(f"    ❌ 文件不存在")
    
    if yolo_path:
        try:
            logger.info("  - 正在加载 YOLO 模型（这可能需要 10-30 秒）...")
            yolo_load_start = time.time()
            yolo_model = YOLO(str(yolo_path))
            yolo_load_elapsed = time.time() - yolo_load_start
            logger.info(f"  ✅ YOLO模型加载成功（耗时 {yolo_load_elapsed:.1f} 秒）")
            logger.info(f"  - 模型路径: {yolo_path}")
        except FileNotFoundError as e:
            logger.error("=" * 70)
            logger.error(f"❌ YOLO模型文件未找到")
            logger.error(f"   错误信息: {e}")
            logger.error(f"   已检查的路径:")
            for path in possible_yolo_paths:
                logger.error(f"     - {path} (存在: {path.exists()})")
            logger.error("=" * 70)
            raise
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ YOLO模型加载失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            logger.error(f"   模型路径: {yolo_path}")
            logger.error("=" * 70)
            import traceback
            traceback.print_exc()
            raise
    else:
        logger.error("=" * 70)
        logger.error("❌ 未找到YOLO模型文件")
        logger.error("   已检查的路径:")
        for path in possible_yolo_paths:
            logger.error(f"     - {path} (存在: {path.exists()})")
        logger.error("=" * 70)
        raise FileNotFoundError("YOLO模型文件不存在")
    
    # 2. 加载 OCR 模型
    logger.info("[2.2/3] 加载 OCR 模型...")
    logger.info("  - 正在查找 OCR 模型文件...")
    
    ocr_model_path = None
    for i, path in enumerate(possible_ocr_paths, 1):
        logger.info(f"    [{i}/{len(possible_ocr_paths)}] 检查路径: {path}")
        if path.exists():
            ocr_model_path = path
            file_size = path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"  ✅ 找到 OCR 模型: {ocr_model_path}")
            logger.info(f"  - 文件大小: {file_size:.2f} MB")
            break
        else:
            logger.info(f"    ❌ 文件不存在")
    
    if not ocr_model_path:
        logger.error("=" * 70)
        logger.error("❌ OCR模型文件不存在")
        logger.error("   已检查的路径:")
        for path in possible_ocr_paths:
            logger.error(f"     - {path} (存在: {path.exists()})")
        logger.error("=" * 70)
        raise FileNotFoundError("OCR模型文件不存在")
    
    logger.info("  - 正在检查 OCR 配置文件...")
    logger.info(f"    配置文件路径: {OCR_CONFIG_FILE}")
    if not OCR_CONFIG_FILE.exists():
        logger.error("=" * 70)
        logger.error(f"❌ OCR配置文件不存在: {OCR_CONFIG_FILE}")
        logger.error("=" * 70)
        raise FileNotFoundError(f"OCR配置文件不存在: {OCR_CONFIG_FILE}")
    logger.info(f"  ✅ OCR 配置文件存在")
    
    try:
        # 读取配置
        logger.info("  - 正在读取配置文件...")
        config_start = time.time()
        with open(OCR_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        config_elapsed = time.time() - config_start
        logger.info(f"  ✅ 配置文件读取成功（耗时 {config_elapsed:.2f} 秒）")
        
        # 修复字符字典配置：优先使用本地 PaddleOCR 源码的字典
        logger.info("  - 正在查找字符字典文件...")
        en_dict_candidates = [
            PROJECT_ROOT / 'PaddleOCR' / 'ppocr' / 'utils' / 'en_dict.txt',
        ]
        # 尝试从paddleocr包中获取
        try:
            import paddleocr as paddleocr_pkg
            import os
            paddleocr_root = Path(os.path.dirname(paddleocr_pkg.__file__))
            en_dict_candidates.insert(0, paddleocr_root / 'ppocr' / 'utils' / 'en_dict.txt')
            logger.info(f"    - 检查 paddleocr 包路径: {paddleocr_root}")
        except Exception as e:
            logger.info(f"    - 无法从 paddleocr 包获取路径: {e}")
        
        dict_found = False
        for i, en_dict_path in enumerate(en_dict_candidates, 1):
            logger.info(f"    [{i}/{len(en_dict_candidates)}] 检查字典路径: {en_dict_path}")
            if en_dict_path.exists():
                config['Global']['character_dict_path'] = str(en_dict_path)
                config['Global']['use_space_char'] = True
                logger.info(f"  ✅ 使用字符字典: {en_dict_path}")
                dict_found = True
                break
            else:
                logger.info(f"      ❌ 文件不存在")
        
        if not dict_found:
            logger.warning("  ⚠️  未找到字符字典文件，使用默认配置")
        
        # 设置设备（Render通常没有GPU，使用CPU）
        logger.info("  - 正在设置计算设备...")
        use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'
        logger.info(f"    USE_GPU 环境变量: {use_gpu}")
        if use_gpu and paddle.device.is_compiled_with_cuda():
            paddle.set_device('gpu:0')
            logger.info("  ✅ 使用 GPU")
        else:
            paddle.set_device('cpu')
            logger.info("  ✅ 使用 CPU")
        
        # 优化内存使用（Render Free Plan 只有 512MB）
        logger.info("  - 正在优化内存使用...")
        os.environ['FLAGS_allocator_strategy'] = 'auto_growth'  # 自动增长内存分配
        logger.info("  ✅ 内存优化设置完成")
        
        # 构建后处理
        logger.info("  - 正在构建后处理器...")
        post_process_start = time.time()
        post_process_class = build_post_process(config['PostProcess'], config['Global'])
        post_process_elapsed = time.time() - post_process_start
        logger.info(f"  ✅ 后处理器构建成功（耗时 {post_process_elapsed:.2f} 秒）")
        
        # 修复 MultiHead 配置
        if config['Architecture']['Head']['name'] == 'MultiHead':
            logger.info("  - 检测到 MultiHead 架构，正在修复配置...")
            char_num = len(getattr(post_process_class, 'character'))
            logger.info(f"    字符字典实际字符数: {char_num}")
            
            out_channels_list = {}
            out_channels_list['CTCLabelDecode'] = char_num
            out_channels_list['SARLabelDecode'] = char_num + 2
            out_channels_list['NRTRLabelDecode'] = char_num + 3
            config['Architecture']['Head']['out_channels_list'] = out_channels_list
            logger.info("  ✅ MultiHead 配置修复完成")
        
        # 构建模型
        logger.info("  - 正在构建 OCR 模型架构...")
        model_build_start = time.time()
        ocr_model = build_model(config['Architecture'])
        model_build_elapsed = time.time() - model_build_start
        logger.info(f"  ✅ 模型架构构建成功（耗时 {model_build_elapsed:.2f} 秒）")
        
        # 加载权重
        logger.info("  - 正在加载模型权重...")
        logger.info(f"    权重文件: {ocr_model_path}")
        weight_load_start = time.time()
        state_dict = paddle.load(str(ocr_model_path))
        ocr_model.set_state_dict(state_dict)
        ocr_model.eval()
        weight_load_elapsed = time.time() - weight_load_start
        logger.info(f"  ✅ 模型权重加载成功（耗时 {weight_load_elapsed:.2f} 秒）")
        logger.info("✅ OCR模型加载完成")
        
        # 3. 准备数据变换
        logger.info("[2.3/3] 准备数据变换...")
        logger.info("  - 正在读取评估数据变换配置...")
        eval_transforms = config['Eval']['dataset']['transforms'].copy()
        logger.info(f"  - 原始变换数量: {len(eval_transforms)}")
        transforms = []
        for op in eval_transforms:
            op_name = list(op)[0]
            if "Label" in op_name:
                logger.info(f"    - 跳过标签变换: {op_name}")
                continue
            elif op_name in ["RecResizeImg"]:
                op[op_name]["infer_mode"] = True
                logger.info(f"    - 设置推理模式: {op_name}")
            elif op_name == "KeepKeys":
                op[op_name]["keep_keys"] = ["image"]
                logger.info(f"    - 设置保留键: {op_name}")
            transforms.append(op)
        
        logger.info(f"  - 最终变换数量: {len(transforms)}")
        config['Global']["infer_mode"] = True
        logger.info("  - 正在创建变换操作符...")
        transform_start = time.time()
        eval_ops = create_operators(transforms, config['Global'])
        transform_elapsed = time.time() - transform_start
        logger.info(f"  ✅ 数据变换准备完成（耗时 {transform_elapsed:.2f} 秒）")
        
        logger.info("=" * 70)
        logger.info("✅ 所有模型加载完成！")
        logger.info("=" * 70)
        
    except FileNotFoundError as e:
        logger.error("=" * 70)
        logger.error(f"❌ 文件未找到错误")
        logger.error(f"   错误信息: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        raise
    except Exception as e:
        logger.error("=" * 70)
        logger.error(f"❌ OCR模型加载失败")
        logger.error(f"   错误类型: {type(e).__name__}")
        logger.error(f"   错误信息: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        raise

# ===== 推理函数 =====
def process_image_sync(image_bytes: bytes) -> Dict:
    """
    同步处理图片（在线程池中运行）
    
    Args:
        image_bytes: 图片字节数据
        
    Returns:
        识别结果字典
    """
    start_time = time.time()
    
    try:
        # 1. 将字节转换为numpy数组
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {
                'success': False,
                'error': '无法解码图片数据'
            }
        
        img_height, img_width = img.shape[:2]
        
        # 2. YOLO检测code区域
        code_bbox = None
        
        # 保存临时文件供YOLO使用
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, img)
        
        try:
            # 检查numpy是否可用
            try:
                import numpy as np
                np.array([1, 2, 3])  # 测试numpy基本功能
            except Exception as np_error:
                logger.error(f"numpy检查失败: {np_error}")
                return {
                    'success': False,
                    'error': f'numpy不可用: {str(np_error)}'
                }
            
            results = yolo_model(str(tmp_path), verbose=False)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    if class_id == 1:  # code区域
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        code_bbox = (x1, y1, x2, y2)
                        break
                if code_bbox:
                    break
        except Exception as yolo_error:
            logger.error(f"YOLO检测失败: {yolo_error}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': f'YOLO检测失败: {str(yolo_error)}'
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        if code_bbox is None:
            return {
                'success': False,
                'error': '未检测到code区域'
            }
        
        # 3. 裁剪code区域
        x1, y1, x2, y2 = code_bbox
        code_region = img[y1:y2, x1:x2]
        
        # 4. 预处理
        processed = preprocess_code_region(code_region)
        
        # 5. OCR识别
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, processed)
        
        try:
            with open(tmp_path, 'rb') as f:
                img_bytes = f.read()
            
            data = {'image': img_bytes}
            batch = transform(data, eval_ops)
            
            images = np.expand_dims(batch[0], axis=0)
            images = paddle.to_tensor(images)
            
            with paddle.no_grad():
                preds = ocr_model(images)
            
            if isinstance(preds, (list, tuple)):
                preds_for_decode = preds[0]
            else:
                preds_for_decode = preds
            
            post_result = post_process_class(preds_for_decode)
            
            # 解析结果
            if isinstance(post_result, dict):
                if 'CTCLabelDecode' in post_result:
                    result_list = post_result['CTCLabelDecode']
                elif 'SARLabelDecode' in post_result:
                    result_list = post_result['SARLabelDecode']
                else:
                    result_list = list(post_result.values())[0]
                
                if isinstance(result_list, list) and len(result_list) > 0:
                    if isinstance(result_list[0], (list, tuple)) and len(result_list[0]) >= 2:
                        pred_text = result_list[0][0]
                        pred_score = float(result_list[0][1])
                    else:
                        pred_text = str(result_list[0])
                        pred_score = 1.0
                else:
                    pred_text = ""
                    pred_score = 0.0
            elif isinstance(post_result, list) and len(post_result) > 0:
                if isinstance(post_result[0], (list, tuple)) and len(post_result[0]) >= 2:
                    pred_text = post_result[0][0]
                    pred_score = float(post_result[0][1])
                else:
                    pred_text = str(post_result[0])
                    pred_score = 1.0
            else:
                pred_text = ""
                pred_score = 0.0
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'text': pred_text,
                'confidence': pred_score,
                'bbox': code_bbox,
                'processing_time': processing_time
            }
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"处理图片时出错: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

# ===== API 路由 =====
# 延迟加载模型（避免启动超时）
# 模型将在第一次请求时加载，而不是在启动时加载
models_loading = False
models_loaded = False

async def ensure_models_loaded():
    """确保模型已加载（如果启动时加载失败，则延迟加载）"""
    global models_loading, models_loaded, yolo_model, ocr_model
    
    # 如果已经加载，直接返回
    if models_loaded and yolo_model is not None and ocr_model is not None:
        return
    
    # 如果正在加载，等待完成
    if models_loading:
        logger.info("=" * 70)
        logger.info("模型正在加载中，等待完成...")
        logger.info("=" * 70)
        wait_start = time.time()
        max_wait_time = 300  # 5分钟
        while models_loading:
            if time.time() - wait_start > max_wait_time:
                logger.error(f"❌ 等待模型加载超时（{max_wait_time}秒）")
                raise TimeoutError(f"模型加载超时（{max_wait_time}秒）")
            await asyncio.sleep(0.5)
            # 每10秒输出一次进度
            elapsed = time.time() - wait_start
            if int(elapsed) % 10 == 0 and elapsed > 0:
                logger.info(f"  仍在等待模型加载...（已等待 {elapsed:.0f} 秒）")
        logger.info("✅ 模型加载完成")
        return
    
    # 如果启动时加载失败，现在尝试加载
    if yolo_model is None or ocr_model is None:
        logger.info("=" * 70)
        logger.info("⚠️  启动时模型未加载，现在开始加载...")
        logger.info("=" * 70)
        models_loading = True
        try:
            logger.info("注意：Render Free Plan 资源有限，模型加载可能需要 5-10 分钟，请耐心等待...")
            loop = asyncio.get_event_loop()
            # 首次请求时加载，无超时限制（让用户等待）
            await loop.run_in_executor(executor, load_models)
            models_loaded = True
            logger.info("=" * 70)
            logger.info("✅ 模型加载完成，服务就绪")
            logger.info("=" * 70)
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ 模型加载失败")
            logger.error(f"   错误类型: {type(e).__name__}")
            logger.error(f"   错误信息: {e}")
            logger.error("=" * 70)
            models_loading = False
            import traceback
            traceback.print_exc()
            raise
        finally:
            models_loading = False

@app.get("/", response_model=HealthResponse)
async def root():
    """健康检查（不加载模型，快速响应）"""
    # 不加载模型，避免 Render 健康检查超时
    queue_size = request_queue.qsize()
    stats['current_queue_size'] = queue_size
    return {
        "status": "ok",
        "models_loaded": yolo_model is not None and ocr_model is not None,
        "queue_size": queue_size,
        "max_queue_size": MAX_QUEUE_SIZE,
        "active_workers": MAX_WORKERS,
        "stats": stats.copy()
    }

@app.get("/health", response_model=HealthResponse)
async def health():
    """健康检查（不加载模型，快速响应）"""
    # 不加载模型，避免 Render 健康检查超时
    queue_size = request_queue.qsize()
    stats['current_queue_size'] = queue_size
    return {
        "status": "ok",
        "models_loaded": yolo_model is not None and ocr_model is not None,
        "queue_size": queue_size,
        "max_queue_size": MAX_QUEUE_SIZE,
        "active_workers": MAX_WORKERS,
        "stats": stats.copy()
    }

@app.post("/ocr", response_model=OCRResponse)
async def ocr_endpoint(file: UploadFile = File(...)):
    """
    OCR识别接口（带排队和等待机制）
    
    上传图片，返回识别结果。
    如果所有worker都在忙，会等待直到有worker空闲（最多等待QUEUE_WAIT_TIMEOUT秒）
    如果队列满，也会等待直到有空位
    """
    stats['total_requests'] += 1
    queue_wait_start = time.time()
    
    # 确保模型已加载（延迟加载），捕获加载错误
    try:
        await ensure_models_loaded()
    except Exception as e:
        stats['failed_requests'] += 1
        logger.error(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return OCRResponse(
            success=False,
            error=f"模型加载失败: {str(e)}。请检查模型文件是否存在，或查看服务器日志。"
        )
    
    # 检查模型是否已加载
    if yolo_model is None or ocr_model is None:
        stats['failed_requests'] += 1
        return OCRResponse(
            success=False,
            error="模型未加载。请检查模型文件是否存在。"
        )
    
    # 读取图片数据
    try:
        image_bytes = await file.read()
    except Exception as e:
        stats['failed_requests'] += 1
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")
    
    # 检查文件大小（限制10MB）
    if len(image_bytes) > 10 * 1024 * 1024:
        stats['failed_requests'] += 1
        raise HTTPException(status_code=400, detail="图片文件过大（最大10MB）")
    
    # 等待队列有空位（用于统计和限流）
    try:
        await asyncio.wait_for(
            request_queue.put(None),  # 放入占位符，表示有一个请求在等待
            timeout=QUEUE_WAIT_TIMEOUT
        )
    except asyncio.TimeoutError:
        stats['failed_requests'] += 1
        raise HTTPException(
            status_code=503,
            detail=f"服务器繁忙，等待超时（{QUEUE_WAIT_TIMEOUT}秒）。请稍后重试。"
        )
    
    # 更新统计
    current_queue_size = request_queue.qsize()
    if current_queue_size > stats['max_queue_size_reached']:
        stats['max_queue_size_reached'] = current_queue_size
    
    # 等待有worker空闲（信号量会自动管理）
    try:
        # 获取信号量（如果所有worker都在忙，这里会等待）
        async with concurrency_semaphore:
            # 从队列中移除占位符
            try:
                request_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            
            queue_wait_time = time.time() - queue_wait_start
            
            # 在线程池中处理
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, process_image_sync, image_bytes),
                timeout=REQUEST_TIMEOUT
            )
            
            result['queue_wait_time'] = queue_wait_time
            
            if result.get('success'):
                stats['successful_requests'] += 1
            else:
                stats['failed_requests'] += 1
            
            return OCRResponse(**result)
    
    except asyncio.TimeoutError:
        stats['failed_requests'] += 1
        # 从队列中移除（超时）
        try:
            request_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        raise HTTPException(
            status_code=504,
            detail=f"处理超时（{REQUEST_TIMEOUT}秒）"
        )
    except Exception as e:
        stats['failed_requests'] += 1
        # 从队列中移除（出错）
        try:
            request_queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        logger.error(f"处理请求时出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

@app.post("/ocr-direct", response_model=OCRResponse)
async def ocr_direct_endpoint(file: UploadFile = File(...)):
    """
    OCR识别接口（直接处理，不排队）
    
    适用于低并发场景或测试
    """
    stats['total_requests'] += 1
    
    # 确保模型已加载（延迟加载），捕获加载错误
    try:
        await ensure_models_loaded()
    except Exception as e:
        stats['failed_requests'] += 1
        logger.error(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return OCRResponse(
            success=False,
            error=f"模型加载失败: {str(e)}。请检查模型文件是否存在，或查看服务器日志。"
        )
    
    # 检查模型是否已加载
    if yolo_model is None or ocr_model is None:
        stats['failed_requests'] += 1
        return OCRResponse(
            success=False,
            error="模型未加载。请检查模型文件是否存在。"
        )
    
    try:
        image_bytes = await file.read()
    except Exception as e:
        stats['failed_requests'] += 1
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")
    
    if len(image_bytes) > 10 * 1024 * 1024:
        stats['failed_requests'] += 1
        raise HTTPException(status_code=400, detail="图片文件过大（最大10MB）")
    
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, process_image_sync, image_bytes),
            timeout=REQUEST_TIMEOUT
        )
        
        if result.get('success'):
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1
        
        return OCRResponse(**result)
    
    except asyncio.TimeoutError:
        stats['failed_requests'] += 1
        raise HTTPException(
            status_code=504,
            detail=f"处理超时（{REQUEST_TIMEOUT}秒）"
        )
    except Exception as e:
        stats['failed_requests'] += 1
        logger.error(f"处理请求时出错: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 70)
    logger.info("🚀 启动服务器...")
    logger.info("=" * 70)
    
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("UVICORN_WORKERS", "1"))  # Render建议用1个worker，用线程池处理并发
    
    logger.info(f"端口: {port}")
    logger.info(f"Workers: {workers}")
    logger.info(f"Host: 0.0.0.0")
    logger.info("=" * 70)
    logger.info("服务器正在启动，模型将在首次请求时加载...")
    logger.info("=" * 70)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            workers=workers,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
