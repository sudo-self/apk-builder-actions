#!/usr/bin/env python3

import os
import glob
import json

def find_apk_files():
    """Find all APK files in the android-project directory"""
    apk_files = []
    
    search_patterns = [
        "android-project/app/build/outputs/apk/**/*.apk",
        "android-project/app/build/outputs/**/*.apk", 
        "android-project/build/outputs/apk/**/*.apk",
        "android-project/**/*.apk"
    ]
    
    for pattern in search_patterns:
        files = glob.glob(pattern, recursive=True)
        apk_files.extend(files)
    
    apk_files = list(set(apk_files))
    apk_files.sort(key=os.path.getmtime, reverse=True)
    
    return apk_files

def main():
    print("🔍 Searching for APK files...")
    
    apk_files = find_apk_files()
    
    if not apk_files:
        print("❌ No APK files found")
  
        print("\n📁 Directory structure:")
        for root, dirs, files in os.walk("android-project/app/build"):
            level = root.replace("android-project/app/build", "").count(os.sep)
            indent = " " * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = " " * 2 * (level + 1)
            for file in files[:10]: 
                if file.endswith('.apk'):
                    print(f"{subindent}📦 {file}")
        return 1
    
    print(f"✅ Found {len(apk_files)} APK file(s):")
    for apk_file in apk_files:
        size = os.path.getsize(apk_file) / (1024 * 1024)  # Size in MB
        print(f"  📦 {apk_file} ({size:.2f} MB)")

    main_apk = apk_files[0]
    print(f"🎯 Using APK: {main_apk}")
    

    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f"apk_path={main_apk}", file=fh)
    
    return 0

if __name__ == "__main__":
    exit(main())
