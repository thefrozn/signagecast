# Changelog

## v0.11.3 (2026-10-29)
- Messages from data sources, cameras, weather, time and clips carry a code (`app/meldung.py`); the admin shows them in
  its language (English texts added; German stays the service's original text). Errors returned when saving or testing
  are translated as well.

## v0.11.2 (2026-10-29)
- Chart history is saved when the service stops (update, restart) – no more gap of up to 5 minutes.
- Admin overview fully in English when English is set: scheduled tasks, load/cores, RAM, Home Assistant errors (also
  in the connection test) are now translated in the admin instead of coming as German text from the service.

## v0.11.1 (2026-10-29)
- **Docker / Podman: admin now on port 19090** (was 9090) – many servers already run Cockpit on 9090, which collides
  with host networking. Changeable with `SC_VERWALTUNG_PORT`. Update: map `-p 19090:19090` (or set `SC_VERWALTUNG_PORT=9090`).
- **Native installation** (Debian VM or real computer): `tvadmin` gets a random initial password shown once at the end
  (containers keep `tvadmin`); an existing Cockpit is reused – SignageCast appears as a menu entry.
- **Stream port configurable** with `SC_STREAM_PORT` (installer remembers it in `/etc/signagecast/umgebung`); the
  installer stops with a hint if the port is already taken. The admin shows TV addresses with the actual port.
- README: table of ports, login and Cockpit integration per installation type.

## v0.11.0 (2026-10-29)
- **Clip buffer** (per clip): “preload in the container” (default) downloads each new edition as soon as it appears and
  the TV plays it from the container – either **complete** or only the **first X MB** (the rest is fetched from the
  server while playing, with byte ranges); “buffer ahead in the browser” (start after X seconds); or off.
  The previous edition is kept until the new one is complete. Not for YouTube.
- A clip that stalls for 20 s is stopped and the live video continues.

## v0.10.0 (2026-10-29)
- **Cameras**: new data source type “camera” (RTSP, HLS or MJPEG). RTSP/HLS are pulled by the built-in MediaMTX only
  while shown and played with hls.js; MJPEG is passed through by the data service. Credentials in the address are masked
  in the admin and left out of backups. Camera paths can only be read inside the container. Test shows codec and size.
- **History / chart** element: Home Assistant history of an entity, or values of a data source recorded by SignageCast
  (up to 7 days).
- **iCal calendars**: new data source type with recurring events (daily/weekly/monthly/yearly, exceptions, moved
  events, time zones); the calendar element can use it instead of a Home Assistant entity.
- **Web page** element: embedded page with zoom, crop and reload interval; “Check” shows whether the site allows embedding.
- Data source tab: format choice for cameras, example “public holidays (iCal)”; elements only offer matching sources.

## v0.9.0 (2026-10-29)
- **Data sources** (new tab): your own JSON APIs, RSS/Atom feeds and pictures, fetched by the container at an interval
  you choose (30 s – 24 h, longer waits after errors). Import from a `curl` command, test with a clickable response tree,
  secret headers shown as ••••; backups leave secrets out unless “include secrets” is ticked. Examples: water level
  (PEGELONLINE), news (tagesschau.de RSS), Bitcoin price (CoinGecko), pollen (DWD).
- **New elements**: API value, API list / feed (list or ticker), API picture (picture source or picture URL from JSON),
  gauge (bar or traffic light with thresholds), countdown (fixed or from an API), QR code (generated on the TV).
- Placeholders `{source:path}` in free text and ticker; conditions (“only show when …”) on values from data sources.
- Numbers with thousands separators when decimals are set.

## v0.8.0 (2026-10-29)
- **Docker / Podman image** `ghcr.io/thefrozn/signagecast` (amd64), built automatically for every release. All data in
  the volume `/data`; `compose.yaml` included. In the container the admin page is served without Cockpit (port 9090)
  with its own login: initial password random and printed in the log (or `SC_PASSWORT`), changeable under Connection.
  `SC_HOST_IP` tells the Home Assistant guide the host's IP.
- **Hardware detection**: a short test encode decides – graphics with H.265 via VAAPI (Intel Quick Sync, 4K) or a
  software fallback with H.264 in Full HD on the CPU. Shown in the overview; also used by LXC installations.
- Chromium uses /tmp instead of a small /dev/shm (Docker default 64 MB).
- Fix: a new installation without settings file had no layout for a moment (TV page error until the profile was loaded).
- Example picture of the practice template is neutral now.

## v0.7.0 (2026-10-29)
- Own weather from **MET Norway** (api.met.no, free, worldwide, no key) – Home Assistant is no longer needed for weather
  and forecast. Default for new installations; updates switch to it automatically if Home Assistant is not reachable.
  Choice under Display → weather source. The TV shows the required credit “Weather data: MET Norway”.
- **Time source**: SignageCast checks the clock against an NTP server (default: the country pool for the location, e.g.
  `de.pool.ntp.org`). If the host (e.g. Proxmox) keeps its clock synchronised, nothing is changed; otherwise clock,
  rotation and clips are corrected. Time zone selectable; a container running in UTC uses the time zone of the
  location's country. `proxmox/ct.sh` now creates the container with the host's time zone.
- Project moved to github.com/thefrozn/signagecast (GitHub account renamed; old links redirect).

## v0.6.0 – first public release (2026-10-28)
- One-line installation: Proxmox host (`proxmox/ct.sh`) or existing Debian 13 (`install.sh`), releases with SHA-256 checksums.
- Admin language follows the browser on a new installation (German/English).
- Update notice in the admin overview when a newer release exists; links to project page and issues.
- New installations start with the built-in list of wildlife and nature live streams.

## v0.5.0
- Project renamed to SignageCast; paths, services, user and API header use `signagecast`. Installations under the old
  name are migrated automatically; old backups remain importable.

## v0.4.x
- Background picture sets (nature, city, sky, mountains, sea) for sunrise, day, sunset and night by real sun position;
  weather combination, slideshow, own pictures per time of day, picture area, fit and crop, dimmed at night.
- Clips at fixed minutes (e.g. the German "tagesschau in 100 Sekunden" on the hour and half hour) in the video window.
- Templates "Practice – calm (waiting room)", "Company – corporate design", "Window to the world"; logo element,
  text colour, multi-line text, ticker.

## v0.3.x
- Layout editor in Cockpit: drag, resize, snap to a 48 × 27 grid; phone list view; templates; export/import;
  schedule per TV (other layout or black); camera, calendar and message elements from Home Assistant; conditions;
  colour schemes, fonts, weight and 9 text positions per element.
- Radio buffer (default 15 s) bridges dropouts of the station.

## v0.2.x
- Internet radio with station suggestions for the location (radio-browser.info), own streams, M3U/PLS import,
  editing; original sound of the animal videos as an option; several TVs with their own address, sound, categories
  and resolution; place search (OpenStreetMap).

## v0.1.0
- Data service, stream list with daylight filter, live check with YouTube rate limiting, daily search, strikes,
  quality watch via DevTools, Cockpit admin, installer.
