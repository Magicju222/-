"""
创建真正的测试Excel文件
"""
import pandas as pd

# 创建测试数据
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'Age': [25, 30, 35, 40, 28],
    'Score': [90, 85, 95, 80, 92],
    'City': ['NY', 'LA', 'SF', 'NY', 'LA']
}

df = pd.DataFrame(data)

# 保存为Excel文件
output_path = 'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data.xlsx'
df.to_excel(output_path, index=False, sheet_name='Sheet1')

print(f"已创建测试文件: {output_path}")
print(f"文件内容:\n{df}")
