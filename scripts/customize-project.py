#!/usr/bin/env python3
import json
import os
import re
import sys

def load_payload():
    """Load build configuration from GitHub event with better debugging"""
    print("🔍 Loading payload...")
    print(f"GITHUB_EVENT_NAME: {os.environ.get('GITHUB_EVENT_NAME')}")
    print(f"GITHUB_EVENT_PATH: {os.environ.get('GITHUB_EVENT_PATH')}")
    
    event_path = os.environ.get('GITHUB_EVENT_PATH')
    
    if event_path and os.path.exists(event_path):
        print("📄 Event file exists, reading...")
        with open(event_path, 'r') as f:
            event_data = json.load(f)
        
        print("📋 Full event data structure:")
        print(json.dumps(event_data, indent=2))
        
        # For repository_dispatch events
        if 'client_payload' in event_data:
            print("✅ Found client_payload in event data")
            return event_data['client_payload']
        else:
            print("❌ client_payload not found in event data")
            print("Available keys:", list(event_data.keys()))
    
    # For workflow_dispatch events
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        print("🔄 Handling workflow_dispatch event")
        if event_path and os.path.exists(event_path):
            with open(event_path, 'r') as f:
                event_data = json.load(f)
            
            if 'inputs' in event_data:
                print("✅ Found inputs in workflow_dispatch")
                return event_data['inputs']
    
    # Fallback for testing
    print("⚠️ Using fallback test configuration")
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
    print(f"🔧 Customizing Android project at: {project_path}")
    
    build_gradle_path = os.path.join(project_path, 'app/build.gradle')
    
    if not os.path.exists(build_gradle_path):
        print(f"❌ build.gradle not found at: {build_gradle_path}")
        # Try to find it
        for root, dirs, files in os.walk(project_path):
            if 'build.gradle' in files:
                build_gradle_path = os.path.join(root, 'build.gradle')
                print(f"✅ Found build.gradle at: {build_gradle_path}")
                break
        else:
            print("❌ Could not find build.gradle anywhere")
            return False
    
    print(f"📝 Reading build.gradle from: {build_gradle_path}")
    
    with open(build_gradle_path, 'r') as f:
        content = f.read()
    
    print(f"🎯 Customizing for: {config.get('hostName', 'example.com')}")
    print(f"📱 App Name: {config.get('name', 'Test App')}")
    
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
        else:
            print(f"⚠️ Pattern not found: {pattern}")
    
    print(f"💾 Writing updated build.gradle...")
    with open(build_gradle_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {changes_made} TWA settings in build.gradle")
    return changes_made > 0

def main():
    print("🚀 Starting APK customization...")
    
    config = load_payload()
    project_path = "android-project"
    
    print("📋 Configuration loaded:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    if not os.path.exists(project_path):
        print(f"❌ Project path not found: {project_path}")
        print("Current directory contents:")
        print(os.listdir('.'))
        sys.exit(1)
    
    print("📁 Project directory contents:")
    print(os.listdir(project_path))
    
    success = customize_build_gradle(project_path, config)
    
    if success:
        print("✅ Project customization completed successfully")
    else:
        print("❌ Project customization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
