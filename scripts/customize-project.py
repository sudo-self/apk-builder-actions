#!/usr/bin/env python3
import json
import os
import shutil
import re

def load_payload():
    """Load build configuration from GitHub event"""
    with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
        event_data = json.load(f)
    return event_data['client_payload']

def customize_build_gradle(project_path, config):
    """Modify build.gradle with custom settings"""
    build_gradle_path = os.path.join(project_path, 'app/build.gradle')
    
    with open(build_gradle_path, 'r') as f:
        content = f.read()
    
    # Replace TWA settings
    replacements = {
        r"hostName:\s*'[^']*'": f"hostName: '{config['hostName']}'",
        r"launchUrl:\s*'[^']*'": f"launchUrl: '{config['launchUrl']}'",
        r"name:\s*'[^']*'": f"name: '{config['name']}'",
        r"launcherName:\s*'[^']*'": f"launcherName: '{config['launcherName']}'",
        r"themeColor:\s*'[^']*'": f"themeColor: '{config['themeColor']}'",
        r"themeColorDark:\s*'[^']*'": f"themeColorDark: '{config['themeColorDark']}'",
        r"backgroundColor:\s*'[^']*'": f"backgroundColor: '{config['backgroundColor']}'"
    }
    
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    with open(build_gradle_path, 'w') as f:
        f.write(content)
    
    print("✅ build.gradle customized")

def process_icons(project_path, build_id):
    """Replace app icons if custom icon was provided"""
    icon_path = f"/tmp/{build_id}/icon.png"
    
    if not os.path.exists(icon_path):
        print("ℹ️  No custom icon provided, using default")
        return
    
    # Define all icon directories (same as your original logic)
    icon_configs = [
        {'dir': 'mipmap-hdpi', 'files': ['ic_launcher.png', 'ic_launcher_round.png']},
        {'dir': 'mipmap-mdpi', 'files': ['ic_launcher.png', 'ic_launcher_round.png']},
        {'dir': 'mipmap-xhdpi', 'files': ['ic_launcher.png', 'ic_launcher_round.png']},
        {'dir': 'mipmap-xxhdpi', 'files': ['ic_launcher.png', 'ic_launcher_round.png']},
        {'dir': 'mipmap-xxxhdpi', 'files': ['ic_launcher.png', 'ic_launcher_round.png']},
        {'dir': 'drawable', 'files': ['store_icon.png']}
    ]
    
    icons_replaced = 0
    for config in icon_configs:
        target_dir = os.path.join(project_path, 'app/src/main/res', config['dir'])
        
        if not os.path.exists(target_dir):
            continue
            
        for icon_file in config['files']:
            target_path = os.path.join(target_dir, icon_file)
            if os.path.exists(target_path):
                shutil.copy(icon_path, target_path)
                icons_replaced += 1
    
    print(f"✅ Replaced {icons_replaced} icon files")

def main():
    config = load_payload()
    project_path = "android-project"
    
    print(f"🔧 Customizing APK for: {config['hostName']}")
    
    customize_build_gradle(project_path, config)
    process_icons(project_path, config['buildId'])
    
    print("✅ Project customization completed")

if __name__ == "__main__":
    main()
