"""
AI图表生成器
利用大模型生成Python代码创建专业图表
"""

import os
import re
import tempfile
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from io import BytesIO
from PIL import Image
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt

from llm_client import LLMClient
from prompts.chart_generation import CHART_CODE_GENERATION_PROMPT


class ChartGenerator:
    """
    AI图表生成器
    使用大模型生成代码创建数据可视化图表
    """
    
    # 支持的图表类型
    SUPPORTED_CHARTS = {
        'line': '折线图',
        'bar': '柱状图',
        'pie': '饼图',
        'scatter': '散点图',
        'histogram': '直方图',
        'box': '箱线图',
        'heatmap': '热力图',
        'area': '面积图',
        'bubble': '气泡图'
    }
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.temp_dir = tempfile.mkdtemp()
    
    def generate_chart(self,
                      df: pd.DataFrame,
                      chart_type: str,
                      columns: List[str],
                      title: str = "",
                      output_path: Optional[str] = None) -> str:
        """
        生成图表
        
        Args:
            df: 数据
            chart_type: 图表类型
            columns: 涉及的列
            title: 图表标题
            output_path: 输出路径（可选）
        
        Returns:
            生成的图表文件路径
        """
        if output_path is None:
            output_path = os.path.join(self.temp_dir, f"chart_{hash(str(df))}.png")
        
        # 构建图表要求
        chart_requirements = {
            'chart_type': chart_type,
            'columns': columns,
            'title': title or f'{chart_type} Chart',
            'style': 'professional',
            'color_scheme': 'blue'
        }
        
        # 生成代码
        code = self._generate_chart_code(df, chart_requirements, output_path)
        
        # 执行代码
        self._execute_chart_code(code, df, output_path)
        
        return output_path
    
    def generate_chart_from_recommendation(self,
                                          df: pd.DataFrame,
                                          recommendation: Dict) -> str:
        """
        根据可视化建议生成图表
        
        Args:
            df: 数据
            recommendation: 可视化建议
        
        Returns:
            图表文件路径
        """
        chart_type = recommendation.get('chart_type', 'bar')
        columns = recommendation.get('columns', df.columns[:2].tolist())
        title = recommendation.get('title', '')
        
        return self.generate_chart(df, chart_type, columns, title)
    
    def _generate_chart_code(self,
                            df: pd.DataFrame,
                            chart_requirements: Dict,
                            output_path: str) -> str:
        """
        使用大模型生成图表代码
        
        Args:
            df: 数据
            chart_requirements: 图表要求
            output_path: 输出路径
        
        Returns:
            Python代码
        """
        # 准备数据信息
        data_sample = df.head(10).to_dict()
        
        prompt = CHART_CODE_GENERATION_PROMPT.format(
            data_shape=str(df.shape),
            columns=json.dumps(df.columns.tolist(), ensure_ascii=False),
            data_sample=json.dumps(data_sample, ensure_ascii=False, default=str),
            chart_requirements=json.dumps(chart_requirements, ensure_ascii=False),
            output_path=output_path,
            data_dict='df.to_dict()'
        )
        
        try:
            code = self.llm.generate_code(prompt)
            return code
        except Exception as e:
            # 生成失败，使用默认代码
            return self._get_default_chart_code(
                df, chart_requirements, output_path
            )
    
    def _get_default_chart_code(self,
                               df: pd.DataFrame,
                               chart_requirements: Dict,
                               output_path: str) -> str:
        """获取默认图表代码"""
        chart_type = chart_requirements.get('chart_type', 'bar')
        columns = chart_requirements.get('columns', df.columns[:2].tolist())
        title = chart_requirements.get('title', 'Chart')
        
        if chart_type == 'scatter' and len(columns) >= 2:
            return f'''
import matplotlib.pyplot as plt
import pandas as pd

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建图表
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df['{columns[0]}'], df['{columns[1]}'], alpha=0.6)
ax.set_xlabel('{columns[0]}', fontsize=12)
ax.set_ylabel('{columns[1]}', fontsize=12)
ax.set_title('{title}', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.savefig('{output_path}', dpi=150, bbox_inches='tight')
plt.close()
'''
        elif chart_type == 'line' and len(columns) >= 2:
            return f'''
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['{columns[0]}'], df['{columns[1]}'], marker='o')
ax.set_xlabel('{columns[0]}', fontsize=12)
ax.set_ylabel('{columns[1]}', fontsize=12)
ax.set_title('{title}', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

plt.savefig('{output_path}', dpi=150, bbox_inches='tight')
plt.close()
'''
        elif chart_type == 'histogram':
            col = columns[0] if columns else df.select_dtypes(include=[np.number]).columns[0]
            return f'''
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(df['{col}'], bins=20, alpha=0.7, edgecolor='black')
ax.set_xlabel('{col}', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.set_title('{title}', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

plt.savefig('{output_path}', dpi=150, bbox_inches='tight')
plt.close()
'''
        else:  # 默认柱状图
            col = columns[0] if columns else df.columns[0]
            return f'''
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(10, 6))
value_counts = df['{col}'].value_counts().head(10)
ax.bar(range(len(value_counts)), value_counts.values)
ax.set_xticks(range(len(value_counts)))
ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
ax.set_xlabel('{col}', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('{title}', fontsize=14, fontweight='bold')

plt.tight_layout()
plt.savefig('{output_path}', dpi=150, bbox_inches='tight')
plt.close()
'''
    
    def _execute_chart_code(self,
                           code: str,
                           df: pd.DataFrame,
                           output_path: str):
        """
        安全执行图表代码
        
        Args:
            code: Python代码
            df: 数据
            output_path: 输出路径
        """
        # 创建安全的执行环境
        safe_globals = {
            'pd': pd,
            'np': np,
            'plt': plt,
            'df': df
        }
        
        safe_locals = {}
        
        try:
            exec(code, safe_globals, safe_locals)
        except Exception as e:
            # 执行失败，使用matplotlib直接生成简单图表
            self._generate_fallback_chart(df, output_path)
    
    def _generate_fallback_chart(self, df: pd.DataFrame, output_path: str):
        """生成备用图表"""
        plt.figure(figsize=(10, 6))
        
        # 尝试绘制数值列的分布
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            plt.hist(df[col].dropna(), bins=20, alpha=0.7, edgecolor='black')
            plt.xlabel(col)
            plt.ylabel('Frequency')
            plt.title(f'{col} Distribution')
        else:
            # 绘制类别列的计数
            col = df.columns[0]
            value_counts = df[col].value_counts().head(10)
            plt.bar(range(len(value_counts)), value_counts.values)
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45)
            plt.xlabel(col)
            plt.ylabel('Count')
            plt.title(f'{col} Value Counts')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    
    def generate_multiple_charts(self,
                                df: pd.DataFrame,
                                recommendations: List[Dict]) -> List[str]:
        """
        生成多个图表
        
        Args:
            df: 数据
            recommendations: 可视化建议列表
        
        Returns:
            图表文件路径列表
        """
        chart_paths = []
        
        for i, rec in enumerate(recommendations):
            try:
                path = self.generate_chart_from_recommendation(df, rec)
                chart_paths.append(path)
            except Exception as e:
                # 单个图表失败不影响其他
                continue
        
        return chart_paths
    
    def get_chart_image(self, chart_path: str) -> Image.Image:
        """
        获取图表图像
        
        Args:
            chart_path: 图表文件路径
        
        Returns:
            PIL图像对象
        """
        return Image.open(chart_path)
    
    def cleanup(self):
        """清理临时文件"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
