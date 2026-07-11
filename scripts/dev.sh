#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

is_windows_bash() {
  case "$(uname -s 2>/dev/null || true)" in
    MINGW*|MSYS*|CYGWIN*) return 0 ;;
  esac

  if [ -r /proc/version ] && grep -qiE "microsoft|wsl" /proc/version; then
    return 0
  fi

  return 1
}

detect_windows_host_ip() {
  if command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      '$ip = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address.IPAddress -notlike "169.254*" -and $_.IPv4Address.IPAddress -ne "127.0.0.1" } | Sort-Object @{ Expression = { if ($_.InterfaceAlias -match "Wi-?Fi|Wireless|WLAN") { 0 } else { 1 } } } | Select-Object -First 1 -ExpandProperty IPv4Address | Select-Object -ExpandProperty IPAddress; if (-not $ip) { $ip = "127.0.0.1" }; Write-Output $ip' \
      | tr -d '\r'
  fi
}

detect_host_ip() {
  if is_windows_bash; then
    detect_windows_host_ip
    return
  fi

  if command -v ip >/dev/null 2>&1; then
    ip route get 1.1.1.1 2>/dev/null | awk '
      {
        for (i = 1; i <= NF; i++) {
          if ($i == "src") {
            print $(i + 1)
            exit
          }
        }
      }'
    return
  fi

  if command -v route >/dev/null 2>&1; then
    iface="$(route -n get default 2>/dev/null | awk '/interface:/{print $2; exit}')"
    if [ -n "${iface:-}" ] && command -v ipconfig >/dev/null 2>&1; then
      ipconfig getifaddr "$iface" 2>/dev/null || true
      return
    fi
  fi

  if command -v hostname >/dev/null 2>&1; then
    hostname -I 2>/dev/null | awk '{print $1}'
    return
  fi

  detect_windows_host_ip
}

docker_compose_up() {
  if is_windows_bash && command -v docker.exe >/dev/null 2>&1; then
    docker.exe compose up --build
    return
  fi

  if command -v docker >/dev/null 2>&1; then
    docker compose up --build
    return
  fi

  if command -v docker.exe >/dev/null 2>&1; then
    docker.exe compose up --build
    return
  fi

  echo "Docker was not found on PATH." >&2
  echo "Start Docker Desktop, then make sure docker or docker.exe is available in this shell." >&2
  exit 1
}

set_env_value() {
  key="$1"
  value="$2"

  touch "$ENV_FILE"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    tmp_file="$(mktemp)"
    awk -v key="$key" -v value="$value" '
      BEGIN { replacement = key "=" value }
      $0 ~ "^" key "=" { print replacement; next }
      { print }
    ' "$ENV_FILE" > "$tmp_file"
    mv "$tmp_file" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

HOST_IP="$(detect_host_ip | head -n 1 | tr -d '[:space:]')"
if [ -z "${HOST_IP:-}" ]; then
  HOST_IP="127.0.0.1"
fi

set_env_value "ZOIPER_HOST_IP" "$HOST_IP"
set_env_value "FREESWITCH_DOMAIN" "$HOST_IP"

cat <<EOF

============================================================
 ZOIPER COPY-PASTE SETTINGS
============================================================
 Host / Domain : $HOST_IP
 SIP Port      : 5060
 Transport     : UDP

 Account 1001
   User        : 1001
   Password    : 1001pass
   Call AI     : 7000

 Account 1002
   User        : 1002
   Password    : 1002pass

 Outbound AI endpoint:
   POST http://localhost:8000/admin/start-outbound-zoiper/1001
============================================================

EOF

cd "$ROOT_DIR"
docker_compose_up
