# SignageCast – installation

[← README](../README.md) · [hardware](HARDWARE.md) · [manual](MANUAL.md) · [how it works](HOW-IT-WORKS.md)

Choose one way. All of them need an **x86 computer** (Intel or AMD CPU); for 4K a CPU with **Intel graphics**
(Quick Sync) – see [hardware](HARDWARE.md). The TV only opens one address in its browser.

| Way | For | Guide |
|---|---|---|
| **Proxmox VE** | a Proxmox server – one command creates a ready container | [below](#proxmox-ve) |
| **Debian 13** | an existing LXC, VM or real computer | [below](#debian-13) |
| **Docker / Podman** | any Linux host | [below](#docker--podman) |
| **Windows** | a Windows 10/11 PC – Docker Desktop with one PowerShell command, or WSL (Full HD, no Quick Sync) | [Windows guide](install/WINDOWS.md) |
| **QNAP** | QNAP NAS with Intel/AMD CPU, Container Station (no command line) | [QNAP guide](install/QNAP.md) |
| **Synology** | Synology NAS with Intel/AMD CPU, Container Manager (no command line) | [Synology guide](install/SYNOLOGY.md) |

**At the TV**, besides its browser: a **Raspberry Pi as player** (from 0.23) – image from the admin, see [PLAYER.md](PLAYER.md).

## Proxmox VE

Run on the Proxmox host shell, answer the questions (Enter = suggestion):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/proxmox/ct.sh)"
```

It creates a Debian 13 container, passes the Intel GPU through and installs SignageCast.

## Debian 13

LXC, VM or a real computer with `/dev/dri/renderD128` – as root:

```bash
curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh
```

Running the same command again updates SignageCast; settings and data are kept. If port 8888 is taken, choose another
stream port: `curl -fsSL …/install.sh | SC_STREAM_PORT=8899 sh` (it is remembered for updates).

**Manual:** download a release, unpack it and run `sh installieren.sh`.

## Docker / Podman

One line:

```bash
docker run -d --name signagecast --restart unless-stopped --device /dev/dri \
  -p 8888:8888 -p 19090:19090 -v signagecast:/data \
  -e TZ=Europe/Berlin -e SC_HOST_IP=192.168.1.20 ghcr.io/thefrozn/signagecast:latest
```

or with [`compose.yaml`](../compose.yaml): `docker compose up -d`. Podman: the same command with `podman`.

- `--device /dev/dri` passes the graphics through; leave it out on systems without Intel graphics (software fallback).
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
  (line “Startpasswort der Verwaltung / initial admin password”, or set your own with `-e SC_PASSWORT=…`). Change it under **System → Access**.
  No Cockpit inside the container.
- `SC_HOST_IP` = the IP of the Docker host; the Home Assistant guide in the admin shows it (HA sees the host's IP).
- All settings and data are in the volume `/data`. **Update:** `docker pull ghcr.io/thefrozn/signagecast:latest`, then
  recreate the container (`docker compose up -d`, or `docker rm -f signagecast` and the `docker run` line again).
- The image is built for `linux/amd64` only – ARM devices (Raspberry Pi, ARM NAS) are not supported.

## Ports, login and Cockpit per installation type

| Installation | Admin | TV stream | Initial login |
|---|---|---|---|
| Proxmox LXC (`ct.sh`) or Debian **container** | **https://&lt;IP&gt;:9090** (Cockpit) | `http://<IP>:8888/<tv>` | user `tvadmin`, password `tvadmin` – please change it |
| Debian **VM / real computer** (`install.sh`, “native”) | **https://&lt;IP&gt;:9090** (Cockpit) | `http://<IP>:8888/<tv>`, other port with `SC_STREAM_PORT` | user `tvadmin` with a **random password shown once** at the end of the installation – or your own Cockpit user |
| **Docker / Podman / NAS** | **http://&lt;host&gt;:19090** (own login, no Cockpit) | `http://<host>:8888/<tv>` | random password in the container log (or `SC_PASSWORT`) |

- **Cockpit already installed?** On a native installation SignageCast integrates into your existing Cockpit: it only
  adds the menu entry **“SignageCast”** (files in `/usr/share/cockpit/signagecast`) – no second port, no second login,
  your Cockpit settings stay untouched, and the system pages (services, logs, updates) remain available.
  Note: Cockpit cannot hide an extension per user – everyone who may log in to this Cockpit can also configure SignageCast.
- **Why 19090 for Docker/Podman?** Many servers already run Cockpit on 9090. With host networking (recommended for
  rootless Podman) both would collide. Change it with `SC_VERWALTUNG_PORT`, the stream port with `SC_STREAM_PORT`.
- **Why a random password on native installations?** `tvadmin` is a Linux account that can log in to Cockpit; on a real
  computer a known default password would be a risk. In a container it only affects the container.
- **Webhook messages** (optional, from v0.16): port **8890** (`SC_WEBHOOK_PORT`; Docker: add `-p 8890:8890`), only
  answers with a secret key created in the admin – see the [manual](MANUAL.md). The same port serves the announcement
  panel and the **Raspberry Pi players** (signed requests per device).
- The installer checks whether the stream port is free and stops with a hint if another program uses it.

## First steps

1. Open the admin (see the table above; accept the certificate warning on port 9090) and log in. Then change the
   initial password (Cockpit: top right → Accounts → tvadmin → Set password; Docker/NAS: **System → Access**).
2. On a new installation a short **assistant** asks for language, location and (optionally) Home Assistant and shows
   the TV address. Later: **Settings → Home Assistant** – enter the address and follow the guide shown there. Home
   Assistant trusts the container via `trusted_networks` – no password or token is stored.
3. **Settings → General**: weather comes from MET Norway (or choose a Home Assistant weather entity).
   **Content → Layouts**: adapt the standard layout or start from a template.
4. On the TV open **http://&lt;IP&gt;:8888/tv** in the browser and set it as start page.
5. Optional: **Radio**, **Clips**, more **TVs**, schedules – see the [manual](MANUAL.md).

## Updates

- **Proxmox / Debian:** in the admin under **System → Updates** (signed packages, automatic return to the previous
  version on errors) or by running the install command again – see [how it works](HOW-IT-WORKS.md#updates-and-backups).
- **Docker / Podman / NAS:** pull the new image and recreate the container; the data in `/data` stays.

---

## Deutsch (kurz)

Wege: **Proxmox** (Einzeiler oben in der Shell des Proxmox-Hosts), **Debian 13** (`install.sh` als root, erneut
ausführen = Update), **Docker/Podman** (`docker run …` oder `compose.yaml`), **Windows** ([Anleitung](install/WINDOWS.md): Docker Desktop mit einem PowerShell-Befehl oder WSL, nur Full HD), **QNAP** ([Anleitung](install/QNAP.md))
und **Synology** ([Anleitung](install/SYNOLOGY.md)) – beide per Klick in der Container-App des NAS. Nötig ist ein
x86-Rechner (Intel/AMD), für 4K mit Intel-Grafik; ARM (Raspberry Pi, ARM-NAS) geht als Server nicht. Am Fernseher
kann ab 0.23 ein **Raspberry Pi als Player** stehen – Image aus der Verwaltung, siehe [PLAYER.md](PLAYER.md#deutsch-raspberry-pi-als-player)
(braucht Port 8890, im Docker-/NAS-Betrieb freigeben). **Rootless Podman** bitte mit `--network host` starten
(Befehl oben): Die normale Portweiterleitung kann die Absenderadresse verdecken, dann wären Kamera-Streams (sonst nur im
Container lesbar) aus dem Netz abrufbar.

| Weg | Verwaltung | Stream | Erste Anmeldung |
|---|---|---|---|
| Proxmox-LXC bzw. Debian-**Container** | https://&lt;IP&gt;:9090 (Cockpit) | :8888 | `tvadmin` / `tvadmin` (bitte ändern) |
| Debian **VM / echter Rechner** (nativ) | https://&lt;IP&gt;:9090 (Cockpit) | :8888, änderbar mit `SC_STREAM_PORT` | `tvadmin` mit **zufälligem Passwort**, das am Ende der Installation einmal angezeigt wird – oder dein eigener Cockpit-Benutzer |
| **Docker / Podman / NAS** | http://&lt;Host&gt;:**19090** (eigene Anmeldung) | :8888 | zufälliges Passwort im Protokoll des Containers (Zeile „Startpasswort der Verwaltung“) |

**Schon Cockpit installiert?** Bei der nativen Installation fügt sich SignageCast in dein vorhandenes Cockpit ein – es
kommt nur der Menüpunkt „SignageCast“ dazu, kein zweiter Port, keine zweite Anmeldung, deine Einstellungen bleiben.
Cockpit kann Erweiterungen nicht pro Benutzer ausblenden – wer sich an diesem Cockpit anmelden darf, kann auch
SignageCast einstellen. Docker/Podman nutzt 19090, weil auf vielen Servern Cockpit schon 9090 belegt.

Danach: Verwaltung öffnen, Startpasswort ändern, der Assistent führt durch Sprache, Ort und Home Assistant; am
Fernseher **http://&lt;IP&gt;:8888/tv** als Startseite öffnen. Updates: Proxmox/Debian in der Verwaltung unter
**System → Updates**, Docker/NAS durch neues Image und Neuerstellen des Containers (Daten in `/data` bleiben).
