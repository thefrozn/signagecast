#!/bin/bash
# SignageCast – Start im Docker-/Podman-Container (läuft unter tini). Richtet /data ein, gibt dem Benutzer signagecast
# Zugriff auf die Grafik und startet Datendienst und MediaMTX (das Rendern startet MediaMTX auf Abruf).
# Endet einer der beiden, endet der Container – Docker/Podman startet ihn mit "restart: unless-stopped" neu.
set -eu
mkdir -p /data/config
[ "$(stat -c %U /data/config)" = signagecast ] || chown -R signagecast:signagecast /data
chmod 750 /data && chmod 700 /data/config

# Grafik: Gruppe des Geräts übernehmen (Docker: z. B. "render" des Hosts). Gehört es keiner abgebildeten Gruppe
# (rootless Podman mit --group-add keep-groups: "nogroup"), die Gruppen des Containers behalten.
GRUPPEN=--clear-groups
if [ -e /dev/dri/renderD128 ]; then
  GID=$(stat -c %g /dev/dri/renderD128)
  if [ "$GID" = 65534 ]; then
    GRUPPEN=--keep-groups
  elif [ "$GID" != 0 ]; then
    getent group "$GID" >/dev/null || groupadd -g "$GID" grafik
    GRUPPEN="--groups=$GID"
  fi
fi
export HOME=/var/lib/signagecast USER=signagecast
ALS=(setpriv --reuid=signagecast --regid=signagecast "$GRUPPEN" --inh-caps=-all)

NEU=""; [ -f /data/config/einstellungen.json ] || NEU=1
if [ ! -f /data/config/mediamtx.yml ]; then
  sed "s#{PFADE}#  tv:\n    runOnDemand: /opt/signagecast/render/tv-render.sh#" /opt/signagecast/render/mediamtx.yml > /data/config/mediamtx.yml
  chown signagecast:signagecast /data/config/mediamtx.yml && chmod 600 /data/config/mediamtx.yml
fi

cd /data
"${ALS[@]}" python3 -I /opt/signagecast/app/dienst.py & DIENST=$!
"${ALS[@]}" /opt/mediamtx/mediamtx /etc/signagecast/mediamtx.yml & MTX=$!
trap 'kill -TERM $DIENST $MTX 2>/dev/null' TERM INT

if [ -n "$NEU" ]; then   # Neuinstallation: mit der Startliste (Tier- und Natur-Livestreams) beginnen
  for _ in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:8080/daten.json && break; sleep 1; done
  curl -sS -o /dev/null -H "X-SignageCast: 1" -H "Content-Type: application/json" \
    --data-binary @/opt/signagecast/profile/start.json http://127.0.0.1:8080/api/sicherung && echo "Startliste eingespielt."
fi
echo "SignageCast $(cat /opt/signagecast/VERSION): Verwaltung http://<host>:${SC_VERWALTUNG_PORT:-9090} · Stream http://<host>:8888/tv"

wait -n $DIENST $MTX || true
kill -TERM $DIENST $MTX 2>/dev/null || true
wait
