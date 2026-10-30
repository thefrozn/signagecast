#!/bin/sh
# SignageCast – Release veröffentlichen (für die Projektpflege):
#
#   ./release.sh v0.14.0            prüfen, taggen, Paket bauen, signieren, hochladen, gegenprüfen
#   ./release.sh v0.14.0 --trocken  alles prüfen und Paket bauen/signieren, aber nichts veröffentlichen
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
(cd "$ARBEIT" && sha256sum "$A" > SHA256SUMS)
minisign -Sqm "$ARBEIT/$A" -s "$SCHLUESSEL_DATEI" -t "SignageCast $TAG"
minisign -Vqm "$ARBEIT/$A" -P "$OEFFENTLICH" || fehler "Signatur passt nicht zum öffentlichen Schlüssel im Programm"
sed -n "/^## $TAG /,/^## v/p" CHANGELOG.md | sed '1d;$d' > "$ARBEIT/notizen.md"
cat "$ARBEIT/SHA256SUMS"

if [ "$TROCKEN" = "--trocken" ]; then
  echo "== Trockenlauf: nichts veröffentlicht"
  exit 0
fi

echo "== Veröffentlichen"
git tag -a "$TAG" -m "SignageCast $TAG"
git push -q origin "$TAG"
gh release create "$TAG" "$ARBEIT/$A" "$ARBEIT/SHA256SUMS" "$ARBEIT/$A.minisig" --title "SignageCast $TAG" --notes-file "$ARBEIT/notizen.md"

echo "== Gegenprobe (von GitHub laden)"
P="$ARBEIT/probe"; mkdir "$P"
for _ in 1 2 3 4 5; do gh release download "$TAG" -D "$P" --clobber >/dev/null 2>&1 && break; sleep 3; done
(cd "$P" && sha256sum -c SHA256SUMS >/dev/null) || fehler "Prüfsumme der hochgeladenen Datei falsch"
minisign -Vqm "$P/$A" -P "$OEFFENTLICH" -x "$P/$A.minisig" || fehler "Signatur der hochgeladenen Datei falsch"
echo "   ok: https://github.com/thefrozn/signagecast/releases/tag/$TAG"
