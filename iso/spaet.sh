#!/bin/sh
# SignageCast – letzter Schritt im Debian-Installer (preseed/late_command, Installations-ISO seit 0.52):
# fragt „Bild per HDMI?“ und legt das Programm für den ersten Start ab. SignageCast selbst installiert sich erst beim
# ersten Start (signagecast-ersteinrichtung.service) – im Installer läuft kein systemd, das Skript braucht ihn.
set -e
Q=/cdrom/signagecast
# shellcheck source=/dev/null
. /usr/share/debconf/confmodule
debconf-loadtemplate signagecast "$Q/vorlagen"
db_fset signagecast/hdmi seen false
db_input critical signagecast/hdmi || true
db_go || true
db_get signagecast/hdmi
HDMI=0
[ "$RET" = true ] && HDMI=1

Z=/target/opt/signagecast-installation
mkdir -p "$Z"
tar -xzf "$Q/signagecast.tar.gz" -C "$Z"
echo "SC_HDMI_START=$HDMI" > "$Z/antworten"
cp "$Z/iso/signagecast-ersteinrichtung.service" /target/etc/systemd/system/
mkdir -p /target/etc/systemd/system/multi-user.target.wants
ln -sf /etc/systemd/system/signagecast-ersteinrichtung.service /target/etc/systemd/system/multi-user.target.wants/
# Anmeldebildschirm (Konsole): Adresse der Verwaltung – \4 setzt agetty durch die IPv4-Adresse
mkdir -p /target/etc/issue.d
printf 'SignageCast – Verwaltung / admin:  https://\\4:9090   (tvadmin)\n\n' > /target/etc/issue.d/signagecast.issue
