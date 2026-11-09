# SignageCast – screenshot tour

A walk through SignageCast: what the TV shows and how you set it up in the browser. All pictures are from a demo
installation (location Berlin, public example data, no Home Assistant connected). The admin pictures show version
0.33 (overview 0.35, players 0.36, categories 0.37) with the six areas Overview, TVs, Content, Live videos, Settings and System.

**🇩🇪 [Deutsche Version mit deutschen Bildern](TOUR.de.md)**

[← README](../README.md) · [installation](INSTALL.md) · [manual](MANUAL.md) · [how it works](HOW-IT-WORKS.md)

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
solved once, since 0.35). Below, every TV with its state, current stream,
resolution and sound, then viewers, weather source, time check against NTP (“time from the host, synchronised”), video
encoding (graphics unit or software fallback), Home Assistant connection, streams in rotation, CPU, RAM and uptime.

![Overview](tour/04-overview.jpg)

### 7. TVs
Each TV has its own address and a card in three parts: **Display** (layout, optional schedule with another layout or
black at certain times, layout carousel, switching the TV via Home Assistant), **Live video** (on/off, what the video
window shows, categories) and **Sound** (radio or the original sound of the cams, volume). Under *Video stream*: output
Full HD (default) or 4K, the **capture size** the browser draws in (720p saves CPU, 1440p is sharper), bitrate and codec.
Since 0.37 *Switch via HA* also shows whether the TV is on or off according to Home Assistant and can, after switching
on, select a source (e.g. HDMI 2) and open the TV page (LG webOS, Android TV / Fire TV or an own HA service).

![TV settings](tour/05-tvs.jpg)

Under *Video stream* → **Encoding (advanced)**: encoder (Automatic, Intel/AMD graphics, Quick Sync, NVENC, software),
preset, tune and B-frames per TV. A change is tried briefly first; if it does not work here, SignageCast stays with
“Automatic”. Fields that do not apply to the active encoder are explained right there.

![Encoding settings per TV](tour/05a-encoding.jpg)

### 8. Players – Raspberry Pi, PC or browser (experimental)
TVs → *Players*: a player at the TV shows SignageCast – also on TVs without a usable browser. *Add player*: enter a
name, pick the TV, the **model** and the network (LAN or Wi-Fi), download a ready image and write it to an SD card or
USB stick; nothing to type at the device. Or download one image for many devices: each shows a 6-digit code on the TV,
which you enter under *Pair a player*.

- **Raspberry Pi** – plays the finished stream via HDMI; 1 GB of memory is enough for that. In direct mode (the Pi shows
  the page itself, no encoding on the server) it needs at least 2 GB, better 4 GB.
- **PC** (since 0.36) – an ordinary PC, mini PC or thin client (x86-64 with UEFI, Secure Boot may stay on) starts from a
  USB stick without touching its disk and shows the page itself in direct mode. The same file is also an ISO for CD,
  Ventoy or a VM.
- **Browser device** (since 0.36) – no image at all, just a secret link for a smart TV, a Fire TV stick or a kiosk
  browser. It counts as online while the page fetches its data.

![Adding a PC as player: model and image format](tour/05d-new-player.jpg)

Afterwards every player is managed here: online state, model with memory, IP, screen, video or direct mode,
temperature, buttons for screenshot, restart and – on a Pi – TV on/off (HDMI-CEC) and system update, and Wi-Fi changes
with automatic return to the old network. A PC runs as a write-protected live system: new software comes with a new
image. The devices in these pictures are simulated (real agent code); the PC image was tested in a UEFI VM with
Secure Boot ([details](PLAYER.md)).

![Card of a PC player in direct mode](tour/05b-players.jpg)

![Browser device with its secret link](tour/05e-browser-device.jpg)

### 9. Remote maintenance – terminal to a Pi (experimental, since 0.33)
**Terminal** on the Pi's card opens a root shell in the browser, drawn like Cockpit's own terminal. Off by default:
the Pi itself must allow it (box when creating the image, or its setup page), so someone who takes over the server
cannot reach Pis that do not. No open port and no SSH on the Pi; input and output are encrypted. The TV shows
*Remote maintenance active* meanwhile, and a session ends after 10 minutes without input or 60 minutes at the latest.

![Terminal to a Raspberry Pi in the browser](tour/05c-remote-terminal.jpg)

### 10. Layouts and editor
Content → Layouts starts with all layouts as tiles – mini preview, on which TV each one is shown, edit, and copy /
export / delete in the “⋯” menu. “New layout” asks for a name and a starting point (empty, template or copy), so an
existing layout is never overwritten.

![Layouts overview](tour/06a-layouts.jpg)

In the editor, drag and resize elements on a 48 × 27 grid. Next to it the **layers** (top = front, as on the TV; show
or hide, bring forward / send backward) and the selected element – here a chart: pick the value with “pick …” by
clicking it in the data source's response. Click the same spot again to reach stacked elements, Tab selects the next one.

![Layout editor with layers and a chart element](tour/06-layout-editor.jpg)

Every element can be limited to a **period** (“Only during …”: date, optionally with time) – the ⏱ in the layers and on
the canvas marks it. Elements such as **PDF** (up to 50 pages) and **web page** with the display “Screenshot” for pages
that forbid embedding make layouts like the service desk above.

![Layout editor: text with a period](tour/06b-editor-period.jpg)

### 11. Data sources
Your own JSON APIs, RSS/Atom feeds, pictures, iCal calendars and cameras, fetched by the container at the interval you
choose. “View data” shows the response as a tree; a click copies the path for use in elements and placeholders.
Instead of an address, a source can also be an uploaded file (up to 1 MB) – e.g. the waste collection calendar of your
town as `.ics` or `.csv` when it offers no subscription address.

![Data sources with response tree](tour/07-data-sources.jpg)

For CSV you choose delimiter, quote character, header row and character set (all detected automatically), which columns
to import under which name, optional row filters and optionally a date column: the rows then appear as events in the
*Calendar / waste collection* element. Here a waste calendar with the row filter *DISTRICT is empty* – it drops the
bulky and hazardous waste dates of another district.

![CSV import with row filter and calendar columns](tour/07a-csv-import.jpg)

### 12. Import from curl
Paste a `curl` command from an API guide – address, method and headers are filled in, `Authorization` is marked as a
secret automatically (shown as •••• after saving, kept out of backups unless you choose otherwise). The command is only
parsed, never executed.

![Data source created from a curl command](tour/08-curl-import.jpg)

### 13. Live videos – streams
The built-in list of wildlife and nature live streams, plus streams found by the nightly search. Every stream has a
**state** – ready, night (with “daylight in …”), not live, resolution too low, paused after a strike, location
unknown – and the chips above the list filter by it (with counts), next to text, category and origin (fixed / found).
Quality is measured while playing, and the next stream is checked on YouTube before it is announced. Protect
favourites, reject unwanted ones.

![Stream list with states and filters](tour/09-streams.jpg)

### 14. Live videos – categories, rotation & quality
**Categories** (since 0.37 an own page) are grouped into **Animals** and **More topics** (cities & squares, beaches &
coasts, mountains & ski, harbours & ships, airports & planes, trains & railways, space & Earth, natural wonders). Each
one can be edited: name, group, up to 6 own YouTube search terms, words that must appear in the title, “ignore
day/night”, on/off for all TVs or per TV – with the number of its streams. Found animal streams are sorted into the
first category whose words match. **New category** adds your own (e.g. lighthouses) with its own nightly search;
built-in ones can be reset to default.

![Categories](tour/09a-categories.jpg)

*Rotation & quality*: minutes per stream, only streams where it is daytime, minimum sun elevation; under *Advanced*
the minimum quality (360p … 1080p) and the strike rules.

### 15. Radio
Content → Radio: your own stations (MP3/AAC, also .m3u/.pls), suggestions for your location from radio-browser.info,
a buffer that bridges short dropouts.

![Radio stations](tour/10-radio.jpg)

### 16. Clips
At fixed minutes a clip interrupts the rotation – e.g. the German news “tagesschau in 100 Sekunden”. Buffer: the
container preloads each new edition (complete or only the first MB), so the clip plays without stalling.

![Clip settings with buffer](tour/11-clips.jpg)

### 17. Settings → General
Language and weather source, location by place search, time source: NTP server (default: the country pool) and time
zone – if the host keeps its clock synchronised, nothing is corrected. Home Assistant and notifications have their own
pages next to it. Unsaved changes are marked on their card, and you are asked before leaving the page.

![Settings: display, location and time source](tour/12-settings.jpg)

### 18. Updates
System (Debian) and SignageCast updates with one click or automatically within a maintenance window, only while
nobody is watching. Releases are signed and carry a software bill of materials (SBOM); an update is installed only with
a valid signature and returns to the previous version automatically if SignageCast does not run afterwards.

![Updates](tour/13-updates.jpg)

### 19. Backup
A ZIP with settings, stream list, pictures and chart history. You are asked explicitly whether credentials and
passwords should be included – then the ZIP is AES-256 encrypted and a strong password is required. Automatic backups
daily or weekly; restore in the admin or when installing a new instance.

![Backup with encryption](tour/14-backup.jpg)

### 20. Docker / Podman
In the container image there is no Cockpit: the same admin page is served with its own login on port 19090; the
initial password is printed in the container log. The password is changed under Settings → Access.

![Login page of the container image](tour/15-docker-login.jpg)

### 21. On the phone
The admin works on a phone as well – the areas become one menu; switch elements on and off, change sizes, sound, sources.

<img src="tour/16-mobile.jpg" width="320" alt="Admin on a phone">

### 22. Notifications
Telegram, e-mail (SMTP) and Home Assistant, each with a test button; rarely needed options under “Advanced”, and what
to report: TV failure, failed update or backup, Home Assistant disconnected, TV stutters.

![Notifications](tour/17-notifications.jpg)

### 23. Performance test
System → Performance measures for 10 seconds how smoothly every running TV is rendered and encoded – frames/s of the
TV page and of the encoder, speed, dropped or duplicated frames, CPU per TV, memory, graphics unit – and gives concrete
recommendations. A second page, opened on the playback device, measures transfer and playback there. Below: after how
many seconds without viewers a TV's video stream switches off.

![Performance test with recommendations](tour/18-performance.jpg)

### 24. Announcements, emergency screen and webhook
Content → Announcements: the panel for the reception (`http://<IP>:8890/pult` – it can only send and end
announcements), the voice (offline with Piper: Kerstin or Thorsten), chime, accounts with their own password and the
TVs they may reach, and templates. Further down the **emergency screen** with its templates and webhook commands, and
**messages via webhook**: other systems (e.g. Home Assistant) put a short banner on the TVs, with a key shown only once.

![Announcements, emergency screen and webhook](tour/19-announcements.jpg)
