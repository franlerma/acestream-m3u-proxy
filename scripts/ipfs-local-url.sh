#!/usr/bin/env bash
# Convierte una URL de gateway IPFS/IPNS a la URL del nodo local.
# Host: IP local de la maquina (o IPFS_HOST).
# Puerto: mapeo de puertos del servicio ipfs-server en docker-compose.yml (o IPFS_PORT).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/../docker-compose.yml}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-ipfs-server}"

url="${1:?uso: $0 <url>}"

local_ip() {
  local ip=""
  if command -v ipconfig >/dev/null 2>&1; then
    ip="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
  elif command -v hostname >/dev/null 2>&1; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  fi
  [[ -n "$ip" ]] || { echo "error: no se pudo detectar la IP local; define IPFS_HOST" >&2; exit 1; }
  echo "$ip"
}

# Puerto de host del primer mapeo "host:container" del servicio en el compose.
compose_port() {
  [[ -f "$COMPOSE_FILE" ]] || { echo "error: no existe $COMPOSE_FILE; define IPFS_PORT" >&2; exit 1; }
  local port
  port="$(awk -v svc="$COMPOSE_SERVICE" '
    /^[^[:space:]#]/            { in_services = ($0 ~ /^services:/); in_svc = 0; in_ports = 0; next }
    !in_services                { next }
    /^  [^[:space:]#][^:]*:[[:space:]]*$/ {
      name = $1; sub(/:$/, "", name); in_svc = (name == svc); in_ports = 0; next
    }
    !in_svc                     { next }
    /^    ports:/               { in_ports = 1; next }
    in_ports && /^      -/ {
      gsub(/^[[:space:]]*-[[:space:]]*/, "")
      gsub(/"/, ""); gsub(/\047/, ""); sub(/\/.*/, "")
      n = split($0, a, ":")
      if (n >= 2) { print a[n-1]; exit }
    }
    in_ports && /^    [^[:space:]-]/ { in_ports = 0 }
  ' "$COMPOSE_FILE")"
  [[ -n "$port" ]] || { echo "error: sin mapeo de puertos para '$COMPOSE_SERVICE' en $COMPOSE_FILE; define IPFS_PORT" >&2; exit 1; }
  echo "$port"
}

HOST="${IPFS_HOST:-$(local_ip)}"
PORT="${IPFS_PORT:-$(compose_port)}"
GATEWAY="${IPFS_GATEWAY:-http://$HOST:$PORT}"

# quitar esquema y host, y el fragmento (#...)
path="${url#*://}"
path="${path#*/}"
path="${path%%#*}"

case "$path" in
  ipfs/*|ipns/*) out="$path" ;;            # ya trae prefijo
  *)
    first="${path%%/*}"
    case "$first" in
      Qm*|bafy*|bafk*) ns=ipfs ;;          # CID
      *)               ns=ipns ;;          # k51..., dominios DNSLink
    esac
    out="$ns/$path"
    ;;
esac

echo "$GATEWAY/$out"
