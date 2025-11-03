# [![APK Builder](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml/badge.svg)](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml)<br>

### website to apk

```
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sudo-self/apk-builder-actions/dispatches \
  -d '{
    "event_type": "apk_build",
    "client_payload": {
      "hostName": "ai.jessejesse.com",
      "name": "AI",
      "launchUrl": "https://ai.jessejesse.com",
      "launcherName": "AI",
      "themeColor": "#2196F3",
      "themeColorDark": "#1976D2",
      "backgroundColor": "#FFFFFF",
      "iconChoice": "phone",
      "createRelease": "true"
    }
  }'

```
