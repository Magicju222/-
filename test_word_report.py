"""
测试完整的Word报告生成器
"""
import pandas as pd
from business_report_word import generate_complete_word_report

def test_word_report():
    """测试Word报告生成"""
    print("="*80)
    print("测试完整Word报告生成器")
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
    
    # 生成Word报告
    print("\n" + "="*80)
    print("开始生成Word报告...")
    print("="*80)
    
    word_report = generate_complete_word_report(
        sales_data, 
        title="销售业务分析报告（完整版）"
    )
    
    print(f"\n✓ Word报告生成成功，大小: {len(word_report)} 字节")
    
    # 保存报告
    with open('business_report_complete.docx', 'wb') as f:
        f.write(word_report)
    print("\n✓ 已保存: business_report_complete.docx")
    
    print("\n" + "="*80)
    print("✓ 测试完成! 请打开 business_report_complete.docx 查看报告")
    print("="*80)

if __name__ == '__main__':
    test_word_report()
