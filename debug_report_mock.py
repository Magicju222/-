"""
使用模拟数据调试报告生成器
不依赖API调用，专注于报告格式和内容
"""

import pandas as pd
import io
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any

# 导入报告生成器
from report_generator import generate_markdown_report, generate_word_report


@dataclass
class MockAnalysisStep:
    """模拟分析步骤"""
    step_number: int
    observation: str
    action: str = ""
    thought: str = ""


@dataclass
class MockAnalysisResult:
    """模拟分析结果"""
    steps: List[MockAnalysisStep]
    insights: List[Dict[str, Any]]
    final_report: str
    merged_dimensions: List[Any] = field(default_factory=list)


def create_mock_result_for_regional_performance():
    """为区域业绩数据创建模拟分析结果"""
    
    steps = [
        MockAnalysisStep(
            step_number=1,
            thought="分析各地区业绩完成情况",
            action="query_data",
            observation="""各地区业绩完成情况分析：

| 地区 | 年度目标 | 实际完成 | 完成率 | 同比增长 |
|------|----------|----------|--------|----------|
| 华北 | 5,000,000 | 4,800,000 | 96.0% | 12% |
| 华东 | 8,000,000 | 8,200,000 | 102.5% | 18% |
| 华南 | 7,000,000 | 6,800,000 | 97.1% | 8% |
| 西南 | 4,000,000 | 4,200,000 | 105.0% | 15% |
| 东北 | 3,000,000 | 2,800,000 | 93.3% | 5% |

华东地区超额完成目标，完成率达到102.5%，同比增长18%，表现最佳。
东北地区完成率最低，仅为93.3%，需要重点关注。"""
        ),
        MockAnalysisStep(
            step_number=2,
            thought="分析市场份额分布",
            action="query_data",
            observation="""各地区市场份额分析：

| 地区 | 市场份额 | 销售人员数 | 客户总数 | 人均产出 |
|------|----------|------------|----------|----------|
| 华东 | 35% | 40 | 780 | 205,000 |
| 华南 | 28% | 35 | 650 | 194,286 |
| 华北 | 20% | 25 | 450 | 192,000 |
| 西南 | 12% | 18 | 320 | 233,333 |
| 东北 | 5% | 12 | 180 | 233,333 |

华东地区市场份额最高（35%），客户数最多（780个）。
西南地区虽然市场份额较小，但人均产出最高（233,333元）。"""
        ),
        MockAnalysisStep(
            step_number=3,
            thought="识别业绩异常和趋势",
            action="analyze_data",
            observation="""业绩趋势分析：

**关键发现：**
1. 华东地区表现突出：完成率102.5%，同比增长18%，市场份额35%
2. 西南地区超额完成：完成率105%，同比增长15%
3. 东北地区存在风险：完成率93.3%，同比增长仅5%，市场份额最小
4. 整体业绩：5个地区中3个超额完成，2个未完成目标

**异常点：**
- 东北地区各项指标均处于末位，需要制定专项提升计划
- 西南地区人均产出最高，但市场份额较小，有增长潜力"""
        )
    ]
    
    insights = [
        {
            "title": "华东地区业绩领跑，可作为标杆推广经验",
            "description": "华东地区超额完成年度目标，完成率达102.5%，同比增长18%，市场份额占35%。该地区在客户数量（780个）和销售团队规模（40人）上均处于领先地位。",
            "key_findings": [
                "完成率102.5%，超额完成目标",
                "同比增长18%，增速最快",
                "市场份额35%，占比最高",
                "客户数780个，客户基础扎实"
            ],
            "action": "总结华东地区的成功经验，包括客户开发策略、销售团队管理方法，推广至其他地区",
            "confidence": "高",
            "priority": "高"
        },
        {
            "title": "东北地区业绩不达标，需重点关注和扶持",
            "description": "东北地区完成率仅93.3%，同比增长5%，市场份额仅5%，各项指标均处于末位，存在业绩下滑风险。",
            "key_findings": [
                "完成率93.3%，未完成年度目标",
                "同比增长仅5%，增速最慢",
                "市场份额5%，占比最小",
                "客户数180个，客户基础薄弱"
            ],
            "action": "制定东北地区专项提升计划，增加资源投入，派遣优秀销售经理驻点指导",
            "confidence": "高",
            "priority": "高"
        },
        {
            "title": "西南地区人均产出最高，具备增长潜力",
            "description": "西南地区虽然市场份额较小（12%），但超额完成目标（105%），人均产出最高（233,333元），显示出较强的销售效率。",
            "key_findings": [
                "人均产出233,333元，全公司最高",
                "完成率105%，超额完成目标",
                "同比增长15%，增速较快",
                "市场份额12%，有提升空间"
            ],
            "action": "扩大西南地区销售团队规模，复制高效销售模式，提升市场份额",
            "confidence": "中",
            "priority": "中"
        }
    ]
    
    final_report = """## 区域业绩分析总结

### 整体业绩概况
2024年度区域业绩分析显示，5个地区中3个超额完成目标，整体业绩表现良好。华东、西南地区表现突出，东北地区需要重点关注。

### 关键指标对比
- **最佳表现**：华东地区（完成率102.5%，增长18%）
- **最大潜力**：西南地区（人均产出最高233,333元）
- **最需要关注**：东北地区（完成率93.3%，增长仅5%）

### 区域分布特点
1. 华东地区：市场份额35%，客户基础扎实，是公司的核心市场
2. 华南地区：市场份额28%，业绩稳定，是重要支撑
3. 华北地区：市场份额20%，传统市场，需要激活
4. 西南地区：市场份额12%，效率高，有增长潜力
5. 东北地区：市场份额5%，基础薄弱，需要扶持

### 建议措施
1. 推广华东经验，提升整体销售能力
2. 制定东北振兴计划，防止业绩下滑
3. 加大西南投入，扩大市场份额
4. 优化人员配置，提升人均产出"""
    
    return MockAnalysisResult(
        steps=steps,
        insights=insights,
        final_report=final_report
    )


def test_report_generation():
    """测试报告生成"""
    print("\n" + "="*80)
    print("报告生成器调试 - 使用模拟数据")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # 1. 加载测试数据
    print("1. 加载测试数据...")
    file_path = 'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\sales_analysis_test.xlsx'
    dfs = pd.read_excel(file_path, sheet_name=None)
    df = dfs['区域业绩']
    print(f"   ✓ 数据加载完成: {df.shape[0]}行 x {df.shape[1]}列")
    print(f"   列名: {list(df.columns)}\n")
    
    # 2. 创建模拟分析结果
    print("2. 创建模拟分析结果...")
    mock_result = create_mock_result_for_regional_performance()
    print(f"   ✓ 模拟数据创建完成")
    print(f"   分析步骤数: {len(mock_result.steps)}")
    print(f"   洞察数: {len(mock_result.insights)}\n")
    
    # 3. 生成Markdown报告
    print("3. 生成Markdown报告...")
    try:
        md_report = generate_markdown_report(mock_result, dfs, '区域业绩')
        md_path = 'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\mock_report_区域业绩.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_report)
        print(f"   ✓ Markdown报告已保存: {md_path}")
        print(f"   报告长度: {len(md_report)} 字符\n")
        
        # 显示报告预览
        print("4. Markdown报告预览:")
        print("-" * 80)
        print(md_report)
        print("-" * 80 + "\n")
        
    except Exception as e:
        print(f"   ✗ Markdown报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 生成Word报告
    print("5. 生成Word报告...")
    try:
        docx_io = generate_word_report(mock_result, dfs, '区域业绩')
        docx_path = 'e:\\徐衡文档\\AI\\Trae EXCEL\\test_data\\mock_report_区域业绩.docx'
        with open(docx_path, 'wb') as f:
            f.write(docx_io.getvalue())
        print(f"   ✓ Word报告已保存: {docx_path}")
        print(f"   文件大小: {len(docx_io.getvalue())} 字节\n")
        
    except Exception as e:
        print(f"   ✗ Word报告生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. 分析报告结构
    print("6. 报告结构分析:")
    sections = [
        "一、分析维度",
        "二、关键洞察", 
        "三、详细分析结果",
        "四、分析摘要",
        "五、结论与建议"
    ]
    for section in sections:
        has_section = section in md_report
        print(f"   {'✓' if has_section else '✗'} {section}")
    print()
    
    # 7. 检查表格格式
    print("7. 表格格式检查:")
    table_count = md_report.count('| --- |')
    print(f"   发现 {table_count} 个Markdown表格")
    if table_count > 0:
        print("   ✓ 表格格式正确")
    print()
    
    print("="*80)
    print("调试完成！")
    print("="*80)


if __name__ == '__main__':
    test_report_generation()
