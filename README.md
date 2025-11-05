# [![APK Builder](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml/badge.svg)](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml)<br>

### Basic apk published to repo

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
      "repoName": "ai-apk", 
      "createRelease": "true"
    }
  }'


```

### custom icon

```
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sudo-self/apk-builder-actions/dispatches \
  -d '{
    "event_type": "apk_build",
    "client_payload": {
      "hostName": "jessejesse.com",
      "name": "CastleApp",
      "launchUrl": "https://jessejesse.com",
      "launcherName": "Castle",
      "themeColor": "#8B4513",
      "themeColorDark": "#654321",
      "backgroundColor": "#F5F5DC",
      "iconChoice": "castle",
      "repoName": "castle-app",
      "createRelease": "true"
    }
  }'

```
