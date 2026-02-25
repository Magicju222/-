"""
Agent 驱动的数据分析模块
使用 Kimi K2.5 的 Tool Use 能力实现自主数据分析
"""

import os
import json
import pandas as pd
import numpy as np
import ast
import sys
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from openai import OpenAI
import traceback
from data_integrity_checker import DataIntegrityChecker, validate_dataframe_integrity


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None


class SecureCodeExecutor:
    """
    安全的代码执行器
    使用 AST 检查限制可执行的代码，防止安全风险
    """
    
    # 允许使用的模块
    ALLOWED_MODULES: Set[str] = {
        'pandas', 'pd',
        'numpy', 'np',
        'math', 'statistics', 'random', 'datetime',
        'json', 're', 'collections', 'itertools'
    }
    
    # 禁止使用的内置函数
    FORBIDDEN_BUILTINS: Set[str] = {
        'eval', 'exec', 'compile', '__import__', 'open',
        'input', 'raw_input', 'help', 'quit', 'exit',
        'reload', 'breakpoint', 'getattr', 'setattr',
        'delattr', 'globals', 'locals', 'vars', 'dir'
    }
    
    # 禁止的 AST 节点类型
    FORBIDDEN_AST_NODES: Set[type] = {
        ast.Delete,      # 禁止删除操作
        ast.With,        # 禁止上下文管理器
        ast.Try,         # 禁止异常处理（简化）
        ast.ExceptHandler,
        ast.Raise,       # 禁止抛出异常
        ast.Assert,      # 禁止断言
        ast.ClassDef,    # 禁止定义类
        # ast.FunctionDef, # 允许定义简单函数（AI分析时常用）
        ast.AsyncFunctionDef,
        # ast.Lambda,      # 允许lambda（数据分析中常用）
        ast.Yield,       # 禁止生成器
        ast.YieldFrom,
    }
    
    # 允许导入的模块（白名单）
    ALLOWED_IMPORTS: Set[str] = {
        'pandas', 'pd', 'numpy', 'np', 'math', 'statistics', 
        'datetime', 'json', 're', 'collections', 'itertools',
        'matplotlib', 'matplotlib.pyplot', 'plt', 'seaborn', 'sns',
        'scipy', 'scipy.stats', 'scipy.optimize', 'scipy.linalg',
        'warnings', 'typing', 'types', 'functools', 'decimal'
    }
    
    def __init__(self, dfs: Dict[str, pd.DataFrame]):
        self.dfs = dfs
        self.df = list(dfs.values())[0] if dfs else pd.DataFrame()
        self.execution_namespace = self._create_safe_namespace()
    
    def _create_safe_namespace(self) -> Dict[str, Any]:
        """创建安全的执行环境"""
        # 基础安全命名空间
        safe_namespace = {
            '__builtins__': {},
        }
        
        # 添加允许的内置函数
        allowed_builtins = {
            'len', 'range', 'enumerate', 'zip', 'map', 'filter',
            'sum', 'min', 'max', 'abs', 'round', 'sorted',
            'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
            'type', 'isinstance', 'hasattr', 'print', '__import__',
            'any', 'all', 'next', 'iter', 'reversed'
        }
        
        for name in allowed_builtins:
            if name in __builtins__:
                safe_namespace['__builtins__'][name] = __builtins__[name]
        
        # 添加允许的模块
        safe_namespace['pd'] = pd
        safe_namespace['np'] = np
        safe_namespace['df'] = self.df
        safe_namespace['dfs'] = self.dfs
        
        # 将所有DataFrame添加到命名空间（使用原始变量名）
        for name, df in self.dfs.items():
            safe_namespace[name] = df
        
        # 添加数学函数
        import math
        import statistics
        safe_namespace['math'] = math
        safe_namespace['statistics'] = statistics
        
        # 添加可视化库（如果已安装）
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            safe_namespace['matplotlib'] = matplotlib
            safe_namespace['plt'] = plt
        except ImportError:
            pass
        
        try:
            import seaborn as sns
            safe_namespace['seaborn'] = sns
            safe_namespace['sns'] = sns
        except ImportError:
            pass
        
        # 添加列名查找辅助函数
        safe_namespace['find_column'] = self._find_column
        safe_namespace['get_columns'] = self._get_columns
        
        return safe_namespace
    
    def _find_column(self, df: pd.DataFrame, partial_name: str) -> str:
        """
        根据部分列名查找完整列名
        
        Args:
            df: DataFrame
            partial_name: 部分列名（如 '车均收入'）
            
        Returns:
            匹配的完整列名，如果没有找到则返回原始输入
        """
        if partial_name in df.columns:
            return partial_name
        
        # 尝试部分匹配
        matches = [col for col in df.columns if partial_name in col]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # 如果有多个匹配，返回最精确的那个（长度最短的）
            return min(matches, key=len)
        
        # 如果没有找到，返回原始输入（让调用者处理错误）
        return partial_name
    
    def _get_columns(self, df: pd.DataFrame) -> list:
        """
        获取DataFrame的所有列名
        
        Args:
            df: DataFrame
            
        Returns:
            列名列表
        """
        return list(df.columns)
    
    def validate_code(self, code: str) -> tuple[bool, str]:
        """
        验证代码是否安全
        返回: (是否安全, 错误信息)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        
        for node in ast.walk(tree):
            # 检查禁止的 AST 节点
            if type(node) in self.FORBIDDEN_AST_NODES:
                return False, f"代码包含不允许的操作: {type(node).__name__}"
            
            # 检查 Import 语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.ALLOWED_IMPORTS:
                        return False, f"禁止导入模块: {alias.name}"
            
            # 检查 ImportFrom 语句
            if isinstance(node, ast.ImportFrom):
                if node.module not in self.ALLOWED_IMPORTS:
                    return False, f"禁止从模块导入: {node.module}"
            
            # 检查函数调用
            if isinstance(node, ast.Call):
                # 检查是否调用了禁止的内置函数
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_BUILTINS:
                        return False, f"禁止使用函数: {node.func.id}"
                
                # 检查属性访问（如 os.system）
                if isinstance(node.func, ast.Attribute):
                    # 检查是否访问了禁止的模块
                    if isinstance(node.func.value, ast.Name):
                        # 允许 DataFrame 变量名（可能是 df、dfs 或其他 DataFrame 变量）
                        # 只禁止已知的危险模块
                        forbidden_modules = {'os', 'sys', 'subprocess', 'socket', 
                                            'urllib', 'http', 'ftplib', 'smtplib',
                                            'pickle', 'marshal', 'ctypes', 'io'}
                        if node.func.value.id in forbidden_modules:
                            return False, f"禁止访问模块: {node.func.value.id}.{node.func.attr}"
            
            # 检查名称引用
            if isinstance(node, ast.Name):
                if node.id in self.FORBIDDEN_BUILTINS:
                    return False, f"禁止使用: {node.id}"
        
        return True, ""
    
    def execute(self, code: str) -> ToolResult:
        """
        安全地执行代码
        """
        # 首先验证代码
        is_safe, error_msg = self.validate_code(code)
        if not is_safe:
            return ToolResult(success=False, result=None, error=f"代码安全检查失败: {error_msg}")
        
        try:
            # 捕获输出
            import io
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # 编译并执行代码
            compiled_code = compile(code, '<string>', 'exec')
            exec(compiled_code, self.execution_namespace)
            
            # 恢复输出
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            if error:
                return ToolResult(success=False, result=output, error=error)
            
            return ToolResult(success=True, result=output)
            
        except Exception as e:
            # 确保恢复输出
            sys.stdout = old_stdout if 'old_stdout' in locals() else sys.stdout
            sys.stderr = old_stderr if 'old_stderr' in locals() else sys.stderr
            return ToolResult(success=False, result=None, error=str(e))


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
    multi_table_info: Dict = field(default_factory=dict)
    table_relations: List[Dict] = field(default_factory=list)


class DataAnalysisTools:
    """数据分析工具集"""
    
    def __init__(self, dfs: Dict[str, pd.DataFrame]):
        if isinstance(dfs, pd.DataFrame):
            dfs = {"default": dfs}
        self.dfs = dfs
        self.primary_df = list(dfs.values())[0] if dfs else pd.DataFrame()
        self.df = self.primary_df
        # 初始化安全代码执行器（保持单例，保留执行上下文）
        self._secure_executor = SecureCodeExecutor(dfs)
        # 初始化完整性检查器
        self.integrity_checker = DataIntegrityChecker(dfs)
        # 记录原始数据行数，用于完整性校验
        self.original_row_counts = {name: len(df) for name, df in dfs.items()}
    
    def get_data_info(self) -> str:
        """获取数据基本信息"""
        if len(self.dfs) > 1:
            info = {
                'total_tables': len(self.dfs),
                'tables': {}
            }
            for name, df in self.dfs.items():
                info['tables'][name] = {
                    'shape': df.shape,
                    'columns': list(df.columns),
                    'dtypes': {k: str(v) for k, v in df.dtypes.to_dict().items()},
                    'missing': df.isnull().sum().to_dict(),
                    'sample': df.head(3).to_dict(orient='records') if len(df) > 0 else []
                }
            return json.dumps(info, ensure_ascii=False, indent=2)
        
        info = {
            'shape': self.df.shape,
            'columns': list(self.df.columns),
            'dtypes': {k: str(v) for k, v in self.df.dtypes.to_dict().items()},
            'missing': self.df.isnull().sum().to_dict(),
            'memory_usage': self.df.memory_usage(deep=True).sum()
        }
        return json.dumps(info, indent=2, default=str)
    
    def execute_python(self, code: str) -> ToolResult:
        """执行 Python 代码 - 使用安全沙箱"""
        # 使用已有的 SecureCodeExecutor 实例，保留执行上下文
        return self._secure_executor.execute(code)
    
    def query_data(self, query_description: str) -> ToolResult:
        """根据描述查询数据 - 返回完整数据"""
        try:
            if len(self.dfs) > 1:
                result = {
                    'tables': {},
                    'query': query_description
                }
                for name, df in self.dfs.items():
                    result['tables'][name] = {
                        'head': df.to_dict(),
                        'describe': df.describe().to_dict(),
                        'shape': df.shape
                    }
                return ToolResult(success=True, result=json.dumps(result, indent=2, default=str))
            
            result = {
                'head': self.df.to_dict(),
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
            
            # 尝试导入 seaborn，如果失败则使用 matplotlib 替代
            try:
                import seaborn as sns
                has_seaborn = True
            except ImportError:
                has_seaborn = False
            
            chart_type = viz_config.get('chart_type', 'bar')
            columns = viz_config.get('columns', [])
            title = viz_config.get('title', 'Chart')
            source_table = viz_config.get('table', list(self.dfs.keys())[0] if self.dfs else 'default')
            
            df = self.dfs.get(source_table, self.df)
            
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'histogram' and columns:
                if columns[0] in df.columns:
                    df[columns[0]].hist(bins=20)
                    plt.xlabel(columns[0])
                    plt.ylabel('Frequency')
            elif chart_type == 'bar' and columns:
                if columns[0] in df.columns:
                    df[columns[0]].value_counts().plot(kind='bar')
                    plt.xlabel(columns[0])
                    plt.ylabel('Count')
            elif chart_type == 'scatter' and len(columns) >= 2:
                if columns[0] in df.columns and columns[1] in df.columns:
                    plt.scatter(df[columns[0]], df[columns[1]])
                    plt.xlabel(columns[0])
                    plt.ylabel(columns[1])
            elif chart_type == 'correlation':
                numeric_df = df.select_dtypes(include=[np.number])
                if has_seaborn:
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
                else:
                    # 使用 matplotlib 绘制相关性热力图
                    plt.imshow(numeric_df.corr(), cmap='coolwarm', aspect='auto')
                    plt.colorbar()
                    plt.xticks(range(len(numeric_df.columns)), numeric_df.columns, rotation=45)
                    plt.yticks(range(len(numeric_df.columns)), numeric_df.columns)
            elif chart_type == 'multi_table_compare' and len(self.dfs) > 1:
                fig, axes = plt.subplots(1, len(self.dfs), figsize=(15, 5))
                if len(self.dfs) == 1:
                    axes = [axes]
                for idx, (name, table_df) in enumerate(self.dfs.items()):
                    if columns and columns[0] in table_df.columns:
                        table_df[columns[0]].value_counts().plot(kind='bar', ax=axes[idx])
                        axes[idx].set_title(f'{name}: {columns[0]}')
                        axes[idx].set_xlabel(columns[0])
                        axes[idx].set_ylabel('Count')
                plt.tight_layout()
            
            plt.title(title)
            plt.tight_layout()
            
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
    
    def analyze(self, dfs: Dict[str, pd.DataFrame], context: str = "", step_callback: callable = None) -> AgentAnalysisResult:
        """
        执行 Agent 驱动的数据分析
        
        Args:
            dfs: 要分析的数据框字典，键为工作表名，值为数据框
            context: 分析背景信息
        
        Returns:
            AgentAnalysisResult: 分析结果
        """
        if isinstance(dfs, pd.DataFrame):
            dfs = {"default": dfs}
        
        result = AgentAnalysisResult(original_data=pd.concat(dfs.values(), ignore_index=True) if len(dfs) > 1 else list(dfs.values())[0])
        tools_executor = DataAnalysisTools(dfs)
        
        # 判断是否为多表分析
        is_multi_table = len(dfs) > 1
        table_names = list(dfs.keys())
        
        # 系统提示词 - 聚焦业务洞察
        if is_multi_table:
            system_prompt = f"""你是一位资深业务数据分析师，专注于从多张相关的数据表中发现业务价值和洞察。

## 当前分析模式：多表关联分析

你正在分析 {len(dfs)} 张相互关联的数据表：{table_names}

## 你的分析原则

1. **多表关联分析**
   - 识别不同工作表之间的关联字段和关系
   - 分析表与表之间的数据一致性
   - 发现跨表的业务逻辑

2. **深入理解业务含义**
   - 每个字段都代表什么业务概念？
   - 不同表之间的数据关系反映了什么业务逻辑？
   - 异常数据可能暗示什么业务问题？

3. **关注数据背后的故事**
   - 不要只报告统计数字，要解释数字的含义
   - 发现数据中的模式、趋势和异常
   - 关联不同表，发现隐藏的业务洞察

4. **提供 actionable insights**
   - 分析结果要能指导业务决策
   - 指出数据反映的业务机会或风险
   - 给出具体的改进建议

## 分析流程

**第一步：多表结构理解**
- 识别每张表的业务含义和字段
- 找出表之间的关联字段（如ID、日期、类别等）
- 理解表之间的业务关系（主从关系、关联关系等）

**第二步：全面业务指标分析（必须执行）**
对每个数值型字段，必须分析以下指标：
- **基础统计**: 总和(sum)、平均值(mean)、中位数(median)、标准差(std)
- **极值分析**: 最大值(max)、最小值(min)、极差(range)
- **分布分析**: 四分位数(25%, 75%)、百分位数分布
- **占比分析**: 各分类维度下的占比、累计占比
- **趋势分析**: 如有时间字段，分析时间趋势

**第三步：多维度交叉分析（必须执行）**
- **分类维度分析**: 对每个分类字段，按数值字段汇总排序
- **相关性分析**: 数值字段之间的相关性矩阵
- **分组对比**: 不同分组间的指标对比
- **异常识别**: 识别异常值和异常模式

**第四步：表间关联分析**
- 使用 execute_python 进行跨表分析
- 分析关联字段的数据匹配情况
- 发现表之间的数据一致性/差异

**第五步：生成综合业务报告**
- 用业务语言描述发现，避免技术术语
- 突出表间关联的重要发现
- 提供3-5个核心洞察和具体业务建议
- **必须包含**: 所有分析维度的完整数据表格

## 工具使用指南

- `get_data_info`: 获取所有表的结构和数据概览
- `execute_python`: 执行跨表分析，使用 `dfs` 字典访问各表数据
- `generate_visualization`: 创建跨表对比图表（可指定 table 参数选择数据源）
- `statistical_analysis`: 进行统计分析

## 数据访问方式

在 execute_python 中使用：
- `dfs` 字典访问多表数据，如 `dfs['表名1']`, `dfs['表名2']`
- `df` 访问第一张表的数据
- `get_columns(df)` 获取所有列名
- `find_column(df, '部分列名')` 根据部分列名查找完整列名（重要！）

### 列名查找辅助函数（重要！）

由于列名可能很长（如 `'运营总收入 / 实际 / 车均收入 / 元'`），使用以下辅助函数：

```python
# ✅ 正确：使用 find_column 查找完整列名
col = find_column(df, '车均收入')  # 返回 '运营总收入 / 实际 / 车均收入 / 元'
result = df[col].sum()

# ✅ 正确：先获取所有列名，再查找
columns = get_columns(df)
# 然后使用字符串匹配找到正确的列名

# ❌ 错误：直接使用部分列名（会导致 KeyError）
result = df['车均收入'].sum()  # 会报错：'车均收入' not in index
```

## 数据完整性要求（强制执行）

⚠️ **警告：必须显示完整数据，严禁截断！**

### 显示完整数据的正确方法：
```python
# ✅ 正确：显示完整数据
print(df.to_string())
print(df.to_dict())
print(df.to_json())

# ❌ 错误：截断数据（严禁使用）
print(df.head())  # 禁止！
print(df.head(10))  # 禁止！
print(df[:10])  # 禁止！
```

### 分组统计必须显示所有分组：
```python
# ✅ 正确：显示所有分组
print(df.groupby('字段').sum().to_string())
print(df.groupby('字段').agg(['sum', 'mean']).to_string())

# ❌ 错误：截断分组结果（严禁使用）
print(df.groupby('字段').sum().head())  # 禁止！
```

### 数据完整性检查清单：
- [ ] 使用 `len(df)` 确认总行数
- [ ] 使用 `df.to_string()` 显示完整数据
- [ ] 分组统计后检查分组数量是否完整
- [ ] 确认没有使用任何 `head()` 方法

## 数据清洗要求

⚠️ **重要：分析前必须过滤无效数据**
- 数值型数据：使用 `df[col].dropna()` 过滤空值，再用 `df[col][df[col] != 0]` 过滤零值
- 文本型数据：过滤空字符串 `''` 和 `'0'`
- 示例代码：`valid_data = df[col].dropna()[df[col].dropna() != 0]`
- 所有统计计算都基于过滤后的有效数据

## Pandas 代码规范（重要！）

⚠️ **避免常见 Pandas 错误：**

### 1. groupby 操作
```python
# ✅ 正确：显式设置 observed=False 避免警告
result = df.groupby('分类列', observed=False)['数值列'].sum()

# ✅ 正确：对分类列进行分组时，确保数值列是数值类型
result = df.groupby('分类列', observed=False)['数值列'].agg(['sum', 'mean'])
```

### 2. pd.cut 分箱操作
```python
# ✅ 正确：cut 函数只接受 bins 参数，不接受 observed 参数
bins = pd.cut(df['数值列'], bins=5)

# ❌ 错误：cut 函数不支持 observed 参数
bins = pd.cut(df['数值列'], bins=5, observed=False)  # 会报错！
```

### 3. 数据类型检查
```python
# ✅ 正确：确保数值操作前检查数据类型
if pd.api.types.is_numeric_dtype(df['列名']):
    result = df['列名'].sum()
else:
    # 尝试转换为数值类型
    result = pd.to_numeric(df['列名'], errors='coerce').sum()
```

### 4. 避免除零错误
```python
# ✅ 正确：除法操作前检查分母是否为零
total = df['列名'].sum()
if total != 0:
    ratio = value / total
else:
    ratio = 0  # 或者 None

# ✅ 正确：计算占比时处理空值和零值
valid_data = df['列名'].dropna()
if len(valid_data) > 0 and valid_data.sum() != 0:
    percentage = (value / valid_data.sum()) * 100
else:
    percentage = 0
```

### 5. 处理缺失模块
```python
# ✅ 正确：导入可选模块时处理 ImportError
try:
    import seaborn as sns
    # 使用 seaborn
except ImportError:
    # 使用 matplotlib 替代
    pass
```

### 6. 处理数值计算警告
```python
# ✅ 正确：计算前过滤无效值，避免 RuntimeWarning
import numpy as np
import warnings

# 方法1：使用 dropna() 过滤空值
valid_data = df['数值列'].dropna()
result = valid_data.mean()

# 方法2：使用 fillna() 填充空值
result = df['数值列'].fillna(0).mean()

# 方法3：使用 np.nanmean() 自动忽略 NaN
result = np.nanmean(df['数值列'])

# 方法4：使用 where 过滤无效值
valid_data = df['数值列'].where(df['数值列'].notna() & np.isfinite(df['数值列']))
result = valid_data.mean()
```

### 7. 处理标准差计算中的警告
```python
# ✅ 正确：计算标准差前检查数据有效性
import numpy as np

data = df['数值列'].dropna()
if len(data) > 1 and data.std() != 0:
    std_val = data.std()
else:
    std_val = 0  # 或 np.nan

# 或使用 numpy 的 nanstd
std_val = np.nanstd(df['数值列'])
```

## 重要提醒

❌ **严禁（会导致数据不完整）**：
- 使用 `head()` 截断数据显示
- 使用 `tail()` 截断数据显示
- 使用切片 `[:n]` 截断数据
- 只显示部分分组结果

✅ **必须（确保数据完整性）**：
- 使用 `to_string()` 显示完整数据
- 显示所有分组、所有类别的完整数据
- 使用 `len()` 验证数据行数
- 确保分析结果包含全部记录

请开始多表关联业务分析。
"""
        else:
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

**第二步：全面业务指标分析（必须执行）**
对每个数值型字段，必须分析以下指标并生成完整表格：
- **基础统计**: 总和(sum)、平均值(mean)、中位数(median)、标准差(std)、方差(var)
- **极值分析**: 最大值(max)、最小值(min)、极差(max-min)
- **分布分析**: 四分位数(25%, 75%)、百分位数(10%, 90%)
- **数据质量**: 非空值数量、空值数量、唯一值数量

**第三步：多维度交叉分析（必须执行）**
- **分类维度分析**: 对每个分类字段，按所有数值字段进行分组汇总（sum, mean, count）
- **相关性分析**: 所有数值字段之间的相关性矩阵
- **排序分析**: 各维度下的Top 10和Bottom 10
- **占比分析**: 各分类的占比和累计占比
- **异常识别**: 识别超出3倍标准差的异常值

**第四步：深度业务洞察**
- 数据反映了什么业务现状？
- 存在什么业务机会或问题？
- 不同维度对比揭示了什么？

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

## 数据访问方式

在 execute_python 中使用：
- `df` 访问数据
- `get_columns(df)` 获取所有列名
- `find_column(df, '部分列名')` 根据部分列名查找完整列名（重要！）

### 列名查找辅助函数（重要！）

由于列名可能很长（如 `'运营总收入 / 实际 / 车均收入 / 元'`），使用以下辅助函数：

```python
# ✅ 正确：使用 find_column 查找完整列名
col = find_column(df, '车均收入')  # 返回 '运营总收入 / 实际 / 车均收入 / 元'
result = df[col].sum()

# ✅ 正确：先获取所有列名，再查找
columns = get_columns(df)
# 然后使用字符串匹配找到正确的列名

# ❌ 错误：直接使用部分列名（会导致 KeyError）
result = df['车均收入'].sum()  # 会报错：'车均收入' not in index
```

## 数据完整性要求

⚠️ **重要：必须显示完整数据**
- 使用 `print(df.to_string())` 显示完整数据，不要使用 `head()` 截断
- 对于分组统计，确保显示所有分组结果
- 对于汇总分析，列出所有类别/分组的完整数据
- 不要遗漏任何数据行，确保分析完整性

## 数据清洗要求

⚠️ **重要：分析前必须过滤无效数据**
- 数值型数据：使用 `df[col].dropna()` 过滤空值，再用 `df[col][df[col] != 0]` 过滤零值
- 文本型数据：过滤空字符串 `''` 和 `'0'`
- 示例代码：`valid_data = df[col].dropna()[df[col].dropna() != 0]`
- 所有统计计算都基于过滤后的有效数据

## Pandas 代码规范（重要！）

⚠️ **避免常见 Pandas 错误：**

### 1. groupby 操作
```python
# ✅ 正确：显式设置 observed=False 避免警告
result = df.groupby('分类列', observed=False)['数值列'].sum()

# ✅ 正确：对分类列进行分组时，确保数值列是数值类型
result = df.groupby('分类列', observed=False)['数值列'].agg(['sum', 'mean'])
```

### 2. pd.cut 分箱操作
```python
# ✅ 正确：cut 函数只接受 bins 参数，不接受 observed 参数
bins = pd.cut(df['数值列'], bins=5)

# ❌ 错误：cut 函数不支持 observed 参数
bins = pd.cut(df['数值列'], bins=5, observed=False)  # 会报错！
```

### 3. 数据类型检查
```python
# ✅ 正确：确保数值操作前检查数据类型
if pd.api.types.is_numeric_dtype(df['列名']):
    result = df['列名'].sum()
else:
    # 尝试转换为数值类型
    result = pd.to_numeric(df['列名'], errors='coerce').sum()
```

### 4. 避免除零错误
```python
# ✅ 正确：除法操作前检查分母是否为零
total = df['列名'].sum()
if total != 0:
    ratio = value / total
else:
    ratio = 0  # 或者 None

# ✅ 正确：计算占比时处理空值和零值
valid_data = df['列名'].dropna()
if len(valid_data) > 0 and valid_data.sum() != 0:
    percentage = (value / valid_data.sum()) * 100
else:
    percentage = 0
```

### 5. 处理缺失模块
```python
# ✅ 正确：导入可选模块时处理 ImportError
try:
    import seaborn as sns
    # 使用 seaborn
except ImportError:
    # 使用 matplotlib 替代
    pass
```

## 重要提醒

❌ 不要做的：
- 只报告"数据有100行5列"这类无意义信息
- 罗列所有统计数字而不解释含义
- 使用复杂的技术术语
- **不要尝试读取外部文件**（如 pd.read_excel('data.xlsx')），数据已通过 `df` 变量提供
- **不要保存文件到本地**，只需分析内存中的数据
- 使用 `head()` 截断数据显示

✅ 应该做的：
- 解释"为什么这个数据分布很重要"
- 指出"这个异常值可能意味着什么业务问题"
- 用业务语言说明"这个相关性揭示了什么机会"
- 给出"基于数据，建议采取什么行动"
- **所有分析都基于提供的 `df` 数据框**，直接使用 `df` 变量
- 确保显示完整数据，不遗漏任何记录

请开始你的深度业务分析。
"""
        
        # 构建初始消息 - 强调业务分析
        # 生成字段描述
        if is_multi_table:
            field_descriptions = []
            for table_name, df in dfs.items():
                table_info = [f"### 工作表: {table_name} ({df.shape[0]}行 x {df.shape[1]}列)"]
                for col in df.columns:
                    dtype = df[col].dtype
                    sample_values = df[col].dropna().head(3).tolist()
                    unique_count = df[col].nunique()
                    table_info.append(f"  - {col}: {dtype}, 示例值: {sample_values}, 唯一值: {unique_count}")
                field_descriptions.append("\n".join(table_info))
            
            initial_message = f"""请对以下多张相关数据进行深度业务分析。

## 业务背景
{context if context else "这是多份相关的业务数据，需要从中提取有价值的业务洞察，并分析表之间的关系。"}

## 数据概览
**正在分析 {len(dfs)} 张工作表：**
{chr(10).join(field_descriptions)}

## 分析要求

请按以下步骤进行多表关联分析：

1. **业务指标识别**
   - 识别各表中的核心业务指标（如金额、数量、比率等）
   - 找出可以对比分析的维度（如车队、线路、时间等）
   - 确定指标的计算方式和业务含义

2. **业务指标对比分析**
   - 使用 execute_python 进行跨表业务指标对比
   - 计算各维度下的业务指标汇总值（sum、mean、max、min等）
   - 生成业务指标对比表格，显示所有对比对象的数据
   - **重点**：分析业务指标的差异，而非数据行数

3. **业务洞察提取**
   - 哪些业务指标表现突出？哪些需要关注？
   - 不同维度间的业务指标差异说明了什么？
   - 存在什么业务机会或风险？

4. **生成业务报告**
   - 用业务语言总结关键发现
   - 提供业务指标对比的核心洞察
   - 给出具体的业务行动建议

**禁止事项**：
- ❌ 不要分析"多少行多少列"这类数据质量信息
- ❌ 不要报告"汇总行数量"等技术细节
- ❌ 不要关注数据结构问题

**必须事项**：
- ✅ 必须分析具体的业务指标数值
- ✅ 必须进行业务指标对比（如各车队收入对比、各线路效率对比）
- ✅ 必须生成业务指标对比表格
- ✅ 必须给出业务层面的结论和建议

请开始多表关联业务分析，重点关注业务指标的对比和洞察。"""
        else:
            df = list(dfs.values())[0]
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
   - **数据完整性要求**：列出所有字段，不遗漏任何字段信息

2. **业务维度分析**
   - 使用 execute_python 深入分析数据分布
   - 计算关键业务指标（如平均值、占比、增长率等）
   - 识别异常值并分析其业务含义
   - 发现数据间的关联性和模式
   - **数据完整性要求**：使用 `to_string()` 显示完整数据，不要使用 `head()` 截断

3. **业务洞察提取**
   - 数据反映了什么业务现状？
   - 有哪些值得关注的业务现象？
   - 存在什么业务机会或风险？
   - **数据完整性要求**：确保所有分组、所有类别的数据都被分析到

4. **生成业务报告**
   - 用业务语言总结关键发现
   - 提供3-5个核心洞察
   - 给出具体的业务行动建议
   - **数据完整性要求**：报告中的数据表格必须包含所有记录

请开始分析，重点关注数据背后的业务含义，而非技术实现细节。

**特别提醒**：
- 每个分析步骤都必须确保数据完整性
- 分组统计时要显示所有分组结果
- 列表数据时不要截断，显示完整列表
- 如果发现数据有遗漏，必须重新分析确保完整"""
        
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
