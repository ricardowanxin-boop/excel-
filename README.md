# 📊 Excel 大模型无损翻译器 (Excel LLM Translator)

## 简介
这是一个基于 **Streamlit** 和 **大语言模型（LLM）** 的智能 Excel 翻译工具。它专为解决传统翻译工具无法保留复杂 Excel 格式（如文本框、形状、图表布局）的问题而设计。通过直接操作 Excel 底层 XML 结构（"Surgeon Mode" / 外科手术模式），实现了对 Excel 文件的**像素级无损翻译**。

![App Screenshot](https://via.placeholder.com/800x400?text=Excel+LLM+Translator+Screenshot)

## 🌟 核心功能

- **🛡️ 像素级无损翻译**：采用独创的 **XML 注入技术**，绕过传统库的重构过程，直接修改底层数据。完美保留 Excel 中的所有格式、样式、图片、图表、悬浮文本框、SmartArt 和复杂排版。
- **🧠 大模型驱动**：支持接入 OpenAI 格式的任意大模型（如 Qwen, GPT-4, DeepSeek 等），结合上下文理解进行精准翻译，拒绝机翻味。
- **🧩 复杂元素支持**：不仅支持普通单元格，还能深入提取并翻译 **Shape（形状）**、**TextBox（文本框）** 内的文字，智能处理段落拼接，解决传统库（如 openpyxl）读取丢失或无法修改的问题。
- **💳 额度管理系统**：内置轻量级的用户鉴权、注册、登录及卡密充值系统，开箱即用，适合作为 SaaS 服务或内部工具部署。
- **⚡️ 智能批处理**：自动提取去重、批量并发请求大模型，显著提高翻译效率并节省 Token 成本。

## 🛠️ 技术栈

- **Frontend**: Streamlit
- **Backend**: Python 3.11+
- **Core Processing**: 
  - `zipfile` & `xml.etree.ElementTree` (用于底层 XML 操作，实现无损读写)
  - `openpyxl` (用于辅助读取 Sheet 信息)
- **AI Integration**: OpenAI Python SDK (兼容所有类 OpenAI 接口)
- **Database**: SQLite (轻量级用户与额度管理)

## 🚀 快速开始

### 1. 环境准备
确保已安装 Python 3.8 或以上版本。

```bash
# 克隆项目
git clone [repository-url]
cd excel-translator

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量
在项目根目录创建 `.env` 文件，配置大模型 API 信息：

```ini
# .env
# LLM API 配置 (以阿里云百炼 Qwen 为例，也支持 OpenAI/DeepSeek 等)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL_NAME=Qwen/Qwen3-30B-A3B-Instruct-2507

# 可选：配置 Streamlit 页面信息
ST_PAGE_TITLE="Excel 大模型无损翻译器"
```

### 3. 运行服务
首次运行会自动在 `data/users.db` 初始化数据库结构。

```bash
streamlit run app.py --server.port 8506
```

启动后访问浏览器：`http://localhost:8506`

## 📖 使用指南

1.  **登录/注册**：
    - 在左侧边栏输入用户名和密码进行注册或登录。
2.  **充值激活**：
    - 新用户可能需要充值额度。
    - **测试卡密**：`TEST-COUNT-100` (可在 `requirements.txt` 或数据库初始化逻辑中查看)。
3.  **上传文件**：
    - 点击主界面的上传区域，选择 `.xlsx` 文件。
4.  **配置翻译**：
    - 选择需要翻译的 **工作表 (Sheet)**。
    - 选择 **目标语言** (如：中文、English、日本語)。
    - 选择 **应用场景** (通用办公 / 商务贸易 / IT互联网) 以调整提示词风格。
5.  **开始翻译**：
    - 点击 "🚀 开始解析与翻译"。
    - 系统将自动提取文本 -> 调用 LLM 翻译 -> 无损注入回 Excel。
6.  **下载结果**：
    - 翻译完成后，预览表格会显示部分结果。
    - 点击 "📥 下载翻译后的 Excel 文件" 获取最终文件。

## 📂 项目结构

```
excel-translator/
├── app.py                # Streamlit 应用入口
├── .env                  # 环境变量配置文件
├── requirements.txt      # Python 依赖库
├── auth/                 # 认证模块
│   ├── __init__.py
│   └── db.py             # SQLite 数据库操作、用户管理、卡密管理
├── core/                 # 核心逻辑模块
│   ├── __init__.py
│   ├── excel_parser.py   # 【核心】Excel 解析、XML 提取与注入算法
│   └── translator.py     # LLM API 调用封装与重试机制
├── ui/                   # 界面模块
│   ├── __init__.py
│   ├── main_content.py   # 主内容区渲染逻辑
│   └── sidebar.py        # 侧边栏渲染逻辑
└── data/                 # 数据存储目录
    └── users.db          # SQLite 数据库文件 (自动生成)
```

## ⚠️ 常见问题 (FAQ)

**Q: 为什么下载的文件打开后，某些复杂的图表还在，文字却变了？**
A: 这正是本项目的 "Surgeon Mode" 在工作。我们只修改了 Excel 压缩包内的 `sharedStrings.xml` (单元格文字) 和 `drawing.xml` (形状文字)，完全没有触碰文件的其他结构数据，因此做到了极致的格式保留。

**Q: 翻译形状（文本框）里的文字时，格式会乱吗？**
A: 我们尽最大努力保留了 XML 标签结构。对于被 Excel 拆分成多个片段的句子，程序实现了智能拼接和替换算法，通常能保持原有的换行和位置。但如果译文长度与原文差异过大，Excel 可能会自动调整文本框内的排版。

**Q: 支持多 Sheet 批量翻译吗？**
A: 目前版本一次仅支持选择一个 Sheet 进行翻译，以确保稳定性和 Token 消耗的可控性。

---
**License**: MIT
