#!/bin/sh
# SignageCast PC-Player – Image bauen (seit 0.36, experimentell). Läuft in einem Container debian:trixie (amd64, als
# root, --privileged: mmdebstrap braucht mount im chroot); GitHub Actions startet ihn (.github/workflows/player.yml).
#
# Ergebnis ist EINE Datei für alles: ein ISO (CD, Ventoy, VM), das man auch 1:1 auf einen USB-Stick schreiben kann
# (balenaEtcher, Raspberry Pi Imager, Rufus im DD-Modus). Aufbau:
#   - ISO9660 mit /live/vmlinuz, /live/initrd.img, /live/filesystem.squashfs (Debian 13 + Player, live-boot) und dem
#     Platzhalter /signagecast.json (16 KiB am Stück – die Verwaltung schreibt die Gerätedatei hinein, wie beim Pi)
#   - Partition 2: EFI-Systempartition mit shim, GRUB und Kernel von Debian (alle signiert) – Secure Boot darf an bleiben
#   - Partition 3: kleine FAT-Partition „SCDATEN“: dort merkt sich der Player Kopplung, WLAN und Agent-Updates
#     (auf CD/Ventoy fehlt sie – dann gilt das bis zum Neustart; die Einstellungen kommen ohnehin vom Server)
# Nur UEFI (kein altes BIOS). Das System läuft schreibgeschützt (squashfs + RAM-Schicht): Stromausfälle schaden nicht.
#
#   sh player/pc/bauen.sh <ausgabeordner> <version>
set -eu
AUS=$(realpath -m "$1")
V=$2
HIER=$(cd "$(dirname "$0")" && pwd)
PLAYER=$(cd "$HIER/.." && pwd)
A=$(mktemp -d)
trap 'rm -rf "$A"' EXIT

echo "== Werkzeuge"
apt-get update -q
DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends mmdebstrap squashfs-tools xorriso mtools \
  dosfstools shim-signed grub-efi-amd64-signed python3 xz-utils ca-certificates gpg >/dev/null

echo "== Debian 13 mit Player"
# Pakete: Kernel + live-boot (startet aus dem squashfs), Netz (NetworkManager, auch Hotspot), Anzeige wie beim Pi
# (mpv für Stream und Hinweise, cage + Chromium für den Direktmodus), Grafik- und Video-Treiber (VAAPI), Firmware für
# gängige WLAN-Karten und Grafik, Mikrocode. Kein Desktop, kein SSH.
PAKETE="linux-image-amd64 live-boot systemd-sysv systemd-timesyncd udev dbus kmod iproute2 iputils-ping procps less nano
  tzdata ca-certificates python3 dosfstools util-linux pciutils usbutils zstd
  network-manager dnsmasq-base wpasupplicant iw rfkill wireless-regdb
  mpv qrencode cage seatd grim wlr-randr alsa-utils fonts-dejavu-core fonts-noto-color-emoji chromium
  libgl1-mesa-dri libegl1 va-driver-all intel-media-va-driver mesa-va-drivers
  firmware-linux-free firmware-misc-nonfree firmware-intel-graphics firmware-amd-graphics firmware-iwlwifi
  firmware-realtek firmware-atheros firmware-brcm80211 firmware-mediatek firmware-intel-sound firmware-sof-signed
  intel-microcode amd64-microcode"
mmdebstrap --variant=minbase --architectures=amd64 --components="main contrib non-free non-free-firmware" \
  --include="$(echo $PAKETE | tr ' ' ',')" \
  --customize-hook='mkdir -p "$1/usr/lib/signagecast-player"' \
  --customize-hook="copy-in $PLAYER/agent.py $PLAYER/start.sh $HIER/medium.sh /usr/lib/signagecast-player/" \
  --customize-hook="copy-in $PLAYER/signagecast-player.service /etc/systemd/system/" \
  --customize-hook="chroot \"\$1\" /bin/sh -eu < $HIER/einrichten.sh" \
  trixie "$A/root" \
  "deb http://deb.debian.org/debian trixie main contrib non-free non-free-firmware" \
  "deb http://deb.debian.org/debian trixie-updates main contrib non-free non-free-firmware" \
  "deb http://security.debian.org/debian-security trixie-security main contrib non-free non-free-firmware"

# Paketliste für die SBOM – direkt aus der dpkg-Datenbank
dpkg-query --admindir="$A/root/var/lib/dpkg" -W -f '${Package}\t${Version}\t${Architecture}\t${source:Package}\n' > "$A/pakete.tsv"
echo "   $(wc -l < "$A/pakete.tsv") Pakete im Image"

echo "== ISO-Inhalt"
I=$A/iso
mkdir -p "$I/live" "$I/boot/grub" "$I/.disk"
cp "$(ls "$A"/root/boot/vmlinuz-* | sort -V | tail -1)" "$I/live/vmlinuz"
cp "$(ls "$A"/root/boot/initrd.img-* | sort -V | tail -1)" "$I/live/initrd.img"
rm -rf "$A/root/boot"/* "$A/root/var/cache/apt"/*.bin "$A/root/var/lib/apt/lists"/* "$A/root/tmp"/*
# zstd: schnell zu entpacken (der Player liest beim Start ~1 GB), kaum größer als xz
mksquashfs "$A/root" "$I/live/filesystem.squashfs" -comp zstd -Xcompression-level 19 -b 1M -noappend -no-progress
echo "SignageCast Player $V (PC, Debian 13 amd64)" > "$I/.disk/info"
# GRUB (signiert, sucht /.disk/info und liest dann /boot/grub/grub.cfg). Kein Menü – Esc beim Start zeigt es.
cat > "$I/boot/grub/grub.cfg" <<'GRUB'
set timeout=1
set timeout_style=hidden
menuentry "SignageCast Player" {
  linux /live/vmlinuz boot=live quiet loglevel=3 vt.global_cursor_default=0 consoleblank=0 net.ifnames=0 noeject
  initrd /live/initrd.img
}
menuentry "SignageCast Player (Startmeldungen)" {
  linux /live/vmlinuz boot=live loglevel=6 net.ifnames=0 noeject systemd.show_status=1
  initrd /live/initrd.img
}
GRUB
MARKE=SCPH-$(od -An -N16 -tx1 /dev/urandom | tr -d ' \n')
i=0
: > "$I/signagecast.json"
while [ $i -lt 32 ]; do                 # 32 Blöcke à 512 Byte, jeder mit eigener Nummer (prüft: Datei liegt am Stück)
  printf '%-511s\n' "$MARKE-$(printf %04d $i)" >> "$I/signagecast.json"
  i=$((i + 1))
done

echo "== EFI- und Datenpartition"
mkfs.vfat -n SCEFI -C "$A/efi.img" 8192 >/dev/null
mmd -i "$A/efi.img" ::/EFI ::/EFI/boot
mcopy -i "$A/efi.img" /usr/lib/shim/shimx64.efi.signed ::/EFI/boot/bootx64.efi
mcopy -i "$A/efi.img" /usr/lib/shim/mmx64.efi.signed ::/EFI/boot/mmx64.efi
mcopy -i "$A/efi.img" /usr/lib/grub/x86_64-efi-signed/gcdx64.efi.signed ::/EFI/boot/grubx64.efi
mkfs.vfat -n SCDATEN -C "$A/daten.img" 32768 >/dev/null
printf 'SignageCast Player: Gerätedatei, Kopplung, WLAN und Agent-Updates dieses Players.\r\nBitte nicht löschen.\r\n' > "$A/LIESMICH.txt"
mcopy -i "$A/daten.img" "$A/LIESMICH.txt" ::/LIESMICH.txt

echo "== ISO bauen"
IMG=$A/signagecast-pc.iso
xorriso -as mkisofs -o "$IMG" -iso-level 3 -r -J -joliet-long -V SIGNAGECAST \
  -partition_offset 16 -appended_part_as_gpt \
  -append_partition 2 0xef "$A/efi.img" -append_partition 3 0x0c "$A/daten.img" \
  -e --interval:appended_partition_2:all:: -no-emul-boot \
  "$I" 2>&1 | grep -v '^xorriso : UPDATE' || true
[ -s "$IMG" ]

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
N=signagecast-pc-v$V.iso.xz
GROESSE=$(stat -c %s "$IMG")
xz -T0 -6 -c "$IMG" > "$AUS/$N"
SB=signagecast-pc-v$V.cdx.json
python3 "$PLAYER/../werkzeug/sbom.py" pc --version "$V" --dpkg "$A/pakete.tsv" --basis "Debian 13 (trixie) amd64" > "$AUS/$SB"
python3 - "$AUS" "$N" "$V" "$GROESSE" "$OFFSET" "$MARKE" "$SB" <<'PY'
import hashlib, json, os, sys, time
aus, n, v, groesse, offset, marke, sb = sys.argv[1:]
h = hashlib.sha256()
with open(os.path.join(aus, n), "rb") as f:
    for teil in iter(lambda: f.read(1 << 20), b""):
        h.update(teil)
meta = {"art": "signagecast-pc-image", "version": v, "datei": n, "sha256": h.hexdigest(),
        "xz_groesse": os.path.getsize(os.path.join(aus, n)), "groesse": int(groesse),
        "platzhalter": {"offset": int(offset), "laenge": 16384, "marke": marke}, "basis": "Debian 13 (trixie) amd64",
        "erstellt": time.strftime("%Y-%m-%d"),
        "sbom": {"datei": sb, "sha256": hashlib.sha256(open(os.path.join(aus, sb), "rb").read()).hexdigest()}}
json.dump(meta, open(os.path.join(aus, f"signagecast-pc-v{v}.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
PY
