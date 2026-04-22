# 智教星瞳 · 后端服务

> **版本**：v0.2.0  
> **负责人**：成员 E  
> **最后更新**：2026-04-21

---

## 📖 项目简介

智教星瞳后端服务是为“智教星瞳”AI 自适应教学系统提供数据存储、业务逻辑处理及 AI 智能体调用的中间层。服务基于 **FastAPI** 构建，通过 **vivo 九问平台 API** 调用蓝心大模型能力，目前已实现以下核心功能：

- 学生档案管理
- **智能诊断题库**：优先本地题库缓存，不足时自动调用大模型生成并入库
- 个性化教案生成与版本管理
- 教学资源（PPT/板书/视频）自动生成
- **课堂实时数据记录**：专注度事件、随堂答题记录存储
- **实时教学调整决策**：根据课堂状态动态调整教学策略

当前版本支持 **Mock 模式**（返回模拟数据）与 **真实 AI 调用模式** 灵活切换，便于开发与调试。

---

## 🛠 技术栈

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI 0.104+ |
| 异步服务器 | Uvicorn |
| ORM | SQLAlchemy 2.0+ |
| 数据库 | SQLite（开发）/ PostgreSQL（生产可切换） |
| 数据校验 | Pydantic v2 |
| HTTP 客户端 | httpx（异步） |
| AI 平台 | vivo 九问（蓝心大模型） |

---

## 📁 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理（环境变量）
│   ├── database.py             # 数据库连接与 Session
│   ├── models.py               # SQLAlchemy ORM 模型
│   ├── schemas.py              # Pydantic 请求/响应模型
│   ├── routers/                # 路由模块
│   │   ├── __init__.py
│   │   ├── students.py         # 学生管理
│   │   ├── diagnosis.py        # 诊断测试与报告
│   │   ├── lesson_plans.py     # 教案管理与资源填充
│   │   └── reports.py          # 学习报告、课堂记录、实时调整
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── mock_service.py     # Mock 数据生成
│   │   ├── ai_client.py        # 九问 API 客户端
│   │   └── question_bank_service.py  # 本地题库服务（缓存与智能生成）
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── json_utils.py       # JSON 解析工具
├── scripts/
│   └── mock_data_generator.py  # 独立 Mock 数据生成脚本
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量示例
└── README.md                   # 本文件
```

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.9 或更高版本（推荐 3.10+）
- pip
- 访问 Rust 官网：https://rustup.rs/
下载 rustup-init.exe（Windows 版本）



### 2. 安装依赖

```bash
python -m venv venv
source venv/bin/activate    # Linux/MacOS  
venv\Scripts\activate       # Windows
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要修改配置：

```ini
DEBUG=True
DATABASE_URL=sqlite:///./zhijiao.db
USE_MOCK_DATA=True

# 若需真实调用九问 API，请填写以下配置
JIUWEN_API_BASE_URL=http://jiuwen-api.vmic.xyz/v1
JIUWEN_API_KEY=your_api_key_here
AI_REQUEST_TIMEOUT=60
```

### 4. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动成功后访问：
- **API 文档（Swagger UI）**：http://localhost:8000/docs
- **根路径**：http://localhost:8000/

---

## 🔧 Mock 模式与真实模式

- **Mock 模式**（`USE_MOCK_DATA=True`）：所有 AI 相关接口返回本地预制的模拟数据，无需网络请求，适合前端独立开发。
- **真实模式**（`USE_MOCK_DATA=False`）：通过九问 API 调用蓝心大模型，需提前在九问平台创建并发布 Bot，获取 API 密钥填入 `.env`。

---

## 📡 核心 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/students/` | 创建学生档案 |
| GET | `/api/students/{id}` | 获取学生信息 |
| GET | `/api/diagnosis/questions` | 获取诊断测试题（支持本地题库缓存 + AI 生成） |
| POST | `/api/diagnosis/submit` | 提交答案，生成报告与教案 |
| GET | `/api/lesson_plans/latest/{student_id}` | 获取最新教案 |
| POST | `/api/lesson_plans/{plan_id}/enrich` | 为教案生成教学资源（异步） |
| GET | `/api/lesson_plans/{plan_id}/status` | 查询资源生成状态 |
| GET | `/api/reports/{student_id}/latest` | 获取最新学习报告 |
| POST | `/api/reports/class_records` | 上报课堂记录（专注度事件 + 答题记录） |
| POST | `/api/reports/real_time_adjustment` | 获取实时教学调整决策 |

详细请求/响应格式请访问 `/docs` 查看交互式文档。

---

## 🧪 使用 Postman 测试

1. 导入项目根目录下的 `postman_collection.json` 到 Postman。
2. 创建环境变量 `base_url` = `http://localhost:8000`。
3. 按顺序调用：创建学生 → 获取题目 → 提交答案 → 获取教案 → 触发资源生成 → 查询状态 → 获取报告。

---

## 🗄 数据库说明

开发阶段使用 SQLite，数据库文件为 `zhijiao.db`。可使用 [DB Browser for SQLite](https://sqlitebrowser.org/) 直接查看表数据。

主要数据表：
- `student`：学生基本信息
- `diagnosis_result`：诊断结果
- `lesson_plan`：教案（支持多版本）
- `class_record`：课堂过程记录（专注度事件、答题记录）
- `learning_report`：学习报告
- `question_bank`：本地题库缓存（新增）

---

## 🔗 与蓝心大模型通信机制

本服务通过 **vivo 九问平台 API** 调用蓝心大模型，具体通信细节请参阅相关文档。核心流程：

1. 构造 `query`（自然语言指令）和 `inputs`（变量）。
2. 携带 `Authorization: Bearer <API_KEY>` 请求 `/chat-messages`。
3. 从响应 `answer` 字段中提取 JSON 数据。
4. 转换为内部标准格式返回前端。

新增的 **本地题库缓存机制** 会在请求题目时优先查询本地数据库，不足时才调用大模型生成并自动入库，有效降低调用成本并提升响应速度。

---

## 🐛 常见问题

### 服务启动失败，提示端口占用
```bash
uvicorn app.main:app --reload --port 8001   # 更换端口
```

### 数据库表未自动创建
删除 `zhijiao.db` 文件，重启服务即可自动重新建表。

### Mock 数据与预期不符
检查 `.env` 中 `USE_MOCK_DATA` 是否为 `True`，并确认 `app/services/mock_service.py` 中的数据结构。

### 真实调用九问 API 无响应
- 确认 `JIUWEN_API_KEY` 是否正确。
- 检查网络是否能访问 `http://jiuwen-api.vmic.xyz`（办公网/IDC 环境）。
- 查看后端日志，排查超时或 4xx 错误。

---

## 📌 后续计划

- [ ] 学习报告生成接口（汇总课堂数据与诊断结果）
- [ ] 习题课内容生成与判题接口
- [ ] 请求重试与熔断机制
- [ ] 支持 PostgreSQL 生产环境切换
- [ ] 集成日志系统与监控

---

## 👥 团队成员

- **成员 A**：项目经理 & AI 智能体总架构师
- **成员 B**：Android 客户端负责人
- **成员 C**：端侧 AI 工程师
- **成员 D**：多媒体与教学资源工程师
- **成员 E**：后端服务与数据工程师

---

## 📄 许可证

本项目为智教星瞳参赛作品，仅供内部开发与比赛使用。