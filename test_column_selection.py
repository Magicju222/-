"""
测试列选择功能的脚本
"""
import pandas as pd
import streamlit as st

# 模拟数据
df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie', 'David'],
    'Age': [25, 30, 35, 40],
    'Score': [90, 85, 95, 80],
    'City': ['NY', 'LA', 'SF', 'NY']
})

print("原始数据框:")
print(df)
print("\n原始列名:", list(df.columns))
print("原始列索引:", [df.columns.get_loc(c) for c in df.columns])

# 模拟显示数据框（1-based列）
display_df = df.copy()
display_df.index = display_df.index + 1  # 行索引1-based
display_df.columns = [str(i + 1) for i in range(len(df.columns))]  # 列标题1-based

print("\n显示数据框（1-based列）:")
print(display_df)
print("显示列名:", list(display_df.columns))

# 模拟用户选择第3列（显示为'3'）
selected_col_from_ui = '3'  # 用户点击的是显示的第3列
print(f"\n用户选择的列（显示）: {selected_col_from_ui}")

# 转换为实际列索引（0-based）
actual_col_idx = int(selected_col_from_ui) - 1
print(f"实际列索引（0-based）: {actual_col_idx}")
print(f"对应原始列名: {df.columns[actual_col_idx]}")

# 数据结束列应该存储的值（1-based）
data_end_col_value = int(selected_col_from_ui)
print(f"\n数据结束列应该存储的值（1-based）: {data_end_col_value}")

# 关键列应该存储的值（0-based索引列表）
key_cols_value = [int(selected_col_from_ui) - 1]
print(f"关键列应该存储的值（0-based列表）: {key_cols_value}")
