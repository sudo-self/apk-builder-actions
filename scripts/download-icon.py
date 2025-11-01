#!/usr/bin/env python3
import requests
import os
import sys

def download_icon(icon_url, build_id):
    """Download custom icon from URL"""
    temp_dir = f"/tmp/{build_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    icon_path = os.path.join(temp_dir, "icon.png")
    
    response = requests.get(icon_url, timeout=30)
    response.raise_for_status()
    
    with open(icon_path, 'wb') as f:
        f.write(response.content)
    
    print(f"✅ Icon downloaded: {icon_path}")
    return icon_path

if __name__ == "__main__":
    icon_url = sys.argv[1]
    build_id = sys.argv[2]
    download_icon(icon_url, build_id)
