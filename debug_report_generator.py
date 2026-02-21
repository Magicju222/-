"""
调试报告生成器
用于快速测试和优化分析报告功能
"""

import pandas as pd
import sys
from datetime import datetime

# 导入需要测试的模块
from agent_analyzer import AgentAnalyzer
from report_generator import generate_markdown_report, generate_word_report
from data_integrity_checker import DataIntegrityChecker

def load_test_data():
    """加载测试数据"""
    file_path = 'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\sales_analysis_test.xlsx'
    dfs = pd.read_excel(file_path, sheet_name=None)
    return dfs

def debug_analysis(sheet_name='区域业绩'):
    """调试分析流程"""
    print(f"\n{'='*80}")
    print(f"开始调试分析: {sheet_name}")
    print(f"{'='*80}\n")
    
    # 1. 加载数据
    print("1. 加载测试数据...")
    dfs = load_test_data()
    df = dfs[sheet_name]
    print(f"   ✓ 数据加载完成: {df.shape[0]}行 x {df.shape[1]}列")
    print(f"   列名: {list(df.columns)}")
    print()
    
    # 2. 数据完整性检查
    print("2. 执行数据完整性检查...")
    checker = DataIntegrityChecker(dfs)
    input_checks = checker.check_input_integrity()
    input_check = input_checks[0] if input_checks else None
    if input_check:
        print(f"   ✓ 输入完整性: {input_check.passed}")
        if not input_check.passed:
            print(f"   问题: {input_check.details}")
    print()
    
    # 3. 执行AI分析
    print("3. 执行AI分析...")
    analyzer = AgentAnalyzer()
    
    try:
        result = analyzer.analyze(df, sheet_name)
        print(f"   ✓ 分析完成")
        print(f"   分析步骤数: {len(result.steps) if hasattr(result, 'steps') else 0}")
        print(f"   洞察数: {len(result.insights) if hasattr(result, 'insights') else 0}")
        print()
        
        # 4. 检查分析结果完整性
        print("4. 检查分析结果完整性...")
        display_checks = checker.check_display_integrity(result)
        display_check = display_checks[0] if display_checks else None
        if display_check:
            print(f"   ✓ 显示完整性: {display_check.passed}")
            if not display_check.passed:
                print(f"   问题: {display_check.details}")
        print()
        
        # 5. 生成Markdown报告
        print("5. 生成Markdown报告...")
        md_report = generate_markdown_report(result, dfs, sheet_name)
        md_path = f'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\report_{sheet_name}.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"   ✓ Markdown报告已保存: {md_path}")
        print(f"   报告长度: {len(md_report)} 字符")
        print()
        
        # 6. 生成Word报告
        print("6. 生成Word报告...")
        docx_io = generate_word_report(result, dfs, sheet_name)
        docx_path = f'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\report_{sheet_name}.docx'
        with open(docx_path, 'wb') as f:
            f.write(docx_io.getvalue())
        print(f"   ✓ Word报告已保存: {docx_path}")
        print()
        
        # 7. 显示报告预览
        print("7. 报告预览 (前2000字符):")
        print("-" * 80)
        print(md_report[:2000])
        print("...")
        print("-" * 80)
        print()
        
        # 8. 分析洞察内容
        print("8. 洞察内容分析:")
        if hasattr(result, 'insights') and result.insights:
            for i, insight in enumerate(result.insights[:3], 1):
                print(f"\n   洞察 {i}:")
                print(f"   - 标题: {insight.get('title', 'N/A')}")
                print(f"   - 描述: {insight.get('description', 'N/A')[:100]}...")
                print(f"   - 关键发现: {insight.get('key_findings', [])}")
                print(f"   - 行动建议: {insight.get('action', 'N/A')}")
        else:
            print("   ⚠ 没有洞察数据")
        print()
        
        # 9. 分析观察结果
        print("9. 观察结果分析:")
        if hasattr(result, 'steps') and result.steps:
            print(f"   总步骤数: {len(result.steps)}")
            for i, step in enumerate(result.steps[:3], 1):
                obs = getattr(step, 'observation', '')
                print(f"\n   步骤 {i} 观察结果 (前200字符):")
                print(f"   {obs[:200]}...")
        else:
            print("   ⚠ 没有步骤数据")
        print()
        
        return True
        
    except Exception as e:
        print(f"   ✗ 分析失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("\n" + "="*80)
    print("报告生成器调试工具")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 测试不同的工作表
    test_sheets = ['区域业绩', '客户数据', '销售明细']
    
    for sheet in test_sheets:
        try:
            debug_analysis(sheet)
        except Exception as e:
            print(f"\n测试 {sheet} 时出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("调试完成")
    print("="*80)

if __name__ == '__main__':
    main()
