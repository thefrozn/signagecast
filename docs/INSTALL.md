# SignageCast – installation

[← README](../README.md) · [live demo](https://thefrozn.github.io/signagecast/?sprache=en) · [hardware](HARDWARE.md) · [manual](MANUAL.md) · [how it works](HOW-IT-WORKS.md)

Choose one way. All of them need an **x86 computer** (Intel or AMD CPU); for 4K a CPU with **Intel graphics**
(Quick Sync) – see [hardware](HARDWARE.md). The TV only opens one address in its browser.

| Way | For | Guide |
|---|---|---|
| **Proxmox VE** | a Proxmox server – one command creates a ready container | [below](#proxmox-ve) |
| **Debian 13** | an existing LXC, VM or real computer | [below](#debian-13) |
| **Docker / Podman** | any Linux host | [below](#docker--podman) |
| **Windows** | a Windows 10/11 PC – Docker Desktop with one PowerShell command, or WSL (Full HD, no Quick Sync) – *not tested on real Windows yet* | [Windows guide](install/WINDOWS.md) |
| **QNAP** | QNAP NAS with Intel/AMD CPU, Container Station (no command line) | [QNAP guide](install/QNAP.md) |
| **Synology** | Synology NAS with Intel/AMD CPU, Container Manager (no command line) | [Synology guide](install/SYNOLOGY.md) |

**At the TV**, besides its browser: a **Raspberry Pi as player** (from 0.23) – image from the admin, see [PLAYER.md](PLAYER.md).

## Proxmox VE

Run on the Proxmox host shell, answer the questions (Enter = suggestion):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/proxmox/ct.sh)"
```

It creates a Debian 13 container, passes the Intel GPU through and installs SignageCast. At the end it shows the
admin address and a **random initial password** for the user `tvadmin` (since 0.62; before it was `tvadmin`). Read it
again later on the Proxmox host: `pct exec <ID> -- cat /root/signagecast-startpasswort` – the file disappears by itself
as soon as you set your own password. Your own password right away: `SC_PASSWORT='…' bash -c "$(curl …)"`.

## Debian 13

LXC, VM or a real computer with `/dev/dri/renderD128` – as root:

```bash
curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh
```

Running the same command again updates SignageCast; settings and data are kept. If port 8888 is taken, choose another
stream port: `curl -fsSL …/install.sh | SC_STREAM_PORT=8899 sh` (it is remembered for updates).

**Manual:** download a release, unpack it and run `sh installieren.sh`.

## Own computer (installation ISO)

Since 0.52 for a computer of its own (mini PC, old laptop) without Proxmox: **`signagecast-server-vX.Y.Z.iso`** from the
[latest release](https://github.com/thefrozn/signagecast/releases/latest). Write it to a USB stick (balenaEtcher,
Raspberry Pi Imager, Rufus in DD mode, Ventoy) and start the computer from it – **UEFI only**, Secure Boot may stay on.

1. Choose **SignageCast installieren (Deutsch)** or **Install SignageCast (English)**.
2. Only if there is no cable: Wi-Fi name and key.
3. A **password for the user `tvadmin`** – that is the admin login later.
4. **Confirm that the disk is erased** – the whole disk is used.
5. **Show the picture on this computer via HDMI too?** – “Yes” if a TV or monitor is connected to this computer.
6. After the restart SignageCast installs itself (a few minutes, needs internet). The screen then shows the admin
   address: **https://&lt;IP&gt;:9090**, user `tvadmin`.

It is the official Debian 13 netinst (signature checked when the ISO is built) with preset answers – partitioning,
boot loader, drivers and Secure Boot are done by the Debian installer. No SSH server; the admin's terminal (Cockpit)
is the way in. Security updates install themselves.

**Picture via HDMI:** the computer shows a channel itself (Chromium in the kiosk frame cage, like a player in direct
mode). Until the setup assistant is finished, the screen shows the console with the admin address. Switch it on or
off later under *Displays → + New device → This computer via HDMI* or by removing that device. On an existing
Debian installation (not a container): `SC_HDMI=1 sh installieren.sh`.

Tested in a virtual machine (UEFI, Secure Boot, German and English); **not yet tested on a real mini PC** –
hardware video decoding and sound via HDMI are unconfirmed. Feedback welcome.

## Docker / Podman

One line:

```bash
docker run -d --name signagecast --restart unless-stopped --device /dev/dri \
  -p 8888:8888 -p 19090:19090 -v signagecast:/data \
  -e TZ=Europe/Berlin -e SC_HOST_IP=192.168.1.20 ghcr.io/thefrozn/signagecast:latest
```

or with [`compose.yaml`](../compose.yaml): `docker compose up -d`. Podman: the same command with `podman`.

- `--device /dev/dri` passes the graphics through; leave it out on systems without Intel graphics (software fallback).
  **To try SignageCast out, Docker without `/dev/dri` is enough.**
  Rootless Podman additionally needs `--group-add keep-groups`.
- **Rootless Podman: use host networking.** Its default port forwarder can hide the client address – every request
  then seems to come from inside the container, and camera streams (only readable inside the container) could be
  read from the network. With `--network host` no `-p` is needed:

  ```bash
  podman run -d --name signagecast --restart unless-stopped --network host --device /dev/dri --group-add keep-groups \
    -v signagecast:/data -e TZ=Europe/Berlin -e SC_HOST_IP=192.168.1.20 ghcr.io/thefrozn/signagecast:latest
  ```
  The ports are then 8888 (TVs), 19090 (admin) and 8890 (webhook, panel, Pi players) directly on the host.
- **Admin:** http://&lt;host&gt;:**19090** – the initial password is printed in the log: `docker logs signagecast`
  (line “Startpasswort der Verwaltung / initial admin password”, or set your own with `-e SC_PASSWORT=…`). Change it under **Settings → Access**.
  No Cockpit inside the container.
- `SC_HOST_IP` = the IP of the Docker host; the Home Assistant guide in the admin shows it (HA sees the host's IP).
- All settings and data are in the volume `/data`. **Update:** `docker pull ghcr.io/thefrozn/signagecast:latest`, then
  recreate the container (`docker compose up -d`, or `docker rm -f signagecast` and the `docker run` line again).
- The image is built for `linux/amd64` only – ARM devices (Raspberry Pi, ARM NAS) are not supported.

## Ports, login and Cockpit per installation type

| Installation | Admin | TV stream | Initial login |
|---|---|---|---|
| Proxmox LXC (`ct.sh`) or Debian **container** | **https://&lt;IP&gt;:9090** (Cockpit) | `http://<IP>:8888/<tv>` | user `tvadmin` with a **random password** shown at the end (since 0.62), readable in `/root/signagecast-startpasswort` until you change it |
| Debian **VM / real computer** (`install.sh`, “native”) | **https://&lt;IP&gt;:9090** (Cockpit) | `http://<IP>:8888/<tv>`, other port with `SC_STREAM_PORT` | user `tvadmin` with a **random password** shown at the end (file as above) – or your own Cockpit user |
| **Installation ISO** | **https://&lt;IP&gt;:9090** (Cockpit) | `http://<IP>:8888/<tv>` | user `tvadmin` with the password you chose in the installer |
| **Docker / Podman / NAS** | **http://&lt;host&gt;:19090** (own login, no Cockpit) | `http://<host>:8888/<tv>` | random password in the container log (or `SC_PASSWORT`) |

- **Cockpit already installed?** On a native installation SignageCast integrates into your existing Cockpit: it only
  adds the menu entry **“SignageCast”** (files in `/usr/share/cockpit/signagecast`) – no second port, no second login,
  your Cockpit settings stay untouched, and the system pages (services, logs, updates) remain available.
  Note: Cockpit cannot hide an extension per user – everyone who may log in to this Cockpit can also configure SignageCast.
- **Why 19090 for Docker/Podman?** Many servers already run Cockpit on 9090. With host networking (recommended for
  rootless Podman) both would collide. Change it with `SC_VERWALTUNG_PORT`, the stream port with `SC_STREAM_PORT`.
- **Why a random password?** `tvadmin` is a Linux account that can log in to Cockpit (with a terminal). A known
  default password would be a risk – since 0.62 also in containers. `SC_PASSWORT=…` sets your own (at least 8 characters).
- **Webhook messages** (optional, from v0.16): port **8890** (`SC_WEBHOOK_PORT`; Docker: add `-p 8890:8890`), only
  answers with a secret key created in the admin – see the [manual](MANUAL.md). The same port serves the announcement
  panel and the **Raspberry Pi players** (signed requests per device).
- The installer checks whether the stream port is free and stops with a hint if another program uses it.

## First steps

1. Open the admin (see the table above; accept the certificate warning on port 9090) and log in. Then change the
   initial password (Cockpit: top right → Accounts → tvadmin → Set password; Docker/NAS: **Settings → Access**).
2. On a new installation a short **assistant** asks for language, location and (optionally) Home Assistant and shows
   the TV address. Later: **Settings → Home Assistant** – enter the address and follow the guide shown there. Home
   Assistant trusts the container via `trusted_networks` – no password or token is stored.
3. **Settings → General**: weather comes from MET Norway – worldwide (or choose a Home Assistant weather entity).
   Official **severe weather warnings** come from the DWD and exist **for Germany only**.
   **Content → Layouts**: adapt the standard layout or start from a template.
4. On the TV open **http://&lt;IP&gt;:8888/tv** in the browser and set it as start page.
5. Optional: **Radio**, **Clips**, more **TVs**, schedules – see the [manual](MANUAL.md).

## Forgot the password? (reset)

| Installation | Reset |
|---|---|
| **Proxmox LXC** | on the Proxmox host: `pct exec <ID> -- passwd tvadmin` |
| **Debian / installation ISO** | as root on the computer (console or SSH): `passwd tvadmin` – on the ISO log in at the console as `tvadmin` and run `sudo passwd tvadmin`; if that password is lost too, boot the Debian rescue mode from the installation stick |
| **Docker / Podman** | `docker exec signagecast rm /data/config/verwaltung.json && docker restart signagecast` – a new random initial password is then in `docker logs signagecast` (or start with `-e SC_PASSWORT=…` before the restart). Podman: the same with `podman` |
| **QNAP / Synology** | Container Station / Container Manager → container **signagecast** → **Terminal** (or *Execute command*): `rm /data/config/verwaltung.json`, then restart the container and read the new password in its **log** |
| **Windows (Docker Desktop)** | PowerShell: `docker exec signagecast rm /data/config/verwaltung.json; docker restart signagecast; docker logs signagecast` |
| **Windows (WSL)** | PowerShell: `wsl -d Debian -u root passwd tvadmin` |

Settings, layouts and data are not touched by a reset.

## What the installation changes on the system

`install.sh` / `installieren.sh` (Debian, Proxmox container, installation ISO) – as root:

- **Package sources:** in `/etc/apt/sources.list.d/debian.sources` the components `contrib non-free non-free-firmware`
  are added (for the Intel video driver).
- **Debian packages** (`--no-install-recommends`): xvfb, chromium, ffmpeg, vainfo, intel-media-va-driver-non-free,
  libmfx-gen1.2, mesa-va-drivers, pulseaudio, pulseaudio-utils, fonts (roboto, dejavu, open-sans, lato, montserrat,
  ubuntu, cantarell, comic-neue, firacode, noto-core, noto-color-emoji), python3, python3-pyzipper, python3-smbc, curl,
  ca-certificates, openssl, procps, minisign, poppler-utils, cockpit-ws, cockpit-system, cockpit-bridge,
  cracklib-runtime. With HDMI (`SC_HDMI=1`, ISO): also cage and seatd.
- **MediaMTX** (stream server) from its GitHub release, checksum verified, to `/opt/mediamtx`.
- **Users:** `signagecast` (system user without login, runs all services) and `tvadmin` (admin login for Cockpit, in
  the group `systemd-journal` to read the logs; random initial password, see above).
- **Folders:** program `/opt/signagecast` (previous version `/opt/signagecast.vorher` for “back to the previous
  version”), settings `/etc/signagecast` (700), data `/var/lib/signagecast` (750), update backups
  `/var/lib/signagecast-aktualisierung` (root only), Cockpit extension `/usr/share/cockpit/signagecast`, command
  `/usr/local/bin/signagecast-mcp` (MCP for AI assistants), initial password `/root/signagecast-startpasswort` (until changed).
- **systemd units** in `/etc/systemd/system`: `signagecast.service` (data service, only 127.0.0.1:8080),
  `signagecast-mediamtx.service` (stream, starts the render chain on demand), `signagecast-aktualisieren.path/.service`
  (updates from the admin: a request file starts a root script with fixed actions – no sudo, no polkit),
  `signagecast-startpasswort.path/.service` (deletes the initial-password file after the change), with HDMI
  `signagecast-hdmi.service` and a drop-in `seatd.service.d/signagecast.conf`. **Cockpit** (`cockpit.socket`) is enabled.
- **Ports:** 9090 (Cockpit), 8888 (stream, `SC_STREAM_PORT`), 8890 (players, webhook, panel – only answers signed or
  keyed requests). No firewall rules are changed, no SSH server is installed, no sudo rights are given.
- **Only when you ask for it in the admin:** Tailscale for remote sites (package source `pkgs.tailscale.com`, key
  checked) and package upgrades via **System → Updates**.

**Docker / Podman / NAS / Windows:** nothing on the host except the image `ghcr.io/thefrozn/signagecast`, the
container `signagecast` and its volume (`/data`). Windows additionally: the folder `%USERPROFILE%\SignageCast`
(compose file); Docker Desktop and WSL only if you installed them for it.

## Uninstall

All ways keep a backup unless you delete the data on purpose. Export a backup first if you might come back:
**System → Backup**.

- **Debian / installation ISO / inside a container** (since 0.62): `sh /opt/signagecast/werkzeug/deinstallieren.sh` –
  removes services and program; settings and data stay in `/etc/signagecast` and `/var/lib/signagecast` (a new
  installation picks them up). With `--alles` also settings, data and the users `signagecast` and `tvadmin` (not on the
  ISO, where `tvadmin` is the computer's login). It always puts a backup to `/root/signagecast-sicherung-<date>.tar.gz`
  first. Debian packages stay; remove them only if nothing else needs them:
  `apt purge chromium ffmpeg xvfb pulseaudio cockpit-ws cockpit-system cockpit-bridge intel-media-va-driver-non-free && apt autoremove --purge`
- **Proxmox VE:** remove the whole container on the host: `pct stop <ID> && pct destroy <ID> --purge` (also removes it
  from backup jobs and HA). Nothing else was changed on the host.
- **Docker / Podman:** `docker rm -f signagecast`, then the data: `docker volume ls | grep signagecast` and
  `docker volume rm <name>` (with `docker run` it is `signagecast`, with compose usually `<folder>_signagecast`), finally
  `docker image rm ghcr.io/thefrozn/signagecast`. With compose: `docker compose down -v` in the folder of `compose.yaml`.
- **QNAP (Container Station):** **Applications** → `signagecast` → **Delete** (if the dialog offers to remove the volumes,
  tick it to delete the data as well; otherwise delete the volume `signagecast_signagecast` under **Volumes**), then **Images** → `ghcr.io/thefrozn/signagecast` → **Delete**.
- **Synology (Container Manager):** **Project** → `signagecast` → **Action → Stop**, then **Action → Delete**; **Image**
  → `ghcr.io/thefrozn/signagecast` → **Delete**; the data is in the shared folder `docker/signagecast` – delete it in
  **File Station**.
- **Windows (Docker Desktop):** PowerShell: `docker compose -p signagecast down -v` and
  `docker image rm ghcr.io/thefrozn/signagecast`, then delete the folder `%USERPROFILE%\SignageCast`. Docker Desktop
  itself only if you do not need it any more: `winget uninstall Docker.DockerDesktop`.
- **Windows (WSL):** inside Debian as above (`deinstallieren.sh`), or remove the whole Debian: `wsl --unregister Debian`
  (deletes everything in it).
- **Raspberry Pi players:** remove the device in the admin (**Displays → Devices**), then reflash the SD card.

## Updates

- **Proxmox / Debian:** in the admin under **System → Updates** (signed packages, automatic return to the previous
  version on errors) or by running the install command again – see [how it works](HOW-IT-WORKS.md#updates-and-backups).
- **Docker / Podman / NAS:** pull the new image and recreate the container; the data in `/data` stays.

---

## Deutsch (kurz)

Wege: **Proxmox** (Einzeiler oben in der Shell des Proxmox-Hosts), **eigener Rechner** (seit 0.52: Installations-ISO
`signagecast-server-vX.Y.Z.iso` aus dem Release auf einen USB-Stick, nur UEFI; der Debian-Installer fragt Passwort für
`tvadmin`, bestätigt das Löschen der Platte und fragt „Bild auch an diesem Rechner per HDMI zeigen?“ – änderbar unter
*Displays → + Neues Gerät → Dieser Rechner per HDMI*; in einer VM getestet, noch nicht auf echtem Mini-PC), **Debian 13** (`install.sh` als root, erneut
ausführen = Update; Bild per HDMI mit `SC_HDMI=1`), **Docker/Podman** (`docker run …` oder `compose.yaml`), **Windows** ([Anleitung](install/WINDOWS.md): Docker Desktop mit einem PowerShell-Befehl oder WSL, nur Full HD – noch nicht auf echtem Windows getestet), **QNAP** ([Anleitung](install/QNAP.md))
und **Synology** ([Anleitung](install/SYNOLOGY.md)) – beide per Klick in der Container-App des NAS. Nötig ist ein
x86-Rechner (Intel/AMD), für 4K mit Intel-Grafik; ARM (Raspberry Pi, ARM-NAS) geht als Server nicht. Am Fernseher
kann ab 0.23 ein **Raspberry Pi als Player** stehen – Image aus der Verwaltung, siehe [PLAYER.md](PLAYER.md#deutsch-raspberry-pi-als-player)
(braucht Port 8890, im Docker-/NAS-Betrieb freigeben). **Rootless Podman** bitte mit `--network host` starten
(Befehl oben): Die normale Portweiterleitung kann die Absenderadresse verdecken, dann wären Kamera-Streams (sonst nur im
Container lesbar) aus dem Netz abrufbar.

| Weg | Verwaltung | Stream | Erste Anmeldung |
|---|---|---|---|
| Proxmox-LXC bzw. Debian-**Container** | https://&lt;IP&gt;:9090 (Cockpit) | :8888 | `tvadmin` mit **zufälligem Passwort** (seit 0.62), am Ende angezeigt und bis zur Änderung in `/root/signagecast-startpasswort` (Proxmox-Host: `pct exec <ID> -- cat /root/signagecast-startpasswort`) |
| Debian **VM / echter Rechner** (nativ) | https://&lt;IP&gt;:9090 (Cockpit) | :8888, änderbar mit `SC_STREAM_PORT` | `tvadmin` mit **zufälligem Passwort** (Datei wie oben) – oder dein eigener Cockpit-Benutzer |
| **Installations-ISO** | https://&lt;IP&gt;:9090 (Cockpit) | :8888 | `tvadmin` mit dem Passwort aus dem Installer |
| **Docker / Podman / NAS** | http://&lt;Host&gt;:**19090** (eigene Anmeldung) | :8888 | zufälliges Passwort im Protokoll des Containers (Zeile „Startpasswort der Verwaltung“) |

**Schon Cockpit installiert?** Bei der nativen Installation fügt sich SignageCast in dein vorhandenes Cockpit ein – es
kommt nur der Menüpunkt „SignageCast“ dazu, kein zweiter Port, keine zweite Anmeldung, deine Einstellungen bleiben.
Cockpit kann Erweiterungen nicht pro Benutzer ausblenden – wer sich an diesem Cockpit anmelden darf, kann auch
SignageCast einstellen. Docker/Podman nutzt 19090, weil auf vielen Servern Cockpit schon 9090 belegt.

Zum Ausprobieren reicht Docker ohne `/dev/dri` (Software-Fallback). Wetter und Vorhersage kommen weltweit von MET
Norway, amtliche Unwetterwarnungen (DWD) gibt es nur für Deutschland.

Danach: Verwaltung öffnen, Startpasswort ändern, der Assistent führt durch Sprache, Ort und Home Assistant; am
Fernseher **http://&lt;IP&gt;:8888/tv** als Startseite öffnen. Updates: Proxmox/Debian in der Verwaltung unter
**System → Updates**, Docker/NAS durch neues Image und Neuerstellen des Containers (Daten in `/data` bleiben).

Eigenes Passwort gleich bei der Installation: `SC_PASSWORT='…'` vor den Befehl setzen (mindestens 8 Zeichen; bei
Docker `-e SC_PASSWORT=…`).

**Passwort vergessen:** Proxmox `pct exec <ID> -- passwd tvadmin` · Debian/ISO `passwd tvadmin` als root (ISO: an der
Konsole als tvadmin anmelden, `sudo passwd tvadmin`) · Docker/Podman/Windows
`docker exec signagecast rm /data/config/verwaltung.json`, Container neu starten, neues Startpasswort im Protokoll ·
QNAP/Synology dasselbe über das Terminal des Containers in der Container-App · WSL `wsl -d Debian -u root passwd tvadmin`.
Einstellungen und Daten bleiben dabei unberührt. Details: [Forgot the password?](#forgot-the-password-reset)

**Was die Installation am System ändert** (Debian, Proxmox-Container, ISO): Paketquellen um `contrib non-free
non-free-firmware` ergänzt, Debian-Pakete (Chromium, ffmpeg, Xvfb, PulseAudio, Intel-Videotreiber, Schriften, Python,
Cockpit …), MediaMTX nach `/opt/mediamtx`, Benutzer `signagecast` (ohne Anmeldung) und `tvadmin`, Ordner
`/opt/signagecast`, `/etc/signagecast`, `/var/lib/signagecast`, `/var/lib/signagecast-aktualisierung`,
`/usr/share/cockpit/signagecast`, `/usr/local/bin/signagecast-mcp`, systemd-Dienste `signagecast`,
`signagecast-mediamtx`, `signagecast-aktualisieren`, `signagecast-startpasswort` (bei HDMI `signagecast-hdmi` + seatd),
Cockpit eingeschaltet, Ports 9090/8888/8890. Keine Firewall-Regeln, kein SSH-Server, keine sudo-Rechte. Tailscale nur auf
Wunsch aus der Verwaltung. Docker/NAS/Windows: nur Image, Container und Volume. Vollständige Liste:
[What the installation changes](#what-the-installation-changes-on-the-system).

**Deinstallieren:** Debian/ISO/im Container `sh /opt/signagecast/werkzeug/deinstallieren.sh` (Daten bleiben, mit
`--alles` alles weg, vorher immer Sicherung nach `/root`) · Proxmox `pct stop <ID> && pct destroy <ID> --purge` ·
Docker/Podman `docker rm -f signagecast`, Volume (`docker volume ls`) und Image löschen bzw. `docker compose down -v` ·
QNAP Container Station → Anwendungen → signagecast → Löschen (Volumes mit entfernen), Image löschen · Synology Container
Manager → Projekt → Stoppen, Löschen, Image löschen, Ordner `docker/signagecast` in der File Station löschen · Windows
`docker compose -p signagecast down -v`, Image löschen, Ordner `%USERPROFILE%\SignageCast` löschen (WSL: `wsl
--unregister Debian`) · Pi-Player in der Verwaltung entfernen, SD-Karte neu beschreiben. Details:
[Uninstall](#uninstall).
