#!/usr/bin/env bash
set -euo pipefail

GATEWAY="${IPFS_GATEWAY:-http://ipfs-server:8080}"
url="${1:?uso: $0 <url>}"

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
