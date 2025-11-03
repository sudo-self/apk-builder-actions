#!/usr/bin/env python3

import os
import re
from pathlib import Path
import traceback
import base64
from PIL import Image
import io
import urllib.request
import urllib.error
import shutil

def log(msg):
    print(f"[CUSTOMIZE] {msg}")

def read_env_or_fail(key, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def generate_package_name(host_name: str):
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '')
    clean_host = clean_host.split('/')[0].split('?')[0].split(':')[0]
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
    if not build_gradle_path.exists():
        log(f"ERROR: {build_gradle_path} not found")
        return False
    try:
        content = build_gradle_path.read_text()
        clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].split('?')[0]
        patterns = {
            r"applicationId\s*:\s*['\"].*?['\"]": f"applicationId: '{package_name}'",
            r"hostName\s*:\s*['\"].*?['\"]": f"hostName: '{clean_host}'",
            r"launchUrl\s*:\s*['\"].*?['\"]": f"launchUrl: '{launch_url}'",
            r"name\s*:\s*['\"].*?['\"]": f"name: '{app_name}'",
            r"launcherName\s*:\s*['\"].*?['\"]": f"launcherName: '{launcher_name}'",
        }
        for pattern, replacement in patterns.items():
            content = re.sub(pattern, replacement, content)
            log(f"Updated: {replacement}")
        def ensure_hash(color):
            color = color.strip()
            if not color.startswith('#'):
                return f'#{color}'
            return color
        theme_color = ensure_hash(theme_color)
        theme_color_dark = ensure_hash(theme_color_dark)
        background_color = ensure_hash(background_color)
        color_patterns = {
            r"themeColor\s*:\s*['\"].*?['\"]": f"themeColor: '{theme_color}'",
            r"themeColorDark\s*:\s*['\"].*?['\"]": f"themeColorDark: '{theme_color_dark}'",
            r"backgroundColor\s*:\s*['\"].*?['\"]": f"backgroundColor: '{background_color}'",
        }
        for pattern, replacement in color_patterns.items():
            content = re.sub(pattern, replacement, content)
            log(f"Updated: {replacement}")
        content = re.sub(
            r'namespace\s+["\'].*?["\']',
            f'namespace "{package_name}"',
            content
        )
        log(f"Set namespace to {package_name}")
        content = re.sub(
            r'applicationId\s+["\'].*?["\']',
            f'applicationId "{package_name}"',
            content
        )
        log(f"Set applicationId to {package_name}")
        build_gradle_path.write_text(content)
        log(f"Successfully updated {build_gradle_path}")
        return True
    except Exception as e:
        log(f"ERROR updating build.gradle: {e}")
        return False

def update_manifest_remove_package(manifest_path: Path):
    if not manifest_path.exists():
        log(f"WARNING: Manifest not found at {manifest_path}")
        return False
    try:
        content = manifest_path.read_text()
        original_content = content
        content = re.sub(r'\s*package="[^"]*"', '', content)
        if content != original_content:
            manifest_path.write_text(content)
            log("Removed deprecated package attribute from AndroidManifest.xml")
        else:
            log("No package attribute found in manifest (already clean)")
        return True
    except Exception as e:
        log(f"ERROR updating manifest: {e}")
        return False

def download_icon_from_url(icon_url: str):
    try:
        log(f"Downloading icon from: {icon_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        req = urllib.request.Request(icon_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            icon_data = response.read()
        log("Successfully downloaded icon")
        return icon_data
    except urllib.error.URLError as e:
        log(f"URL error downloading icon: {e}")
    except Exception as e:
        log(f"ERROR downloading icon: {e}")
    return None

def clean_existing_icons(res_dir: Path):
    mipmap_dirs = ['mipmap-mdpi', 'mipmap-hdpi', 'mipmap-xhdpi', 'mipmap-xxhdpi', 'mipmap-xxxhdpi']
    cleaned_count = 0
    for mipmap_dir in mipmap_dirs:
        dir_path = res_dir / mipmap_dir
        if dir_path.exists():
            for file_path in dir_path.iterdir():
                if file_path.is_file() and file_path.name.startswith('ic_launcher'):
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        log(f"Removed existing icon: {file_path}")
                    except Exception as e:
                        log(f"ERROR removing {file_path}: {e}")
            v26_dir = res_dir / f"{mipmap_dir}-v26"
            if v26_dir.exists():
                for file_path in v26_dir.iterdir():
                    if file_path.is_file() and file_path.name.startswith('ic_launcher'):
                        try:
                            file_path.unlink()
                            cleaned_count += 1
                            log(f"Removed adaptive icon: {file_path}")
                        except Exception as e:
                            log(f"ERROR removing adaptive {file_path}: {e}")
    log(f"Cleaned {cleaned_count} existing icon files")
    return cleaned_count

def set_launcher_icons(app_dir: Path, icon_choice: str = None, icon_base64: str = None):
    res_dir = app_dir / 'src/main/res'
    clean_existing_icons(res_dir)
    icon_urls = {
        "phone": "https://apk.jessejesse.com/phone-512.png",
        "castle": "https://apk.jessejesse.com/castle-512.png", 
        "smile": "https://apk.jessejesse.com/smile-512.png"
    }
    img = None
    if icon_base64:
        log("Using provided base64 icon")
        try:
            icon_data = base64.b64decode(icon_base64)
            img = Image.open(io.BytesIO(icon_data))
        except Exception as e:
            log(f"ERROR decoding base64 icon: {e}")
            img = None
    if img is None and icon_choice and icon_choice in icon_urls:
        log(f"Downloading icon: {icon_choice}")
        icon_data = download_icon_from_url(icon_urls[icon_choice])
        if icon_data:
            try:
                img = Image.open(io.BytesIO(icon_data))
            except Exception as e:
                log(f"ERROR processing downloaded icon: {e}")
    if img is None:
        log("No custom icon available - using default template icons")
        return
    sizes = {
        'mipmap-mdpi': 48,
        'mipmap-hdpi': 72, 
        'mipmap-xhdpi': 96,
        'mipmap-xxhdpi': 144,
        'mipmap-xxxhdpi': 192
    }
    created_count = 0
    for mipmap, size in sizes.items():
        try:
            dir_path = res_dir / mipmap
            dir_path.mkdir(parents=True, exist_ok=True)
            target_file = dir_path / 'ic_launcher.png'
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(target_file, format='PNG', optimize=True)
            created_count += 1
            log(f"Created icon: {target_file} ({size}x{size})")
        except Exception as e:
            log(f"ERROR creating {mipmap} icon: {e}")
    log(f"Successfully created {created_count} icon files")

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
        icon_choice = os.getenv('ICON_CHOICE', 'phone')
        icon_base64 = os.getenv('ICON_BASE64')
        log(f"Build ID: {build_id}")
        log(f"Host: {host_name}")
        log(f"App Name: {app_name}")
        log(f"Launcher Name: {launcher_name}")
        log(f"Launch URL: {launch_url}")
        log(f"Theme Color: {theme_color}")
        log(f"Theme Color Dark: {theme_color_dark}") 
        log(f"Background Color: {background_color}")
        log(f"Icon Choice: {icon_choice}")
        log(f"Icon Base64 provided: {'Yes' if icon_base64 else 'No'}")
        app_dir = Path('android-project/app')
        if not app_dir.exists():
            alternative_paths = ['app', './app', '../app']
            for path in alternative_paths:
                if Path(path).exists():
                    app_dir = Path(path)
                    break
            else:
                log(f"ERROR: App directory not found. Checked: {app_dir.resolve()}")
                return 1
        main_dir = app_dir / 'src/main'
        if not main_dir.exists():
            log(f"ERROR: src/main not found at {main_dir.resolve()}")
            log("Available files:")
            for item in app_dir.iterdir():
                log(f"  - {item.name}")
            return 1
        log(f"Using app directory: {app_dir.resolve()}")
        package_name = generate_package_name(host_name)
        log("=" * 60)
        build_gradle = app_dir / 'build.gradle'
        log("Updating build.gradle with configuration...")
        if not update_twa_manifest_in_gradle(
            build_gradle, package_name, host_name, launch_url,
            app_name, launcher_name, theme_color, theme_color_dark, background_color
        ):
            log("WARNING: Failed to update build.gradle")
            return 1
        manifest_path = main_dir / 'AndroidManifest.xml'
        if not update_manifest_remove_package(manifest_path):
            log("WARNING: Failed to update AndroidManifest.xml")
        log("Setting up launcher icons...")
        set_launcher_icons(app_dir, icon_choice, icon_base64)
        log("=" * 60)
        log("Android project customization completed successfully!")
        log("=" * 60)
        return 0
    except ValueError as e:
        log(f"ERROR: {e}")
        return 1
    except Exception as e:
        log(f"UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())









