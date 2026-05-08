$src = "$env:USERPROFILE\Documents\lifeplanner_data.json"
$onedrive = $env:OneDriveConsumer
if (-not $onedrive) { $onedrive = $env:OneDrive }
$dst = "$onedrive\lifeplanner_data.json"

if (-not (Test-Path $src)) {
    Write-Host "Source file not found: $src"
    Read-Host "Press Enter to exit"
    exit
}

if (Test-Path $dst) {
    Copy-Item $dst "$onedrive\lifeplanner_data_backup.json" -Force
    Write-Host "Backup saved: lifeplanner_data_backup.json"
}

Copy-Item $src $dst -Force
Write-Host "Done! Data copied to: $dst"
Read-Host "Press Enter to exit"
