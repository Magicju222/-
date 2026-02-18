"""
Agent 驱动的数据分析模块
使用 Kimi K2.5 的 Tool Use 能力实现自主数据分析
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from openai import OpenAI
import traceback


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None


@dataclass
class AgentStep:
    """Agent 执行步骤"""
    step_number: int
    thought: str
    action: str
    action_input: Dict
    observation: str
    tool_result: Optional[ToolResult] = None


@dataclass
class AgentAnalysisResult:
    """Agent 分析结果"""
    original_data: pd.DataFrame
    steps: List[AgentStep] = field(default_factory=list)
    final_report: str = ""
    generated_code: List[str] = field(default_factory=list)
    visualizations: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


class DataAnalysisTools:
    """数据分析工具集"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.execution_namespace = {
            'pd': pd,
            'np': np,
            'df': df,
            'plt': None,  # 懒加载 matplotlib
        }
    
    def get_data_info(self) -> str:
        """获取数据基本信息"""
        info = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': self.df.dtypes.to_dict(),
            'missing': self.df.isnull().sum().to_dict(),
            'memory_usage': self.df.memory_usage(deep=True).sum()
        }
        return json.dumps(info, indent=2, default=str)
    
    def execute_python(self, code: str) -> ToolResult:
        """执行 Python 代码"""
        try:
            # 捕获输出
            import io
            import sys
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # 执行代码
            exec(code, self.execution_namespace)
            
            # 恢复输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            if error:
                return ToolResult(success=False, result=output, error=error)
            
            return ToolResult(success=True, result=output)
            
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))
    
    def query_data(self, query_description: str) -> ToolResult:
        """根据描述查询数据"""
        try:
            # 这里可以实现自然语言到 pandas 查询的转换
            # 简化版本：返回数据的基本统计
            result = {
                'head': self.df.head(10).to_dict(),
                'describe': self.df.describe().to_dict(),
                'info': f"数据形状: {self.df.shape}, 列: {list(self.df.columns)}"
            }
            return ToolResult(success=True, result=json.dumps(result, indent=2, default=str))
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))
    
    def generate_visualization(self, viz_config: Dict) -> ToolResult:
        """生成可视化图表"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            self.execution_namespace['plt'] = plt
            self.execution_namespace['sns'] = sns
            
            chart_type = viz_config.get('chart_type', 'bar')
            columns = viz_config.get('columns', [])
            title = viz_config.get('title', 'Chart')
            
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'histogram' and columns:
                self.df[columns[0]].hist(bins=20)
                plt.xlabel(columns[0])
                plt.ylabel('Frequency')
            elif chart_type == 'bar' and columns:
                self.df[columns[0]].value_counts().plot(kind='bar')
                plt.xlabel(columns[0])
                plt.ylabel('Count')
            elif chart_type == 'scatter' and len(columns) >= 2:
                plt.scatter(self.df[columns[0]], self.df[columns[1]])
                plt.xlabel(columns[0])
                plt.ylabel(columns[1])
            elif chart_type == 'correlation':
                numeric_df = self.df.select_dtypes(include=[np.number])
                sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
            
            plt.title(title)
            plt.tight_layout()
            
            # 保存图表
            import tempfile
            chart_path = tempfile.mktemp(suffix='.png')
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return ToolResult(success=True, result=chart_path)
            
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))
    
    def statistical_analysis(self, analysis_type: str, columns: List[str]) -> ToolResult:
        """执行统计分析"""
        try:
            if analysis_type == 'describe':
                result = self.df[columns].describe().to_dict()
            elif analysis_type == 'correlation':
                result = self.df[columns].corr().to_dict()
            elif analysis_type == 'value_counts':
                result = {col: self.df[col].value_counts().to_dict() for col in columns}
            else:
                result = {'error': f'Unknown analysis type: {analysis_type}'}
            
            return ToolResult(success=True, result=json.dumps(result, indent=2, default=str))
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))


class AgentAnalyzer:
    """Agent 驱动的数据分析器"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv('LLM_API_KEY')
        # 从环境变量读取模型配置，默认为 moonshot-v1-8k（K2.5 的 Tool Use 有兼容性问题）
        self.model = model or os.getenv('LLM_MODEL', 'moonshot-v1-8k')
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.cn/v1"
        )
        self.tools = self._define_tools()
        print(f"🤖 AgentAnalyzer 初始化完成，使用模型: {self.model}")
        
    def _define_tools(self) -> List[Dict]:
        """定义可用的工具"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_data_info",
                    "description": "获取数据集的基本信息，包括形状、列名、数据类型、缺失值等",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": "执行 Python 代码进行数据分析，可以使用 pandas、numpy 等库",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "要执行的 Python 代码"
                            }
                        },
                        "required": ["code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_data",
                    "description": "根据自然语言描述查询数据，返回数据的统计信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_description": {
                                "type": "string",
                                "description": "数据查询的描述"
                            }
                        },
                        "required": ["query_description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_visualization",
                    "description": "生成数据可视化图表",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "viz_config": {
                                "type": "object",
                                "properties": {
                                    "chart_type": {"type": "string", "enum": ["histogram", "bar", "scatter", "correlation", "line"]},
                                    "columns": {"type": "array", "items": {"type": "string"}},
                                    "title": {"type": "string"}
                                },
                                "required": ["chart_type", "columns"]
                            }
                        },
                        "required": ["viz_config"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "statistical_analysis",
                    "description": "执行统计分析，如描述统计、相关性分析等",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "analysis_type": {"type": "string", "enum": ["describe", "correlation", "value_counts"]},
                            "columns": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["analysis_type", "columns"]
                    }
                }
            }
        ]
    
    def analyze(self, df: pd.DataFrame, context: str = "", step_callback: callable = None) -> AgentAnalysisResult:
        """
        执行 Agent 驱动的数据分析
        
        Args:
            df: 要分析的数据框
            context: 分析背景信息
        
        Returns:
            AgentAnalysisResult: 分析结果
        """
        result = AgentAnalysisResult(original_data=df)
        tools_executor = DataAnalysisTools(df)
        
        # 系统提示词
        system_prompt = """你是一个专业的数据分析师，擅长使用 Python 进行数据分析和可视化。

你的任务是按照以下步骤完成数据分析：

1. **数据理解与预处理**
   - 使用 get_data_info 了解数据结构
   - 识别数据质量问题（缺失值、异常值）
   - 必要时使用 execute_python 进行数据清洗

2. **探索性数据分析**
   - 使用 statistical_analysis 进行描述统计
   - 使用 generate_visualization 创建可视化
   - 识别数据分布、趋势和异常

3. **深度分析与洞察**
   - 使用 execute_python 进行复杂分析
   - 发现数据中的模式和关联
   - 提取有价值的业务洞察

4. **报告生成**
   - 总结关键发现
   - 提供可操作的建议

请逐步思考，每次选择一个合适的工具来完成当前步骤。如果工具返回错误，请分析原因并尝试其他方法。
"""
        
        # 构建初始消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下数据集。\n\n分析背景：{context}\n\n数据形状：{df.shape}\n列名：{list(df.columns)}\n\n请开始数据理解步骤。"}
        ]
        
        max_steps = 10
        step_number = 0
        
        while step_number < max_steps:
            step_number += 1
            
            try:
                # 调用模型
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=1,  # Kimi K2.5 只支持 temperature=1
                    max_tokens=2000
                )
                
                message = response.choices[0].message
                
                # 检查是否有工具调用
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # 记录步骤
                        step = AgentStep(
                            step_number=step_number,
                            thought=message.content or "执行工具调用",
                            action=function_name,
                            action_input=function_args,
                            observation=""
                        )
                        
                        # 执行工具
                        if function_name == "get_data_info":
                            tool_result = ToolResult(success=True, result=tools_executor.get_data_info())
                        elif function_name == "execute_python":
                            tool_result = tools_executor.execute_python(function_args.get("code", ""))
                            if tool_result.success:
                                result.generated_code.append(function_args.get("code", ""))
                        elif function_name == "query_data":
                            tool_result = tools_executor.query_data(function_args.get("query_description", ""))
                        elif function_name == "generate_visualization":
                            tool_result = tools_executor.generate_visualization(function_args.get("viz_config", {}))
                            if tool_result.success:
                                result.visualizations.append(tool_result.result)
                        elif function_name == "statistical_analysis":
                            tool_result = tools_executor.statistical_analysis(
                                function_args.get("analysis_type", ""),
                                function_args.get("columns", [])
                            )
                        else:
                            tool_result = ToolResult(success=False, result=None, error=f"Unknown function: {function_name}")
                        
                        step.tool_result = tool_result
                        step.observation = str(tool_result.result) if tool_result.success else str(tool_result.error)
                        result.steps.append(step)
                        
                        # 实时回调通知
                        if step_callback:
                            try:
                                step_callback(step)
                            except Exception as cb_error:
                                print(f"⚠️ 回调函数出错: {cb_error}")
                        
                        # 添加工具结果到消息历史
                        try:
                            # 构建 assistant 消息（包含 tool_calls）
                            assistant_message = {
                                "role": "assistant",
                                "content": message.content or "",
                            }
                            
                            # 添加 tool_calls
                            assistant_message["tool_calls"] = [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": function_name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            ]
                            
                            # 对于 Kimi K2.5，需要添加 reasoning_content 字段
                            if 'k2.5' in self.model or 'k2-' in self.model:
                                assistant_message["reasoning_content"] = message.content or "分析数据并决定使用工具"
                            
                            messages.append(assistant_message)
                            
                            # 添加 tool 消息（工具执行结果）
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({"result": step.observation}) if tool_result.success else json.dumps({"error": step.observation})
                            }
                            messages.append(tool_message)
                            
                        except Exception as msg_error:
                            print(f"⚠️  添加消息历史时出错: {msg_error}")
                            # 简化处理：只添加基本消息
                            messages.append({
                                "role": "assistant",
                                "content": f"使用了 {function_name} 工具"
                            })
                
                else:
                    # 模型返回最终回复
                    step = AgentStep(
                        step_number=step_number,
                        thought=message.content,
                        action="final_response",
                        action_input={},
                        observation=message.content
                    )
                    result.steps.append(step)
                    result.final_report = message.content
                    
                    # 提取洞察
                    if "洞察" in message.content or "发现" in message.content:
                        result.insights.append(message.content)
                    
                    break
                    
            except Exception as e:
                import traceback
                error_detail = f"{str(e)}\n{traceback.format_exc()}"
                print(f"❌ 步骤 {step_number} 执行出错:\n{error_detail}")
                
                error_step = AgentStep(
                    step_number=step_number,
                    thought="执行出错",
                    action="error",
                    action_input={},
                    observation=str(e)
                )
                result.steps.append(error_step)
                break
        
        # 如果循环结束但没有最终报告，强制生成一份
        if not result.final_report:
            print("📝 生成最终分析报告...")
            try:
                # 构建总结消息
                summary_messages = [
                    {"role": "system", "content": "你是一个数据分析专家。请根据前面的分析步骤，生成一份完整的分析报告。"},
                    {"role": "user", "content": f"请基于以下分析步骤生成一份完整的销售数据分析报告，包括：\n\n1. 数据概览\n2. 关键发现\n3. 业务洞察\n4. 建议\n\n分析步骤:\n" + "\n".join([f"步骤 {s.step_number}: {s.action} - {s.observation[:100]}..." for s in result.steps[:5]])}
                ]
                
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=summary_messages,
                    temperature=1,
                    max_tokens=2000
                )
                
                result.final_report = final_response.choices[0].message.content
                
                # 添加最终步骤
                final_step = AgentStep(
                    step_number=step_number + 1,
                    thought="生成最终报告",
                    action="generate_report",
                    action_input={},
                    observation="报告已生成"
                )
                result.steps.append(final_step)
                
            except Exception as report_error:
                print(f"⚠️ 生成最终报告失败: {report_error}")
                # 使用步骤摘要作为报告
                result.final_report = "# 数据分析报告\n\n" + "\n".join([f"## 步骤 {s.step_number}: {s.action}\n{s.observation[:200]}..." for s in result.steps])
        
        return result
