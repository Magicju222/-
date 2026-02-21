"""
完整测试业务语义分析报告生成器
"""
import pandas as pd
from business_semantic_report import (
    BusinessSemanticReportGenerator, 
    generate_business_semantic_report
)

def test_full_report():
    """测试完整报告生成"""
    print("="*80)
    print("完整测试业务语义分析报告生成器")
    print("="*80)
    
    # 创建测试数据 - 销售数据
    sales_data = pd.DataFrame({
        '产品类别': ['电子产品', '服装', '食品', '电子产品', '服装', '食品', '电子产品', '服装', '食品', '电子产品'],
        '销售额': [150000, 80000, 45000, 200000, 95000, 52000, 180000, 72000, 48000, 220000],
        '销售量': [150, 400, 900, 200, 475, 1040, 180, 360, 960, 220],
        '地区': ['华东', '华东', '华东', '华南', '华南', '华南', '华北', '华北', '华北', '华东'],
        '月份': ['2024-01', '2024-01', '2024-01', '2024-02', '2024-02', '2024-02', '2024-03', '2024-03', '2024-03', '2024-04']
    })
    
    print("\n1. 测试数据:")
    print(sales_data)
    print(f"   数据行数: {len(sales_data)}")
    
    # 使用便捷函数生成报告
    print("\n2. 生成业务语义分析报告...")
    md_report, word_report = generate_business_semantic_report(
        sales_data, 
        title="销售业务分析报告"
    )
    
    print(f"   Markdown报告: {len(md_report)} 字符")
    print(f"   Word报告: {len(word_report)} 字节")
    
    # 保存报告
    print("\n3. 保存报告文件...")
    with open('test_business_report.md', 'w', encoding='utf-8') as f:
        f.write(md_report)
    print("   已保存: test_business_report.md")
    
    with open('test_business_report.docx', 'wb') as f:
        f.write(word_report)
    print("   已保存: test_business_report.docx")
    
    # 显示报告预览
    print("\n4. 报告预览（前2000字符）:")
    print("-"*80)
    print(md_report[:2000])
    print("-"*80)
    
    print("\n" + "="*80)
    print("测试完成! 报告已生成并保存。")
    print("="*80)

if __name__ == '__main__':
    test_full_report()
