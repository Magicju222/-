import streamlit as st
import pandas as pd
import os
import struct
import io
import traceback
from cleaner import ExcelCleaner
from i18n import t
import ui
import auth
import services
import time
from admin import show_admin_panel, check_admin_access


def validate_file_type(file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """
    验证文件真实类型（通过文件头魔数）
    返回: (是否有效, 错误信息)
    """
    # 定义文件类型魔数
    FILE_SIGNATURES = {
        'xlsx': (b'\x50\x4b\x03\x04', b'\x50\x4b\x05\x06', b'\x50\x4b\x07\x08'),  # ZIP格式（Excel）
        'xls': (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',),  # OLE格式（旧版Excel）
        'csv': (b'\xef\xbb\xbf', b'\xff\xfe', b'\xfe\xff', b'')  # UTF-8/UTF-16 BOM 或无BOM
    }
    
    # 获取文件扩展名
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext not in FILE_SIGNATURES:
        return False, f"不支持的文件类型: .{ext}"
    
    # 检查文件头
    expected_signatures = FILE_SIGNATURES[ext]
    file_header = file_bytes[:8]  # 读取前8字节
    
    # CSV文件可以是任意文本，检查是否包含二进制数据
    if ext == 'csv':
        try:
            # 尝试解码为文本
            file_bytes.decode('utf-8')
            return True, ""
        except UnicodeDecodeError:
            return False, "CSV文件包含非文本数据，可能不是有效的CSV文件"
    
    # 检查Excel文件魔数
    if ext in ['xlsx', 'xls']:
        if not any(file_header.startswith(sig) for sig in expected_signatures):
            return False, f"文件内容不匹配.{ext}格式，可能不是有效的Excel文件"
    
    return True, ""

# Page Config (Must be first)
st.set_page_config(
    page_title="AI Excel Cleaner",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Session State Initialization
if 'lang' not in st.session_state:
    st.session_state.lang = 'zh'
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'raw_preview' not in st.session_state:
    st.session_state.raw_preview = None
# Track uploaded file to detect changes
if 'last_uploaded_file_id' not in st.session_state:
    st.session_state.last_uploaded_file_id = None
# Track if user guide has been clicked
if 'guide_clicked' not in st.session_state:
    st.session_state.guide_clicked = False
# Track admin panel visibility
if 'show_admin_panel' not in st.session_state:
    st.session_state.show_admin_panel = False
# Track AI analyzer visibility
if 'show_analyzer' not in st.session_state:
    st.session_state.show_analyzer = False

# Load CSS
ui.load_css()

# Callback to handle file upload
def handle_file_upload():
    """Callback to handle file upload"""
    # Reset states when new file is uploaded
    st.session_state.cleaned_data = None
    st.session_state.raw_preview = None
    st.session_state.show_analyzer = False
    # Clean up all manual structure states
    keys_to_remove = [k for k in st.session_state.keys() if 'header_rows' in k or 'data_start_row' in k or 'key_columns' in k or 'selected_sheets' in k or 'preview_df_' in k or 'data_end_row' in k or 'data_end_col' in k or 'select_mode' in k]
    for k in keys_to_remove:
        del st.session_state[k]
    # Clear caches
    if 'cached_raw_df' in st.session_state:
        del st.session_state.cached_raw_df
    if 'cached_sheet_names' in st.session_state:
        del st.session_state.cached_sheet_names

# Authentication Check - TEMPORARILY DISABLED FOR TESTING
# if not auth.check_auth():
#     auth.show_login_page()
#     st.stop()
# Auto-login for testing
if 'user' not in st.session_state:
    from types import SimpleNamespace
    st.session_state.user = SimpleNamespace(email='test@example.com', id='test-user-id')

# Initialize Services and Config
supabase = auth.init_supabase()
config_service = services.ConfigService(supabase) if supabase else None
log_service = services.LogService(supabase) if supabase else None

# Load System Config with caching to improve performance
@st.cache_data(ttl=60)  # Cache for 1 minute (reduced for faster sync)
def get_cached_config(_service):
    if _service:
        return _service.get_system_config()
    # Return default config for testing when supabase is not available
    return {
        "SYSTEM_NOTICE": "",
        "MAX_FILE_SIZE": "50",
        "ALLOWED_FILE_TYPES": "xlsx,xls,csv",
        "DEFAULT_SEPARATOR": " / ",
        "ENABLE_AI_ANALYSIS": "true"
    }

# Initialize system config in session state
if 'system_config' not in st.session_state:
    st.session_state.system_config = get_cached_config(config_service)

# Track config version for detecting updates from other sessions
if 'config_version' not in st.session_state:
    st.session_state.config_version = 0

# Check if config was updated from admin panel (via config_last_updated timestamp)
config_updated = False
if 'config_last_updated' in st.session_state:
    last_update = st.session_state.config_last_updated
    if 'last_seen_config_update' not in st.session_state:
        st.session_state.last_seen_config_update = last_update
        config_updated = True
    elif st.session_state.last_seen_config_update != last_update:
        st.session_state.last_seen_config_update = last_update
        config_updated = True

# Refresh config if needed (either not loaded or was updated)
if config_updated or not st.session_state.system_config:
    with st.spinner("🔄 正在同步最新配置..."):
        fresh_config = get_cached_config(config_service)
        if fresh_config:
            st.session_state.system_config = fresh_config
            st.session_state.config_version += 1
        else:
            st.error("❌ 配置同步失败，请刷新页面重试")

system_config = st.session_state.system_config

# --- Cached Helper Functions ---
def get_file_hash(file_bytes: bytes) -> str:
    """计算文件哈希值（用于缓存键）- 只取前8KB以提高性能"""
    import hashlib
    # 对于大文件，只取前8KB计算哈希，平衡性能和准确性
    sample = file_bytes[:8192] if len(file_bytes) > 8192 else file_bytes
    return hashlib.md5(sample).hexdigest()

@st.cache_data(show_spinner=False, max_entries=10)  # 限制缓存条目数
def cached_get_sheet_names(file_hash: str, file_name: str, file_size: int):
    """Cache sheet names based on file hash and name.
    
    Args:
        file_hash: 文件内容的MD5哈希值（前8KB）
        file_name: 文件名
        file_size: 文件大小（用于确保唯一性）
    """
    # 注意：实际的字节数据需要从session_state或其他地方获取
    # 这里我们使用哈希作为键，实际数据存储在session_state中
    if 'uploaded_file_bytes' not in st.session_state:
        return []
    
    import io
    cleaner = ExcelCleaner()
    file_bytes = st.session_state.uploaded_file_bytes
    file_io = io.BytesIO(file_bytes)
    file_io.name = file_name
    return cleaner.get_sheet_names(file_io)

@st.cache_data(show_spinner=False)
def cached_load_preview(file_bytes, file_name, sheet_name):
    """Cache the first 100 rows of a sheet."""
    import io
    cleaner = ExcelCleaner()
    file_io = io.BytesIO(file_bytes)
    file_io.name = file_name
    full_df = cleaner.load_and_fill_merged_cells(file_io, sheet_name=sheet_name)
    preview_df = full_df.head(100).fillna("").astype(str)
    
    # Explicitly clear memory
    del full_df
    import gc
    gc.collect()
    
    return preview_df


# AI数据分析界面
def render_ai_analysis_interface():
    """渲染AI数据分析界面"""
    st.markdown("---")
    st.header("🔮 AI驱动数据分析")
    
    # 导入必要的模块
    try:
        from analyzer import DataAnalyzer
        from llm_client import LLMClient
        from ai_visualizer.chart_generator import ChartGenerator
        from document_generator.word_generator import WordDocumentGenerator
        from document_generator.ppt_generator import PPTDocumentGenerator
    except ImportError as e:
        st.error(f"模块导入失败: {str(e)}")
        return
    
    # 获取清洗后的数据
    cleaned_data = st.session_state.cleaned_data
    if not cleaned_data:
        st.warning("请先完成数据清洗")
        return
    
    # 选择工作表（支持多选）
    sheet_names = list(cleaned_data.keys())
    if len(sheet_names) > 1:
        selected_sheets = st.multiselect(
            "选择要分析的工作表（可多选）",
            sheet_names,
            default=sheet_names[:1] if sheet_names else None,
            help="选择多个工作表进行综合分析，AI将分析所有选中工作表之间的数据关联"
        )
    else:
        selected_sheets = sheet_names
    
    if not selected_sheets:
        st.warning("请至少选择一个工作表进行分析")
        return
    
    # 生成 selected_sheet 变量
    if len(selected_sheets) == 1:
        selected_sheet = selected_sheets[0]
    else:
        selected_sheet = "_".join(selected_sheets)
    
    # 显示已保存的分析结果（如果存在）
    if (st.session_state.get('agent_result') and 
        st.session_state.get('selected_sheet') == selected_sheet and
        st.session_state.get('agent_dfs')):
        
        agent_result = st.session_state.agent_result
        stored_dfs = st.session_state.agent_dfs
        
        st.write("## 📊 Agent 智能分析结果")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("执行步骤", len(agent_result.steps))
        with col2:
            st.metric("生成代码", len(agent_result.generated_code))
        with col3:
            st.metric("生成图表", len(agent_result.visualizations))
        with col4:
            st.metric("关键洞察", len(agent_result.insights))
        
        if agent_result.visualizations:
            st.write("### 📈 数据可视化")
            chart_cols = st.columns(min(len(agent_result.visualizations), 3))
            for i, path in enumerate(agent_result.visualizations):
                if os.path.exists(path):
                    with chart_cols[i % 3]:
                        st.image(path, use_container_width=True)
        
        st.write("### 📄 分析报告")
        st.markdown(agent_result.final_report)
        
        st.write("### 📥 导出报告")
        
        # 使用增强版报告生成器
        from enhanced_report_generator import (
            generate_enhanced_reports,
            generate_enhanced_word_report,
            generate_enhanced_excel_report
        )
        
        # 生成增强版报告（直接从Agent结果中提取完整数据）
        md_report, word_report, excel_report = generate_enhanced_reports(
            agent_result, 
            sheet_name=selected_sheet
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="📄 下载 Markdown 报告",
                data=md_report,
                file_name=f"analysis_report_{selected_sheet}.md",
                mime="text/markdown"
            )
        with col2:
            st.download_button(
                label="📝 下载 Word 报告",
                data=word_report.getvalue(),
                file_name=f"analysis_report_{selected_sheet}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        with col3:
            if excel_report:
                st.download_button(
                    label="📊 下载 Excel 报告",
                    data=excel_report,
                    file_name=f"analysis_report_{selected_sheet}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.button("📊 下载 Excel 报告", disabled=True)
        
        if st.button("🔄 重新分析", type="secondary"):
            del st.session_state.agent_result
            del st.session_state.selected_sheet
            if 'agent_dfs' in st.session_state:
                del st.session_state.agent_dfs
            st.rerun()
        
        st.markdown("---")
        st.info("💡 如需重新分析，请点击上方「重新分析」按钮")
        return
    
    # 合并多表数据用于分析
    dfs = {name: cleaned_data[name] for name in selected_sheets}
    
    if len(selected_sheets) == 1:
        df = dfs[selected_sheet]
    else:
        import pandas as pd
        df = pd.concat(dfs.values(), ignore_index=True)
    
    # 分析模板上传（可选）
    with st.expander("📄 上传分析模板（可选）", expanded=False):
        st.markdown("""
        **说明**：上传以往的分析报告作为格式参考模板
        - 支持格式：Word (.docx)、PDF (.pdf)、图片 (.png, .jpg, .jpeg)
        - 系统会提取模板的分析维度和格式作为参考
        """)
        
        template_file = st.file_uploader(
            "选择模板文件",
            type=['docx', 'pdf', 'png', 'jpg', 'jpeg'],
            key="template_upload",
            help="上传Word、PDF或图片格式的分析报告模板"
        )
        
        template_dimensions = []
        if template_file:
            st.info("正在解析模板...")
            try:
                # 读取模板内容
                if template_file.type in ['application/pdf']:
                    template_content = "PDF模板已上传"
                elif template_file.type in ['image/png', 'image/jpeg']:
                    template_content = "图片模板已上传"
                else:
                    template_content = "Word模板已上传"
                
                # 提取维度
                llm_client = LLMClient()
                analyzer = DataAnalyzer(llm_client)
                template_dimensions = analyzer.extract_dimensions_from_template(template_content)
                
                if template_dimensions:
                    st.success(f"从模板提取到 {len(template_dimensions)} 个分析维度")
                    st.write("模板维度:", template_dimensions)
                else:
                    st.warning("未能从模板中提取分析维度")
            except Exception as e:
                st.error(f"模板解析失败: {str(e)}")
    
    # 选择分析模式
    analysis_mode = st.radio(
        "选择分析模式",
        options=["传统分析", "Agent智能分析"],
        help="传统分析：按固定步骤执行分析 | Agent智能分析：AI自主决定分析步骤和工具调用",
        horizontal=True
    )
    
    # 业务背景描述
    context = st.text_area(
        "业务背景描述（可选）",
        placeholder="请描述数据的业务背景、分析目标等...",
        key="analysis_context"
    )
    
    # 用户自定义维度
    user_dimensions_input = st.text_area(
        "自定义分析维度（可选，每行一个）",
        placeholder="例如：\n时间趋势分析\n用户行为分析\n产品对比分析",
        key="user_dimensions"
    )
    user_dimensions = [d.strip() for d in user_dimensions_input.split('\n') if d.strip()]
    
    # 分析执行按钮
    if st.button("🚀 开始AI分析", type="primary", use_container_width=True):
        # 使用 st.status 显示实时进度
        with st.status("🤖 AI正在深度分析中，请稍候...", expanded=True) as status:
            try:
                # Agent 智能分析模式
                if analysis_mode == "Agent智能分析":
                    st.write("🤖 启动 Agent 智能分析模式...")
                    
                    from agent_analyzer import AgentAnalyzer
                    
                    # 初始化 Agent 分析器
                    agent_analyzer = AgentAnalyzer()
                    
                    # 创建实时显示区域
                    st.write("### 📋 实时分析过程")
                    progress_text = st.empty()
                    steps_container = st.container()
                    
                    # 用于存储步骤的列表
                    step_placeholders = []
                    
                    def step_callback(step):
                        """每执行一步就实时显示"""
                        with steps_container:
                            # 根据步骤状态选择显示样式
                            if step.action == "error":
                                with st.expander(f"❌ 步骤 {step.step_number}: {step.action}", expanded=True):
                                    st.error(f"错误: {step.observation[:300]}")
                            elif step.tool_result and step.tool_result.success:
                                with st.expander(f"✅ 步骤 {step.step_number}: {step.action}", expanded=False):
                                    if step.thought:
                                        st.info(f"**思考过程:**\n{step.thought}")
                                    if step.action == "execute_python" and step.tool_result.success:
                                        st.code(step.tool_result.result[:500], language="python")
                                    elif step.action == "generate_visualization" and step.tool_result.success:
                                        if os.path.exists(step.tool_result.result):
                                            st.image(step.tool_result.result)
                                    else:
                                        st.text(step.observation[:500])
                            else:
                                with st.expander(f"ℹ️ 步骤 {step.step_number}: {step.action}", expanded=False):
                                    if step.thought:
                                        st.info(step.thought)
                                    st.text(step.observation[:300])
                    
                    # 执行 Agent 分析（带实时回调）
                    agent_result = agent_analyzer.analyze(dfs, context, step_callback=step_callback)
                    
                    # 显示最终分析结果
                    st.write("## 📊 Agent 智能分析结果")
                    
                    # 显示关键指标卡片
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("执行步骤", len(agent_result.steps))
                    with col2:
                        st.metric("生成代码", len(agent_result.generated_code))
                    with col3:
                        st.metric("生成图表", len(agent_result.visualizations))
                    with col4:
                        st.metric("关键洞察", len(agent_result.insights))
                    
                    # 显示生成的图表
                    if agent_result.visualizations:
                        st.write("### 📈 数据可视化")
                        chart_cols = st.columns(min(len(agent_result.visualizations), 3))
                        for i, path in enumerate(agent_result.visualizations):
                            if os.path.exists(path):
                                with chart_cols[i % 3]:
                                    st.image(path, use_container_width=True)
                    
                    # 显示最终报告
                    st.write("### 📄 分析报告")
                    report_container = st.container()
                    with report_container:
                        st.markdown(agent_result.final_report)
                    
                    # 生成可下载的报告文档
                    st.write("### 📥 导出报告")
                    
                    # 使用报告生成器生成报告
                    from report_generator import generate_markdown_report, generate_word_report
                    
                    # 生成报告
                    md_report = generate_markdown_report(agent_result, dfs, selected_sheet)
                    word_report = generate_word_report(agent_result, dfs, selected_sheet)
                    
                    # 保存报告到session_state，确保下载按钮在页面重新运行后仍然显示
                    st.session_state.agent_md_report = md_report
                    st.session_state.agent_word_report = word_report.getvalue()
                    st.session_state.agent_report_filename = f"analysis_report_{selected_sheet}"
                    
                    # 保存结果
                    st.session_state.agent_result = agent_result
                    st.session_state.selected_sheet = selected_sheet
                    st.session_state.agent_dfs = dfs
                    
                    status.update(label="✅ Agent 分析完成！", state="complete")
                    st.success("✅ Agent 智能分析完成！报告和图表已生成。")
                
                # 显示下载按钮（在条件外部，确保页面重新运行后仍然显示）
                if 'agent_md_report' in st.session_state:
                    st.subheader("📥 下载报告")
                    
                    # 生成Excel报告
                    if 'agent_excel_report' not in st.session_state and 'agent_dfs' in st.session_state and 'selected_sheet' in st.session_state:
                        try:
                            from business_report_excel import generate_excel_report
                            selected_sheet = st.session_state.selected_sheet
                            if selected_sheet in st.session_state.agent_dfs:
                                df_for_excel = st.session_state.agent_dfs[selected_sheet]
                                excel_report_data = generate_excel_report(
                                    df_for_excel, 
                                    title=f"业务分析报告 - {selected_sheet}"
                                )
                                if excel_report_data:
                                    st.session_state.agent_excel_report = excel_report_data
                                else:
                                    st.warning("⚠️ Excel报告生成失败，请检查数据")
                        except Exception as e:
                            st.warning(f"⚠️ Excel报告生成失败: {str(e)}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            label="📄 下载 Markdown 报告",
                            data=st.session_state.agent_md_report,
                            file_name=f"{st.session_state.agent_report_filename}.md",
                            mime="text/markdown",
                            key="agent_download_md"
                        )
                    with col2:
                        st.download_button(
                            label="📝 下载 Word 报告",
                            data=st.session_state.agent_word_report,
                            file_name=f"{st.session_state.agent_report_filename}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="agent_download_word"
                        )
                    with col3:
                        if 'agent_excel_report' in st.session_state and st.session_state.agent_excel_report:
                            st.download_button(
                                label="📊 下载 Excel 报告",
                                data=st.session_state.agent_excel_report,
                                file_name=f"{st.session_state.agent_report_filename}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="agent_download_excel"
                            )
                        else:
                            st.button("📊 下载 Excel 报告", disabled=True, key="agent_download_excel_disabled")
                
                else:
                    # 传统分析模式
                    # 初始化组件
                    st.write("📡 正在初始化 AI 客户端...")
                    llm_client = LLMClient()
                    analyzer = DataAnalyzer(llm_client)
                    
                    # 创建进度容器
                    progress_container = st.container()
                    
                    # 步骤1: 数据理解与预处理
                    with progress_container:
                        st.write("📊 **步骤 1/5**: 数据理解与预处理...")
                    preprocessing = analyzer._data_understanding_and_preprocessing(df)
                    with progress_container:
                        # 从 structure_understanding 中获取列信息
                        structure = preprocessing.get('structure_understanding', {})
                        columns = structure.get('columns', [])
                        # 如果没有返回列信息，使用原始数据的列
                        if not columns and hasattr(df, 'columns'):
                            columns = list(df.columns)
                        st.write(f"   ✅ 识别了 {len(columns)} 个字段，{len(df)} 行数据")
                    
                    # 步骤2: 分析维度处理
                    with progress_container:
                        st.write("🔍 **步骤 2/5**: 正在处理分析维度...")
                    merged_dims = analyzer._process_dimensions(
                        df, template_dimensions if template_dimensions else None, user_dimensions if user_dimensions else None
                    )
                    with progress_container:
                        template_count = len([d for d in merged_dims if d.source == 'template'])
                        ai_count = len([d for d in merged_dims if d.source == 'ai'])
                        user_count = len([d for d in merged_dims if d.source == 'user'])
                        st.write(f"   ✅ 共识别 {len(merged_dims)} 个维度（模板:{template_count}, AI:{ai_count}, 用户:{user_count}）")
                    
                    # 步骤3: 探索性数据分析
                    with progress_container:
                        st.write("📈 **步骤 3/5**: 探索性数据分析（EDA）...")
                    eda = analyzer._exploratory_data_analysis(df, preprocessing, merged_dims)
                    with progress_container:
                        st.write(f"   ✅ 完成数据分布分析和统计检验")
                    
                    # 步骤4: 深度分析与洞察
                    with progress_container:
                        st.write("💡 **步骤 4/5**: 深度分析与洞察挖掘...")
                    insights = analyzer._deep_analysis_and_insights(df, eda, merged_dims, context)
                    with progress_container:
                        st.write(f"   ✅ 生成 {len(insights)} 个关键洞察")
                    
                    # 步骤5: 生成可视化建议
                    with progress_container:
                        st.write("🎨 **步骤 5/5**: 生成可视化建议...")
                    viz_recommendations = analyzer._generate_visualization_recommendations(df, eda, insights, merged_dims)
                    with progress_container:
                        st.write(f"   ✅ 推荐 {len(viz_recommendations)} 种可视化方案")
                    
                    # 显示处理日志（用于调试）
                    with progress_container:
                        with st.expander("查看详细处理日志"):
                            for log in analyzer.processing_log:
                                st.text(log)
                    
                    # 构建完整结果
                    from analyzer import AnalysisResult
                    analysis_result = AnalysisResult(
                        preprocessing=preprocessing,
                        eda=eda,
                        insights=insights,
                        visualization_recommendations=viz_recommendations,
                        merged_dimensions=merged_dims,
                        processing_log=analyzer.processing_log
                    )
                    
                    # 保存分析结果到session state
                    st.session_state.analysis_result = analysis_result
                    st.session_state.selected_sheet = selected_sheet
                    
                    status.update(label="✅ AI 分析完成！", state="complete", expanded=False)
                    st.success("✅ 分析完成！请查看下方的分析结果。")
                
            except Exception as e:
                status.update(label="❌ 分析失败", state="error")
                st.error(f"分析失败: {str(e)}")
                # 仅在调试模式下显示详细错误信息
                if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
                    import traceback
                    st.error(traceback.format_exc())
                else:
                    st.info("💡 如果问题持续存在，请联系管理员或稍后重试。")
    
    # 显示分析结果
    if 'analysis_result' in st.session_state and st.session_state.selected_sheet == selected_sheet:
        result = st.session_state.analysis_result
        
        # 显示分析维度
        st.subheader("📊 分析维度")
        dim_cols = st.columns(3)
        
        template_dims = [d for d in result.merged_dimensions if d.source == 'template']
        ai_dims = [d for d in result.merged_dimensions if d.source == 'ai']
        user_dims = [d for d in result.merged_dimensions if d.source == 'user']
        
        with dim_cols[0]:
            st.write("**模板维度**")
            for dim in template_dims[:5]:
                st.write(f"• {dim.name}")
        
        with dim_cols[1]:
            st.write("**AI自动维度**")
            for dim in ai_dims[:5]:
                st.write(f"• {dim.name}")
        
        with dim_cols[2]:
            st.write("**用户维度**")
            for dim in user_dims[:5]:
                st.write(f"• {dim.name}")
        
        # 显示关键洞察
        st.subheader("💡 关键洞察")
        for i, insight in enumerate(result.insights[:5], 1):
            with st.expander(f"洞察 {i}: {insight.get('title', '')}"):
                st.write(insight.get('description', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**关键发现:**")
                    for finding in insight.get('key_findings', []):
                        st.write(f"• {finding}")
                
                with col2:
                    st.write("**行动建议:**")
                    st.write(insight.get('action', '继续监控'))
                
                # 显示维度来源
                source = insight.get('dimension_source', 'ai')
                source_label = {"template": "模板维度", "ai": "AI维度", "user": "用户维度"}.get(source, "AI维度")
                st.caption(f"维度来源: {source_label} | 置信度: {insight.get('confidence', '中')} | 优先级: {insight.get('priority', '中')}")
        
        # 生成AI图表
        st.subheader("📈 AI生成图表")
        
        # 显示可视化建议信息
        if result.visualization_recommendations:
            with st.expander("查看可视化建议"):
                for i, rec in enumerate(result.visualization_recommendations[:3], 1):
                    st.write(f"**建议 {i}:** {rec.get('title', '未命名')}")
                    st.write(f"   类型: {rec.get('chart_type', '未知')}")
                    st.write(f"   列: {rec.get('columns', [])}")
        else:
            st.warning("没有可用的可视化建议，将使用默认建议")
        
        if st.button("生成可视化图表", key="generate_charts"):
            with st.spinner("正在生成图表..."):
                try:
                    # 准备可视化建议
                    recommendations = result.visualization_recommendations or []
                    
                    # 如果没有建议，创建默认建议
                    if not recommendations:
                        st.info("创建默认可视化建议...")
                        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                        
                        if numeric_cols:
                            recommendations.append({
                                'chart_type': 'histogram',
                                'columns': [numeric_cols[0]],
                                'title': f'{numeric_cols[0]}分布'
                            })
                        if categorical_cols:
                            recommendations.append({
                                'chart_type': 'bar',
                                'columns': [categorical_cols[0]],
                                'title': f'{categorical_cols[0]}频次'
                            })
                        if len(numeric_cols) >= 2:
                            recommendations.append({
                                'chart_type': 'scatter',
                                'columns': numeric_cols[:2],
                                'title': f'{numeric_cols[0]} vs {numeric_cols[1]}'
                            })
                        
                        if not recommendations:
                            st.error("数据中没有可用于可视化的列（需要数值或类别列）")
                            return
                        
                        st.write(f"创建了 {len(recommendations)} 个默认建议")
                    
                    # 重新初始化 LLMClient
                    llm_client = LLMClient()
                    chart_gen = ChartGenerator(llm_client)
                    
                    # 逐个生成图表，显示详细进度
                    chart_paths = []
                    progress_bar = st.progress(0)
                    
                    for i, rec in enumerate(recommendations[:3]):
                        st.write(f"🎨 正在生成图表 {i+1}/{min(len(recommendations), 3)}: {rec.get('title', '未命名')}...")
                        try:
                            path = chart_gen.generate_chart_from_recommendation(df, rec)
                            if path:
                                chart_paths.append(path)
                                st.write(f"   ✅ 图表 {i+1} 生成成功: {path}")
                            else:
                                st.warning(f"   ⚠️ 图表 {i+1} 返回空路径")
                        except Exception as chart_error:
                            st.error(f"   ❌ 图表 {i+1} 生成失败: {str(chart_error)}")
                        progress_bar.progress((i + 1) / min(len(recommendations), 3))
                    
                    st.session_state.chart_paths = chart_paths
                    
                    # 显示图表
                    if chart_paths:
                        st.success(f"✅ 成功生成 {len(chart_paths)} 个图表")
                        for i, path in enumerate(chart_paths):
                            if path and os.path.exists(path):
                                st.image(path, caption=f"图表 {i+1}: {recommendations[i].get('title', '')}")
                            else:
                                st.warning(f"图表 {i+1} 文件不存在: {path}")
                    else:
                        st.error("没有生成任何图表，请检查上面的错误信息")
                    
                except Exception as e:
                    st.error(f"图表生成过程出错: {str(e)}")
                    # 仅在调试模式下显示详细错误信息
                    if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
                        import traceback
                        st.error(traceback.format_exc())
        
        # 文档下载
        st.subheader("📄 生成报告")
        col_word, col_ppt, col_excel = st.columns(3)
        
        with col_word:
            # 生成Word报告按钮
            if st.button("📘 生成Word报告", use_container_width=True, key="generate_word"):
                with st.spinner("正在生成Word文档..."):
                    try:
                        word_gen = WordDocumentGenerator()
                        chart_paths = st.session_state.get('chart_paths', [])
                        
                        word_doc = word_gen.generate(
                            result,
                            chart_images=chart_paths,
                            title=f"{selected_sheet} 数据分析报告"
                        )
                        
                        # 保存到session_state，这样页面重新运行后下载按钮仍然显示
                        st.session_state.word_doc = word_doc
                        st.session_state.word_filename = f"{selected_sheet}_数据分析报告.docx"
                        st.success("✅ Word报告生成成功！")
                    except Exception as e:
                        st.error(f"Word生成失败: {str(e)}")
            
            # 显示下载按钮（如果文档已生成）
            if 'word_doc' in st.session_state and st.session_state.word_doc:
                st.download_button(
                    "⬇️ 下载Word报告",
                    st.session_state.word_doc,
                    file_name=st.session_state.word_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="download_word"
                )
        
        with col_ppt:
            # 生成PPT报告按钮
            if st.button("📊 生成PPT报告", use_container_width=True, key="generate_ppt"):
                with st.spinner("正在生成PPT文档..."):
                    try:
                        ppt_gen = PPTDocumentGenerator()
                        chart_paths = st.session_state.get('chart_paths', [])
                        
                        ppt_doc = ppt_gen.generate(
                            result,
                            chart_images=chart_paths,
                            title=f"{selected_sheet} 数据分析汇报"
                        )
                        
                        # 保存到session_state
                        st.session_state.ppt_doc = ppt_doc
                        st.session_state.ppt_filename = f"{selected_sheet}_数据分析汇报.pptx"
                        st.success("✅ PPT报告生成成功！")
                    except Exception as e:
                        st.error(f"PPT生成失败: {str(e)}")
            
            # 显示下载按钮（如果文档已生成）
            if 'ppt_doc' in st.session_state and st.session_state.ppt_doc:
                st.download_button(
                    "⬇️ 下载PPT报告",
                    st.session_state.ppt_doc,
                    file_name=st.session_state.ppt_filename,
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                    use_container_width=True,
                    key="download_ppt"
                )
        
        with col_excel:
            # 生成Excel报告按钮
            if st.button("📈 生成Excel报告", use_container_width=True, key="generate_excel"):
                with st.spinner("正在生成Excel文档..."):
                    try:
                        from business_report_excel import generate_excel_report
                        
                        # 获取清洗后的数据
                        if selected_sheet in stored_dfs:
                            df_for_excel = stored_dfs[selected_sheet]
                            excel_doc = generate_excel_report(
                                df_for_excel,
                                title=f"{selected_sheet} 业务分析报告"
                            )
                            
                            # 保存到session_state
                            st.session_state.excel_doc = excel_doc
                            st.session_state.excel_filename = f"{selected_sheet}_业务分析报告.xlsx"
                            st.success("✅ Excel报告生成成功！")
                        else:
                            st.error("未找到数据，无法生成Excel报告")
                    except Exception as e:
                        st.error(f"Excel生成失败: {str(e)}")
            
            # 显示下载按钮（如果文档已生成）
            if 'excel_doc' in st.session_state and st.session_state.excel_doc:
                st.download_button(
                    "⬇️ 下载Excel报告",
                    st.session_state.excel_doc,
                    file_name=st.session_state.excel_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_excel"
                )


# Check Maintenance Mode
if system_config.get("MAINTENANCE_MODE") == "true":
    user_profile = st.session_state.get('user_profile') or {}
    if user_profile.get('role') not in ('admin', 'super_admin'):
        st.error("🔧 系统正在维护中，请稍后再试。")
        st.stop()

# Get User Profile
user_profile = st.session_state.get('user_profile') or {}

# If user is logged in but profile is empty or has no role, reload it from database
if st.session_state.get('user') and (not user_profile or not user_profile.get('role')):
    supabase = auth.init_supabase()
    if supabase:
        user_service = services.UserService(supabase)
        profile = user_service.get_profile(st.session_state.user.id)
        if profile:
            st.session_state.user_profile = profile
            user_profile = profile

is_admin = user_profile.get('role') in ('admin', 'super_admin')

# Show System Notice if configured
system_notice = system_config.get("SYSTEM_NOTICE", "").strip()
if system_notice:
    # Track dismissed notices
    if 'dismissed_notices' not in st.session_state:
        st.session_state.dismissed_notices = set()

    # Create a hash of the notice to track if it's been dismissed
    import hashlib
    notice_hash = hashlib.md5(system_notice.encode()).hexdigest()[:8]

    if notice_hash not in st.session_state.dismissed_notices:
        with st.container():
            col1, col2 = st.columns([10, 1])
            with col1:
                st.info(f"📢 系统公告: {system_notice}", icon="ℹ️")
            with col2:
                if st.button("✕", key=f"dismiss_notice_{notice_hash}"):
                    st.session_state.dismissed_notices.add(notice_hash)
                    st.rerun()

# Show Admin Panel if requested
if st.session_state.get('show_admin_panel', False):
    if check_admin_access():
        # Add back button
        if st.button("← 返回主页面"):
            st.session_state.show_admin_panel = False
            st.rerun()
        
        # Show admin panel
        show_admin_panel()
        
        # Stop here to not show main content
        st.stop()
    else:
        st.error("🚫 访问被拒绝：需要管理员权限")
        st.session_state.show_admin_panel = False

# Render Layout - Only if not in admin panel
api_key, settings = ui.render_sidebar()

# Admin Panel Button (only for admins)
if is_admin:
    with st.sidebar:
        st.divider()
        if st.button("⚙️ 管理面板", use_container_width=True):
            st.session_state.show_admin_panel = True
            st.rerun()

# Logout Button in Sidebar
with st.sidebar:
    st.divider()
    if st.button("🚪 Logout"):
        auth.logout()

# Only show navbar and hero if not in admin panel
if not st.session_state.get('show_admin_panel', False):
    ui.render_navbar()
    ui.render_hero()

# Main Controller Logic - Only show if not in admin panel
if not st.session_state.get('show_admin_panel', False):
    main_col1, main_col2, main_col3 = st.columns([1, 3, 1])

    with main_col2:
        # File Uploader Card
        with st.container(border=True):
            uploaded_file = st.file_uploader(
                "Upload Excel/CSV file", 
                type=['xlsx', 'xls', 'csv'], 
                label_visibility="collapsed",
                key="uploaded_file",
                on_change=handle_file_upload
            )

        # Show previous error if any
        if 'last_error' in st.session_state:
            with st.expander("上次错误信息", expanded=True):
                st.error(st.session_state['last_error'])
                if 'last_traceback' in st.session_state:
                    st.code(st.session_state['last_traceback'])
        
        if uploaded_file:
            # Check File Size Limit
            max_size_mb = int(system_config.get("MAX_FILE_SIZE_MB", 50))
            if uploaded_file.size > max_size_mb * 1024 * 1024:
                st.error(f"文件大小超过限制 ({max_size_mb}MB)。")
            else:
                try:
                    # 1. 验证文件类型（安全检查）
                    file_bytes = uploaded_file.getvalue()
                    is_valid, error_msg = validate_file_type(file_bytes, uploaded_file.name)
                    if not is_valid:
                        st.error(f"文件验证失败: {error_msg}")
                        st.stop()
                    
                    # 存储文件字节到session_state供缓存函数使用
                    st.session_state.uploaded_file_bytes = file_bytes
                    
                    cleaner = ExcelCleaner()
                
                    # 2. Get Sheet Names（使用文件哈希作为缓存键）
                    file_hash = get_file_hash(file_bytes)
                    sheet_names = cached_get_sheet_names(file_hash, uploaded_file.name, len(file_bytes))
                    
                    # 2. Sheet Selection
                    st.markdown(f"### {t('select_sheets')}")
                    selected_sheets = st.multiselect(
                        t("select_sheets"),
                        options=sheet_names,
                        default=sheet_names, # Default select all
                        label_visibility="collapsed",
                        key="selected_sheets_input"
                    )
                    
                    if not selected_sheets:
                        st.warning("Please select at least one sheet.")
                    else:
                        # 3. Tabbed Configuration
                        st.markdown(f"### {t('sheet_config')}")
                        tabs = st.tabs(selected_sheets)
                        
                        # Dictionary to store configs for each sheet
                        sheet_configs = {}
                        
                        for i, sheet in enumerate(selected_sheets):
                            with tabs[i]:
                                # Load specific sheet data preview using CACHE
                                preview_df = cached_load_preview(file_bytes, uploaded_file.name, sheet)
                                    
                                # Render Selector
                                # Use sheet name as key prefix for isolation
                                header_rows, data_start_row, key_columns, data_end_row, data_end_col = ui.render_interactive_structure_selector(
                                    preview_df, 
                                    key_prefix=f"sheet_{sheet}"
                                )
                                
                                sheet_configs[sheet] = {
                                    "header_rows": header_rows,
                                    "data_start_row": data_start_row,
                                    "key_columns": key_columns,
                                    "data_end_row": data_end_row,
                                    "data_end_col": data_end_col
                                }
                        
                        # Store sheet_configs in session state so callback can access it
                        st.session_state['sheet_configs'] = sheet_configs
                        st.session_state['selected_sheets'] = selected_sheets
                        # Don't store uploaded_file in session_state to avoid widget key conflict
                        # Store file bytes instead
                        st.session_state['uploaded_file_bytes'] = file_bytes
                        st.session_state['uploaded_file_name'] = uploaded_file.name
                        st.session_state['uploaded_file_size'] = uploaded_file.size
                        st.session_state['settings'] = settings
                        
                        # Action Button
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                        with col_btn2:
                            button_label = t("batch_clean_btn")
                            if st.button(
                                button_label,
                                use_container_width=True,
                                key="batch_clean_start_button",
                                type="primary"
                            ):
                                # Show processing message
                                st.info("正在处理，请稍候...")
                                
                                # Get data from session state
                                sheet_configs = st.session_state['sheet_configs']
                                selected_sheets = st.session_state['selected_sheets']
                                file_bytes = st.session_state['uploaded_file_bytes']
                                file_name = st.session_state['uploaded_file_name']
                                file_size = st.session_state['uploaded_file_size']
                                settings = st.session_state['settings']
                                
                                # Progress Animation
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                try:
                                    status_text.text(t("processing"))
                                    progress_bar.progress(10)
                                    
                                    sep = settings.get("sep_option", " / ")
                                    
                                    cleaned_results = {}
                                    total_sheets = len(selected_sheets)
                                    
                                    for idx, sheet in enumerate(selected_sheets):
                                        status_text.text(f"{t('cleaning')} - {sheet}")
                                        
                                        config = sheet_configs[sheet]
                                        
                                        # Clean Data
                                        start_time = time.time()
                                        # Create a new BytesIO for each sheet to ensure fresh file pointer
                                        file_obj = io.BytesIO(file_bytes)
                                        file_obj.name = file_name  # Set name for file type detection
                                        result = cleaner.clean_data(
                                            file_obj,
                                            header_rows=config["header_rows"],
                                            data_start_row=config["data_start_row"],
                                            key_columns=config["key_columns"],
                                            separator=sep,
                                            sheet_name=sheet,
                                            data_end_row=config.get("data_end_row"),
                                            data_end_col=config.get("data_end_col")
                                        )
                                        processing_time_ms = int((time.time() - start_time) * 1000)
                                        
                                        cleaned_results[sheet] = result['cleaned_df']
                                        
                                        # Log Success
                                        if log_service and st.session_state.user:
                                            log_service.log_cleaning_task(
                                                user_id=st.session_state.user.id,
                                                file_name=file_name,
                                                file_size=file_size,
                                                row_count=len(result['cleaned_df']),
                                                processing_time_ms=processing_time_ms,
                                                status='success'
                                            )
                                        
                                        # Update progress
                                        progress = int(10 + (idx + 1) / total_sheets * 80)
                                        progress_bar.progress(progress)
                                        
                                    # Store results (Dictionary of DFs)
                                    st.session_state.cleaned_data = cleaned_results
                                    st.session_state.raw_preview = None # Not applicable for batch
                                    
                                    progress_bar.progress(100)
                                    status_text.text(t("success"))
                                    st.success("清洗完成！")
                                    st.balloons()
                                    
                                except Exception as e:
                                    error_msg = f"处理出错: {str(e)}"
                                    st.session_state['last_error'] = error_msg
                                    st.session_state['last_traceback'] = traceback.format_exc()
                                    st.error(error_msg)
                                    st.error(traceback.format_exc())
                except Exception as e:
                    st.error(f"Failed to load file: {e}")

    # Render Results
    if st.session_state.cleaned_data is not None:
        st.markdown("---")
        st.markdown(f"### {t('preview_clean')}")
        
        # Display results in tabs
        result_sheets = list(st.session_state.cleaned_data.keys())
        res_tabs = st.tabs(result_sheets)
        
        for i, sheet in enumerate(result_sheets):
            with res_tabs[i]:
                st.dataframe(st.session_state.cleaned_data[sheet], height=400, use_container_width=True)
                
        # Download All
        st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
        col_dl1, col_dl2, col_dl3 = st.columns([1, 1, 1])
        with col_dl2:
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                for sheet, df in st.session_state.cleaned_data.items():
                    # Sheet name length limit in Excel is 31 chars
                    safe_sheet_name = sheet[:31]
                    df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
            st.download_button(
                label=t("download_btn"),
                data=buffer,
                file_name="cleaned_batch_data.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        
        # AI数据分析入口
        st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
        col_an1, col_an2, col_an3 = st.columns([1, 1, 1])
        with col_an2:
            if st.button("🔮 AI数据分析", type="primary", use_container_width=True):
                st.session_state.show_analyzer = True
                st.rerun()
        
        # 显示AI数据分析界面
        if st.session_state.get('show_analyzer'):
            render_ai_analysis_interface()
    else:
        # Placeholder or Instructions when no data
        if not uploaded_file:
            ui.render_no_file_instruction()
