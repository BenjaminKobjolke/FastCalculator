$versionFile = "$PSScriptRoot\..\version.txt"
$pyproject = "$PSScriptRoot\..\pyproject.toml"
$content = (Get-Content $versionFile -Raw).Trim()

if ($content -match '^(\d+)\.(\d+)\.(\d+)$') {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]

    Write-Host "Current version: $major.$minor.$patch"

    if ($patch -le 0) {
        Write-Host "Cannot decrement: patch number is already 0"
        exit 1
    }

    $newVersion = "$major.$minor.$($patch - 1)"

    Write-Host "New version: $newVersion"

    Set-Content $versionFile $newVersion -NoNewline
    (Get-Content $pyproject -Raw) -replace '(?m)^version = "\d+\.\d+\.\d+"', "version = `"$newVersion`"" |
        Set-Content $pyproject -NoNewline

    Write-Host "Version decremented to $newVersion (version.txt + pyproject.toml)"
} else {
    Write-Host "Could not parse version from version.txt (expected format: X.Y.Z)"
    exit 1
}
