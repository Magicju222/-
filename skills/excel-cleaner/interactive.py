"""
Excel Cleaner - Interactive Mode
交互式清洗模块
"""

import pandas as pd
from typing import Optional
from excel_cleaner import ExcelCleaner
from utils import (
    parse_row_input, 
    parse_column_input, 
    simple_preview,
    suggest_key_columns,
    validate_cleaning_params,
    get_file_info,
    format_file_size
)


def ask_user(prompt: str, default: Optional[str] = None) -> str:
    """
    向用户提问
    
    Args:
        prompt: 提示文本
        default: 默认值
        
    Returns:
        str: 用户输入
    """
    if default:
        full_prompt = f"{prompt} (默认: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    answer = input(full_prompt).strip()
    
    if not answer and default:
        return default
    
    return answer


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    """
    询问是/否问题
    
    Args:
        prompt: 提示文本
        default: 默认值
        
    Returns:
        bool: 用户回答
    """
    default_str = "Y/n" if default else "y/N"
    answer = ask_user(prompt, default_str).lower()
    
    if answer in ['y', 'yes', '是']:
        return True
    elif answer in ['n', 'no', '否']:
        return False
    else:
        return default


def interactive_clean():
    """
    交互式清洗流程
    
    完整的 7 步交互流程：
    1. 获取文件
    2. 选择工作表
    3. 预览并选择表头行
    4. 确认数据开始行
    5. 选择关键列
    6. 执行清洗
    7. 导出结果
    """
    print("\n" + "="*60)
    print("📊 Excel 数据清洗助手")
    print("="*60 + "\n")
    
    cleaner = ExcelCleaner()
    
    # Step 1: 获取文件
    print("Step 1/7: 选择文件")
    print("-" * 40)
    
    while True:
        file_path = ask_user("请输入 Excel/CSV 文件路径")
        
        if not file_path:
            print("❌ 文件路径不能为空")
            continue
        
        file_info = get_file_info(file_path)
        
        if not file_info['exists']:
            print(f"❌ 文件不存在: {file_path}")
            continue
        
        print(f"✓ 文件已加载: {file_info['name']}")
        print(f"  大小: {format_file_size(file_info['size'])}")
        break
    
    # Step 2: 选择工作表
    print("\nStep 2/7: 选择工作表")
    print("-" * 40)
    
    try:
        sheet_names = cleaner.get_sheet_names(file_path)
        
        if len(sheet_names) > 1:
            print(f"发现 {len(sheet_names)} 个工作表:")
            for i, name in enumerate(sheet_names, 1):
                print(f"  {i}. {name}")
            
            sheet_choice = ask_user("请选择工作表编号", "1")
            try:
                sheet_idx = int(sheet_choice) - 1
                sheet_name = sheet_names[sheet_idx]
            except (ValueError, IndexError):
                sheet_name = sheet_names[0]
        else:
            sheet_name = sheet_names[0]
        
        print(f"✓ 已选择工作表: {sheet_name}")
    except Exception as e:
        print(f"⚠️ 获取工作表失败，使用默认: {e}")
        sheet_name = None
    
    # Step 3: 加载预览并选择表头
    print("\nStep 3/7: 预览并选择表头行")
    print("-" * 40)
    
    try:
        raw_df = cleaner.load_and_fill_merged_cells(file_path, sheet_name)
        print(f"✓ 文件加载成功，共 {len(raw_df)} 行 x {len(raw_df.columns)} 列")
        
        # 显示预览
        print("\n预览前 10 行:")
        print(simple_preview(raw_df, max_rows=10))
        
    except Exception as e:
        print(f"❌ 加载文件失败: {e}")
        return
    
    # 询问表头行
    while True:
        header_input = ask_user("\n哪些行是表头？（输入行号，如 1,2 或 1-3）", "1")
        header_rows = parse_row_input(header_input)
        
        if not header_rows:
            print("❌ 请至少指定一行作为表头")
            continue
        
        # 验证行号范围
        if max(header_rows) >= len(raw_df):
            print(f"❌ 行号超出范围，文件只有 {len(raw_df)} 行")
            continue
        
        # 显示选择的表头
        print(f"\n✓ 已选择表头行: {[r + 1 for r in header_rows]}")
        print("表头内容:")
        for row_idx in header_rows:
            row_data = raw_df.iloc[row_idx].tolist()
            print(f"  行 {row_idx + 1}: {row_data[:5]}{'...' if len(row_data) > 5 else ''}")
        
        break
    
    # Step 4: 确认数据开始行
    print("\nStep 4/7: 确认数据开始行")
    print("-" * 40)
    
    suggested_data_row = max(header_rows) + 1
    
    while True:
        data_row_input = ask_user(f"数据从第几行开始？", str(suggested_data_row + 1))
        
        try:
            data_start_row = int(data_row_input) - 1  # 转为 0-based
            
            if data_start_row < 0:
                print("❌ 行号不能为负数")
                continue
            
            if data_start_row <= max(header_rows):
                print(f"❌ 数据开始行必须在表头行 {max(header_rows) + 1} 之后")
                continue
            
            if data_start_row >= len(raw_df):
                print(f"❌ 行号超出范围")
                continue
            
            break
        except ValueError:
            print("❌ 请输入有效的数字")
    
    print(f"✓ 数据从第 {data_start_row + 1} 行开始")
    
    # Step 5: 选择关键列
    print("\nStep 5/7: 选择关键列（向下填充）")
    print("-" * 40)
    print("提示: 关键列通常包含合并单元格（如地区、类别等）")
    print("      这些列的空值会被向下填充\n")
    
    # 智能建议
    suggestions = suggest_key_columns(raw_df, header_rows)
    if suggestions:
        print(f"💡 建议关键列: {[c + 1 for c in suggestions]} (可能有合并单元格)")
    
    # 显示列信息
    print("\n可用列:")
    for i in range(min(5, len(raw_df.columns))):
        col_values = raw_df.iloc[data_start_row:data_start_row + 3, i].tolist()
        print(f"  列 {i + 1}: {col_values}")
    if len(raw_df.columns) > 5:
        print(f"  ... 还有 {len(raw_df.columns) - 5} 列")
    
    key_cols_input = ask_user("\n哪些列需要向下填充？（输入列号，如 1 或 1,3，不需要则输入 none）", "none")
    key_columns = parse_column_input(key_cols_input)
    
    if key_columns:
        print(f"✓ 已选择关键列: {[c + 1 for c in key_columns]}")
    else:
        print("✓ 不填充任何列")
    
    # Step 6: 选择分隔符
    print("\nStep 6/7: 配置分隔符")
    print("-" * 40)
    
    print("分隔符用于连接多级表头，如 'Q1' + '/' + 'Sales' = 'Q1/Sales'")
    separator = ask_user("选择分隔符", " / ")
    
    print(f"✓ 使用分隔符: '{separator}'")
    
    # Step 7: 执行清洗
    print("\nStep 7/7: 执行清洗")
    print("-" * 40)
    
    # 验证参数
    is_valid, error_msg = validate_cleaning_params(header_rows, data_start_row, len(raw_df))
    if not is_valid:
        print(f"❌ 参数错误: {error_msg}")
        return
    
    print("🔄 正在清洗数据...")
    
    try:
        result = cleaner.clean_data(
            file_content=file_path,
            header_rows=header_rows,
            data_start_row=data_start_row,
            key_columns=key_columns,
            separator=separator,
            sheet_name=sheet_name
        )
        
        cleaned_df = result['cleaned_df']
        
        print(f"✅ 清洗完成！")
        print(f"   原始数据: {len(raw_df)} 行")
        print(f"   清洗后: {len(cleaned_df)} 行")
        print(f"   列名: {list(cleaned_df.columns)}")
        
        # 显示结果预览
        print("\n结果预览（前5行）:")
        print(simple_preview(cleaned_df, max_rows=5))
        
    except Exception as e:
        print(f"❌ 清洗失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 导出结果
    print("\n" + "="*60)
    if ask_yes_no("是否导出为 Excel 文件？", True):
        import os
        
        # 生成输出文件名
        base_name = os.path.splitext(file_info['name'])[0]
        output_path = f"cleaned_{base_name}.xlsx"
        
        # 如果文件已存在，添加数字后缀
        counter = 1
        while os.path.exists(output_path):
            output_path = f"cleaned_{base_name}_{counter}.xlsx"
            counter += 1
        
        try:
            cleaned_df.to_excel(output_path, index=False)
            print(f"✅ 已导出: {output_path}")
            print(f"   文件大小: {format_file_size(os.path.getsize(output_path))}")
        except Exception as e:
            print(f"❌ 导出失败: {e}")
    
    print("\n" + "="*60)
    print("感谢使用 Excel 数据清洗助手！")
    print("="*60 + "\n")
    
    return result


if __name__ == "__main__":
    # 直接运行交互式清洗
    interactive_clean()
