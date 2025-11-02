#!/usr/bin/env sign-apk.py

import os
import subprocess
import glob
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

def find_android_tools():
    """Find Android SDK tools"""
    sdk_path = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if not sdk_path:
        # Try to find SDK in common locations
        possible_paths = [
            '/usr/local/lib/android/sdk',
            '/opt/android/sdk',
            '/home/runner/android-sdk'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                sdk_path = path
                break
    
    if not sdk_path:
        raise FileNotFoundError("Android SDK not found")
    
    print(f"Found Android SDK at: {sdk_path}")
    
    # Find build-tools directory
    build_tools_dir = None
    build_tools_path = Path(sdk_path) / 'build-tools'
    if build_tools_path.exists():
        # Get the highest version
        versions = [d for d in build_tools_path.iterdir() if d.is_dir()]
        if versions:
            versions.sort()
            build_tools_dir = versions[-1]
            print(f"Found build-tools: {build_tools_dir.name}")
    
    if not build_tools_dir:
        raise FileNotFoundError("Android build-tools not found")
    
    zipalign = build_tools_dir / 'zipalign'
    apksigner = build_tools_dir / 'apksigner'
    
    return str(zipalign), str(apksigner)

def sign_and_align_apk():
    """Sign the APK with existing android.keystore and zipalign"""
    try:
        # Verify keystore exists
        if not os.path.exists("android.keystore"):
            raise FileNotFoundError("android.keystore not found in template")
        
        # Find Android tools
        zipalign_path, apksigner_path = find_android_tools()
        
        # Find the APK file
        apk_search_paths = [
            "app/build/outputs/apk/debug/*.apk",
            "app/build/outputs/apk/*.apk"
        ]
        
        apk_path = None
        for search_path in apk_search_paths:
            files = glob.glob(search_path)
            if files and not any('unaligned' in f.lower() for f in files):
                apk_path = files[0]
                break
        
        if not apk_path:
            raise FileNotFoundError("No APK file found to sign")
        
        print(f"Found APK to sign: {apk_path}")
        
        # First zipalign the APK
        print("Running zipalign...")
        aligned_apk = apk_path.replace('.apk', '-aligned.apk')
        zipalign_cmd = [
            zipalign_path, "-v", "-p", "4",
            apk_path,
            aligned_apk
        ]
        run_command(" ".join(zipalign_cmd))
        
        # Sign the aligned APK with apksigner
        print("Signing APK with apksigner...")
        signed_apk = apk_path.replace('.apk', '-signed.apk')
        sign_cmd = [
            apksigner_path, "sign",
            "--ks", "android.keystore",
            "--ks-pass", "pass:123321",
            "--key-pass", "pass:123321",
            "--ks-key-alias", "android",
            "--v2-signing-enabled", "true",
            "--out", signed_apk,
            aligned_apk
        ]
        run_command(" ".join(sign_cmd))
        
        # Verify the signature
        print("Verifying APK signature...")
        verify_cmd = [
            apksigner_path, "verify",
            "--verbose",
            signed_apk
        ]
        run_command(" ".join(verify_cmd))
        
        # Clean up intermediate files
        if os.path.exists(aligned_apk):
            os.remove(aligned_apk)
        
        print("APK signed and aligned successfully")
        print(f"Signed APK: {signed_apk}")
        
        return signed_apk
        
    except Exception as e:
        print(f"Error signing APK: {e}")
        raise

def main():
    print("Starting APK signing process...")
    
    try:
        signed_apk_path = sign_and_align_apk()
        print(f"APK signing completed successfully: {signed_apk_path}")
        return 0
    except Exception as e:
        print(f"APK signing failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
