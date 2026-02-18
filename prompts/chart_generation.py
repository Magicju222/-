"""
AI图表生成提示词库
"""

CHART_CODE_GENERATION_PROMPT = """
你是一位数据可视化专家。请根据以下要求生成Python代码来创建专业图表。

数据信息：
- 数据形状: {data_shape}
- 列名: {columns}
- 数据样本: {data_sample}

可视化要求：
{chart_requirements}

要求：
1. 使用matplotlib或plotly
2. 包含所有必要的样式设置
3. 确保图表专业美观
4. 保存为PNG格式到指定路径
5. 代码必须可执行，处理所有边界情况
6. 添加中文支持（使用SimHei字体）
7. 图表标题、轴标签、图例清晰

只返回Python代码，不要其他解释。
代码格式：
```python
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 数据准备
data = {data_dict}
df = pd.DataFrame(data)

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))

# 绘图代码...

# 样式设置
plt.title('图表标题', fontsize=14, fontweight='bold')
plt.xlabel('X轴标签', fontsize=12)
plt.ylabel('Y轴标签', fontsize=12)
plt.grid(True, alpha=0.3)

# 保存
plt.savefig('{output_path}', dpi=150, bbox_inches='tight')
plt.close()
```
"""

CHART_RECOMMENDATION_PROMPT = """
基于数据分析结果，推荐最适合的可视化方案。

数据特征：
{data_characteristics}

分析维度：
{analysis_dimensions}

洞察内容：
{insight_content}

请为每个关键洞察推荐：
1. 图表类型（折线图/柱状图/饼图/散点图/热力图/箱线图等）
2. 推荐理由（为什么这种图表最适合）
3. 数据映射（X轴、Y轴、颜色、大小等维度）
4. 关键元素（需要突出的数据点、趋势线等）
5. 配色建议（符合数据语义的颜色）
6. 布局建议（标题、标签、注释位置）

请以JSON格式返回推荐列表。
"""
