"""
System Configuration Module
Handles system settings management with real-time sync
"""

import streamlit as st
import json
from typing import Dict, List, Optional
from datetime import datetime
from .admin_api import get_admin_api

# Configuration definitions with metadata
CONFIG_DEFINITIONS = {
    'MAINTENANCE_MODE': {
        'label': '维护模式',
        'description': '开启后只有管理员可以访问系统，普通用户将看到维护提示',
        'type': 'boolean',
        'default': 'false',
        'category': 'basic'
    },
    'MAX_FILE_SIZE_MB': {
        'label': '最大文件大小',
        'description': '允许上传的单个文件最大大小（单位：MB）',
        'type': 'number',
        'min': 1,
        'max': 500,
        'default': '50',
        'unit': 'MB',
        'category': 'file'
    },
    'ALLOWED_EXTENSIONS': {
        'label': '允许的文件类型',
        'description': '系统支持处理的文件扩展名列表（JSON格式）',
        'type': 'json',
        'default': '["xlsx", "xls", "csv"]',
        'category': 'file'
    },
    'MAX_ROWS_PER_FILE': {
        'label': '最大行数限制',
        'description': '单个文件允许的最大数据行数，超过将拒绝处理',
        'type': 'number',
        'min': 1000,
        'max': 1000000,
        'default': '100000',
        'unit': '行',
        'category': 'file'
    },
    'ENABLE_USER_REGISTRATION': {
        'label': '允许用户注册',
        'description': '关闭后新用户将无法注册账号',
        'type': 'boolean',
        'default': 'true',
        'category': 'basic'
    },
    'REQUIRE_EMAIL_VERIFICATION': {
        'label': '需要邮箱验证',
        'description': '开启后用户注册后需要验证邮箱才能使用系统',
        'type': 'boolean',
        'default': 'false',
        'category': 'basic'
    },
    'SYSTEM_NOTICE': {
        'label': '系统公告',
        'description': '显示给所有用户的系统公告消息（支持HTML）',
        'type': 'textarea',
        'default': '',
        'category': 'display'
    },
    'CLEANUP_INTERVAL_DAYS': {
        'label': '数据清理周期',
        'description': '自动清理过期日志和临时文件的时间间隔',
        'type': 'number',
        'min': 1,
        'max': 365,
        'default': '30',
        'unit': '天',
        'category': 'maintenance'
    },
    'ENABLE_ANALYTICS': {
        'label': '启用统计分析',
        'description': '开启后将收集使用统计数据用于改进系统',
        'type': 'boolean',
        'default': 'true',
        'category': 'advanced'
    },
    'API_RATE_LIMIT': {
        'label': 'API 速率限制',
        'description': '每个用户每分钟允许的API请求次数',
        'type': 'number',
        'min': 10,
        'max': 10000,
        'default': '100',
        'unit': '次/分钟',
        'category': 'advanced'
    }
}


def sync_config_to_session(updated_config: List[Dict]) -> bool:
    """
    Sync updated configuration to session state for real-time updates.
    This ensures all parts of the app use the latest config.
    """
    try:
        if not updated_config:
            return False

        # Convert list to dict for easier access
        config_dict = {item.get('key'): item.get('value') for item in updated_config if 'key' in item}

        # Update session state
        st.session_state.system_config = config_dict

        # Mark that config has been updated (for other components to detect)
        st.session_state.config_last_updated = datetime.now().isoformat()

        return True
    except Exception as e:
        st.error(f"配置同步失败: {str(e)}")
        return False


def update_config_with_sync(api, key: str, value: str) -> bool:
    """
    Update config and sync to session state immediately.
    Returns True if successful.
    """
    with st.spinner("正在更新配置..."):
        updated_config = api.update_config(key, value)

    if updated_config:
        if sync_config_to_session(updated_config):
            st.success("✅ 配置已更新并同步")
            return True
        else:
            st.warning("⚠️ 配置已更新但同步失败，请刷新页面")
            return False
    else:
        st.error("❌ 配置更新失败")
        return False


def show_system_config():
    """Display system configuration interface with real-time sync"""
    st.header("⚙️ 系统配置")

    # Show last sync time if available
    if 'config_last_updated' in st.session_state:
        with st.expander("ℹ️ 同步状态", expanded=False):
            st.info(f"上次同步时间: {st.session_state.config_last_updated}")
            if st.button("🔄 立即刷新配置"):
                st.rerun()

    # Get admin API client
    api = get_admin_api()

    # Load current configuration with error handling
    try:
        with st.spinner("加载配置..."):
            config = api.get_config()

        if not config:
            st.info("暂无配置数据")
            return

        # Sync to session state on load
        sync_config_to_session(config)

    except Exception as e:
        st.error(f"加载配置失败: {str(e)}")
        if st.button("🔄 重试"):
            st.rerun()
        return

    # Convert to dict for easier access
    config_dict = {item.get('key'): item.get('value') for item in config if 'key' in item}

    # Create tabs for different categories
    tabs = st.tabs([
        "🏠 基本设置",
        "📁 文件设置",
        "🎨 显示设置",
        "🔧 维护设置",
        "⚡ 高级设置",
        "📋 所有配置"
    ])

    with tabs[0]:
        show_config_category(config_dict, api, 'basic')

    with tabs[1]:
        show_config_category(config_dict, api, 'file')

    with tabs[2]:
        show_config_category(config_dict, api, 'display')

    with tabs[3]:
        show_config_category(config_dict, api, 'maintenance')

    with tabs[4]:
        show_config_category(config_dict, api, 'advanced')

    with tabs[5]:
        show_all_config(config)

    # Configuration help section
    st.markdown("---")
    with st.expander("❓ 配置说明"):
        show_config_help()


def show_config_category(config_dict: Dict, api, category: str):
    """Show configuration for a specific category"""
    category_configs = {k: v for k, v in CONFIG_DEFINITIONS.items() if v.get('category') == category}

    if not category_configs:
        st.info("该分类下暂无配置项")
        return

    for key, definition in category_configs.items():
        show_config_item(key, definition, config_dict, api)


def show_config_item(key: str, definition: Dict, config_dict: Dict, api):
    """Show a single configuration item"""
    current_value = config_dict.get(key, definition.get('default', ''))

    # Create container for each config item
    with st.container():
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown(f"**{definition['label']}**")
            st.caption(definition['description'])

        with col2:
            config_type = definition.get('type', 'text')

            if config_type == 'boolean':
                current_bool = current_value.lower() == 'true' if isinstance(current_value, str) else bool(
                    current_value)
                new_value = st.toggle(
                    "启用",
                    value=current_bool,
                    key=f"config_{key}"
                )
                new_value_str = 'true' if new_value else 'false'

                if new_value_str != str(current_value).lower():
                    if update_config_with_sync(api, key, new_value_str):
                        st.rerun()

            elif config_type == 'number':
                min_val = definition.get('min', 0)
                max_val = definition.get('max', 100)
                default_val = int(current_value) if str(current_value).isdigit() else int(
                    definition.get('default', 0))

                new_value = st.number_input(
                    definition.get('unit', ''),
                    min_value=min_val,
                    max_value=max_val,
                    value=default_val,
                    key=f"config_{key}",
                    label_visibility="collapsed"
                )

                if str(new_value) != str(current_value):
                    if update_config_with_sync(api, key, str(new_value)):
                        st.rerun()

            elif config_type == 'json':
                # Display as code block
                st.code(current_value, language="json")

                # Edit button
                if st.button("✏️ 编辑", key=f"edit_{key}"):
                    st.session_state[f"editing_{key}"] = True

                # Show edit form if editing
                if st.session_state.get(f"editing_{key}", False):
                    with st.form(key=f"form_{key}"):
                        new_value = st.text_area(
                            "新值（JSON格式）",
                            value=current_value,
                            height=100
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 保存"):
                                # Validate JSON
                                try:
                                    json.loads(new_value)
                                    if update_config_with_sync(api, key, new_value):
                                        st.session_state[f"editing_{key}"] = False
                                        st.rerun()
                                except json.JSONDecodeError:
                                    st.error("❌ JSON格式错误，请检查")

                        with col2:
                            if st.form_submit_button("❌ 取消"):
                                st.session_state[f"editing_{key}"] = False
                                st.rerun()

            elif config_type == 'textarea':
                new_value = st.text_area(
                    "",
                    value=current_value,
                    height=100,
                    key=f"config_{key}",
                    label_visibility="collapsed"
                )

                if new_value != current_value:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 保存", key=f"save_{key}"):
                            if update_config_with_sync(api, key, new_value):
                                st.rerun()
                    with col2:
                        if st.button("❌ 取消", key=f"cancel_{key}"):
                            st.rerun()

            else:  # text
                new_value = st.text_input(
                    "",
                    value=current_value,
                    key=f"config_{key}",
                    label_visibility="collapsed"
                )

                if new_value != current_value:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("💾 保存", key=f"save_{key}"):
                            if update_config_with_sync(api, key, new_value):
                                st.rerun()
                    with col2:
                        if st.button("❌ 取消", key=f"cancel_{key}"):
                            st.rerun()

        st.markdown("---")


def show_all_config(config: List[Dict]):
    """Show all configurations in a table"""
    st.subheader("所有配置项")

    # Search filter
    search_query = st.text_input("🔍 搜索配置", placeholder="输入配置项名称或关键字")

    config_data = []
    for item in config:
        if isinstance(item, dict):
            key = item.get('key', 'N/A')
            value = item.get('value', 'N/A')

            # Apply search filter
            if search_query and search_query.lower() not in key.lower() and search_query.lower() not in str(
                    value).lower():
                continue

            # Get definition info
            definition = CONFIG_DEFINITIONS.get(key, {})
            category = definition.get('category', 'other')
            label = definition.get('label', key)

            config_data.append({
                '配置项': label,
                '键名': key,
                '当前值': str(value)[:50] + '...' if len(str(value)) > 50 else str(value),
                '分类': get_category_name(category),
                '更新时间': item.get('updated_at', 'N/A')
            })

    if config_data:
        import pandas as pd
        df = pd.DataFrame(config_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export config
        st.markdown("---")
        if st.button("📥 导出配置"):
            config_export = {item['key']: item['value'] for item in config if isinstance(item, dict)}
            json_str = json.dumps(config_export, indent=2, ensure_ascii=False)
            st.download_button(
                label="下载 JSON",
                data=json_str,
                file_name=f"system_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("没有找到匹配的配置项")


def get_category_name(category: str) -> str:
    """Get Chinese name for category"""
    category_names = {
        'basic': '基本设置',
        'file': '文件设置',
        'display': '显示设置',
        'maintenance': '维护设置',
        'advanced': '高级设置',
        'other': '其他'
    }
    return category_names.get(category, '其他')


def show_config_help():
    """Show configuration help documentation"""
    st.markdown("""
    ### 配置项说明

    **基本设置**
    - **维护模式**: 开启后系统进入维护状态，只有管理员可以访问
    - **允许用户注册**: 控制是否开放新用户注册
    - **需要邮箱验证**: 开启后新用户必须验证邮箱才能使用

    **文件设置**
    - **最大文件大小**: 限制单个上传文件的大小，防止服务器过载
    - **允许的文件类型**: 系统支持处理的文件格式列表
    - **最大行数限制**: 防止处理过大的文件导致内存不足

    **显示设置**
    - **系统公告**: 向所有用户显示的通知消息，支持HTML格式

    **维护设置**
    - **数据清理周期**: 自动清理过期数据的时间间隔

    **高级设置**
    - **启用统计分析**: 是否收集使用数据用于分析
    - **API 速率限制**: 防止API被滥用的请求频率限制

    ### 注意事项
    1. 修改配置后会立即生效
    2. 某些配置可能需要刷新页面才能看到效果
    3. JSON格式的配置请确保格式正确
    4. 建议在修改前导出备份当前配置
    """)
