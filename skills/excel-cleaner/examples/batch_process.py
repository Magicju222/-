"""
批量处理示例
展示如何批量处理多个文件
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from excel_cleaner import ExcelCleaner
import pandas as pd
from pathlib import Path


def batch_process_folder(input_folder, output_folder, config):
    """
    批量处理文件夹中的所有 Excel 文件
    
    Args:
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径
        config: 清洗配置字典
    """
    cleaner = ExcelCleaner()
    
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)
    
    # 获取所有 Excel 文件
    excel_files = list(Path(input_folder).glob("*.xlsx"))
    excel_files.extend(Path(input_folder).glob("*.xls"))
    excel_files.extend(Path(input_folder).glob("*.csv"))
    
    print(f"发现 {len(excel_files)} 个文件待处理")
    print("=" * 60)
    
    success_count = 0
    failed_files = []
    
    for i, file_path in enumerate(excel_files, 1):
        print(f"\n[{i}/{len(excel_files)}] 处理: {file_path.name}")
        
        try:
            # 执行清洗
            result = cleaner.clean_data(
                file_content=str(file_path),
                header_rows=config['header_rows'],
                data_start_row=config['data_start_row'],
                key_columns=config.get('key_columns', []),
                separator=config.get('separator', '_'),
                sheet_name=config.get('sheet_name')
            )
            
            # 生成输出文件名
            base_name = file_path.stem
            output_path = os.path.join(output_folder, f"cleaned_{base_name}.xlsx")
            
            # 导出
            result['cleaned_df'].to_excel(output_path, index=False)
            
            print(f"  ✓ 成功 -> {output_path}")
            print(f"    原始: {len(result['raw_df'])} 行 -> 清洗后: {len(result['cleaned_df'])} 行")
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            failed_files.append((file_path.name, str(e)))
    
    # 输出统计
    print("\n" + "=" * 60)
    print("批量处理完成!")
    print(f"  成功: {success_count}/{len(excel_files)}")
    print(f"  失败: {len(failed_files)}")
    
    if failed_files:
        print("\n失败的文件:")
        for name, error in failed_files:
            print(f"  - {name}: {error}")


def batch_process_with_different_configs(input_folder, output_folder, config_file):
    """
    根据配置文件批量处理（每个文件可能有不同的配置）
    
    Args:
        input_folder: 输入文件夹路径
        output_folder: 输出文件夹路径
        config_file: 配置文件路径（JSON 格式）
    """
    import json
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        configs = json.load(f)
    
    cleaner = ExcelCleaner()
    os.makedirs(output_folder, exist_ok=True)
    
    print(f"根据配置文件处理 {len(configs)} 个文件")
    print("=" * 60)
    
    for file_name, config in configs.items():
        file_path = os.path.join(input_folder, file_name)
        
        if not os.path.exists(file_path):
            print(f"\n⚠️ 文件不存在: {file_name}")
            continue
        
        print(f"\n处理: {file_name}")
        print(f"  配置: {config}")
        
        try:
            result = cleaner.clean_data(
                file_content=file_path,
                **config
            )
            
            output_path = os.path.join(output_folder, f"cleaned_{file_name}")
            result['cleaned_df'].to_excel(output_path, index=False)
            
            print(f"  ✓ 成功 -> {output_path}")
            
        except Exception as e:
            print(f"  ✗ 失败: {e}")


def batch_merge_sheets(input_file, output_file, config):
    """
    将多工作表文件的所有表合并成一个
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        config: 清洗配置
    """
    cleaner = ExcelCleaner()
    
    # 获取所有工作表
    sheet_names = cleaner.get_sheet_names(input_file)
    print(f"发现 {len(sheet_names)} 个工作表: {sheet_names}")
    
    all_data = []
    
    for sheet in sheet_names:
        print(f"\n处理工作表: {sheet}")
        
        result = cleaner.clean_data(
            file_content=input_file,
            sheet_name=sheet,
            **config
        )
        
        # 添加来源标记
        df = result['cleaned_df']
        df['Source_Sheet'] = sheet
        
        all_data.append(df)
        print(f"  ✓ 添加了 {len(df)} 行")
    
    # 合并所有数据
    merged_df = pd.concat(all_data, ignore_index=True)
    
    # 导出
    merged_df.to_excel(output_file, index=False)
    
    print("\n" + "=" * 60)
    print(f"✓ 合并完成!")
    print(f"  总工作表: {len(sheet_names)}")
    print(f"  总行数: {len(merged_df)}")
    print(f"  已导出: {output_file}")


def create_sample_config():
    """创建示例配置文件"""
    import json
    
    config = {
        "file1.xlsx": {
            "header_rows": [0, 1],
            "data_start_row": 2,
            "key_columns": [0],
            "separator": " / "
        },
        "file2.xlsx": {
            "header_rows": [0],
            "data_start_row": 1,
            "key_columns": [],
            "separator": "_"
        },
        "file3.csv": {
            "header_rows": [0],
            "data_start_row": 1,
            "key_columns": [0, 1],
            "separator": " | "
        }
    }
    
    with open('batch_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✓ 示例配置文件已创建: batch_config.json")
    print("\n文件内容:")
    print(json.dumps(config, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    print("Excel Cleaner - 批量处理示例")
    print("=" * 60)
    
    # 示例 1: 批量处理文件夹
    print("\n示例 1: 批量处理文件夹中的所有文件")
    print("-" * 60)
    
    # 配置
    config = {
        'header_rows': [0, 1],
        'data_start_row': 2,
        'key_columns': [0],
        'separator': ' / '
    }
    
    # 批量处理（请确保 input 文件夹存在）
    # batch_process_folder('input', 'output', config)
    
    print("\n注意: 请创建 input 文件夹并放入测试文件，或修改代码中的路径")
    
    # 示例 2: 创建配置文件
    print("\n示例 2: 创建示例配置文件")
    print("-" * 60)
    create_sample_config()
    
    # 示例 3: 根据配置文件处理
    print("\n示例 3: 根据配置文件批量处理")
    print("-" * 60)
    # batch_process_with_different_configs('input', 'output', 'batch_config.json')
    
    # 示例 4: 合并多工作表
    print("\n示例 4: 合并多工作表文件")
    print("-" * 60)
    # batch_merge_sheets(
    #     'multi_sheet.xlsx',
    #     'merged_output.xlsx',
    #     config
    # )
    
    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)
