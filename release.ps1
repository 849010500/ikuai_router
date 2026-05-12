<# 
    Release Script for ikuai_router HACS Integration
    Usage: .\release.ps1
#>

# Stop on errors
$ErrorActionPreference = "Stop"

Write-Host "=== ikuai_router Release Script ===" -ForegroundColor Cyan

# Step 1: Read current version from manifest.json
$manifestPath = "custom_components/ikuai_router/manifest.json"
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
$currentVersion = $manifest.version
Write-Host "Current version: $currentVersion" -ForegroundColor Yellow

# Step 2: Bump version (patch)
$versionParts = $currentVersion.Split('.')
$major = [int]$versionParts[0]
$minor = [int]$versionParts[1]
$patch = [int]$versionParts[2] + 1
$newVersion = "$major.$minor.$patch"
Write-Host "New version:     $newVersion" -ForegroundColor Green

# Step 3: Update manifest.json
$manifest.version = $newVersion
$manifest | ConvertTo-Json -Depth 10 | Set-Content $manifestPath -Encoding UTF8
Write-Host "[OK] Updated manifest.json" -ForegroundColor Green

# Step 4: Git commit and tag
git add -A
git commit -m "Release v$newVersion"
git tag "v$newVersion"
git push origin main
git push origin "v$newVersion"
Write-Host "[OK] Pushed commit and tag v$newVersion" -ForegroundColor Green

# Step 5: Build release zip (only the files needed for HACS)
$zipName = "ikuai_router_v$newVersion.zip"
if (Test-Path $zipName) { Remove-Item $zipName }

Compress-Archive -Path "custom_components/", "hacs.json" -DestinationPath $zipName
Write-Host "[OK] Created release zip: $zipName" -ForegroundColor Green

# Step 6: Create GitHub release with the zip as asset
gh release create "v$newVersion" $zipName --title "v$newVersion" --notes "Release v$newVersion"
Write-Host "[OK] Created GitHub release v$newVersion" -ForegroundColor Green

