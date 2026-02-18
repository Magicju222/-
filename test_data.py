"""
创建测试用的 Excel 文件
"""
import pandas as pd
import numpy as np

# 创建测试数据
np.random.seed(42)
n = 100

data = {
    '姓名': [f'用户{i}' for i in range(n)],
    '年龄': np.random.randint(18, 65, n),
    '收入': np.random.randint(3000, 50000, n),
    '部门': np.random.choice(['销售', '技术', '市场', '人事', '财务'], n),
    '入职年份': np.random.randint(2015, 2024, n),
    '绩效评分': np.random.uniform(60, 100, n).round(2),
    '是否全职': np.random.choice(['是', '否'], n),
}

df = pd.DataFrame(data)
df.to_excel('test_data.xlsx', index=False)
print("✅ 测试文件已创建: test_data.xlsx")
print(f"📊 数据形状: {df.shape}")
print(f"📋 列名: {list(df.columns)}")
