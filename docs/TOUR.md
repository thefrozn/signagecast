# SignageCast – tour

A walk through SignageCast: what the TV shows and how you set it up in the browser. All pictures are from a demo
installation (location Berlin, public example data, no Home Assistant connected). The admin pictures show version
0.68: the menu lists the things you manage – Overview, Channels, Devices, Layouts, Data sources, Media, Live videos,
Radio stations – with **Settings** as tiles at the right end and the **📢 Announcement** and **⚠ Emergency** buttons at
the top right ([UI rules](UI-RULES.md)).

**🇩🇪 [Deutsche Version mit deutschen Bildern](TOUR.de.md)**

**🎬 Videos:** [SignageCast in 45 seconds](https://github.com/thefrozn/signagecast/releases/download/demo-videos/signagecast-demo-short-en.mp4) · [full walkthrough, 3:24](https://github.com/thefrozn/signagecast/releases/download/demo-videos/signagecast-demo-long-en.mp4) (AI voice, subtitles)

[← README](../README.md) · [live demo](https://thefrozn.github.io/signagecast/?sprache=en) · [installation](INSTALL.md) · [manual](MANUAL.md) · [how it works](HOW-IT-WORKS.md)

---

## On the TV

### 1. Live window to the world
A live wildlife cam from wherever it is daytime right now, with clock, weather from MET Norway and the forecast.
The bar below mixes your own data: the Rhine water level and the Bitcoin price from public APIs, and a countdown.

![TV with live cam, weather and own data](tour/01-tv-living-room.jpg)

The same TV with the *Calendar / waste collection* element as **icons only** in the top right corner: residual waste
and recycling are collected tomorrow (example data from a CSV file). The icons appear three days before the pickup and
disappear afterwards by themselves.

![TV with waste collection icons in the corner](tour/01a-tv-waste-icons.jpg)

### 2. Data dashboard
A second TV with a layout built only from data sources: API value, gauge as bar and traffic light, a 24-hour chart
(real measurements of the Rhine at Cologne), public holidays from an iCal calendar, a feed list and the same feed as
ticker, a QR code and a countdown. Background: city picture set by time of day (here: night).

![Data dashboard on the TV](tour/02-tv-data-dashboard.jpg)

### 3. Service desk with PDF, web page and period
A reception layout: a **PDF** (price list and opening hours, the pages change by the clock), a **web page as
screenshot** – GitHub forbids embedding, so SignageCast loads the page itself and shows a fresh picture every 30 minutes
– and a notice with a **period**: “Closed from 24 December …” appears on 1 November and disappears by itself.

![Service desk layout with PDF, web page screenshot and holiday notice](tour/02a-tv-service-desk.jpg)

### 4. Emergency screen
One click in the admin, from the announcement panel or by webhook: a red full screen with your text above every
layout, also at night (“black”), optionally with a warning tone every 10 seconds.

![Emergency screen on the TV](tour/02b-tv-emergency.jpg)

---

## The admin page

### 5. Inside Cockpit
On Proxmox LXC and native Debian installations the admin is a Cockpit extension – “SignageCast” is just a menu entry
next to Cockpit's own pages. If your server already runs Cockpit, SignageCast integrates there.

![SignageCast as a menu entry in Cockpit](tour/03-cockpit.jpg)

### 6. Overview
At the top a **to-do list**: problems first (e.g. Home Assistant not reachable), then tips (automatic backup off, no
notification set up) – each entry links to the page where you fix it; the ✕ hides it (tips for good, problems until they were
solved once, since 0.35). Below, every channel with its state, current live video,
resolution and sound, then viewers, weather source, time check against NTP (“time from the host, synchronised”), video
encoding (graphics unit or software fallback), Home Assistant connection, live videos in rotation, CPU, RAM and uptime.
Since 0.38 a tile shows whether the **internet** is reachable (without it the TVs show own media or a calm picture),
and a channel card says when the **picture check** found a black or frozen picture.

![Overview](tour/04-overview.jpg)

### 7. Channels
A **channel** is what a TV shows – with its own address that a device or the TV's browser opens. The list is a table:
per channel its state in plain words with the layout, which devices show it (online or offline) and the last change,
with a search field and *+ New channel* at the top right.

![Channels as a table](tour/05-tvs.jpg)

*Open* shows one channel with tabs in a fixed order: **Overview** (state, current live video, sound, devices, the
address and quick actions *Reload TV page*, *Restart stream* and a fresh picture of this channel), **Display &
schedule**, **Live video**, **Sound**, **Video stream** and **History** (what happened to exactly this channel). *Delete*
is at the bottom and says where the channel is still used.

![A channel: overview with quick actions](tour/05f-channel.jpg)

**Display & schedule** holds the layout, an optional schedule with another layout or black at certain times, the
layout carousel and – since 0.66 in the same tab – *On/off via Home Assistant* (switching, state according to HA, after
switching on select a source and open the TV page). **Video stream** sets output Full HD or 4K, capture size, bitrate
and codec; each channel is saved on its own.

![Display & schedule with schedule, carousel and on/off via HA](tour/05h-channel-schedule.jpg)

In the *Video stream* tab → **Encoding (advanced)**: encoder (Automatic, Intel/AMD graphics, Quick Sync, NVENC, software),
preset, tune and B-frames per channel. A change is tried briefly first; if it does not work here, SignageCast stays with
“Automatic”.

![Encoding settings per channel](tour/05a-encoding.jpg)

### 8. Devices – Raspberry Pi, PC or browser (experimental)
A **device** at the TV shows a channel – also on TVs without a usable browser. *+ New device* → *Add device*: enter a
name, pick the channel, the **model** and the network (LAN or Wi-Fi), download a ready image and write it to an SD card
or USB stick; nothing to type at the device. Or download one image for many devices: each shows a 6-digit code on the
TV, which you enter under *Pair devices*.

- **Raspberry Pi** – plays the finished stream via HDMI; 1 GB of memory is enough for that. In direct mode (the Pi shows
  the page itself, no encoding on the server) it needs at least 2 GB, better 4 GB.
- **PC** (since 0.36) – an ordinary PC, mini PC or thin client (x86-64 with UEFI, Secure Boot may stay on) starts from a
  USB stick without touching its disk and shows the page itself in direct mode.
- **Browser device** (since 0.36) – no image at all, just a secret link for a smart TV, a Fire TV stick or a kiosk
  browser.

![Adding a PC: model and image format](tour/05d-new-player.jpg)

The device list shows every device with its state in plain words (“online”, “offline since …”), its channel and the
last change. *Open* shows the tabs **Overview** (state, screenshot, model, IP, screen, temperature and commands such as
*Restart playback*, TV on/off via HDMI-CEC or system update), **Remote management** (what was sent to the device and
when it was picked up), **Settings** (name, channel, model, rotation, direct mode, Wi-Fi, new image) and **History**;
*Remove* is at the bottom. The devices in these pictures are simulated (real agent code) ([details](PLAYER.md)).

![Devices as a table](tour/05b-players.jpg)

![A PC in direct mode: overview with commands](tour/05i-device.jpg)

![Browser device with its secret link](tour/05e-browser-device.jpg)

### 9. Remote maintenance – terminal to a Pi (experimental, since 0.33)
**Terminal** in the Pi's *Overview* tab opens a root shell in the browser, drawn like Cockpit's own terminal. Off by default:
the Pi itself must allow it (box when creating the image, or its setup page), so someone who takes over the server
cannot reach Pis that do not. No open port and no SSH on the Pi; input and output are encrypted. The TV shows
*Remote maintenance active* meanwhile, and a session ends after 10 minutes without input or 60 minutes at the latest.

![Terminal to a Raspberry Pi in the browser](tour/05c-remote-terminal.jpg)

### 10. Layouts and editor
Layouts starts with all layouts as tiles – mini preview, on which channel each one is shown and the last change, with a
search field and *+ New layout* at the top right. “New layout” asks for a name and a starting point (empty, template or
copy), so an existing layout is never overwritten.

![Layouts as tiles](tour/06a-layouts.jpg)

An open layout has the tabs **Overview** (preview, where it is used – channel, schedule, carousel –, number of elements,
copy, export, versions), **Designer** (opens first) and **History**; *Delete* is at the bottom and stays locked while a
channel uses the layout.

![A layout's overview tab](tour/06e-layout-overview.jpg)

In the editor, drag and resize elements on a 48 × 27 grid. Next to it the **layers** (top = front, as on the TV; show
or hide, bring forward / send backward) and the selected element – here a chart: pick the value with “pick …” by
clicking it in the data source's response. Click the same spot again to reach stacked elements, Tab selects the next one.

![Layout editor with layers and a chart element](tour/06-layout-editor.jpg)

Every element can be limited to a **period** (“Only during …”: date, optionally with time) – the ⏱ in the layers and on
the canvas marks it. Elements such as **PDF** (up to 50 pages) and **web page** with the display “Screenshot” for pages
that forbid embedding make layouts like the service desk above.

![Layout editor: text with a period](tour/06b-editor-period.jpg)

Since 0.59 the panel on the right has the tabs **Element** (with *Content*, *Look* and *When* and an ⓘ help per
field) and **Layout** (background, colours, font), and *Zoom* shows the canvas up to 200 %.

Since 0.58 **+ Element** opens a bar with all elements in groups – click one and it lands on a free spot, or drag it
onto the canvas. **Shift+click** or a frame dragged on an empty part of the canvas selects several elements: move them
together, align or distribute them evenly, duplicate (Ctrl+D) or remove them; Ctrl+Z / Ctrl+Y undo and redo. A **⚠**
marks what the live preview finds hard to read: small text from 3 m, low contrast, content that does not fit, covered
elements or more than one live video.

![Layout editor: elements bar and three elements selected](tour/06d-editor-multi.jpg)

Since 0.38 **“Create with AI …”** copies instructions with the complete layout format: paste them into ChatGPT, Claude
or Gemini, describe your wish, and apply the answer with **“Paste text …”** – SignageCast repairs what it can and lists
it. In the “⋯” menu, **Versions** keeps the last 10 versions of every layout (restore or download), and *Deleted
layouts* below the tiles brings back deleted ones.

![Layouts with the AI instructions](tour/06c-layout-ai.jpg)

### 11. Data sources
Your own JSON APIs, RSS/Atom feeds, pictures, iCal calendars, tables (CSV) and cameras, fetched by the container at the
interval you choose. Since 0.57 the page is a **list**: per source its type, origin, interval, **in which layouts it is
used**, its **last value** and a light – up to date, waiting for the first fetch or the error in plain words. A click
opens the details on the right: state, *Used in*, *View values* – tap a value to get its path for elements and the
placeholder for free text –, the settings, the *History* of this source and *Delete* at the bottom.

![Data sources: list and a source with its values](tour/07-data-sources.jpg)

**+ Add data source** leads in three steps: **What?** (tiles for news, value from the web, calendar, table, picture,
camera, text – or an example), **Where from?** (address, uploaded file up to 1 MB or a file in a storage location, how
often) and **Values** (*Test*, then tap the value you need). Technical fields – identifier, method, headers – are under
*Advanced*.

![Assistant for a new data source](tour/07b-data-assistant.jpg)

For CSV you choose delimiter, quote character, header row and character set (all detected automatically), which columns
to import under which name, optional row filters and optionally a date column: the rows then appear as events in the
*Calendar / waste collection* element. Here a waste calendar with the row filter *DISTRICT is empty* – it drops the
bulky and hazardous waste dates of another district.

![CSV import with row filter and calendar columns](tour/07a-csv-import.jpg)

### 12. Import from curl
⋯ → *Import from a curl command …*: paste a `curl` command from an API guide – address, method and headers are filled
in, `Authorization` is marked as a secret automatically (shown as •••• after saving, kept out of backups unless you
choose otherwise). The command is only parsed, never executed.

![Data source created from a curl command](tour/08-curl-import.jpg)

### 13. Live videos – collection
Live cams from YouTube for the video window, found automatically and shown only where it is daytime. Live videos →
**Collection** shows the search state and *Search now* at the top, then every live video as a row with its state in
plain words (“dark on site · light in 5:05 h”, “paused after failures”), filter buttons and a switch. What each
channel plays right now is on the overview.

![Live videos: search state and collection](tour/09b-live-overview.jpg)

A click opens the panel on the right: name, topic, location (with place search), *Show now*, *Don't count failures*,
technical data and removing – *Never suggest again* keeps the search from taking it in again.

![A live video's details](tour/09-streams.jpg)

### 14. Live videos – topics and automation
**Topics** are grouped into **Animals** and **More topics** (cities & squares, beaches & coasts, mountains & ski,
harbours & ships, airports & planes, trains & railways, space & Earth, natural wonders). A click opens a topic: name,
group, up to 6 own YouTube search terms, words that must appear in the title (with how many existing streams they
match), “ignore day/night”, on/off for all channels or per channel. **+ New topic** adds your own with its own nightly
search.

![Topics with a topic's settings](tour/09a-categories.jpg)

The **automation** is set once for all channels, so since 0.65 it is a settings tile: Settings → **Live videos** –
minutes per live video, only live videos where it is daytime, minimum sun elevation, search time and limits, the
optional YouTube API key with what was asked at YouTube; under *Advanced* blocked words and the location table that
recognises places in titles.

![Automation: playback, search and location table](tour/09c-automation.jpg)

### 15. Radio stations
Radio stations: your own stations (MP3/AAC, also .m3u/.pls), suggestions for your location from radio-browser.info,
a buffer that bridges short dropouts.

![Radio stations](tour/10-radio.jpg)

### 16. Clips
Media → Clips: at fixed minutes a clip interrupts the rotation – e.g. the German news “tagesschau in 100 Sekunden”.
The list shows schedule, channels and the last fetch; an open clip has *Overview* (with *Show now*), *Settings*
(source, minutes, time window, channels, buffer – the container preloads each new edition) and *History*.

![Clips as a table](tour/11-clips.jpg)

### 17. Settings
Everything you set once for the whole server is on one page of tiles at the right end of the menu – each with one
sentence and its state in plain words (“connected”, “2 accesses”, “nightly search at 04:30”).

![Settings as tiles](tour/12-settings.jpg)

**General**: language and weather source, location by place search, time source (NTP server and time zone – if the host
keeps its clock synchronised, nothing is corrected), and hidden legal notes can be shown again.

![Settings → General](tour/12b-general.jpg)

**Accounts & access** (since 0.65) collects every way to log in to SignageCast: the admin login, the accesses of the
announcement panel with their rights, the computers of AI assistants and the webhook key. Keys for other services
(Home Assistant token, Telegram, SMB/WebDAV, YouTube API, Tailscale) stay with their connection; the page links to them.

![Settings → Accounts & access](tour/12c-accounts.jpg)

### 18. Updates
System (Debian) and SignageCast updates with one click or automatically within a maintenance window, only while
nobody is watching. Releases are signed and carry a software bill of materials (SBOM); an update is installed only with
a valid signature and returns to the previous version automatically if SignageCast does not run afterwards. Since 0.66
the **player images** for new devices are also downloaded here (Settings → System → Updates).

![Updates](tour/13-updates.jpg)

### 19. Backup
A ZIP with settings, stream list, pictures and chart history. You are asked explicitly whether credentials and
passwords should be included – then the ZIP is AES-256 encrypted and a strong password is required. Automatic backups
daily or weekly; restore in the admin or when installing a new instance.

![Backup with encryption](tour/14-backup.jpg)

Settings → System → **Log** (since 0.38) shows who changed what and when – in the admin, at the panel, via webhook or by
SignageCast itself (updates, picture check, internet outages). Only kind and area, never values; part of the backup.

![Change log](tour/14a-log.jpg)

### 20. Docker / Podman
In the container image there is no Cockpit: the same admin page is served with its own login on port 19090; the
initial password is printed in the container log. The password is changed under Settings → Accounts & access.

![Login page of the container image](tour/15-docker-login.jpg)

### 21. On the phone
The admin works on a phone as well – the menu becomes one selection list, the announcement and emergency buttons stay at the top; switch elements on and off, change sizes, sound, sources.

<img src="tour/16-mobile.jpg" width="320" alt="Admin on a phone">

### 22. Notifications
Telegram, e-mail (SMTP) and Home Assistant, each with a test button; rarely needed options under “Advanced”, and what
to report: channel failure, failed update or backup, Home Assistant disconnected, channel stutters.

![Notifications](tour/17-notifications.jpg)

### 23. Health and performance test
Settings → System → Health shows at the top how much disk space is free and what uses it. The **performance test** measures for
10 seconds how smoothly every running channel is rendered and encoded – frames/s of the
TV page and of the encoder, speed, dropped or duplicated frames, CPU per channel, memory, graphics unit – and gives concrete
recommendations. A second page, opened on the playback device, measures transfer and playback there. Below: after how
many seconds without viewers a channel's video stream switches off.

![Performance test with recommendations](tour/18-performance.jpg)

### 24. Announcements, emergency screen and webhook
**📢 Announcement** at the top right – on every page: an announcement shown large in the middle of the picture (choose a
template or type a text, channels, display time, read aloud) or a **ticker** along the bottom.

![Announcement and ticker](tour/19a-announce.jpg)

**⚠ Emergency** next to it (since 0.65 its own button) triggers and ends the **emergency screen** – red text over every
layout, also at night. The button turns red while an emergency screen is shown.

![Emergency screen](tour/19b-emergency.jpg)

Settings → Announcement panel: the panel for the reception (`http://<IP>:8890/pult` – it sends and ends
announcements, nothing else unless the account has more rights), the voice (offline with Piper: Kerstin or Thorsten, English LJ Speech or Joe),
chime and templates, further down the templates and the warning tone of the **emergency screen** and the webhook
commands. The panel's accounts (own password, channels, rights such as **ticker**, **switch the layout for a while**,
**switch TVs on/off**) and the key for **messages via webhook** are under Settings → Accounts & access.

![Announcement panel, emergency templates and webhook](tour/19-announcements.jpg)
