"""
启动服务器并测试
"""
import sys
import io
from pathlib import Path
import subprocess
import time
import requests

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 70)
print("启动服务器并测试")
print("=" * 70)

# 启动服务器
print("\n[1/3] 启动服务器...")
server_process = subprocess.Popen(
    [sys.executable, "server.py"],
    cwd=str(Path(__file__).parent),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    bufsize=1
)

# 等待服务器启动
print("等待服务器启动...")
time.sleep(15)

# 检查服务器是否运行
print("\n[2/3] 检查服务器状态...")
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    if response.status_code == 200:
        print("✅ 服务器运行正常！")
        print(f"响应: {response.json()}")
    else:
        print(f"❌ 服务器返回错误状态码: {response.status_code}")
except Exception as e:
    print(f"❌ 无法连接到服务器: {e}")
    print("\n服务器输出:")
    try:
        output, _ = server_process.communicate(timeout=5)
        print(output)
    except:
        pass

# 测试OCR
print("\n[3/3] 测试OCR...")
try:
    from pathlib import Path
    test_image = Path(__file__).parent.parent / 'data' / 'sample.jpg'
    if test_image.exists():
        with open(test_image, 'rb') as f:
            files = {'image': f}
            response = requests.post('http://localhost:8000/ocr', files=files, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ OCR识别成功!")
                print(f"   识别结果: {result.get('text', 'N/A')}")
                print(f"   置信度: {result.get('confidence', 'N/A')}")
            else:
                print(f"❌ OCR请求失败: {response.status_code}")
                print(f"   响应: {response.text}")
    else:
        print(f"⚠️  测试图片不存在: {test_image}")
except Exception as e:
    print(f"❌ OCR测试失败: {e}")
    import traceback
    traceback.print_exc()

# 停止服务器
print("\n停止服务器...")
server_process.terminate()
try:
    server_process.wait(timeout=5)
except:
    server_process.kill()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
