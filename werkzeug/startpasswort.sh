#!/bin/sh
# SignageCast (seit 0.62): Hat tvadmin inzwischen ein eigenes Passwort (Abdruck des Eintrags in /etc/shadow anders als
# bei der Installation), die Datei mit dem Startpasswort löschen und die Beobachtung abschalten.
set -eu
D=/root/signagecast-startpasswort
A=/root/.signagecast-startpasswort.abdruck
[ -f "$D" ] || exit 0
JETZT=$(getent shadow tvadmin | cut -d: -f2 | sha256sum | cut -d' ' -f1)
if [ ! -f "$A" ] || [ "$JETZT" != "$(cat "$A")" ]; then
  rm -f "$D" "$A"
  systemctl disable --now signagecast-startpasswort.path >/dev/null 2>&1 || true
  echo "Startpasswort geändert – Datei gelöscht."
fi
