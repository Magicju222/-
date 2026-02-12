"""
Log Viewer Module
Handles cleaning logs display and filtering
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from .admin_api import get_admin_api


def show_log_viewer():
    """Display log viewer interface"""
    st.header("📋 清洗日志")

    # Get admin API client
    api = get_admin_api()

    # Load data
    with st.spinner("加载数据..."):
        logs = api.get_logs(limit=5000)
        users = api.get_users(limit=1000)

    if not logs:
        st.info("暂无日志数据")
        return

    # Convert to DataFrame
    df_logs = pd.DataFrame(logs)
    df_users = pd.DataFrame(users) if users else pd.DataFrame()

    # Show cleaning trend chart
    show_cleaning_trend(df_logs)

    st.markdown("---")

    # Filters section
    st.subheader("筛选条件")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        date_from = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=7),
            max_value=datetime.now(),
            key="logs_date_from"
        )

    with col2:
        date_to = st.date_input(
            "结束日期",
            value=datetime.now(),
            max_value=datetime.now(),
            key="logs_date_to"
        )

    with col3:
        status_filter = st.selectbox(
            "状态筛选",
            ["全部", "success", "error", "processing"]
        )

    with col4:
        # User filter
        user_options = ["全部"]
        if not df_users.empty and 'id' in df_users.columns and 'email' in df_users.columns:
            user_dict = dict(zip(df_users['id'], df_users['email']))
            user_options.extend([f"{uid} ({email})" for uid, email in user_dict.items()])

        user_filter = st.selectbox(
            "用户筛选",
            options=user_options
        )

    # Apply filters
    if 'created_at' in df_logs.columns:
        df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
        df_logs = df_logs[
            (df_logs['created_at'].dt.date >= date_from) &
            (df_logs['created_at'].dt.date <= date_to)
            ]

    if status_filter != "全部" and 'status' in df_logs.columns:
        df_logs = df_logs[df_logs['status'] == status_filter]

    if user_filter != "全部" and 'user_id' in df_logs.columns:
        selected_user_id = user_filter.split(" ")[0]
        df_logs = df_logs[df_logs['user_id'] == selected_user_id]

    # Display summary statistics
    st.markdown("---")
    show_statistics(df_logs, df_users)

    # Display logs table
    st.markdown("---")
    st.subheader("日志列表")

    if len(df_logs) > 0:
        show_logs_table(df_logs, df_users)
    else:
        st.info("没有符合筛选条件的日志")


def show_cleaning_trend(df: pd.DataFrame):
    """Show cleaning task trend chart"""
    if 'created_at' not in df.columns or len(df) == 0:
        return

    st.subheader("📈 清洗任务趋势")

    # Convert to datetime
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Get task counts by date (last 30 days)
    df['date'] = df['created_at'].dt.date
    last_30_days = datetime.now().date() - timedelta(days=30)

    daily_tasks = df[df['date'] >= last_30_days].groupby('date').size().reset_index(name='count')

    if len(daily_tasks) > 0:
        # Fill missing dates
        date_range = pd.date_range(start=last_30_days, end=datetime.now().date(), freq='D')
        daily_tasks = daily_tasks.set_index('date').reindex(date_range.date, fill_value=0).reset_index()
        daily_tasks.columns = ['date', 'count']

        # Display metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_tasks = len(df)
            st.metric("总任务数", total_tasks)

        with col2:
            today = datetime.now().date()
            today_count = len(df[df['date'] == today])
            st.metric("今日任务", today_count)

        with col3:
            last_7_days = datetime.now().date() - timedelta(days=7)
            week_count = len(df[df['date'] >= last_7_days])
            st.metric("近7天任务", week_count)

        with col4:
            if 'status' in df.columns:
                success_rate = (len(df[df['status'] == 'success']) / len(df)) * 100 if len(df) > 0 else 0
                st.metric("成功率", f"{success_rate:.1f}%")

        # Show chart
        st.line_chart(daily_tasks.set_index('date'))
    else:
        st.info("暂无任务数据")


def show_statistics(df_logs: pd.DataFrame, df_users: pd.DataFrame):
    """Show detailed statistics"""
    st.subheader("统计概览")

    # Basic stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总记录数", len(df_logs))

    with col2:
        if 'status' in df_logs.columns:
            success_count = len(df_logs[df_logs['status'] == 'success'])
            st.metric("成功", success_count)

    with col3:
        if 'status' in df_logs.columns:
            error_count = len(df_logs[df_logs['status'] == 'error'])
            st.metric("失败", error_count)

    with col4:
        if 'status' in df_logs.columns and len(df_logs) > 0:
            success_rate = (len(df_logs[df_logs['status'] == 'success']) / len(df_logs)) * 100
            st.metric("成功率", f"{success_rate:.1f}%")

    # Advanced stats
    st.markdown("**详细统计**")

    col1, col2 = st.columns(2)

    with col1:
        # Top users by task count
        if 'user_id' in df_logs.columns:
            st.markdown("🏆 活跃用户 TOP 10")
            user_counts = df_logs['user_id'].value_counts().head(10)

            if not df_users.empty and 'id' in df_users.columns and 'email' in df_users.columns:
                user_dict = dict(zip(df_users['id'], df_users['email']))
                user_counts.index = [f"{uid} ({user_dict.get(uid, 'Unknown')})" for uid in user_counts.index]

            st.bar_chart(user_counts)

    with col2:
        # File type distribution
        if 'file_type' in df_logs.columns:
            st.markdown("📁 文件类型分布")
            file_types = df_logs['file_type'].value_counts().head(10)
            st.bar_chart(file_types)

    # Status distribution over time
    if 'status' in df_logs.columns and 'date' in df_logs.columns:
        st.markdown("📊 每日状态分布")
        status_by_date = df_logs.groupby(['date', 'status']).size().unstack(fill_value=0)
        st.bar_chart(status_by_date)


def show_logs_table(df_logs: pd.DataFrame, df_users: pd.DataFrame):
    """Show logs table with details"""
    # Select columns to display
    display_columns = ['id', 'user_id', 'filename', 'status', 'created_at', 'rows_processed', 'file_size']
    available_columns = [col for col in display_columns if col in df_logs.columns]

    if available_columns:
        display_df = df_logs[available_columns].copy()

        # Format dates
        if 'created_at' in display_df.columns:
            display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')

        # Add user email
        if 'user_id' in display_df.columns and not df_users.empty and 'email' in df_users.columns:
            user_dict = dict(zip(df_users['id'], df_users['email']))
            display_df['user_email'] = display_df['user_id'].map(user_dict)

        # Format file size
        if 'file_size' in display_df.columns:
            display_df['file_size'] = display_df['file_size'].apply(format_file_size)

        # Rename columns
        column_names = {
            'id': '日志ID',
            'user_id': '用户ID',
            'user_email': '用户邮箱',
            'filename': '文件名',
            'status': '状态',
            'created_at': '处理时间',
            'rows_processed': '处理行数',
            'file_size': '文件大小'
        }
        display_df.columns = [column_names.get(col, col) for col in display_df.columns]

        # Show table with pagination
        page_size = 50
        total_pages = max(1, (len(display_df) + page_size - 1) // page_size)

        if total_pages > 1:
            col1, col2 = st.columns([1, 4])
            with col1:
                page = st.number_input("页码", min_value=1, max_value=total_pages, value=1)
            with col2:
                st.write(f"共 {total_pages} 页，每页 {page_size} 条")
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(display_df))
            display_df = display_df.iloc[start_idx:end_idx]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Log details section
        st.markdown("---")
        st.subheader("日志详情")

        selected_log_id = st.selectbox(
            "选择日志查看详情",
            options=df_logs['id'].tolist(),
            format_func=lambda x: f"{x} - {df_logs[df_logs['id'] == x]['filename'].iloc[0] if 'filename' in df_logs.columns else 'Unknown'}"
        )

        if selected_log_id:
            show_log_details(df_logs[df_logs['id'] == selected_log_id].iloc[0], df_users)

        # Export section
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 导出当前筛选结果"):
                csv = df_logs.to_csv(index=False)
                st.download_button(
                    label="下载 CSV",
                    data=csv,
                    file_name=f"cleaning_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col2:
            if st.button("📊 导出统计报告"):
                report = generate_statistics_report(df_logs, df_users)
                st.download_button(
                    label="下载报告",
                    data=report,
                    file_name=f"cleaning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )


def show_log_details(log: Dict, df_users: pd.DataFrame):
    """Show detailed log information"""
    with st.expander("日志详情", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**基本信息**")
            st.write(f"日志ID: `{log.get('id', 'N/A')}`")

            user_id = log.get('user_id', 'N/A')
            st.write(f"用户ID: `{user_id}`")

            # Show user email if available
            if not df_users.empty and 'id' in df_users.columns and 'email' in df_users.columns:
                user_email = df_users[df_users['id'] == user_id]['email'].iloc[0] if len(
                    df_users[df_users['id'] == user_id]) > 0 else 'Unknown'
                st.write(f"用户邮箱: {user_email}")

            st.write(f"文件名: {log.get('filename', 'N/A')}")
            st.write(f"文件类型: {log.get('file_type', 'N/A')}")

        with col2:
            st.markdown("**处理信息**")
            status = log.get('status', 'N/A')
            status_icon = "✅" if status == 'success' else "❌" if status == 'error' else "⏳"
            st.write(f"状态: {status_icon} {status}")

            st.write(f"处理行数: {log.get('rows_processed', 'N/A')}")
            st.write(f"文件大小: {format_file_size(log.get('file_size', 0))}")
            st.write(f"处理时间: {log.get('created_at', 'N/A')}")

        # Error details
        if status == 'error' and 'error_message' in log and log['error_message']:
            st.markdown("**错误信息**")
            st.error(log['error_message'])

        # Processing details
        if 'processing_time_ms' in log and log['processing_time_ms']:
            st.markdown("**性能信息**")
            st.write(f"处理耗时: {log['processing_time_ms']} ms")

        # Raw data
        with st.expander("查看原始数据"):
            st.json(log)


def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable"""
    if size_bytes is None or size_bytes == 0:
        return "0 B"

    size_bytes = int(size_bytes)

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} TB"


def generate_statistics_report(df_logs: pd.DataFrame, df_users: pd.DataFrame) -> str:
    """Generate a text statistics report"""
    report = []
    report.append("=" * 60)
    report.append("清洗任务统计报告")
    report.append("=" * 60)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # Basic stats
    report.append("【基本统计】")
    report.append(f"总任务数: {len(df_logs)}")

    if 'status' in df_logs.columns:
        success_count = len(df_logs[df_logs['status'] == 'success'])
        error_count = len(df_logs[df_logs['status'] == 'error'])
        success_rate = (success_count / len(df_logs)) * 100 if len(df_logs) > 0 else 0

        report.append(f"成功: {success_count}")
        report.append(f"失败: {error_count}")
        report.append(f"成功率: {success_rate:.1f}%")

    report.append("")

    # Date range
    if 'created_at' in df_logs.columns:
        df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
        report.append("【时间范围】")
        report.append(f"最早: {df_logs['created_at'].min()}")
        report.append(f"最晚: {df_logs['created_at'].max()}")
        report.append("")

    # Top users
    if 'user_id' in df_logs.columns:
        report.append("【活跃用户 TOP 5】")
        top_users = df_logs['user_id'].value_counts().head(5)

        for i, (user_id, count) in enumerate(top_users.items(), 1):
            user_email = 'Unknown'
            if not df_users.empty and 'id' in df_users.columns and 'email' in df_users.columns:
                user_rows = df_users[df_users['id'] == user_id]
                if len(user_rows) > 0:
                    user_email = user_rows['email'].iloc[0]

            report.append(f"{i}. {user_email} ({user_id}): {count} 次")

        report.append("")

    # File types
    if 'file_type' in df_logs.columns:
        report.append("【文件类型分布】")
        file_types = df_logs['file_type'].value_counts()
        for file_type, count in file_types.items():
            report.append(f"{file_type}: {count} 次")

    report.append("")
    report.append("=" * 60)
    report.append("报告结束")
    report.append("=" * 60)

    return "\n".join(report)
