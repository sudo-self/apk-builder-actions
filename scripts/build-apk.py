#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def run_command(cmd, cwd=None):
    """Execute a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=True)
        print(f"Command successful: {cmd}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e.stderr}")
        raise

def update_strings_xml(app_name, launcher_name):
    """Update strings.xml with app name and launcher name"""
    strings_path = "app/src/main/res/values/strings.xml"
    
    try:
        tree = ET.parse(strings_path)
        root = tree.getroot()
        
        for string_elem in root.findall("string"):
            if string_elem.get("name") == "app_name":
                string_elem.text = app_name
            elif string_elem.get("name") == "launcher_name":
                string_elem.text = launcher_name
        
        tree.write(strings_path, encoding="utf-8", xml_declaration=True)
        print(f"Updated strings.xml with app_name: {app_name}, launcher_name: {launcher_name}")
        
    except Exception as e:
        print(f"Error updating strings.xml: {e}")
        raise

def update_colors_xml(theme_color, theme_color_dark, background_color):
    """Update colors.xml with theme colors"""
    colors_path = "app/src/main/res/values/colors.xml"
    
    try:
        tree = ET.parse(colors_path)
        root = tree.getroot()
        
        for color_elem in root.findall("color"):
            name = color_elem.get("name")
            if name == "colorPrimary":
                color_elem.text = theme_color
            elif name == "colorPrimaryDark":
                color_elem.text = theme_color_dark
            elif name == "backgroundColor":
                color_elem.text = background_color
        
        tree.write(colors_path, encoding="utf-8", xml_declaration=True)
        print("Updated colors.xml with theme colors")
        
    except Exception as e:
        print(f"Error updating colors.xml: {e}")
        raise

def update_webview_activity(host_name, launch_url):
    """Update MainActivity.java with the target URL"""
    activity_path = "app/src/main/java/com/example/webviewapp/MainActivity.java"
    
    try:
        with open(activity_path, 'r') as file:
            content = file.read()
        
        content = content.replace('"https://example.com"', f'"{host_name}"')
        content = content.replace('"example.com"', f'"{host_name}"')
        
        with open(activity_path, 'w') as file:
            file.write(content)
        
        print(f"Updated MainActivity.java with host: {host_name}")
        
    except Exception as e:
        print(f"Error updating MainActivity.java: {e}")
        raise

def update_build_gradle(app_name):
    """Update build.gradle with app name and configuration"""
    gradle_path = "app/build.gradle"
    
    try:
        with open(gradle_path, 'r') as file:
            content = file.read()
        
        sanitized_name = app_name.lower().replace(' ', '').replace('-', '')
        content = content.replace('applicationId "com.example.webviewapp"', 
                                f'applicationId "com.{sanitized_name}.app"')
        
        with open(gradle_path, 'w') as file:
            file.write(content)
        
        print("Updated build.gradle with application ID")
        
    except Exception as e:
        print(f"Error updating build.gradle: {e}")
        raise

def sign_and_align_apk():
    """Sign the APK with existing android.keystore and zipalign"""
    try:
        # Verify keystore exists
        if not os.path.exists("android.keystore"):
            raise FileNotFoundError("android.keystore not found in template")
        
        # First zipalign the APK
        print("Running zipalign...")
        zipalign_cmd = [
            "zipalign", "-v", "-p", "4",
            "app/build/outputs/apk/debug/app-debug.apk",
            "app/build/outputs/apk/debug/app-debug-aligned.apk"
        ]
        run_command(" ".join(zipalign_cmd))
        
        # Sign the aligned APK with apksigner (recommended for v2 signing)
        print("Signing APK with apksigner...")
        sign_cmd = [
            "apksigner", "sign",
            "--ks", "android.keystore",
            "--ks-pass", "pass:123321",
            "--key-pass", "pass:123321",
            "--ks-key-alias", "android",
            "--v2-signing-enabled", "true",
            "app/build/outputs/apk/debug/app-debug-aligned.apk"
        ]
        run_command(" ".join(sign_cmd))
        
        # Verify the signature
        print("Verifying APK signature...")
        verify_cmd = [
            "apksigner", "verify",
            "--verbose",
            "app/build/outputs/apk/debug/app-debug-aligned.apk"
        ]
        run_command(" ".join(verify_cmd))
        
        # Rename to final signed APK
        run_command("mv app/build/outputs/apk/debug/app-debug-aligned.apk app/build/outputs/apk/debug/app-debug-signed.apk")
        
        print("APK signed and aligned successfully")
        
    except Exception as e:
        print(f"Error signing APK: {e}")
        raise

def verify_apk_installable():
    """Verify the APK is properly signed and aligned"""
    try:
        # Check if APK exists
        apk_path = "app/build/outputs/apk/debug/app-debug-signed.apk"
        if not os.path.exists(apk_path):
            raise FileNotFoundError("Signed APK not found")
        
        # Verify with apksigner
        verify_cmd = [
            "apksigner", "verify",
            "--print-certs",
            apk_path
        ]
        result = run_command(" ".join(verify_cmd))
        
        print("APK verification successful")
        print("APK is ready for installation")
        
    except Exception as e:
        print(f"APK verification failed: {e}")
        raise

def main():
    print("Starting APK build process...")
    
    # Get build data from environment or command line
    if len(sys.argv) > 1:
        build_data = json.loads(sys.argv[1])
    else:
        build_data = json.loads(os.environ.get('BUILD_DATA', '{}'))
    
    if not build_data:
        print("No build data provided")
        sys.exit(1)
    
    # Extract build parameters
    build_id = build_data.get('buildId', 'unknown')
    host_name = build_data.get('hostName', '')
    launch_url = build_data.get('launchUrl', '/')
    app_name = build_data.get('name', 'WebView App')
    launcher_name = build_data.get('launcherName', app_name)
    theme_color = build_data.get('themeColor', '#171717')
    theme_color_dark = build_data.get('themeColorDark', '#000000')
    background_color = build_data.get('backgroundColor', '#FFFFFF')
    
    print(f"Build ID: {build_id}")
    print(f"Host: {host_name}")
    print(f"App Name: {app_name}")
    
    try:
        # Ensure we're in the template_apk directory
        if not os.path.exists('app'):
            print("Not in template_apk directory")
            sys.exit(1)
        
        # Update app configuration
        print("Updating app configuration...")
        update_strings_xml(app_name, launcher_name)
        update_colors_xml(theme_color, theme_color_dark, background_color)
        update_webview_activity(host_name, launch_url)
        update_build_gradle(app_name)
        
        # Build the APK
        print("Building APK...")
        run_command("./gradlew assembleDebug")
        
        # Sign and align the APK
        print("Signing and aligning APK...")
        sign_and_align_apk()
        
        # Verify APK is installable
        print("Verifying APK...")
        verify_apk_installable()
        
        print("Build completed successfully")
        print(f"APK location: app/build/outputs/apk/debug/app-debug-signed.apk")
        
    except Exception as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
