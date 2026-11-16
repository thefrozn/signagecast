#!/bin/sh
# SignageCast – erster Start nach der Installation vom ISO (seit 0.52): SignageCast installieren. Braucht Internet für
# die Pakete; ohne Netz bricht es ab und versucht es beim nächsten Start erneut. Danach räumt es sich selbst weg.
set -u
Q=/opt/signagecast-installation
SC_HDMI_START=0
# shellcheck disable=SC1091
[ -f "$Q/antworten" ] && . "$Q/antworten"
echo "== SignageCast wird eingerichtet / setting up SignageCast (einige Minuten / a few minutes)"
for _ in $(seq 1 60); do getent hosts deb.debian.org >/dev/null 2>&1 && break; sleep 5; done
if ! (cd "$Q" && SC_HDMI=1 sh installieren.sh); then
  echo "== Einrichtung fehlgeschlagen / setup failed – neuer Versuch beim nächsten Start / retry on next boot"
  exit 1
fi
if [ "$SC_HDMI_START" = 1 ]; then
  # Bild per HDMI: der Datendienst legt das Gerät beim nächsten Start an (erster Kanal)
  touch /var/lib/signagecast/hdmi-start && chown signagecast:signagecast /var/lib/signagecast/hdmi-start
  systemctl restart signagecast
fi
systemctl disable signagecast-ersteinrichtung.service >/dev/null 2>&1
rm -f /etc/systemd/system/signagecast-ersteinrichtung.service
rm -rf "$Q"
IP=$(hostname -I | awk '{print $1}')
echo
echo "== SignageCast ist bereit / is ready:  https://$IP:9090   (tvadmin + Passwort aus der Installation / password from setup)"
