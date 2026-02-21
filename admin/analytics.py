"""
Analytics Module
Provides data analysis and visualization for admin
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .admin_api import get_admin_api

ANALYTICS_CACHE_TTL = 30  # seconds


@st.cache_data(ttl=ANALYTICS_CACHE_TTL, show_spinner=False)
def get_cached_stats(api_url: str) -> Dict:
    """Cached stats fetch"""
    from .admin_api import AdminAPI
    api = AdminAPI(api_url)
    return api.get_stats()


@st.cache_data(ttl=ANALYTICS_CACHE_TTL, show_spinner=False)
def get_cached_users_analytics(api_url: str, limit: int = 10000) -> List[Dict]:
    """Cached users fetch for analytics"""
    from .admin_api import AdminAPI
    api = AdminAPI(api_url)
    return api.get_users(limit=limit)


@st.cache_data(ttl=ANALYTICS_CACHE_TTL, show_spinner=False)
def get_cached_logs_analytics(api_url: str, limit: int = 10000) -> List[Dict]:
    """Cached logs fetch for analytics"""
    from .admin_api import AdminAPI
    api = AdminAPI(api_url)
    return api.get_logs(limit=limit)


def show_analytics():
    """Display analytics dashboard"""
    st.header("📊 数据分析")

    # Get admin API client
    api = get_admin_api()

    # Time range selector
    st.subheader("时间范围")
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        date_from = st.date_input(
            "开始日期",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            key="analytics_date_from"
        )

    with col2:
        date_to = st.date_input(
            "结束日期",
            value=datetime.now(),
            max_value=datetime.now(),
            key="analytics_date_to"
        )

    with col3:
        # Quick select
        quick_range = st.selectbox(
            "快速选择",
            ["自定义", "今天", "昨天", "最近7天", "最近30天", "本月", "上月"]
        )

        if quick_range != "自定义":
            date_from, date_to = get_quick_date_range(quick_range)

    # Load data with caching
    stats = get_cached_stats(api.base_url)
    users = get_cached_users_analytics(api.base_url, limit=10000)
    logs = get_cached_logs_analytics(api.base_url, limit=10000)

    # Filter data by date range
    df_users, df_logs = filter_data_by_date(users, logs, date_from, date_to)

    # KPI Cards with comparison
    show_kpi_cards(df_users, df_logs, date_from, date_to)

    # User Analysis
    st.markdown("---")
    show_user_analysis(df_users, date_from, date_to)

    # Task Analysis
    st.markdown("---")
    show_task_analysis(df_logs, date_from, date_to)

    # Data Comparison
    st.markdown("---")
    show_comparison_analysis(df_users, df_logs, date_from, date_to)


def get_quick_date_range(range_type: str) -> Tuple[datetime.date, datetime.date]:
    """Get date range based on quick selection"""
    today = datetime.now().date()

    if range_type == "今天":
        return today, today
    elif range_type == "昨天":
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif range_type == "最近7天":
        return today - timedelta(days=7), today
    elif range_type == "最近30天":
        return today - timedelta(days=30), today
    elif range_type == "本月":
        first_day = today.replace(day=1)
        return first_day, today
    elif range_type == "上月":
        last_month = today.replace(day=1) - timedelta(days=1)
        first_day = last_month.replace(day=1)
        return first_day, last_month

    return today - timedelta(days=30), today


def filter_data_by_date(users: List[Dict], logs: List[Dict], date_from: datetime.date,
                        date_to: datetime.date) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filter data by date range"""
    df_users = pd.DataFrame(users) if users else pd.DataFrame()
    df_logs = pd.DataFrame(logs) if logs else pd.DataFrame()

    # Filter users by registration date
    if not df_users.empty and 'created_at' in df_users.columns:
        df_users['created_at'] = pd.to_datetime(df_users['created_at'])
        df_users = df_users[
            (df_users['created_at'].dt.date >= date_from) &
            (df_users['created_at'].dt.date <= date_to)
            ]

    # Filter logs by created date
    if not df_logs.empty and 'created_at' in df_logs.columns:
        df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
        df_logs = df_logs[
            (df_logs['created_at'].dt.date >= date_from) &
            (df_logs['created_at'].dt.date <= date_to)
            ]

    return df_users, df_logs


def show_kpi_cards(df_users: pd.DataFrame, df_logs: pd.DataFrame, date_from: datetime.date,
                   date_to: datetime.date):
    """Show KPI cards with comparison to previous period"""
    st.subheader("关键指标")

    # Calculate previous period for comparison
    period_days = (date_to - date_from).days + 1
    prev_date_from = date_from - timedelta(days=period_days)
    prev_date_to = date_from - timedelta(days=1)

    # Get previous period data
    api = get_admin_api()
    prev_users, prev_logs = get_previous_period_data(api, prev_date_from, prev_date_to)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_users = len(df_users)
        prev_total_users = len(prev_users)
        delta = total_users - prev_total_users if prev_total_users > 0 else None
        st.metric(
            label="新增用户",
            value=total_users,
            delta=delta,
            delta_color="normal"
        )

    with col2:
        total_tasks = len(df_logs)
        prev_total_tasks = len(prev_logs)
        delta = total_tasks - prev_total_tasks if prev_total_tasks > 0 else None
        st.metric(
            label="清洗任务",
            value=total_tasks,
            delta=delta,
            delta_color="normal"
        )

    with col3:
        # Calculate success rate
        success_rate = 0
        if not df_logs.empty and 'status' in df_logs.columns and len(df_logs) > 0:
            success_count = len(df_logs[df_logs['status'] == 'success'])
            success_rate = (success_count / len(df_logs)) * 100

        prev_success_rate = 0
        if not prev_logs.empty and 'status' in prev_logs.columns and len(prev_logs) > 0:
            prev_success_count = len(prev_logs[prev_logs['status'] == 'success'])
            prev_success_rate = (prev_success_count / len(prev_logs)) * 100

        delta = success_rate - prev_success_rate if prev_success_rate > 0 else None
        st.metric(
            label="成功率",
            value=f"{success_rate:.1f}%",
            delta=f"{delta:.1f}%" if delta is not None else None,
            delta_color="normal"
        )

    with col4:
        # Calculate active users (users with tasks)
        active_users = 0
        if not df_logs.empty and 'user_id' in df_logs.columns:
            active_users = df_logs['user_id'].nunique()

        prev_active_users = 0
        if not prev_logs.empty and 'user_id' in prev_logs.columns:
            prev_active_users = prev_logs['user_id'].nunique()

        delta = active_users - prev_active_users if prev_active_users > 0 else None
        st.metric(
            label="活跃用户",
            value=active_users,
            delta=delta,
            delta_color="normal"
        )


def get_previous_period_data(api, date_from: datetime.date, date_to: datetime.date) -> Tuple[
    pd.DataFrame, pd.DataFrame]:
    """Get data from previous period for comparison"""
    users = api.get_users(limit=10000)
    logs = api.get_logs(limit=10000)

    df_users = pd.DataFrame(users) if users else pd.DataFrame()
    df_logs = pd.DataFrame(logs) if logs else pd.DataFrame()

    # Filter by date
    if not df_users.empty and 'created_at' in df_users.columns:
        df_users['created_at'] = pd.to_datetime(df_users['created_at'])
        df_users = df_users[
            (df_users['created_at'].dt.date >= date_from) &
            (df_users['created_at'].dt.date <= date_to)
            ]

    if not df_logs.empty and 'created_at' in df_logs.columns:
        df_logs['created_at'] = pd.to_datetime(df_logs['created_at'])
        df_logs = df_logs[
            (df_logs['created_at'].dt.date >= date_from) &
            (df_logs['created_at'].dt.date <= date_to)
            ]

    return df_users, df_logs


def show_user_analysis(df_users: pd.DataFrame, date_from: datetime.date, date_to: datetime.date):
    """Show user analysis section"""
    st.subheader("用户分析")

    if df_users.empty:
        st.info("该时间段内没有用户数据")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**角色分布**")
        if 'role' in df_users.columns:
            role_counts = df_users['role'].value_counts()
            st.bar_chart(role_counts)

            # Show percentages
            total = len(df_users)
            st.caption("分布详情:")
            for role, count in role_counts.items():
                percentage = (count / total) * 100
                st.write(f"- {role}: {count} ({percentage:.1f}%)")

    with col2:
        st.markdown("**状态分布**")
        if 'status' in df_users.columns:
            status_counts = df_users['status'].value_counts()
            st.bar_chart(status_counts)

            # Show percentages
            total = len(df_users)
            st.caption("分布详情:")
            for status, count in status_counts.items():
                percentage = (count / total) * 100
                st.write(f"- {status}: {count} ({percentage:.1f}%)")

    # User registration trend
    st.markdown("**用户注册趋势**")
    if 'created_at' in df_users.columns:
        df_users['date'] = df_users['created_at'].dt.date
        daily_registrations = df_users.groupby('date', observed=False).size()

        if len(daily_registrations) > 1:
            st.line_chart(daily_registrations)
        else:
            st.info("数据点不足，无法显示趋势图")

    # Recent users table
    st.markdown("**最近注册用户 TOP 10**")
    if 'created_at' in df_users.columns:
        recent_users = df_users.nlargest(10, 'created_at')
        display_cols = ['email', 'role', 'status', 'created_at']
        available_cols = [col for col in display_cols if col in recent_users.columns]

        if available_cols:
            display_df = recent_users[available_cols].copy()
            if 'created_at' in display_df.columns:
                display_df['created_at'] = display_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_df, hide_index=True, use_container_width=True)


def show_task_analysis(df_logs: pd.DataFrame, date_from: datetime.date, date_to: datetime.date):
    """Show task analysis section"""
    st.subheader("任务分析")

    if df_logs.empty:
        st.info("该时间段内没有任务数据")
        return

    # Task trend
    st.markdown("**任务趋势**")
    if 'created_at' in df_logs.columns:
        df_logs['date'] = df_logs['created_at'].dt.date
        daily_tasks = df_logs.groupby('date', observed=False).size()

        if len(daily_tasks) > 1:
            st.line_chart(daily_tasks)
        else:
            st.info("数据点不足，无法显示趋势图")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**任务状态分布**")
        if 'status' in df_logs.columns:
            status_counts = df_logs['status'].value_counts()
            st.bar_chart(status_counts)

            # Show success rate
            total = len(df_logs)
            success_count = len(df_logs[df_logs['status'] == 'success'])
            success_rate = (success_count / total) * 100 if total > 0 else 0
            st.caption(f"成功率: {success_rate:.1f}%")

    with col2:
        st.markdown("**文件类型分布**")
        if 'file_type' in df_logs.columns:
            file_type_counts = df_logs['file_type'].value_counts().head(10)
            st.bar_chart(file_type_counts)

    # Hourly distribution
    st.markdown("**时段分布（按小时）**")
    if 'created_at' in df_logs.columns:
        df_logs['hour'] = df_logs['created_at'].dt.hour
        hourly_tasks = df_logs.groupby('hour', observed=False).size()
        st.bar_chart(hourly_tasks)

    # Top users by task count
    st.markdown("**活跃用户 TOP 10**")
    if 'user_id' in df_logs.columns:
        user_counts = df_logs['user_id'].value_counts().head(10)
        st.bar_chart(user_counts)

    # File size statistics
    if 'file_size' in df_logs.columns:
        st.markdown("**文件大小统计**")
        col1, col2, col3 = st.columns(3)

        with col1:
            avg_size = df_logs['file_size'].mean()
            st.metric("平均大小", format_file_size(avg_size))

        with col2:
            max_size = df_logs['file_size'].max()
            st.metric("最大大小", format_file_size(max_size))

        with col3:
            min_size = df_logs['file_size'].min()
            st.metric("最小大小", format_file_size(min_size))


def show_comparison_analysis(df_users: pd.DataFrame, df_logs: pd.DataFrame, date_from: datetime.date,
                             date_to: datetime.date):
    """Show comparison analysis between periods"""
    st.subheader("数据对比分析")

    # Week over week comparison
    st.markdown("**周环比分析**")

    # Calculate current week and previous week
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    prev_week_start = current_week_start - timedelta(days=7)
    prev_week_end = current_week_start - timedelta(days=1)

    # Get data for both weeks
    api = get_admin_api()
    all_users = api.get_users(limit=10000)
    all_logs = api.get_logs(limit=10000)

    df_all_users = pd.DataFrame(all_users) if all_users else pd.DataFrame()
    df_all_logs = pd.DataFrame(all_logs) if all_logs else pd.DataFrame()

    if not df_all_users.empty and 'created_at' in df_all_users.columns:
        df_all_users['created_at'] = pd.to_datetime(df_all_users['created_at'])

    if not df_all_logs.empty and 'created_at' in df_all_logs.columns:
        df_all_logs['created_at'] = pd.to_datetime(df_all_logs['created_at'])

    # Current week data
    current_week_users = 0
    current_week_tasks = 0

    if not df_all_users.empty:
        current_week_users = len(df_all_users[
                                     (df_all_users['created_at'].dt.date >= current_week_start) &
                                     (df_all_users['created_at'].dt.date <= today)
                                     ])

    if not df_all_logs.empty:
        current_week_tasks = len(df_all_logs[
                                     (df_all_logs['created_at'].dt.date >= current_week_start) &
                                     (df_all_logs['created_at'].dt.date <= today)
                                     ])

    # Previous week data
    prev_week_users = 0
    prev_week_tasks = 0

    if not df_all_users.empty:
        prev_week_users = len(df_all_users[
                                  (df_all_users['created_at'].dt.date >= prev_week_start) &
                                  (df_all_users['created_at'].dt.date <= prev_week_end)
                                  ])

    if not df_all_logs.empty:
        prev_week_tasks = len(df_all_logs[
                                  (df_all_logs['created_at'].dt.date >= prev_week_start) &
                                  (df_all_logs['created_at'].dt.date <= prev_week_end)
                                  ])

    # Show comparison
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**本周 vs 上周 - 新增用户**")
        user_change = ((current_week_users - prev_week_users) / prev_week_users * 100) if prev_week_users > 0 else 0
        st.metric(
            label="本周新增用户",
            value=current_week_users,
            delta=f"{user_change:.1f}%" if prev_week_users > 0 else None
        )
        st.caption(f"上周: {prev_week_users} 人")

    with col2:
        st.markdown("**本周 vs 上周 - 清洗任务**")
        task_change = ((current_week_tasks - prev_week_tasks) / prev_week_tasks * 100) if prev_week_tasks > 0 else 0
        st.metric(
            label="本周任务数",
            value=current_week_tasks,
            delta=f"{task_change:.1f}%" if prev_week_tasks > 0 else None
        )
        st.caption(f"上周: {prev_week_tasks} 次")

    # Export data
    st.markdown("---")
    if st.button("📊 导出分析数据"):
        export_data = {
            'period': f"{date_from} to {date_to}",
            'total_users': len(df_users),
            'total_tasks': len(df_logs),
            'active_users': df_logs['user_id'].nunique() if not df_logs.empty and 'user_id' in df_logs.columns else 0
        }

        report = generate_analytics_report(export_data, df_users, df_logs)
        st.download_button(
            label="下载分析报告",
            data=report,
            file_name=f"analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


def format_file_size(size_bytes: float) -> str:
    """Format file size to human readable"""
    if size_bytes is None or size_bytes == 0:
        return "0 B"

    size_bytes = float(size_bytes)

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} TB"


def generate_analytics_report(export_data: Dict, df_users: pd.DataFrame, df_logs: pd.DataFrame) -> str:
    """Generate analytics report"""
    report = []
    report.append("=" * 60)
    report.append("数据分析报告")
    report.append("=" * 60)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"分析周期: {export_data['period']}")
    report.append("")

    report.append("【概览统计】")
    report.append(f"新增用户: {export_data['total_users']} 人")
    report.append(f"清洗任务: {export_data['total_tasks']} 次")
    report.append(f"活跃用户: {export_data['active_users']} 人")

    if not df_logs.empty and 'status' in df_logs.columns:
        success_count = len(df_logs[df_logs['status'] == 'success'])
        success_rate = (success_count / len(df_logs)) * 100 if len(df_logs) > 0 else 0
        report.append(f"成功率: {success_rate:.1f}%")

    report.append("")

    if not df_users.empty and 'role' in df_users.columns:
        report.append("【角色分布】")
        role_counts = df_users['role'].value_counts()
        for role, count in role_counts.items():
            percentage = (count / len(df_users)) * 100
            report.append(f"{role}: {count} 人 ({percentage:.1f}%)")
        report.append("")

    if not df_logs.empty and 'file_type' in df_logs.columns:
        report.append("【文件类型分布】")
        file_type_counts = df_logs['file_type'].value_counts().head(5)
        for file_type, count in file_type_counts.items():
            report.append(f"{file_type}: {count} 次")
        report.append("")

    report.append("=" * 60)
    report.append("报告结束")
    report.append("=" * 60)

    return "\n".join(report)
