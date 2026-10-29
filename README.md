# SignageCast

**Turn any TV into a calm information screen – with live wildlife cams from around the world.**

SignageCast shows clock, weather (MET Norway) and – optionally – any values from **Home Assistant** together with a large window of
**live nature and wildlife cams** (YouTube) – always where it is currently daytime. Everything is rendered in a small
Linux container and sent to the TV as a **4K video stream**; the TV only has to open one address in its browser.
You design the screen in a **drag-and-drop editor** and manage everything in the browser, also from your phone.

Made for the living room, waiting rooms of practices and company receptions. Free and open source (MIT).

*Deutsche Kurzfassung weiter unten.*

![Practice template](docs/praxis.jpg)

## Features

- **Live window to the world** – fixed and automatically discovered YouTube live streams (safari, sea, birds, bears …),
  rotating every few minutes, only where it is daytime. Bad streams (not starting, buffering, frozen, low resolution) are
  skipped automatically; favourites can be protected, unwanted ones rejected.
- **Layout editor** – drag, resize and configure elements on a 48 × 27 grid: clock, date, weather, forecast, rooms, tiles
  with any Home Assistant value, live video, radio station, free text and ticker, logo, camera, calendar / waste
  collection, messages from Home Assistant. Conditions (“only show when …”), fonts, colours, 9 text positions.
- **Templates** – Standard, Video large, Video only, Info without video, *Practice – calm (waiting room)*,
  *Company – corporate design*, *Window to the world*, Night.
- **Backgrounds by time of day** – picture sets (nature, city, sky, mountains, sea) for sunrise, day, sunset and night,
  following the real sun position at your location; optionally weather pictures, slideshow or your own pictures.
- **Internet radio** – own streams or suggestions for your location; or the original sound of the cams.
- **Clips at fixed times** – e.g. the German news *tagesschau in 100 Sekunden* on the hour and half hour.
- **Several TVs** – each with its own address, layout, schedule, sound and categories.
- **Energy saving** – rendering runs only while someone watches; schedules can switch a TV to night mode or black.
- **Admin in Cockpit** – overview with preview picture, system pages, backup/restore, German and English.

<p align="center"><img src="docs/firma.jpg" width="49%" alt="Company template"> <img src="docs/fenster.jpg" width="49%" alt="Window to the world template"></p>
<p align="center"><img src="docs/editor.jpg" width="80%" alt="Layout editor in Cockpit"></p>

## Requirements

- A PC with **Intel graphics** (Quick Sync / VAAPI, e.g. a mini PC with an Intel CPU from the 7th generation on),
  running **Proxmox VE**, **Debian 13** or **Docker / Podman**. 2–4 cores, 10 GB disk and about 1 GB RAM per TV.
  Without usable graphics SignageCast falls back to H.264 in Full HD on the CPU (about 1–2 cores while someone watches).
- Optional: **Home Assistant** in the same network (for your own values; weather comes from MET Norway).
- A TV whose browser plays **H.265 / HEVC** (for 4K; most smart TVs from about 2018). Full HD output is also possible.

## Installation

**Proxmox VE** – run on the Proxmox host shell, answer the questions (Enter = suggestion):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/proxmox/ct.sh)"
```

It creates a Debian 13 container, passes the Intel GPU through and installs SignageCast.

**Existing Debian 13** (LXC or VM with `/dev/dri/renderD128`) – as root:

```bash
curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh
```

Running the same command again updates SignageCast; settings and data are kept.

**Docker / Podman** (any Linux host, also NAS systems like Unraid, Synology, TrueNAS) – one line:

```bash
docker run -d --name signagecast --restart unless-stopped --device /dev/dri \
  -p 8888:8888 -p 9090:9090 -v signagecast:/data \
  -e TZ=Europe/Berlin -e SC_HOST_IP=192.168.1.20 ghcr.io/thefrozn/signagecast:latest
```

or with [`compose.yaml`](compose.yaml): `docker compose up -d`. Podman: the same command with `podman`.

- `--device /dev/dri` passes the graphics through; leave it out on systems without Intel graphics (software fallback).
  Rootless Podman additionally needs `--group-add keep-groups`.
- **Admin:** http://&lt;host&gt;:9090 – the initial password is printed in the log: `docker logs signagecast`
  (or set your own with `-e SC_PASSWORT=…`). Change it under **Connection**. No Cockpit inside the container.
- `SC_HOST_IP` = the IP of the Docker host; the Home Assistant guide in the admin shows it (HA sees the host's IP).
- All settings and data are in the volume `/data`. **Update:** `docker pull ghcr.io/thefrozn/signagecast:latest`, then
  recreate the container (`docker compose up -d`, or `docker rm -f signagecast` and the `docker run` line again).

**Manual:** download a release, unpack it and run `sh installieren.sh`.

## First steps

1. Open **https://&lt;container-IP&gt;:9090** (accept the certificate warning), log in as **tvadmin** with the initial
   password **tvadmin** – then please change it (top right → Accounts → tvadmin → Set password).
   (Docker / Podman: **http://&lt;host&gt;:9090**, password from the log – see above.)
2. Menu **SignageCast → Connection**: enter the Home Assistant address and follow the guide shown there. Home Assistant
   trusts the container via `trusted_networks` – no password or token is stored. Take the location from Home Assistant.
3. **Display**: weather comes from MET Norway (or choose a Home Assistant weather entity). **Layout**: adapt the standard layout or start from a template.
4. On the TV open **http://&lt;container-IP&gt;:8888/tv** in the browser and set it as start page.
5. Optional: **Radio**, **Clips**, more **TVs**, schedules.

## How it works

| Part | Where | Task |
|---|---|---|
| Data service `signagecast` | `/opt/signagecast/app/`, only 127.0.0.1:8080 | TV page, Home Assistant values, stream list, search, quality watch, API for the admin |
| Render chain | `/opt/signagecast/render/tv-render.sh` | Xvfb + Chromium (Full HD) → ffmpeg → Intel GPU (upscale, H.265) + AAC → MediaMTX |
| MediaMTX `signagecast-mediamtx` | `/opt/mediamtx`, port 8888 | HLS stream, starts rendering on demand |
| Admin | `/usr/share/cockpit/signagecast`, port 9090 | Cockpit extension (Docker/Podman: same page served by `app/verwaltung.py` with its own login) |
| Settings / data | `/etc/signagecast/`, `/var/lib/signagecast/` | backup and restore in the admin |

Only the Python standard library and Debian packages are used. Third-party components and picture sources:
see [NOTICE.md](NOTICE.md).

## Good to know

- Only public YouTube pages and the **official embed player** are used; streams whose operators do not allow embedding
  are not shown. If YouTube reports too many requests, SignageCast pauses for an hour. Nothing is circumvented.
- The small browser extension `render/h264-fluessig` tells YouTube that H.264 up to 1080p plays smoothly – Chromium in
  the container decodes without GPU and would otherwise report “not smooth”, and YouTube would deliver only 144p.
- The admin user `tvadmin` has no administrator rights in the container.

## Support

Questions, bugs and ideas: [GitHub issues](https://github.com/thefrozn/signagecast/issues).

---

## Deutsch (kurz)

SignageCast macht aus einem Fernseher einen ruhigen Infobildschirm: Uhr, Wetter (MET Norway) und auf Wunsch Werte aus **Home Assistant**,
dazu ein großes Fenster mit **Live-Kameras von Tieren und Natur** aus aller Welt – nur dort, wo gerade Tag ist.
Gezeichnet wird in einem kleinen Linux-Container, der Fernseher öffnet nur eine Adresse im Browser. Das Bild gestaltest
du im **Layout-Editor** (Bausteine ziehen, Größe ändern, Vorlagen für Wohnzimmer, Wartezimmer und Firma),
dazu Hintergründe nach Tageszeit, Internetradio, Einspieler wie „tagesschau in 100 Sekunden“, mehrere Fernseher.

**Installation auf Proxmox** (in der Shell des Proxmox-Hosts):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/proxmox/ct.sh)"
```

**In einem vorhandenen Debian 13** (als root): `curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh`

**Docker / Podman:** `docker run -d --name signagecast --restart unless-stopped --device /dev/dri -p 8888:8888 -p 9090:9090 -v signagecast:/data -e TZ=Europe/Berlin -e SC_HOST_IP=<IP des Hosts> ghcr.io/thefrozn/signagecast:latest`
(oder `compose.yaml`). Verwaltung **http://&lt;Host&gt;:9090**, Startpasswort steht im Protokoll (`docker logs signagecast`).
Ohne Intel-Grafik läuft ein Notbetrieb mit H.264 in Full HD per CPU.

Danach **https://&lt;IP&gt;:9090** öffnen, Anmeldung **tvadmin** / Startpasswort **tvadmin** (bitte ändern),
unter **Verbindung** Home Assistant einrichten (Anleitung steht dort), am Fernseher **http://&lt;IP&gt;:8888/tv** öffnen.
Voraussetzungen: Intel-Grafik, ein Fernseher-Browser mit H.265; Home Assistant optional.

## License

MIT – see [LICENSE](LICENSE). Pictures and icons: see [NOTICE.md](NOTICE.md).
