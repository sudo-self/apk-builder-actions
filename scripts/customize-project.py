#!/usr/bin/env python3
"""
Customize the Android project with user-provided values.
This script modifies the Android project files to match the build configuration.

Fixes included:
- Generate a safe package name from HOST_NAME
- Ensure app/build.gradle (or build.gradle.kts) has matching namespace and applicationId
- Ensure AndroidManifest.xml package attribute matches the Gradle namespace (insert/replace)
- Update strings.xml and colors.xml safely (replace or insert)
- Clear logging for CI visibility
"""

import os
import re
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

def replace_xml_tag(content, tag, value, insert_if_missing=False):
    pattern = f'<string name="{tag}">.*?</string>'
    if re.search(pattern, content):
        return re.sub(pattern, f'<string name="{tag}">{value}</string>', content)
    elif insert_if_missing:
        return content.replace('</resources>', f'    <string name="{tag}">{value}</string>\n</resources>')
    else:
        return content

def ensure_gradle_namespace_and_appid(build_gradle_path: Path, package_name: str):
    """Ensure namespace and applicationId exist and match the package_name in a Groovy build.gradle"""
    content = build_gradle_path.read_text()
    original = content

    # Ensure namespace "com.example"
    if re.search(r'^\s*namespace\s+["\'].*?["\']', content, flags=re.MULTILINE):
        content = re.sub(r'^\s*namespace\s+["\'].*?["\']', f'    namespace "{package_name}"', content, flags=re.MULTILINE)
        log("Replaced existing namespace in build.gradle")
    else:
        # Insert namespace after first 'android {' occurrence
        if re.search(r'^\s*android\s*\{', content, flags=re.MULTILINE):
            content = re.sub(r'(^\s*android\s*\{)', r'\1\n    namespace "' + package_name + '"', content, count=1, flags=re.MULTILINE)
            log("Inserted namespace into build.gradle (android block)")
        else:
            log("Could not find android { block to insert namespace into build.gradle")

    # Ensure applicationId "com.example"
    if re.search(r'applicationId\s+["\'].*?["\']', content):
        content = re.sub(r'applicationId\s+["\'].*?["\']', f'applicationId "{package_name}"', content)
        log("Replaced existing applicationId in build.gradle")
    else:
        # Insert into defaultConfig block if present
        if re.search(r'^\s*defaultConfig\s*\{', content, flags=re.MULTILINE):
            content = re.sub(r'(^\s*defaultConfig\s*\{)', r'\1\n        applicationId "' + package_name + '"', content, count=1, flags=re.MULTILINE)
            log("Inserted applicationId into defaultConfig in build.gradle")
        else:
            # As a fallback, append applicationId at end of file (not ideal but avoids missing appId)
            content += f'\n// Added by customize-project.py\nandroid {{\n    defaultConfig {{\n        applicationId "{package_name}"\n    }}\n}}\n'
            log("Appended android.defaultConfig.applicationId fallback to build.gradle")

    if content != original:
        build_gradle_path.write_text(content)
        log(f"Updated {build_gradle_path}")
    else:
        log(f"No changes required for {build_gradle_path}")

def ensure_kts_namespace_and_appid(build_gradle_kts_path: Path, package_name: str):
    """Ensure namespace and applicationId exist in Kotlin DSL build.gradle.kts"""
    content = build_gradle_kts_path.read_text()
    original = content

    # Namespace pattern: namespace = "com.example"
    if re.search(r'^\s*namespace\s*=\s*["\'].*?["\']', content, flags=re.MULTILINE):
        content = re.sub(r'^\s*namespace\s*=\s*["\'].*?["\']', f'namespace = "{package_name}"', content, flags=re.MULTILINE)
        log("Replaced existing namespace in build.gradle.kts")
    else:
        if re.search(r'^\s*android\s*\{', content, flags=re.MULTILINE):
            content = re.sub(r'(^\s*android\s*\{)', r'\1\n    namespace = "' + package_name + '"', content, count=1, flags=re.MULTILINE)
            log("Inserted namespace into build.gradle.kts (android block)")
        else:
            log("Could not find android { block to insert namespace into build.gradle.kts")

    # applicationId in kts is usually inside defaultConfig: applicationId = "com.example"
    if re.search(r'^\s*applicationId\s*=\s*["\'].*?["\']', content, flags=re.MULTILINE):
        content = re.sub(r'^\s*applicationId\s*=\s*["\'].*?["\']', f'applicationId = "{package_name}"', content, flags=re.MULTILINE)
        log("Replaced existing applicationId in build.gradle.kts")
    else:
        if re.search(r'^\s*defaultConfig\s*\{', content, flags=re.MULTILINE):
            content = re.sub(r'(^\s*defaultConfig\s*\{)', r'\1\n        applicationId = "' + package_name + '"', content, count=1, flags=re.MULTILINE)
            log("Inserted applicationId into defaultConfig in build.gradle.kts")
        else:
            content += f'\n// Added by customize-project.py\nandroid {{\n    defaultConfig {{\n        applicationId = "{package_name}"\n    }}\n}}\n'
            log("Appended android.defaultConfig.applicationId fallback to build.gradle.kts")

    if content != original:
        build_gradle_kts_path.write_text(content)
        log(f"Updated {build_gradle_kts_path}")
    else:
        log(f"No changes required for {build_gradle_kts_path}")

def ensure_manifest_package(manifest_path: Path, package_name: str):
    """Ensure AndroidManifest.xml has a package attribute matching package_name.
       If manifest has package attribute, replace it. If missing, insert it into the <manifest ...> tag."""
    content = manifest_path.read_text()
    original = content

    if re.search(r'<manifest[^>]*\bpackage\s*=\s*["\'][^"\']*["\']', content):
        content = re.sub(r'(<manifest[^>]*\b)package\s*=\s*["\'][^"\']*["\']', r'\1package="' + package_name + '"', content, count=1)
        log("Replaced existing package attribute in AndroidManifest.xml")
    else:
        # Insert package attribute into the opening <manifest ...> tag
        content = re.sub(r'(<manifest\b)([^>]*)', r'\1 package="' + package_name + r'"\2', content, count=1)
        log("Inserted package attribute into AndroidManifest.xml")

    # Update any android:host occurrences (for TWA intent filter host)
    content = re.sub(r'android:host="[^"]*"', f'android:host="{os.getenv("HOST_NAME", "")}"', content)

    if content != original:
        manifest_path.write_text(content)
        log(f"Updated {manifest_path}")
    else:
        log(f"No changes required for {manifest_path}")

def main():
    log("Starting Android project customization...")

    try:
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

        # Paths (assume script is executed from android-project directory or parent; use cwd .)
        cwd = Path.cwd()
        # If script is copied to android-project and run from there, app dir is ./app
        app_dir = Path('.') / 'app'
        if not app_dir.exists():
            # also try cwd/android-project/app
            possible = cwd / 'android-project' / 'app'
            if possible.exists():
                app_dir = possible
        log(f"Using app dir: {app_dir.resolve()}")

        # Generate package name
        package_name = generate_package_name(host_name)

        # Update build.gradle (Groovy)
        build_gradle_path = app_dir / 'build.gradle'
        if build_gradle_path.exists():
            log(f"Updating {build_gradle_path}...")
            ensure_gradle_namespace_and_appid(build_gradle_path, package_name)
        else:
            log(f"No {build_gradle_path} found, skipping")

        # Update build.gradle.kts (Kotlin DSL)
        build_gradle_kts_path = app_dir / 'build.gradle.kts'
        if build_gradle_kts_path.exists():
            log(f"Updating {build_gradle_kts_path}...")
            ensure_kts_namespace_and_appid(build_gradle_kts_path, package_name)
        else:
            log(f"No {build_gradle_kts_path} found, skipping")

        # Update AndroidManifest.xml
        manifest_path = app_dir / 'src' / 'main' / 'AndroidManifest.xml'
        if manifest_path.exists():
            log(f"Updating {manifest_path}...")
            ensure_manifest_package(manifest_path, package_name)
        else:
            log(f"No manifest at {manifest_path}, skipping")

        # Update strings.xml
        strings_path = app_dir / 'src' / 'main' / 'res' / 'values' / 'strings.xml'
        if strings_path.exists():
            log(f"Updating {strings_path}...")
            content = strings_path.read_text()
            content = replace_xml_tag(content, 'app_name', app_name)
            content = replace_xml_tag(content, 'launcher_name', launcher_name, insert_if_missing=True)
            content = replace_xml_tag(content, 'hostName', host_name, insert_if_missing=True)
            content = replace_xml_tag(content, 'launchUrl', launch_url, insert_if_missing=True)
            strings_path.write_text(content)
            log("strings.xml updated successfully")
        else:
            log(f"No strings.xml found at {strings_path}, skipping")

        # Update colors.xml
        colors_path = app_dir / 'src' / 'main' / 'res' / 'values' / 'colors.xml'
        if colors_path.exists():
            log(f"Updating {colors_path}...")
            content = colors_path.read_text()
            content = re.sub(r'<color name="colorPrimary">.*?</color>', f'<color name="colorPrimary">{theme_color}</color>', content)
            content = re.sub(r'<color name="colorPrimaryDark">.*?</color>', f'<color name="colorPrimaryDark">{theme_color_dark}</color>', content)
            content = re.sub(r'<color name="backgroundColor">.*?</color>', f'<color name="backgroundColor">{background_color}</color>', content)
            colors_path.write_text(content)
            log("colors.xml updated successfully")
        else:
            log(f"No colors.xml found at {colors_path}, skipping")

        log("Android project customization completed successfully!")
    except Exception as e:
        log(f"ERROR: {e}")
        traceback.print_exc()
        raise

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        traceback.print_exc()
        exit(1)


