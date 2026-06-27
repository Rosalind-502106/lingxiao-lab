# 🔬 凌逍科学社团 · 资产管理系统 v3.0

多设备云端同步的社团物资管理系统。

## ✨ 功能特性

- **📦 物资管理** — 添加、编辑、删除物资，支持分类筛选
- **📋 借出记录** — 记录物资借出/归还，跟踪库存变化
- **📝 操作日志** — 自动记录所有操作，方便审计追溯
- **🔑 管理员模式** — 密码保护的管理员权限，防止误操作
- **🔄 多设备同步** — 基于云端的数据同步，多台设备实时共享
- **🔍 实时搜索** — 快速搜索物资名称
- **📤 数据导出** — 一键导出 JSON 格式数据
- **📱 响应式设计** — 完美适配手机/平板/电脑
- **🔄 自动备份** — 服务端每 5 分钟自动备份

## 🚀 快速部署 (Render)

### 1. Fork 或 Push 到 GitHub

```bash
cd lingxiao-lab
git init
git add .
git commit -m "init: 凌逍资产管理系统 v3.0"
# 创建 GitHub 仓库后推送
git remote add origin https://github.com/你的用户名/lingxiao-lab.git
git push -u origin main
```

### 2. 在 Render 部署

1. 登录 [Render](https://dashboard.render.com)
2. 点击 **New +** → **Web Service**
3. 选择你的 GitHub 仓库
4. 配置参数：
   - **Name**: `lingxiao-lab`（或自定义）
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: **Free**（已足够使用）
5. 设置环境变量（**Environment Variables**）：
   - `ADMIN_PASSWORD` = `你的管理员密码`（**务必修改！**）
   - `FLASK_DEBUG` = `0`
6. 点击 **Deploy Web Service**
7. 等待部署完成（约 2-3 分钟）

### 3. 访问使用

部署完成后，访问 `https://your-app.onrender.com` 即可使用。

## 💻 本地开发

### 前置条件

- Python 3.9+
- Git（可选）

### 安装

```bash
cd lingxiao-lab
pip install -r requirements.txt
```

### 运行

```bash
python app.py
```

访问 http://localhost:8080

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ADMIN_PASSWORD` | 管理员密码 | `lingxiao2025` |
| `FLASK_DEBUG` | 调试模式 | `0` |
| `PORT` | 服务端口 | `8080` |

## 📁 项目结构

```
lingxiao-lab/
├── app.py                  # Flask 后端服务器
├── lingxiao-lab-manager.html  # 前端页面（单页应用）
├── requirements.txt        # Python 依赖
├── .env.example            # 环境变量模板
├── data/                   # 数据目录（自动创建）
│   ├── lab_data.json       # 主数据文件
│   ├── backups/            # 自动备份目录
│   └── operation_log.json  # 操作日志
└── README.md               # 本文件
```

## 🔒 安全提示

1. **部署前务必修改管理员密码！** 在 Render 的环境变量中设置 `ADMIN_PASSWORD`
2. 建议定期导出数据备份
3. 服务端自动保留最近 50 个备份

## 📄 License

MIT