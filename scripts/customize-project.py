#!/usr/bin/env python3
import json
import os
import re

def load_payload():
    """Load build configuration from GitHub event"""
    # For repository_dispatch events
    if 'GITHUB_EVENT_NAME' in os.environ and os.environ['GITHUB_EVENT_NAME'] == 'repository_dispatch':
        with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
            event_data = json.load(f)
        return event_data.get('client_payload', {})
    
    # For workflow_dispatch events
    if 'GITHUB_EVENT_NAME' in os.environ and os.environ['GITHUB_EVENT_NAME'] == 'workflow_dispatch':
        with open(os.environ['GITHUB_EVENT_PATH'], 'r') as f:
            event_data = json.load(f)
        return event_data.get('inputs', {})
    
    return {}

def customize_build_gradle(project_path, config):
    """Modify TWA settings in build.gradle"""
    build_gradle_path = os.path.join(project_path, 'app/build.gradle')
    
    with open(build_gradle_path, 'r') as f:
        content = f.read()
    
    print(f"🔧 Customizing for: {config.get('hostName', 'example.com')}")
    
    # Replace TWA settings
    replacements = {
        r"hostName:\s*'[^']*'": f"hostName: '{config.get('hostName', 'example.com')}'",
        r"launchUrl:\s*'[^']*'": f"launchUrl: '{config.get('launchUrl', '/')}'",
        r"name:\s*'[^']*'": f"name: '{config.get('name', 'My PWA')}'",
        r"launcherName:\s*'[^']*'": f"launcherName: '{config.get('launcherName', config.get('name', 'My PWA'))}'",
        r"themeColor:\s*'[^']*'": f"themeColor: '{config.get('themeColor', '#FFFFFF')}'",
        r"backgroundColor:\s*'[^']*'": f"backgroundColor: '{config.get('backgroundColor', '#FFFFFF')}'"
    }
    
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    with open(build_gradle_path, 'w') as f:
        f.write(content)
    
    print("✅ build.gradle customized")

def main():
    config = load_payload()
    project_path = "android-project"
    
    if not config:
        print("❌ No configuration found")
        return
    
    customize_build_gradle(project_path, config)
    print("✅ Project customization completed")

if __name__ == "__main__":
    main()
