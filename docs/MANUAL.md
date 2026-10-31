# SignageCast – manual and FAQ

[← back to the README](../README.md) · [screenshot tour](TOUR.md)

This manual explains the daily use of SignageCast. Installation is described in the README.

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
| **TVs** | – | Address, layout, schedule, carousel, sound, video source (YouTube / own media / mixed), quality |
| **Content** | Layouts · Data sources · Media · Clips | Layout editor and templates, JSON APIs/feeds/iCal/cameras, own pictures and videos, scheduled clips |
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
Not recommended – rendering and encoding need an x86 CPU with Intel/AMD graphics (see README, Hardware).
A Pi is fine as the *player* that opens the stream.

**Why does a live stream disappear from the list?**
Streams that stall, deliver only low resolution or cannot be embedded get strikes and are skipped. Protect favourites
in the Streams tab; rejected ones stay rejected.

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

Das Handbuch erklärt den Alltag: Zeitplan und Karussell je Fernseher, eigene Medien (H.264, kein H.265),
**Unwetterwarnungen des DWD** als Layout-Baustein (Stufenfarben, nur Deutschland, Abruf alle 10 min nur bei Nutzung),
**Meldung per Webhook** (Schlüssel unter Einstellungen → Benachrichtigungen erzeugen – wird nur einmal angezeigt –, dann
`POST http://<IP>:8890/meldung` mit `Authorization: Bearer <Schlüssel>` und JSON `text`, `dauer`, `stil`, optional `tv`;
Beispiel für Home Assistant oben) und **Benachrichtigungen** über Telegram, E-Mail (SMTP) und Home Assistant bei
Ausfall eines Fernsehers, Update- oder Sicherungsfehler und getrenntem Home Assistant – je einmal, mit Entwarnung,
Test-Knopf je Kanal. Danach FAQ zu Bild, Ton, Hardware, Datenschutz, Umzug und Webhook-Schlüssel.
