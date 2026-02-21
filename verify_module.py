"""
验证业务语义报告模块核心功能
"""
import pandas as pd
from business_semantic_report import BusinessSemanticReportGenerator

def verify_module():
    """验证模块功能"""
    print("="*80)
    print("验证业务语义报告模块")
    print("="*80)
    
    # 创建测试数据
    df = pd.DataFrame({
        '产品类别': ['电子产品', '服装', '食品'] * 4,
        '销售额': [150000, 80000, 45000, 200000, 95000, 52000, 180000, 72000, 48000, 220000, 85000, 50000],
        '销售量': [150, 400, 900, 200, 475, 1040, 180, 360, 960, 220, 425, 1000],
        '地区': ['华东', '华南', '华北'] * 4,
    })
    
    print("\n✓ 测试数据创建成功")
    print(f"  数据维度: {df.shape}")
    
    # 创建生成器
    try:
        gen = BusinessSemanticReportGenerator(df)
        print("\n✓ 报告生成器创建成功")
        print(f"  数值列: {gen.numeric_columns}")
        print(f"  分类列: {gen.categorical_columns}")
    except Exception as e:
        print(f"\n✗ 报告生成器创建失败: {e}")
        return
    
    # 测试业务指标分析
    try:
        metrics = gen._analyze_business_metrics()
        print(f"\n✓ 业务指标分析成功")
        print(f"  识别到 {len(metrics)} 个业务指标")
        for m in metrics[:3]:
            print(f"    - {m.name}: {m.value:.2f} {m.unit}")
    except Exception as e:
        print(f"\n✗ 业务指标分析失败: {e}")
        return
    
    # 测试维度分析
    try:
        dimensions = gen._analyze_by_dimensions()
        print(f"\n✓ 维度分析成功")
        print(f"  识别到 {len(dimensions)} 个维度分析")
        for d in dimensions[:2]:
            print(f"    - {d.dimension_name} × {d.metric_name}: {len(d.data)} 个类别")
    except Exception as e:
        print(f"\n✗ 维度分析失败: {e}")
        return
    
    # 测试关键洞察提取
    try:
        insights = gen._extract_key_insights()
        print(f"\n✓ 关键洞察提取成功")
        print(f"  提取到 {len(insights)} 个关键洞察")
        for i in insights[:3]:
            print(f"    - [{i.insight_type}] {i.title}")
    except Exception as e:
        print(f"\n✗ 关键洞察提取失败: {e}")
        return
    
    # 测试业务建议生成
    try:
        recommendations = gen._generate_recommendations()
        print(f"\n✓ 业务建议生成成功")
        print(f"  生成 {len(recommendations)} 个业务建议")
        for r in recommendations[:3]:
            print(f"    - [{r.rec_type}] {r.title}")
    except Exception as e:
        print(f"\n✗ 业务建议生成失败: {e}")
        return
    
    # 测试Markdown报告生成
    try:
        md_report = gen.generate_markdown_report(
            title="业务分析报告",
            metrics=metrics,
            dimensions=dimensions,
            trends=[],
            insights=insights,
            recommendations=recommendations
        )
        print(f"\n✓ Markdown报告生成成功")
        print(f"  报告长度: {len(md_report)} 字符")
        
        # 保存报告
        with open('business_report_verify.md', 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"  已保存: business_report_verify.md")
    except Exception as e:
        print(f"\n✗ Markdown报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试Word报告生成
    try:
        word_report = gen.generate_word_report(
            title="业务分析报告",
            metrics=metrics,
            dimensions=dimensions,
            trends=[],
            insights=insights,
            recommendations=recommendations
        )
        print(f"\n✓ Word报告生成成功")
        print(f"  报告大小: {len(word_report)} 字节")
        
        # 保存报告
        with open('business_report_verify.docx', 'wb') as f:
            f.write(word_report)
        print(f"  已保存: business_report_verify.docx")
    except Exception as e:
        print(f"\n✗ Word报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*80)
    print("✓ 所有功能验证通过!")
    print("="*80)
    
    # 显示报告预览
    print("\n报告预览（前1500字符）:")
    print("-"*80)
    print(md_report[:1500])
    print("-"*80)

if __name__ == '__main__':
    verify_module()
