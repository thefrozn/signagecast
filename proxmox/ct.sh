#!/usr/bin/env bash
# SignageCast – create a ready-to-use LXC container on a Proxmox VE host (run as root on the host):
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/tschmidt82/signagecast/main/proxmox/ct.sh)"
#
# Asks a few questions (Enter = suggested value), creates an unprivileged Debian 13 container with the Intel GPU
# (/dev/dri/renderD128) passed through and installs SignageCast inside it.
# Without questions: SIGNAGECAST_YES=1 plus optional CTID, CT_HOSTNAME, CORES, RAM, DISK, STORAGE, BRIDGE, IP (dhcp or
# 192.168.1.50/24), GW as environment variables.
set -euo pipefail
REPO=tschmidt82/signagecast
INSTALL_URL=${SIGNAGECAST_INSTALL_URL:-https://raw.githubusercontent.com/$REPO/main/install.sh}

rot() { printf '\033[31m%s\033[0m\n' "$*"; }
gruen() { printf '\033[32m%s\033[0m\n' "$*"; }
frage() {   # frage VAR "Text" "Vorschlag"
  local var=$1 text=$2 vorschlag=$3 antwort
  if [ -n "${SIGNAGECAST_YES:-}" ]; then printf -v "$var" '%s' "${!var:-$vorschlag}"; return; fi
  read -r -p "$text [${!var:-$vorschlag}]: " antwort </dev/tty || true
  printf -v "$var" '%s' "${antwort:-${!var:-$vorschlag}}"
}

echo "SignageCast – Proxmox LXC"
command -v pct >/dev/null || { rot "This must run on a Proxmox VE host (pct not found)."; exit 1; }
[ "$(id -u)" = 0 ] || { rot "Please run as root."; exit 1; }
if [ ! -e /dev/dri/renderD128 ]; then
  rot "No GPU found at /dev/dri/renderD128 – SignageCast needs an Intel GPU (Quick Sync/VAAPI) for H.265 encoding."
  [ -n "${SIGNAGECAST_YES:-}" ] && exit 1
  read -r -p "Continue anyway? [y/N]: " w </dev/tty; [ "${w,,}" = y ] || exit 1
fi

frage CTID "Container ID" "$(pvesh get /cluster/nextid)"
frage CT_HOSTNAME "Hostname" "signagecast"
frage CORES "CPU cores" "4"
frage RAM "RAM in MB (about 1 GB per TV)" "3072"
frage DISK "Disk in GB" "10"
frage STORAGE "Storage for the container" "$(pvesm status -content rootdir | awk 'NR==2 {print $1}')"
frage BRIDGE "Network bridge" "vmbr0"
frage IP "IP address (dhcp or e.g. 192.168.1.50/24)" "dhcp"
GW=${GW:-}
if [ "$IP" != dhcp ]; then frage GW "Gateway" "$(ip route | awk '/default/ {print $3; exit}')"; fi

if pct status "$CTID" >/dev/null 2>&1; then rot "Container $CTID already exists."; exit 1; fi

echo "== Debian 13 template"
TSTORE=$(pvesm status -content vztmpl | awk 'NR==2 {print $1}')
pveam update >/dev/null
ARCH=$(dpkg --print-architecture)          # amd64 – nicht die arm64-Vorlage nehmen
VORLAGE=$(pveam available --section system | awk -v a="_${ARCH}.tar" '/debian-13-standard/ && index($2, a) {print $2}' | sort -V | tail -1)
[ -n "$VORLAGE" ] || { rot "No Debian 13 template available."; exit 1; }
pveam list "$TSTORE" | grep -q "$VORLAGE" || pveam download "$TSTORE" "$VORLAGE"

echo "== Creating container $CTID"
NETZ="name=eth0,bridge=$BRIDGE,ip=$IP"
[ "$IP" != dhcp ] && [ -n "$GW" ] && NETZ="$NETZ,gw=$GW"
pct create "$CTID" "$TSTORE:vztmpl/$VORLAGE" --hostname "$CT_HOSTNAME" --cores "$CORES" --memory "$RAM" --swap 512 \
  --rootfs "$STORAGE:$DISK" --net0 "$NETZ" --unprivileged 1 --features nesting=1 --onboot 1 \
  --dev0 /dev/dri/renderD128,mode=0666 --description "SignageCast – https://github.com/$REPO" >/dev/null
pct start "$CTID"

echo "== Waiting for network"
for _ in $(seq 1 60); do pct exec "$CTID" -- getent hosts deb.debian.org >/dev/null 2>&1 && break; sleep 2; done

echo "== Installing SignageCast inside the container (takes a few minutes)"
pct exec "$CTID" -- bash -c "export LC_ALL=C.UTF-8; apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq curl ca-certificates >/dev/null && \
  curl -fsSL '$INSTALL_URL' | SIGNAGECAST_TARBALL='${SIGNAGECAST_TARBALL:-}' SIGNAGECAST_VERSION='${SIGNAGECAST_VERSION:-}' sh"

ADR=$(pct exec "$CTID" -- hostname -I | awk '{print $1}')
echo
gruen "SignageCast is ready in container $CTID."
echo "  Admin:  https://$ADR:9090   (user tvadmin, initial password tvadmin – please change it)"
echo "  TV:     http://$ADR:8888/tv  (open in the TV browser)"
echo "  Next:   in the admin page open “Connection” and follow the Home Assistant guide."
