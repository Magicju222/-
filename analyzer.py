"""
数据分析引擎
基于大模型提示词框架实现完整的数据分析流程
支持三级分析维度优先级：模板 > AI自动识别 > 用户手动输入
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from io import BytesIO
from PIL import Image

from llm_client import LLMClient
from prompts.data_analysis import (
    DATA_UNDERSTANDING_PROMPT,
    EDA_PROMPT,
    DEEP_ANALYSIS_PROMPT,
    EXTRACT_DIMENSIONS_FROM_TEMPLATE_PROMPT,
    RECOMMEND_DIMENSIONS_PROMPT
)


@dataclass
class AnalysisDimension:
    """分析维度数据类"""
    name: str
    dim_type: str  # 'univariate', 'bivariate', 'multivariate', 'other'
    source: str    # 'template', 'ai', 'user'
    priority: int  # 1=template, 2=ai, 3=user
    focus: str = ""
    columns: List[str] = field(default_factory=list)
    method: str = ""
    reason: str = ""


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    preprocessing: Dict
    eda: Dict
    insights: List[Dict]
    visualization_recommendations: List[Dict]
    merged_dimensions: List[AnalysisDimension]
    processing_log: List[str]


class DataAnalyzer:
    """
    数据分析引擎
    基于大模型提示词框架实现完整的数据分析流程
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.processing_log: List[str] = []
    
    def analyze(self, 
                df: pd.DataFrame,
                template_dimensions: Optional[List[str]] = None,
                user_dimensions: Optional[List[str]] = None,
                context: str = "") -> AnalysisResult:
        """
        执行完整的数据分析流程
        
        Args:
            df: 输入数据
            template_dimensions: 从模板提取的维度（最高优先级）
            user_dimensions: 用户手动输入的维度（最低优先级）
            context: 业务背景描述
        
        Returns:
            分析结果
        """
        self._log("开始数据分析流程")
        
        # 1. 数据理解与预处理
        self._log("步骤1: 数据理解与预处理")
        preprocessing = self._data_understanding_and_preprocessing(df)
        
        # 2. 分析维度处理
        self._log("处理分析维度")
        merged_dims = self._process_dimensions(
            df, template_dimensions, user_dimensions
        )
        
        # 3. 探索性数据分析
        self._log("步骤2: 探索性数据分析")
        eda = self._exploratory_data_analysis(df, preprocessing, merged_dims)
        
        # 4. 深度分析与洞察
        self._log("步骤3: 深度分析与洞察")
        insights = self._deep_analysis_and_insights(
            df, eda, merged_dims, context
        )
        
        # 5. 生成可视化建议
        self._log("生成可视化建议")
        viz_recommendations = self._generate_visualization_recommendations(
            df, eda, insights, merged_dims
        )
        
        self._log("数据分析完成")
        
        return AnalysisResult(
            preprocessing=preprocessing,
            eda=eda,
            insights=insights,
            visualization_recommendations=viz_recommendations,
            merged_dimensions=merged_dims,
            processing_log=self.processing_log
        )
    
    def _log(self, message: str):
        """记录处理日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.processing_log.append(log_entry)
    
    def extract_dimensions_from_template(self, 
                                        template_content: str) -> List[str]:
        """
        从分析模板内容中提取分析维度
        
        Args:
            template_content: 模板文本内容
        
        Returns:
            维度列表
        """
        self._log("从模板提取分析维度")
        
        prompt = EXTRACT_DIMENSIONS_FROM_TEMPLATE_PROMPT.format(
            template_content=template_content[:5000]  # 限制长度
        )
        
        try:
            result = self.llm.analyze_json(prompt)
            dimensions = result.get('dimensions', [])
            return [d['name'] for d in dimensions]
        except Exception as e:
            self._log(f"模板维度提取失败: {str(e)}")
            return []
    
    def recommend_dimensions(self, 
                            df: pd.DataFrame,
                            template_dimensions: Optional[List[str]] = None) -> List[AnalysisDimension]:
        """
        根据数据特征自动推荐分析维度
        必须包含单变量、双变量、多变量分析
        
        Args:
            df: 输入数据
            template_dimensions: 已有模板维度
        
        Returns:
            推荐的维度列表
        """
        self._log("自动推荐分析维度")
        
        # 准备数据特征
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        data_characteristics = {
            'total_rows': len(df),
            'total_cols': len(df.columns),
            'numeric_columns': numeric_cols,
            'categorical_columns': categorical_cols,
            'column_types': {col: str(df[col].dtype) for col in df.columns},
            'sample_data': df.head(5).to_dict()
        }
        
        prompt = RECOMMEND_DIMENSIONS_PROMPT.format(
            data_characteristics=json.dumps(data_characteristics, ensure_ascii=False, default=str),
            template_dimensions=json.dumps(template_dimensions or [], ensure_ascii=False)
        )
        
        try:
            result = self.llm.analyze_json(prompt)
            dimensions_data = result.get('dimensions', [])
            
            # 如果LLM返回空维度，使用默认维度
            if not dimensions_data:
                self._log("LLM返回空维度，使用默认维度")
                return self._get_default_dimensions(df)
            
            # 确保包含三类分析
            has_univariate = any(d.get('type') == 'univariate' for d in dimensions_data)
            has_bivariate = any(d.get('type') == 'bivariate' for d in dimensions_data)
            has_multivariate = any(d.get('type') == 'multivariate' for d in dimensions_data)
            
            # 如果缺少某类分析，添加默认的
            if not has_univariate and numeric_cols:
                dimensions_data.append({
                    'name': '数值列分布分析',
                    'type': 'univariate',
                    'columns': numeric_cols[:3],
                    'method': '描述统计',
                    'reason': '基础单变量分析'
                })
            
            if not has_bivariate and len(numeric_cols) >= 2:
                dimensions_data.append({
                    'name': '数值列相关性分析',
                    'type': 'bivariate',
                    'columns': numeric_cols[:2],
                    'method': '相关性分析',
                    'reason': '基础双变量分析'
                })
            
            if not has_multivariate and len(numeric_cols) >= 3:
                dimensions_data.append({
                    'name': '多变量关系分析',
                    'type': 'multivariate',
                    'columns': numeric_cols[:3],
                    'method': '主成分分析',
                    'reason': '基础多变量分析'
                })
            
            # 转换为AnalysisDimension对象
            dimensions = []
            for d in dimensions_data:
                dim = AnalysisDimension(
                    name=d.get('name', '未命名维度'),
                    dim_type=d.get('type', 'other'),
                    source='ai',
                    priority=2,
                    focus=d.get('focus', ''),
                    columns=d.get('columns', []),
                    method=d.get('method', ''),
                    reason=d.get('reason', '')
                )
                dimensions.append(dim)
            
            self._log(f"成功生成 {len(dimensions)} 个AI维度")
            return dimensions
            
        except Exception as e:
            self._log(f"维度推荐失败: {str(e)}")
            # 返回默认维度
            return self._get_default_dimensions(df)
    
    def _get_default_dimensions(self, df: pd.DataFrame) -> List[AnalysisDimension]:
        """获取默认分析维度"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        all_cols = list(df.columns)
        
        dimensions = []
        
        # 单变量分析 - 数值列
        for col in numeric_cols[:3]:
            dimensions.append(AnalysisDimension(
                name=f'{col}分布分析',
                dim_type='univariate',
                source='ai',
                priority=2,
                columns=[col],
                method='描述统计',
                reason='基础单变量分析'
            ))
        
        # 单变量分析 - 类别列（如果没有数值列，使用类别列）
        if not numeric_cols:
            for col in categorical_cols[:3]:
                dimensions.append(AnalysisDimension(
                    name=f'{col}分布分析',
                    dim_type='univariate',
                    source='ai',
                    priority=2,
                    columns=[col],
                    method='频次统计',
                    reason='基础单变量分析'
                ))
        
        # 双变量分析
        if len(numeric_cols) >= 2:
            dimensions.append(AnalysisDimension(
                name=f'{numeric_cols[0]}与{numeric_cols[1]}相关性',
                dim_type='bivariate',
                source='ai',
                priority=2,
                columns=numeric_cols[:2],
                method='相关性分析',
                reason='基础双变量分析'
            ))
        elif len(categorical_cols) >= 2:
            # 如果没有数值列，使用类别列做交叉分析
            dimensions.append(AnalysisDimension(
                name=f'{categorical_cols[0]}与{categorical_cols[1]}交叉分析',
                dim_type='bivariate',
                source='ai',
                priority=2,
                columns=categorical_cols[:2],
                method='交叉表分析',
                reason='基础双变量分析'
            ))
        
        # 多变量分析
        if len(numeric_cols) >= 3:
            dimensions.append(AnalysisDimension(
                name='多变量关系分析',
                dim_type='multivariate',
                source='ai',
                priority=2,
                columns=numeric_cols[:3],
                method='主成分分析',
                reason='基础多变量分析'
            ))
        elif len(all_cols) >= 3:
            # 使用任意类型的列做多变量分析
            dimensions.append(AnalysisDimension(
                name='多变量关系分析',
                dim_type='multivariate',
                source='ai',
                priority=2,
                columns=all_cols[:3],
                method='综合分析',
                reason='基础多变量分析'
            ))
        
        # 如果仍然没有维度，至少创建一个通用维度
        if not dimensions and all_cols:
            dimensions.append(AnalysisDimension(
                name='数据概览分析',
                dim_type='univariate',
                source='ai',
                priority=2,
                columns=all_cols[:5],
                method='描述统计',
                reason='基础数据分析'
            ))
        
        self._log(f"生成默认维度: {len(dimensions)} 个")
        return dimensions
    
    def merge_dimensions(self,
                        template_dims: Optional[List[str]],
                        ai_dims: List[AnalysisDimension],
                        user_dims: Optional[List[str]]) -> List[AnalysisDimension]:
        """
        融合三级维度，按优先级去重
        
        优先级：template (1) > ai (2) > user (3)
        
        Args:
            template_dims: 模板维度名称列表
            ai_dims: AI推荐的维度对象列表
            user_dims: 用户手动输入的维度名称列表
        
        Returns:
            融合后的维度列表
        """
        self._log("融合分析维度")
        
        merged = []
        seen_names = set()
        
        # 1. 添加模板维度（最高优先级）
        if template_dims:
            for name in template_dims:
                if name not in seen_names:
                    merged.append(AnalysisDimension(
                        name=name,
                        dim_type='other',
                        source='template',
                        priority=1
                    ))
                    seen_names.add(name)
        
        # 2. 添加AI维度（中等优先级）
        for dim in ai_dims:
            if dim.name not in seen_names:
                merged.append(dim)
                seen_names.add(dim.name)
        
        # 3. 添加用户维度（最低优先级）
        if user_dims:
            for name in user_dims:
                if name not in seen_names:
                    merged.append(AnalysisDimension(
                        name=name,
                        dim_type='other',
                        source='user',
                        priority=3
                    ))
                    seen_names.add(name)
        
        self._log(f"融合完成，共{len(merged)}个维度")
        return merged
    
    def _process_dimensions(self,
                           df: pd.DataFrame,
                           template_dimensions: Optional[List[str]],
                           user_dimensions: Optional[List[str]]) -> List[AnalysisDimension]:
        """处理分析维度"""
        # AI推荐维度
        ai_dims = self.recommend_dimensions(df, template_dimensions)
        
        # 融合所有维度
        merged = self.merge_dimensions(
            template_dimensions,
            ai_dims,
            user_dimensions
        )
        
        return merged
    
    def _data_understanding_and_preprocessing(self, 
                                             df: pd.DataFrame) -> Dict:
        """
        步骤1: 数据理解与预处理
        
        Args:
            df: 输入数据
        
        Returns:
            预处理结果
        """
        # 准备提示词参数
        data_sample = df.head(20).to_string()
        total_rows = len(df)
        total_cols = len(df.columns)
        columns = list(df.columns)
        
        prompt = DATA_UNDERSTANDING_PROMPT.format(
            data_sample=data_sample,
            total_rows=total_rows,
            total_cols=total_cols,
            columns=json.dumps(columns, ensure_ascii=False)
        )
        
        try:
            result = self.llm.analyze_json(prompt)
            return result
        except Exception as e:
            self._log(f"数据理解失败: {str(e)}")
            # 返回基础信息
            return {
                'structure_understanding': {
                    'columns': [{'name': col, 'data_type': str(df[col].dtype)} for col in df.columns]
                },
                'quality_assessment': {
                    'missing_values': {col: {'count': int(df[col].isnull().sum()), 
                                            'percentage': float(df[col].isnull().sum() / len(df) * 100)} 
                                     for col in df.columns},
                    'outliers': {},
                    'duplicates': {'count': int(df.duplicated().sum())},
                    'consistency_issues': []
                },
                'cleaning_recommendations': [],
                'processing_log': ['基础数据理解完成']
            }
    
    def _exploratory_data_analysis(self,
                                  df: pd.DataFrame,
                                  preprocessing: Dict,
                                  dimensions: List[AnalysisDimension]) -> Dict:
        """
        步骤2: 探索性数据分析
        必须包含单变量、双变量、多变量分析
        
        Args:
            df: 输入数据
            preprocessing: 预处理结果
            dimensions: 融合后的分析维度
        
        Returns:
            EDA结果
        """
        # 准备统计摘要
        try:
            statistical_summary = df.describe().to_string()
        except:
            statistical_summary = "统计摘要生成失败"
        
        # 准备维度信息
        dims_info = []
        for dim in dimensions:
            dims_info.append({
                'name': dim.name,
                'type': dim.dim_type,
                'columns': dim.columns,
                'method': dim.method,
                'source': dim.source
            })
        
        prompt = EDA_PROMPT.format(
            preprocessing_result=json.dumps(preprocessing, ensure_ascii=False, default=str)[:2000],
            statistical_summary=statistical_summary,
            dimensions_info=json.dumps(dims_info, ensure_ascii=False)
        )
        
        try:
            result = self.llm.analyze_json(prompt)
            
            # 确保包含三类分析
            if 'univariate_analysis' not in result:
                result['univariate_analysis'] = self._compute_univariate_analysis(df)
            if 'bivariate_analysis' not in result:
                result['bivariate_analysis'] = self._compute_bivariate_analysis(df)
            if 'multivariate_analysis' not in result:
                result['multivariate_analysis'] = self._compute_multivariate_analysis(df)
            
            return result
            
        except Exception as e:
            self._log(f"EDA失败: {str(e)}")
            # 返回基础EDA结果
            return {
                'univariate_analysis': self._compute_univariate_analysis(df),
                'bivariate_analysis': self._compute_bivariate_analysis(df),
                'multivariate_analysis': self._compute_multivariate_analysis(df)
            }
    
    def _compute_univariate_analysis(self, df: pd.DataFrame) -> Dict:
        """计算单变量分析"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        result = {}
        
        for col in numeric_cols[:5]:  # 限制列数
            result[col] = {
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'q25': float(df[col].quantile(0.25)),
                'q75': float(df[col].quantile(0.75)),
                'skewness': float(df[col].skew()),
                'kurtosis': float(df[col].kurtosis())
            }
        
        return result
    
    def _compute_bivariate_analysis(self, df: pd.DataFrame) -> Dict:
        """计算双变量分析"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            return {'message': '数值列不足，无法进行双变量分析'}
        
        corr_matrix = numeric_df.corr().to_dict()
        
        return {
            'correlation_matrix': corr_matrix,
            'strong_correlations': self._find_strong_correlations(numeric_df)
        }
    
    def _find_strong_correlations(self, df: pd.DataFrame, threshold: float = 0.7) -> List[Dict]:
        """查找强相关关系"""
        corr_matrix = df.corr()
        strong_corrs = []
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) >= threshold:
                    strong_corrs.append({
                        'column1': corr_matrix.columns[i],
                        'column2': corr_matrix.columns[j],
                        'correlation': float(corr_val)
                    })
        
        return strong_corrs
    
    def _compute_multivariate_analysis(self, df: pd.DataFrame) -> Dict:
        """计算多变量分析"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 3:
            return {'message': '数值列不足，无法进行多变量分析'}
        
        # 简化的多变量分析
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA
        
        try:
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(numeric_df.dropna())
            
            n_components = min(3, len(numeric_df.columns))
            pca = PCA(n_components=n_components)
            pca_result = pca.fit_transform(scaled_data)
            
            return {
                'pca': {
                    'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                    'n_components': n_components
                },
                'recommendations': ['考虑使用PCA降维', '检查变量间多重共线性']
            }
        except Exception as e:
            return {'message': f'多变量分析失败: {str(e)}'}
    
    def _deep_analysis_and_insights(self,
                                   df: pd.DataFrame,
                                   eda: Dict,
                                   dimensions: List[AnalysisDimension],
                                   context: str) -> List[Dict]:
        """
        步骤3: 深度分析与洞察
        
        Args:
            df: 输入数据
            eda: EDA结果
            dimensions: 融合后的分析维度
            context: 业务背景
        
        Returns:
            洞察列表
        """
        # 准备维度信息
        dims_info = [{'name': d.name, 'type': d.dim_type, 'source': d.source} for d in dimensions]
        
        prompt = DEEP_ANALYSIS_PROMPT.format(
            context=context or "通用数据分析",
            eda_result=json.dumps(eda, ensure_ascii=False, default=str)[:2000],
            merged_dimensions=json.dumps(dims_info, ensure_ascii=False)
        )
        
        try:
            result = self.llm.analyze_json(prompt)
            insights = result.get('insights', [])
            
            # 确保有洞察
            if not insights:
                insights = self._generate_default_insights(eda, dimensions)
            
            return insights
            
        except Exception as e:
            self._log(f"深度分析失败: {str(e)}")
            return self._generate_default_insights(eda, dimensions)
    
    def _generate_default_insights(self, 
                                  eda: Dict, 
                                  dimensions: List[AnalysisDimension]) -> List[Dict]:
        """生成默认洞察"""
        insights = []
        
        # 从单变量分析生成洞察
        univariate = eda.get('univariate_analysis', {})
        for col, stats in list(univariate.items())[:2]:
            insights.append({
                'title': f'{col}分布特征',
                'description': f'{col}的均值为{stats.get("mean", "N/A"):.2f}，标准差为{stats.get("std", "N/A"):.2f}',
                'key_findings': ['数据分布正常' if abs(stats.get('skewness', 0)) < 1 else '数据分布偏斜'],
                'data_evidence': [f'均值: {stats.get("mean", "N/A"):.2f}', f'标准差: {stats.get("std", "N/A"):.2f}'],
                'action': '继续监控该指标',
                'confidence': '中',
                'priority': '中',
                'dimension_source': 'ai'
            })
        
        # 从双变量分析生成洞察
        bivariate = eda.get('bivariate_analysis', {})
        strong_corrs = bivariate.get('strong_correlations', [])
        if strong_corrs:
            corr = strong_corrs[0]
            insights.append({
                'title': f'{corr["column1"]}与{corr["column2"]}强相关',
                'description': f'两个变量存在强相关关系（r={corr["correlation"]:.2f}）',
                'key_findings': ['存在强相关关系'],
                'data_evidence': [f'相关系数: {corr["correlation"]:.2f}'],
                'action': '深入分析因果关系',
                'confidence': '高',
                'priority': '高',
                'dimension_source': 'ai'
            })
        
        return insights
    
    def _generate_visualization_recommendations(self,
                                               df: pd.DataFrame,
                                               eda: Dict,
                                               insights: List[Dict],
                                               dimensions: List[AnalysisDimension]) -> List[Dict]:
        """
        生成可视化建议
        
        Args:
            df: 输入数据
            eda: EDA结果
            insights: 洞察列表
            dimensions: 分析维度
        
        Returns:
            可视化建议列表
        """
        recommendations = []
        
        # 为每个洞察生成可视化建议
        for i, insight in enumerate(insights[:5]):  # 限制数量
            # 根据洞察内容推断图表类型
            chart_type = self._infer_chart_type(insight, df)
            
            recommendations.append({
                'insight_index': i,
                'insight_title': insight.get('title', f'洞察{i+1}'),
                'chart_type': chart_type,
                'reason': f'适合展示{insight.get("title", "该洞察")}',
                'columns': self._infer_columns(insight, df),
                'title': insight.get('title', ''),
                'key_elements': ['数据点', '趋势线']
            })
        
        return recommendations
    
    def _infer_chart_type(self, insight: Dict, df: pd.DataFrame) -> str:
        """推断图表类型"""
        title = insight.get('title', '').lower()
        
        if '相关' in title or '关系' in title:
            return 'scatter'
        elif '趋势' in title or '时间' in title:
            return 'line'
        elif '分布' in title or '占比' in title:
            return 'histogram'
        elif '对比' in title:
            return 'bar'
        else:
            # 默认根据数据类型
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                return 'scatter'
            else:
                return 'bar'
    
    def _infer_columns(self, insight: Dict, df: pd.DataFrame) -> List[str]:
        """推断涉及的列"""
        title = insight.get('title', '')
        description = insight.get('description', '')
        
        # 从标题和描述中提取列名
        mentioned_cols = []
        for col in df.columns:
            if col in title or col in description:
                mentioned_cols.append(col)
        
        # 如果没有找到，使用数值列
        if not mentioned_cols:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            mentioned_cols = list(numeric_cols[:2])
        
        return mentioned_cols
