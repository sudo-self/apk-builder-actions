#!/usr/bin/env python3
import os
import subprocess
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

def sign_and_align_apk():
    """Sign the APK with existing android.keystore and zipalign"""
    try:
        # Verify keystore exists
        if not os.path.exists("android.keystore"):
            raise FileNotFoundError("android.keystore not found in template")
        
        # Find the APK file
        apk_search_paths = [
            "app/build/outputs/apk/debug/*.apk",
            "app/build/outputs/apk/*.apk"
        ]
        
        apk_path = None
        for search_path in apk_search_paths:
            import glob
            files = glob.glob(search_path)
            if files and not any('unaligned' in f for f in files):
                apk_path = files[0]
                break
        
        if not apk_path:
            raise FileNotFoundError("No APK file found to sign")
        
        print(f"Found APK to sign: {apk_path}")
        
        # First zipalign the APK
        print("Running zipalign...")
        aligned_apk = apk_path.replace('.apk', '-aligned.apk')
        zipalign_cmd = [
            "zipalign", "-v", "-p", "4",
            apk_path,
            aligned_apk
        ]
        run_command(" ".join(zipalign_cmd))
        
        # Sign the aligned APK with apksigner
        print("Signing APK with apksigner...")
        signed_apk = apk_path.replace('.apk', '-signed.apk')
        sign_cmd = [
            "apksigner", "sign",
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
            "apksigner", "verify",
            "--verbose",
            signed_apk
        ]
        run_command(" ".join(verify_cmd))
        
        # Clean up intermediate files
        if os.path.exists(aligned_apk):
            os.remove(aligned_apk)
        
        print("APK signed and aligned successfully")
        print(f"Signed APK: {signed_apk}")
        
    except Exception as e:
        print(f"Error signing APK: {e}")
        raise

def main():
    print("Starting APK signing process...")
    
    try:
        sign_and_align_apk()
        print("APK signing completed successfully")
        return 0
    except Exception as e:
        print(f"APK signing failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
