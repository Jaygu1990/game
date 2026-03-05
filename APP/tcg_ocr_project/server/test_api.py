"""
测试TCG OCR API服务器
"""

import requests
import time
from pathlib import Path

# API地址（本地测试）
API_BASE_URL = "http://localhost:8000"

# 测试图片路径（相对于项目根目录）
TEST_IMAGE = Path(__file__).parent.parent / "data" / "sample.jpg"

def test_health():
    """测试健康检查接口"""
    print("=" * 70)
    print("测试健康检查接口...")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ 服务状态: {data['status']}")
        print(f"✅ 模型已加载: {data['models_loaded']}")
        print(f"✅ 当前队列大小: {data['queue_size']}")
        print(f"✅ 最大队列大小: {data['max_queue_size']}")
        print(f"✅ 活跃Workers: {data['active_workers']}")
        print(f"\n统计信息:")
        for key, value in data['stats'].items():
            print(f"  - {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_ocr(image_path: Path, use_direct: bool = False):
    """测试OCR识别接口"""
    endpoint = "/ocr-direct" if use_direct else "/ocr"
    print("=" * 70)
    print(f"测试OCR识别接口: {endpoint}")
    print("=" * 70)
    
    if not image_path.exists():
        print(f"❌ 测试图片不存在: {image_path}")
        return False
    
    print(f"📷 图片路径: {image_path}")
    
    try:
        start_time = time.time()
        
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                files=files,
                timeout=120  # 2分钟超时
            )
        
        total_time = time.time() - start_time
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print(f"✅ 识别成功!")
            print(f"   识别结果: {data['text']}")
            print(f"   置信度: {data['confidence']:.4f}")
            print(f"   Code区域: {data['bbox']}")
            print(f"   处理时间: {data.get('processing_time', 0):.2f}秒")
            if 'queue_wait_time' in data:
                print(f"   队列等待时间: {data['queue_wait_time']:.2f}秒")
            print(f"   总耗时: {total_time:.2f}秒")
        else:
            print(f"❌ 识别失败: {data.get('error', '未知错误')}")
        
        return data.get('success', False)
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时（>120秒）")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
        if e.response is not None:
            try:
                error_data = e.response.json()
                print(f"   错误详情: {error_data.get('detail', '无详情')}")
            except:
                print(f"   响应内容: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_concurrent_requests(image_path: Path, num_requests: int = 5):
    """测试并发请求"""
    print("=" * 70)
    print(f"测试并发请求（{num_requests}个请求）...")
    print("=" * 70)
    
    if not image_path.exists():
        print(f"❌ 测试图片不存在: {image_path}")
        return
    
    import concurrent.futures
    
    def send_request(index):
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/jpeg')}
                response = requests.post(
                    f"{API_BASE_URL}/ocr",
                    files=files,
                    timeout=120
                )
                response.raise_for_status()
                data = response.json()
                return {
                    'index': index,
                    'success': data.get('success', False),
                    'text': data.get('text', ''),
                    'queue_wait_time': data.get('queue_wait_time', 0),
                    'processing_time': data.get('processing_time', 0)
                }
        except Exception as e:
            return {
                'index': index,
                'success': False,
                'error': str(e)
            }
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(send_request, i) for i in range(num_requests)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    
    print(f"\n并发测试结果:")
    print(f"  总耗时: {total_time:.2f}秒")
    print(f"  平均每个请求: {total_time/num_requests:.2f}秒")
    
    success_count = sum(1 for r in results if r.get('success'))
    print(f"  成功: {success_count}/{num_requests}")
    
    if success_count > 0:
        avg_queue_wait = sum(r.get('queue_wait_time', 0) for r in results if r.get('success')) / success_count
        avg_processing = sum(r.get('processing_time', 0) for r in results if r.get('success')) / success_count
        print(f"  平均队列等待时间: {avg_queue_wait:.2f}秒")
        print(f"  平均处理时间: {avg_processing:.2f}秒")
    
    print(f"\n详细结果:")
    for result in sorted(results, key=lambda x: x['index']):
        if result.get('success'):
            print(f"  请求{result['index']}: ✅ {result.get('text', 'N/A')} "
                  f"(等待:{result.get('queue_wait_time', 0):.2f}s, "
                  f"处理:{result.get('processing_time', 0):.2f}s)")
        else:
            print(f"  请求{result['index']}: ❌ {result.get('error', '未知错误')}")

def main():
    """主函数"""
    print("=" * 70)
    print("TCG OCR API 测试工具")
    print("=" * 70)
    
    # 1. 健康检查
    if not test_health():
        print("\n⚠️  服务可能未启动，请先运行: python server.py")
        return
    
    print("\n")
    
    # 2. 测试单张图片（带排队）
    if TEST_IMAGE.exists():
        test_ocr(TEST_IMAGE, use_direct=False)
        print("\n")
        
        # 3. 测试单张图片（直接处理）
        test_ocr(TEST_IMAGE, use_direct=True)
        print("\n")
        
        # 4. 测试并发请求
        test_concurrent_requests(TEST_IMAGE, num_requests=5)
    else:
        print(f"⚠️  测试图片不存在: {TEST_IMAGE}")
        print("   请提供图片路径作为参数，例如:")
        print("   python test_api.py --image path/to/image.jpg")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='测试TCG OCR API')
    parser.add_argument('--image', type=str, help='测试图片路径')
    parser.add_argument('--url', type=str, default=API_BASE_URL, help='API地址（默认: http://localhost:8000）')
    parser.add_argument('--concurrent', type=int, help='并发请求数量')
    
    args = parser.parse_args()
    
    if args.url:
        API_BASE_URL = args.url
    
    if args.image:
        image_path = Path(args.image)
        if image_path.exists():
            test_ocr(image_path)
            if args.concurrent:
                test_concurrent_requests(image_path, num_requests=args.concurrent)
        else:
            print(f"❌ 图片不存在: {image_path}")
    else:
        main()
