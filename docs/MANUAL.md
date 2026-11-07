# SignageCast – manual and FAQ

[← README](../README.md) · [installation](INSTALL.md) · [hardware](HARDWARE.md) · [how it works](HOW-IT-WORKS.md) · [screenshot tour](TOUR.md)

This manual explains the daily use of SignageCast. Installation is described in [installation](INSTALL.md).

---

## 1. The idea in one paragraph

SignageCast renders a web page per TV on the server (Chromium in a virtual screen), encodes it as a video stream and
serves it via HLS. The TV only opens one address (`http://<IP>:8888/<tv>`) – a browser, a media player app or
Home Assistant can show it. Everything you configure in the admin page (layouts, data, streams, radio) is drawn into
that video, so the TV needs no app, no login and no updates.

## 2. Admin tabs at a glance

| Area | Pages | What you do there |
|---|---|---|
| **Overview** | – | To-do list (problems first, then tips), state of every TV, viewers, CPU/RAM, time check, Home Assistant |
| **TVs** | TVs · Players (Raspberry Pi) | Address, layout, schedule, carousel, sound, video source (YouTube / own media / mixed), quality; Raspberry Pi players at the TV ([PLAYER.md](PLAYER.md)) |
| **Content** | Layouts · Data sources · Media · Clips | Layout editor and templates, JSON APIs/feeds/iCal/CSV (also as uploaded file)/cameras, own pictures and videos, scheduled clips |
| **Video & sound** | Streams · Rules · Search · Radio | Live cams, rotation and quality rules, nightly search, radio stations |
| **Settings** | General · Home Assistant · Notifications | Language, weather, location, time source; HA address and guide; Telegram/e-mail/HA and webhook |
| **System** | Updates · Backup (· Access in Docker) | Signed updates, maintenance window, encrypted backups, admin password |

Every page has its own address (e.g. `…/index.html#benachrichtigung`). Unsaved changes are marked on their card;
rarely needed options are folded under “Advanced”. On a new installation a short assistant asks for language,
location and (optionally) Home Assistant and shows the TV address.

## 3. Typical tasks

### Show something different at night
TVs → *Schedule*: add a time range with another layout or “black”. A schedule always wins over the carousel.

### Rotate several layouts
TVs → *Carousel*: tick the layouts and set the minutes. Example: weather dashboard and photo layout every 5 minutes.

### Own pictures and videos instead of (or between) live cams
Media → upload JPG/PNG/MP4 (H.264)/WebM. Then TVs → *Video source*: “own media” or “mixed” (every N-th item own media).
H.265 videos are refused – convert them first, e.g. `ffmpeg -i in.mp4 -c:v libx264 -crf 20 -c:a aac out.mp4`.

### Severe weather warnings (Germany)
Layout → add the element **“Weather warning (DWD)”**. It shows the official warnings of the Deutscher Wetterdienst for
the configured location (Settings → General → Location), coloured by level (1 yellow, 2 orange, 3 red, 4 dark purple). Without a warning the element is hidden – or tick
“show also without warning”. The data are fetched every
10 minutes and only while a layout uses the element. Outside Germany there are no data.

### Put a short message on all TVs (webhook)
Settings → Notifications → *Message via webhook* → **Create new key**. The key is shown **only once** – store it, e.g. in a password
manager. Then any system in your network can send:

```sh
curl -X POST http://<IP>:8890/meldung \
  -H "Authorization: Bearer <key>" \
  -H "Content-Type: application/json" \
  -d '{"text": "The parcel service is at the door", "dauer": 120, "stil": "warnung"}'
```

| Field | Meaning |
|---|---|
| `text` | up to 300 characters; empty text removes the current message |
| `dauer` | seconds, 5 … 86400 (default 60) |
| `stil` | `info` (blue) or `warnung` (red) |
| `tv` | optional: only this TV (its id, e.g. `tv`); otherwise all TVs |

The banner lies above every layout (also above “black”) and appears within 15 seconds. Wrong keys are answered with
403 after a short delay; more than 20 requests per minute from one address get 429. Port: `SC_WEBHOOK_PORT`
(default 8890; Docker: publish it with `-p 8890:8890`).

Home Assistant example (`configuration.yaml`; the key belongs in `secrets.yaml`):

```yaml
rest_command:
  signagecast_meldung:
    url: "http://<IP>:8890/meldung"
    method: post
    headers:
      Authorization: !secret signagecast_webhook
    content_type: "application/json"
    payload: '{"text": "{{ text }}", "dauer": {{ dauer | default(60) }}, "stil": "{{ stil | default("info") }}"}'
```

with `signagecast_webhook: "Bearer <key>"` in `secrets.yaml`, and in an automation:
`action: rest_command.signagecast_meldung` with `data: {text: "Doorbell", stil: warnung}`.

### Announcements from the reception
Settings → Announcements: download a voice (Kerstin or Thorsten, once), add an account with a password and tick the
TVs it may reach. At the reception open `http://<IP>:8890/pult`, log in, choose TVs, click a template (the first “…”
is selected – type the name), tick “read aloud” and send. The call appears in the middle of the screen and is read
after a chime; because of the stream it takes about 6–10 seconds. Names are not stored (memory only, 2 hours).
TVs reachable by a panel account record real sound so that announcements can be heard.

### Show a web page that forbids embedding
Many sites (news, dashboards, timetables) refuse to be embedded – the *Check* button in the layout editor tells you.
Set the web page element's **Display** to **Screenshot**: SignageCast loads the page itself and shows a fresh picture
every *reload* minutes (0 = hourly). Zoom and crop work as with live pages. Limits: no motion or video, no login, and
cookie banners stay visible – pick a page or a direct sub-page without a banner if possible. Each picture costs about
2–5 seconds of CPU for Chromium, so intervals of 5 minutes or more are sensible.

### Show a PDF (price list, menu, presentation)
Add the element **PDF (page by page)** and upload the file (up to 50 pages; export PowerPoint or Word as PDF first).
SignageCast converts every page into a picture once; the element shows them one after another, *seconds per page*
apart. Pages change by the clock, so several TVs turn pages together. *Fit* shows the whole page, *fill* crops it. A new
upload replaces the file in this element only – save the layout afterwards.

### Show something only for a while
Every element has **Only during …** with *from* and *until* (date, optionally a time). Without a time the whole day
counts: from 2026-12-23 until 2027-01-02 shows the text from the morning of 23 December to the end of 2 January. The
editor marks such elements with ⏱. Combine it with a condition if needed (both must apply).

### Emergency screen
Settings → Announcements → **Emergency screen**: enter templates (the first is used from the admin and the webhook),
optionally a warning tone, then *Trigger now* (all TVs or one) and *End*. It shows the text in red across the whole
screen above every layout – also during “black” – and stays until someone ends it, even across a restart. Panel
accounts with **may trigger the emergency screen** get a red section in the panel. By webhook (key from “Message via
webhook”):

```bash
curl -X POST http://<IP>:8890/alarm -H "Authorization: Bearer <key>" -H "Content-Type: application/json" -d '{"text": "Please leave the building."}'
curl -X POST http://<IP>:8890/alarm -H "Authorization: Bearer <key>" -d '{"aus": true}'      # end
```

The warning tone is audible only on TVs that record sound (sound on, or reachable by a panel account with read-aloud).
An emergency screen is an additional notice, not a replacement for a certified alarm system.

### Really switch TVs off at night
TVs → **Switch via HA**: enter the TV's entity in Home Assistant (`media_player.…`, `switch.…` for a smart plug, or
`remote.…`), save, try *Off (test)* and *On (test)*. From then on the TV is switched off when “black” starts in its
schedule and on again when it ends or an emergency screen comes – only at that moment, so a TV switched on by hand at
night stays on. Switching on works only if Home Assistant can do it (Samsung and LG usually need Wake-on-LAN in their
integration; a smart plug works with TVs that start on power). After switching on, the TV must open the SignageCast
address by itself (start page or autostart of its browser).

### Play on a Raspberry Pi at the TV

From 0.23 (experimental): **TVs → Players (Raspberry Pi)** creates a ready SD card image per screen (Wi-Fi included)
and manages all Pis – status, screenshot, TV on/off via HDMI-CEC, rotation, Wi-Fi change, updates. Step by step:
[Raspberry Pi as player](PLAYER.md). Pi 3 and Zero 2 W need the TV on H.264 / Full HD.

### Output and capture size
TVs → **Video stream**, per TV:

| Setting | Values | Meaning |
|---|---|---|
| **Output** | **Full HD** (default since 0.29) · 4K | Size of the stream the TV receives. The page is drawn at the capture size anyway – a 4K TV upscales Full HD itself, so Full HD saves bitrate and graphics work without visible loss in most cases. 4K needs a TV that plays H.265. |
| **Capture (browser)** | 720p · **1080p** · 1440p | Size in which the browser draws the TV page (the layout stays 1920 × 1080 points and is only rasterised coarser or finer). 720p saves CPU and fetches live videos in 720p; 1440p is sharper for text on a 4K output but needs clearly more CPU. More than the output brings nothing. A change briefly restarts the stream. |

### Choose the encoder (advanced)
TVs → **Video stream** → **Encoding (advanced)**, per TV. Normally leave everything on *Automatic*. Every option has an
explanation in the admin; in short:

| Setting | Values | Meaning |
|---|---|---|
| **Encoder** | Automatic · Intel/AMD graphics (VAAPI) · Intel Quick Sync (QSV) · NVIDIA NVENC (experimental) · Software (libx264) | Automatic = VAAPI, without usable graphics software. QSV needs Intel graphics of the 11th/12th generation or newer (e.g. N100); NVENC needs an NVIDIA card with driver passed into the container – untested. Software: H.264, Full HD, at most 8 Mbit/s, about 1–2 cores per TV. |
| **Preset** | ultrafast · superfast · **veryfast** · fast · medium | Slower = nicer picture at the same bitrate, but more computing time. Software uses the names directly, QSV and NVENC get their matching level (NVENC p1–p5). VAAPI has no presets. |
| **Tune** | **zerolatency** · none | zerolatency = low delay (recommended for live pictures). VAAPI ignores it. |
| **B-frames** | **0**–4 | Save about 5–15 % data but add delay; some TV browsers stutter. 0 is the safe choice. |

Encoders that do not work on this computer are greyed out with the reason. Before a changed setting is used,
SignageCast encodes one second as a test; if that fails, the TV stays on *Automatic* and the TV page says why. Saving
restarts the stream of that TV (a few seconds black). Then check **System → Performance**: a speed below 1.0× means the
setting is too heavy (measured on an i5-7500T: software *medium* without tune ran at only 0.73× real time).

### Get notified when something breaks
Settings → Notifications. Channels (any combination):

- **Telegram:** create a bot with @BotFather, copy the bot token; send the bot a message and read your chat id, e.g.
  from `https://api.telegram.org/bot<token>/getUpdates`. Group chats have negative ids.
- **E-mail (SMTP):** server, port, encryption (STARTTLS on 587, SSL on 465), user/password, sender and recipients.
- **Home Assistant:** uses the existing connection and calls a notify service, e.g. `notify.mobile_app_<phone>`.

Each channel has a **Test message** button (it saves first). Events: a TV fails (render chain incomplete for two
minutes), an update fails or was rolled back, the automatic backup fails, Home Assistant is unreachable for more than
5 minutes. Every event is sent once, plus an all-clear when it is over. The bot token and the SMTP password are shown as
•••• and are not part of a backup unless you include secrets.

## 4. FAQ

**The TV shows nothing / “connecting” forever.**
Open `http://<IP>:8888/<tv>` in a desktop browser first. If that works, the TV's browser or player is the issue. If not:
Overview shows whether the render chain runs; the first start takes 10–20 seconds.

**Sound is missing.**
Browsers block autoplay with sound until you interact once. Click/press OK once on the TV, or use a player app.

**Which TV address do I use in Home Assistant?**
The same HLS address, e.g. in a media player card or with `media_player.play_media` and content type `video`.

**Can I use a Raspberry Pi as server?**
Not recommended – rendering and encoding need an x86 CPU with Intel/AMD graphics (see [hardware](HARDWARE.md)).
A Pi is fine as the *player* that opens the stream.

**Why does a live stream disappear from the list?**
Streams that stall, deliver only low resolution or cannot be embedded get strikes and are skipped. Protect favourites
in the Streams tab; rejected ones stay rejected. The Streams tab shows each stream's state – filter by *night* (with
“daylight in …”), *not live*, *resolution too low*, *paused after strike* or *location unknown* to see why. Night
streams come back on their own at daylight; streams without a location never run until you enter it (Edit).

**Why does the next stream not get skipped any more?**
The TV tells the data service which streams come next; they are checked on YouTube in advance (live, embeddable,
offered resolution). Only checked streams are announced, so “Next: …” is what comes.

**Is anything sent to the internet?**
Only what you configure: YouTube (official embed player), weather (MET Norway), DWD warnings, radio, your own data
sources, GitHub for update checks, and your notification channels. No telemetry.

**How do I move to new hardware?**
Backup tab → create a backup (with secrets if you want credentials to move along – then it is AES-256 encrypted),
install SignageCast on the new machine with `SC_SICHERUNG=<file> SC_SICHERUNG_PASSWORT=… sh install.sh` or restore in
the admin.

**The webhook answers 403 although the key is right.**
Is “Accept messages” ticked? A new key replaces the old one immediately. With `?token=` in the URL, special characters
must not be changed by the sending tool – prefer the `Authorization` header.

**I lost the webhook key.**
It is never shown again. Create a new one and update the senders.

---

## Deutsch (kurz)

Seit 0.23 (experimentell): **Raspberry Pi als Player** unter Fernseher → Player – fertiges Image je Bildschirm mit WLAN,
zentrale Verwaltung; Anleitung in [PLAYER.md](PLAYER.md#deutsch-raspberry-pi-als-player).

Das Handbuch erklärt den Alltag: Zeitplan und Karussell je Fernseher, eigene Medien (H.264, kein H.265),
**Webseiten als Bildschirmfoto** (Baustein „Webseite“ → Darstellung „Bildschirmfoto“ für Seiten, die das Einbetten
verbieten; Foto alle *n* Minuten, ohne Anmeldung, Cookie-Hinweise bleiben sichtbar),
**Unwetterwarnungen des DWD** als Layout-Baustein (Stufenfarben, nur Deutschland, Abruf alle 10 min nur bei Nutzung),
**Meldung per Webhook** (Schlüssel unter Einstellungen → Benachrichtigungen erzeugen – wird nur einmal angezeigt –, dann
`POST http://<IP>:8890/meldung` mit `Authorization: Bearer <Schlüssel>` und JSON `text`, `dauer`, `stil`, optional `tv`;
Beispiel für Home Assistant oben) und **Benachrichtigungen** über Telegram, E-Mail (SMTP) und Home Assistant bei
Ausfall eines Fernsehers, Update- oder Sicherungsfehler und getrenntem Home Assistant – je einmal, mit Entwarnung,
Test-Knopf je Kanal.
Seit 0.21: **PDF** als Baustein (bis 50 Seiten, blättert nach der Uhr), **Zeitraum** je Baustein
(„ab“/„bis“, ohne Uhrzeit der ganze Tag), **Notfall-Vollbild** (Einstellungen → Durchsage-Pult; im Pult für Zugänge mit
dem Recht dazu; Webhook `POST /alarm`, beenden mit `{"aus": true}`) und **Fernseher über Home Assistant schalten**
(Fernseher → „Über HA schalten“: bei „schwarz“ aus, danach wieder an – nur beim Wechsel).
Seit 0.22: **Kodierung je Fernseher** (Fernseher → Videostream → „Kodierung (für Fortgeschrittene)“): Encoder
(Automatisch, VAAPI, Intel Quick Sync ab 11./12. Generation, NVIDIA NVENC experimentell, Software libx264), Preset
(ultrafast bis medium, Standard veryfast), Tune (zerolatency oder keins) und B-Frames (0–4, Standard 0) – mit Erklärung
je Feld; was hier nicht geht, ist ausgegraut, jede Änderung wird vorher kurz probekodiert, sonst bleibt „Automatisch“.
Seit 0.29: **Ausgabe** Standard Full HD (ein 4K-Fernseher rechnet selbst hoch; spart Bitrate) und **Aufnahme (Browser)** je
Fernseher: 720p (spart CPU, Live-Videos in 720p), 1080p (Standard) oder 1440p (schärfer, deutlich mehr CPU) – das Layout
bleibt 1920 × 1080 Punkte. Danach FAQ zu Bild, Ton, Hardware, Datenschutz, Umzug und Webhook-Schlüssel.
