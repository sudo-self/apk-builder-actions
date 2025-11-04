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
    """Generate a valid Android package name from host name."""
    # Clean the host name more thoroughly
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
        # Only allow valid package name characters
        segment = re.sub(r'[^a-zA-Z0-9_]', '', segment)
        if segment:
            segments.append(segment)
    
    # Ensure we have at least 2 segments
    if len(segments) < 2:
        segments = ['com', 'webapp'] + segments
    
    final_package = '.'.join(segments).lower()
    log(f"Generated package name: {final_package}")
    return final_package

def update_twa_manifest_in_gradle(build_gradle_path: Path, package_name: str, host_name: str, 
                                   launch_url: str, app_name: str, launcher_name: str,
                                   theme_color: str, theme_color_dark: str, background_color: str):
    """Update the build.gradle with app configuration."""
    if not build_gradle_path.exists():
        log(f"ERROR: {build_gradle_path} not found")
        return False
    
    try:
        content = build_gradle_path.read_text()
        
        # Update namespace and applicationId in android block
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
    """Remove deprecated package attribute from AndroidManifest.xml."""
    if not manifest_path.exists():
        log(f"WARNING: Manifest not found at {manifest_path}")
        return False
    
    try:
        content = manifest_path.read_text()
        
        # Remove package attribute (deprecated in AGP 7.0+)
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

def update_strings_xml(app_dir: Path, app_name: str, host_name: str, launch_url: str):
    """Update the strings.xml file with custom app name and URL."""
    res_dir = app_dir / 'src/main/res'
    strings_path = res_dir / 'values/strings.xml'
    
    if not strings_path.exists():
        log(f"ERROR: strings.xml not found at {strings_path}")
        return False
    
    try:
        content = strings_path.read_text()
        
        # Build the full URL
        full_url = f"https://{host_name}{launch_url}"
        
        # Update app_name
        old_app_name_match = re.search(r'<string name="app_name">([^<]*)</string>', content)
        if old_app_name_match:
            old_app_name = old_app_name_match.group(1)
            content = content.replace(f'<string name="app_name">{old_app_name}</string>', f'<string name="app_name">{app_name}</string>')
            log(f"Updated app_name from '{old_app_name}' to '{app_name}'")
        
        # Update launch_url
        old_url_match = re.search(r'<string name="launch_url">([^<]*)</string>', content)
        if old_url_match:
            old_url = old_url_match.group(1)
            content = content.replace(f'<string name="launch_url">{old_url}</string>', f'<string name="launch_url">{full_url}</string>')
            log(f"Updated launch_url from '{old_url}' to '{full_url}'")
        
        strings_path.write_text(content)
        log("Successfully updated strings.xml")
        return True
        
    except Exception as e:
        log(f"ERROR updating strings.xml: {e}")
        return False

def update_java_kotlin_package(app_dir: Path, old_package: str, new_package: str):
    """Update package references in Java/Kotlin source files."""
    java_dir = app_dir / 'src/main/java'
    
    if not java_dir.exists():
        log(f"WARNING: Java source directory not found at {java_dir}")
        return False
    
    # Find all Java and Kotlin files
    source_files = list(java_dir.rglob('*.java')) + list(java_dir.rglob('*.kt'))
    
    updated_count = 0
    for source_file in source_files:
        try:
            content = source_file.read_text()
            
            # Update package declaration
            if f"package {old_package}" in content:
                content = content.replace(f"package {old_package}", f"package {new_package}")
                updated_count += 1
                log(f"Updated package in: {source_file}")
            
            # Update import statements
            content = re.sub(
                fr'import {re.escape(old_package)}',
                f'import {new_package}',
                content
            )
            
            source_file.write_text(content)
            
        except Exception as e:
            log(f"ERROR updating {source_file}: {e}")
    
    log(f"Updated package references in {updated_count} source files")
    return updated_count > 0

def download_icon_from_url(icon_url: str):
    """Download icon from URL using urllib (no external dependencies)."""
    try:
        log(f"Downloading icon from: {icon_url}")
        
        # Set up a request with headers to avoid blocking
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
    """Remove all existing launcher icons to avoid duplicates."""
    mipmap_dirs = ['mipmap-mdpi', 'mipmap-hdpi', 'mipmap-xhdpi', 'mipmap-xxhdpi', 'mipmap-xxxhdpi']
    
    cleaned_count = 0
    
    for mipmap_dir in mipmap_dirs:
        dir_path = res_dir / mipmap_dir
        if dir_path.exists():
            # Remove ALL icon files (both WebP and PNG)
            for file_path in dir_path.iterdir():
                if file_path.is_file() and any(name in file_path.name for name in ['ic_launcher', 'ic_foreground']):
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        log(f"Removed existing icon: {file_path}")
                    except Exception as e:
                        log(f"ERROR removing {file_path}: {e}")
    
    log(f"Cleaned {cleaned_count} existing icon files")
    return cleaned_count

def set_launcher_icons(app_dir: Path, icon_choice: str = None, icon_base64: str = None):
    """Replace launcher icons with selected icon - FIXED: ONLY WEBP FORMAT."""
    res_dir = app_dir / 'src/main/res'
    
    if not res_dir.exists():
        log(f"ERROR: Resources directory not found at {res_dir}")
        return
    
    # Clean existing icons first to avoid duplicates
    clean_existing_icons(res_dir)
    
    # Icon URLs based on choice
    icon_urls = {
        "phone": "https://apk.jessejesse.com/phone-512.png",
        "castle": "https://apk.jessejesse.com/castle-512.png", 
        "smile": "https://apk.jessejesse.com/smile-512.png"
    }
    
    # Determine which icon to use
    img = None
    icon_source = "default"
    
    # Try base64 icon first
    if icon_base64:
        log("Attempting to use provided base64 icon")
        try:
            icon_data = base64.b64decode(icon_base64)
            img = Image.open(io.BytesIO(icon_data))
            icon_source = "base64"
            log("Successfully loaded base64 icon")
        except Exception as e:
            log(f"ERROR decoding base64 icon: {e}")
            img = None
    
    # Try downloaded icon if base64 failed
    if img is None and icon_choice and icon_choice in icon_urls:
        icon_url = icon_urls[icon_choice]
        log(f"Downloading icon: {icon_choice} from {icon_url}")
        icon_data = download_icon_from_url(icon_url)
        if icon_data:
            try:
                img = Image.open(io.BytesIO(icon_data))
                icon_source = "downloaded"
                log("Successfully loaded downloaded icon")
            except Exception as e:
                log(f"ERROR processing downloaded icon: {e}")
                img = None
    
    # Fallback to default template behavior
    if img is None:
        log("No custom icon available - icons will use template defaults")
        return
    
    # Create different size icons for Android
    sizes = {
        'mipmap-mdpi': 48,
        'mipmap-hdpi': 72, 
        'mipmap-xhdpi': 96,
        'mipmap-xxhdpi': 144,
        'mipmap-xxxhdpi': 192
    }
    
    created_count = 0
    
    try:
        # Create ONLY WebP versions (like the original template)
        for mipmap, size in sizes.items():
            dir_path = res_dir / mipmap
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Resize the image once for this density
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Create WebP versions only
            # Standard launcher icon - WebP
            target_file = dir_path / 'ic_launcher.webp'
            resized.save(target_file, format='WEBP', quality=95, optimize=True)
            created_count += 1
            log(f"Created WebP icon: {target_file} ({size}x{size})")
            
            # Round launcher icon - WebP  
            round_file = dir_path / 'ic_launcher_round.webp'
            resized.save(round_file, format='WEBP', quality=95, optimize=True)
            created_count += 1
            log(f"Created round WebP icon: {round_file}")
        
        log(f"Successfully created {created_count} WebP icon files from {icon_source} source")
        
        # Verify icons were created
        log("Verifying icon creation...")
        for mipmap in sizes.keys():
            dir_path = res_dir / mipmap
            if dir_path.exists():
                icons = list(dir_path.glob("ic_launcher*"))
                log(f"  {mipmap}: {len(icons)} icons found")
                for icon in icons:
                    log(f"    - {icon.name}")
        
    except Exception as e:
        log(f"ERROR during icon creation: {e}")
        # Don't fail the entire build if icons fail

def main():
    log("=" * 60)
    log("Starting Android project customization...")
    log("=" * 60)
    
    try:
        # Read all environment variables
        build_id = os.getenv('BUILD_ID', 'local')
        host_name = read_env_or_fail('HOST_NAME')
        app_name = read_env_or_fail('APP_NAME')
        launch_url = os.getenv('LAUNCH_URL', '/')
        launcher_name = os.getenv('LAUNCHER_NAME', app_name)
        theme_color = os.getenv('THEME_COLOR', '#171717')
        theme_color_dark = os.getenv('THEME_COLOR_DARK', '#000000')
        background_color = os.getenv('BACKGROUND_COLOR', '#FFFFFF')
        icon_choice = os.getenv('ICON_CHOICE', 'phone')  # Default to phone icon
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

        # Validate app directory
        app_dir = Path('android-project/app')
        if not app_dir.exists():
            # Try alternative paths
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

        # Generate package name
        package_name = generate_package_name(host_name)
        log("=" * 60)

        # Update build.gradle
        build_gradle = app_dir / 'build.gradle'
        log("Updating build.gradle with configuration...")
        if not update_twa_manifest_in_gradle(
            build_gradle, package_name, host_name, launch_url,
            app_name, launcher_name, theme_color, theme_color_dark, background_color
        ):
            log("WARNING: Failed to update build.gradle")
            return 1

        # Manifest cleanup
        manifest_path = main_dir / 'AndroidManifest.xml'
        if not update_manifest_remove_package(manifest_path):
            log("WARNING: Failed to update AndroidManifest.xml")

        # Update strings.xml with custom app name and URL
        log("Updating strings.xml with custom app name and URL...")
        if not update_strings_xml(app_dir, app_name, host_name, launch_url):
            log("WARNING: Failed to update strings.xml")

        # Update Java/Kotlin source files with new package
        log("Updating Java/Kotlin source files with new package...")
        old_package = "com.example.githubactionapks"  # Default package from template
        update_java_kotlin_package(app_dir, old_package, package_name)

        # Handle icons
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















