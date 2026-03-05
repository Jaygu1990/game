# ✅ 部署前检查清单

## 📦 代码准备

- [ ] 所有代码已提交到Git
- [ ] `server/` 目录包含所有必要文件
- [ ] `server/render.yaml` 配置正确
- [ ] `server/requirements_server.txt` 包含所有依赖

## 📁 文件检查

- [ ] 模型文件在仓库中：
  - [ ] `models/detector_yolo/detector_yolov8s_best.pt` (YOLO模型)
  - [ ] `data/ocr_train/code/models/best_accuracy.pdparams` (OCR模型)
  - [ ] `data/ocr_train/code/config.yml` (OCR配置)
- [ ] `PaddleOCR/` 目录在仓库中
- [ ] `.gitignore` 已创建，排除不必要的文件

## 🔧 配置检查

- [ ] `server/render.yaml` 中的路径正确：
  - [ ] `buildCommand: cd server && pip install -r requirements_server.txt`
  - [ ] `startCommand: cd server && python server.py`
- [ ] `requirements_server.txt` 版本正确：
  - [ ] 如果模型用numpy 2.0训练：`numpy>=2.0.0`
  - [ ] 如果模型用numpy 1.x训练：`numpy<2.0.0`

## 🧪 本地测试（可选但推荐）

- [ ] 本地可以导入所有模块
- [ ] 服务器代码语法正确
- [ ] 模型文件路径正确

## 📤 Git提交

- [ ] 已添加所有必要文件：`git add server/ models/ data/ PaddleOCR/`
- [ ] 已提交：`git commit -m "Add server for Render deployment"`
- [ ] 已推送到GitHub：`git push origin main`

## 🌐 Render部署

- [ ] 已在Render创建Web Service
- [ ] 已连接GitHub仓库
- [ ] 已选择正确的分支
- [ ] 已配置环境变量（或使用render.yaml）
- [ ] 已选择Plan（推荐Starter $7/月）

## ✅ 部署后验证

- [ ] 构建成功（查看日志）
- [ ] 服务启动成功
- [ ] 健康检查通过：`curl https://your-service.onrender.com/health`
- [ ] OCR测试成功

## 🎯 完成！

部署成功后，保存服务URL，在Flutter APP中使用。
