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

def generate_package_name(host_name):
    """Generate a valid Android package name from host name."""
    # Remove protocol and paths
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '')
    clean_host = clean_host.split('/')[0].split('?')[0].split(':')[0]
    clean_host = clean_host.rstrip('/').strip()
    
    log(f"Cleaned hostname: {clean_host}")
    
    # Split by dots and reverse for package name (com.example instead of example.com)
    parts = clean_host.split('.')
    
    # Remove empty parts
    parts = [part for part in parts if part and part.strip()]
    
    if len(parts) >= 2:
        # Reverse domain for package name (com.example)
        reversed_parts = list(reversed(parts))
        package_name = '.'.join(reversed_parts)
    else:
        # Single part domain, use com. prefix
        package_name = f"com.{clean_host}" if parts else "com.webapp.generated"
    
    # Validate and fix package name
    package_name = re.sub(r'[^a-zA-Z0-9._]', '_', package_name)
    
    # Ensure it starts with a letter and has valid segments
    segments = package_name.split('.')
    cleaned_segments = []
    
    for segment in segments:
        if not segment:
            continue
        # Ensure segment starts with a letter
        if segment[0].isdigit():
            segment = 'a' + segment
        # Remove any remaining invalid characters
        segment = re.sub(r'[^a-zA-Z0-9_]', '', segment)
        if segment:
            cleaned_segments.append(segment)
    
    # Ensure we have at least 2 segments
    if len(cleaned_segments) < 2:
        cleaned_segments = ['com', 'webapp'] + cleaned_segments
    
    final_package = '.'.join(cleaned_segments).lower()
    
    log(f"Generated package name: {final_package}")
    return final_package

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
    
    # Generate package name first
    package_name = generate_package_name(host_name)
    
    # Update build.gradle (app level)
    build_gradle_path = app_dir / 'build.gradle'
    if build_gradle_path.exists():
        log(f"Updating {build_gradle_path}...")
        content = build_gradle_path.read_text()
        
        # Update applicationId
        if 'applicationId' in content:
            content = re.sub(
                r'applicationId\s+"[^"]*"',
                f'applicationId "{package_name}"',
                content
            )
            build_gradle_path.write_text(content)
            log(f"Updated applicationId to {package_name}")
    
    # Update build.gradle.kts (Kotlin DSL)
    build_gradle_kts_path = app_dir / 'build.gradle.kts'
    if build_gradle_kts_path.exists():
        log(f"Updating {build_gradle_kts_path}...")
        content = build_gradle_kts_path.read_text()
        
        if 'applicationId' in content:
            content = re.sub(
                r'applicationId\s*=\s*"[^"]*"',
                f'applicationId = "{package_name}"',
                content
            )
            build_gradle_kts_path.write_text(content)
            log(f"Updated applicationId in build.gradle.kts to {package_name}")
    
    # Update AndroidManifest.xml
    manifest_path = app_dir / 'src' / 'main' / 'AndroidManifest.xml'
    if manifest_path.exists():
        log(f"Updating {manifest_path}...")
        content = manifest_path.read_text()
        
        # Update package name in manifest
        if 'package="' in content:
            content = re.sub(
                r'package="[^"]*"',
                f'package="{package_name}"',
                content
            )
        
        # Update the host name in the intent filter
        content = re.sub(
            r'android:host="[^"]*"',
            f'android:host="{host_name}"',
            content
        )
        
        manifest_path.write_text(content)
        log("AndroidManifest.xml updated successfully")
    
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
        if launcher_name != app_name:
            if '<string name="launcher_name">' in content:
                content = re.sub(
                    r'<string name="launcher_name">.*?</string>',
                    f'<string name="launcher_name">{launcher_name}</string>',
                    content
                )
        
        # Update host name for TWA
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
        
        strings_path.write_text(content)
        log("strings.xml updated successfully")
    
    # Update colors.xml
    colors_path = app_dir / 'src' / 'main' / 'res' / 'values' / 'colors.xml'
    if colors_path.exists():
        log(f"Updating {colors_path}...")
        content = colors_path.read_text()
        
        # Update theme color
        if '<color name="colorPrimary">' in content:
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
    
    log("Android project customization completed successfully!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
