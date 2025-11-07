#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
import traceback
import base64
from PIL import Image
import io
import urllib.request
import subprocess
import requests

# -----------------------------
# Logging
# -----------------------------
def log(msg):
    print(f"[CUSTOMIZE] {msg}")

def read_env_or_fail(key, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

# -----------------------------
# Package & Manifest Utilities
# -----------------------------
def generate_package_name(host_name: str):
    try:
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
    except Exception as e:
        log(f"ERROR generating package name: {e}")
        return "com.webapp.generated"

def update_twa_manifest_in_gradle(build_gradle_path: Path, package_name: str):
    if not build_gradle_path.exists():
        log(f"ERROR: {build_gradle_path} not found")
        return False
    try:
        content = build_gradle_path.read_text()
        content = re.sub(r'namespace\s+["\'].*?["\']', f'namespace "{package_name}"', content)
        content = re.sub(r'applicationId\s+["\'].*?["\']', f'applicationId "{package_name}"', content)
        build_gradle_path.write_text(content)
        log(f"Updated build.gradle with package {package_name}")
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
        new_content = re.sub(r'\s*package="[^"]*"', '', content)
        if new_content != content:
            manifest_path.write_text(new_content)
            log("Removed deprecated package attribute from AndroidManifest.xml")
        return True
    except Exception as e:
        log(f"ERROR updating manifest: {e}")
        return False

def update_strings_xml(app_dir: Path, app_name: str, host_name: str, launch_url: str):
    res_dir = app_dir / 'app/src/main/res'
    strings_path = res_dir / 'values/strings.xml'
    if not strings_path.exists():
        log(f"ERROR: strings.xml not found at {strings_path}")
        return False
    try:
        content = strings_path.read_text()
        if not launch_url.startswith("http"):
            if not launch_url.startswith("/"):
                launch_url = "/" + launch_url
            host_clean = host_name.replace("https://", "").replace("http://", "")
            launch_url = f"https://{host_clean}{launch_url}"

        content = re.sub(r'<string name="app_name">[^<]*</string>', f'<string name="app_name">{app_name}</string>', content)
        content = re.sub(r'<string name="launch_url">[^<]*</string>', f'<string name="launch_url">{launch_url}</string>', content)
        strings_path.write_text(content)
        log("Updated strings.xml")
        return True
    except Exception as e:
        log(f"ERROR updating strings.xml: {e}")
        return False

def update_java_kotlin_package(app_dir: Path, old_package: str, new_package: str):
    java_dir = app_dir / 'app/src/main/java'
    if not java_dir.exists():
        log(f"WARNING: Java source directory not found at {java_dir}")
        return False
    source_files = list(java_dir.rglob('*.java')) + list(java_dir.rglob('*.kt'))
    updated_count = 0
    for f in source_files:
        try:
            content = f.read_text()
            if f"package {old_package}" in content:
                content = content.replace(f"package {old_package}", f"package {new_package}")
                updated_count += 1
            content = re.sub(fr'import {re.escape(old_package)}', f'import {new_package}', content)
            f.write_text(content)
        except Exception as e:
            log(f"ERROR updating {f}: {e}")
    log(f"Updated package references in {updated_count} source files")
    return updated_count > 0

# -----------------------------
# Icon Utilities
# -----------------------------
def download_icon_from_url(icon_url: str):
    try:
        log(f"Downloading icon from: {icon_url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(icon_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        log(f"Downloaded icon ({len(data)} bytes)")
        return data
    except Exception as e:
        log(f"ERROR downloading icon: {e}")
        return None

def download_vector_foreground(vector_url: str):
    """Download vector XML content"""
    try:
        log(f"Downloading vector from: {vector_url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(vector_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
        log(f"Downloaded vector ({len(data)} bytes)")
        return data
    except Exception as e:
        log(f"ERROR downloading vector: {e}")
        return None

def clean_existing_icons(res_dir: Path):
    mipmaps = ['mipmap-mdpi','mipmap-hdpi','mipmap-xhdpi','mipmap-xxhdpi','mipmap-xxxhdpi']
    count = 0
    for m in mipmaps:
        d = res_dir / m
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and any(name in f.name for name in ['ic_launcher','ic_foreground']):
                    try:
                        f.unlink()
                        count +=1
                        log(f"Removed {f}")
                    except: pass
    log(f"Cleaned {count} existing icons")
    return count

def create_webp_icon(image: Image.Image, output_path: Path, size: int):
    try:
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        image.resize((size, size), Image.Resampling.LANCZOS).save(output_path, format='WEBP', quality=90, method=6)
        if output_path.exists() and output_path.stat().st_size > 100:
            log(f"Created {output_path.name} ({size}x{size})")
            return True
        return False
    except Exception as e:
        log(f"ERROR creating WebP icon {output_path}: {e}")
        return False

def create_adaptive_foreground_icon(res_dir: Path, icon_choice: str):
    """Create the appropriate foreground vector drawable based on icon_choice"""
    drawable_dir = res_dir / 'drawable'
    drawable_dir.mkdir(parents=True, exist_ok=True)
    
    # Vector foreground URLs for adaptive icons
    vector_foregrounds = {
        "phone": "https://pub-c1de1cb456e74d6bbbee111ba9e6c757.r2.dev/phone.xml",
        "rocket": "https://pub-c1de1cb456e74d6bbbee111ba9e6c757.r2.dev/rocket.xml",
        "shield": "https://pub-c1de1cb456e74d6bbbee111ba9e6c757.r2.dev/shield.xml"
    }
    
    if icon_choice in vector_foregrounds:
        vector_content = download_vector_foreground(vector_foregrounds[icon_choice])
        if vector_content:
            foreground_path = drawable_dir / 'ic_launcher_phone_foreground.xml'
            foreground_path.write_text(vector_content)
            log(f"Created {icon_choice} foreground vector icon")
            return True
        else:
            log(f"Failed to download {icon_choice} vector, falling back to phone")
    
    # Fallback to default phone foreground
    return create_phone_foreground_icon(res_dir)

def create_phone_foreground_icon(res_dir: Path):
    """Create the phone foreground vector drawable (fallback)"""
    drawable_dir = res_dir / 'drawable'
    drawable_dir.mkdir(parents=True, exist_ok=True)
    
    phone_foreground_content = '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path android:pathData="M24,24L84,24L84,84L24,84z">
        <aapt:attr name="android:fillColor">
            <gradient
                android:endX="85.84757"
                android:endY="92.4963"
                android:startX="42.9492"
                android:startY="49.59793"
                android:type="linear">
                <item
                    android:color="#44000000"
                    android:offset="0.0" />
                <item
                    android:color="#00000000"
                    android:offset="1.0" />
            </gradient>
        </aapt:attr>
    </path>
    <path
        android:fillColor="#3B82F6"
        android:fillType="nonZero"
        android:pathData="M32,32L76,32L76,76L32,76z"
        android:strokeWidth="1"
        android:strokeColor="#00000000" />
    <path
        android:fillColor="#FFFFFF"
        android:fillType="nonZero"
        android:pathData="M54,40L54,68"
        android:strokeWidth="3"
        android:strokeColor="#FFFFFF" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M50,34a4,4 0,1 1,8 0a4,4 0,1 1,-8 0z" />
</vector>'''
    
    phone_foreground_path = drawable_dir / 'ic_launcher_phone_foreground.xml'
    phone_foreground_path.write_text(phone_foreground_content)
    log("Created phone foreground vector icon (fallback)")
    return True

def create_adaptive_icon_config(res_dir: Path):
    """Create the adaptive icon configuration for API 26+"""
    mipmap_v26_dir = res_dir / 'mipmap-anydpi-v26'
    mipmap_v26_dir.mkdir(parents=True, exist_ok=True)
    
    adaptive_icon_content = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_phone_foreground"/>
</adaptive-icon>'''
    
    adaptive_icon_path = mipmap_v26_dir / 'ic_launcher.xml'
    adaptive_icon_path.write_text(adaptive_icon_content)
    log("Created adaptive icon configuration for API 26+")
    return True

def create_launcher_background_color(res_dir: Path):
    """Create the launcher background color resource"""
    colors_path = res_dir / 'values/colors.xml'
    
    # Read existing colors or create new
    if colors_path.exists():
        content = colors_path.read_text()
        # Check if ic_launcher_background already exists
        if 'ic_launcher_background' not in content:
            # Add it before the closing </resources> tag
            content = content.replace('</resources>', '    <color name="ic_launcher_background">#3B82F6</color>\n</resources>')
            colors_path.write_text(content)
            log("Added ic_launcher_background color to colors.xml")
    else:
        # Create colors.xml if it doesn't exist
        colors_content = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#3B82F6</color>
</resources>'''
        colors_path.write_text(colors_content)
        log("Created colors.xml with ic_launcher_background")
    
    return True

def set_launcher_icons(app_dir: Path, icon_choice: str = None, icon_base64: str = None):
    res_dir = app_dir / 'app/src/main/res'
    if not res_dir.exists():
        log(f"ERROR: Resources directory not found at {res_dir}")
        return True
    clean_existing_icons(res_dir)

    icon_urls = {
        "phone": "https://apk.jessejesse.com/phone-512.png",
        "rocket": "https://apk.jessejesse.com/rocket-512.png",
        "shield": "https://apk.jessejesse.com/shield-512.png"
    }

    img = None
    if icon_base64:
        try:
            img = Image.open(io.BytesIO(base64.b64decode(icon_base64)))
            log(f"Loaded base64 icon ({img.size[0]}x{img.size[1]})")
        except Exception as e:
            log(f"ERROR decoding base64 icon: {e}")

    if img is None and icon_choice in icon_urls:
        data = download_icon_from_url(icon_urls[icon_choice])
        if data:
            try:
                img = Image.open(io.BytesIO(data))
                log(f"Loaded downloaded icon ({img.size[0]}x{img.size[1]})")
            except Exception as e:
                log(f"ERROR loading downloaded icon: {e}")

    if img is None:
        log("No icon available; using default template")
        return True

    sizes = {'mipmap-mdpi':48,'mipmap-hdpi':72,'mipmap-xhdpi':96,'mipmap-xxhdpi':144,'mipmap-xxxhdpi':192}
    total_expected = len(sizes)*2+2
    created_count = 0
    try:
        for mipmap,size in sizes.items():
            dir_path = res_dir / mipmap
            dir_path.mkdir(parents=True, exist_ok=True)
            if create_webp_icon(img, dir_path/'ic_launcher.webp', size): created_count+=1
            if create_webp_icon(img, dir_path/'ic_launcher_round.webp', size): created_count+=1

        # Create the appropriate foreground vector icon based on choice
        create_adaptive_foreground_icon(res_dir, icon_choice)
        
        # Create the adaptive icon configuration
        create_adaptive_icon_config(res_dir)
        
        # Create the background color
        create_launcher_background_color(res_dir)

        log(f"Icon creation: {created_count}/{total_expected} successful")
        return True
    except Exception as e:
        log(f"ERROR creating icons: {e}")
        return True

# -----------------------------
# GitHub Release
# -----------------------------
def publish_github_release(repo: str, tag: str, token: str, release_name: str, body: str=""):
    url = f"https://api.github.com/repos/{repo}/releases"
    headers = {"Authorization": f"token {token}", "Accept":"application/vnd.github+json"}
    data = {"tag_name": tag, "name": release_name, "body": body, "draft": False, "prerelease": False}
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code==201:
            log(f"Release '{release_name}' published successfully!")
            return True
        else:
            log(f"ERROR publishing release: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        log(f"ERROR publishing release: {e}")
        return False

# -----------------------------
# Main
# -----------------------------
def main():
    log("="*60)
    log("Starting Android project customization...")
    log("="*60)

    try:
        build_id = os.getenv('BUILD_ID','local')
        host_name = read_env_or_fail('HOST_NAME')
        app_name = read_env_or_fail('APP_NAME')
        launch_url = os.getenv('LAUNCH_URL','/')
        launcher_name = os.getenv('LAUNCHER_NAME',app_name)
        theme_color = os.getenv('THEME_COLOR','#171717')
        theme_color_dark = os.getenv('THEME_COLOR_DARK','#000000')
        background_color = os.getenv('BACKGROUND_COLOR','#FFFFFF')
        icon_choice = os.getenv('ICON_CHOICE','phone')
        icon_base64 = os.getenv('ICON_BASE64')
        publish_release = os.getenv('PUBLISH_RELEASE','false').lower()=='true'
        app_dir = Path(os.getenv('APP_DIR', 'android-project'))

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
        log(f"Using app directory: {app_dir.resolve()}")

        if not app_dir.exists():
            log("App directory not found; cloning template_apk...")
            subprocess.run(['git','clone','https://github.com/sudo-self/template_apk.git', str(app_dir)], check=True)

        package_name = generate_package_name(host_name)
        build_gradle = app_dir / 'app/build.gradle'
        update_twa_manifest_in_gradle(build_gradle, package_name)
        manifest_path = app_dir / 'app/src/main/AndroidManifest.xml'
        update_manifest_remove_package(manifest_path)
        update_strings_xml(app_dir, app_name, host_name, launch_url)
        old_package = "com.example.githubactionapks"
        update_java_kotlin_package(app_dir, old_package, package_name)
        set_launcher_icons(app_dir, icon_choice, icon_base64)

        if publish_release:
            github_repo = read_env_or_fail('GITHUB_REPO')
            github_token = read_env_or_fail('GITHUB_TOKEN')
            release_tag = read_env_or_fail('RELEASE_TAG')
            release_name = os.getenv('RELEASE_NAME', release_tag)
            release_body = os.getenv('RELEASE_BODY', f"Automated release {release_tag}")
            log("Publishing GitHub release...")
            publish_github_release(github_repo, release_tag, github_token, release_name, release_body)

        log("="*60)
        log("Android project customization completed successfully!")
        log("="*60)
        return 0

    except Exception as e:
        log(f"UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__=='__main__':
    sys.exit(main())

























