#!/usr/bin/env python3

import os
import re
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

def update_twa_manifest_in_gradle(build_gradle_path: Path, package_name: str, host_name: str, 
                                   launch_url: str, app_name: str, launcher_name: str,
                                   theme_color: str, theme_color_dark: str, background_color: str):
    """Update the twaManifest map in build.gradle."""
    if not build_gradle_path.exists():
        log(f"ERROR: {build_gradle_path} not found")
        return False
    
    content = build_gradle_path.read_text()
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
    
    # twaManifest values
    content = re.sub(
        r"applicationId:\s*['\"].*?['\"]",
        f"applicationId: '{package_name}'",
        content
    )
    log(f"Set applicationId to {package_name}")
    
    content = re.sub(
        r"hostName:\s*['\"].*?['\"]",
        f"hostName: '{clean_host}'",
        content
    )
    log(f"Set hostName to {clean_host}")
    
    content = re.sub(
        r"launchUrl:\s*['\"].*?['\"]",
        f"launchUrl: '{launch_url}'",
        content
    )
    log(f"Set launchUrl to {launch_url}")
    
    content = re.sub(
        r"name:\s*['\"].*?['\"],\s*//\s*The application name",
        f"name: '{app_name}', // The application name",
        content
    )
    log(f"Set name to {app_name}")
    
    content = re.sub(
        r"launcherName:\s*['\"].*?['\"]",
        f"launcherName: '{launcher_name}'",
        content
    )
    log(f"Set launcherName to {launcher_name}")
    
    # colors have prefix
    def ensure_hash(color):
        return color if color.startswith('#') else f'#{color}'
    
    theme_color = ensure_hash(theme_color)
    theme_color_dark = ensure_hash(theme_color_dark)
    background_color = ensure_hash(background_color)
    
    content = re.sub(
        r"themeColor:\s*['\"].*?['\"]",
        f"themeColor: '{theme_color}'",
        content
    )
    log(f"Set themeColor to {theme_color}")
    
    content = re.sub(
        r"themeColorDark:\s*['\"].*?['\"]",
        f"themeColorDark: '{theme_color_dark}'",
        content
    )
    log(f"Set themeColorDark to {theme_color_dark}")
    
    content = re.sub(
        r"backgroundColor:\s*['\"].*?['\"]",
        f"backgroundColor: '{background_color}'",
        content
    )
    log(f"Set backgroundColor to {background_color}")
    
    # namespace
    content = re.sub(
        r'namespace\s+".*?"',
        f'namespace "{package_name}"',
        content
    )
    
    # applicationId 
    content = re.sub(
        r'applicationId\s+".*?"',
        f'applicationId "{package_name}"',
        content
    )
    
    build_gradle_path.write_text(content)
    log(f"Updated {build_gradle_path}")
    return True

def update_manifest_remove_package(manifest_path: Path):
    """Remove deprecated package attribute from AndroidManifest.xml."""
    if not manifest_path.exists():
        log(f"WARNING: Manifest not found at {manifest_path}")
        return False
    
    try:
        content = manifest_path.read_text()
        
        # Remove package attribute (deprecated in AGP 7.0+)
        if 'package=' in content:
            content = re.sub(r'\s*package="[^"]*"', '', content)
            manifest_path.write_text(content)
            log("Removed deprecated package attribute from AndroidManifest.xml")
        else:
            log("No package attribute found in manifest (already clean)")
        
        return True
        
    except Exception as e:
        log(f"ERROR updating manifest: {e}")
        return False

def create_asset_links(values_dir: Path, host_name: str, package_name: str):
    """Create assetlinks.xml for Digital Asset Links verification."""
    values_dir.mkdir(parents=True, exist_ok=True)
    path = values_dir / 'assetlinks.xml'
    
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
    
    # UPDATE THIS LINE with your actual SHA256 fingerprint
    sha256_fingerprint = "A0:2C:AA:A7:1A:5D:AD:43:47:FD:BF:08:DB:97:30:30:6A:3C:EB:AC:11:C8:E2:3F:9A:5E:10:15:BE:0D:19:CC"
    
    content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="assetStatements">
        [{{"relation": ["delegate_permission/common.handle_all_urls"], 
          "target": {{"namespace": "web", "site": "https://{clean_host}"}}}},
         {{"relation": ["delegate_permission/common.handle_all_urls"],
          "target": {{"namespace": "android_app", "package_name": "{package_name}",
                      "sha256_cert_fingerprints": ["{sha256_fingerprint}"]}}}}]
    </string>
</resources>'''
    
    path.write_text(content, encoding='utf-8')
    log(f"Created assetlinks.xml at {path}")
    
def main():
    log("=" * 60)
    log("Starting Android project customization...")
    log("=" * 60)
    
    try:
    
        build_id = os.getenv('BUILD_ID', 'local')
        
     
        host_name = read_env_or_fail('HOST_NAME')
        app_name = read_env_or_fail('APP_NAME')
        
      
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

     
        app_dir = Path('android-project/app')
        if not app_dir.exists():
            log(f"ERROR: App directory not found at {app_dir.resolve()}")
            return 1
        
        main_dir = app_dir / 'src/main'
        if not main_dir.exists():
            log(f"ERROR: src/main not found at {main_dir.resolve()}")
            return 1
            
        log(f"Using app directory: {app_dir.resolve()}")

        # package name
        package_name = generate_package_name(host_name)
        log("=" * 60)

        # build.gradle
        log("Updating build.gradle with twaManifest configuration...")
        build_gradle = app_dir / 'build.gradle'
        if not update_twa_manifest_in_gradle(
            build_gradle, package_name, host_name, launch_url,
            app_name, launcher_name, theme_color, theme_color_dark, background_color
        ):
            log("WARNING: Failed to update build.gradle")
        
      
        log("Cleaning up AndroidManifest.xml...")
        manifest_path = main_dir / 'AndroidManifest.xml'
        update_manifest_remove_package(manifest_path)

        log("=" * 60)
        log("Android project customization completed successfully!")
        log("=" * 60)
        return 0

    except ValueError as e:
        log("=" * 60)
        log(f"ERROR: {e}")
        log("=" * 60)
        log("\nEnvironment variables received:")
        for key in ['BUILD_ID', 'HOST_NAME', 'LAUNCH_URL', 'APP_NAME', 'LAUNCHER_NAME', 
                    'THEME_COLOR', 'THEME_COLOR_DARK', 'BACKGROUND_COLOR']:
            value = os.getenv(key, '<not set>')
            log(f"  {key}: {value}")
        return 1
        
    except Exception as e:
        log("=" * 60)
        log(f"UNEXPECTED ERROR: {e}")
        log("=" * 60)
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())







