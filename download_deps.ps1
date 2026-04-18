param([switch]$Update = $false)

$ErrorActionPreference = "Stop"

$depsDir = ".\external"
$glmVersion = "0.9.9.8"
$glmDir = "$depsDir\glm"

Write-Host "Downloading ASCII RTX dependencies..." -ForegroundColor Green

if (-not (Test-Path $depsDir)) {
	New-Item -ItemType Directory -Path $depsDir | Out-Null
	Write-Host "Created $depsDir directory" -ForegroundColor Green
}

# Check if GLM already exists
if ((Test-Path $glmDir) -and -not $Update) {
	Write-Host "GLM already installed" -ForegroundColor Green
} else {
	Write-Host "Downloading GLM..." -ForegroundColor Yellow
	$glmUrl = "https://github.com/g-truc/glm/releases/download/$glmVersion/glm-$glmVersion.zip"
	$glmZip = "$depsDir\glm.zip"

	$ProgressPreference = 'SilentlyContinue'
	Invoke-WebRequest -Uri $glmUrl -OutFile $glmZip

	Write-Host "Extracting GLM..." -ForegroundColor Yellow
	Expand-Archive -Path $glmZip -DestinationPath $depsDir -Force
	Remove-Item $glmZip

	$extracted = Get-ChildItem -Path $depsDir -Filter "glm-*" -Directory
	if ($extracted) {
		Rename-Item -Path $extracted.FullName -NewName "glm" -Force
	}

	Write-Host "GLM ready" -ForegroundColor Green
}

# Verify GLM
if (Test-Path "$glmDir\glm\glm.hpp") {
	Write-Host "Dependencies verified!" -ForegroundColor Green
} else {
	Write-Host "Warning: GLM headers may not be found" -ForegroundColor Red
}
