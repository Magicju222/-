# Excel Cleaner Skill

一个功能强大的 Excel 数据清洗工具，支持合并单元格处理、多级表头合并、关键列向下填充等功能。

## 功能特点

- ✅ **合并单元格处理**：自动解合并并填充值
- ✅ **多级表头合并**：将层级表头合并为单级字段
- ✅ **关键列向下填充**：解决垂直合并单元格数据丢失问题
- ✅ **多格式支持**：.xlsx, .xls, .csv
- ✅ **交互式配置**：通过问答完成所有参数设置
- ✅ **纯 Python**：不依赖 Streamlit、Gradio 等 UI 框架

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 方式一：交互式清洗（推荐）

```bash
cd skills/excel-cleaner
python interactive.py
```

然后按照提示操作：
1. 输入文件路径
2. 选择工作表
3. 指定表头行
4. 确认数据开始行
5. 选择关键列
6. 导出结果

### 方式二：编程式调用

```python
from excel_cleaner import ExcelCleaner

cleaner = ExcelCleaner()

# 清洗数据
result = cleaner.clean_data(
    file_content="data.xlsx",
    header_rows=[0, 1],      # 第1、2行是表头
    data_start_row=2,        # 第3行开始数据
    key_columns=[0],         # 第1列需要向下填充
    separator=" / "          # 多级表头分隔符
)

# 获取清洗后的数据
cleaned_df = result['cleaned_df']

# 导出
cleaned_df.to_excel('output.xlsx', index=False)
```

## API 文档

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

## 使用示例

### 示例 1：基础使用

```python
from excel_cleaner import ExcelCleaner

cleaner = ExcelCleaner()
result = cleaner.clean_data(
    file_content="sales.xlsx",
    header_rows=[0, 1],
    data_start_row=2,
    key_columns=[0],
    separator=" / "
)

print(result['cleaned_df'].head())
```

### 示例 2：批量处理

```python
import os
from excel_cleaner import ExcelCleaner

cleaner = ExcelCleaner()
files = ['data1.xlsx', 'data2.xlsx', 'data3.xlsx']

for file in files:
    result = cleaner.clean_data(
        file_content=file,
        header_rows=[0],
        data_start_row=1
    )
    output_name = f"cleaned_{file}"
    result['cleaned_df'].to_excel(output_name, index=False)
    print(f"已处理: {file} -> {output_name}")
```

### 示例 3：处理多个工作表

```python
from excel_cleaner import ExcelCleaner

cleaner = ExcelCleaner()
file_path = "multi_sheet.xlsx"

# 获取所有工作表名称
sheet_names = cleaner.get_sheet_names(file_path)

for sheet in sheet_names:
    result = cleaner.clean_data(
        file_content=file_path,
        header_rows=[0, 1],
        data_start_row=2,
        sheet_name=sheet
    )
    result['cleaned_df'].to_excel(f"cleaned_{sheet}.xlsx", index=False)
```

## 文件结构

```
excel-cleaner/
├── SKILL.md              # Skill 定义文档
├── excel_cleaner.py      # 核心清洗类
├── interactive.py        # 交互式脚本
├── utils.py              # 工具函数
├── requirements.txt      # 依赖
├── README.md             # 本文件
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

## 常见问题

### Q: 如何处理超大文件？

A: 目前会加载整个文件到内存。对于超大文件（>100MB），建议：
1. 先分割文件
2. 分批处理
3. 合并结果

### Q: 支持哪些文件格式？

A: 支持 .xlsx（推荐）、.xls（旧版 Excel）、.csv

### Q: 可以处理合并单元格吗？

A: 可以！这是本工具的核心功能之一。会自动解合并并填充值。

## 许可证

MIT License
