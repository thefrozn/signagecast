#!/bin/sh
# SignageCast – install or update inside an existing Debian 13 (LXC or VM) / Installation oder Update in Debian 13.
#
#   curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh
#
# Downloads the latest release from GitHub, verifies its minisign signature (releases from v0.13.0 on) and SHA-256
# checksum and runs installieren.sh.
# Running it again updates SignageCast; settings and data are kept.
# Options (environment): SIGNAGECAST_VERSION=v0.6.0 (instead of the latest), SIGNAGECAST_TARBALL=<url> (testing).
set -eu
REPO=thefrozn/signagecast
# Public key the releases are signed with (minisign) / Öffentlicher Schlüssel der Releases
SCHLUESSEL=RWS+1ozfjYuftY7DYt4RjDJLsJKenGkFL7prSxRjeDuk3c+++cclZqgD

[ "$(id -u)" = 0 ] || { echo "Please run as root / Bitte als root ausführen."; exit 1; }
if ! command -v curl >/dev/null 2>&1 || ! command -v minisign >/dev/null 2>&1; then
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl ca-certificates minisign >/dev/null
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
  # Signatur: beweist, dass das Paket vom Projekt stammt (die Prüfsumme allein liegt im selben Konto wie das Paket)
  if curl -fsSL -o "$ARBEIT/signagecast.tar.gz.minisig" "$BASIS/signagecast-$TAG.tar.gz.minisig" 2>/dev/null; then
    minisign -Vqm "$ARBEIT/signagecast.tar.gz" -P "$SCHLUESSEL" -x "$ARBEIT/signagecast.tar.gz.minisig" \
      || { echo "Signature invalid / Signatur ungültig – abgebrochen."; exit 1; }
    echo "   signature ok"
  elif [ "$(printf '%s\nv0.13.0\n' "$TAG" | sort -V | head -1)" = "v0.13.0" ]; then
    echo "Signature missing / Signatur fehlt – abgebrochen."; exit 1
  else
    echo "   (no signature – releases before v0.13.0 are not signed)"
  fi
fi

tar xzf "$ARBEIT/signagecast.tar.gz" -C "$ARBEIT"
QUELLE=$(find "$ARBEIT" -maxdepth 2 -name installieren.sh -printf '%h\n' | head -1)
[ -n "$QUELLE" ] || { echo "installieren.sh not found in the archive."; exit 1; }
sh "$QUELLE/installieren.sh" "$@"
