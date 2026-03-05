"""
OCR API客户端示例
演示如何调用OCR API
"""

import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json
from pathlib import Path

def ocr_image(image_path, api_url="http://localhost:8000", use_direct=False):
    """
    上传图片进行OCR识别
    
    Args:
        image_path: 图片路径
        api_url: API服务器地址
        use_direct: 是否使用直接处理（不排队）
    
    Returns:
        识别结果字典
    """
    endpoint = "/ocr-direct" if use_direct else "/ocr"
    url = f"{api_url}{endpoint}"
    
    image_path = Path(image_path)
    if not image_path.exists():
        return {"success": False, "error": f"图片文件不存在: {image_path}"}
    
    print(f"📷 上传图片: {image_path}")
    print(f"🔗 API地址: {url}")
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            print("⏳ 正在处理...")
            response = requests.post(url, files=files, timeout=120)
        
        response.raise_for_status()
        result = response.json()
        
        return result
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时（>120秒）"}
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            return {"success": False, "error": error_data.get('detail', str(e))}
        except:
            return {"success": False, "error": f"HTTP错误: {e.response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"请求失败: {str(e)}"}

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR API客户端示例')
    parser.add_argument('--image', type=str, required=True, help='图片路径')
    parser.add_argument('--url', type=str, default='http://localhost:8000', help='API服务器地址')
    parser.add_argument('--direct', action='store_true', help='使用直接处理（不排队）')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("OCR API 客户端示例")
    print("=" * 70)
    print()
    
    # 调用API
    result = ocr_image(args.image, args.url, use_direct=args.direct)
    
    # 显示结果
    print()
    print("=" * 70)
    print("识别结果")
    print("=" * 70)
    
    if result.get('success'):
        print(f"✅ 识别成功!")
        print(f"   识别结果: {result['text']}")
        print(f"   置信度: {result['confidence']:.4f}")
        if result.get('bbox'):
            bbox = result['bbox']
            print(f"   Code区域: ({bbox[0]}, {bbox[1]}) -> ({bbox[2]}, {bbox[3]})")
        if 'processing_time' in result:
            print(f"   处理时间: {result['processing_time']:.2f}秒")
        if 'queue_wait_time' in result:
            print(f"   队列等待: {result['queue_wait_time']:.2f}秒")
    else:
        print(f"❌ 识别失败")
        print(f"   错误: {result.get('error', '未知错误')}")
    
    print("=" * 70)
    
    # 返回JSON格式（用于脚本调用）
    if '--json' in sys.argv:
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
