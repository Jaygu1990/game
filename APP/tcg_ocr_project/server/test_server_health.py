"""
测试服务器健康状态
"""

import sys
import io

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json

try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    print("=" * 70)
    print("服务器健康检查")
    print("=" * 70)
    print(f"状态码: {response.status_code}")
    print("\n响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("\n" + "=" * 70)
    print("✅ 服务器运行正常！")
    print("=" * 70)
except requests.exceptions.ConnectionError:
    print("[ERROR] 无法连接到服务器，请确保服务器正在运行")
    print("   运行: python server.py")
except Exception as e:
    print(f"[ERROR] 错误: {e}")
