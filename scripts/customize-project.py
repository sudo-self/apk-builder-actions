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
    res_dir.mkdir(parents=True, exist_ok=True)
    values_dir = res_dir / 'values'
    values_dir.mkdir(exist_ok=True)
    return values_dir

def create_strings_xml(values_dir, app_name, launcher_name, host_name, launch_url):
    path = values_dir / 'strings.xml'
    content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="appName">{app_name}</string>
    <string name="launcherName">{launcher_name}</string>
    <string name="hostName">{host_name}</string>
    <string name="launchUrl">{launch_url}</string>
    <string name="providerAuthority">{generate_package_name(host_name)}.fileprovider</string>
</resources>'''
    path.write_text(content, encoding='utf-8')
    log(f"Updated strings.xml at {path}")

def create_colors_xml(values_dir, theme_color, theme_color_dark, background_color):
    path = values_dir / 'colors.xml'
    content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">{theme_color}</color>
    <color name="colorPrimaryDark">{theme_color_dark}</color>
    <color name="backgroundColor">{background_color}</color>
</resources>'''
    path.write_text(content, encoding='utf-8')
    log(f"Updated colors.xml at {path}")

def update_gradle(build_gradle_path: Path, package_name: str):
    if not build_gradle_path.exists():
        log(f"Warning: {build_gradle_path} not found")
        return
    content = build_gradle_path.read_text()
    original = content
    is_kts = build_gradle_path.suffix == '.kts'

    # Patterns
    ns_pat = r'namespace\s*[:=]\s*["\'].*?["\']'
    id_pat = r'applicationId\s*[:=]?\s*["\'].*?["\']'
    ns_repl = f'namespace = "{package_name}"' if is_kts else f'    namespace "{package_name}"'
    id_repl = f'applicationId = "{package_name}"' if is_kts else f'    applicationId "{package_name}"'

    if re.search(ns_pat, content, re.MULTILINE):
        content = re.sub(ns_pat, ns_repl, content, re.MULTILINE)
        log("Updated namespace in build.gradle")
    else:
        content = re.sub(r'(^\s*android\s*\{)', r'\1\n' + ns_repl, content, count=1, flags=re.MULTILINE)
        log("Inserted namespace in android block")

    if re.search(id_pat, content, re.MULTILINE):
        content = re.sub(id_pat, id_repl, content, re.MULTILINE)
        log("Updated applicationId in build.gradle")
    else:
        content = re.sub(r'(^\s*defaultConfig\s*\{)', r'\1\n' + id_repl, content, count=1, flags=re.MULTILINE)
        log("Inserted applicationId in defaultConfig")

    if content != original:
        build_gradle_path.write_text(content)
        log(f"Saved changes to {build_gradle_path}")

def update_manifest(manifest_path: Path, host_name: str):
    if not manifest_path.exists():
        log(f"Manifest not found: {manifest_path}")
        return False
    content = manifest_path.read_text()
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    content = re.sub(r'android:host="[^"]*"', f'android:host="{clean_host}"', content)
    manifest_path.write_text(content)
    log(f"Updated intent filter host in {manifest_path}")
    return True

def main():
    log("Starting Android project customization...")
    try:
        build_id = read_env_or_fail('BUILD_ID')
        host_name = read_env_or_fail('HOST_NAME')
        launch_url = os.getenv('LAUNCH_URL', '/')
        app_name = read_env_or_fail('APP_NAME')
        launcher_name = os.getenv('LAUNCHER_NAME', app_name)
        theme_color = os.getenv('THEME_COLOR', '#171717')
        theme_color_dark = os.getenv('THEME_COLOR_DARK', '#000000')
        background_color = os.getenv('BACKGROUND_COLOR', '#FFFFFF')

        possible_dirs = [Path('.'), Path('android-project'), Path('app'), Path('..') / 'android-project']
        app_dir = next((p / 'app' if (p / 'app' / 'src' / 'main').exists() else p for p in possible_dirs if (p / 'src' / 'main').exists()), None)
        if not app_dir:
            log("Error: Could not find Android project")
            return 1
        log(f"Using app dir: {app_dir.resolve()}")

        package_name = generate_package_name(host_name)

        for f in ['build.gradle', 'build.gradle.kts']:
            build_path = app_dir / f
            update_gradle(build_path, package_name)

        manifest_path = app_dir / 'src' / 'main' / 'AndroidManifest.xml'
        if not update_manifest(manifest_path, host_name):
            log("Failed to update manifest")
            return 1

        res_dir = app_dir / 'src' / 'main' / 'res'
        values_dir = ensure_resources(res_dir)
        create_strings_xml(values_dir, app_name, launcher_name, host_name, launch_url)
        create_colors_xml(values_dir, theme_color, theme_color_dark, background_color)

        log("✅ Android project customization completed!")
        return 0

    except Exception as e:
        log(f"❌ ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())




