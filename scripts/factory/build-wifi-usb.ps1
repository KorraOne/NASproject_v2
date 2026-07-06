param(
    [Parameter(Mandatory = $true)]
    [string]$DriveLetter
)

$ErrorActionPreference = "Stop"
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$src = Join-Path $root "tools\wifi-setup"
$dest = "{0}:\" -f $DriveLetter.TrimEnd(':')

if (-not (Test-Path $src)) {
    throw "WiFi setup source not found: $src"
}

if (-not (Test-Path $dest)) {
    throw "Drive not found: $dest"
}

Copy-Item -Path (Join-Path $src "*") -Destination $dest -Force

$labelFile = Join-Path $dest "FROGSWORK_WIFI_USB.txt"
@"
FrogsWork WiFi Setup USB
========================

On your Windows or Mac computer:
  1. Open "WiFi Setup.html" on this USB
  2. Enter your Wi-Fi name and password, then save frogswork-setup.json to this USB
  3. Safely eject the USB

On the FrogsWork box (power on, no ethernet required):
  4. Plug in this USB and wait about 2 minutes
  5. Unplug the USB and plug it back into your computer
  6. Open frogswork-setup.log — look for "Finished: SUCCESS"
  7. Join the same Wi-Fi on your computer, open http://frogswork.local

Ethernet is still the easiest option if you can run a cable to your router.
"@ | Set-Content -Path $labelFile -Encoding UTF8

Write-Host "WiFi setup USB ready on $dest"
Write-Host "Files: WiFi Setup.html, README.txt"
