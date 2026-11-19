#!/bin/sh
# SignageCast entfernen (seit 0.62) – Debian, Installations-ISO und Proxmox-Container von innen. Als root:
#
#   sh /opt/signagecast/werkzeug/deinstallieren.sh           Programm und Dienste entfernen, Einstellungen und Daten
#                                                             bleiben liegen (eine erneute Installation übernimmt sie)
#   sh /opt/signagecast/werkzeug/deinstallieren.sh --alles   zusätzlich Einstellungen, Daten und die Benutzer
#                                                             signagecast und tvadmin löschen
#   … --ja                                                    ohne Rückfrage
#
# Vorher wird immer eine Sicherung von /etc/signagecast und /var/lib/signagecast nach /root gelegt.
# Debian-Pakete (Chromium, ffmpeg, Cockpit …) bleiben installiert – sie können auch anderen Programmen dienen; der
# Befehl zum Entfernen steht in docs/INSTALL.md („Uninstall“). Tailscale (falls über SignageCast eingerichtet) bleibt.
# Docker/Podman, NAS, Windows und den ganzen Proxmox-Container entfernt man anders – siehe docs/INSTALL.md.
set -eu
ALLES=""; JA=""
for a in "$@"; do
  case "$a" in
    --alles|--all) ALLES=1 ;;
    --ja|--yes) JA=1 ;;
    *) echo "Unbekannte Option: $a  (erlaubt: --alles, --ja)"; exit 1 ;;
  esac
done
[ "$(id -u)" = 0 ] || { echo "Bitte als root ausführen."; exit 1; }
[ -d /opt/signagecast ] || [ -d /etc/signagecast ] || { echo "SignageCast ist hier nicht installiert."; exit 0; }

echo "SignageCast entfernen:"
echo "  - Dienste signagecast, signagecast-mediamtx, signagecast-hdmi, signagecast-aktualisieren, signagecast-startpasswort"
echo "  - /opt/signagecast, /opt/mediamtx, Cockpit-Erweiterung, signagecast-mcp"
if [ -n "$ALLES" ]; then
  echo "  - ALLE Einstellungen und Daten (/etc/signagecast, /var/lib/signagecast) und die Benutzer signagecast und tvadmin"
else
  echo "  Einstellungen und Daten bleiben in /etc/signagecast und /var/lib/signagecast (mit --alles auch löschen)."
fi
if [ -z "$JA" ]; then
  printf "Fortfahren? [j/N] "; read -r w </dev/tty || w=""
  case "$w" in j|J|y|Y|ja|yes) ;; *) echo "Abgebrochen."; exit 1 ;; esac
fi

SICH=/root/signagecast-sicherung-$(date +%Y%m%d-%H%M%S).tar.gz
( umask 077; tar -czf "$SICH" --ignore-failed-read -C / etc/signagecast var/lib/signagecast 2>/dev/null || true )
echo "== Sicherung: $SICH"

echo "== Dienste"
for d in signagecast-hdmi signagecast signagecast-mediamtx signagecast-aktualisieren.path signagecast-aktualisieren \
         signagecast-startpasswort.path signagecast-startpasswort; do
  systemctl disable --now "$d" >/dev/null 2>&1 || true
done
for n in Xvfb chromium ffmpeg pulseaudio cage; do pkill -KILL -u signagecast -x "$n" 2>/dev/null || true; done
rm -f /etc/systemd/system/signagecast.service /etc/systemd/system/signagecast-mediamtx.service \
      /etc/systemd/system/signagecast-hdmi.service /etc/systemd/system/signagecast-aktualisieren.service \
      /etc/systemd/system/signagecast-aktualisieren.path /etc/systemd/system/signagecast-startpasswort.service \
      /etc/systemd/system/signagecast-startpasswort.path /etc/systemd/system/seatd.service.d/signagecast.conf
rmdir /etc/systemd/system/seatd.service.d 2>/dev/null || true
systemctl daemon-reload

echo "== Programm"
rm -rf /opt/signagecast /opt/signagecast.vorher /opt/signagecast.neu /opt/signagecast.alt /opt/mediamtx \
       /usr/share/cockpit/signagecast /usr/local/bin/signagecast-mcp /var/lib/signagecast-aktualisierung \
       /root/signagecast-startpasswort /root/.signagecast-startpasswort.abdruck

if [ -n "$ALLES" ]; then
  echo "== Einstellungen, Daten, Benutzer"
  rm -rf /etc/signagecast /var/lib/signagecast
  if id signagecast >/dev/null 2>&1; then userdel signagecast 2>/dev/null || true; fi
  if id tvadmin >/dev/null 2>&1; then
    # Beim Installations-ISO ist tvadmin das Anmelde-Konto des Rechners (Gruppe sudo) – dann nicht löschen, sonst
    # sperrt man sich aus; ebenso nicht, wenn dieses Skript gerade über tvadmin (sudo) läuft
    if [ "${SUDO_USER:-}" = tvadmin ] || id -nG tvadmin | tr ' ' '\n' | grep -qx sudo; then
      echo "   Benutzer tvadmin bleibt (Anmelde-Konto dieses Rechners) – bei Bedarf später: userdel -r tvadmin"
    else
      # offene Sitzungen (z. B. Cockpit-Anmeldung, systemd --user) beenden, sonst verweigert userdel das Löschen
      loginctl terminate-user tvadmin >/dev/null 2>&1 || true
      pkill -KILL -u tvadmin 2>/dev/null || true
      sleep 1
      userdel -r tvadmin 2>/dev/null || userdel tvadmin 2>/dev/null || true
      if id tvadmin >/dev/null 2>&1; then echo "   Benutzer tvadmin ließ sich nicht löschen (noch angemeldet?) – später: userdel -r tvadmin"; fi
    fi
  fi
fi

echo
echo "SignageCast ist entfernt. Sicherung: $SICH"
[ -z "$ALLES" ] && echo "Einstellungen und Daten liegen weiter in /etc/signagecast und /var/lib/signagecast."
echo "Debian-Pakete sind noch installiert – entfernen nur, wenn nichts anderes sie braucht (siehe docs/INSTALL.md)."
