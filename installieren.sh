#!/bin/sh
# SignageCast – Installation und Update auf Debian 13 (z. B. Proxmox-LXC mit durchgereichter Intel-Grafik /dev/dri/renderD128).
# Aufruf als root im Projektordner:  sh installieren.sh [--profil datei.json]
# Optional: SC_STREAM_PORT=8899 sh installieren.sh  – anderer Port für den Stream (Standard 8888, wird gemerkt).
# Optional: SC_SICHERUNG=/pfad/sicherung.zip [SC_SICHERUNG_PASSWORT=…] – Sicherung (ZIP oder .json) gleich einspielen.
# In einem Container (LXC) bekommt der Benutzer tvadmin das Startpasswort „tvadmin“; auf einem echten Rechner (nativ)
# ein zufälliges, das am Ende angezeigt wird. Ist Cockpit schon installiert, erscheint SignageCast dort als Menüpunkt.
# Ein erneuter Aufruf aktualisiert Programm und Dienste; Einstellungen und Daten bleiben erhalten.
set -eu
QUELLE=$(cd "$(dirname "$0")" && pwd)
MTX_VERSION=v1.21.3
PROFIL=""
[ "${1:-}" = "--profil" ] && PROFIL=$(readlink -f "$2")
# Neuinstallation ohne Profil: mit der Startliste (Tier- und Natur-Livestreams) beginnen
if [ -z "$PROFIL" ] && [ ! -f /etc/signagecast/einstellungen.json ] && [ ! -d /etc/tv-stream ]; then
  PROFIL="$QUELLE/profile/start.json"
fi

[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
grep -q 'VERSION_ID="13"' /etc/os-release || echo "Warnung: getestet nur mit Debian 13."
[ -e /dev/dri/renderD128 ] || echo "Warnung: /dev/dri/renderD128 fehlt – ohne Grafikeinheit kann der Stream nicht kodiert werden."

# Container (lxc, docker …) oder nativ (VM/echter Rechner)?
UMGEBUNG=$(systemd-detect-virt -c 2>/dev/null || true); [ -n "$UMGEBUNG" ] || UMGEBUNG=none
# Stream-Port: angegeben > gemerkt > 8888
PORT=${SC_STREAM_PORT:-$(sed -n 's/^SC_STREAM_PORT=//p' /etc/signagecast/umgebung 2>/dev/null || true)}
PORT=${PORT:-8888}
case "$PORT" in *[!0-9]*|"") echo "SC_STREAM_PORT muss eine Zahl sein."; exit 1;; esac
# Ist der Port schon von einem anderen Programm belegt? (MediaMTX von SignageCast selbst ist ok)
if command -v ss >/dev/null && ss -ltnpH "sport = :$PORT" 2>/dev/null | grep -v '"mediamtx"' | grep -q .; then
  echo "Port $PORT ist schon belegt:"; ss -ltnpH "sport = :$PORT"
  echo "Bitte einen anderen Stream-Port wählen, z. B.:  SC_STREAM_PORT=$((PORT + 11)) sh installieren.sh"
  exit 1
fi
[ -d /usr/share/cockpit ] && [ ! -d /usr/share/cockpit/signagecast ] && COCKPIT_DA=1

echo "== Pakete"
export DEBIAN_FRONTEND=noninteractive
if [ -f /etc/apt/sources.list.d/debian.sources ] && ! grep -q "non-free" /etc/apt/sources.list.d/debian.sources; then
  sed -i "s/^Components:.*/Components: main contrib non-free non-free-firmware/" /etc/apt/sources.list.d/debian.sources
fi
apt-get update -qq
apt-get install -y -qq --no-install-recommends xvfb chromium ffmpeg vainfo intel-media-va-driver-non-free mesa-va-drivers \
  pulseaudio pulseaudio-utils fonts-roboto-unhinted fonts-dejavu-core fonts-open-sans fonts-lato fonts-montserrat \
  fonts-ubuntu fonts-cantarell fonts-comic-neue fonts-firacode fonts-noto-core fonts-noto-color-emoji python3 python3-pyzipper curl ca-certificates procps \
  cockpit-ws cockpit-system cockpit-bridge >/dev/null

echo "== MediaMTX $MTX_VERSION"
if ! /opt/mediamtx/mediamtx --version 2>/dev/null | grep -q "$MTX_VERSION"; then
  T=$(mktemp -d); F=mediamtx_${MTX_VERSION}_linux_amd64.tar.gz
  curl -sSfL -o "$T/$F" "https://github.com/bluenviron/mediamtx/releases/download/$MTX_VERSION/$F"
  curl -sSfL -o "$T/sum" "https://github.com/bluenviron/mediamtx/releases/download/$MTX_VERSION/checksums.sha256"
  (cd "$T" && grep -F "*$F" sum | sha256sum -c - >/dev/null) || { echo "Prüfsumme MediaMTX falsch"; exit 1; }
  mkdir -p /opt/mediamtx && tar xzf "$T/$F" -C /opt/mediamtx && rm -rf "$T"
fi

echo "== Benutzer und Ordner"
id signagecast >/dev/null 2>&1 || useradd -r -M -d /var/lib/signagecast -s /usr/sbin/nologin signagecast

# Umzug einer Installation unter dem alten Namen „TV-Stream“ (bis 0.4.1): Dienste stoppen, Einstellungen und Daten
# (Streams, Strikes, Layouts, Bilder, Browser-Profile) übernehmen, alte Programmteile entfernen.
if [ -d /etc/tv-stream ] && [ ! -d /etc/signagecast ]; then
  echo "   Umzug von TV-Stream: /etc/tv-stream, /var/lib/tv-stream -> signagecast"
  systemctl disable --now tv-stream >/dev/null 2>&1 || true
  if grep -qs "/etc/tv-stream/mediamtx.yml" /etc/systemd/system/mediamtx.service; then
    systemctl disable --now mediamtx >/dev/null 2>&1 || true
    rm -f /etc/systemd/system/mediamtx.service
  fi
  rm -f /etc/systemd/system/tv-stream.service
  pkill -u tv -f "/opt/tv-stream/" 2>/dev/null || true
  for n in ffmpeg chromium Xvfb pulseaudio; do pkill -KILL -u tv -x $n 2>/dev/null || true; done
  mv /etc/tv-stream /etc/signagecast
  [ -d /var/lib/tv-stream ] && mv /var/lib/tv-stream /var/lib/signagecast
  rm -rf /var/lib/signagecast/run /var/lib/signagecast/kette-* /opt/tv-stream /usr/share/cockpit/tv-stream
  # Pfade in der MediaMTX-Konfiguration – der Datendienst schreibt sie beim Start ohnehin neu
  sed -i "s#/opt/tv-stream/#/opt/signagecast/#g" /etc/signagecast/mediamtx.yml
  UMZUG=1
fi
install -d -o signagecast -g signagecast -m 750 /var/lib/signagecast
install -d -o signagecast -g signagecast -m 700 /etc/signagecast
if [ "$PORT" != 8888 ] || [ -f /etc/signagecast/umgebung ]; then
  echo "SC_STREAM_PORT=$PORT" > /etc/signagecast/umgebung
  chown signagecast:signagecast /etc/signagecast/umgebung && chmod 600 /etc/signagecast/umgebung
fi
chown -R signagecast:signagecast /etc/signagecast /var/lib/signagecast

echo "== Programm"
rm -rf /opt/signagecast.neu && mkdir -p /opt/signagecast.neu
cp -r "$QUELLE/app" "$QUELLE/www" "$QUELLE/render" "$QUELLE/VERSION" /opt/signagecast.neu/
chown -R root:root /opt/signagecast.neu && chmod -R a+rX,go-w /opt/signagecast.neu && chmod 755 /opt/signagecast.neu/render/tv-render.sh
rm -rf /opt/signagecast.alt; [ -d /opt/signagecast ] && mv /opt/signagecast /opt/signagecast.alt
mv /opt/signagecast.neu /opt/signagecast && rm -rf /opt/signagecast.alt
# Startfassung mit einem Pfad "tv"; der Datendienst schreibt danach die Pfade aller Fernseher hinein
if [ ! -f /etc/signagecast/mediamtx.yml ] || grep -q "runOnDemand: /usr/local/bin\|{ABSCHALTEN}" /etc/signagecast/mediamtx.yml; then
  sed "s#{PFADE}#  tv:\n    runOnDemand: /opt/signagecast/render/tv-render.sh#" /opt/signagecast/render/mediamtx.yml > /etc/signagecast/mediamtx.yml
fi
chown signagecast:signagecast /etc/signagecast/mediamtx.yml && chmod 600 /etc/signagecast/mediamtx.yml

echo "== Cockpit-Erweiterung"
rm -rf /usr/share/cockpit/signagecast && cp -r "$QUELLE/cockpit/signagecast" /usr/share/cockpit/signagecast
chmod -R a+rX /usr/share/cockpit/signagecast
systemctl enable --now cockpit.socket >/dev/null 2>&1
if ! id tvadmin >/dev/null 2>&1; then
  useradd -m -s /bin/bash tvadmin
  if [ "$UMGEBUNG" = none ]; then
    # Echter Rechner: kein bekanntes Passwort für ein Linux-Konto, das sich über Cockpit anmelden kann
    STARTPW=$(head -c 64 /dev/urandom | tr -dc 'A-Za-z0-9' | head -c 14)
  else
    STARTPW=tvadmin
  fi
  echo "tvadmin:$STARTPW" | chpasswd
  NEUER_ADMIN=1
fi
usermod -aG systemd-journal tvadmin

echo "== Dienste"
install -m 644 /opt/signagecast/render/signagecast.service /etc/systemd/system/signagecast.service
# MediaMTX nur neu starten, wenn sich seine Dienstdatei geändert hat – sonst läuft der Stream am Fernseher weiter
# (Änderungen an tv-render.sh wirken beim nächsten Start der Kette, die Pfade schreibt der Datendienst)
MTX_NEU=1; cmp -s /opt/signagecast/render/signagecast-mediamtx.service /etc/systemd/system/signagecast-mediamtx.service && MTX_NEU=""
install -m 644 /opt/signagecast/render/signagecast-mediamtx.service /etc/systemd/system/signagecast-mediamtx.service
systemctl daemon-reload
systemctl enable signagecast signagecast-mediamtx >/dev/null 2>&1
systemctl restart signagecast
if [ -n "$MTX_NEU" ]; then systemctl restart signagecast-mediamtx; else systemctl is-active -q signagecast-mediamtx || systemctl start signagecast-mediamtx; fi

if [ -n "${SC_SICHERUNG:-}" ]; then
  # Sicherung einer anderen Instanz übernehmen (Passwort nur über die Umgebung, nie als Argument)
  echo "== Sicherung einspielen: $SC_SICHERUNG"
  for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null http://127.0.0.1:8080/daten.json && break; sleep 1; done
  python3 -I - "$SC_SICHERUNG" <<'PY'
import base64, json, os, sys, urllib.request
pfad = sys.argv[1]
roh = open(pfad, "rb").read()
if pfad.endswith(".json"):
    ziel, daten = "/api/sicherung", json.loads(roh)
else:
    ziel, daten = "/api/sicherung/zip", {"daten": base64.b64encode(roh).decode(), "passwort": os.environ.get("SC_SICHERUNG_PASSWORT", ""), "strikes": True}
anf = urllib.request.Request("http://127.0.0.1:8080" + ziel, data=json.dumps(daten).encode(),
                             headers={"X-SignageCast": "1", "Content-Type": "application/json"})
r = json.load(urllib.request.urlopen(anf, timeout=300))
print("   eingespielt" if r.get("ok") else "   Fehler: " + str(r.get("fehler")))
sys.exit(0 if r.get("ok") else 1)
PY
  PROFIL=""                               # Sicherung ersetzt die Startliste
fi
if [ -n "$PROFIL" ]; then
  echo "== Profil einspielen: $PROFIL"
  for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null http://127.0.0.1:8080/daten.json && break; sleep 1; done
  curl -sSf -H "X-SignageCast: 1" -H "Content-Type: application/json" --data-binary "@$PROFIL" http://127.0.0.1:8080/api/sicherung
  echo
fi

IP=$(hostname -I | awk '{print $1}')
echo
echo "Fertig (Version $(cat /opt/signagecast/VERSION))."
[ -n "${UMZUG:-}" ] && echo "  Alte Installation „TV-Stream“ übernommen. Der frühere Systembenutzer „tv“ wird nicht mehr gebraucht."
echo "  Verwaltung:  https://$IP:9090   (Benutzer tvadmin$([ -n "${COCKPIT_DA:-}" ] && echo " – oder dein Cockpit-Benutzer; SignageCast ist ein neuer Menüpunkt"))"
if [ -n "${NEUER_ADMIN:-}" ]; then
  if [ "$STARTPW" = tvadmin ]; then echo "  Startpasswort = Benutzername. Bitte nach dem ersten Anmelden ändern (Konten → tvadmin)."
  else echo "  Startpasswort für tvadmin: $STARTPW   (nur jetzt sichtbar – bitte notieren oder ändern: passwd tvadmin)"; fi
fi
echo "  Stream (TV): http://$IP:$PORT/tv   (weitere Fernseher: http://$IP:$PORT/<kennung>)"
echo "  Danach in der Verwaltung unter „Verbindung“ Home Assistant einrichten (Anleitung steht dort)."
