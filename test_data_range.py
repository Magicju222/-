"""
测试数据结束行和结束列功能的测试脚本 (1-based索引版本)
"""
import pandas as pd
import numpy as np
import io
from cleaner import ExcelCleaner

def test_data_end_row():
    """测试数据结束行功能 (1-based)"""
    print("=" * 60)
    print("测试 1: 数据结束行功能 (1-based)")
    print("=" * 60)
    
    # 创建一个测试数据框
    data = [
        ['Name', 'Age', 'Score'],      # Row 1: Header (1-based)
        ['Alice', 25, 90],             # Row 2: Data
        ['Bob', 30, 85],               # Row 3: Data
        ['Charlie', 35, 95],           # Row 4: Data
        ['David', 40, 80],             # Row 5: Data
        ['Eve', 45, 88],               # Row 6: Data
        ['Frank', 50, 92],             # Row 7: Data
    ]
    
    test_df = pd.DataFrame(data)
    
    # 模拟 ui.py 的转换逻辑 (1-based to 0-based)
    # 用户输入 5 (1-based) -> 内部使用 4 (0-based)
    user_input_end_row = 5  # 用户输入第5行结束
    internal_end_row = user_input_end_row - 1  # 转换为 0-based = 4
    
    print(f"\n场景: 用户设置结束行 = {user_input_end_row} (1-based)")
    print(f"  内部转换为: {internal_end_row} (0-based)")
    
    # 数据从第2行开始 (1-based = 索引1)
    data_start_row = 1  # 0-based
    
    # 使用 iloc 切片 [start:end+1]
    sliced = test_df.iloc[data_start_row:internal_end_row+1].copy()
    print(f"  结果: 从第{data_start_row+1}行到第{internal_end_row+1}行，共 {len(sliced)} 行")
    print(f"  数据:\n{sliced}")
    
    # 验证: 应该取到第5行 (Alice, Bob, Charlie, David)
    assert len(sliced) == 4, f"期望4行，实际{len(sliced)}行"
    print("✓ 数据结束行功能测试通过")

def test_data_end_col():
    """测试数据结束列功能 (1-based)"""
    print("\n" + "=" * 60)
    print("测试 2: 数据结束列功能 (1-based)")
    print("=" * 60)
    
    data = [
        ['Name', 'Age', 'Score', 'City', 'Country'],  # Header
        ['Alice', 25, 90, 'NY', 'USA'],                # Data
        ['Bob', 30, 85, 'LA', 'USA'],                  # Data
    ]
    
    test_df = pd.DataFrame(data)
    
    # 用户输入 3 (1-based) -> 内部使用 2 (0-based)
    user_input_end_col = 3  # 用户输入第3列结束
    internal_end_col = user_input_end_col - 1  # 转换为 0-based = 2
    
    print(f"\n场景: 用户设置结束列 = {user_input_end_col} (1-based)")
    print(f"  内部转换为: {internal_end_col} (0-based)")
    
    # 使用 iloc 切片 [:end+1]
    sliced = test_df.iloc[1:, :internal_end_col+1].copy()
    print(f"  结果: 从第1列到第{internal_end_col+1}列，共 {len(sliced.columns)} 列")
    print(f"  列名: {list(sliced.columns)}")
    print(f"  数据:\n{sliced}")
    
    assert len(sliced.columns) == 3, f"期望3列，实际{len(sliced.columns)}列"
    print("✓ 数据结束列功能测试通过")

def test_combined_range():
    """测试同时设置结束行和结束列 (1-based)"""
    print("\n" + "=" * 60)
    print("测试 3: 同时设置结束行和结束列 (1-based)")
    print("=" * 60)
    
    data = [
        ['Name', 'Age', 'Score', 'City', 'Country', 'Salary'],  # Row 1
        ['Alice', 25, 90, 'NY', 'USA', 50000],                   # Row 2
        ['Bob', 30, 85, 'LA', 'USA', 60000],                     # Row 3
        ['Charlie', 35, 95, 'SF', 'USA', 70000],                 # Row 4
        ['David', 40, 80, 'NY', 'USA', 55000],                   # Row 5
        ['Eve', 45, 88, 'LA', 'USA', 65000],                     # Row 6
    ]
    
    test_df = pd.DataFrame(data)
    
    # 用户输入
    user_end_row = 4  # 第4行结束 (1-based)
    user_end_col = 4  # 第4列结束 (1-based)
    
    # 内部转换
    internal_end_row = user_end_row - 1  # 3 (0-based)
    internal_end_col = user_end_col - 1  # 3 (0-based)
    data_start_row = 1  # 0-based (第2行)
    
    print(f"\n场景: 用户设置结束行={user_end_row}, 结束列={user_end_col} (1-based)")
    print(f"  内部转换: 结束行={internal_end_row}, 结束列={internal_end_col} (0-based)")
    
    sliced = test_df.iloc[data_start_row:internal_end_row+1, :internal_end_col+1].copy()
    print(f"  结果: {len(sliced)} 行 x {len(sliced.columns)} 列")
    print(f"  数据:\n{sliced}")
    
    assert len(sliced) == 3, f"期望3行，实际{len(sliced)}行"
    assert len(sliced.columns) == 4, f"期望4列，实际{len(sliced.columns)}列"
    print("✓ 组合范围功能测试通过")

def test_with_excel_cleaner():
    """使用 ExcelCleaner 测试完整流程 (1-based)"""
    print("\n" + "=" * 60)
    print("测试 4: ExcelCleaner 完整流程测试 (1-based)")
    print("=" * 60)
    
    cleaner = ExcelCleaner()
    
    csv_content = """Name,Age,Score,City,Country
Alice,25,90,NY,USA
Bob,30,85,LA,USA
Charlie,35,95,SF,USA
David,40,80,NY,USA
Eve,45,88,LA,USA
Frank,50,92,SF,USA"""
    
    file_obj = io.BytesIO(csv_content.encode('utf-8'))
    file_obj.name = 'test.csv'
    
    print("\n场景1: 不设置结束行和结束列")
    result1 = cleaner.clean_data(
        file_content=file_obj,
        header_rows=[0],  # 第1行是表头 (0-based)
        data_start_row=1,  # 第2行开始 (0-based)
        data_end_row=None,
        data_end_col=None
    )
    print(f"  结果: {len(result1['cleaned_df'])} 行 x {len(result1['cleaned_df'].columns)} 列")
    
    # 重置文件指针
    file_obj.seek(0)
    
    # 用户想要取到第4行 (1-based) = 索引3 (0-based)
    # 用户想要取到第3列 (1-based) = 索引2 (0-based)
    user_end_row = 4  # 1-based
    user_end_col = 3  # 1-based
    internal_end_row = user_end_row - 1  # 3 (0-based)
    internal_end_col = user_end_col - 1  # 2 (0-based)
    
    print(f"\n场景2: 用户设置结束行={user_end_row}, 结束列={user_end_col} (1-based)")
    print(f"  内部转换: 结束行={internal_end_row}, 结束列={internal_end_col} (0-based)")
    
    result2 = cleaner.clean_data(
        file_content=file_obj,
        header_rows=[0],
        data_start_row=1,
        data_end_row=internal_end_row,
        data_end_col=internal_end_col
    )
    print(f"  结果: {len(result2['cleaned_df'])} 行 x {len(result2['cleaned_df'].columns)} 列")
    print(f"  列名: {list(result2['cleaned_df'].columns)}")
    print(f"  数据:\n{result2['cleaned_df']}")
    
    assert len(result1['cleaned_df']) == 6, f"期望6行，实际{len(result1['cleaned_df'])}行"
    assert len(result2['cleaned_df']) == 3, f"期望3行，实际{len(result2['cleaned_df'])}行"  # 第2,3,4行
    assert len(result2['cleaned_df'].columns) == 3, f"期望3列，实际{len(result2['cleaned_df'].columns)}列"
    print("✓ ExcelCleaner 完整流程测试通过")

def test_ui_conversion_logic():
    """测试 UI 转换逻辑 (1-based to 0-based)"""
    print("\n" + "=" * 60)
    print("测试 5: UI 转换逻辑测试 (1-based to 0-based)")
    print("=" * 60)
    
    # 模拟 ui.py 中的转换逻辑
    def convert_to_internal(data_end_row_1based, data_end_col_1based):
        """模拟 ui.py 的转换逻辑"""
        internal_data_end_row = data_end_row_1based - 1 if data_end_row_1based is not None else None
        internal_data_end_col = data_end_col_1based - 1 if data_end_col_1based is not None else None
        return internal_data_end_row, internal_data_end_col
    
    test_cases = [
        # (user_input_row, user_input_col, expected_row, expected_col)
        (5, 3, 4, 2),   # 正常情况
        (1, 1, 0, 0),   # 最小值
        (None, None, None, None),  # 不设置
        (10, None, 9, None),  # 只设置行
        (None, 5, None, 4),   # 只设置列
    ]
    
    for user_row, user_col, expected_row, expected_col in test_cases:
        result_row, result_col = convert_to_internal(user_row, user_col)
        assert result_row == expected_row, f"行转换失败: {user_row} -> {result_row}, 期望 {expected_row}"
        assert result_col == expected_col, f"列转换失败: {user_col} -> {result_col}, 期望 {expected_col}"
        print(f"  ✓ {user_row}, {user_col} -> {result_row}, {result_col}")
    
    print("✓ UI 转换逻辑测试通过")

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("开始测试数据范围功能（1-based 索引版本）")
    print("=" * 70)
    
    try:
        test_data_end_row()
        test_data_end_col()
        test_combined_range()
        test_with_excel_cleaner()
        test_ui_conversion_logic()
        
        print("\n" + "=" * 70)
        print("所有测试通过！✅")
        print("=" * 70)
        print("\n功能说明:")
        print("- 数据开始行: 1-based 索引（用户输入2表示第2行）")
        print("- 数据结束行: 1-based 索引（用户输入100表示第100行）")
        print("- 数据结束列: 1-based 索引（用户输入10表示第10列）")
        print("- 输入0或留空表示不限制（到最后一行/列）")
        print("- 内部处理时自动转换为 0-based 索引")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
