#!/usr/bin/env python3

import os
import glob
import json
from pathlib import Path

def find_apk_files():
    """Find all APK files with better search patterns"""
    apk_files = []
    
    # More comprehensive search patterns
    search_patterns = [
        "**/build/outputs/apk/**/*.apk",
        "**/build/outputs/bundle/**/*.apk",
        "**/build/**/*.apk",
        "**/*.apk"
    ]
    
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        # Filter out test APKs and unaligned APKs
        filtered_files = [
            f for f in files 
            if not any(exclude in f.lower() for exclude in ['test', 'unaligned'])
        ]
        apk_files.extend(filtered_files)
    
    # Remove duplicates and sort by modification time (newest first)
    apk_files = list(set(apk_files))
    apk_files.sort(key=os.path.getmtime, reverse=True)
    
    return apk_files

def analyze_apk(apk_path):
    """Basic APK analysis"""
    try:
        size = os.path.getsize(apk_path) / (1024 * 1024)  # MB
        return {
            'path': apk_path,
            'size_mb': round(size, 2),
            'file_name': os.path.basename(apk_path),
            'is_signed': check_apk_signed(apk_path)
        }
    except:
        return {'path': apk_path, 'error': 'Could not analyze'}

def check_apk_signed(apk_path):
    """Check if APK is signed using apksigner"""
    try:
        import subprocess
        result = subprocess.run(
            ['apksigner', 'verify', '--print-certs', apk_path],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except:
        # Fallback: check if file contains META-INF (basic check)
        try:
            import zipfile
            with zipfile.ZipFile(apk_path, 'r') as z:
                return any('META-INF/' in name for name in z.namelist())
        except:
            return False

def print_directory_structure():
    """Print relevant build directory structure"""
    print("\n📁 Build directory structure:")
    
    build_dirs = [
        "android-project/app/build/outputs",
        "app/build/outputs", 
        "build/outputs",
        "android-project/build"
    ]
    
    for build_dir in build_dirs:
        if os.path.exists(build_dir):
            print(f"\n📍 {build_dir}:")
            for root, dirs, files in os.walk(build_dir):
                level = root.replace(build_dir, "").count(os.sep)
                if level > 2:  # Limit depth
                    continue
                    
                indent = "  " * level
                print(f"{indent}{os.path.basename(root)}/")
                
                # Show APK files immediately
                apk_files = [f for f in files if f.endswith('.apk')]
                for apk_file in apk_files[:5]:
                    print(f"{indent}  📦 {apk_file}")

def main():
    print("🔍 Searching for APK files...")
    
    apk_files = find_apk_files()
    
    if not apk_files:
        print("❌ No APK files found")
        print_directory_structure()
        
        # Check if build was successful
        build_dirs = [
            "android-project/app/build",
            "app/build", 
            "build"
        ]
        
        for build_dir in build_dirs:
            if os.path.exists(build_dir):
                print(f"\n✅ Build directory exists: {build_dir}")
            else:
                print(f"\n❌ Build directory missing: {build_dir}")
                
        return 1
    
    print(f"✅ Found {len(apk_files)} APK file(s):")
    
    apk_info = []
    for apk_file in apk_files:
        info = analyze_apk(apk_file)
        apk_info.append(info)
        
        status = "✅" if info.get('is_signed', False) else "⚠️"
        print(f"  {status} {apk_file} ({info['size_mb']} MB)")
        if not info.get('is_signed', False):
            print("     ⚠️  APK may not be signed (will not install)")
    
    # Prefer signed release APKs
    signed_apks = [info for info in apk_info if info.get('is_signed', False)]
    release_apks = [info for info in apk_info if 'release' in info['path'].lower()]
    
    if signed_apks:
        main_apk = signed_apks[0]['path']
        print(f"🎯 Using signed APK: {main_apk}")
    elif release_apks:
        main_apk = release_apks[0]['path']
        print(f"🎯 Using release APK: {main_apk}")
    else:
        main_apk = apk_files[0]
        print(f"🎯 Using first found APK: {main_apk}")
        print("⚠️  Warning: This APK may not be signed and might not install")

    # Write to GitHub outputs
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"apk_path={main_apk}", file=fh)
        print(f"apk_filename={os.path.basename(main_apk)}", file=fh)
    
    return 0

if __name__ == "__main__":
    exit(main())
