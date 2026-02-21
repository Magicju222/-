import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建测试数据 - 销售分析场景
np.random.seed(42)

# 1. 销售数据
n_records = 150
dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n_records)]
regions = ['华北', '华东', '华南', '西南', '东北'] * 30
products = ['产品A', '产品B', '产品C', '产品D', '产品E'] * 30
sales_reps = ['张三', '李四', '王五', '赵六', '钱七'] * 30

sales_data = pd.DataFrame({
    '日期': dates,
    '地区': regions[:n_records],
    '产品': products[:n_records],
    '销售员': sales_reps[:n_records],
    '销售额': np.random.randint(10000, 100000, n_records),
    '销售量': np.random.randint(10, 200, n_records),
    '客户数': np.random.randint(5, 50, n_records),
    '利润率': np.random.uniform(0.1, 0.4, n_records)
})

# 2. 客户数据
n_customers = 80
customer_types = ['企业客户', '个人客户', '政府客户', '渠道客户'] * 20
customer_levels = ['VIP', '普通', '新客户', '流失风险'] * 20

customer_data = pd.DataFrame({
    '客户ID': [f'CUST_{i:04d}' for i in range(n_customers)],
    '客户名称': [f'客户_{i}' for i in range(n_customers)],
    '客户类型': customer_types[:n_customers],
    '客户等级': customer_levels[:n_customers],
    '年消费额': np.random.randint(5000, 500000, n_customers),
    '订单次数': np.random.randint(1, 50, n_customers),
    '最近购买日期': [datetime(2024, 1, 1) + timedelta(days=np.random.randint(0, 365)) for _ in range(n_customers)],
    '满意度评分': np.random.uniform(3.0, 5.0, n_customers)
})

# 3. 产品数据
n_products = 20
categories = ['电子产品', '家居用品', '办公用品', '服装配饰', '食品饮料'] * 4

product_data = pd.DataFrame({
    '产品ID': [f'PROD_{i:04d}' for i in range(n_products)],
    '产品名称': [f'产品_{i}' for i in range(n_products)],
    '产品类别': categories[:n_products],
    '单价': np.random.randint(50, 5000, n_products),
    '库存量': np.random.randint(0, 1000, n_products),
    '月销量': np.random.randint(10, 500, n_products),
    '退货率': np.random.uniform(0.01, 0.15, n_products),
    '好评率': np.random.uniform(0.85, 0.99, n_products)
})

# 4. 区域业绩数据
region_performance = pd.DataFrame({
    '地区': ['华北', '华东', '华南', '西南', '东北'],
    '年度目标': [5000000, 8000000, 7000000, 4000000, 3000000],
    '实际完成': [4800000, 8200000, 6800000, 4200000, 2800000],
    '同比增长': [0.12, 0.18, 0.08, 0.15, 0.05],
    '市场份额': [0.20, 0.35, 0.28, 0.12, 0.05],
    '销售人员数': [25, 40, 35, 18, 12],
    '客户总数': [450, 780, 650, 320, 180]
})

# 保存到Excel
with pd.ExcelWriter('e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\sales_analysis_test.xlsx', engine='openpyxl') as writer:
    sales_data.to_excel(writer, sheet_name='销售明细', index=False)
    customer_data.to_excel(writer, sheet_name='客户数据', index=False)
    product_data.to_excel(writer, sheet_name='产品数据', index=False)
    region_performance.to_excel(writer, sheet_name='区域业绩', index=False)

print("测试数据文件已创建: sales_analysis_test.xlsx")
print("包含4个工作表:")
print("1. 销售明细 - 150条销售记录")
print("2. 客户数据 - 80条客户信息")
print("3. 产品数据 - 20条产品信息")
print("4. 区域业绩 - 5个地区业绩对比")
