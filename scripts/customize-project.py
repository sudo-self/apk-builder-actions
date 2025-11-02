#!/usr/bin/env python3

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import traceback

def log(msg):
    print(f"[CUSTOMIZE] {msg}")

def read_env_or_fail(key, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def generate_package_name(host_name: str):
    """Generate a valid Android package name from host name."""
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
    parts = [p for p in clean_host.split('.') if p]
    
    if len(parts) >= 2:
        package_name = '.'.join(reversed(parts))
    else:
        package_name = f"com.{clean_host}" if parts else "com.webapp.generated"

    segments = []
    for segment in package_name.split('.'):
        if segment and segment[0].isdigit():
            segment = 'a' + segment
        segment = re.sub(r'[^a-zA-Z0-9_]', '', segment)
        if segment:
            segments.append(segment)
    
    if len(segments) < 2:
        segments = ['com', 'webapp'] + segments
    
    final_package = '.'.join(segments).lower()
    log(f"Generated package name: {final_package}")
    return final_package

def ensure_resources(res_dir: Path):
    """Ensure resource directories exist."""
    res_dir.mkdir(parents=True, exist_ok=True)
    values_dir = res_dir / 'values'
    values_dir.mkdir(exist_ok=True)
    return values_dir

def create_strings_xml(values_dir, app_name, launcher_name, host_name, launch_url):
    """Create or update strings.xml with app configuration."""
    path = values_dir / 'strings.xml'
    package_name = generate_package_name(host_name)
    provider_authority = f"{package_name}.fileprovider"
    
    # Clean the host name for use in strings
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    
    content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="appName">{app_name}</string>
    <string name="launcherName">{launcher_name}</string>
    <string name="hostName">{clean_host}</string>
    <string name="launchUrl">{launch_url}</string>
    <string name="providerAuthority">{provider_authority}</string>
</resources>'''
    
    path.write_text(content, encoding='utf-8')
    log(f"Created/updated strings.xml at {path}")

def create_colors_xml(values_dir, theme_color, theme_color_dark, background_color):
    """Create or update colors.xml with theme colors."""
    path = values_dir / 'colors.xml'
    
    # Ensure colors start with #
    def ensure_hash(color):
        return color if color.startswith('#') else f'#{color}'
    
    theme_color = ensure_hash(theme_color)
    theme_color_dark = ensure_hash(theme_color_dark)
    background_color = ensure_hash(background_color)
    
    content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">{theme_color}</color>
    <color name="colorPrimaryDark">{theme_color_dark}</color>
    <color name="backgroundColor">{background_color}</color>
    <color name="navigationBarColor">{theme_color_dark}</color>
    <color name="statusBarColor">{theme_color_dark}</color>
</resources>'''
    
    path.write_text(content, encoding='utf-8')
    log(f"Created/updated colors.xml at {path}")

def update_gradle(build_gradle_path: Path, package_name: str):
    """Update build.gradle with package name and configuration."""
    if not build_gradle_path.exists():
        log(f"Warning: {build_gradle_path} not found")
        return
    
    content = build_gradle_path.read_text()
    original = content
    is_kts = build_gradle_path.suffix == '.kts'

    # For Kotlin DSL
    if is_kts:
        # Update namespace
        if 'namespace' in content:
            content = re.sub(
                r'namespace\s*=\s*"[^"]*"',
                f'namespace = "{package_name}"',
                content
            )
            log("Updated namespace in build.gradle.kts")
        else:
            content = re.sub(
                r'(android\s*\{)',
                f'\\1\n    namespace = "{package_name}"',
                content,
                count=1
            )
            log("Added namespace to build.gradle.kts")
        
        # Update applicationId
        if 'applicationId' in content:
            content = re.sub(
                r'applicationId\s*=\s*"[^"]*"',
                f'applicationId = "{package_name}"',
                content
            )
            log("Updated applicationId in build.gradle.kts")
        else:
            content = re.sub(
                r'(defaultConfig\s*\{)',
                f'\\1\n        applicationId = "{package_name}"',
                content,
                count=1
            )
            log("Added applicationId to build.gradle.kts")
    
    # For Groovy DSL
    else:
        # Update or add namespace (matches both syntaxes: namespace "..." and namespace = "...")
        namespace_pattern = r'namespace\s*[=]?\s*["\'][^"\']*["\']'
        if re.search(namespace_pattern, content):
            content = re.sub(
                namespace_pattern,
                f'namespace "{package_name}"',
                content
            )
            log("Updated namespace in build.gradle")
        else:
            # Add namespace after android { opening
            content = re.sub(
                r'(android\s*\{)',
                f'\\1\n    namespace "{package_name}"',
                content,
                count=1
            )
            log("Added namespace to build.gradle")
        
        # Update or add applicationId
        appid_pattern = r'applicationId\s*[=]?\s*["\'][^"\']*["\']'
        if re.search(appid_pattern, content):
            content = re.sub(
                appid_pattern,
                f'applicationId "{package_name}"',
                content
            )
            log("Updated applicationId in build.gradle")
        else:
            # Add applicationId after defaultConfig { opening
            content = re.sub(
                r'(defaultConfig\s*\{)',
                f'\\1\n        applicationId "{package_name}"',
                content,
                count=1
            )
            log("Added applicationId to build.gradle")

    if content != original:
        build_gradle_path.write_text(content)
        log(f"✅ Saved changes to {build_gradle_path}")
    else:
        log(f"No changes needed for {build_gradle_path}")

def update_manifest(manifest_path: Path, host_name: str, package_name: str):
    """Update AndroidManifest.xml with package name and host."""
    if not manifest_path.exists():
        log(f"ERROR: Manifest not found at {manifest_path}")
        return False
    
    try:
        content = manifest_path.read_text()
        
        # Update package attribute
        content = re.sub(r'package="[^"]*"', f'package="{package_name}"', content)
        
        # Clean the host name
        clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        
        # Update android:host attributes (for intent filters)
        content = re.sub(r'android:host="[^"]*"', f'android:host="{clean_host}"', content)
        
        manifest_path.write_text(content)
        log(f"Updated AndroidManifest.xml with package={package_name} and host={clean_host}")
        return True
        
    except Exception as e:
        log(f"ERROR updating manifest: {e}")
        return False

def main():
    log("=" * 60)
    log("Starting Android project customization...")
    log("=" * 60)
    
    try:
        # Read environment variables
        # BUILD_ID is optional, not used in the script
        build_id = os.getenv('BUILD_ID', 'local')
        
        # Required variables
        host_name = read_env_or_fail('HOST_NAME')
        app_name = read_env_or_fail('APP_NAME')
        
        # Optional variables with defaults
        launch_url = os.getenv('LAUNCH_URL', '/')
        launcher_name = os.getenv('LAUNCHER_NAME', app_name)
        theme_color = os.getenv('THEME_COLOR', '#171717')
        theme_color_dark = os.getenv('THEME_COLOR_DARK', '#000000')
        background_color = os.getenv('BACKGROUND_COLOR', '#FFFFFF')

        log(f"Build ID: {build_id}")
        log(f"Host: {host_name}")
        log(f"App Name: {app_name}")
        log(f"Launcher Name: {launcher_name}")
        log(f"Launch URL: {launch_url}")

        # Locate android project
        app_dir = Path('android-project/app')
        if not app_dir.exists():
            log(f"ERROR: App directory not found at {app_dir.resolve()}")
            log("Current directory contents:")
            for item in Path('.').iterdir():
                log(f"  - {item}")
            return 1
        
        main_dir = app_dir / 'src/main'
        if not main_dir.exists():
            log(f"ERROR: src/main not found at {main_dir.resolve()}")
            return 1
            
        log(f"Using app directory: {app_dir.resolve()}")

        # Generate package name
        package_name = generate_package_name(host_name)
        log("=" * 60)

        # Update Gradle build files
        log("Updating Gradle configuration...")
        for gradle_file in ['build.gradle', 'build.gradle.kts']:
            build_path = app_dir / gradle_file
            if build_path.exists():
                update_gradle(build_path, package_name)
        
        # Update AndroidManifest.xml
        log("Updating AndroidManifest.xml...")
        manifest_path = main_dir / 'AndroidManifest.xml'
        if not update_manifest(manifest_path, host_name, package_name):
            log("WARNING: Failed to update manifest, but continuing...")

        # Update resource files
        log("Creating/updating resource files...")
        res_dir = main_dir / 'res'
        values_dir = ensure_resources(res_dir)
        
        create_strings_xml(values_dir, app_name, launcher_name, host_name, launch_url)
        create_colors_xml(values_dir, theme_color, theme_color_dark, background_color)

        log("=" * 60)
        log("✅ Android project customization completed successfully!")
        log("=" * 60)
        return 0

    except ValueError as e:
        log("=" * 60)
        log(f"❌ ERROR: {e}")
        log("=" * 60)
        log("\nEnvironment variables received:")
        for key in ['BUILD_ID', 'HOST_NAME', 'LAUNCH_URL', 'APP_NAME', 'LAUNCHER_NAME', 
                    'THEME_COLOR', 'THEME_COLOR_DARK', 'BACKGROUND_COLOR']:
            value = os.getenv(key, '<not set>')
            log(f"  {key}: {value}")
        return 1
        
    except Exception as e:
        log("=" * 60)
        log(f"❌ UNEXPECTED ERROR: {e}")
        log("=" * 60)
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())






