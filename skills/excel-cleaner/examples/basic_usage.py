"""
基础使用示例
展示如何编程式调用 ExcelCleaner
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_cleaner import ExcelCleaner
import pandas as pd


def example_basic():
    """基础清洗示例"""
    print("=" * 60)
    print("示例 1: 基础清洗")
    print("=" * 60)
    
    cleaner = ExcelCleaner()
    
    # 假设有一个文件 data.xlsx
    file_path = "data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        print("请创建一个测试文件或修改文件路径")
        return
    
    # 执行清洗
    result = cleaner.clean_data(
        file_content=file_path,
        header_rows=[0, 1],      # 第1、2行是表头
        data_start_row=2,        # 第3行开始数据
        key_columns=[0],         # 第1列需要向下填充
        separator=" / "          # 多级表头分隔符
    )
    
    # 查看结果
    cleaned_df = result['cleaned_df']
    print(f"✓ 清洗完成！")
    print(f"  原始数据: {len(result['raw_df'])} 行")
    print(f"  清洗后: {len(cleaned_df)} 行")
    print(f"  列名: {list(cleaned_df.columns)}")
    print("\n前5行预览:")
    print(cleaned_df.head())
    
    # 导出
    output_path = "output_basic.xlsx"
    cleaned_df.to_excel(output_path, index=False)
    print(f"\n✓ 已导出: {output_path}")


def example_simple():
    """简单清洗（单级表头）"""
    print("\n" + "=" * 60)
    print("示例 2: 简单清洗（单级表头）")
    print("=" * 60)
    
    cleaner = ExcelCleaner()
    file_path = "data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        return
    
    result = cleaner.clean_data(
        file_content=file_path,
        header_rows=[0],         # 只有第1行是表头
        data_start_row=1,        # 第2行开始数据
        key_columns=[],          # 无关键列
        separator="_"
    )
    
    cleaned_df = result['cleaned_df']
    print(f"✓ 清洗完成！")
    print(f"  列名: {list(cleaned_df.columns)}")
    print("\n前5行:")
    print(cleaned_df.head())


def example_with_key_columns():
    """带关键列填充的示例"""
    print("\n" + "=" * 60)
    print("示例 3: 带关键列填充")
    print("=" * 60)
    
    cleaner = ExcelCleaner()
    file_path = "data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        return
    
    # 假设第1列是"地区"，有合并单元格
    result = cleaner.clean_data(
        file_content=file_path,
        header_rows=[0],
        data_start_row=1,
        key_columns=[0, 2],      # 第1列和第3列需要向下填充
        separator="_"
    )
    
    cleaned_df = result['cleaned_df']
    print(f"✓ 清洗完成！")
    print(f"  关键列已填充: 第1列, 第3列")
    print("\n前5行:")
    print(cleaned_df.head())


def example_multi_sheet():
    """多工作表示例"""
    print("\n" + "=" * 60)
    print("示例 4: 处理多个工作表")
    print("=" * 60)
    
    cleaner = ExcelCleaner()
    file_path = "multi_sheet.xlsx"
    
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        return
    
    # 获取所有工作表
    sheet_names = cleaner.get_sheet_names(file_path)
    print(f"发现 {len(sheet_names)} 个工作表: {sheet_names}")
    
    # 处理每个工作表
    for sheet in sheet_names:
        print(f"\n处理工作表: {sheet}")
        
        result = cleaner.clean_data(
            file_content=file_path,
            header_rows=[0, 1],
            data_start_row=2,
            sheet_name=sheet
        )
        
        output_path = f"cleaned_{sheet}.xlsx"
        result['cleaned_df'].to_excel(output_path, index=False)
        print(f"  ✓ 已导出: {output_path}")


def example_api_methods():
    """展示各个 API 方法的使用"""
    print("\n" + "=" * 60)
    print("示例 5: API 方法详解")
    print("=" * 60)
    
    cleaner = ExcelCleaner()
    file_path = "data.xlsx"
    
    if not os.path.exists(file_path):
        print(f"⚠️ 文件不存在: {file_path}")
        return
    
    # 1. 加载并处理合并单元格
    print("\n1. 加载文件并处理合并单元格:")
    raw_df = cleaner.load_and_fill_merged_cells(file_path)
    print(f"   加载了 {len(raw_df)} 行 x {len(raw_df.columns)} 列")
    
    # 2. 处理表头
    print("\n2. 处理多级表头:")
    header_rows = [0, 1]
    new_columns = cleaner.process_headers(raw_df, header_rows, separator=" / ")
    print(f"   原始列数: {len(raw_df.columns)}")
    print(f"   处理后列名: {new_columns[:5]}...")  # 只显示前5个
    
    # 3. 处理关键列
    print("\n3. 处理关键列（向下填充）:")
    # 创建一个示例 DataFrame
    sample_df = pd.DataFrame({
        'Region': ['North', None, None, 'South', None],
        'Sales': [100, 200, 300, 400, 500]
    })
    print("   填充前:")
    print(sample_df)
    
    filled_df = cleaner.process_key_columns(sample_df, key_columns=[0])
    print("\n   填充后:")
    print(filled_df)


if __name__ == "__main__":
    print("Excel Cleaner - 基础使用示例")
    print("=" * 60)
    print("\n注意: 请确保有测试文件 data.xlsx 或修改代码中的文件路径\n")
    
    # 运行示例
    example_basic()
    # example_simple()
    # example_with_key_columns()
    # example_multi_sheet()
    # example_api_methods()
    
    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)
