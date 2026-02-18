# AI Excel 数据清洗与分析助手 (AI Excel Cleaner & Analyzer)

一个基于 Streamlit 的智能 Excel 数据处理平台，集成了企业级用户认证系统、AI 驱动的数据分析和后台管理面板。结合所见即所得的交互式操作、强大的清洗算法和智能分析能力，帮助您快速处理和分析复杂的 Excel 表格数据。

## ✨ 功能特点

### 核心功能
- **企业级身份验证**: 集成 Supabase Auth，支持安全的用户注册与登录管理
- **后台管理面板**: 完整的管理员界面，支持用户管理、日志查看、系统配置
- **实时配置同步**: 系统配置修改后前端自动同步，无需刷新页面
- **交互式结构定义**: 点击表格行即可轻松定义表头和数据开始行，所见即所得
- **关键列智能填充**: 点击列标题标记"关键列"，自动取消合并单元格并向下填充
- **多 Sheet 批量清洗**: 支持一次性选择并配置多个工作表，一键批量清洗并导出
- **多格式支持**: 全面支持 `.xlsx`, `.xls`, `.csv` 文件
- **语义合并**: 将复杂的层级表头合并为易于分析的单级字段（如 "Q1_营收"）

### 🤖 AI 数据分析功能 (NEW!)
- **Agent 智能分析**: 基于 Kimi K2.5 大模型的自主数据分析能力
- **实时分析过程**: 可视化展示 AI 的每一步分析思路和工具调用
- **自动代码生成**: AI 自动生成 Python 代码执行复杂数据分析
- **智能可视化**: 自动识别数据特征并生成合适的图表
- **完整分析报告**: 自动生成包含洞察、建议和可视化的专业报告
- **报告导出**: 支持导出 Markdown 和 Word 格式的完整分析报告
- **业务导向分析**: 聚焦业务洞察而非技术细节，提供 actionable insights

### 分析模式
1. **传统分析模式**: 按固定步骤执行数据理解、探索性分析、深度洞察
2. **Agent 智能分析模式**: AI 自主决定分析步骤，实时调用工具完成分析

### UI 设计
- **Apple 风格界面**: 透明毛玻璃效果、激光流动动画、现代排版
- **多语言支持**: 支持简体中文和英文切换
- **响应式布局**: 适配不同屏幕尺寸

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
创建 `.env` 文件或在系统环境变量中配置：
```env
# Supabase 配置
SUPABASE_URL="your-project-url"
SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_KEY="your-service-key"  # 用于后端 API

# 后端 API 地址
API_BASE_URL="http://localhost:8000"

# LLM 配置 (用于 AI 数据分析)
LLM_PROVIDER="moonshot"
LLM_API_KEY="your-moonshot-api-key"
LLM_BASE_URL="https://api.moonshot.cn/v1"
LLM_MODEL="kimi-k2.5"
```

### 数据库初始化
1. 在 Supabase 控制台执行 `migrations/01_initial_schema.sql`
2. 运行配置初始化脚本：
   ```bash
   python init_system_config.py
   ```

### 启动服务

**前端 (Streamlit)**:
```bash
streamlit run app.py
```
访问: http://localhost:8501

**后端 (FastAPI)**:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
访问: http://localhost:8000/docs (API 文档)

## 🤖 AI 数据分析使用指南

### 1. 上传数据
- 支持 Excel (.xlsx, .xls) 和 CSV 格式
- 自动识别多个工作表

### 2. 数据清洗
- 定义表头和数据起始行
- 标记关键列进行智能填充
- 一键批量清洗多个 Sheet

### 3. AI 分析
- 选择分析模式：
  - **传统分析**: 固定流程的数据分析
  - **Agent 智能分析**: AI 自主决策的分析流程
- 输入业务背景（可选）
- 点击"开始AI分析"

### 4. 查看结果
- **实时过程**: 观察 AI 的每一步分析思路
- **可视化图表**: 自动生成的数据图表
- **分析报告**: 包含洞察和建议的完整报告
- **导出报告**: 下载 Markdown 或 Word 格式的报告文档

## 📚 文档

- [用户使用手册](USER_GUIDE.md) - 详细的功能介绍和操作步骤
- [开发规范](PROJECT_SPEC.md) - 开发规范、Agent 角色定义
- [部署指南](DEPLOY.md) - 部署详情
- [开发备注](DEV_NOTES.md) - 开发过程中的注意事项

## 🏗️ 项目架构

```
AI Excel Cleaner/
├── app.py                    # Streamlit 主应用
├── auth.py                   # 用户认证模块
├── services.py               # 业务服务层
├── cleaner.py                # Excel 清洗核心
├── analyzer.py               # AI 数据分析核心
├── agent_analyzer.py         # Agent 智能分析模块 (NEW!)
├── ui.py                     # UI 组件
├── i18n.py                   # 国际化
├── llm_client.py             # LLM 客户端
├── ai_visualizer/            # AI 可视化模块
│   ├── chart_generator.py    # 图表生成器
│   └── prompts/              # AI 提示词模板
├── report_generator.py       # 报告生成器 (Markdown/Word)
├── admin/                    # 后台管理模块
│   ├── admin.py              # 管理面板主入口
│   ├── system_config.py      # 系统配置管理
│   ├── user_management.py    # 用户管理
│   ├── log_viewer.py         # 日志查看
│   ├── analytics.py          # 数据分析
│   └── admin_api.py          # 管理 API 客户端
├── backend/                  # FastAPI 后端
│   └── app/
│       ├── api/              # API 路由
│       ├── core/             # 核心配置
│       └── services/         # 服务层
├── migrations/               # 数据库迁移
└── docs/                     # 文档
```

## 🔧 系统配置

管理员可在后台管理面板配置以下系统参数：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| MAINTENANCE_MODE | 维护模式 | false |
| MAX_FILE_SIZE_MB | 最大文件大小(MB) | 50 |
| ALLOWED_EXTENSIONS | 允许的文件类型 | ["xlsx", "xls", "csv"] |
| MAX_ROWS_PER_FILE | 最大行数限制 | 100000 |
| ENABLE_USER_REGISTRATION | 允许用户注册 | true |
| SYSTEM_NOTICE | 系统公告 | "" |

## 🤖 AI 配置

### 支持的 LLM 提供商
- **Moonshot (Kimi)**: 推荐使用 kimi-k2.5 模型
- **OpenAI**: GPT-4, GPT-3.5-turbo 等
- **Gemini**: Google Gemini 系列模型

### 配置示例
```env
# Moonshot (Kimi) - 推荐
LLM_PROVIDER="moonshot"
LLM_API_KEY="sk-xxxxxxxx"
LLM_BASE_URL="https://api.moonshot.cn/v1"
LLM_MODEL="kimi-k2.5"

# OpenAI
LLM_PROVIDER="openai"
LLM_API_KEY="sk-xxxxxxxx"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"
```

## 🛡️ 权限管理

系统支持三种用户角色：
- **user**: 普通用户，可使用清洗和分析功能
- **admin**: 管理员，可访问管理面板
- **super_admin**: 超级管理员，拥有所有权限

## 📝 注意事项

- 需要配置 Supabase 项目并执行数据库迁移
- 管理员需要在 `user_profiles` 表中设置 `role` 字段
- 后端 API 需要 `SUPABASE_SERVICE_KEY` 进行管理员操作
- AI 数据分析功能需要配置 LLM API Key
- 推荐使用 Python 3.8+ 环境

### RLS 策略配置

如果前端无法读取 `user_profiles` 表，请在 Supabase SQL Editor 执行：

```sql
-- 删除可能导致递归的策略
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.user_profiles;

-- 确保有以下策略
CREATE POLICY "user_profiles_select_policy" 
    ON public.user_profiles
    FOR SELECT 
    USING (id = auth.uid());

CREATE POLICY "user_profiles_insert_policy" 
    ON public.user_profiles
    FOR INSERT
    WITH CHECK (id = auth.uid());

CREATE POLICY "user_profiles_update_policy" 
    ON public.user_profiles
    FOR UPDATE
    USING (id = auth.uid());
```

**注意**: 避免使用嵌套查询 user_profiles 的策略，会导致无限递归错误。

## 🔗 相关链接

- [Moonshot AI 平台](https://platform.moonshot.cn/) - Kimi 大模型 API
- [Supabase 文档](https://supabase.com/docs) - 后端服务
- [Streamlit 文档](https://docs.streamlit.io/) - 前端框架

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
