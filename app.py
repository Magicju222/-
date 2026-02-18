import streamlit as st
import pandas as pd
import os
from cleaner import ExcelCleaner
from i18n import t
import ui
import auth
import services
import time
from admin import show_admin_panel, check_admin_access

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
    keys_to_remove = [k for k in st.session_state.keys() if 'header_rows' in k or 'data_start_row' in k or 'key_columns' in k or 'selected_sheets' in k or 'preview_df_' in k]
    for k in keys_to_remove:
        del st.session_state[k]
    # Clear caches
    if 'cached_raw_df' in st.session_state:
        del st.session_state.cached_raw_df
    if 'cached_sheet_names' in st.session_state:
        del st.session_state.cached_sheet_names

# Authentication Check
if not auth.check_auth():
    auth.show_login_page()
    st.stop()

# Initialize Services and Config
supabase = auth.init_supabase()
config_service = services.ConfigService(supabase) if supabase else None
log_service = services.LogService(supabase) if supabase else None

# Load System Config with caching to improve performance
@st.cache_data(ttl=60)  # Cache for 1 minute (reduced for faster sync)
def get_cached_config(_service):
    if _service:
        return _service.get_system_config()
    return {}

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
@st.cache_data(show_spinner=False)
def cached_get_sheet_names(file_bytes, file_name):
    """Cache sheet names based on file content and name."""
    import io
    cleaner = ExcelCleaner()
    # Use a dummy file-like object since we pass bytes
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
    
    # 选择工作表
    sheet_names = list(cleaned_data.keys())
    if len(sheet_names) > 1:
        selected_sheet = st.selectbox("选择要分析的工作表", sheet_names)
    else:
        selected_sheet = sheet_names[0]
    
    df = cleaned_data[selected_sheet]
    
    # 分析模板上传（可选）
    with st.expander("📄 上传分析模板（可选）", expanded=False):
        template_file = st.file_uploader(
            "上传以往的分析报告作为模板（Word/PDF/图片）",
            type=['docx', 'pdf', 'png', 'jpg', 'jpeg'],
            key="template_upload"
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
                    agent_result = agent_analyzer.analyze(df, context, step_callback=step_callback)
                    
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
                    
                    # 构建完整的报告文本
                    full_report = f"""# 数据分析报告

## 分析概况
- **数据形状**: {df.shape[0]} 行 × {df.shape[1]} 列
- **分析步骤**: {len(agent_result.steps)} 步
- **生成代码**: {len(agent_result.generated_code)} 段
- **生成图表**: {len(agent_result.visualizations)} 个

## 详细分析过程

"""
                    for step in agent_result.steps:
                        full_report += f"\n### 步骤 {step.step_number}: {step.action}\n"
                        if step.thought:
                            full_report += f"**思考**: {step.thought}\n\n"
                        full_report += f"**结果**: {step.observation[:500]}...\n\n"
                    
                    full_report += f"\n## 最终分析报告\n\n{agent_result.final_report}"
                    
                    # 提供下载按钮
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📄 下载 Markdown 报告",
                            data=full_report,
                            file_name=f"analysis_report_{selected_sheet}.md",
                            mime="text/markdown"
                        )
                    
                    # 保存结果
                    st.session_state.agent_result = agent_result
                    st.session_state.selected_sheet = selected_sheet
                    
                    status.update(label="✅ Agent 分析完成！", state="complete")
                    st.success("✅ Agent 智能分析完成！报告和图表已生成。")
                    
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
                import traceback
                st.error(traceback.format_exc())
    
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
                    import traceback
                    st.error(traceback.format_exc())
        
        # 文档下载
        st.subheader("📄 生成报告")
        col_word, col_ppt = st.columns(2)
        
        with col_word:
            if st.button("📘 生成Word报告", use_container_width=True):
                with st.spinner("正在生成Word文档..."):
                    try:
                        word_gen = WordDocumentGenerator()
                        chart_paths = st.session_state.get('chart_paths', [])
                        
                        word_doc = word_gen.generate(
                            result,
                            chart_images=chart_paths,
                            title=f"{selected_sheet} 数据分析报告"
                        )
                        
                        st.download_button(
                            "下载Word报告",
                            word_doc,
                            file_name=f"{selected_sheet}_数据分析报告.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Word生成失败: {str(e)}")
        
        with col_ppt:
            if st.button("📊 生成PPT报告", use_container_width=True):
                with st.spinner("正在生成PPT文档..."):
                    try:
                        ppt_gen = PPTDocumentGenerator()
                        chart_paths = st.session_state.get('chart_paths', [])
                        
                        ppt_doc = ppt_gen.generate(
                            result,
                            chart_images=chart_paths,
                            title=f"{selected_sheet} 数据分析汇报"
                        )
                        
                        st.download_button(
                            "下载PPT报告",
                            ppt_doc,
                            file_name=f"{selected_sheet}_数据分析汇报.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"PPT生成失败: {str(e)}")


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

        if uploaded_file:
            # Check File Size Limit
            max_size_mb = int(system_config.get("MAX_FILE_SIZE_MB", 50))
            if uploaded_file.size > max_size_mb * 1024 * 1024:
                st.error(f"文件大小超过限制 ({max_size_mb}MB)。")
            else:
                try:
                    cleaner = ExcelCleaner()
                
                    # 1. Get Sheet Names
                    # Read file as bytes once for caching
                    file_bytes = uploaded_file.getvalue()
                    sheet_names = cached_get_sheet_names(file_bytes, uploaded_file.name)
                    
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
                                header_rows, data_start_row, key_columns = ui.render_interactive_structure_selector(
                                    preview_df, 
                                    key_prefix=f"sheet_{sheet}"
                                )
                                
                                sheet_configs[sheet] = {
                                    "header_rows": header_rows,
                                    "data_start_row": data_start_row,
                                    "key_columns": key_columns
                                }
                        
                        # Action Button
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                        with col_btn2:
                            start_btn = st.button(t("batch_clean_btn"), use_container_width=True)
                        
                        if start_btn:
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
                                    try:
                                        result = cleaner.clean_data(
                                            uploaded_file,
                                            header_rows=config["header_rows"],
                                            data_start_row=config["data_start_row"],
                                            key_columns=config["key_columns"],
                                            separator=sep,
                                            sheet_name=sheet
                                        )
                                        processing_time_ms = int((time.time() - start_time) * 1000)
                                        
                                        cleaned_results[sheet] = result['cleaned_df']
                                        
                                        # Log Success
                                        if log_service and st.session_state.user:
                                            log_service.log_cleaning_task(
                                                user_id=st.session_state.user.id,
                                                file_name=uploaded_file.name,
                                                file_size=uploaded_file.size,
                                                row_count=len(result['cleaned_df']),
                                                processing_time_ms=processing_time_ms,
                                                status='success'
                                            )
                                            
                                    except Exception as e:
                                        # Log Failure
                                        if log_service and st.session_state.user:
                                            log_service.log_cleaning_task(
                                                user_id=st.session_state.user.id,
                                                file_name=uploaded_file.name,
                                                file_size=uploaded_file.size,
                                                status='failed',
                                                error_message=str(e)
                                            )
                                        raise e
                                    
                                    # Update progress
                                    progress = int(10 + (idx + 1) / total_sheets * 80)
                                    progress_bar.progress(progress)
                                    
                                # Store results (Dictionary of DFs)
                                st.session_state.cleaned_data = cleaned_results
                                st.session_state.raw_preview = None # Not applicable for batch
                                
                                progress_bar.progress(100)
                                status_text.text(t("success"))
                                st.balloons()
                                
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
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
