import zipfile
import os

def pack_project():
    # Files to include
    files_to_pack = [
        'app.py',
        'auth.py',
        'cleaner.py',
        'ui.py',
        'i18n.py',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'style.css',
        '.env.example',
        'README.md'
    ]
    
    # Folders to include (recursively)
    folders_to_pack = [
        '.streamlit'
    ]

    zip_filename = "deploy_package.zip"
    
    print(f"📦 Packing files into {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        for file in files_to_pack:
            if os.path.exists(file):
                print(f"  - Adding {file}")
                zipf.write(file)
            else:
                print(f"  ⚠️ Warning: {file} not found!")
        
        # Add folders
        for folder in folders_to_pack:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Don't pack secrets.toml for security, user should set env vars on server
                        # But for convenience in this specific guide, we might include config.toml
                        if 'secrets.toml' in file:
                            continue 
                        
                        print(f"  - Adding {file_path}")
                        zipf.write(file_path)

    print(f"\n✅ Successfully created {zip_filename}!")
    print("👉 Upload this file to your server to deploy.")

if __name__ == "__main__":
    pack_project()
