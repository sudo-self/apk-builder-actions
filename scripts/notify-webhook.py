#!/usr/bin/env python3
import os
import requests
import sys

def notify_webhook(status):
    webhook_url = os.environ.get('WEBHOOK_URL')
    build_id = os.environ.get('BUILD_ID')
    artifact_name = os.environ.get('ARTIFACT_NAME')
    
    if not webhook_url:
        print("⚠️ No webhook URL set")
        return
    
    payload = {
        'buildId': build_id,
        'status': status,
        'artifactId': artifact_name if status == 'success' else None
    }
    
    if status == 'failure':
        payload['error'] = 'Build failed in GitHub Actions'
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Webhook notified: {status}")
        else:
            print(f"❌ Webhook failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python notify-webhook.py <success|failure>")
        sys.exit(1)
    
    notify_webhook(sys.argv[1])
