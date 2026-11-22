# SignageCast – hardware

[← README](../README.md) · [installation](INSTALL.md) · [manual](MANUAL.md) · [how it works](HOW-IT-WORKS.md)

## Requirements

- A PC with **Intel graphics** (Quick Sync / VAAPI, e.g. a mini PC with Intel N100 or an Intel CPU from the 7th generation on),
  running **Proxmox VE**, **Debian 13**, **Docker / Podman** or a **QNAP / Synology NAS** with Intel CPU.
  2–4 cores, 10 GB disk and about 1 GB RAM per TV.
  Without usable graphics SignageCast falls back to H.264 in Full HD on the CPU (about 1–2 cores while someone watches).
  Only x86 (Intel/AMD) – no ARM.
- Optional: **Home Assistant** in the same network (for your own values; weather comes from MET Norway).
- A TV whose browser plays **H.265 / HEVC** (for 4K; most smart TVs from about 2018). Full HD output is also possible.

## Recommendations

SignageCast renders the TV page in a browser, records it and encodes a video stream. The graphics unit does the
encoding (H.265/HEVC in 4K via VAAPI); the CPU mainly runs the browser, which decodes the live video in software.

| | Recommendation |
|---|---|
| **Minimum (recommended)** | Mini PC with **Intel N100 / N95** (Alder Lake-N): H.264 and H.265 encoding in hardware up to 4K, 6–10 W, inexpensive |
| **Good** | Any Intel CPU with integrated graphics from the **7th generation** (Kaby Lake) on, e.g. Core i5-7500T – via VAAPI; the encoder *Intel Quick Sync (QSV)* needs the 11th/12th generation or newer (N100 etc.) |
| **Works** | Intel 6th generation (Skylake): H.265 only 8 bit |
| **Without usable graphics** | Works (since 0.69 the default for new devices is **direct mode**, see below). Stream mode encodes H.264 in Full HD on the CPU (about one more core per channel while someone is watching) |
| **AMD graphics** | Works via VAAPI (radeonsi) – tested with Ryzen 9 4900H / Radeon Vega, see below |
| **NVIDIA graphics card** | Experimental from 0.22: encoder *NVIDIA NVENC* per TV, if card and driver are passed into the container (`/dev/nvidia*`, Docker `--gpus all`) – untested |
| **Raspberry Pi** | Not suitable as a server: the Pi 5 has **no** hardware video encoder, the Pi 4 only H.264 up to 1080p and too little CPU for browser + video. **As a player at the TV** it works from 0.23: the Pi plays the finished stream via HDMI – see [Raspberry Pi as player](PLAYER.md). |

Per TV: about 1 GB RAM and one CPU core for the browser; disk 10 GB. The TV's browser must play **H.265** for 4K
(most smart TVs from about 2018); Full HD output with H.264 is possible as well.

**Our experience** (author's setup): Proxmox VE on a mini PC with **Intel Core i5-7500T / HD Graphics 630**, SignageCast
in an LXC container with 4 cores and 3 GB RAM, one Samsung TV (4K H.265, 16 Mbit/s, 25 fps):

| Measured (CPU package via RAPL) | Value |
|---|---|
| Idle, nobody watching (rendering stops automatically) | about 1.2 W |
| Streaming 4K with a live video (1080p) and sound | about **10–11 W**; Chromium ~50 %, ffmpeg ~11 %, Xvfb ~6 % of one core |
| Earlier prototype rendering the full Home Assistant dashboard in 4K | about 16–23 W – the light own TV page and Full HD rendering with GPU upscaling saved more than half |
| Software fallback test (no GPU, 2 cores) | ffmpeg ~70 % of one core for H.264 1080p25 |

## Tested devices

What the author has running or has tested. Everything else should work if it meets the requirements – reports welcome
(GitHub Discussions).

| Device | Role | Way | Status |
|---|---|---|---|
| Mini PC Intel Core i5-7500T / HD Graphics 630 | server | Proxmox VE 9, LXC (4 cores, 3 GB) | **in daily use** since 0.1, 4K H.265 via VAAPI |
| Intel test container (same host) | server | Proxmox LXC, Debian 13 | every release is tested and measured here first |
| AMD Ryzen 9 4900H / Radeon Vega (Renoir) | server | Proxmox VE 9, LXC | **in daily use** since 0.45, VAAPI radeonsi |
| Docker (inside the Intel test container) | server | `docker run` / compose | tested; without `/dev/dri` software fallback |
| Rootless Podman, Docker bridge network on a normal host | server | `--network host` / `-p` | **untested** |
| Installation ISO | server | virtual machine (UEFI, Secure Boot) | tested – **not yet on a real mini PC** |
| Windows 10/11 Docker Desktop / WSL | server | `schnellstart.ps1` | **untested** on real Windows |
| QNAP / Synology NAS | server | Container Station / Container Manager | **untested** on a real NAS (guides follow the official apps) |
| Raspberry Pi 4 (4 GB) | player | player image, Wi-Fi, also via Tailscale | tested (stream and direct mode, smooth also via Tailscale) |
| Raspberry Pi 5 | player | player image | **untested** on real hardware |
| Raspberry Pi offline copy | player | player image | **untested** on a real Pi |
| PC player (x86 image) / browser device | player | image / any browser | tested in a VM / in browsers |
| Samsung smart TV (Tizen, 4K) | TV | built-in browser, H.265 | **in daily use** (Full HD and 4K) |

YouTube in the container is decoded in software; the small extension `render/h264-fluessig` keeps YouTube at 720p/1080p
instead of 144p (see [how it works](HOW-IT-WORKS.md#good-to-know)).

## Without a graphics card

SignageCast checks at every start with a short test encode whether the graphics can encode the video stream. If not
(no `/dev/dri`, no access, or a GPU without H.265), it runs anyway:

- **New devices start in direct mode** (Pi 4/5, PC; browser devices always): the device draws the TV page itself, the
  server only delivers the page and its data. The setup assistant gives the TV's browser the address of the TV page
  instead of the video stream. Existing devices keep their mode.
- **Stream mode still works** and can be chosen per device (*Devices → device → Settings → Display*). The CPU then
  encodes H.264 in Full HD (at most 8 Mbit/s). The admin page says so next to the choice, in the channel's *Video
  stream* tab and in the performance test.
- **Pi 3 and Zero 2 W** can only show the stream – with them the CPU encodes in any case.
- The video stream is only produced while someone is watching it, so a server whose devices are all in direct mode
  does not encode at all.

Measured on the test container (Core i5-7500T, 4 cores, one channel in Full HD, 2026-11-22): stream mode with the GPU
about 100 % of one core for the whole chain, without the GPU about 180 %; no frames lost in either case.

---

## Deutsch (kurz)

Empfohlenes Minimum ist ein Mini-PC mit **Intel N100/N95** (H.265 in 4K per Hardware, 6–10 W); jede Intel-CPU mit
Grafik ab der 7. Generation läuft gut, auch ein QNAP-/Synology-NAS mit Intel-Celeron (z. B. J4125). **Ohne
Grafikkarte** geht es auch (seit 0.69): Neue Geräte starten dann im **Direktmodus** (das Gerät zeichnet die TV-Seite
selbst, der Server braucht kaum Leistung), der Assistent gibt dem Fernseher-Browser die Adresse der TV-Seite statt des
Videostreams. Der **Streammodus** bleibt je Gerät wählbar; dann kodiert die CPU H.264 in Full HD – gemessen im
Testcontainer (i5-7500T) etwa 180 % eines Kerns statt 100 % mit Grafik; die Verwaltung weist an der Wahl, im Reiter
*Videostream* und im Leistungstest darauf hin. Pi 3 und Zero 2 W gehen nur mit Stream. Nur x86 (Intel/AMD), kein ARM.
**Raspberry Pi** eignet sich nicht als Server: Der Pi 5 hat keinen Video-Encoder, der Pi 4 nur H.264 bis 1080p und zu
wenig CPU für Browser und Video. **Als Player am Fernseher** geht er ab 0.23 – siehe [Raspberry Pi als Player](PLAYER.md#deutsch-raspberry-pi-als-player). Je Fernseher etwa 1 GB RAM und ein Kern; der Fernseher-Browser muss für 4K H.265 können.
**Getestete Geräte** (Tabelle oben): im Alltag Mini-PC Core i5-7500T (Proxmox-LXC), AMD Ryzen 9 4900H mit Vega
(Proxmox-LXC), Raspberry Pi 4 als Player (WLAN, Tailscale; Stream und Direktmodus ruckelfrei), Samsung-Smart-TV (4K, H.265); getestet Docker (im Test-Container, mit und
ohne `/dev/dri`), Installations-ISO und PC-Player in einer VM. **Ungetestet:** echter Mini-PC mit ISO, Windows,
QNAP/Synology, rootless Podman, Raspberry Pi 5, Pi-Offline-Kopie. Rückmeldungen gern in den GitHub Discussions.

Erfahrung des Autors: Core i5-7500T mit HD 630 unter Proxmox, LXC mit 4 Kernen/3 GB, 4K-Stream mit Live-Video und Ton
bei etwa **10–11 W** CPU-Paket, im Leerlauf etwa 1,2 W.
