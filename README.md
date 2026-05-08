# 🌸 生活规划本 Life Planner

一款可爱清新风格的桌面生活规划应用，基于 Python + tkinter 构建。

## 功能

- **日历** — 月视图，带优先级彩色标记和倒数日粉圈，支持点击年月跳转
- **待办清单** — 按日期管理事件，支持优先级（紧急/重要/普通）、拖动排序、双击编辑/删除
- **倒数日** — 支持不重复/每年/每月/每日重复，拖动排序，双击编辑/删除，到期自动清除
- **体重管理** — 记录体重和腰围，本周折线图，点击图表数据点可编辑/删除
- **周/月/年总结** — 带图表、任务统计和反思文本区
- **周/月/年计划** — 记录年计划、月计划、周计划
- **导出记录** — 将计划和总结导出成pdf

## 运行方式

需要 Python 3.x 和 Pillow（可选，用于窗口图标）。

```bash
pip install pillow
pythonw LifePlanner.py
```

或双击桌面上的 `启动生活规划本.bat` 启动（无控制台窗口）。

## 数据

本地模式：数据保存在 `~/Documents/lifeplanner_data.json`。

云端模式：数据存储在 Supabase PostgreSQL，重启不丢失。

## 后端部署（Render + Supabase）

### 1. 创建数据库

1. 注册 [Supabase](https://supabase.com)，新建项目
2. 进入项目首页，点击顶部 **Connect** 按钮，复制 URI 格式的连接字符串

### 2. 部署到 Render

1. 注册 [Render](https://render.com)，新建 **Web Service**，连接本仓库
2. 配置：
   - **Root Directory**：`backend`
   - **Build Command**：`pip install -r requirements.txt`
   - **Start Command**：`uvicorn main:app --host 0.0.0.0 --port $PORT`
3. 在 **Environment** 中添加环境变量：
   - `DATABASE_URL`：Supabase 连接字符串
   - `API_TOKEN`：自定义访问密钥（可选，默认 `lifeplanner_secret`）
4. 部署，首次启动自动建表

### 3. 连接桌面端

打开桌面应用 → 设置 → 填入 Render 服务地址和 API Token

## 2026.5.8新增功能

  ### 💭 胡思乱想
  点击工具栏「💭 胡思乱想」按钮，打开想法记录模块。
  支持按年计划 / 月计划 / 周计划分类记录，历史内容完整显示，双击可编辑。

  ### 📤 导出记录
  点击工具栏「📤 导出记录」，自动生成 PDF 文件保存至 `D:\lifeplanner\recording\`。
  内容按年份组织：年计划 → 年总结（含体重波动折线图）→ 各月 →各周，跳过空白章节，附页码。

  ### ☁️ 云端后端（跨设备同步）
  `backend/` 目录为 FastAPI 后端，可部署至 Render，数据存储在云端 PostgreSQL（Supabase）。
  桌面端通过 REST API 同步数据，本地缓存 30 秒以减少请求次数。

  ### 📱 手机 Web 端
  部署后端后，直接用手机浏览器打开后端地址即可使用。
  包含日程、倒数日、体重、胡思乱想四个模块，支持添加 / 编辑 / 删除。

  ### ⚙ 设置
  点击工具栏「⚙ 设置」配置后端地址和 Token。
  内置连接测试和旧数据迁移工具（将本地 JSON 数据一键导入云端）。
  首次启动若未配置后端，自动弹出设置窗口。
