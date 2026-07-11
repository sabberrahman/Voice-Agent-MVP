$ErrorActionPreference = "Stop"

function Get-PreferredHostIp {
    $configs = Get-NetIPConfiguration |
        Where-Object {
            $_.IPv4DefaultGateway -and
            $_.IPv4Address.IPAddress -and
            $_.IPv4Address.IPAddress -notlike "169.254*" -and
            $_.IPv4Address.IPAddress -ne "127.0.0.1"
        } |
        Sort-Object @{ Expression = { if ($_.InterfaceAlias -match "Wi-?Fi|Wireless|WLAN") { 0 } else { 1 } } }

    $selected = $configs | Select-Object -First 1
    if ($selected) {
        return $selected.IPv4Address.IPAddress
    }

    return (
        Get-NetIPAddress -AddressFamily IPv4 |
            Where-Object {
                $_.IPAddress -notlike "169.254*" -and
                $_.IPAddress -ne "127.0.0.1" -and
                $_.PrefixOrigin -ne "WellKnown"
            } |
            Select-Object -First 1 -ExpandProperty IPAddress
    )
}

function Set-DotEnvValue {
    param(
        [string] $Path,
        [string] $Key,
        [string] $Value
    )

    $line = "$Key=$Value"
    if (-not (Test-Path $Path)) {
        Set-Content -Path $Path -Value $line
        return
    }

    $content = Get-Content -Path $Path
    if ($content -match "^$([regex]::Escape($Key))=") {
        $content = $content | ForEach-Object {
            if ($_ -match "^$([regex]::Escape($Key))=") { $line } else { $_ }
        }
    } else {
        $content += $line
    }
    Set-Content -Path $Path -Value $content
}

$hostIp = Get-PreferredHostIp
if (-not $hostIp) {
    $hostIp = "127.0.0.1"
}

$envPath = Join-Path (Get-Location) ".env"
Set-DotEnvValue -Path $envPath -Key "ZOIPER_HOST_IP" -Value $hostIp
Set-DotEnvValue -Path $envPath -Key "FREESWITCH_DOMAIN" -Value $hostIp

Write-Host ""
Write-Host "============================================================"
Write-Host " ZOIPER COPY-PASTE SETTINGS"
Write-Host "============================================================"
Write-Host " Host / Domain : $hostIp"
Write-Host " SIP Port      : 5060"
Write-Host " Transport     : UDP"
Write-Host ""
Write-Host " Account 1001"
Write-Host "   User        : 1001"
Write-Host "   Password    : 1001pass"
Write-Host "   Call AI     : 7000"
Write-Host ""
Write-Host " Account 1002"
Write-Host "   User        : 1002"
Write-Host "   Password    : 1002pass"
Write-Host ""
Write-Host " Outbound AI endpoint:"
Write-Host "   POST http://localhost:8000/admin/start-outbound-zoiper/1001"
Write-Host "============================================================"
Write-Host ""

docker compose up --build
