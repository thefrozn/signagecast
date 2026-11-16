#!/bin/sh
# SignageCast – Installations-ISO für einen eigenen Rechner bauen (seit 0.52, „Bare Metal“). Läuft in einem Container
# debian:trixie (amd64, als root); GitHub Actions startet ihn beim Release (.github/workflows/player.yml).
#
# Grundlage ist das offizielle Debian-13-netinst-ISO (Signatur des Debian-CD-Schlüssels und SHA-512 geprüft). Hinzu
# kommen nur: ein Startmenü (Deutsch/English), Antworten für den Installer (iso/preseed.cfg), die Frage „Bild per
# HDMI?“ und SignageCast selbst (dieser Stand des Repos). Partitionieren, Bootloader, Secure Boot und Treiber macht
# der Debian-Installer; SignageCast installiert sich beim ersten Start (braucht Internet, wie der Installer selbst).
#
#   sh iso/bauen.sh <ausgabeordner> <version>
set -eu
AUS=$(realpath -m "$1")
V=$2
HIER=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HIER/.." && pwd)
A=$(mktemp -d)
trap 'rm -rf "$A"' EXIT
QUELLE=https://cdimage.debian.org/debian-cd/current/amd64/iso-cd
# „Debian CD signing key“ (https://www.debian.org/CD/verify)
CD_SCHLUESSEL=DF9B9C49EAA9298432589D76DA87E80D6294BE9B

echo "== Werkzeuge"
apt-get update -q >/dev/null
DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends xorriso gpg gpgv curl ca-certificates python3 >/dev/null

echo "== Debian-netinst laden und prüfen"
curl -fsSL -o "$A/SHA512SUMS" "$QUELLE/SHA512SUMS"
curl -fsSL -o "$A/SHA512SUMS.sign" "$QUELLE/SHA512SUMS.sign"
curl -fsSL -o "$A/schluessel.asc" "https://keyring.debian.org/pks/lookup?op=get&search=0x$CD_SCHLUESSEL"
# ohne gpg-agent: Schlüssel nur entpacken und anzeigen, prüfen mit gpgv – und nur eine Signatur genau dieses
# Schlüssels gilt (VALIDSIG mit seinem Fingerabdruck)
export GNUPGHOME="$A/gpg"
mkdir -m 700 "$GNUPGHOME"
gpg --dearmor < "$A/schluessel.asc" > "$A/cd.gpg"
gpg --show-keys --with-colons "$A/cd.gpg" | grep -q "^fpr:::::::::$CD_SCHLUESSEL:" || { echo "Debian-CD-Schlüssel fehlt"; exit 1; }
gpgv --status-fd 1 --keyring "$A/cd.gpg" "$A/SHA512SUMS.sign" "$A/SHA512SUMS" | grep -q "VALIDSIG $CD_SCHLUESSEL " \
  || { echo "Signatur von SHA512SUMS ungültig"; exit 1; }
echo "   Signatur von SHA512SUMS gültig (Debian CD signing key)"
N=$(grep -o 'debian-13[0-9.]*-amd64-netinst\.iso' "$A/SHA512SUMS" | head -1)
[ -n "$N" ] || { echo "kein Debian-13-netinst in SHA512SUMS"; exit 1; }
echo "   $N"
curl -fsSL -o "$A/$N" "$QUELLE/$N"
(cd "$A" && grep " $N\$" SHA512SUMS | sha512sum -c -)

echo "== SignageCast und Startmenü"
mkdir -p "$A/neu/signagecast" "$A/neu/boot/grub" "$A/neu/isolinux"
tar -czf "$A/neu/signagecast/signagecast.tar.gz" -C "$REPO" --exclude=.git --exclude=__pycache__ --exclude=./out --exclude=./tests .
cp "$HIER/preseed.cfg" "$HIER/vorlagen" "$HIER/spaet.sh" "$A/neu/signagecast/"
ARGS="auto=true priority=critical preseed/file=/cdrom/signagecast/preseed.cfg"
DE="locale=de_DE.UTF-8 keyboard-configuration/xkb-keymap=de"
EN="locale=en_US.UTF-8 keyboard-configuration/xkb-keymap=us"
# UEFI (GRUB): Kopf des Debian-Menüs (Schrift, Grafik, Thema) behalten, Einträge durch unsere ersetzen
xorriso -osirrox on -indev "$A/$N" -extract /boot/grub/grub.cfg "$A/grub.orig" -extract /md5sum.txt "$A/md5sum.txt" >/dev/null 2>&1
chmod u+w "$A/grub.orig" "$A/md5sum.txt"
sed '/^menuentry /,$d' "$A/grub.orig" > "$A/neu/boot/grub/grub.cfg"
cat >> "$A/neu/boot/grub/grub.cfg" <<GRUB
menuentry 'SignageCast installieren (Deutsch)' {
    set background_color=black
    linux    /install.amd/vmlinuz vga=788 $ARGS $DE --- quiet
    initrd   /install.amd/gtk/initrd.gz
}
menuentry 'Install SignageCast (English)' {
    set background_color=black
    linux    /install.amd/vmlinuz vga=788 $ARGS $EN --- quiet
    initrd   /install.amd/gtk/initrd.gz
}
menuentry 'Rescue mode / Rettungsmodus (Debian)' {
    set background_color=black
    linux    /install.amd/vmlinuz vga=788 rescue/enable=true --- quiet
    initrd   /install.amd/gtk/initrd.gz
}
GRUB
# BIOS (isolinux): eigenes Hauptmenü – offiziell unterstützt ist UEFI, alte Rechner sollen aber nicht in einem
# fremden Menü landen
cat > "$A/neu/isolinux/menu.cfg" <<ISO
menu hshift 4
menu width 70
menu title SignageCast $V
include stdmenu.cfg
label sc-de
	menu label SignageCast installieren (^Deutsch)
	menu default
	kernel /install.amd/vmlinuz
	append vga=788 initrd=/install.amd/gtk/initrd.gz $ARGS $DE --- quiet
label sc-en
	menu label Install SignageCast (^English)
	kernel /install.amd/vmlinuz
	append vga=788 initrd=/install.amd/gtk/initrd.gz $ARGS $EN --- quiet
label rescue
	menu label ^Rescue mode / Rettungsmodus (Debian)
	kernel /install.amd/vmlinuz
	append vga=788 initrd=/install.amd/gtk/initrd.gz rescue/enable=true --- quiet
ISO
# Prüfsummenliste des ISO (für „CD prüfen“ im Installer) für die geänderten Dateien neu
python3 - "$A/md5sum.txt" "$A/neu" <<'PY'
import hashlib, os, sys
liste, neu = sys.argv[1], sys.argv[2]
zeilen = {}
for z in open(liste):
    if "  " in z:
        s, p = z.rstrip("\n").split("  ", 1)
        zeilen[p] = s
for ordner, _, namen in os.walk(neu):
    for n in namen:
        pfad = os.path.join(ordner, n)
        zeilen["./" + os.path.relpath(pfad, neu)] = hashlib.md5(open(pfad, "rb").read()).hexdigest()
open(liste, "w").write("".join(f"{s}  {p}\n" for p, s in sorted(zeilen.items())))
PY
cp "$A/md5sum.txt" "$A/neu/md5sum.txt"

echo "== ISO schreiben"
mkdir -p "$AUS"
D=signagecast-server-v$V.iso
# Boot-Aufbau des Debian-ISO (El Torito BIOS/UEFI, Hybrid-MBR/GPT für USB-Sticks) unverändert übernehmen
xorriso -indev "$A/$N" -outdev "$AUS/$D" -boot_image any replay \
  -map "$A/neu/signagecast" /signagecast -map "$A/neu/boot/grub/grub.cfg" /boot/grub/grub.cfg \
  -map "$A/neu/isolinux/menu.cfg" /isolinux/menu.cfg -map "$A/neu/md5sum.txt" /md5sum.txt >/dev/null 2>&1
python3 - "$AUS" "$D" "$V" "$N" <<'PY'
import hashlib, json, os, sys, time
aus, d, v, basis = sys.argv[1:]
h = hashlib.sha256()
with open(os.path.join(aus, d), "rb") as f:
    for teil in iter(lambda: f.read(1 << 20), b""):
        h.update(teil)
meta = {"art": "signagecast-server-iso", "version": v, "datei": d, "sha256": h.hexdigest(),
        "groesse": os.path.getsize(os.path.join(aus, d)), "basis": basis, "erstellt": time.strftime("%Y-%m-%d")}
json.dump(meta, open(os.path.join(aus, f"signagecast-server-v{v}.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
PY
