"""
报告生成器 - 支持 Markdown 和 Word 格式
"""
import io
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def generate_markdown_report(agent_result, df, sheet_name):
    """生成 Markdown 格式的报告"""
    report = f"""# 数据分析报告

## 基本信息
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **数据表**: {sheet_name}
- **数据规模**: {df.shape[0]} 行 × {df.shape[1]} 列
- **分析步骤**: {len(agent_result.steps)} 步
- **生成代码**: {len(agent_result.generated_code)} 段
- **生成图表**: {len(agent_result.visualizations)} 个

## 数据字段说明

"""
    
    # 添加字段说明
    for col in df.columns:
        dtype = str(df[col].dtype)
        unique_count = df[col].nunique()
        null_count = df[col].isnull().sum()
        report += f"- **{col}**: 类型={dtype}, 唯一值={unique_count}, 缺失值={null_count}\n"
    
    report += "\n## 详细分析过程\n\n"
    
    # 添加分析步骤
    for step in agent_result.steps:
        if step.action == 'error':
            continue
        report += f"### 步骤 {step.step_number}: {step.action}\n"
        if step.thought:
            report += f"**思考过程**: {step.thought}\n\n"
        if step.observation:
            obs = step.observation[:500] + "..." if len(step.observation) > 500 else step.observation
            report += f"**分析结果**: {obs}\n\n"
    
    report += f"\n## 最终分析报告\n\n{agent_result.final_report}\n"
    
    return report


def generate_word_report(agent_result, df, sheet_name):
    """生成 Word 格式的报告"""
    doc = Document()
    
    # 设置中文字体
    doc.styles['Normal'].font.name = 'Microsoft YaHei'
    doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    
    # 标题
    title = doc.add_heading('数据分析报告', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 基本信息
    doc.add_heading('基本信息', level=1)
    info_table = doc.add_table(rows=5, cols=2)
    info_table.style = 'Light Grid Accent 1'
    
    info_data = [
        ('分析时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('数据表', sheet_name),
        ('数据规模', f"{df.shape[0]} 行 × {df.shape[1]} 列"),
        ('分析步骤', str(len(agent_result.steps))),
        ('生成图表', str(len(agent_result.visualizations))),
    ]
    
    for i, (key, value) in enumerate(info_data):
        info_table.rows[i].cells[0].text = key
        info_table.rows[i].cells[1].text = value
    
    doc.add_paragraph()
    
    # 数据字段说明
    doc.add_heading('数据字段说明', level=1)
    for col in df.columns:
        dtype = str(df[col].dtype)
        unique_count = df[col].nunique()
        null_count = df[col].isnull().sum()
        
        p = doc.add_paragraph()
        p.add_run(f"{col}").bold = True
        p.add_run(f" - 类型: {dtype}, 唯一值: {unique_count}, 缺失值: {null_count}")
    
    doc.add_page_break()
    
    # 详细分析过程
    doc.add_heading('详细分析过程', level=1)
    
    for step in agent_result.steps:
        if step.action == 'error':
            continue
        
        doc.add_heading(f"步骤 {step.step_number}: {step.action}", level=2)
        
        if step.thought:
            p = doc.add_paragraph()
            p.add_run("思考过程: ").bold = True
            doc.add_paragraph(step.thought)
        
        if step.observation:
            p = doc.add_paragraph()
            p.add_run("分析结果: ").bold = True
            obs = step.observation[:800] + "..." if len(step.observation) > 800 else step.observation
            doc.add_paragraph(obs)
    
    doc.add_page_break()
    
    # 最终分析报告
    doc.add_heading('最终分析报告', level=1)
    
    # 将 Markdown 格式的报告分段添加到 Word
    report_lines = agent_result.final_report.split('\n')
    current_level = 0
    
    for line in report_lines:
        line = line.strip()
        if not line:
            continue
        
        # 处理标题
        if line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            doc.add_heading(line[4:], level=3)
        elif line.startswith('#### '):
            doc.add_heading(line[5:], level=4)
        # 处理列表
        elif line.startswith('- ') or line.startswith('* '):
            doc.add_paragraph(line[2:], style='List Bullet')
        elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '):
            doc.add_paragraph(line[3:], style='List Number')
        # 处理粗体
        elif line.startswith('**') and line.endswith('**'):
            p = doc.add_paragraph()
            p.add_run(line[2:-2]).bold = True
        # 普通段落
        else:
            doc.add_paragraph(line)
    
    # 保存到内存
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    return doc_io
