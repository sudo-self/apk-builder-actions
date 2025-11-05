# [![APK Builder](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml/badge.svg)](https://github.com/sudo-self/apk-builder-actions/actions/workflows/apk-builder.yml)<br>

## Required Fields

-   `hostName`: Android package name (e.g., com.example.app)
    
-   `name`: App display name
    
-   `launchUrl`: Website URL to load in the app
    

## Optional Fields

-   `launcherName`: Short name for app launcher (defaults to `name`)
    
-   `themeColor`: Primary color (default: #2196F3)
    
-   `themeColorDark`: Dark mode color (default: #1976D2)
    
-   `backgroundColor`: Background color (default: #FFFFFF)
    
-   `iconChoice`: App icon (default: phone)
    

## Available Icons

`phone`, `rocket`, `star`, `fire`, `lightning`, `globe`, `laptop`, `heart`, `castle`

The built APK will be available as a downloadable artifact in the GitHub Actions run.<hr>

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
