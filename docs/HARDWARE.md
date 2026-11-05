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
| **Without usable graphics** | Software fallback: H.264 in Full HD on the CPU (about one more core while someone is watching) |
| **AMD graphics** | VAAPI drivers are installed, but untested so far |
| **NVIDIA graphics card** | Experimental from 0.22: encoder *NVIDIA NVENC* per TV, if card and driver are passed into the container (`/dev/nvidia*`, Docker `--gpus all`) – untested |
| **Raspberry Pi** | Not suitable as a server: the Pi 5 has **no** hardware video encoder, the Pi 4 only H.264 up to 1080p and too little CPU for browser + video. A “player mode” (Pi at the TV showing the page directly via HDMI, no encoding) is an idea for later. |

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

YouTube in the container is decoded in software; the small extension `render/h264-fluessig` keeps YouTube at 720p/1080p
instead of 144p (see [how it works](HOW-IT-WORKS.md#good-to-know)).

---

## Deutsch (kurz)

Empfohlenes Minimum ist ein Mini-PC mit **Intel N100/N95** (H.265 in 4K per Hardware, 6–10 W); jede Intel-CPU mit
Grafik ab der 7. Generation läuft gut, auch ein QNAP-/Synology-NAS mit Intel-Celeron (z. B. J4125). Ohne nutzbare Grafik
gibt es einen Notbetrieb (H.264 Full HD per CPU, etwa ein Kern je zuschauendem Fernseher). Nur x86 (Intel/AMD), kein ARM.
**Raspberry Pi** eignet sich nicht als Server: Der Pi 5 hat keinen Video-Encoder, der Pi 4 nur H.264 bis 1080p und zu
wenig CPU für Browser und Video. Je Fernseher etwa 1 GB RAM und ein Kern; der Fernseher-Browser muss für 4K H.265 können.
Erfahrung des Autors: Core i5-7500T mit HD 630 unter Proxmox, LXC mit 4 Kernen/3 GB, 4K-Stream mit Live-Video und Ton
bei etwa **10–11 W** CPU-Paket, im Leerlauf etwa 1,2 W.
