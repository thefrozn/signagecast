# SignageCast PC-Player – im chroot des Images (von bauen.sh über mmdebstrap aufgerufen, /bin/sh -eu)
export DEBIAN_FRONTEND=noninteractive
chmod 755 /usr/lib/signagecast-player/agent.py /usr/lib/signagecast-player/start.sh /usr/lib/signagecast-player/medium.sh
chmod 644 /etc/systemd/system/signagecast-player.service
# Merkmal: dieser Player ist ein PC (der Agent passt Modell, Ausgänge, Ton, Schreibschutz und Updates daran an)
echo "SignageCast PC-Player (Debian 13 amd64, live)" > /etc/signagecast-pc
# Benutzer für mpv und Chromium (ohne Anmeldung)
useradd -r -m -d /var/lib/signage -s /usr/sbin/nologin -G video,render,audio signage
# Niemand meldet sich an: keine Konsolen (auch nicht per Strg+Alt+F2), kein Strg+Alt+Entf, root ohne Passwort gesperrt
systemctl disable getty@tty1.service 2>/dev/null || true
mkdir -p /etc/systemd/logind.conf.d
printf '[Login]\nNAutoVTs=0\nReserveVT=0\n' > /etc/systemd/logind.conf.d/signagecast.conf
systemctl mask ctrl-alt-del.target
passwd -l root >/dev/null
systemctl enable signagecast-player.service NetworkManager.service systemd-timesyncd.service
# seatd: Gruppe video darf den Bildschirm nehmen (Benutzer signage ist darin)
mkdir -p /etc/systemd/system/seatd.service.d
printf '[Service]\nExecStart=\nExecStart=/usr/bin/seatd -g video\n' > /etc/systemd/system/seatd.service.d/signagecast.conf
systemctl enable seatd.service
# Hotspot: jede Adresse zeigt auf den Player – Handys öffnen die Einrichtungsseite dann von selbst
mkdir -p /etc/NetworkManager/dnsmasq-shared.d /etc/NetworkManager/conf.d
echo 'address=/#/10.42.0.1' > /etc/NetworkManager/dnsmasq-shared.d/signagecast.conf
# LAN-Kabel ohne Einrichtung: NetworkManager verwaltet alle Anschlüsse selbst (DHCP)
printf '[main]\nplugins=keyfile\n\n[ifupdown]\nmanaged=true\n' > /etc/NetworkManager/conf.d/signagecast.conf
# Protokoll nur im RAM, Watchdog (wenn das Gerät einen hat) startet einen hängenden PC neu
mkdir -p /etc/systemd/journald.conf.d /etc/systemd/system.conf.d
printf '[Journal]\nStorage=volatile\nRuntimeMaxUse=32M\n' > /etc/systemd/journald.conf.d/signagecast.conf
printf '[Manager]\nRuntimeWatchdogSec=15\n' > /etc/systemd/system.conf.d/signagecast.conf
# Keine automatischen apt-Läufe: das System ist schreibgeschützt – Updates kommen mit einem neuen Image
systemctl mask apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true
echo signagecast-player > /etc/hostname
printf '127.0.0.1\tlocalhost\n127.0.1.1\tsignagecast-player\n::1\tlocalhost ip6-localhost ip6-loopback\n' > /etc/hosts
: > /etc/machine-id                                   # bei jedem Start neu (jeder Stick ist ein eigenes Gerät)
update-initramfs -u -k all
apt-get clean
