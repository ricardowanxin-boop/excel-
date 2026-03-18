# 📊 Excel 大模型无损翻译系统 (SaaS Edition)

## 简介
这是一个基于 **Streamlit** 和 **大语言模型（LLM）** 的商业级 Excel 翻译 SaaS 系统。它专为解决传统翻译工具无法保留复杂 Excel 格式（如文本框、形状、图表布局）的问题而设计。通过直接操作 Excel 底层 XML 结构（"Surgeon Mode" / 外科手术模式），实现了对 Excel 文件的**像素级无损翻译**。

## 🌟 核心功能

- **🛡️ 像素级无损翻译**：采用独创的 **XML 注入技术**，绕过传统库的重构过程，直接修改底层数据。完美保留 Excel 中的所有格式、样式、图片、图表、悬浮文本框、SmartArt 和复杂排版。
- **🧠 大模型驱动**：支持接入 OpenAI 格式的任意大模型（如 Qwen, GPT-4, DeepSeek 等），结合上下文理解进行精准翻译，拒绝机翻味。
- **🧩 复杂元素极致支持**：不仅支持普通单元格，还能深入提取并翻译 **Shape（形状）**、**TextBox（文本框）** 内的文字。支持**段落级(Paragraph-level)**智能拼接匹配，彻底解决长句被底层 XML 截断导致的漏翻问题。
- **💳 SaaS级卡密计费系统**：内置完善的卡密分发与额度扣除机制，支持多种卡密类型：
  - **按次卡 (Count Sheet)**：精确到单个 Sheet 的翻译计次。
  - **全文件卡 (Count File)**：一次性扫描并自动翻译整个 Excel 文件的所有 Sheet，一键搞定。
  - **时间卡 (Time)**：在有效期内无限次翻译（包含每日上限限制）。
- **👑 独立管理后台**：内置超级管理员面板，支持动态生成卡密、查看卡密使用状态、实时编辑或删除用户数据。
- **⚡️ 智能批处理与全局去重**：自动在整个工作簿级别提取并去重文本，批量并发请求大模型，显著提高翻译效率并大幅节省 Token 成本。
- **🛑 实时中断控制**：翻译过程中随时可以点击“取消翻译”，立即中断 API 调用且不扣除用户额度。
- **☁️ 云原生就绪**：完全兼容 Streamlit Community Cloud 部署，支持安全的 Secrets 动态注入，抛弃不安全的 `.env` 文件上传。

## 🛠️ 技术栈

- **Frontend**: Streamlit (全屏定制化 UI、动态路由)
- **Backend**: Python 3.11+
- **Core Processing**: 
  - `zipfile` & `xml.etree.ElementTree` (用于底层 XML 操作，实现无损读写)
  - `openpyxl` (用于辅助读取 Sheet 信息)
- **AI Integration**: OpenAI Python SDK + Tenacity (支持失败重试)
- **Database**: SQLite (支持高并发的本地关系型数据库)
- **Deployment**: Streamlit Cloud / Docker

## 🚀 部署与运行

### 1. 环境准备
推荐使用 Python 3.11。

```bash
# 克隆项目
git clone [repository-url]
cd excel-translator

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境变量配置 (本地开发)
在项目根目录创建 `.env` 文件（**注意：此文件已加入 .gitignore，切勿上传至公开仓库**）：

```ini
# .env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1
MODEL_NAME=Qwen/Qwen3-30B-A3B-Instruct-2507
```

*如果部署到 Streamlit Cloud，请在控制台的 **Settings -> Secrets** 中使用 TOML 格式配置上述变量。*

### 3. 运行服务

```bash
streamlit run app.py --server.port 8506
```
启动后访问浏览器：`http://localhost:8506`

## 📖 使用指南

### 🧑‍💻 用户端
1.  **独立登录页**：进入系统后，输入购买的卡密直接登录。
2.  **上传文件**：选择需要翻译的 `.xlsx` 文件。
3.  **配置翻译**：
    - 如果是【单次卡】，选择需要翻译的工作表 (Sheet)。
    - 如果是【全文件卡】，系统会自动隐藏选择框，默认全文件扫描。
    - 选择 **目标语言** 和 **应用场景**。
4.  **开始翻译**：点击 "🚀 开始解析与翻译"。过程中可随时点击 "❌ 取消翻译" 中断。
5.  **下载结果**：翻译完成后，可在线预览前 100 条结果，并下载无损翻译后的最终文件。

### 👑 管理端
1.  **管理员登录**：在登录页输入超级管理员密码（默认初始账号：`admin888`，密码：`admin888`）。
2.  **卡密管理**：
    - 在侧边栏生成新的卡密，可选择不同类型（按次、按文件、包月）和额度。
    - 在数据表格中实时查看所有卡密的使用状态（剩余额度、创建时间等）。
    - 支持直接在表格中点击编辑图标修改卡密类型，或点击删除图标作废卡密。

## 📂 核心架构说明

```text
excel-translator/
├── app.py                # 路由中心与 Streamlit 页面配置入口
├── .python-version       # 锁定云端部署 Python 版本 (3.11)
├── packages.txt          # 云端 Linux 系统依赖 (如 libjpeg-dev)
├── requirements.txt      # Python 依赖库
├── generate_keys.py      # (可选) CLI 批量生成卡密脚本
├── auth/                 
│   └── db.py             # SQLite 数据库引擎、Schema 结构、RBAC 权限校验
├── core/                 
│   ├── excel_parser.py   # 【核心】"Surgeon Mode" 引擎，XML 段落级拆解与回填
│   └── translator.py     # LLM 调度引擎，带指数退避重试机制
├── ui/                   
│   ├── login.py          # 独立的沉浸式登录 UI 
│   ├── admin_dashboard.py# 管理员 CRUD 数据面板
│   ├── main_content.py   # 核心翻译工作流 UI 与状态机
│   └── sidebar.py        # 动态侧边栏组件
└── data/                 
    └── users.db          # 运行时自动生成的 SQLite 数据库
```

## ⚠️ 常见问题 (FAQ)

**Q: 为什么翻译形状（文本框）里的文字时，长段落也能完美保留格式？**
A: 这是最新的段落级（Paragraph-level）解析引擎在起作用。系统会将 XML 中 `<a:p>` 标签下的所有文本碎片 `<a:t>` 拼接成完整句子发给大模型。回填时，将译文注入第一个节点并清空其余节点，既保证了长句不漏翻，又继承了原有的文本框样式。

**Q: 如何处理云端部署时的 401 报错？**
A: 请确保在 Streamlit Cloud 的 Secrets 中正确配置了 API Key，且格式为严格的 TOML 字符串（带双引号）。代码中已实现了动态读取 Secrets 的容错机制。

---
**License**: MIT
