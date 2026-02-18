"""
AI图像生成提示词库
用于为报告生成配图和示意图
"""

ILLUSTRATION_GENERATION_PROMPT = """
为以下业务洞察生成专业配图：

洞察标题：{insight_title}
洞察描述：{insight_description}
关键数据：{key_data}

要求：
- 风格：{style}（professional/modern/abstract）
- 内容：抽象化、概念化的商业数据可视化
- 主题：{theme}
- 用途：数据分析报告配图
- 尺寸：16:9宽屏比例
- 色调：商务蓝/灰色调

图像应该：
- 简洁专业
- 突出关键信息
- 易于理解
- 符合商务场景
"""

INFOGRAPHIC_GENERATION_PROMPT = """
生成一个信息图，汇总以下关键洞察：

洞察列表：
{insights_summary}

布局要求：
1. 标题区域（报告主题）
2. 3-4个关键数字突出显示
3. 主要发现区域（图标+简短描述）
4. 建议行动区域
5. 配色方案（专业商务）

风格：
- 现代简约
- 信息层次清晰
- 视觉吸引力强
- 适合演示汇报
"""

CHART_CONCEPT_PROMPT = """
为数据图表生成概念说明图：

图表类型：{chart_type}
数据主题：{data_theme}
关键信息：{key_message}

要求：
- 展示图表的核心概念
- 突出数据关系
- 简洁易懂
- 适合作为章节配图
"""
