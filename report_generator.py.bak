"""
报告生成器 - 聚焦业务深度分析的专业报告
强调业务数据分析和洞察，先罗列所有步骤数据表格，再进行文字总结
"""
import io
import json
import re
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def _extract_all_step_data(agent_result):
    """从所有步骤中提取完整的数据和分析结果"""
    all_data = []
    
    for idx, step in enumerate(agent_result.steps, 1):
        step_data = {
            'step_num': idx,
            'action': step.action,
            'thought': step.thought,
            'observation': step.observation,
            'tool_result': None,
            'parsed_table': None
        }
        
        # 提取工具执行结果
        if step.tool_result and step.tool_result.success:
            result = step.tool_result.result
            step_data['tool_result'] = result
            
            # 尝试解析为表格
            if result:
                try:
                    if isinstance(result, str):
                        result = result.strip()
                        if result.startswith('[') or result.startswith('{'):
                            data = json.loads(result)
                            table_data = _parse_data_to_table(data)
                            if table_data:
                                step_data['parsed_table'] = table_data
                except:
                    pass
        
        all_data.append(step_data)
    
    return all_data


def _parse_data_to_table(data):
    """解析数据为表格"""
    if isinstance(data, dict):
        return _parse_dict_to_table(data)
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        return _parse_list_to_table(data)
    return None


def _parse_dict_to_table(data):
    """解析字典数据为表格"""
    table_data = {'headers': [], 'rows': []}
    
    # 处理 describe 统计结果
    if 'describe' in data and isinstance(data['describe'], dict):
        stats = data['describe']
        table_data['headers'] = ['统计指标', '数值']
        
        for key, value in stats.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    val_str = str(round(sub_value, 2)) if isinstance(sub_value, (int, float)) else str(sub_value)
                    table_data['rows'].append([str(sub_key), val_str])
            else:
                val_str = str(round(value, 2)) if isinstance(value, (int, float)) else str(value)
                table_data['rows'].append([str(key), val_str])
        
        return table_data if table_data['rows'] else None
    
    # 处理 head 数据
    if 'head' in data and isinstance(data['head'], dict):
        headers = list(data['head'].keys())
        table_data['headers'] = headers
        
        if headers:
            first_val = data['head'][headers[0]]
            if isinstance(first_val, list):
                num_rows = len(first_val)
                for i in range(num_rows):
                    row = []
                    for h in headers:
                        val = data['head'][h]
                        if isinstance(val, list) and i < len(val):
                            row.append(str(val[i])[:60])
                        else:
                            row.append('-')
                    table_data['rows'].append(row)
        
        return table_data if table_data['rows'] else None
    
    # 处理普通字典
    if data:
        table_data['headers'] = ['指标', '数值']
        for key, value in data.items():
            if not isinstance(value, (dict, list)):
                val_str = str(round(value, 2)) if isinstance(value, (int, float)) else str(value)
                table_data['rows'].append([str(key)[:40], val_str[:60]])
        return table_data if table_data['rows'] else None
    
    return None


def _parse_list_to_table(data):
    """解析列表数据为表格"""
    if not data or len(data) == 0:
        return None
    
    table_data = {'headers': [], 'rows': []}
    
    headers = list(data[0].keys())
    table_data['headers'] = headers
    
    for item in data:
        row = []
        for h in headers:
            val = item.get(h, '-')
            if isinstance(val, (int, float)):
                val = round(val, 2)
            row.append(str(val)[:60])
        table_data['rows'].append(row)
    
    return table_data if table_data['rows'] else None


def _format_table_markdown(table_data):
    """将表格数据格式化为 Markdown"""
    if not table_data.get('headers') or not table_data.get('rows'):
        return None
    
    lines = []
    
    header_line = "| " + " | ".join(str(h) for h in table_data['headers']) + " |"
    lines.append(header_line)
    
    separator = "|" + "|".join(["---" for _ in table_data['headers']]) + "|"
    lines.append(separator)
    
    for row in table_data['rows']:
        row_line = "| " + " | ".join(str(cell) for cell in row) + " |"
        lines.append(row_line)
    
    return "\n".join(lines)


def _analyze_business_metrics(dfs):
    """分析业务指标 - 自动过滤空值和零值"""
    import pandas as pd
    import numpy as np
    
    metrics = []
    
    for table_name, df in dfs.items():
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        for col in numeric_cols:
            # 过滤空值和零值
            col_data = df[col].dropna()
            col_data = col_data[col_data != 0]
            
            if len(col_data) > 0:
                metrics.append({
                    '指标名称': col,
                    '所属表': table_name,
                    '记录数': len(col_data),
                    '汇总值': round(col_data.sum(), 2),
                    '平均值': round(col_data.mean(), 2),
                    '最大值': round(col_data.max(), 2),
                    '最小值': round(col_data.min(), 2),
                    '标准差': round(col_data.std(), 2) if len(col_data) > 1 else 0
                })
    
    return metrics


def _analyze_categories(dfs):
    """分析分类数据 - 自动过滤空值和零值"""
    import pandas as pd
    
    categories = []
    
    for table_name, df in dfs.items():
        for col in df.columns:
            # 过滤空值和零值
            col_data = df[col].dropna()
            col_data = col_data[col_data != 0]
            col_data = col_data[col_data != '0']
            col_data = col_data[col_data != '']
            
            if len(col_data) > 0 and col_data.dtype == 'object':
                unique_count = col_data.nunique()
                if unique_count <= 20:
                    value_counts = col_data.value_counts()
                    categories.append({
                        '字段名': col,
                        '表名': table_name,
                        '类别数': unique_count,
                        '分布详情': ', '.join([f"{k}({v})" for k, v in value_counts.head(5).items()])
                    })
    
    return categories


def generate_markdown_report(agent_result, dfs, sheet_name):
    """生成业务分析报告 - 完整显示每个步骤的数据和分析"""
    import pandas as pd
    
    if isinstance(dfs, pd.DataFrame):
        dfs = {"default": dfs}
    
    is_multi_table = len(dfs) > 1
    
    if is_multi_table:
        table_list = ", ".join([f"{name}" for name in dfs.keys()])
    else:
        table_list = sheet_name
    
    # 提取所有步骤的完整数据
    step_data_list = _extract_all_step_data(agent_result)
    business_metrics = _analyze_business_metrics(dfs)
    categories = _analyze_categories(dfs)
    
    report = f"""业务数据分析报告

分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析对象: {table_list}

"""

    # 第一部分：业务指标汇总
    report += "一、业务指标汇总\n\n"
    
    if business_metrics:
        report += "业务指标统计表\n\n"
        report += "| 指标名称 | 所属表 | 记录数 | 汇总值 | 平均值 | 最大值 | 最小值 | 标准差 |\n"
        report += "|:--------|:------|------:|-------:|-------:|-------:|-------:|-------:|\n"
        
        for metric in business_metrics:
            report += f"| {metric['指标名称']} | {metric['所属表']} | {metric['记录数']} | {metric['汇总值']} | {metric['平均值']} | {metric['最大值']} | {metric['最小值']} | {metric['标准差']} |\n"
        
        report += "\n"

    if categories:
        report += "分类数据统计表\n\n"
        report += "| 字段名 | 表名 | 类别数 | 分布详情 |\n"
        report += "|:------|:------|------:|:--------|\n"
        
        for cat in categories:
            report += f"| {cat['字段名']} | {cat['表名']} | {cat['类别数']} | {cat['分布详情']} |\n"
        
        report += "\n"

    # 第二部分：详细步骤分析（完整显示每个步骤）
    report += "二、详细分析过程\n\n"
    
    valid_steps = [s for s in step_data_list if s['action'] not in ['error', 'final_response']]
    
    for step_data in valid_steps:
        step_num = step_data['step_num']
        action = step_data['action']
        
        report += f"分析步骤 {step_num}: {action}\n\n"
        
        # 显示解析的表格数据
        if step_data['parsed_table']:
            formatted = _format_table_markdown(step_data['parsed_table'])
            if formatted:
                report += f"{formatted}\n\n"
        
        # 显示工具执行结果（文本格式）
        if step_data['tool_result'] and isinstance(step_data['tool_result'], str):
            result_text = step_data['tool_result'].strip()
            if result_text and len(result_text) > 10:
                # 如果结果不是表格格式，显示文本摘要
                if not step_data['parsed_table']:
                    report += f"分析结果:\n{result_text[:800]}\n\n"
        
        # 显示AI的观察结论
        if step_data['observation']:
            observation = step_data['observation'].strip()
            if observation:
                report += f"结论: {observation[:500]}\n\n"
        
        report += "---\n\n"

    # 第三部分：业务洞察总结
    report += "三、业务洞察总结\n\n"
    
    if agent_result.final_report:
        report += agent_result.final_report + "\n\n"

    # 第四部分：结论与建议
    report += "四、结论与建议\n\n"
    
    report += "核心发现\n\n"
    
    findings = []
    if business_metrics:
        findings.append(f"共分析 {len(business_metrics)} 个业务指标")
    if categories:
        findings.append(f"识别 {len(categories)} 个分类维度")
    if valid_steps:
        findings.append(f"完成 {len(valid_steps)} 个分析步骤")
    
    for finding in findings:
        report += f"- {finding}\n"
    
    report += "\n行动建议\n\n"
    
    actions = [
        "持续监控业务指标变化趋势",
        "深入分析分类数据的业务含义",
        "定期评估业务运营状况",
        "基于数据洞察优化业务策略"
    ]
    
    for i, action in enumerate(actions, 1):
        report += f"{i}. {action}\n"

    report += f"""

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析工具: AI Excel 数据分析助手

"""

    return report


def generate_word_report(agent_result, dfs, sheet_name):
    """生成业务分析Word报告 - 完整显示每个步骤的数据和分析"""
    import pandas as pd
    
    if isinstance(dfs, pd.DataFrame):
        dfs = {"default": dfs}
    
    is_multi_table = len(dfs) > 1
    
    if is_multi_table:
        table_list = ", ".join([f"{name}" for name in dfs.keys()])
    else:
        table_list = sheet_name
    
    doc = Document()
    
    def set_chinese_font(run, font_name='Microsoft YaHei', font_size=12):
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    
    title = doc.add_heading('业务数据分析报告', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        set_chinese_font(run, 'Microsoft YaHei', 22)
    
    doc.add_paragraph(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph(f"分析对象: {table_list}")
    doc.add_paragraph()
    
    # 提取所有步骤的完整数据
    step_data_list = _extract_all_step_data(agent_result)
    business_metrics = _analyze_business_metrics(dfs)
    categories = _analyze_categories(dfs)
    
    # 第一部分：业务指标汇总
    doc.add_heading('一、业务指标汇总', level=1)
    
    if business_metrics:
        doc.add_paragraph('业务指标统计表')
        
        metric_table = doc.add_table(rows=len(business_metrics)+1, cols=8)
        metric_table.style = 'Light Grid Accent 1'
        metric_table.rows[0].cells[0].text = '指标名称'
        metric_table.rows[0].cells[1].text = '所属表'
        metric_table.rows[0].cells[2].text = '记录数'
        metric_table.rows[0].cells[3].text = '汇总值'
        metric_table.rows[0].cells[4].text = '平均值'
        metric_table.rows[0].cells[5].text = '最大值'
        metric_table.rows[0].cells[6].text = '最小值'
        metric_table.rows[0].cells[7].text = '标准差'
        
        for i, metric in enumerate(business_metrics, 1):
            metric_table.rows[i].cells[0].text = metric['指标名称']
            metric_table.rows[i].cells[1].text = metric['所属表']
            metric_table.rows[i].cells[2].text = str(metric['记录数'])
            metric_table.rows[i].cells[3].text = str(metric['汇总值'])
            metric_table.rows[i].cells[4].text = str(metric['平均值'])
            metric_table.rows[i].cells[5].text = str(metric['最大值'])
            metric_table.rows[i].cells[6].text = str(metric['最小值'])
            metric_table.rows[i].cells[7].text = str(metric['标准差'])
        
        doc.add_paragraph()
    
    if categories:
        doc.add_paragraph('分类数据统计表')
        
        cat_table = doc.add_table(rows=len(categories)+1, cols=4)
        cat_table.style = 'Light Grid Accent 1'
        cat_table.rows[0].cells[0].text = '字段名'
        cat_table.rows[0].cells[1].text = '表名'
        cat_table.rows[0].cells[2].text = '类别数'
        cat_table.rows[0].cells[3].text = '分布详情'
        
        for i, cat in enumerate(categories, 1):
            cat_table.rows[i].cells[0].text = cat['字段名']
            cat_table.rows[i].cells[1].text = cat['表名']
            cat_table.rows[i].cells[2].text = str(cat['类别数'])
            cat_table.rows[i].cells[3].text = cat['分布详情']
        
        doc.add_paragraph()
    
    # 第二部分：详细步骤分析
    doc.add_heading('二、详细分析过程', level=1)
    
    valid_steps = [s for s in step_data_list if s['action'] not in ['error', 'final_response']]
    
    for step_data in valid_steps:
        step_num = step_data['step_num']
        action = step_data['action']
        
        doc.add_paragraph(f"分析步骤 {step_num}: {action}")
        
        # 显示解析的表格数据
        if step_data['parsed_table']:
            table = step_data['parsed_table']
            if table.get('headers') and table.get('rows'):
                num_cols = len(table['headers'])
                num_rows = len(table['rows']) + 1
                
                step_table = doc.add_table(rows=num_rows, cols=num_cols)
                step_table.style = 'Light Grid Accent 1'
                
                for col_idx, header in enumerate(table['headers']):
                    step_table.rows[0].cells[col_idx].text = str(header)
                
                for row_idx, row in enumerate(table['rows']):
                    for col_idx, cell in enumerate(row):
                        if col_idx < num_cols:
                            step_table.rows[row_idx + 1].cells[col_idx].text = str(cell)[:60]
                
                doc.add_paragraph()
        
        # 显示工具执行结果
        if step_data['tool_result'] and isinstance(step_data['tool_result'], str):
            result_text = step_data['tool_result'].strip()
            if result_text and len(result_text) > 10 and not step_data['parsed_table']:
                doc.add_paragraph(f"分析结果: {result_text[:600]}")
        
        # 显示AI的观察结论
        if step_data['observation']:
            observation = step_data['observation'].strip()
            if observation:
                doc.add_paragraph(f"结论: {observation[:400]}")
        
        doc.add_paragraph()
    
    # 第三部分：业务洞察总结
    doc.add_heading('三、业务洞察总结', level=1)
    doc.add_paragraph(agent_result.final_report[:3000])
    
    # 第四部分：结论与建议
    doc.add_heading('四、结论与建议', level=1)
    
    doc.add_paragraph('核心发现')
    
    findings = []
    if business_metrics:
        findings.append(f"共分析 {len(business_metrics)} 个业务指标")
    if categories:
        findings.append(f"识别 {len(categories)} 个分类维度")
    if valid_steps:
        findings.append(f"完成 {len(valid_steps)} 个分析步骤")
    
    for finding in findings:
        doc.add_paragraph(f"- {finding}")
    
    doc.add_paragraph()
    doc.add_paragraph('行动建议')
    
    actions = [
        "持续监控业务指标变化趋势",
        "深入分析分类数据的业务含义",
        "定期评估业务运营状况",
        "基于数据洞察优化业务策略"
    ]
    
    for i, action in enumerate(actions, 1):
        doc.add_paragraph(f"{i}. {action}")
    
    doc.add_paragraph()
    doc.add_paragraph(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc.add_paragraph("分析工具: AI Excel 数据分析助手")
    
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    
    return doc_io
