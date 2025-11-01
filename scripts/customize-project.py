#!/usr/bin/env python3
"""
Customize the Android project with user-provided values.
This script modifies the Android project files to match the build configuration.
"""

import os
import re
import json
from pathlib import Path

def log(message):
    """Print a log message."""
    print(f"[CUSTOMIZE] {message}")

def read_env_or_fail(key, default=None):
    """Read an environment variable or use default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def main():
    log("Starting Android project customization...")
    
    # Read environment variables
    build_id = read_env_or_fail('BUILD_ID')
    host_name = read_env_or_fail('HOST_NAME')
    launch_url = read_env_or_fail('LAUNCH_URL', '/')
    app_name = read_env_or_fail('APP_NAME')
    launcher_name = read_env_or_fail('LAUNCHER_NAME', app_name)
    theme_color = read_env_or_fail('THEME_COLOR', '#171717')
    theme_color_dark = read_env_or_fail('THEME_COLOR_DARK', '#000000')
    background_color = read_env_or_fail('BACKGROUND_COLOR', '#FFFFFF')
    
    log(f"Build ID: {build_id}")
    log(f"Host Name: {host_name}")
    log(f"Launch URL: {launch_url}")
    log(f"App Name: {app_name}")
    log(f"Launcher Name: {launcher_name}")
    log(f"Theme Color: {theme_color}")
    log(f"Theme Color Dark: {theme_color_dark}")
    log(f"Background Color: {background_color}")
    
    # Project paths
    project_dir = Path('android-project')
    app_dir = project_dir / 'app'
    
    # Update strings.xml
    strings_path = app_dir / 'src' / 'main' / 'res' / 'values' / 'strings.xml'
    if strings_path.exists():
        log(f"Updating {strings_path}...")
        content = strings_path.read_text()
        
        # Replace app name
        content = re.sub(
            r'<string name="app_name">.*?</string>',
            f'<string name="app_name">{app_name}</string>',
            content
        )
        
        # Replace launcher name if different
        if '<string name="launcher_name">' in content:
            content = re.sub(
                r'<string name="launcher_name">.*?</string>',
                f'<string name="launcher_name">{launcher_name}</string>',
                content
            )
        
        strings_path.write_text(content)
        log("strings.xml updated successfully")
    else:
        log(f"WARNING: {strings_path} not found")
    
    # Update AndroidManifest.xml
    manifest_path = app_dir / 'src' / 'main' / 'AndroidManifest.xml'
    if manifest_path.exists():
        log(f"Updating {manifest_path}...")
        content = manifest_path.read_text()
        
        # Update the host name in the intent filter
        content = re.sub(
            r'android:host="[^"]*"',
            f'android:host="{host_name}"',
            content
        )
        
        manifest_path.write_text(content)
        log("AndroidManifest.xml updated successfully")
    else:
        log(f"WARNING: {manifest_path} not found")
    
    # Update TWA configuration (if exists)
    # This is typically in res/values/strings.xml or a separate config file
    twa_config_path = app_dir / 'src' / 'main' / 'res' / 'values' / 'strings.xml'
    if twa_config_path.exists():
        log(f"Updating TWA configuration in {twa_config_path}...")
        content = twa_config_path.read_text()
        
        # Update host
        if '<string name="host">' in content or '<string name="hostName">' in content:
            content = re.sub(
                r'<string name="host(?:Name)?">.*?</string>',
                f'<string name="hostName">{host_name}</string>',
                content
            )
        
        # Update launch URL
        if '<string name="launchUrl">' in content:
            content = re.sub(
                r'<string name="launchUrl">.*?</string>',
                f'<string name="launchUrl">{launch_url}</string>',
                content
            )
        
        twa_config_path.write_text(content)
        log("TWA configuration updated successfully")
    
    # Update colors.xml
    colors_path = app_dir / 'src' / 'main' / 'res' / 'values' / 'colors.xml'
    if colors_path.exists():
        log(f"Updating {colors_path}...")
        content = colors_path.read_text()
        
        # Update theme color
        content = re.sub(
            r'<color name="colorPrimary">.*?</color>',
            f'<color name="colorPrimary">{theme_color}</color>',
            content
        )
        
        # Update theme color dark
        if '<color name="colorPrimaryDark">' in content:
            content = re.sub(
                r'<color name="colorPrimaryDark">.*?</color>',
                f'<color name="colorPrimaryDark">{theme_color_dark}</color>',
                content
            )
        
        # Update background color
        if '<color name="backgroundColor">' in content:
            content = re.sub(
                r'<color name="backgroundColor">.*?</color>',
                f'<color name="backgroundColor">{background_color}</color>',
                content
            )
        
        colors_path.write_text(content)
        log("colors.xml updated successfully")
    else:
        log(f"WARNING: {colors_path} not found")
    
    # Update build.gradle (app level) if needed
    build_gradle_path = app_dir / 'build.gradle'
    if build_gradle_path.exists():
        log(f"Checking {build_gradle_path}...")
        content = build_gradle_path.read_text()
        
        # You can update version codes, application IDs, etc. here if needed
        # For example, update applicationId based on domain
        if 'applicationId' in content:
            # Generate a package name from the domain
            package_name = 'com.' + host_name.replace('.', '_').replace('-', '_')
            content = re.sub(
                r'applicationId\s+"[^"]*"',
                f'applicationId "{package_name}"',
                content
            )
            build_gradle_path.write_text(content)
            log(f"Updated applicationId to {package_name}")
    else:
        log(f"WARNING: {build_gradle_path} not found")
    
    # Create a build info file for debugging
    build_info = {
        'build_id': build_id,
        'host_name': host_name,
        'launch_url': launch_url,
        'app_name': app_name,
        'launcher_name': launcher_name,
        'theme_color': theme_color,
        'theme_color_dark': theme_color_dark,
        'background_color': background_color
    }
    
    build_info_path = project_dir / 'build-info.json'
    build_info_path.write_text(json.dumps(build_info, indent=2))
    log(f"Created build info file at {build_info_path}")
    
    log("Android project customization completed successfully!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
