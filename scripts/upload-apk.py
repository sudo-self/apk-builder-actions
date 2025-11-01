#!/usr/bin/env python3
import boto3
import os
import glob
import json

def find_apk_file():
    """Find the built APK file"""
    search_paths = [
        'android-project/app/build/outputs/apk/release/*.apk',
        'android-project/app/build/outputs/apk/*.apk',
        'android-project/build/outputs/apk/release/*.apk'
    ]
    
    for path in search_paths:
        files = glob.glob(path)
        if files:
            return files[0]
    return None

def upload_to_s3(apk_path, build_id):
    """Upload APK to S3 bucket"""
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        region_name=os.environ.get('AWS_REGION', 'us-east-1')
    )
    
    bucket_name = os.environ['S3_BUCKET']
    s3_key = f"apks/{build_id}.apk"
    
    with open(apk_path, 'rb') as file:
        s3.upload_fileobj(
            file,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': 'application/vnd.android.package-archive',
                'ACL': 'public-read'
            }
        )
    
    # Generate public URL
    if os.environ.get('AWS_REGION') == 'us-east-1':
        url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    else:
        url = f"https://{bucket_name}.s3.{os.environ['AWS_REGION']}.amazonaws.com/{s3_key}"
    
    return url

def main():
    build_id = os.sys.argv[1]
    
    apk_path = find_apk_file()
    if not apk_path:
        print("❌ No APK file found")
        return 1
    
    print(f"📦 Found APK: {apk_path}")
    
    try:
        download_url = upload_to_s3(apk_path, build_id)
        print(f"✅ APK uploaded: {download_url}")
        
        # Output URL for next steps
        with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
            print(f"apk_url={download_url}", file=fh)
            
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return 1

if __name__ == "__main__":
    main()
