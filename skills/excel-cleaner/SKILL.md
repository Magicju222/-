---
name: "excel-cleaner"
description: "Cleans Excel/CSV files through interactive Q&A. Handles merged cells, multi-level headers, and key column fill-down. Invoke when user needs to process Excel files with complex structures."
---

# Excel Cleaner Skill

一个通过**问答式交互**完成 Excel 数据清洗的 Skill，无需任何 UI 框架。

## 功能特点

- ✅ **合并单元格处理**：自动解合并并填充值
- ✅ **多级表头合并**：将层级表头合并为单级字段
- ✅ **关键列向下填充**：解决垂直合并单元格数据丢失问题
- ✅ **多格式支持**：.xlsx, .xls, .csv
- ✅ **交互式配置**：通过问答完成所有参数设置
- ✅ **纯 Python**：不依赖 Streamlit、Gradio 等 UI 框架

## 快速开始

### 方式一：交互式清洗（推荐）

```python
from interactive import interactive_clean

# 启动交互式清洗流程
interactive_clean()
```

交互流程：
1. 上传文件
2. 预览表格
3. 回答：哪些行是表头？
4. 回答：数据从第几行开始？
5. 回答：哪些列需要向下填充？
6. 查看结果并导出

### 方式二：编程式调用

```python
from excel_cleaner import ExcelCleaner

cleaner = ExcelCleaner()
result = cleaner.clean_data(
    file_content="data.xlsx",
    header_rows=[0, 1],      # 第1、2行是表头
    data_start_row=2,        # 第3行开始数据
    key_columns=[0],         # 第1列需要向下填充
    separator=" / "          # 多级表头分隔符
)

cleaned_df = result['cleaned_df']
cleaned_df.to_excel('output.xlsx', index=False)
```

## 核心 API

### ExcelCleaner 类

#### `clean_data(file_content, header_rows, data_start_row, key_columns=None, separator="_", sheet_name=None)`

主清洗方法。

**参数：**
- `file_content`: 文件路径或文件对象
- `header_rows`: 表头行索引列表（0-based），如 `[0, 1]`
- `data_start_row`: 数据开始行索引（0-based）
- `key_columns`: 关键列索引列表（0-based），可选
- `separator`: 多级表头分隔符，默认 `"_"`
- `sheet_name`: 工作表名称，默认第一个表

**返回：**
```python
{
    "raw_df": DataFrame,           # 原始数据预览（前20行）
    "cleaned_df": DataFrame,       # 清洗后的完整数据
    "structure_info": {            # 结构信息
        "header_rows": [...],
        "data_start_row": int
    }
}
```

#### `process_headers(df, header_rows, separator="_", max_length=100, keep_case=True)`

处理多级表头，合并为单级字段。

**示例：**
```python
# 输入表头：
# Row 1: Region |  Q1   |       |
# Row 2:        | Sales | Profit|
# 输出列名：['Region', 'Q1_Sales', 'Q1_Profit']
```

#### `process_key_columns(df, key_columns)`

对关键列执行向下填充（forward fill）。

**适用场景：**
- 第一列是"地区"，合并单元格跨多行
- 需要让每个数据行都知道所属地区

#### `load_and_fill_merged_cells(file_content, sheet_name=None)`

加载文件并处理合并单元格。

## 交互式使用示例

```
👤 用户: 帮我清洗这个表格

🤖 Skill: 请上传需要清洗的 Excel 文件（支持 .xlsx, .xls, .csv）

👤 用户: [上传 sales_report.xlsx]

🤖 Skill: 
📊 文件已加载，共 3 个工作表：Sheet1, Sheet2, Sheet3
请选择要清洗的工作表（输入名称，默认 Sheet1）：
Sheet1

🤖 Skill:
预览前 10 行：
┌────┬─────────┬─────────┬─────────┐
│    │    A    │    B    │    C    │
├────┼─────────┼─────────┼─────────┤
│  1 │  Region │  Q1     │         │
│  2 │         │  Sales  │  Profit │
│  3 │  North  │  1000   │  200    │
│  4 │         │  1200   │  250    │
└────┴─────────┴─────────┴─────────┘

哪些行是表头？（输入行号，如 1,2 或 1-3）
1,2

🤖 Skill: 
✓ 表头行：1, 2
数据从第几行开始？（默认: 3）
[用户直接回车]

🤖 Skill:
哪些列需要向下填充？（输入列号，如 1 或 1,3，或输入 "none"）
提示：第1列"Region"有合并单元格
1

🤖 Skill:
✅ 清洗完成！
结果预览（前5行）：
┌─────────────┬──────────┬─────────┐
│ Region_Q1   │ Sales    │ Profit  │
├─────────────┼──────────┼─────────┤
│ North       │ 1000     │ 200     │
│ North       │ 1200     │ 250     │
└─────────────┴──────────┴─────────┘

是否需要导出为 Excel 文件？（yes/no）
yes

🤖 Skill: 
📥 已生成 cleaned_sales_report.xlsx
```

## 依赖安装

```bash
pip install pandas openpyxl xlsxwriter xlrd
```

## 文件结构

```
excel-cleaner/
├── SKILL.md              # 本文件
├── excel_cleaner.py      # 核心清洗类
├── interactive.py        # 交互式脚本
├── utils.py              # 工具函数
├── requirements.txt      # 依赖
├── README.md             # 详细文档
└── examples/
    ├── basic_usage.py    # 基础使用示例
    ├── interactive_cli.py # 交互式 CLI
    └── batch_process.py  # 批量处理
```

## 注意事项

1. **索引从 0 开始**：所有行号、列号都是 0-based
2. **显示从 1 开始**：交互时显示给用户的是 1-based（更符合直觉）
3. **内存优化**：大文件会自动触发垃圾回收
4. **预览限制**：交互预览只显示前 50 行，避免卡顿

## 许可证

MIT License
