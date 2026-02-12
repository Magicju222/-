"""
Initialize System Configuration
Ensures all system config keys exist in the database with default values
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default system configurations
DEFAULT_CONFIGS = {
    'MAINTENANCE_MODE': 'false',
    'MAX_FILE_SIZE_MB': '50',
    'ALLOWED_EXTENSIONS': '["xlsx", "xls", "csv"]',
    'MAX_ROWS_PER_FILE': '100000',
    'ENABLE_USER_REGISTRATION': 'true',
    'REQUIRE_EMAIL_VERIFICATION': 'false',
    'SYSTEM_NOTICE': '',
    'CLEANUP_INTERVAL_DAYS': '30',
    'ENABLE_ANALYTICS': 'true',
    'API_RATE_LIMIT': '100'
}


def init_system_config():
    """Initialize system configuration in database"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")  # Use service key for admin operations

    if not url or not key:
        print("❌ 错误：缺少 Supabase 配置")
        print("请确保 .env 文件中包含 SUPABASE_URL 和 SUPABASE_SERVICE_KEY")
        return False

    try:
        supabase = create_client(url, key)

        print("🔌 连接到 Supabase...")

        # Check existing configs
        response = supabase.table("system_config").select("key").execute()
        existing_keys = {item['key'] for item in response.data} if response.data else set()

        print(f"📊 数据库中已有 {len(existing_keys)} 个配置项")

        # Add missing configs
        added_count = 0
        for key, value in DEFAULT_CONFIGS.items():
            if key not in existing_keys:
                result = supabase.table("system_config").insert({
                    "key": key,
                    "value": value
                }).execute()

                if result.data:
                    print(f"✅ 添加配置: {key} = {value}")
                    added_count += 1
                else:
                    print(f"❌ 添加配置失败: {key}")

        if added_count > 0:
            print(f"\n🎉 成功添加 {added_count} 个配置项")
        else:
            print("\n✨ 所有配置项已存在，无需添加")

        # Show all configs
        print("\n📋 当前系统配置:")
        print("-" * 60)

        response = supabase.table("system_config").select("key, value").execute()
        if response.data:
            for item in response.data:
                key = item['key']
                value = item['value']
                # Show default indicator
                is_default = key in DEFAULT_CONFIGS and DEFAULT_CONFIGS[key] == value
                indicator = " (默认)" if is_default else ""
                print(f"  {key}: {value}{indicator}")

        print("-" * 60)
        return True

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("系统配置初始化工具")
    print("=" * 60)
    print()

    success = init_system_config()

    print()
    if success:
        print("✅ 配置初始化完成")
    else:
        print("❌ 配置初始化失败")

    print("=" * 60)
