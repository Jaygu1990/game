# API 使用示例

## 端点说明

### 1. 健康检查
- **URL**: `GET /health` 或 `GET /`
- **用途**: 检查服务器状态和模型加载情况

### 2. OCR识别（带排队）
- **URL**: `POST /ocr`
- **用途**: 上传图片进行OCR识别，支持排队机制
- **参数**: `file` (multipart/form-data)

### 3. OCR识别（直接处理）
- **URL**: `POST /ocr-direct`
- **用途**: 上传图片进行OCR识别，不排队（适合测试）
- **参数**: `file` (multipart/form-data)

## 使用示例

### 方法1: 使用curl（命令行）

```bash
# OCR识别（带排队）
curl -X POST "http://localhost:8000/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample.jpg"

# OCR识别（直接处理）
curl -X POST "http://localhost:8000/ocr-direct" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/sample.jpg"
```

### 方法2: 使用Python requests

```python
import requests

# 上传图片并识别
with open('data/sample.jpg', 'rb') as f:
    files = {'file': ('sample.jpg', f, 'image/jpeg')}
    response = requests.post(
        'http://localhost:8000/ocr',
        files=files
    )

result = response.json()
print(f"识别结果: {result['text']}")
print(f"置信度: {result['confidence']}")
print(f"处理时间: {result['processing_time']:.2f}秒")
```

### 方法3: 使用测试脚本

```bash
# 使用提供的测试脚本
python server/test_api.py --image data/sample.jpg

# 或指定API地址
python server/test_api.py --url http://localhost:8000 --image data/sample.jpg
```

## 响应格式

### 成功响应

```json
{
  "success": true,
  "text": "088/063",
  "confidence": 0.95,
  "bbox": [100, 200, 300, 250],
  "processing_time": 0.35,
  "queue_wait_time": 0.12
}
```

**字段说明：**
- `success`: 是否成功（true/false）
- `text`: 识别出的文字
- `confidence`: 置信度（0-1之间）
- `bbox`: Code区域的边界框坐标 [x1, y1, x2, y2]
- `processing_time`: 处理时间（秒）
- `queue_wait_time`: 队列等待时间（秒，仅/ocr端点）

### 错误响应

```json
{
  "success": false,
  "error": "未检测到code区域",
  "text": null,
  "confidence": null,
  "bbox": null
}
```

## 完整Python示例

```python
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
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': (image_path.name, f, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=120)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        return {"success": False, "error": "请求超时"}
    except requests.exceptions.HTTPError as e:
        try:
            error_data = e.response.json()
            return {"success": False, "error": error_data.get('detail', str(e))}
        except:
            return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 使用示例
if __name__ == "__main__":
    result = ocr_image("data/sample.jpg")
    
    if result.get('success'):
        print(f"✅ 识别成功!")
        print(f"   识别结果: {result['text']}")
        print(f"   置信度: {result['confidence']:.4f}")
        print(f"   Code区域: {result['bbox']}")
        print(f"   处理时间: {result.get('processing_time', 0):.2f}秒")
        if 'queue_wait_time' in result:
            print(f"   队列等待: {result['queue_wait_time']:.2f}秒")
    else:
        print(f"❌ 识别失败: {result.get('error', '未知错误')}")
```

## 从移动端/前端调用

### JavaScript (Fetch API)

```javascript
async function ocrImage(imageFile) {
    const formData = new FormData();
    formData.append('file', imageFile);
    
    try {
        const response = await fetch('http://localhost:8000/ocr', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('识别结果:', result.text);
            console.log('置信度:', result.confidence);
            return result;
        } else {
            console.error('识别失败:', result.error);
            return null;
        }
    } catch (error) {
        console.error('请求失败:', error);
        return null;
    }
}

// 使用示例
const fileInput = document.querySelector('input[type="file"]');
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        const result = await ocrImage(file);
        if (result) {
            document.getElementById('result').textContent = result.text;
        }
    }
});
```

### React示例

```jsx
import React, { useState } from 'react';

function OCRUpload() {
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('http://localhost:8000/ocr', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('上传失败:', error);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div>
            <input type="file" onChange={handleUpload} accept="image/*" />
            {loading && <p>处理中...</p>}
            {result && result.success && (
                <div>
                    <p>识别结果: {result.text}</p>
                    <p>置信度: {(result.confidence * 100).toFixed(2)}%</p>
                </div>
            )}
        </div>
    );
}
```

## 错误处理

### 常见错误

1. **文件过大**
   ```json
   {
     "detail": "图片文件过大（最大10MB）"
   }
   ```
   解决：压缩图片或使用更小的图片

2. **未检测到code区域**
   ```json
   {
     "success": false,
     "error": "未检测到code区域"
   }
   ```
   解决：确保图片中包含code区域，或调整YOLO检测阈值

3. **服务器繁忙**
   ```json
   {
     "detail": "服务器繁忙，等待超时（300秒）。请稍后重试。"
   }
   ```
   解决：稍后重试，或使用/ocr-direct端点

4. **处理超时**
   ```json
   {
     "detail": "处理超时（60秒）"
   }
   ```
   解决：检查图片大小，或联系管理员增加超时时间

## 性能建议

1. **图片大小**：建议图片大小 < 5MB，分辨率适中
2. **并发请求**：使用/ocr端点会自动排队，无需担心并发
3. **超时设置**：建议客户端设置120秒超时
4. **错误重试**：建议实现指数退避重试机制
