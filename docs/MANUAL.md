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
| **Overview** | – | To-do list (problems first, then tips; entries can be hidden), state of every TV, viewers, CPU/RAM, time check, Home Assistant |
| **TVs** | TVs · Players | Per TV in sections: display (layout, schedule, carousel, switch via HA), live video (on/off, video source, categories), sound; video stream technology folded; players at the TV – Raspberry Pi, PC or browser device ([PLAYER.md](PLAYER.md)) |
| **Content** | Layouts · Data sources · Media · Gallery · Clips · Radio · Announcements | Layout editor and templates, JSON APIs/feeds/iCal/CSV (also as uploaded file)/cameras, own pictures and videos, gallery folders (pictures/PDFs for slideshows), scheduled clips, radio stations, announcement panel, emergency screen and messages via webhook |
| **Live videos** | Streams · Categories · Rotation & quality · Search | Live cams; categories (edit, create, switch on/off for all TVs or per TV); minutes per stream, daylight, minimum quality and strikes; nightly search |
| **Settings** | General · Home Assistant · Notifications · Storage locations (· Access in Docker) | Language, weather, location, time source; HA address and guide; outgoing notifications via Telegram/e-mail/HA; NAS/cloud folders for all file dialogs; admin password |
| **System** | Updates · Backup · Storage · Performance · Log | Signed updates, maintenance window, encrypted backups, free space and what uses it, performance test, switching off the stream without viewers, change log |

Every page has its own address (e.g. `…/index.html#benachrichtigung`). Unsaved changes are marked on their card;
rarely needed options are folded under “Advanced”. On a new installation a short assistant asks for language,
location and (optionally) Home Assistant and shows the TV address.

## 3. Typical tasks

### More than animals: cities, beaches, space …
Live videos → Categories → **More topics**: cities & squares, beaches & coasts,
mountains & ski, harbours & ships, airports & planes, trains & railways, space & Earth, natural wonders. Each topic has
its own nightly search (only while it is switched on), sorts what it finds into its category and takes the location
from the title (daylight rule as for animals; space and northern lights ignore it). On an update new categories start
**switched off**, so your rotation does not change until you switch them on. Per TV you can switch categories off again
under TVs → Live video → Categories.

### Edit categories or create your own (since 0.37)
Live videos → **Categories** shows every category with the number of its streams and where it is switched off. Open
one to change:
- **Name** – empty keeps the built-in name (translated); own categories need one.
- **Group** – *Animals* or *More topics* (only decides where it is listed and which filters apply).
- **Switched on** – for all TVs and, with several TVs, per TV (the same switches as on the TV card).
- **Search terms** – up to 6, one per line; each is one YouTube request per nightly search. The search only runs while
  the category is switched on for all TVs. Animal categories can stay empty – the general animal search (Search page)
  fills them.
- **Words in the title** – one must appear in the title of a found stream (regular expressions allowed). For animals
  they also sort the finds of the general animal search: the first matching category wins, otherwise *Newly found*.
  When you save, found streams in *Newly found* are sorted again; a category you set by hand on a stream stays.
- **Ignore day/night** – for things without daylight like space; optionally only for certain words in the title
  (northern lights).

**New category** adds your own (e.g. lighthouses: search term `lighthouse live cam`, words `lighthouse`, `leuchtturm`).
Built-in categories can be **reset to default** but not deleted; unchanged ones follow improvements in updates. When you
delete your own category you choose where its streams go; it disappears from all TVs.

### Switch the TV on and off via Home Assistant
TVs → TV card → *Switch via HA*: the TV's entity (`media_player`, `switch` or `remote`). When “black” starts in the
schedule the TV is switched off, when it ends switched on again (also for the emergency screen). Since 0.37:
- the card and the overview show whether the TV is **on, off or unreachable** according to HA (asked once a minute);
- **after switching on** SignageCast waits until the TV is ready (up to 90 s) and can **select a source** (media_player,
  e.g. `HDMI 2` where the player is connected – “Get sources from HA” shows the names) and then **open the TV page**:
  *LG webOS* (opens the browser with the TV address, integration “LG webOS TV”), *Android TV / Google TV / Fire TV*
  (integration “Android TV” with ADB; a kiosk app as default browser works best) or an *own HA service* – its data is
  JSON, `{url}` becomes the TV address and `{entity}` the entity (e.g. a script for Samsung TVs, whose standard
  integration cannot open web addresses);
- “Run now (test)” runs this immediately while the TV is on.

### Show something different at night
TVs → *Schedule*: add a time range with another layout or “black”. A schedule always wins over the carousel.

### Rotate several layouts
TVs → *Carousel*: tick the layouts and set the minutes. Example: weather dashboard and photo layout every 5 minutes.

### Own pictures and videos instead of (or between) live cams
Media → upload JPG/PNG/MP4 (H.264)/WebM. Then TVs → *Video source*: “own media” or “mixed” (every N-th item own media).

### When the internet is gone (since 0.38)
Nothing to set up. If YouTube is not reachable (checked once a minute, two failures in a row), the video window shows
all your own media in a loop – upload a few calm pictures under *Media* for this – or, without media, a calm picture
matching the time of day. No error appears on the TV; streams get no strikes. Overview → *Internet* shows the state;
under Settings → Notifications the event *Internet not reachable* sends a message (via Home Assistant it arrives right
away, Telegram/e-mail usually only with the all-clear, which names the period).

### A TV shows only black or a frozen picture (since 0.38)
SignageCast checks every running TV every 2 minutes on a tiny grey copy of the captured picture. Black three times in a
row (unless the schedule says black) or no change three times in a row although the layout shows a clock: first the
TV page is reloaded; if it happens again the playback is restarted and a notification is sent (event *TV failure*).
Layouts without a clock may stand still (e.g. only text or a picture). TVs in direct mode (player shows the page
itself) are not checked this way.

### Undo a layout change, bring back a deleted layout (since 0.38)
Layout → ⋯ on the layout → *Versions*: the last 10 versions with time and user; *Restore* replaces the layout (the
current one becomes a version), *Download* saves one as file. Below the layouts, *Deleted layouts* brings back
deleted ones.

### Let an AI build a layout (since 0.38)
Layout → *Create with AI …* → *Copy instructions*. Paste them into an AI (ChatGPT, Claude, Gemini …), describe your wish
at the marked place (“MY WISH: …”), copy the answer, then Layout → *Paste text …* → *Apply*. SignageCast repairs what
it can and lists it (unknown elements, invalid values, pictures that are not here yet). Then open the layout, upload
pictures and choose Home Assistant entities. The format is described in [LAYOUT-FORMAT.md](LAYOUT-FORMAT.md) –
generated from the code, so it is always current.

### Let Claude manage the content (since 0.39)
SignageCast has an MCP server for AI assistants. Since 0.40: **Settings → AI assistants → Connect a computer** – for
Claude Desktop a file to double-click, for Claude Code, Cursor and VS Code a ready command or link. Each computer gets
its own access (*change content* or *only read*) that you can **remove** there at any time. Home network only.
Alternatively over SSH: `claude mcp add signagecast -- ssh -T tvadmin@<IP> signagecast-mcp`. The assistant can build
layouts, look at preview pictures, assign layouts and schedules, send tickers and announcements, upload pictures,
manage streams and data sources – not updates, backups, players or secrets. Details: [MCP.md](MCP.md).

### Who changed what? (since 0.38)
System → *Log*: every change in the admin (with the Cockpit user), at the announcement panel, via webhook and by
SignageCast itself (updates, picture check, internet outages). Only kind and area, never values – no passwords, no
announcement texts. The last 500 entries; part of the backup.
H.265 videos are refused – convert them first, e.g. `ffmpeg -i in.mp4 -c:v libx264 -crf 20 -c:a aac out.mp4`.

### Severe weather warnings (Germany)
Layout → add the element **“Weather warning (DWD)”**. It shows the official warnings of the Deutscher Wetterdienst for
the configured location (Settings → General → Location), coloured by level (1 yellow, 2 orange, 3 red, 4 dark purple). Without a warning the element is hidden – or tick
“show also without warning”. The data are fetched every
10 minutes and only while a layout uses the element. Outside Germany there are no data.

### Put a short message on all TVs (webhook)
Content → Announcements → *Message via webhook* → **Create new key**. The key is shown **only once** – store it, e.g. in a password
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
Content → Announcements: download a voice (Kerstin or Thorsten, once), add an account with a password and tick the
TVs it may reach. At the reception open `http://<IP>:8890/pult`, log in, choose TVs, click a template (the first “…”
is selected – type the name), tick “read aloud” and send. The call appears in the middle of the screen and is read
after a chime; because of the stream it takes about 6–10 seconds. Names are not stored (memory only, 2 hours).
TVs reachable by a panel account record real sound so that announcements can be heard.

Since 0.38 an account can get more rights (tick them at the account): **ticker message** (runs along the bottom of the
chosen TVs for 15 min – 12 h, optionally red), **switch layout for a while** (15 min – 12 h, before schedule and
carousel, switches back by itself) and **switch TVs on/off** via Home Assistant (TVs with a switch entity). The panel
shows what is currently set, with “switch back” / “end”. Every panel action is in the log (announcements without text).

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

### Show a folder of pictures (gallery, since 0.45)
**Content → Gallery:** create a folder (e.g. “Family”, “Notices”) and drag pictures (JPG, PNG, WebP, GIF) and PDFs into
it – or choose files or a whole folder; from a phone use the file picker (iPhone photos arrive as JPG). Photos are
scaled down to at most 3840 × 2160 when uploaded and only this version is kept; PDFs become one picture per page. Drag
thumbnails to change the order, tick several to delete them. Limits: 50 MB per photo, 100 MB per PDF, 1000 files per
folder, and the gallery limit (default 5 GB for all folders, adjustable on the same page).

In the layout add the element **Gallery (pictures/PDFs)** and choose the folder – or start from the template
**Galerie Vollbild** (full screen). Options: *seconds per picture* (3 s–60 min), *fit* (whole picture, border black or
the blurred picture behind) or *fill* (crop), order *as in the folder*, *by name*, *newest first* or *random* (new
shuffle every round), change *cross-fade* or *cut*. Pictures change by the clock, so all TVs show the same picture; new
pictures appear without saving the layout. A folder can also be the **background** of a layout (Background → “Gallery
folder (slideshow)”). The pictures stay on this server only and are **not part of the backup** (the folder names
are) – keep your originals.

### Storage guard (since 0.45)
SignageCast never fills its disk. A reserve of **2 GB or 10 % of the disk** (whichever is more) always stays free for
streams, logs and automatic backups. Uploads (gallery, media, PDFs, pictures, backups to restore) are checked
**before** anything is transferred – the announced size has to fit above the reserve – and again for every chunk.
**System → Storage** shows free space and what uses it (gallery, media, backups, clip cache …) with links to clean up.
Below twice the reserve the to-do list and notifications (event “Storage getting low or full”) warn; at the reserve
uploads and the clip cache stop, everything already there keeps running.

### Pictures and files from a NAS or cloud (storage locations, since 0.48)
**Settings → Storage locations:** add a **WebDAV** address (Nextcloud/ownCloud: Files → Settings → WebDAV; best with an
app password), an **SMB** share (`smb://nas/share/folder`, SMB3 only, best a read-only account) or a **folder on the
server** (below `/mnt`, `/media`, `/srv`; in Docker mount a volume to `/speicherorte`, see `compose.yaml`). On Proxmox
you can mount the NAS on the host and pass it read-only into the container
(`pct set <ID> -mp0 /mnt/pve/nas,mp=/mnt/nas,ro=1`) – then SignageCast needs no password at all. *Test connection*
lists the folder (and, with write permission, writes and deletes a small test file). Locations are read-only unless you
tick *Allow writing* (only needed for backups).

Afterwards every file field in the admin has a **From storage location** button: browse the folders and pick one or
several files. Gallery pictures, media and backups to restore are fetched by the server itself; other files (CSV,
playlist, layout, background picture, PDF up to 25 MB) run through the normal import. In **Content → Gallery** a folder
can be **linked** to a folder of a location: new and changed pictures arrive by themselves (every 5–1440 minutes or
*Sync now*), deleted ones disappear (can be switched off), the order follows the file names; pictures you upload by hand
stay. A **data source** can read its file from a location on every fetch (origin *File from storage location*). Under
**System → Backup** the automatic backup can also be stored in a location with write permission (experimental). If a
location cannot be reached, nothing is deleted and *To do* shows it. Passwords are never shown again, are not part of
backups and never reach the log – after restoring a backup on a new server, enter the locations again.

### Show something only for a while
Every element has **Only during …** with *from* and *until* (date, optionally a time). Without a time the whole day
counts: from 2026-12-23 until 2027-01-02 shows the text from the morning of 23 December to the end of 2 January. The
editor marks such elements with ⏱. Combine it with a condition if needed (both must apply).

### Emergency screen
Content → Announcements → **Emergency screen**: enter templates (the first is used from the admin and the webhook),
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

From 0.23 (experimental): **TVs → Set up** creates a ready SD card image per screen (Wi-Fi included);
**TVs → Devices** manages all Pis – status, screenshot, TV on/off via HDMI-CEC, rotation, Wi-Fi change, updates. Step by step:
[Raspberry Pi as player](PLAYER.md). Pi 3 and Zero 2 W need the TV on H.264 / Full HD.
Since 0.33 a Pi that allows it opens a **terminal** (root shell in the browser) from its card – off by default,
see [Remote maintenance](PLAYER.md#remote-maintenance--terminal-in-the-browser-since-033).
Since 0.41 a player can stand **at another site** and reach SignageCast through Tailscale or Headscale
(*Settings → Remote sites*, then tick *At another site* for its image) – see [REMOTE.md](REMOTE.md).

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

### Hide an entry in the to-do list
Overview → *To do*: the **✕** next to an entry hides it without fixing it. How long depends on the kind of entry:

- **Tips** (automatic backup off, no notification, video in software): for good, until you show them again.
- **New version available:** only for this version – the next one appears again.
- **Problems** (player not responding, Home Assistant or weather not reachable, TV stutters, backup or notification
  failed): until the problem was solved once. If it comes back later, it shows again. For players this applies per Pi.

“*n* hidden – show” below the list shows the hidden entries with a **Show again** button. *Change the initial password*
(Docker) cannot be hidden. Hiding only affects the list – notifications are still sent. The hidden entries are kept on
the server (`/var/lib/signagecast/todo.json`, valid for every browser and account) and are part of backups.

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

Seit 0.23 (experimentell): **Raspberry Pi als Player** unter Fernseher → Einrichten – fertiges Image je Bildschirm mit WLAN,
zentrale Verwaltung unter Fernseher → Geräte; Anleitung in [PLAYER.md](PLAYER.md#deutsch-raspberry-pi-als-player).
Seit 0.41 auch **an anderen Standorten** über Tailscale oder Headscale (Einstellungen → Fernstandorte, beim Image
„An einem anderen Standort“) – [REMOTE.md](REMOTE.md#deutsch-kurz).

Seit 0.35: Einträge in **Zu erledigen** (Übersicht) mit **✕** ausblenden, ohne sie zu erledigen – Tipps dauerhaft, „Neue Version“ nur für diese Version, Probleme bis sie einmal behoben waren (tritt es wieder auf, erscheint es wieder). „Startpasswort ändern“ lässt sich nicht ausblenden; Benachrichtigungen kommen weiter.

Seit 0.32: **Themen ohne Tiere** – Städte, Strände, Berge, Häfen, Flughäfen, Bahn, Weltraum, Naturschauspiele (Live-Videos → Kategorien → *Weitere Themen*); eigene Suche je Thema, beim Update zunächst ausgeschaltet.

Seit 0.37: **Kategorien bearbeiten und eigene anlegen** unter Live-Videos → **Kategorien**: Name, Gruppe, bis zu 6 Suchbegriffe (je eine YouTube-Anfrage pro Suchlauf), Wörter im Titel, Tag/Nacht egal, ein-/ausschalten für alle Fernseher oder je Fernseher, Zahl der Streams. Gefundene Tier-Streams landen über die Wörter in der passenden Kategorie statt in „Neu gefunden“. Eingebaute lassen sich auf den Standard zurücksetzen (unveränderte folgen Verbesserungen per Update), eigene löschen – ihre Streams wandern in eine Kategorie deiner Wahl.

Seit 0.38: **Internet weg** – das Videofenster zeigt eigene Medien im Kreis (ohne Medien ein ruhiges Bild zur
Tageszeit) statt Schwarz oder Fehler, keine Strikes; Kachel *Internet* in der Übersicht, Ereignis „Internet nicht
erreichbar“ (die Entwarnung nennt den Zeitraum). **Bildprüfung** – alle 2 min ein Miniaturbild je laufendem Fernseher:
schwarz oder (mit sichtbarer Uhr) stehend, dreimal hintereinander → TV-Seite neu laden, beim nächsten Mal Wiedergabe neu
starten und melden. **Änderungsprotokoll** (System → Protokoll: wer, wann, was – nie Werte), **Layout-Versionen**
(⋯ → Versionen, die letzten 10, auch gelöschte Layouts) und **Layout mit KI bauen** (Layout → „Mit KI erstellen …“ →
Anleitung kopieren, Antwort mit „Text einfügen …“ übernehmen; der Import repariert und nennt jede Änderung; Format in
[LAYOUT-FORMAT.md](LAYOUT-FORMAT.md)). **Pult-Rechte** je Zugang: Laufschrift-Meldung, Layout vorübergehend
umschalten, Fernseher über HA ein/aus.

Seit 0.39: **MCP-Schnittstelle** für Claude & Co.: Layouts bauen, Vorschaubild, Zuweisung, Zeitplan, Laufschrift,
Durchsage, Bilder, Streams, Datenquellen; nichts am System. Seit 0.40 per Klick: Einstellungen → **KI-Assistenten** →
*Computer verbinden* (Claude Desktop: Datei zum Doppelklicken; Claude Code, Cursor, VS Code: Befehl/Link); jeder
Computer lässt sich dort wieder **entfernen**. Weiter auch per SSH (`ssh -T tvadmin@<IP> signagecast-mcp`). Anleitung:
[MCP.md](MCP.md#deutsch-kurz).

Das Handbuch erklärt den Alltag: Zeitplan und Karussell je Fernseher, eigene Medien (H.264, kein H.265),
**Webseiten als Bildschirmfoto** (Baustein „Webseite“ → Darstellung „Bildschirmfoto“ für Seiten, die das Einbetten
verbieten; Foto alle *n* Minuten, ohne Anmeldung, Cookie-Hinweise bleiben sichtbar),
**Unwetterwarnungen des DWD** als Layout-Baustein (Stufenfarben, nur Deutschland, Abruf alle 10 min nur bei Nutzung),
**Meldung per Webhook** (Schlüssel unter Inhalte → Durchsagen erzeugen – wird nur einmal angezeigt –, dann
`POST http://<IP>:8890/meldung` mit `Authorization: Bearer <Schlüssel>` und JSON `text`, `dauer`, `stil`, optional `tv`;
Beispiel für Home Assistant oben) und **Benachrichtigungen** über Telegram, E-Mail (SMTP) und Home Assistant bei
Ausfall eines Fernsehers, Update- oder Sicherungsfehler und getrenntem Home Assistant – je einmal, mit Entwarnung,
Test-Knopf je Kanal.
Seit 0.45: **Galerie** – Inhalte → Galerie: Ordner anlegen, Bilder (JPG, PNG, WebP, GIF) und PDFs hineinziehen oder
auswählen (auch ganze Ordner, vom Handy über die Dateiauswahl). Fotos werden beim Hochladen auf höchstens 4K
verkleinert, nur diese Fassung bleibt; Reihenfolge per Ziehen, mehrere auswählen und löschen. Im Layout der Baustein
**Galerie** (oder die Vorlage „Galerie Vollbild“): Sekunden je Bild, einpassen (Rand schwarz oder unscharf) oder
füllen, Reihenfolge wie im Ordner/Name/neueste/zufällig, überblenden oder direkt – alle Fernseher zeigen dasselbe Bild.
Auch als **Hintergrund-Diashow**. Die Bilder kommen nicht in die Sicherung (die Ordnernamen schon).
**Speicherwächter**: Reserve von 2 GB bzw. 10 % der Platte bleibt immer frei; Uploads werden schon vor dem Übertragen
abgelehnt, wenn sie nicht passen. **System → Speicher** zeigt, was wie viel belegt; bei wenig Platz Hinweis unter
„Zu erledigen“ und Benachrichtigung, ist die Reserve erreicht, sind Uploads gesperrt – alles andere läuft weiter.
Seit 0.48: **Speicherorte** – Einstellungen → Speicherorte: WebDAV (Nextcloud, ownCloud, NAS), SMB (nur SMB3) oder ein
Ordner auf dem Server (unter /mnt, /media, /srv; Docker: Volume nach /speicherorte) einmal eintragen, standardmäßig nur
lesend. Danach hat jedes Dateifeld den Knopf **Aus Speicherort**. Galerie-Ordner lassen sich mit einem Ordner
**verknüpfen** (neue/geänderte Bilder kommen von selbst, gelöschte gehen, von Hand hochgeladene bleiben),
Datenquellen lesen ihre Datei bei jedem Abruf aus dem Speicherort, und die automatische Sicherung kann zusätzlich in
einen Speicherort mit Schreibrecht (experimentell). Passwörter bleiben nur auf dem Server (nicht in Sicherungen).
Seit 0.21: **PDF** als Baustein (bis 50 Seiten, blättert nach der Uhr), **Zeitraum** je Baustein
(„ab“/„bis“, ohne Uhrzeit der ganze Tag), **Notfall-Vollbild** (Inhalte → Durchsagen; im Pult für Zugänge mit
dem Recht dazu; Webhook `POST /alarm`, beenden mit `{"aus": true}`) und **Fernseher über Home Assistant schalten**
(Fernseher → „Über HA schalten“: bei „schwarz“ aus, danach wieder an – nur beim Wechsel).
Seit 0.22: **Kodierung je Fernseher** (Fernseher → Videostream → „Kodierung (für Fortgeschrittene)“): Encoder
(Automatisch, VAAPI, Intel Quick Sync ab 11./12. Generation, NVIDIA NVENC experimentell, Software libx264), Preset
(ultrafast bis medium, Standard veryfast), Tune (zerolatency oder keins) und B-Frames (0–4, Standard 0) – mit Erklärung
je Feld; was hier nicht geht, ist ausgegraut, jede Änderung wird vorher kurz probekodiert, sonst bleibt „Automatisch“.
Seit 0.29: **Ausgabe** Standard Full HD (ein 4K-Fernseher rechnet selbst hoch; spart Bitrate) und **Aufnahme (Browser)** je
Fernseher: 720p (spart CPU, Live-Videos in 720p), 1080p (Standard) oder 1440p (schärfer, deutlich mehr CPU) – das Layout
bleibt 1920 × 1080 Punkte. Danach FAQ zu Bild, Ton, Hardware, Datenschutz, Umzug und Webhook-Schlüssel.
