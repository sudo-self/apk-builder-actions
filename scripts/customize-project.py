#!/usr/bin/env python3
import json
import os
import re
import sys

def load_payload():
    """Load build configuration from GitHub event"""
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    if event_path and os.path.exists(event_path):
        with open(event_path, 'r') as f:
            event_data = json.load(f)
        
        # For repository_dispatch events
        if 'client_payload' in event_data:
            return event_data['client_payload']
    
    # For workflow_dispatch events
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        if event_path and os.path.exists(event_path):
            with open(event_path, 'r') as f:
                event_data = json.load(f)
            return event_data.get('inputs', {})
    
    # Fallback for testing
    return {
        'buildId': os.environ.get('GITHUB_RUN_ID', 'test-build'),
        'hostName': 'example.com',
        'launchUrl': '/',
        'name': 'Test App',
        'launcherName': 'Test App',
        'themeColor': '#FFFFFF',
        'themeColorDark': '#000000',
        'backgroundColor': '#FFFFFF'
    }

def customize_build_gradle(project_path, config):
    """Modify TWA settings in build.gradle"""
    build_gradle_path = os.path.join(project_path, 'app/build.gradle')
    
    if not os.path.exists(build_gradle_path):
        print(f"❌ build.gradle not found at: {build_gradle_path}")
        return False
    
    with open(build_gradle_path, 'r') as f:
        content = f.read()
    
    print(f"🔧 Customizing for: {config.get('hostName', 'example.com')}")
    
    # Replace TWA settings
    replacements = {
        r"hostName:\s*'[^']*'": f"hostName: '{config.get('hostName', 'example.com')}'",
        r"launchUrl:\s*'[^']*'": f"launchUrl: '{config.get('launchUrl', '/')}'",
        r"name:\s*'[^']*'": f"name: '{config.get('name', 'Test App')}'",
        r"launcherName:\s*'[^']*'": f"launcherName: '{config.get('launcherName', config.get('name', 'Test App'))}'",
        r"themeColor:\s*'[^']*'": f"themeColor: '{config.get('themeColor', '#FFFFFF')}'",
        r"themeColorDark:\s*'[^']*'": f"themeColorDark: '{config.get('themeColorDark', '#000000')}'",
        r"backgroundColor:\s*'[^']*'": f"backgroundColor: '{config.get('backgroundColor', '#FFFFFF')}'"
    }
    
    changes_made = 0
    for pattern, replacement in replacements.items():
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made += 1
            print(f"✅ Updated: {pattern.split(':')[0].strip()}")
    
    with open(build_gradle_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {changes_made} TWA settings")
    return changes_made > 0

def main():
    print("🚀 Starting APK customization...")
    
    config = load_payload()
    project_path = "android-project"
    
    if not os.path.exists(project_path):
        print(f"❌ Project path not found: {project_path}")
        sys.exit(1)
    
    success = customize_build_gradle(project_path, config)
    
    if success:
        print("✅ Project customization completed")
    else:
        print("❌ Project customization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
