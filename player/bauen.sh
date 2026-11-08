#!/bin/sh
# SignageCast Player – Image bauen (GitHub Actions auf ubuntu-24.04-arm, als root; arm64 läuft dort nativ im chroot).
# Nimmt das offizielle Raspberry Pi OS Lite (64 bit, mit Prüfsumme), baut mpv, qrencode, overlayroot und den Player ein
# (seit 0.24 auch Chromium im Kiosk-Rahmen cage für den Direktmodus)
# und legt auf der Boot-Partition den Platzhalter signagecast.json (16 KiB) an. Die Verwaltung schreibt beim Herunterladen
# die Gerätedaten genau an diese Stelle des Images (Versatz steht in der .json daneben) – ohne mounten, auch im Container.
#
#   sudo sh player/bauen.sh <ausgabeordner> <version>
set -eu
AUS=$1
V=$2
QUELLE=https://downloads.raspberrypi.com/raspios_lite_arm64_latest
HIER=$(cd "$(dirname "$0")" && pwd)
A=$(mktemp -d)
LOOP=
aufraeumen() {
  umount -R "$A/root" 2>/dev/null || true
  [ -n "$LOOP" ] && losetup -d "$LOOP" 2>/dev/null || true
  rm -rf "$A"
}
trap aufraeumen EXIT

echo "== Raspberry Pi OS Lite laden"
URL=$(curl -fsSLI -o /dev/null -w '%{url_effective}' "$QUELLE")
echo "   $URL"
curl -fsSL -o "$A/os.img.xz" "$URL"
SUMME=$(curl -fsSL "$URL.sha256" | awk '{print $1}')
echo "$SUMME  $A/os.img.xz" | sha256sum -c -
xz -d "$A/os.img.xz"
IMG=$A/os.img

echo "== Platz schaffen und einhängen"
truncate -s +2048M "$IMG"                # Platz für mpv und Chromium
parted -s "$IMG" resizepart 2 100%
LOOP=$(losetup -fP --show "$IMG")
e2fsck -fy "${LOOP}p2" >/dev/null || true
resize2fs "${LOOP}p2" >/dev/null
mkdir "$A/root"
mount "${LOOP}p2" "$A/root"
mount "${LOOP}p1" "$A/root/boot/firmware"
for d in dev dev/pts proc sys; do mount --bind "/$d" "$A/root/$d"; done
mv "$A/root/etc/resolv.conf" "$A/resolv.conf.orig" 2>/dev/null || true
cp -L /etc/resolv.conf "$A/root/etc/resolv.conf"

echo "== Player einbauen"
install -d "$A/root/usr/lib/signagecast-player"
install -m 755 "$HIER/agent.py" "$HIER/start.sh" "$A/root/usr/lib/signagecast-player/"
install -m 644 "$HIER/signagecast-player.service" "$A/root/etc/systemd/system/"
chroot "$A/root" /bin/sh -eu <<'CHROOT'
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q --no-install-recommends mpv qrencode overlayroot iw rfkill unattended-upgrades
# Direktmodus (seit 0.24): Chromium in cage (Wayland-Kiosk), seatd vergibt den Bildschirm ohne Anmeldung, grim macht
# Bildschirmfotos, wlr-randr stellt Auflösung und Drehung ein, amixer die Lautstärke
apt-get install -y -q --no-install-recommends cage seatd grim wlr-randr alsa-utils fonts-dejavu-core fonts-noto-color-emoji
apt-get install -y -q --no-install-recommends chromium || apt-get install -y -q --no-install-recommends chromium-browser
command -v chromium >/dev/null || command -v chromium-browser >/dev/null
update-initramfs -u -k all
apt-get clean
rm -rf /var/lib/apt/lists/*
# Benutzer für mpv (ohne Anmeldung); der Dialog „Benutzer anlegen“ beim ersten Start entfällt
useradd -r -m -d /var/lib/signage -s /usr/sbin/nologin -G video,render,audio signage
systemctl mask userconfig.service
systemctl disable getty@tty1.service
systemctl enable signagecast-player.service
# seatd: Gruppe video darf den Bildschirm nehmen (Benutzer signage ist darin)
mkdir -p /etc/systemd/system/seatd.service.d
if [ -f /usr/lib/systemd/system/seatd.service ] || [ -f /lib/systemd/system/seatd.service ]; then
  # Debian liefert /usr/sbin/seatd (bis 0.35 stand hier /usr/bin – seatd startete nie, der Agent repariert das zur Laufzeit)
  printf '[Service]\nExecStart=\nExecStart=%s -g video\n' "$(command -v seatd)" > /etc/systemd/system/seatd.service.d/signagecast.conf
else
  printf '[Unit]\nDescription=Seat management daemon\n\n[Service]\nType=simple\nExecStart=/usr/bin/seatd -g video\nRestart=always\nRestartSec=1\n\n[Install]\nWantedBy=multi-user.target\n' > /etc/systemd/system/seatd.service
fi
systemctl enable seatd.service
# Hotspot: jede Adresse zeigt auf den Pi – Handys öffnen die Einrichtungsseite dann von selbst
mkdir -p /etc/NetworkManager/dnsmasq-shared.d
echo 'address=/#/10.42.0.1' > /etc/NetworkManager/dnsmasq-shared.d/signagecast.conf
# Protokoll nur im RAM (schont die Karte), Hardware-Watchdog startet einen hängenden Pi neu
mkdir -p /etc/systemd/journald.conf.d /etc/systemd/system.conf.d
printf '[Journal]\nStorage=volatile\nRuntimeMaxUse=32M\n' > /etc/systemd/journald.conf.d/signagecast.conf
printf '[Manager]\nRuntimeWatchdogSec=15\n' > /etc/systemd/system.conf.d/signagecast.conf
echo signagecast-player > /etc/hostname
CHROOT
rm -f "$A/root/etc/resolv.conf"
mv "$A/resolv.conf.orig" "$A/root/etc/resolv.conf" 2>/dev/null || true

echo "== Boot-Partition"
B=$A/root/boot/firmware
sed -i '1 s/$/ quiet loglevel=3 logo.nologo vt.global_cursor_default=0 consoleblank=0/' "$B/cmdline.txt"
printf '\n[all]\n# SignageCast Player\ndisable_splash=1\n' >> "$B/config.txt"
MARKE=SCPH-$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')
i=0
: > "$B/signagecast.json"
while [ $i -lt 32 ]; do                 # 32 Blöcke à 512 Byte, jeder mit eigener Nummer (prüft: Datei liegt am Stück)
  printf '%-511s\n' "$MARKE-$(printf %04d $i)" >> "$B/signagecast.json"
  i=$((i + 1))
done
# Paketliste für die SBOM (seit 0.30) – direkt aus der dpkg-Datenbank des Images
dpkg-query --admindir="$A/root/var/lib/dpkg" -W -f '${Package}\t${Version}\t${Architecture}\t${source:Package}\n' > "$A/pakete.tsv"
echo "   $(wc -l < "$A/pakete.tsv") Pakete im Image"
sync
umount -R "$A/root"
e2fsck -fy "${LOOP}p2" >/dev/null || true
zerofree "${LOOP}p2"                   # freie Blöcke mit Nullen füllen (gelöschte Paketlisten) – das Image packt viel kleiner
losetup -d "$LOOP"
LOOP=

echo "== Platzhalter suchen"
OFFSET=$(python3 - "$IMG" "$MARKE" <<'PY'
import sys
img, marke = sys.argv[1], sys.argv[2].encode()
f = open(img, "rb")
pos, rest, fund = 0, b"", []
while True:
    teil = f.read(64 << 20)
    if not teil:
        break
    daten = rest + teil
    i = daten.find(marke + b"-0000")
    while i >= 0:
        fund.append(pos - len(rest) + i)
        i = daten.find(marke + b"-0000", i + 1)
    rest = daten[-64:]
    pos += len(teil)
fund = sorted(set(fund))
assert len(fund) == 1, f"Platzhalter {len(fund)}-mal gefunden"
for n in range(32):
    f.seek(fund[0] + 512 * n)
    assert f.read(len(marke) + 5) == marke + b"-%04d" % n, f"Platzhalter nicht am Stück (Block {n})"
print(fund[0])
PY
)
echo "   Versatz $OFFSET"

echo "== Packen"
mkdir -p "$AUS"
N=signagecast-player-v$V.img.xz
GROESSE=$(stat -c %s "$IMG")
xz -T0 -6 -c "$IMG" > "$AUS/$N"
SB=signagecast-player-v$V.cdx.json
python3 "$HIER/../werkzeug/sbom.py" pi --version "$V" --dpkg "$A/pakete.tsv" --basis "$(basename "$URL")" > "$AUS/$SB"
python3 - "$AUS" "$N" "$V" "$GROESSE" "$OFFSET" "$MARKE" "$(basename "$URL")" "$SB" <<'PY'
import hashlib, json, os, sys, time
aus, n, v, groesse, offset, marke, basis, sb = sys.argv[1:]
h = hashlib.sha256()
with open(os.path.join(aus, n), "rb") as f:
    for teil in iter(lambda: f.read(1 << 20), b""):
        h.update(teil)
meta = {"art": "signagecast-player-image", "version": v, "datei": n, "sha256": h.hexdigest(),
        "xz_groesse": os.path.getsize(os.path.join(aus, n)), "groesse": int(groesse),
        "platzhalter": {"offset": int(offset), "laenge": 16384, "marke": marke}, "basis": basis,
        "erstellt": time.strftime("%Y-%m-%d"),
        # SBOM des Images (seit 0.30): ihre Prüfsumme steht hier, die .json wird signiert
        "sbom": {"datei": sb, "sha256": hashlib.sha256(open(os.path.join(aus, sb), "rb").read()).hexdigest()}}
json.dump(meta, open(os.path.join(aus, f"signagecast-player-v{v}.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
PY
