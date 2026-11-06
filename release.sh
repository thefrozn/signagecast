#!/bin/sh
# SignageCast – Release veröffentlichen (für die Projektpflege):
#
#   ./release.sh v0.14.0            prüfen, taggen, Paket bauen, signieren, hochladen, gegenprüfen
#   ./release.sh v0.14.0 --trocken  alles prüfen und Paket bauen/signieren, aber nichts veröffentlichen
#   ./release.sh v0.23.0 --player   nach der Action „Player-Image“: dessen .json signieren und hochladen
#
# Voraussetzungen: git, gh (angemeldet), minisign, python3 (+ python3-pyzipper für alle Tests), optional shellcheck.
# Signaturschlüssel: $SIGNATUR_SCHLUESSEL oder ~/.config/signagecast-signatur/signagecast.key (nie im Repo).
set -eu
TAG=${1:-}
TROCKEN=${2:-}
SCHLUESSEL_DATEI=${SIGNATUR_SCHLUESSEL:-$HOME/.config/signagecast-signatur/signagecast.key}
cd "$(dirname "$0")"

fehler() { echo "Abbruch: $*" >&2; exit 1; }
case "$TAG" in v[0-9]*.[0-9]*.[0-9]*) ;; *) fehler "Version als vX.Y.Z angeben";; esac
V=${TAG#v}

# Player-Image (seit 0.23): GitHub Actions baut es nach dem Tag; danach hier seine .json signieren und hochladen
if [ "$TROCKEN" = "--player" ]; then
  [ -r "$SCHLUESSEL_DATEI" ] || fehler "Signaturschlüssel fehlt: $SCHLUESSEL_DATEI"
  OEFFENTLICH=$(sed -n 's/^SCHLUESSEL=//p' werkzeug/aktualisieren.sh)
  P=$(mktemp -d)
  trap 'rm -rf "$P"' EXIT
  M="signagecast-player-$TAG.json"
  echo "== Warten auf das Player-Image ($M)"
  for _ in $(seq 1 90); do gh release download "$TAG" -p "$M" -D "$P" --clobber >/dev/null 2>&1 && break; sleep 20; done
  [ -s "$P/$M" ] || fehler "$M nicht im Release – läuft die Action „Player-Image“? (gh run list -w player.yml)"
  python3 -c 'import json,sys; m=json.load(open(sys.argv[1])); assert m["art"]=="signagecast-player-image" and m["version"]==sys.argv[2]' "$P/$M" "$V" \
    || fehler "$M passt nicht zu $TAG"
  minisign -Sqm "$P/$M" -s "$SCHLUESSEL_DATEI" -t "SignageCast Player $TAG"
  minisign -Vqm "$P/$M" -P "$OEFFENTLICH" || fehler "Signatur passt nicht zum öffentlichen Schlüssel"
  gh release upload "$TAG" "$P/$M.minisig" --clobber
  echo "   ok: $M signiert"
  # SBOM des Images (seit 0.30): Prüfsumme steht in der .json – erst prüfen, dann signieren
  S="signagecast-player-$TAG.cdx.json"
  gh release download "$TAG" -p "$S" -D "$P" --clobber >/dev/null 2>&1 || fehler "$S nicht im Release"
  python3 -c 'import hashlib,json,sys; m=json.load(open(sys.argv[1])); assert m["sbom"]["sha256"]==hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest()' "$P/$M" "$P/$S" \
    || fehler "$S passt nicht zur Prüfsumme in $M"
  minisign -Sqm "$P/$S" -s "$SCHLUESSEL_DATEI" -t "SignageCast Player $TAG SBOM"
  gh release upload "$TAG" "$P/$S.minisig" --clobber
  echo "   ok: $S signiert"
  exit 0
fi

echo "== Prüfen"
[ -z "$(git status --porcelain)" ] || fehler "Arbeitskopie nicht sauber (git status)"
[ "$(git rev-parse --abbrev-ref HEAD)" = main ] || fehler "nicht auf main"
git fetch -q origin
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || fehler "main ist nicht auf dem Stand von origin/main (push/pull)"
[ "$(cat VERSION)" = "$V" ] || fehler "VERSION ist $(cat VERSION), nicht $V"
grep -q "^## $TAG " CHANGELOG.md || fehler "CHANGELOG.md hat keinen Abschnitt „## $TAG …“"
git rev-parse -q --verify "refs/tags/$TAG" >/dev/null && fehler "Tag $TAG gibt es schon"
[ -r "$SCHLUESSEL_DATEI" ] || fehler "Signaturschlüssel fehlt: $SCHLUESSEL_DATEI"
# Der Schlüssel muss zu dem öffentlichen Schlüssel passen, den die Installationen prüfen
OEFFENTLICH=$(sed -n 's/^SCHLUESSEL=//p' werkzeug/aktualisieren.sh)
[ "$(sed -n 's/^SCHLUESSEL=//p' install.sh)" = "$OEFFENTLICH" ] || fehler "install.sh und aktualisieren.sh nennen verschiedene Schlüssel"
[ "$(sed -n 's/^SCHLUESSEL = "\(.*\)"$/\1/p' app/player.py)" = "$OEFFENTLICH" ] || fehler "app/player.py nennt einen anderen Schlüssel"
python3 -m unittest discover -s tests >/dev/null 2>&1 || fehler "Tests schlagen fehl (python3 -m unittest discover -s tests -v)"
find . -name __pycache__ -prune -exec rm -rf {} +
if command -v shellcheck >/dev/null; then
  shellcheck -S warning install.sh installieren.sh werkzeug/aktualisieren.sh render/tv-render.sh docker/start.sh proxmox/ct.sh \
    || fehler "shellcheck"
fi
echo "   ok: $TAG, Tests grün"

ARBEIT=$(mktemp -d)
trap 'rm -rf "$ARBEIT"' EXIT
A="signagecast-$TAG.tar.gz"

echo "== Paket, Prüfsumme, Signatur"
git archive --format=tar.gz --prefix="signagecast-$TAG/" -o "$ARBEIT/$A" HEAD
# SBOM (seit 0.30, CycloneDX): Fremdkomponenten, MediaMTX, Debian-Pakete; Zeitstempel = Commit (wiederholbar)
B="signagecast-$TAG.cdx.json"
SOURCE_DATE_EPOCH=$(git log -1 --format=%ct) python3 werkzeug/sbom.py paket --version "$V" --datei "$ARBEIT/$A" > "$ARBEIT/$B" \
  || fehler "SBOM"
(cd "$ARBEIT" && sha256sum "$A" "$B" > SHA256SUMS)
for f in "$A" "$B"; do
  minisign -Sqm "$ARBEIT/$f" -s "$SCHLUESSEL_DATEI" -t "SignageCast $TAG"
  minisign -Vqm "$ARBEIT/$f" -P "$OEFFENTLICH" || fehler "Signatur passt nicht zum öffentlichen Schlüssel im Programm"
done
sed -n "/^## $TAG /,/^## v/p" CHANGELOG.md | sed '1d;$d' > "$ARBEIT/notizen.md"
cat "$ARBEIT/SHA256SUMS"

if [ "$TROCKEN" = "--trocken" ]; then
  echo "== Trockenlauf: nichts veröffentlicht"
  exit 0
fi

echo "== Veröffentlichen"
git tag -a "$TAG" -m "SignageCast $TAG"
git push -q origin "$TAG"
gh release create "$TAG" "$ARBEIT/$A" "$ARBEIT/SHA256SUMS" "$ARBEIT/$A.minisig" "$ARBEIT/$B" "$ARBEIT/$B.minisig" --title "SignageCast $TAG" --notes-file "$ARBEIT/notizen.md"

echo "== Gegenprobe (von GitHub laden)"
P="$ARBEIT/probe"; mkdir "$P"
for _ in 1 2 3 4 5; do gh release download "$TAG" -D "$P" --clobber >/dev/null 2>&1 && break; sleep 3; done
(cd "$P" && sha256sum -c SHA256SUMS >/dev/null) || fehler "Prüfsumme der hochgeladenen Datei falsch"
for f in "$A" "$B"; do minisign -Vqm "$P/$f" -P "$OEFFENTLICH" -x "$P/$f.minisig" || fehler "Signatur von $f falsch"; done
echo "   ok: https://github.com/thefrozn/signagecast/releases/tag/$TAG"
echo "   Player-Image baut GitHub Actions (~20 min); danach: ./release.sh $TAG --player"
