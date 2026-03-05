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
from typing import Optional, Dict, Tuple
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

# 添加PaddleOCR路径
PROJECT_ROOT = Path(__file__).parent.parent  # server文件夹的父目录
PADDLEOCR_DIR = PROJECT_ROOT / 'PaddleOCR'
if PADDLEOCR_DIR.exists():
    sys.path.insert(0, str(PADDLEOCR_DIR))

# 注意：使用numpy 2.0以兼容用numpy 2.0训练的模型文件
# 不再需要兼容性修复，因为环境已升级到numpy 2.0

import paddle
from ppocr.modeling.architectures import build_model
from ppocr.postprocess import build_post_process
from ppocr.data import create_operators, transform
import yaml
from ultralytics import YOLO

# ===== 配置 =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
app = FastAPI(
    title="TCG OCR API",
    version="1.0.0",
    description="TCG卡片Code区域OCR识别API服务"
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
    
    logger.info("=" * 70)
    logger.info("开始加载模型...")
    logger.info("=" * 70)
    
    # 1. 加载 YOLO 模型
    logger.info("[1/3] 加载 YOLO 模型...")
    yolo_path = None
    for path in possible_yolo_paths:
        if path.exists():
            yolo_path = path
            break
    
    if yolo_path:
        try:
            yolo_model = YOLO(str(yolo_path))
            logger.info(f"✅ YOLO模型加载成功: {yolo_path}")
        except Exception as e:
            logger.error(f"❌ YOLO模型加载失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    else:
        logger.warning("⚠️  未找到YOLO模型文件")
        raise FileNotFoundError("YOLO模型文件不存在")
    
    # 2. 加载 OCR 模型
    logger.info("[2/3] 加载 OCR 模型...")
    
    ocr_model_path = None
    for path in possible_ocr_paths:
        if path.exists():
            ocr_model_path = path
            break
    
    if not ocr_model_path:
        raise FileNotFoundError("OCR模型文件不存在")
    
    if not OCR_CONFIG_FILE.exists():
        raise FileNotFoundError(f"OCR配置文件不存在: {OCR_CONFIG_FILE}")
    
    try:
        # 读取配置
        with open(OCR_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 修复字符字典配置
        en_dict_path = PROJECT_ROOT / 'PaddleOCR' / 'ppocr' / 'utils' / 'en_dict.txt'
        if en_dict_path.exists():
            config['Global']['character_dict_path'] = str(en_dict_path)
            config['Global']['use_space_char'] = True
            logger.info(f"✅ 使用字符字典: {en_dict_path}")
        
        # 设置设备（Render通常没有GPU，使用CPU）
        use_gpu = os.getenv('USE_GPU', 'false').lower() == 'true'
        if use_gpu and paddle.device.is_compiled_with_cuda():
            paddle.set_device('gpu:0')
            logger.info("✅ 使用 GPU")
        else:
            paddle.set_device('cpu')
            logger.info("✅ 使用 CPU")
        
        # 构建后处理
        post_process_class = build_post_process(config['PostProcess'], config['Global'])
        
        # 修复 MultiHead 配置
        if config['Architecture']['Head']['name'] == 'MultiHead':
            char_num = len(getattr(post_process_class, 'character'))
            logger.info(f"   字符字典实际字符数: {char_num}")
            
            out_channels_list = {}
            out_channels_list['CTCLabelDecode'] = char_num
            out_channels_list['SARLabelDecode'] = char_num + 2
            out_channels_list['NRTRLabelDecode'] = char_num + 3
            config['Architecture']['Head']['out_channels_list'] = out_channels_list
        
        # 构建模型
        ocr_model = build_model(config['Architecture'])
        
        # 加载权重
        logger.info(f"   加载模型权重: {ocr_model_path}")
        state_dict = paddle.load(str(ocr_model_path))
        ocr_model.set_state_dict(state_dict)
        ocr_model.eval()
        
        logger.info("✅ OCR模型加载完成")
        
        # 3. 准备数据变换
        logger.info("[3/3] 准备数据变换...")
        eval_transforms = config['Eval']['dataset']['transforms'].copy()
        transforms = []
        for op in eval_transforms:
            op_name = list(op)[0]
            if "Label" in op_name:
                continue
            elif op_name in ["RecResizeImg"]:
                op[op_name]["infer_mode"] = True
            elif op_name == "KeepKeys":
                op[op_name]["keep_keys"] = ["image"]
            transforms.append(op)
        
        config['Global']["infer_mode"] = True
        eval_ops = create_operators(transforms, config['Global'])
        logger.info("✅ 数据变换准备完成")
        
        logger.info("=" * 70)
        logger.info("✅ 所有模型加载完成！")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ OCR模型加载失败: {e}")
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
@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    try:
        load_models()
        logger.info(f"服务器配置: MAX_WORKERS={MAX_WORKERS}, MAX_QUEUE_SIZE={MAX_QUEUE_SIZE}")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        raise

@app.get("/", response_model=HealthResponse)
async def root():
    """健康检查"""
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
    """健康检查（详细）"""
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
    queue_wait_start = time.time()
    stats['total_requests'] += 1
    
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
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("UVICORN_WORKERS", "1"))  # Render建议用1个worker，用线程池处理并发
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=workers,
        log_level="info"
    )
