# SignageCast Player – Tailscale einbauen (seit 0.41), im chroot des Images (Pi: bauen.sh, PC: pc/einrichten.sh).
# Paket aus dem Archiv von Tailscale; dessen Signaturschlüssel ist per Prüfsumme festgeschrieben (Tailscale Inc.,
# Fingerabdruck 2596A99EAAB33821893C0A79458CA832957F5868) – ändert Tailscale ihn, bricht der Bau ab statt still zu
# vertrauen. Der Systemdienst bleibt gesperrt: der Agent startet tailscaled nur für Geräte an einem anderen Standort.
set -eu
. /etc/os-release
K=/usr/share/keyrings/tailscale-archive-keyring.gpg
python3 - "$VERSION_CODENAME" "$K" <<'PY'
import sys, urllib.request
with urllib.request.urlopen(f"https://pkgs.tailscale.com/stable/debian/{sys.argv[1]}.noarmor.gpg", timeout=60) as a:
    roh = a.read(100_000)
with open(sys.argv[2], "wb") as f:
    f.write(roh)
PY
echo "3e03dacf222698c60b8e2f990b809ca1b3e104de127767864284e6c228f1fb39  $K" | sha256sum -c -
echo "deb [signed-by=$K] https://pkgs.tailscale.com/stable/debian $VERSION_CODENAME main" > /etc/apt/sources.list.d/tailscale.list
apt-get update -q
apt-get install -y -q --no-install-recommends tailscale
systemctl disable tailscaled.service 2>/dev/null || true
systemctl mask tailscaled.service
command -v tailscale >/dev/null && command -v tailscaled >/dev/null
