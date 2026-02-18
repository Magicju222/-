

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
                    # PDF处理需要额外库
                    template_content = "PDF模板已上传"
                elif template_file.type in ['image/png', 'image/jpeg']:
                    template_content = "图片模板已上传"
                else:
                    # Word文档
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
        with st.spinner("🤖 AI正在深度分析中，请稍候..."):
            try:
                # 初始化组件
                llm_client = LLMClient()
                analyzer = DataAnalyzer(llm_client)
                
                # 执行分析
                analysis_result = analyzer.analyze(
                    df=df,
                    template_dimensions=template_dimensions if template_dimensions else None,
                    user_dimensions=user_dimensions if user_dimensions else None,
                    context=context
                )
                
                # 保存分析结果到session state
                st.session_state.analysis_result = analysis_result
                st.session_state.selected_sheet = selected_sheet
                
                st.success("✅ 分析完成！")
                
            except Exception as e:
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
        if st.button("生成可视化图表", key="generate_charts"):
            with st.spinner("正在生成图表..."):
                try:
                    chart_gen = ChartGenerator(llm_client)
                    chart_paths = chart_gen.generate_multiple_charts(
                        df, 
                        result.visualization_recommendations[:3]
                    )
                    
                    st.session_state.chart_paths = chart_paths
                    
                    # 显示图表
                    for i, path in enumerate(chart_paths):
                        if path:
                            st.image(path, caption=f"图表 {i+1}")
                    
                except Exception as e:
                    st.error(f"图表生成失败: {str(e)}")
        
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
