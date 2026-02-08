# AI Excel 数据清洗助手 (AI Excel Cleaner)

这是一个基于 Streamlit 的智能 Excel 数据清洗工具，采用**纯本地模式**运行，无需 API Key。它结合了所见即所得的交互式操作和强大的清洗算法，帮助您快速处理复杂的 Excel 表格。

## 功能特点

- **纯本地运行**: 彻底移除外部 AI 依赖，数据安全可控，无需联网。
- **交互式结构定义**: 点击表格行即可轻松定义表头和数据开始行，所见即所得。
- **关键列智能填充**: 点击列标题即可标记“关键列”，系统自动执行**取消合并单元格**并**向下填充**，完美解决合并单元格导致的数据丢失问题。
- **多 Sheet 批量清洗**: 支持一次性选择并配置多个工作表，一键批量清洗并导出。
- **多格式支持**: 全面支持 `.xlsx` (现代 Excel), `.xls` (Legacy Excel), 和 `.csv` 文件。
- **语义合并**: 将复杂的层级表头合并为易于分析的单级字段（如 "Q1_营收"）。
- **Apple 风格 UI**: 
    - **透明毛玻璃 (Frosted Glass)**: 深度定制的透明磨砂背景，提供极佳的通透感。
    - **激光流动动画 (Laser Flow)**: 按钮和上传区域拥有科技感十足的动态边框流光效果。
    - **现代排版**: 优化了文字层级和字体，完全遵循 Apple Human Interface Guidelines。
- **多语言支持**: 支持简体中文和英文切换。

## 开发指南

详细的开发规范、Agent 角色定义及调用时机请参考 [PROJECT_SPEC.md](PROJECT_SPEC.md)。

## 安装与运行

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用:
   ```bash
   streamlit run app.py
   ```

## 注意事项

- 本项目不再需要 Google Gemini API Key。
- 推荐使用 Python 3.8+ 环境。

## 用户手册

详细的功能介绍和操作步骤，请阅读 [用户使用手册 (USER_GUIDE.md)](USER_GUIDE.md)。
