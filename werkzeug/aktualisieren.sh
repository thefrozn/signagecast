#!/bin/sh
# SignageCast – Updates (läuft als root, gestartet von signagecast-aktualisieren.path, wenn die Verwaltung eine Anfrage
# ablegt). Erlaubt sind nur diese Aktionen:
#   pruefen      Paketlisten holen, verfügbare System-Updates und neueste SignageCast-Version ermitteln
#   system       alle System-Updates installieren (apt-get upgrade, Konfigurationen bleiben)
#   sicherheit   nur Sicherheitsupdates (Quelle Debian-Security)
#   signagecast  neueste Version holen – nur mit gültiger minisign-Signatur –, vorher Einstellungen sichern, danach
#                prüfen, ob der Dienst läuft; sonst automatisch zurück zur vorigen Version
#   zurueck      vorige Version wiederherstellen
# Ergebnis: /var/lib/signagecast/aktualisierung.json (für die Verwaltung lesbar).
set -u
REPO=thefrozn/signagecast
# Öffentlicher Schlüssel, mit dem jedes Release signiert ist (minisign). Der private Schlüssel liegt beim Projekt.
SCHLUESSEL=RWS+1ozfjYuftY7DYt4RjDJLsJKenGkFL7prSxRjeDuk3c+++cclZqgD
DATEN=/var/lib/signagecast
ANFRAGE=$DATEN/update-anfrage
STATUS=$DATEN/aktualisierung.json
VORHER=/opt/signagecast.vorher
# Eigener Ordner nur für root: Dateien in $DATEN gehören dem Dienst-Benutzer – dort schreibt root nichts außer dem Status
# (mktemp + mv ersetzt auch einen untergeschobenen Symlink, statt ihm zu folgen)
ROOTDIR=/var/lib/signagecast-aktualisierung
install -d -m 700 -o root -g root "$ROOTDIR"
SICHERUNG=$ROOTDIR/vor-update.tar.gz
LOG=$ROOTDIR/letztes.log
# Nur für Tests: andere Adresse für Releases (Datei gehört root). Die Signatur wird trotzdem geprüft.
QUELLE_BASIS=$(cat /etc/signagecast/update-quelle 2>/dev/null || echo "https://github.com/$REPO/releases/download")
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8

json() { python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"; }
status() {   # status <aktion> <phase: laeuft|ok|fehler|zurueck> <meldung> [extra-json]
  status_datei "$1" "$@"                                          # je Aktion (das letzte „pruefen“ bleibt erhalten)
  [ "${STILL:-}" = 1 ] && [ "$1" = pruefen ] && return            # stilles Auffrischen ändert die „letzte“ Meldung nicht
  status_datei "" "$@"                                            # letzte Aktion
}
status_datei() {   # <ziel: aktion oder leer> <aktion> <phase> <meldung> [extra]
  # Inhalt im root-Ordner erzeugen und nur verschieben: Ein Symlink im Datenordner (gehört dem Dienst) wird so ersetzt,
  # nicht verfolgt – root liest und beschreibt dort nichts direkt.
  ZIEL=$1; shift
  T=$(mktemp "$ROOTDIR/.status.XXXXXX")
  printf '{"aktion": %s, "phase": %s, "meldung": %s, "zeit": %s, "ts": %s, "neustart_noetig": %s%s}\n' \
    "$(json "$1")" "$(json "$2")" "$(json "$3")" "$(json "$(date '+%Y-%m-%d %H:%M:%S')")" "$(date +%s)" \
    "$([ -f /var/run/reboot-required ] && echo true || echo false)" "${4:+, $4}" > "$T"
  chmod 644 "$T" && mv -f "$T" "$DATEN/aktualisierung${ZIEL:+-$ZIEL}.json"
}
protokoll() { echo "$*"; }

pruefen() {
  status pruefen laeuft "Paketlisten werden geholt"
  apt-get update -qq 2>&1 | tail -3
  # „Inst paket [alt] (neu Quelle [arch])“ aus der Simulation; Sicherheitsupdates erkennt man an „-security“
  LISTE=$(apt-get -s -o Debug::NoLocking=1 upgrade 2>/dev/null | python3 -c '
import json, re, sys
pakete = []
for z in sys.stdin:
    m = re.match(r"Inst (\S+) \[([^\]]*)\] \((\S+) ([^)]*)\)", z)
    if m:
        pakete.append({"name": m.group(1), "alt": m.group(2), "neu": m.group(3), "sicherheit": "-security" in m.group(4)})
print(json.dumps(pakete))')
  NEUESTE=$(curl -fsSL -m 20 "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
  status pruefen ok "geprüft" "\"pakete\": ${LISTE:-[]}, \"neueste\": $(json "${NEUESTE:-}"), \"installiert\": $(json "$(cat /opt/signagecast/VERSION)")"
}

system_aktualisieren() {   # $1 = alle | sicherheit
  status "$2" laeuft "Updates werden installiert"
  apt-get update -qq
  if [ "$1" = sicherheit ]; then
    PAKETE=$(apt-get -s -o Debug::NoLocking=1 upgrade 2>/dev/null | awk '/^Inst / && /-security/ {print $2}' | tr '\n' ' ')
    if [ -z "$PAKETE" ]; then status "$2" ok "keine Sicherheitsupdates"; return 0; fi
    # shellcheck disable=SC2086
    apt-get install -y -qq --only-upgrade -o Dpkg::Options::=--force-confold $PAKETE >"$LOG" 2>&1
  else
    apt-get upgrade -y -qq -o Dpkg::Options::=--force-confold >"$LOG" 2>&1
  fi
  RC=$?
  if [ $RC = 0 ]; then status "$2" ok "installiert"; else status "$2" fehler "apt-get: $(tail -2 "$LOG" | tr '\n' ' ')"; fi
}

dienst_gesund() {   # $1 = erwartete Version; bis zu 60 s warten
  for _ in $(seq 1 30); do
    if systemctl is-active -q signagecast && [ "$(cat /opt/signagecast/VERSION)" = "$1" ] \
       && curl -fs -m 5 -o /dev/null http://127.0.0.1:8080/daten.json; then
      return 0
    fi
    sleep 2
  done
  return 1
}

zurueck() {   # vorige Version und die Einstellungen von vor dem Update wiederherstellen
  [ -d "$VORHER" ] || { status zurueck fehler "keine vorige Version vorhanden"; return 1; }
  ALT=$(cat "$VORHER/VERSION" 2>/dev/null)
  systemctl stop signagecast
  rm -rf /opt/signagecast.fehlgeschlagen
  mv /opt/signagecast /opt/signagecast.fehlgeschlagen && mv "$VORHER" /opt/signagecast
  # als Dienst-Benutzer auspacken (seine eigenen Ordner) – root folgt so keinem untergeschobenen Symlink
  [ -f "$SICHERUNG" ] && runuser -u signagecast -- tar xzf - -C / --no-same-owner --no-overwrite-dir < "$SICHERUNG"
  for u in signagecast.service signagecast-mediamtx.service; do
    [ -f "/opt/signagecast/render/$u" ] && install -m 644 "/opt/signagecast/render/$u" "/etc/systemd/system/$u"
  done
  if [ -d /opt/signagecast/cockpit/signagecast ] && [ -d /usr/share/cockpit ]; then
    rm -rf /usr/share/cockpit/signagecast && cp -r /opt/signagecast/cockpit/signagecast /usr/share/cockpit/signagecast
  fi
  systemctl daemon-reload
  systemctl restart signagecast
  rm -rf /opt/signagecast.fehlgeschlagen
  if dienst_gesund "$ALT"; then status "$1" zurueck "zurück auf Version $ALT"; else status "$1" fehler "zurück auf $ALT, aber der Dienst läuft nicht"; fi
}

signagecast_aktualisieren() {
  status signagecast laeuft "neueste Version wird ermittelt"
  TAG=$(curl -fsSL -m 20 "https://api.github.com/repos/$REPO/releases/latest" | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
  [ -f /etc/signagecast/update-tag ] && TAG=$(cat /etc/signagecast/update-tag)          # nur für Tests
  [ -n "$TAG" ] || { status signagecast fehler "keine Version gefunden"; return 1; }
  JETZT=$(cat /opt/signagecast/VERSION)
  if [ "v$JETZT" = "$TAG" ]; then status signagecast ok "bereits aktuell ($JETZT)"; return 0; fi
  ARBEIT=$(mktemp -d)
  A="signagecast-$TAG.tar.gz"
  status signagecast laeuft "lade $TAG"
  if ! curl -fsSL -o "$ARBEIT/$A" "$QUELLE_BASIS/$TAG/$A" || ! curl -fsSL -o "$ARBEIT/SHA256SUMS" "$QUELLE_BASIS/$TAG/SHA256SUMS" \
     || ! curl -fsSL -o "$ARBEIT/$A.minisig" "$QUELLE_BASIS/$TAG/$A.minisig"; then
    rm -rf "$ARBEIT"; status signagecast fehler "Download von $TAG fehlgeschlagen (Signatur vorhanden?)"; return 1
  fi
  # Erst Signatur (beweist: vom Projekt), dann Prüfsumme
  if ! minisign -Vqm "$ARBEIT/$A" -P "$SCHLUESSEL" -x "$ARBEIT/$A.minisig"; then
    rm -rf "$ARBEIT"; status signagecast fehler "Signatur ungültig – Update abgelehnt"; return 1
  fi
  ERWARTET=$(awk -v f="$A" '$2 == f || $2 == "*"f {print $1}' "$ARBEIT/SHA256SUMS")
  if [ "$ERWARTET" != "$(sha256sum "$ARBEIT/$A" | awk '{print $1}')" ]; then
    rm -rf "$ARBEIT"; status signagecast fehler "Prüfsumme falsch – Update abgelehnt"; return 1
  fi
  # Einstellungen und Daten (ohne Caches/Browserprofile) für die Rückkehr sichern
  status signagecast laeuft "sichere Einstellungen"
  # als Dienst-Benutzer packen (Symlinks bleiben Symlinks), root legt die Datei in seinem eigenen Ordner ab
  TEILE=$(cd / && ls -d etc/signagecast var/lib/signagecast/streams.json var/lib/signagecast/strikes.json \
      var/lib/signagecast/qualitaet.json var/lib/signagecast/verlauf.json var/lib/signagecast/bilder 2>/dev/null | tr '\n' ' ')
  # shellcheck disable=SC2086
  (cd / && runuser -u signagecast -- tar czf - $TEILE) > "$SICHERUNG.neu" && mv "$SICHERUNG.neu" "$SICHERUNG"
  chmod 600 "$SICHERUNG"
  tar xzf "$ARBEIT/$A" -C "$ARBEIT"
  Q=$(find "$ARBEIT" -maxdepth 2 -name installieren.sh -printf '%h\n' | head -1)
  NEU=$(cat "$Q/VERSION")
  status signagecast laeuft "installiere $NEU"
  if ! sh "$Q/installieren.sh" >"$LOG" 2>&1; then
    status signagecast laeuft "Installation fehlgeschlagen – gehe zurück"
    rm -rf "$ARBEIT"; zurueck signagecast; return 1
  fi
  rm -rf "$ARBEIT"
  if dienst_gesund "$NEU"; then
    status signagecast ok "aktualisiert von $JETZT auf $NEU"
  else
    status signagecast laeuft "Dienst läuft nach dem Update nicht – gehe zurück"
    zurueck signagecast
  fi
}

# ---------- Anfrage auswerten ----------
AKTION=${1:-}
if [ -z "$AKTION" ] && [ -e "$ANFRAGE" ]; then
  if [ -L "$ANFRAGE" ] || [ ! -f "$ANFRAGE" ]; then rm -f "$ANFRAGE"; exit 1; fi   # nur eine echte Datei, kein Symlink
  AKTION=$(head -c 20 "$ANFRAGE" | tr -cd 'a-z')
  rm -f "$ANFRAGE"
fi
case "$AKTION" in
  pruefen) pruefen ;;
  system) system_aktualisieren alle system; STILL=1 pruefen ;;          # Liste danach still auffrischen
  sicherheit) system_aktualisieren sicherheit sicherheit; STILL=1 pruefen ;;
  signagecast) signagecast_aktualisieren; STILL=1 pruefen ;;
  zurueck) zurueck zurueck ;;
  "") exit 0 ;;
  *) status unbekannt fehler "unbekannte Aktion"; exit 1 ;;
esac
