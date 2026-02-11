"""
Excel Cleaner - Utility Functions
工具函数模块
"""

import pandas as pd
from typing import List, Union, Optional


def parse_row_input(input_str: str) -> List[int]:
    """
    解析用户输入的行号字符串
    
    支持格式：
    - "1,2,3" -> [0, 1, 2]  (转换为 0-based)
    - "1-3" -> [0, 1, 2]
    - "1,3-5" -> [0, 2, 3, 4]
    - "1" -> [0]
    
    Args:
        input_str: 用户输入的字符串（1-based）
        
    Returns:
        List[int]: 行索引列表（0-based）
    """
    if not input_str or input_str.strip() == '':
        return []
    
    rows = []
    parts = input_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # 处理范围，如 "1-3"
            try:
                start, end = part.split('-')
                start = int(start.strip()) - 1  # 转为 0-based
                end = int(end.strip()) - 1
                rows.extend(range(start, end + 1))
            except ValueError:
                continue
        else:
            # 处理单个数字
            try:
                rows.append(int(part) - 1)  # 转为 0-based
            except ValueError:
                continue
    
    return sorted(list(set(rows)))  # 去重并排序


def parse_column_input(input_str: str) -> List[int]:
    """
    解析用户输入的列号字符串
    
    支持格式：
    - "1,2,3" -> [0, 1, 2]
    - "1" -> [0]
    - "none" or "" -> []
    
    Args:
        input_str: 用户输入的字符串（1-based）
        
    Returns:
        List[int]: 列索引列表（0-based）
    """
    input_str = input_str.strip().lower()
    
    if not input_str or input_str in ['none', '无', 'null', '']:
        return []
    
    columns = []
    parts = input_str.split(',')
    
    for part in parts:
        part = part.strip()
        try:
            columns.append(int(part) - 1)  # 转为 0-based
        except ValueError:
            continue
    
    return sorted(list(set(columns)))


def format_preview(df: pd.DataFrame, max_rows: int = 10, max_cols: int = 8) -> str:
    """
    格式化 DataFrame 为字符串预览
    
    Args:
        df: 数据框
        max_rows: 最大显示行数
        max_cols: 最大显示列数
        
    Returns:
        str: 格式化的预览字符串
    """
    # 限制行列数
    preview_df = df.head(max_rows)
    
    if len(df.columns) > max_cols:
        preview_df = preview_df.iloc[:, :max_cols]
        col_truncated = True
    else:
        col_truncated = False
    
    # 转换为字符串
    lines = []
    
    # 表头
    header = ['    '] + [f'  {chr(65 + i)}  ' for i in range(len(preview_df.columns))]
    lines.append('│'.join(header))
    lines.append('─' * len('│'.join(header)))
    
    # 数据行
    for idx, row in preview_df.iterrows():
        # 行号（1-based）
        row_num = str(idx + 1).rjust(3)
        
        # 单元格值
        cells = [row_num]
        for val in row:
            val_str = str(val) if pd.notna(val) else ''
            val_str = val_str[:6].center(6)  # 截断并居中
            cells.append(val_str)
        
        lines.append('│'.join(cells))
    
    if len(df) > max_rows:
        lines.append(f'... ({len(df) - max_rows} more rows)')
    
    if col_truncated:
        lines.append(f'... ({len(df.columns) - max_cols} more columns)')
    
    return '\n'.join(lines)


def simple_preview(df: pd.DataFrame, max_rows: int = 10) -> str:
    """
    简单的表格预览（使用 pandas 默认格式）
    
    Args:
        df: 数据框
        max_rows: 最大显示行数
        
    Returns:
        str: 预览字符串
    """
    # 设置显示选项
    pd.set_option('display.max_rows', max_rows)
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 100)
    pd.set_option('display.max_colwidth', 20)
    
    preview = df.head(max_rows).to_string()
    
    if len(df) > max_rows:
        preview += f'\n... ({len(df) - max_rows} more rows)'
    
    return preview


def suggest_key_columns(df: pd.DataFrame, header_rows: List[int]) -> List[int]:
    """
    智能建议可能的关键列（有合并单元格的列）
    
    启发式规则：
    - 第一列通常是索引列
    - 包含大量重复值的列可能是关键列
    
    Args:
        df: 原始数据框
        header_rows: 表头行索引
        
    Returns:
        List[int]: 建议的关键列索引
    """
    suggestions = []
    
    # 数据起始行
    data_start = max(header_rows) + 1 if header_rows else 1
    
    if data_start >= len(df):
        return suggestions
    
    # 获取数据部分（前20行用于分析）
    data_df = df.iloc[data_start:data_start + 20]
    
    # 检查第一列
    if len(data_df.columns) > 0:
        first_col = data_df.iloc[:, 0]
        # 如果第一列有很多空值，可能是合并单元格
        empty_ratio = first_col.isna().sum() / len(first_col)
        if empty_ratio > 0.2:  # 超过20%空值
            suggestions.append(0)
    
    return suggestions


def validate_cleaning_params(header_rows: List[int], data_start_row: int, total_rows: int) -> tuple[bool, str]:
    """
    验证清洗参数是否合法
    
    Args:
        header_rows: 表头行索引
        data_start_row: 数据开始行索引
        total_rows: 总行数
        
    Returns:
        tuple: (是否合法, 错误信息)
    """
    if not header_rows:
        return False, "表头行不能为空"
    
    if data_start_row < 0:
        return False, "数据开始行不能为负数"
    
    if data_start_row >= total_rows:
        return False, f"数据开始行 ({data_start_row}) 超出总行数 ({total_rows})"
    
    if max(header_rows) >= data_start_row:
        return False, f"表头行 {max(header_rows)} 必须在数据开始行 {data_start_row} 之前"
    
    return True, ""


def get_file_info(file_path: str) -> dict:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 文件信息
    """
    import os
    
    info = {
        'path': file_path,
        'name': os.path.basename(file_path),
        'size': 0,
        'extension': '',
        'exists': False
    }
    
    if os.path.exists(file_path):
        info['exists'] = True
        info['size'] = os.path.getsize(file_path)
        _, ext = os.path.splitext(file_path)
        info['extension'] = ext.lower()
    
    return info


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        str: 格式化后的字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
