# 安装 Visual C++ Redistributable 指南

## 问题
torch DLL加载失败：
```
OSError: [WinError 127] The specified procedure could not be found. 
Error loading "D:\Anaconda3\Lib\site-packages\torch\lib\shm.dll" or one of its dependencies.
```

## 解决方案：安装 Visual C++ Redistributable

### 步骤1：下载安装程序

**方法1：直接下载（推荐）**
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe
- 或者访问：https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

**方法2：使用PowerShell下载**
```powershell
# 下载到当前目录
Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vc_redist.x64.exe" -OutFile "$env:TEMP\vc_redist.x64.exe"
```

### 步骤2：安装

1. 运行下载的 `vc_redist.x64.exe`
2. 选择"安装"
3. 等待安装完成
4. **重要：重启计算机**

### 步骤3：验证安装

运行以下命令检查是否安装成功：
```powershell
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" | Where-Object {$_.DisplayName -like "*Visual C++*Redistributable*"} | Select-Object DisplayName, DisplayVersion
```

应该看到类似：
```
DisplayName                              DisplayVersion
-----------                              --------------
Microsoft Visual C++ 2015-2022 Redistributable (x64) - 14.40.33807
```

### 步骤4：测试服务器

重启后，运行：
```bash
cd server
python server.py
```

如果仍然失败，尝试：
```bash
python -c "import torch; print('torch导入成功')"
python -c "import albumentations; print('albumentations导入成功')"
```

## 如果问题仍然存在

如果安装Visual C++ Redistributable后问题仍然存在，可以尝试：

1. **使用conda安装torch**（包含所有依赖）：
   ```bash
   conda install pytorch torchvision cpuonly -c pytorch
   ```

2. **延迟导入albumentations**（修改服务器代码）

3. **检查系统PATH环境变量**，确保包含torch的lib目录

## 相关链接

- Visual C++ Redistributable下载：https://aka.ms/vs/17/release/vc_redist.x64.exe
- PyTorch安装指南：https://pytorch.org/get-started/locally/
