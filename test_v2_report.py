"""
测试业务语义分析报告生成器 V2
"""
import pandas as pd
from business_semantic_report_v2 import generate_business_semantic_report

def test_v2_report():
    """测试V2版本报告生成"""
    print("="*80)
    print("测试业务语义分析报告生成器 V2")
    print("="*80)
    
    # 创建测试数据
    sales_data = pd.DataFrame({
        '产品类别': ['电子产品', '服装', '食品'] * 4,
        '销售额': [150000, 80000, 45000, 200000, 95000, 52000, 180000, 72000, 48000, 220000, 85000, 50000],
        '销售量': [150, 400, 900, 200, 475, 1040, 180, 360, 960, 220, 425, 1000],
        '地区': ['华东', '华南', '华北'] * 4,
    })
    
    print("\n测试数据:")
    print(sales_data.head(10))
    print(f"\n数据维度: {sales_data.shape}")
    
    # 生成报告
    print("\n" + "="*80)
    print("开始生成报告...")
    print("="*80)
    
    md_report, word_report = generate_business_semantic_report(
        sales_data, 
        title="销售业务分析报告V2"
    )
    
    print(f"\n✓ Markdown报告生成成功，长度: {len(md_report)} 字符")
    print(f"✓ Word报告生成成功，大小: {len(word_report)} 字节")
    
    # 保存报告
    with open('business_report_v2.md', 'w', encoding='utf-8') as f:
        f.write(md_report)
    print("\n✓ 已保存: business_report_v2.md")
    
    with open('business_report_v2.docx', 'wb') as f:
        f.write(word_report)
    print("✓ 已保存: business_report_v2.docx")
    
    # 显示报告预览
    print("\n" + "="*80)
    print("报告预览（前2000字符）:")
    print("="*80)
    print(md_report[:2000])
    
    print("\n" + "="*80)
    print("✓ 测试完成!")
    print("="*80)

if __name__ == '__main__':
    test_v2_report()
