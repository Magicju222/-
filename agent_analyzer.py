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
        
        # 系统提示词 - 聚焦业务洞察
        system_prompt = f"""你是一位资深业务数据分析师，专注于从数据中发现业务价值和洞察。

## 你的分析原则

1. **深入理解业务含义**
   - 每个字段都代表什么业务概念？
   - 数据之间的关系反映了什么业务逻辑？
   - 异常数据可能暗示什么业务问题？

2. **关注数据背后的故事**
   - 不要只报告统计数字，要解释数字的含义
   - 发现数据中的模式、趋势和异常
   - 关联不同字段，发现隐藏的业务洞察

3. **提供 actionable insights**
   - 分析结果要能指导业务决策
   - 指出数据反映的业务机会或风险
   - 给出具体的改进建议

## 分析流程

**第一步：深度理解数据字段**
- 分析每个字段的业务含义和数据类型
- 识别关键业务指标（KPIs）
- 理解字段间的业务关系

**第二步：多维度业务分析**
- 数据分布：哪些情况最常见？什么很少见？
- 关键指标：核心业务的度量是什么？
- 关联分析：不同维度如何相互影响？
- 异常识别：哪些数据点值得关注？为什么？

**第三步：业务洞察提取**
- 数据反映了什么业务现状？
- 存在什么业务机会或问题？
- 不同维度对比揭示了什么？

**第四步：生成业务报告**
- 用业务语言描述发现，避免技术术语
- 突出最重要的3-5个洞察
- 提供具体的业务建议

## 工具使用指南

- `get_data_info`: 获取数据基本信息，但**不要**只报告行数列数，要思考这些数字的业务含义
- `execute_python`: 执行深度分析，关注数据分布、相关性、异常值等业务指标
- `generate_visualization`: 创建能说明业务问题的图表
- `statistical_analysis`: 进行统计分析，但**重点解释统计结果的业务意义**

## 重要提醒

❌ 不要做的：
- 只报告"数据有100行5列"这类无意义信息
- 罗列所有统计数字而不解释含义
- 使用复杂的技术术语
- **不要尝试读取外部文件**（如 pd.read_excel('data.xlsx')），数据已通过 `df` 变量提供
- **不要保存文件到本地**，只需分析内存中的数据

✅ 应该做的：
- 解释"为什么这个数据分布很重要"
- 指出"这个异常值可能意味着什么业务问题"
- 用业务语言说明"这个相关性揭示了什么机会"
- 给出"基于数据，建议采取什么行动"
- **所有分析都基于提供的 `df` 数据框**，直接使用 `df` 变量

请开始你的深度业务分析。
"""
        
        # 构建初始消息 - 强调业务分析
        # 生成字段描述
        field_descriptions = []
        for col in df.columns:
            dtype = df[col].dtype
            sample_values = df[col].dropna().head(3).tolist()
            unique_count = df[col].nunique()
            field_descriptions.append(f"- {col}: {dtype}, 示例值: {sample_values}, 唯一值: {unique_count}")
        
        initial_message = f"""请对以下数据进行深度业务分析。

## 业务背景
{context if context else "这是一份业务数据，需要从中提取有价值的业务洞察。"}

## 数据概览
**数据表包含以下字段：**
{chr(10).join(field_descriptions)}

## 分析要求

请按以下步骤进行深度分析：

1. **字段业务含义解读**
   - 每个字段代表什么业务概念？
   - 识别关键业务指标
   - 字段间可能存在什么业务关系？

2. **业务维度分析**
   - 使用 execute_python 深入分析数据分布
   - 计算关键业务指标（如平均值、占比、增长率等）
   - 识别异常值并分析其业务含义
   - 发现数据间的关联性和模式

3. **业务洞察提取**
   - 数据反映了什么业务现状？
   - 有哪些值得关注的业务现象？
   - 存在什么业务机会或风险？

4. **生成业务报告**
   - 用业务语言总结关键发现
   - 提供3-5个核心洞察
   - 给出具体的业务行动建议

请开始分析，重点关注数据背后的业务含义，而非技术实现细节。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_message}
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
        
        # 如果循环结束但没有最终报告，强制生成一份业务导向的报告
        if not result.final_report:
            print("📝 生成业务分析报告...")
            try:
                # 构建业务总结消息
                business_summary_prompt = f"""你是一位资深业务顾问。请基于以下数据分析过程，生成一份聚焦业务洞察的分析报告。

## 报告要求

**请用业务语言（而非技术术语）撰写报告，包括：**

1. **业务背景与数据理解** (2-3句话)
   - 这份数据反映什么业务场景？
   - 关键业务指标有哪些？

2. **核心业务洞察** (3-5个要点)
   - 数据揭示了哪些重要业务现象？
   - 有哪些异常或值得关注的模式？
   - 不同维度间的关联说明了什么？

3. **业务机会与风险**
   - 存在什么业务机会？
   - 需要注意什么潜在风险？

4. **行动建议** (具体可执行的建议)
   - 基于数据，应该采取什么行动？
   - 优先级排序

## 分析过程摘要
""" + "\n".join([f"- 步骤 {s.step_number} ({s.action}): {s.observation[:150]}..." for s in result.steps if s.action not in ['error', 'final_response']][:8])
                
                summary_messages = [
                    {"role": "system", "content": "你是一位资深业务顾问，擅长从数据中发现业务价值并提供 actionable insights。请用业务语言撰写报告，避免技术术语。"},
                    {"role": "user", "content": business_summary_prompt}
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
