#!/bin/sh
# SignageCast PC-Player: beschreibbaren Ort für signagecast.json und Agent-Updates bereitstellen (vor dem Agenten).
# Vom USB-Stick gestartet: die FAT-Partition „SCDATEN“ auf demselben Datenträger wie das Startmedium. Von CD, Ventoy
# oder ohne diese Partition: ein kleiner RAM-Ordner – dann gilt alles nur bis zum Neustart.
# Steht dort noch keine gültige Gerätedatei, kommt die aus dem ISO (/signagecast.json, von der Verwaltung beschrieben).
D=/run/signagecast-medium
ISO=/run/live/medium/signagecast.json
mountpoint -q "$D" && exit 0
mkdir -p "$D"
quelle=$(findmnt -no SOURCE /run/live/medium 2>/dev/null | head -1)
platte=$(lsblk -no PKNAME "$quelle" 2>/dev/null | head -1)
[ -n "$platte" ] || platte=$(basename "${quelle:-x}")
teil=$(lsblk -lnpo NAME,LABEL "/dev/$platte" 2>/dev/null | awk '$2 == "SCDATEN" { print $1; exit }')
if [ -n "$teil" ]; then
  fsck.vfat -a "$teil" >/dev/null 2>&1 || true        # nach einem Stromausfall beim Schreiben
  if mount -t vfat -o rw,noatime,flush,fmask=0177,dmask=0077 "$teil" "$D"; then
    echo "Datenpartition $teil"
  else
    teil=
  fi
fi
if [ -z "$teil" ]; then
  mount -t tmpfs -o size=16m,mode=0700 tmpfs "$D"
  echo "Keine beschreibbare Datenpartition (CD/Ventoy?) – Kopplung und WLAN gelten bis zum Neustart"
fi
gueltig() {
  python3 -c 'import json, sys; k = json.load(open(sys.argv[1])); sys.exit(0 if k.get("art") == "signagecast-player" else 1)' "$1" 2>/dev/null
}
if ! gueltig "$D/signagecast.json" && gueltig "$ISO"; then
  cp "$ISO" "$D/signagecast.json.neu" && sync && mv "$D/signagecast.json.neu" "$D/signagecast.json" && sync
  echo "Gerätedatei aus dem Image übernommen"
fi
exit 0
