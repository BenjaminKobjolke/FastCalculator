$versionFile = "$PSScriptRoot\..\version.txt"
if (Test-Path $versionFile) {
    $version = (Get-Content $versionFile -Raw).Trim()
    Write-Output $version
} else {
    Write-Host "Could not find version.txt"
    exit 1
}
