#!/usr/bin/env python3

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import traceback

def log(message):
    print(f"[CUSTOMIZE] {message}")

def read_env_or_fail(key, default=None):
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value

def generate_package_name(host_name):
    clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '')
    clean_host = clean_host.split('/')[0].split('?')[0].split(':')[0].strip()
    log(f"Cleaned hostname: {clean_host}")

    parts = [p for p in clean_host.split('.') if p]
    if len(parts) >= 2:
        reversed_parts = list(reversed(parts))
        package_name = '.'.join(reversed_parts)
    else:
        package_name = f"com.{clean_host}" if parts else "com.webapp.generated"

    package_name = re.sub(r'[^a-zA-Z0-9._]', '_', package_name)
    segments = package_name.split('.')
    cleaned_segments = []

    for segment in segments:
        if not segment:
            continue
        if segment[0].isdigit():
            segment = 'a' + segment
        segment = re.sub(r'[^a-zA-Z0-9_]', '', segment)
        if segment:
            cleaned_segments.append(segment)

    if len(cleaned_segments) < 2:
        cleaned_segments = ['com', 'webapp'] + cleaned_segments

    final_package = '.'.join(cleaned_segments).lower()
    log(f"Generated package name: {final_package}")
    return final_package

def ensure_resources_directory(res_dir):
    res_dir.mkdir(parents=True, exist_ok=True)
    values_dir = res_dir / 'values'
    values_dir.mkdir(exist_ok=True)
    return values_dir

def create_strings_xml(values_dir, app_name, launcher_name, host_name, launch_url):
    strings_path = values_dir / 'strings.xml'
    
    if strings_path.exists():
        tree = ET.parse(strings_path)
        root = tree.getroot()
        strings_map = {
            'appName': app_name,
            'launcherName': launcher_name,
            'hostName': host_name,
            'launchUrl': launch_url or '/'
        }
        for name, value in strings_map.items():
            existing = root.find(f"./string[@name='{name}']")
            if existing is not None:
                existing.text = value
            else:
                new_elem = ET.Element('string', {'name': name})
                new_elem.text = value
                root.append(new_elem)
        tree.write(strings_path, encoding='utf-8', xml_declaration=True)
    else:
        content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="appName">{app_name}</string>
    <string name="launcherName">{launcher_name}</string>
    <string name="hostName">{host_name}</string>
    <string name="launchUrl">{launch_url or '/'}</string>
</resources>'''
        strings_path.write_text(content, encoding='utf-8')
    
    log(f"Updated strings.xml at {strings_path}")

def create_colors_xml(values_dir, theme_color, theme_color_dark, background_color):
    colors_path = values_dir / 'colors.xml'
    if colors_path.exists():
        tree = ET.parse(colors_path)
        root = tree.getroot()
        colors_map = {
            'colorPrimary': theme_color,
            'colorPrimaryDark': theme_color_dark,
            'backgroundColor': background_color
        }
        for name, value in colors_map.items():
            existing = root.find(f"./color[@name='{name}']")
            if existing is not None:
                existing.text = value
            else:
                new_elem = ET.Element('color', {'name': name})
                new_elem.text = value
                root.append(new_elem)
        tree.write(colors_path, encoding='utf-8', xml_declaration=True)
    else:
        content = f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">{theme_color}</color>
    <color name="colorPrimaryDark">{theme_color_dark}</color>
    <color name="backgroundColor">{background_color}</color>
</resources>'''
        colors_path.write_text(content, encoding='utf-8')
    log(f"Updated colors.xml at {colors_path}")

def ensure_gradle_namespace_and_appid(build_gradle_path: Path, package_name: str):
    if not build_gradle_path.exists():
        log(f"Warning: {build_gradle_path} not found")
        return

    content = build_gradle_path.read_text()
    original = content
    is_kotlin_dsl = build_gradle_path.suffix == '.kts'
    if is_kotlin_dsl:
        namespace_pattern = r'^\s*namespace\s*=\s*["\'].*?["\']'
        application_id_pattern = r'^\s*applicationId\s*=\s*["\'].*?["\']'
        namespace_replacement = f'namespace = "{package_name}"'
        application_id_replacement = f'applicationId = "{package_name}"'
    else:
        namespace_pattern = r'^\s*namespace\s+["\'].*?["\']'
        application_id_pattern = r'applicationId\s+["\'].*?["\']'
        namespace_replacement = f'    namespace "{package_name}"'
        application_id_replacement = f'applicationId "{package_name}"'

    if re.search(namespace_pattern, content, flags=re.MULTILINE):
        content = re.sub(namespace_pattern, namespace_replacement, content, flags=re.MULTILINE)
        log("Replaced existing namespace")
    elif re.search(r'^\s*android\s*\{', content, flags=re.MULTILINE):
        indent = '    ' if not is_kotlin_dsl else '    '
        content = re.sub(r'(^\s*android\s*\{)', r'\1\n' + indent + namespace_replacement, content, count=1, flags=re.MULTILINE)
        log("Inserted namespace into android block")

    if re.search(application_id_pattern, content, flags=re.MULTILINE):
        content = re.sub(application_id_pattern, application_id_replacement, content, flags=re.MULTILINE)
        log("Replaced existing applicationId")
    elif re.search(r'^\s*defaultConfig\s*\{', content, flags=re.MULTILINE):
        indent = '        ' if not is_kotlin_dsl else '        '
        content = re.sub(r'(^\s*defaultConfig\s*\{)', r'\1\n' + indent + application_id_replacement, content, count=1, flags=re.MULTILINE)
        log("Inserted applicationId into defaultConfig")

    if content != original:
        build_gradle_path.write_text(content)
        log(f"Updated {build_gradle_path}")
    else:
        log(f"No changes required for {build_gradle_path}")

def ensure_manifest_package(manifest_path: Path, package_name: str):
    if not manifest_path.exists():
        log(f"Error: {manifest_path} not found - this is required!")
        return False
    content = manifest_path.read_text()
    original = content
    if re.search(r'<manifest[^>]*\bpackage\s*=\s*["\'][^"\']*["\']', content):
        content = re.sub(r'(<manifest[^>]*\b)package\s*=\s*["\'][^"\']*["\']', r'\1package="' + package_name + '"', content, count=1)
        log("Replaced existing package attribute")
    else:
        content = re.sub(r'(<manifest\b)([^>]*)', r'\1 package="' + package_name + r'"\2', content, count=1)
        log("Inserted package attribute")

    host_name = os.getenv("HOST_NAME", "")
    if host_name:
        clean_host = host_name.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        content = re.sub(r'android:host="[^"]*"', f'android:host="{clean_host}"', content)
        log(f"Updated intent filter host to: {clean_host}")

    if content != original:
        manifest_path.write_text(content)
        log(f"Updated {manifest_path}")
        return True
    return True

def main():
    log("Starting enhanced Android project customization...")
    try:
        build_id = read_env_or_fail('BUILD_ID')
        host_name = read_env_or_fail('HOST_NAME')
        launch_url = os.getenv('LAUNCH_URL', '/')
        app_name = read_env_or_fail('APP_NAME')
        launcher_name = os.getenv('LAUNCHER_NAME', app_name)
        theme_color = os.getenv('THEME_COLOR', '#171717')
        theme_color_dark = os.getenv('THEME_COLOR_DARK', '#000000')
        background_color = os.getenv('BACKGROUND_COLOR', '#FFFFFF')

        log(f"Build ID: {build_id}")
        log(f"Host Name: {host_name}")
        log(f"Launch URL: {launch_url}")
        log(f"App Name: {app_name}")

        possible_dirs = [Path('.'), Path('android-project'), Path('app'), Path('..') / 'android-project']
        app_dir = None
        for possible in possible_dirs:
            if (possible / 'src' / 'main').exists():
                app_dir = possible
                break
            elif (possible / 'app' / 'src' / 'main').exists():
                app_dir = possible / 'app'
                break
        if not app_dir:
            log("Error: Could not find Android project directory")
            return 1
        log(f"Using app directory: {app_dir.resolve()}")

        package_name = generate_package_name(host_name)

        for build_file in ['build.gradle', 'build.gradle.kts']:
            build_path = app_dir / build_file
            if build_path.exists():
                ensure_gradle_namespace_and_appid(build_path, package_name)

        main_dir = app_dir / 'src' / 'main'
        manifest_path = main_dir / 'AndroidManifest.xml'
        if not ensure_manifest_package(manifest_path, package_name):
            log("Error: Failed to update AndroidManifest.xml")
            return 1

        res_dir = main_dir / 'res'
        values_dir = ensure_resources_directory(res_dir)

        create_strings_xml(values_dir, app_name, launcher_name, host_name, launch_url)
        create_colors_xml(values_dir, theme_color, theme_color_dark, background_color)

        log("✅ Android project customization completed successfully!")
        return 0

    except Exception as e:
        log(f"❌ ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())



