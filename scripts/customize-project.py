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
        else:
            # Add it if it doesn't exist
            content = content.replace('</resources>', f'    <color name="colorPrimary">{theme_color}</color>\n</resources>')
        
        # Update theme color dark
        if '<color name="colorPrimaryDark">' in content:
            content = re.sub(
                r'<color name="colorPrimaryDark">.*?</color>',
                f'<color name="colorPrimaryDark">{theme_color_dark}</color>',
                content
            )
        else:
            content = content.replace('</resources>', f'    <color name="colorPrimaryDark">{theme_color_dark}</color>\n</resources>')
        
        # Update background color
        if '<color name="backgroundColor">' in content:
            content = re.sub(
                r'<color name="backgroundColor">.*?</color>',
                f'<color name="backgroundColor">{background_color}</color>',
                content
            )
        else:
            content = content.replace('</resources>', f'    <color name="backgroundColor">{background_color}</color>\n</resources>')
        
        # Update navigationBarColor if it exists
        if '<color name="navigationBarColor">' in content:
            content = re.sub(
                r'<color name="navigationBarColor">.*?</color>',
                f'<color name="navigationBarColor">{theme_color_dark}</color>',
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
        
        # Update applicationId based on domain
        if 'applicationId' in content:
            # Clean the hostname and generate a valid package name
            clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '')
            # Remove any trailing slashes and paths
            clean_host = clean_host.split('/')[0].rstrip('/')
            
            log(f"Cleaned hostname: {clean_host}")
            
            # Split by dots and reverse for package name convention
            parts = clean_host.split('.')
            if len(parts) >= 2:
                # Standard domain like "example.com" -> "com.example"
                # Take TLD and first part of domain
                package_name = f"{parts[-1]}.{parts[0]}"
            else:
                # Single part domain, use com. prefix
                package_name = f"com.{clean_host}"
            
            # Replace any invalid characters with underscore
            package_name = re.sub(r'[^a-zA-Z0-9.]', '_', package_name)
            
            # Ensure no numbers at start of segments
            package_parts = package_name.split('.')
            package_parts = [f"_{part}" if part and part[0].isdigit() else part for part in package_parts if part]
            package_name = '.'.join(package_parts)
            
            # Ensure package name is lowercase (Android convention)
            package_name = package_name.lower()
            
            log(f"Generated package name: {package_name}")
            
            content = re.sub(
                r'applicationId\s+"[^"]*"',
                f'applicationId "{package_name}"',
                content
            )
            build_gradle_path.write_text(content)
            log(f"Updated applicationId to {package_name}")
        else:
            log("No applicationId found in build.gradle")
    else:
        log(f"WARNING: {build_gradle_path} not found")
    
    # Check for build.gradle.kts (Kotlin DSL)
    build_gradle_kts_path = app_dir / 'build.gradle.kts'
    if build_gradle_kts_path.exists():
        log(f"Checking {build_gradle_kts_path}...")
        content = build_gradle_kts_path.read_text()
        
        if 'applicationId' in content:
            # Clean the hostname
            clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '')
            clean_host = clean_host.split('/')[0].rstrip('/')
            
            parts = clean_host.split('.')
            if len(parts) >= 2:
                package_name = f"{parts[-1]}.{parts[0]}"
            else:
                package_name = f"com.{clean_host}"
            
            package_name = re.sub(r'[^a-zA-Z0-9.]', '_', package_name)
            package_parts = package_name.split('.')
            package_parts = [f"_{part}" if part and part[0].isdigit() else part for part in package_parts if part]
            package_name = '.'.join(package_parts).lower()
            
            log(f"Generated package name (KTS): {package_name}")
            
            content = re.sub(
                r'applicationId\s*=\s*"[^"]*"',
                f'applicationId = "{package_name}"',
                content
            )
            build_gradle_kts_path.write_text(content)
            log(f"Updated applicationId in build.gradle.kts to {package_name}")
    
    # Create a build info file for debugging
    build_info = {
        'build_id': build_id,
        'host_name': host_name,
        'launch_url': launch_url,
        'app_name': app_name,
        'launcher_name': launcher_name,
        'theme_color': theme_color,
        'theme_color_dark': theme_color_dark,
        'background_color': background_color,
        'timestamp': str(Path(__file__).stat().st_mtime)
    }
    
    build_info_path = project_dir / 'build-info.json'
    build_info_path.write_text(json.dumps(build_info, indent=2))
    log(f"Created build info file at {build_info_path}")
    
    # Log the build info
    log("Build configuration:")
    log(json.dumps(build_info, indent=2))
    
    log("Android project customization completed successfully!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
