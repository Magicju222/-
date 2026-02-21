"""
测试业务语义分析报告生成器
"""
import pandas as pd
from business_semantic_report import BusinessSemanticReportGenerator, generate_business_semantic_report

def test_business_report():
    """测试业务语义分析报告"""
    print("="*80)
    print("测试业务语义分析报告生成器")
    print("="*80)
    
    # 创建测试数据 - 销售数据
    sales_data = pd.DataFrame({
        '产品类别': ['电子产品', '服装', '食品', '电子产品', '服装', '食品', '电子产品', '服装'],
        '销售额': [150000, 80000, 45000, 200000, 95000, 52000, 180000, 72000],
        '销售量': [150, 400, 900, 200, 475, 1040, 180, 360],
        '地区': ['华东', '华东', '华东', '华南', '华南', '华南', '华北', '华北'],
        '日期': pd.to_datetime(['2024-01', '2024-01', '2024-01', '2024-02', '2024-02', '2024-02', '2024-03', '2024-03'])
    })
    
    print("\n1. 测试数据预览:")
    print(sales_data.head())
    
    # 创建报告生成器
    generator = BusinessSemanticReportGenerator(sales_data)
    
    # 测试业务指标分析
    print("\n2. 测试业务指标分析:")
    metrics = generator._analyze_business_metrics()
    print(f"   识别到 {len(metrics)} 个业务指标:")
    for metric in metrics[:3]:
        print(f"   - {metric.name}: {metric.format_str.format(metric.value)} {metric.unit}")
    
    # 测试维度分析
    print("\n3. 测试维度分析:")
    dimensions = generator._analyze_by_dimensions()
    print(f"   识别到 {len(dimensions)} 个维度分析:")
    for dim in dimensions[:2]:
        print(f"   - {dim.dimension_name} × {dim.metric_name}: {len(dim.data)} 个类别")
    
    # 测试趋势分析
    print("\n4. 测试趋势分析:")
    trends = generator._analyze_trends()
    print(f"   识别到 {len(trends)} 个趋势分析:")
    for trend in trends[:2]:
        print(f"   - {trend.time_field} × {trend.metric_name}: {trend.trend_direction}")
    
    # 测试关键洞察提取
    print("\n5. 测试关键洞察提取:")
    insights = generator._extract_key_insights(metrics, dimensions, trends)
    print(f"   提取到 {len(insights)} 个关键洞察:")
    for insight in insights[:3]:
        print(f"   - [{insight.insight_type}] {insight.title}")
    
    # 测试业务建议生成
    print("\n6. 测试业务建议生成:")
    recommendations = generator._generate_recommendations(insights, metrics, dimensions)
    print(f"   生成 {len(recommendations)} 个业务建议:")
    for rec in recommendations[:3]:
        print(f"   - [{rec.rec_type}] {rec.title}")
    
    # 测试Markdown报告生成
    print("\n7. 测试Markdown报告生成:")
    try:
        md_report = generator.generate_markdown_report(
            title="销售数据分析报告",
            metrics=metrics,
            dimensions=dimensions,
            trends=trends,
            insights=insights,
            recommendations=recommendations
        )
        print(f"   Markdown报告生成成功，长度: {len(md_report)} 字符")
        print("\n   报告预览（前1000字符）:")
        print(md_report[:1000])
    except Exception as e:
        print(f"   Markdown报告生成失败: {e}")
    
    # 测试Word报告生成
    print("\n8. 测试Word报告生成:")
    try:
        word_report = generator.generate_word_report(
            title="销售数据分析报告",
            metrics=metrics,
            dimensions=dimensions,
            trends=trends,
            insights=insights,
            recommendations=recommendations
        )
        print(f"   Word报告生成成功，大小: {len(word_report)} 字节")
    except Exception as e:
        print(f"   Word报告生成失败: {e}")
    
    # 测试便捷函数
    print("\n9. 测试便捷函数:")
    try:
        md_report, word_report = generate_business_semantic_report(sales_data, title="销售数据分析报告")
        print(f"   便捷函数执行成功")
        print(f"   Markdown报告: {len(md_report)} 字符")
        print(f"   Word报告: {len(word_report)} 字节")
    except Exception as e:
        print(f"   便捷函数执行失败: {e}")
    
    print("\n" + "="*80)
    print("测试完成!")
    print("="*80)

if __name__ == '__main__':
    test_business_report()
