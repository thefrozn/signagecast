<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/logo/signagecast-wortmarke-dunkel.svg">
    <img src="docs/logo/signagecast-wortmarke.svg" alt="SignageCast" width="400">
  </picture>
</p>

<p align="center"><strong>Turn any TV into a calm information screen – with live wildlife cams from around the world.</strong></p>

<p align="center">
  <a href="https://github.com/thefrozn/signagecast/releases/latest"><img src="https://img.shields.io/github/v/release/thefrozn/signagecast?label=release&color=0066cc" alt="Latest release"></a>
  <a href="https://github.com/thefrozn/signagecast/actions/workflows/tests.yml"><img src="https://github.com/thefrozn/signagecast/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/thefrozn/signagecast?color=0066cc" alt="MIT license"></a>
</p>

<p align="center">
  <a href="#installation"><b>Install</b></a> ·
  <a href="docs/TOUR.md"><b>Screenshot tour</b></a> ·
  <a href="docs/PLAYER.md">Players</a> ·
  <a href="docs/MANUAL.md">Manual &amp; FAQ</a> ·
  <a href="docs/HOW-IT-WORKS.md">How it works</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="README.de.md">Deutsch</a>
</p>

![A TV showing clock, weather, a live cam and Home Assistant values](docs/tour/01-tv-living-room.jpg)

SignageCast shows clock, weather and – if you like – values from **Home Assistant** next to a large window with **live
nature and wildlife cams**, always from a place where it is daytime. You design the screen in a **drag-and-drop editor**
and manage everything in the browser, also from your phone. A small Linux container draws the page and streams it to the
TV as video, or a Raspberry Pi or PC at the TV shows it directly.

Made for living rooms, waiting rooms and company receptions. Self-hosted, no cloud, no account – free and open source.

## What it does

<table>
<tr>
<td valign="top" width="50%">

**The screen**
- Live window to the world: YouTube live cams that rotate and skip bad streams by themselves
- Clock, weather, forecast, official severe weather warnings (DWD)
- Backgrounds that follow the real sun at your location
- Templates for living room, practice, company and night

</td>
<td valign="top" width="50%">

**Content**
- Layout editor on a 48 × 27 grid with conditions, fonts and colours – or let an AI build a layout
- Home Assistant values, own JSON/RSS sources, charts, calendars
- IP cameras, web pages, PDFs, internet radio, clips at fixed times
- Messages, announcements and a red emergency screen on all TVs

</td>
</tr>
<tr>
<td valign="top">

**Players**
- Any TV browser that plays H.265 – just open one address
- Raspberry Pi or PC from a ready image, managed centrally
- Direct mode: the player shows the page itself, no encoding on the server
- Browser device: a secret link for a smart TV or kiosk browser

</td>
<td valign="top">

**Operation**
- Admin in Cockpit, German and English, with a to-do list
- Signed updates that roll back by themselves
- Backup and restore, notifications via Telegram, e-mail or Home Assistant
- Rendering runs only while someone watches
- Picture check, calm fallback when the internet is gone, change log and layout versions

</td>
</tr>
</table>

<details>
<summary><b>All features in detail</b></summary>

- **Live window to the world** – fixed and automatically discovered YouTube live streams (safari, sea, birds, bears;
  also cities, beaches, mountains, harbours, airports, trains, space and natural wonders – switch on what you like),
  rotating every few minutes, only where it is daytime. Bad streams (not starting, buffering, frozen, low resolution)
  are skipped; favourites can be protected, unwanted ones rejected.
- **Layout editor** – clock, date, weather, forecast, rooms, tiles with any Home Assistant value, live video, radio,
  free text and ticker, logo, camera, calendar / waste collection, messages from Home Assistant. Conditions (“only show
  when …”), fonts, colours, 9 text positions.
- **Your own data sources** – any JSON API, RSS/Atom feed or picture address, fetched at your interval (paste a `curl`
  command, pick values by clicking in the response). Elements: value, list / feed (also as ticker), picture, gauge,
  countdown, QR code, placeholders like `{source:path}` in any text.
- **Cameras, charts, calendars, web pages** – IP cameras (RTSP, HLS, MJPEG; e.g. the doorbell only when it rings),
  history charts, calendars from iCal addresses or uploaded .ics/.csv files, web pages live or as a regular screenshot.
- **Templates** – Standard, Video large, Video only, Info without video, *Practice – calm*, *Company – corporate design*,
  *Window to the world*, Night.
- **Backgrounds by time of day** – picture sets for sunrise, day, sunset and night, weather pictures, slideshow or your
  own pictures.
- **Internet radio** – own streams or suggestions for your location; or the original sound of the cams.
- **Clips at fixed times** – e.g. *tagesschau in 100 Sekunden* on the hour.
- **Several TVs** – each with its own address, layout, schedule, sound and categories.
- **Raspberry Pi as player** (experimental) – a ready SD card image per screen (Wi-Fi included, hotspot with QR code
  as fallback) or one image for many Pis with a pairing code; status, screenshot, TV on/off via HDMI-CEC, rotation,
  updates; optional terminal in the browser. [PLAYER.md](docs/PLAYER.md)
- **PC as player** (experimental) – a PC or thin client (x86-64, UEFI, Secure Boot may stay on) starts from a USB stick
  and shows the page itself. [PLAYER.md](docs/PLAYER.md#pc-as-player-since-036-experimental)
- **Messages and notifications** – DWD warnings as an element; banners from other systems via a webhook; notifications
  when a TV fails, an update or backup fails or Home Assistant is disconnected.
- **Elements with a period** – e.g. “Closed from 23 Dec to 2 Jan” appears and disappears by itself.
- **Emergency screen and announcement panel** – a red full-screen message on all TVs; a separate reception page that
  sends calls like “Mrs Baker, please go to room 2”, read aloud offline (Piper) – and, if allowed, ticker messages,
  a layout for a while and switching TVs on/off.
- **Energy saving** – schedules switch a TV to night mode or black, and really off and on via Home Assistant.
- **Built to run unattended** – when the internet is gone the video window shows your own media or a calm picture
  instead of an error; a picture check notices a black or frozen TV and repairs it (reload, restart, notify).
- **Change log and layout versions** – who changed what and when (admin, panel, webhook, system – never values); the
  last 10 versions of every layout, also of deleted ones.
- **Layouts from an AI** – copy the instructions with the complete [layout format](docs/LAYOUT-FORMAT.md) into
  ChatGPT, Claude or Gemini and paste the answer; the import repairs what it can and tells you what.

</details>

<p align="center">
  <img src="docs/praxis.jpg" width="49%" alt="Practice template">
  <img src="docs/firma.jpg" width="49%" alt="Company template">
</p>
<p align="center">
  <img src="docs/editor.jpg" width="49%" alt="Layout editor in Cockpit">
  <img src="docs/tour/04-overview.jpg" width="49%" alt="Overview in the admin">
</p>

## Installation

You need an **x86 computer with Intel graphics** (e.g. a mini PC with Intel N100) and a TV whose browser plays H.265 –
or a Raspberry Pi or PC as player. Without usable graphics a Full HD software fallback runs. Details:
[hardware](docs/HARDWARE.md).

| Where | How | Guide |
|---|---|---|
| **Proxmox VE** | one command on the Proxmox host shell (below) | [Installation](docs/INSTALL.md#proxmox-ve) |
| **Debian 13** (LXC, VM, PC) | `curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh \| sh` | [Installation](docs/INSTALL.md#debian-13) |
| **Docker / Podman** | `docker run …` or [`compose.yaml`](compose.yaml) | [Installation](docs/INSTALL.md#docker--podman) |
| **QNAP NAS** | by mouse in Container Station | [QNAP guide](docs/install/QNAP.md) |
| **Synology NAS** | by mouse in Container Manager | [Synology guide](docs/install/SYNOLOGY.md) |

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/proxmox/ct.sh)"
```

Then open the admin – **https://&lt;IP&gt;:9090** (Proxmox/Debian, user `tvadmin`) or **http://&lt;host&gt;:19090**
(Docker/NAS, password in the container log) – follow the short assistant and open **http://&lt;IP&gt;:8888/tv** on the TV.

## Principles

Three goals rank equally – none is traded for another:

- **Rock-stable** – a screen runs for months unattended; every part restarts itself, updates roll back on failure.
- **Secure** – signed releases, secrets stay on the server, nothing listens that does not have to, no cloud needed.
- **Light** – runs on a small mini PC; every release is measured (CPU, memory, lost frames) before it is published.

## Thanks

Special thanks to **[RaspiSignage](https://github.com/boschkundendienst/raspisignage)** by boschkundendienst – the
Raspberry Pi signage project that inspired the idea of a self-hosted screen that “normal” people manage in the browser.
SignageCast contains no code from it; the approach (server-side rendering and streaming) is different.

## Support

Questions, bugs and ideas: [GitHub issues](https://github.com/thefrozn/signagecast/issues).

## License

MIT – see [LICENSE](LICENSE). Pictures, icons and the logo font: see [NOTICE.md](NOTICE.md).
