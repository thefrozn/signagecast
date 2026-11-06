# SignageCast – screenshot tour

A walk through SignageCast: what the TV shows and how you set it up in the browser. All pictures are from a demo
installation (location Berlin, public example data, no Home Assistant connected). The admin pictures show versions
0.17–0.23 with the six areas Overview, TVs, Content, Video & sound, Settings and System.

[← README](../README.md) · [installation](INSTALL.md) · [manual](MANUAL.md) · [how it works](HOW-IT-WORKS.md)

---

## On the TV

### 1. Live window to the world
A live wildlife cam from wherever it is daytime right now, with clock, weather from MET Norway and the forecast.
The bar below mixes your own data: the Rhine water level and the Bitcoin price from public APIs, and a countdown.

![TV with live cam, weather and own data](tour/01-tv-living-room.jpg)

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
notification set up) – each entry links to the page where you fix it. Below, every TV with its state and sound, viewers, weather source, time check against NTP (“time from the host,
synchronised”), video encoding (graphics unit or software fallback), Home Assistant connection, CPU, RAM, uptime.

![Overview](tour/04-overview.jpg)

### 7. TVs
Each TV has its own address, layout, optional schedule (other layout or black at certain times), sound (radio or the
original sound of the cams), volume, categories and video settings (4K/Full HD, bitrate).

![TV settings](tour/05-tvs.jpg)

Under *Video stream* → **Encoding (advanced)**: encoder (Automatic, Intel/AMD graphics, Quick Sync, NVENC, software),
preset, tune and B-frames per TV. A change is tried briefly first; if it does not work here, SignageCast stays with
“Automatic”. Fields that do not apply to the active encoder are explained right there.

![Encoding settings per TV](tour/05a-encoding.jpg)

### 8. Raspberry Pi as player (experimental)
TVs → *Players (Raspberry Pi)*: a Pi at the TV plays the finished stream via HDMI – also on TVs without a usable
browser. Enter a name, pick the TV and the network (LAN or Wi-Fi), download a ready image and write it to an SD card;
nothing to type on the Pi. Afterwards every Pi is managed here: online state, model, IP, Wi-Fi signal, screen, video,
temperature, a screenshot of what it shows, buttons for screenshot, TV on/off (HDMI-CEC), restart and system update,
and Wi-Fi changes with automatic return to the old network. The Pi in this picture is simulated – the player has not
been tested on real hardware yet ([details](PLAYER.md)).

![Players page with one Raspberry Pi](tour/05b-players.jpg)

### 9. Layouts and editor
Content → Layouts starts with all layouts as tiles – mini preview, on which TV each one is shown, edit, and copy /
export / delete in the “⋯” menu. “New layout” asks for a name and a starting point (empty, template or copy), so an
existing layout is never overwritten.

![Layouts overview](tour/06a-layouts.jpg)

In the editor, drag and resize elements on a 48 × 27 grid. Next to it the **layers** (top = front, as on the TV; show
or hide, bring forward / send backward) and the selected element – here a chart: pick the value by clicking it in the
data source's response. Click the same spot again to reach stacked elements, Tab selects the next one.

![Layout editor with layers and path picker](tour/06-layout-editor.jpg)

Every element can be limited to a **period** (“Only during …”: date, optionally with time) – the ⏱ in the layers and on
the canvas marks it. New elements since 0.20: **PDF** (up to 50 pages) and **web page** with the display “Screenshot”
for pages that forbid embedding.

![Layout editor: text with a period](tour/06b-editor-period.jpg)

### 10. Data sources
Your own JSON APIs, RSS/Atom feeds, pictures, iCal calendars and cameras, fetched by the container at the interval you
choose. “View data” shows the response as a tree; a click copies the path for use in elements and placeholders.
Instead of an address, a source can also be an uploaded file (up to 1 MB) – e.g. the waste collection calendar of your
town as `.ics` or `.csv` when it offers no subscription address. For CSV you choose delimiter, quote character, header
row and character set (all detected automatically), which columns to import under which name, optional row filters
(e.g. *LOCATION is empty* or *TYPE does not contain bulky waste*) and optionally a date column: the rows then appear as
events in the *Calendar / waste collection* element. That element can also show icons only – e.g. a bin in the top
corner when residual waste is collected in the next days (rules *title contains … → icon and colour*, with a waste
template).

![Data sources with response tree](tour/07-data-sources.jpg)

### 11. Import from curl
Paste a `curl` command from an API guide – address, method and headers are filled in, `Authorization` is marked as a
secret automatically (shown as •••• after saving, kept out of backups unless you choose otherwise). The command is only
parsed, never executed.

![Data source created from a curl command](tour/08-curl-import.jpg)

### 12. Streams
The built-in list of wildlife and nature live streams, plus streams found by the nightly search. Quality is measured
while playing; streams that stall or only deliver low resolution get strikes and are skipped. Protect favourites,
reject unwanted ones.

![Stream list](tour/09-streams.jpg)

### 13. Radio
Your own stations (MP3/AAC, also .m3u/.pls), suggestions for your location from radio-browser.info, a buffer that
bridges short dropouts.

![Radio stations](tour/10-radio.jpg)

### 14. Clips
At fixed minutes a clip interrupts the rotation – e.g. the German news “tagesschau in 100 Sekunden”. Buffer: the
container preloads each new edition (complete or only the first MB), so the clip plays without stalling.

![Clip settings with buffer](tour/11-clips.jpg)

### 15. Settings → General
Language and weather source, location by place search, time source: NTP server (default: the country pool) and time
zone – if the host keeps its clock synchronised, nothing is corrected. Home Assistant has its own page next to it.
Unsaved changes are marked on their card, and you are asked before leaving the page.

![Settings: display, location and time source](tour/12-settings.jpg)

### 16. Updates
System (Debian) and SignageCast updates with one click or automatically within a maintenance window, only while
nobody is watching. Releases are signed; an update is installed only with a valid signature and returns to the
previous version automatically if SignageCast does not run afterwards.

![Updates](tour/13-updates.jpg)

### 17. Backup
A ZIP with settings, stream list, pictures and chart history. You are asked explicitly whether credentials and
passwords should be included – then the ZIP is AES-256 encrypted and a strong password is required. Automatic backups
daily or weekly; restore in the admin or when installing a new instance.

![Backup with encryption](tour/14-backup.jpg)

### 18. Docker / Podman
In the container image there is no Cockpit: the same admin page is served with its own login on port 19090; the
initial password is printed in the container log.

![Login page of the container image](tour/15-docker-login.jpg)

### 19. On the phone
The admin works on a phone as well – the areas become one menu; switch elements on and off, change sizes, sound, sources.

<img src="tour/16-mobile.jpg" width="320" alt="Admin on a phone">

### 20. Notifications and webhook
Telegram, e-mail (SMTP) and Home Assistant, each with a test button; rarely needed options under “Advanced”. Below,
the webhook for short messages on the TVs (key shown only once).

![Notifications and webhook](tour/17-notifications.jpg)

### 21. Performance test
System → Performance measures for 10 seconds how smoothly every running TV is rendered and encoded – frames/s of the
TV page and of the encoder, speed, duplicated frames, CPU per TV, memory, graphics unit – and gives concrete
recommendations. Here a deliberately overloaded 2-core test container. A second page, opened on the playback device,
measures transfer and playback there.

![Performance test with recommendations](tour/18-performance.jpg)

### 22. Announcement panel
Settings → Announcements: accounts with their own password and the TVs they may reach, the voice (offline with Piper:
Kerstin or Thorsten), chime and templates. The reception opens `http://<IP>:8890/pult` – it can only send and end
announcements, nothing else.

![Announcement panel settings](tour/19-announcements.jpg)

---

## Deutsch (kurz)

Die Verwaltung ist seit 0.17 in sechs Bereiche gegliedert (Übersicht mit „Zu erledigen“, Fernseher, Inhalte,
Video & Ton, Einstellungen, System). Neu seit 0.17–0.19: Layouts-Übersicht mit Kacheln, Ebenen im Editor,
Leistungstest mit Empfehlungen und das Durchsage-Pult. Neu seit 0.20–0.23: Empfangs-Layout mit PDF, Webseite als
Bildschirmfoto und Hinweis mit Zeitraum, das rote Notfall-Vollbild, die Kodierung je Fernseher und die Seite
„Player (Raspberry Pi)“ mit einem simulierten Pi (am echten Gerät noch nicht getestet). Die Tour zeigt zuerst zwei Fernseher – Live-Tierkamera mit Wetter und eigenen Daten (Rheinpegel, Bitcoin, Countdown)
sowie ein reines Daten-Layout (Diagramm mit echten Pegelwerten, Feiertage per iCal, Feed, QR-Code). Danach die
Verwaltung: SignageCast als Menüpunkt in Cockpit, Übersicht mit „Zu erledigen“, Fernseher, Layout-Editor mit Pfad-Auswahl, Datenquellen
mit Antwort-Baum und curl-Import, Streams, Radio, Einspieler mit Puffer, Verbindung mit Zeitquelle, Updates
(signiert, mit Rückkehr bei Fehlern), Sicherung (AES-256 mit Zugangsdaten), die Anmeldeseite im Docker-Betrieb und
die Ansicht auf dem Handy sowie Benachrichtigungen und Webhook. Alle Bilder stammen aus einer Demo-Installation ohne private Daten.
