#!/bin/sh
# SignageCast – install or update inside an existing Debian 13 (LXC or VM) / Installation oder Update in Debian 13.
#
#   curl -fsSL https://raw.githubusercontent.com/tschmidt82/signagecast/main/install.sh | sh
#
# Downloads the latest release from GitHub, verifies its SHA-256 checksum and runs installieren.sh.
# Running it again updates SignageCast; settings and data are kept.
# Options (environment): SIGNAGECAST_VERSION=v0.6.0 (instead of the latest), SIGNAGECAST_TARBALL=<url> (testing).
set -eu
REPO=tschmidt82/signagecast

[ "$(id -u)" = 0 ] || { echo "Please run as root / Bitte als root ausführen."; exit 1; }
if ! command -v curl >/dev/null 2>&1; then
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl ca-certificates >/dev/null
fi

ARBEIT=$(mktemp -d)
trap 'rm -rf "$ARBEIT"' EXIT

if [ -n "${SIGNAGECAST_TARBALL:-}" ]; then
  echo "== SignageCast from $SIGNAGECAST_TARBALL"
  curl -fsSL -o "$ARBEIT/signagecast.tar.gz" "$SIGNAGECAST_TARBALL"
else
  TAG=${SIGNAGECAST_VERSION:-}
  if [ -z "$TAG" ]; then
    TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
  fi
  [ -n "$TAG" ] || { echo "Could not determine the latest release / Keine Version gefunden."; exit 1; }
  echo "== SignageCast $TAG"
  BASIS="https://github.com/$REPO/releases/download/$TAG"
  curl -fsSL -o "$ARBEIT/signagecast.tar.gz" "$BASIS/signagecast-$TAG.tar.gz"
  curl -fsSL -o "$ARBEIT/SHA256SUMS" "$BASIS/SHA256SUMS"
  ERWARTET=$(awk -v f="signagecast-$TAG.tar.gz" '$2 == f || $2 == "*"f {print $1}' "$ARBEIT/SHA256SUMS")
  IST=$(sha256sum "$ARBEIT/signagecast.tar.gz" | awk '{print $1}')
  [ -n "$ERWARTET" ] && [ "$ERWARTET" = "$IST" ] || { echo "Checksum mismatch / Prüfsumme falsch – abgebrochen."; exit 1; }
  echo "   checksum ok"
fi

tar xzf "$ARBEIT/signagecast.tar.gz" -C "$ARBEIT"
QUELLE=$(find "$ARBEIT" -maxdepth 2 -name installieren.sh -printf '%h\n' | head -1)
[ -n "$QUELLE" ] || { echo "installieren.sh not found in the archive."; exit 1; }
sh "$QUELLE/installieren.sh" "$@"
