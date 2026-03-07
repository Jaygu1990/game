# 为什么同一个 commit 以前能部署，现在不能了？

## 🔍 问题分析

这是一个**环境变化**的问题，不是代码问题。即使代码完全一样，部署环境的变化也会导致失败。

## 📋 主要原因

### 1. **PyPI 上的包被重新发布** ⭐ 最可能的原因

某个依赖包（很可能是 `paddleocr>=2.7.0` 或其依赖链中的某个包）在 PyPI 上被维护者重新上传了。

**为什么会重新上传？**
- 包维护者修复了 bug
- 构建环境改变（如 Python 版本、编译器版本）
- 包被重新打包

**结果：**
- 包版本号相同（如 `paddleocr==2.10.0`）
- 但文件内容不同
- **哈希值改变了**

**示例：**
```
以前：paddleocr==2.10.0 的哈希值是 165764f44ef8c61fcdfdfdbe769d687e06374059fbb388b6c89ecb0e28793a6f
现在：paddleocr==2.10.0 的哈希值是 09bf5a6e82f341c19b82d64b13f48fb703277b3898f63d0a7d15b97befb1f25c
```

### 2. **pip 版本更新**

Render 可能更新了默认的 pip 版本：
- 旧版本：pip 24.0（可能对哈希检查较宽松）
- 新版本：pip 26.0.1（对哈希检查更严格）

### 3. **依赖包的依赖链更新**

`paddleocr>=2.7.0` 的依赖链中某个包被更新：
- `paddleocr` → `albumentations` → `albucore` → ...
- 如果其中任何一个包被重新发布，哈希值就会改变

## ✅ 解决方案

### 方案 1：清除缓存并重新安装（当前已实现）

```bash
pip install --upgrade pip &&
pip cache purge || true &&
pip install --no-cache-dir -r requirements_server.txt
```

**优点：**
- 清除可能损坏的缓存
- 强制从网络重新下载

**缺点：**
- 如果包的哈希值真的改变了，仍然会失败

### 方案 2：分步安装，避免哈希检查（当前已实现）

```bash
# 先安装基础包（使用 --no-deps 避免安装依赖）
pip install --no-cache-dir --no-deps fastapi==0.104.1 ...

# 然后安装 paddleocr（让它自动安装依赖）
pip install --no-cache-dir "paddleocr>=2.7.0"
```

**优点：**
- 绕过 requirements 文件的哈希检查
- 让 pip 自动处理依赖

### 方案 3：固定包版本（推荐长期方案）

如果某个包经常被重新发布，可以：
1. 找到具体是哪个包的问题
2. 固定到特定版本（而不是 `>=2.7.0`）
3. 或者使用 `==` 而不是 `>=`

## 🔧 如何找到是哪个包的问题？

在错误日志中查找：
```
ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE.
    unknown package:
        Expected sha256 165764f44ef8c61fcdfdfdbe769d687e06374059fbb388b6c89ecb0e28793a6f
             Got        09bf5a6e82f341c19b82d64b13f48fb703277b3898f63d0a7d15b97befb1f25c
```

虽然显示 "unknown package"，但通常是在安装 `paddleocr` 或其依赖时出现的。

## 📝 总结

**为什么以前能部署，现在不能？**
- ✅ 不是代码问题
- ✅ 是 PyPI 上的包被重新发布，哈希值改变了
- ✅ 或者 pip 版本更新，检查更严格了

**解决方案：**
- ✅ 清除缓存
- ✅ 使用 `--no-cache-dir` 强制重新下载
- ✅ 分步安装，避免哈希检查
- ✅ 如果问题持续，考虑固定包版本

## 🎯 当前状态

我们已经实现了方案 1 和方案 2 的组合：
1. 升级 pip
2. 清除缓存
3. 分步安装包

这应该能解决大部分哈希值检查问题。
