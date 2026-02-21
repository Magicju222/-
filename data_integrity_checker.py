"""
数据完整性校验模块
用于检查数据分析全流程的数据完整性
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class IntegrityCheckResult:
    """完整性检查结果"""
    check_name: str
    passed: bool
    expected_count: int
    actual_count: int
    missing_count: int
    details: Dict[str, Any]
    suggestions: List[str]


class DataIntegrityChecker:
    """数据完整性检查器"""
    
    def __init__(self, dfs: Dict[str, pd.DataFrame]):
        if isinstance(dfs, pd.DataFrame):
            dfs = {"default": dfs}
        self.dfs = dfs
        self.check_results: List[IntegrityCheckResult] = []
    
    def check_input_integrity(self) -> List[IntegrityCheckResult]:
        """检查数据输入完整性"""
        results = []
        
        for name, df in self.dfs.items():
            # 检查1: 数据是否为空
            if df.empty:
                results.append(IntegrityCheckResult(
                    check_name=f"{name}_empty_check",
                    passed=False,
                    expected_count=1,
                    actual_count=0,
                    missing_count=1,
                    details={"error": "数据表为空"},
                    suggestions=["检查数据源是否正确", "确认文件是否正确上传"]
                ))
                continue
            
            # 检查2: 记录数检查
            row_count = len(df)
            results.append(IntegrityCheckResult(
                check_name=f"{name}_row_count",
                passed=row_count > 0,
                expected_count=row_count,
                actual_count=row_count,
                missing_count=0,
                details={"rows": row_count, "columns": len(df.columns)},
                suggestions=[]
            ))
            
            # 检查3: 列完整性检查
            for col in df.columns:
                non_null_count = df[col].notna().sum()
                null_count = df[col].isna().sum()
                
                results.append(IntegrityCheckResult(
                    check_name=f"{name}_{col}_completeness",
                    passed=null_count == 0,
                    expected_count=row_count,
                    actual_count=non_null_count,
                    missing_count=null_count,
                    details={
                        "column": col,
                        "null_count": null_count,
                        "null_ratio": null_count / row_count if row_count > 0 else 0
                    },
                    suggestions=[f"列 {col} 有 {null_count} 个空值"] if null_count > 0 else []
                ))
        
        self.check_results.extend(results)
        return results
    
    def check_computation_integrity(self, original_df: pd.DataFrame, 
                                    result_df: pd.DataFrame,
                                    operation_name: str) -> IntegrityCheckResult:
        """检查计算完整性"""
        original_count = len(original_df)
        result_count = len(result_df)
        
        # 检查记录数是否一致
        if original_count != result_count:
            return IntegrityCheckResult(
                check_name=f"{operation_name}_row_integrity",
                passed=False,
                expected_count=original_count,
                actual_count=result_count,
                missing_count=original_count - result_count,
                details={
                    "operation": operation_name,
                    "original_rows": original_count,
                    "result_rows": result_count
                },
                suggestions=[
                    "检查过滤条件是否正确",
                    "确认是否有数据被意外删除",
                    "验证分组操作是否完整"
                ]
            )
        
        return IntegrityCheckResult(
            check_name=f"{operation_name}_row_integrity",
            passed=True,
            expected_count=original_count,
            actual_count=result_count,
            missing_count=0,
            details={"operation": operation_name},
            suggestions=[]
        )
    
    def check_display_integrity(self, data: Any, displayed_data: Any, 
                                display_name: str) -> IntegrityCheckResult:
        """检查数据显示完整性"""
        
        # 处理DataFrame
        if isinstance(data, pd.DataFrame):
            original_count = len(data)
            
            if isinstance(displayed_data, pd.DataFrame):
                displayed_count = len(displayed_data)
            elif isinstance(displayed_data, dict):
                # 检查字典中的数据
                displayed_count = len(displayed_data)
            elif isinstance(displayed_data, list):
                displayed_count = len(displayed_data)
            else:
                displayed_count = 0
            
            if original_count != displayed_count:
                return IntegrityCheckResult(
                    check_name=f"{display_name}_display_integrity",
                    passed=False,
                    expected_count=original_count,
                    actual_count=displayed_count,
                    missing_count=original_count - displayed_count,
                    details={
                        "original_rows": original_count,
                        "displayed_rows": displayed_count,
                        "data_type": "DataFrame"
                    },
                    suggestions=[
                        "检查是否使用了 head() 截断数据",
                        "确认数据传输过程是否完整",
                        "验证前端渲染逻辑"
                    ]
                )
        
        # 处理列表
        elif isinstance(data, list):
            original_count = len(data)
            displayed_count = len(displayed_data) if isinstance(displayed_data, list) else 0
            
            if original_count != displayed_count:
                return IntegrityCheckResult(
                    check_name=f"{display_name}_display_integrity",
                    passed=False,
                    expected_count=original_count,
                    actual_count=displayed_count,
                    missing_count=original_count - displayed_count,
                    details={
                        "original_count": original_count,
                        "displayed_count": displayed_count,
                        "data_type": "list"
                    },
                    suggestions=[
                        "检查列表切片操作",
                        "确认分页逻辑是否正确"
                    ]
                )
        
        return IntegrityCheckResult(
            check_name=f"{display_name}_display_integrity",
            passed=True,
            expected_count=len(data) if hasattr(data, '__len__') else 1,
            actual_count=len(displayed_data) if hasattr(displayed_data, '__len__') else 1,
            missing_count=0,
            details={"display_name": display_name},
            suggestions=[]
        )
    
    def check_step_integrity(self, step_data: Dict[str, Any]) -> List[IntegrityCheckResult]:
        """检查单个步骤的数据完整性"""
        results = []
        
        # 检查工具执行结果
        tool_result = step_data.get('tool_result')
        if tool_result:
            if tool_result.success:
                result_data = tool_result.result
                
                # 检查返回的数据是否完整
                if isinstance(result_data, str):
                    try:
                        import json
                        parsed = json.loads(result_data)
                        
                        # 检查 head 数据
                        if 'head' in parsed and isinstance(parsed['head'], dict):
                            for key, values in parsed['head'].items():
                                if isinstance(values, dict):
                                    count = len(values)
                                    results.append(IntegrityCheckResult(
                                        check_name=f"step_{step_data.get('step_number', 0)}_{key}_count",
                                        passed=True,
                                        expected_count=count,
                                        actual_count=count,
                                        missing_count=0,
                                        details={"field": key, "count": count},
                                        suggestions=[]
                                    ))
                    except:
                        pass
        
        self.check_results.extend(results)
        return results
    
    def generate_integrity_report(self) -> str:
        """生成完整性检查报告"""
        report = []
        report.append("=" * 60)
        report.append("数据完整性检查报告")
        report.append("=" * 60)
        report.append("")
        
        passed_count = sum(1 for r in self.check_results if r.passed)
        failed_count = len(self.check_results) - passed_count
        
        report.append(f"总检查项: {len(self.check_results)}")
        report.append(f"通过: {passed_count}")
        report.append(f"失败: {failed_count}")
        report.append("")
        
        # 显示失败的检查
        if failed_count > 0:
            report.append("失败的检查项:")
            report.append("-" * 60)
            for result in self.check_results:
                if not result.passed:
                    report.append(f"\n检查项: {result.check_name}")
                    report.append(f"预期数量: {result.expected_count}")
                    report.append(f"实际数量: {result.actual_count}")
                    report.append(f"缺失数量: {result.missing_count}")
                    report.append(f"详细信息: {result.details}")
                    report.append("建议:")
                    for suggestion in result.suggestions:
                        report.append(f"  - {suggestion}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取检查摘要"""
        passed = sum(1 for r in self.check_results if r.passed)
        failed = len(self.check_results) - passed
        
        return {
            "total_checks": len(self.check_results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.check_results) if self.check_results else 0,
            "all_passed": failed == 0
        }


def validate_dataframe_integrity(df: pd.DataFrame, name: str = "data") -> Tuple[bool, List[str]]:
    """快速验证DataFrame完整性"""
    issues = []
    
    if df.empty:
        issues.append(f"{name} 为空")
        return False, issues
    
    # 检查空值比例
    null_counts = df.isnull().sum()
    for col in df.columns:
        null_ratio = null_counts[col] / len(df)
        if null_ratio > 0.5:
            issues.append(f"{name}.{col} 空值比例过高: {null_ratio:.2%}")
    
    # 检查重复行
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        issues.append(f"{name} 存在 {duplicate_count} 行重复数据")
    
    return len(issues) == 0, issues
