"""
测试Excel报告生成器
"""
import pandas as pd
from business_report_excel import generate_excel_report

def test_excel_report():
    """测试Excel报告生成"""
    print("="*80)
    print("测试Excel报告生成器")
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
    
    # 生成Excel报告
    print("\n" + "="*80)
    print("开始生成Excel报告...")
    print("="*80)
    
    excel_report = generate_excel_report(
        sales_data, 
        title="销售业务分析报告"
    )
    
    print(f"\n✓ Excel报告生成成功，大小: {len(excel_report)} 字节")
    
    # 保存报告
    with open('business_report.xlsx', 'wb') as f:
        f.write(excel_report)
    print("\n✓ 已保存: business_report.xlsx")
    
    print("\n" + "="*80)
    print("✓ 测试完成! 请打开 business_report.xlsx 查看报告")
    print("="*80)
    print("\n报告包含以下工作表:")
    print("  1. 报告概览 - 数据概览信息")
    print("  2. 核心业务指标 - 业务指标统计表")
    print("  3. 维度分析 - 各维度详细分析")
    print("  4. 关键洞察 - 关键洞察及支撑数据")
    print("  5. 业务建议 - 可执行的业务建议")

if __name__ == '__main__':
    test_excel_report()
