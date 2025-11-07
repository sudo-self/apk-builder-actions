# <a href="https://apk.jessejesse.com">APP BUILDER</a>
## [![APK Builder](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml/badge.svg)](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml)<br>

<img width="1147" height="652" alt="Screenshot 2025-11-07 at 11 39 06" src="https://github.com/user-attachments/assets/bba4501d-e449-4867-836e-42a180629c9c" />

## command line npx

`npx apk-builder-cli`

## Required

Github `token` needs `repo` scope permissions

## Optional

- `launcherName`: Short name for app launcher (defaults to `name`)
- `themeColor`: Primary color (default: #2196F3)
- `themeColorDark`: Dark mode color (default: #1976D2)
- `backgroundColor`: Background color (default: #FFFFFF)
- `iconChoice`: App icon (default: phone)

## Available Icons

`phone`, `smile`, `castle`

## Builds

### Basic APK

```
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sudo-self/apk-builder-actions/dispatches \
  -d '{
    "event_type": "apk_build",
    "client_payload": {
      "buildConfig": {
        "hostName": "ai.jessejesse.com",
        "name": "AI",
        "launchUrl": "https://ai.jessejesse.com",
        "launcherName": "AI",
        "themeColor": "#2196F3",
        "themeColorDark": "#1976D2",
        "backgroundColor": "#FFFFFF",
        "iconChoice": "phone"
      }
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
      "buildConfig": {
        "hostName": "jessejesse.com",
        "name": "CastleApp",
        "launchUrl": "https://jessejesse.com",
        "launcherName": "Castle",
        "themeColor": "#8B4513",
        "themeColorDark": "#654321",
        "backgroundColor": "#F5F5DC",
        "iconChoice": "castle"
      }
    }
  }'

```
### minimal build

```
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sudo-self/apk-builder-actions/dispatches \
  -d '{
    "event_type": "apk_build",
    "client_payload": {
      "buildConfig": {
        "hostName": "com.example.myapp",
        "name": "My App",
        "launchUrl": "https://example.com"
      }
    }
  }'

```

### dark theme

```
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sudo-self/apk-builder-actions/dispatches \
  -d '{
    "event_type": "apk_build",
    "client_payload": {
      "buildConfig": {
        "hostName": "com.darkapp.news",
        "name": "Dark Reader",
        "launchUrl": "https://news.example.com",
        "launcherName": "News",
        "themeColor": "#1a1a1a",
        "themeColorDark": "#000000",
        "backgroundColor": "#0a0a0a",
        "iconChoice": "smile"
      }
    }
  }'

```

### blog

```
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/sudo-self/apk-builder-actions/dispatches \
  -d '{
    "event_type": "apk_build",
    "client_payload": {
      "buildConfig": {
        "hostName": "com.blog.reader",
        "name": "Blog Reader Pro",
        "launchUrl": "https://blog.example.com",
        "launcherName": "Blogs",
        "themeColor": "#4A90E2",
        "themeColorDark": "#357ABD",
        "backgroundColor": "#F8F9FA",
        "iconChoice": "phone"
      }
    }
  }'

```








