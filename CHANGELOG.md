# Changelog

## v0.19.2 (2026-10-31)
- **Stutter fixed for TVs with sound:** if ffmpeg captured the screen and the live sound in one process, it slowed the
  screen capture down – up to 90 % of the frames were duplicates (stutter, sound dropouts). Now one process captures
  only the picture and a second one adds the sound (copying the picture, no second encoding). Measured on a real
  installation for 10 minutes: 0 duplicated frames, 25 frames/s in the stream, sound continuous.
- **No more jumps of about one second:** MediaMTX's queue was too small for 4K and discarded frames
  (“reader is too slow”); `writeQueueSize` is now 8192. The performance test counts these discards.
- **Clearer announcements:** chime, a short silence and the speech are one audio file (the start of the speech is no
  longer cut off), spoken 15 % slower.

## v0.19.1 (2026-10-31)
- Announcements: spoken audio files are now removed every minute after an announcement has ended and when the service
  starts – before, only when the panel or the admin asked for data.

## v0.19.0 (2026-10-31)
- **Announcement panel** `http://<IP>:8890/pult` – e.g. for the reception: send short messages to chosen TVs, shown as
  a large call window in the middle of the screen, optionally **read aloud** with a chime first (radio and animal sound
  get quieter meanwhile). Templates with gaps (“Mrs …, please go to room …”), display time, end early, recent list.
  The panel cannot change any setting.
- **Accounts** in Settings → Announcements: each with its own password (stored only as PBKDF2 hash) and the TVs it may
  reach. Login cookie (HttpOnly, SameSite=Strict), wrong passwords delayed, rate limit.
- **Speech offline with Piper**, voices selectable: Kerstin (female, default) and Thorsten (male), both CC0. Program
  and voice are downloaded once on demand (approx. 90 MB) and only used with a matching checksum.
- **Privacy:** announcement texts (names) are kept only in memory – at most 10, for 2 hours – and never written to
  logs or backups; spoken audio files are deleted when the announcement ends.
- The TV page fetches announcements every 2 s, so they appear after the usual stream delay (about 6–10 s).

## v0.18.1 (2026-10-31)
- **Ticker much cheaper:** the scrolling text (text and API list as ticker) now moves a finished layer (`transform`)
  instead of recalculating layout and text 60 times per second (`left`). Measured with a full-screen video plus ticker
  in Full HD: the TV's render chain needs 0.76 instead of 1.21 CPU cores (−37 %), the TV page runs at 60 instead of
  51 frames/s; on a 2-core container the total CPU load dropped from 94 % to 41 %.
- Checked and not changed: Chromium with `--disable-gpu` (no difference).

## v0.18.0 (2026-10-31)
- **Performance test** (System → Performance): measures for 10 s how smoothly each running TV is rendered (frames/s of
  the TV page) and encoded (frames/s, speed, duplicated/dropped frames), CPU per TV, memory and graphics unit – with
  traffic lights and concrete recommendations (simplify layout, more cores, Full HD, lower bitrate, …).
- **Test on the playback device:** open `http://<IP>:8890/test` on the device that stutters – it loads the stream like
  a TV (data rate, load time per segment) and plays it (dropped frames, stalls); the result also appears in the admin.
- **Monitoring:** if a TV page stays below 20 frames/s for 5 minutes, a to-do entry and optionally a notification.
- **Codec per TV:** “Automatic” (H.265 for 4K, H.264 for Full HD – plays on practically every device), or H.265 / H.264
  fixed, with an explanation in the TV settings.
- TVs that cannot play any sound (sound off, no clip or camera with sound) now record a silent track instead of the
  live sound – this saves CPU and avoids duplicated frames seen with the live sound capture.
- **Duplicated frames are monitored:** if the capture of a TV duplicates more than 3 frames per second for 3 minutes, a
  to-do entry and optionally a notification. “Restart sound and stream” in the performance test restarts PulseAudio and
  the streams (this cured a state seen once in testing where most frames were duplicated).

## v0.17.2 (2026-10-31)
- **Layouts overview:** Content → Layouts now starts with tiles of all layouts – mini preview, name and on which TV
  each one is shown; Edit, and Copy / Export / Delete in the “⋯” menu (actions there are saved immediately).
- **“New layout”** asks for a name and the starting point (empty, a template or a copy of an existing layout) and then
  opens the new layout – an existing layout is never overwritten. Import is on the same tile.
- **Editor header:** “← All layouts”, the name editable directly, a hint when the layout is shown on a TV (changes are
  visible right after saving), Undo and Save; background and colours in their own section. Leaving with unsaved
  changes asks first.

## v0.17.1 (2026-10-31)
- **Layout editor:** the selected element no longer jumps above everything – before, a selected large live video
  covered smaller elements on top of it, and they could not be clicked any more. Only the selection frame (with resize
  corner and a move handle ✥) lies on top now.
- **Layers list** next to the editor: all elements in their stacking order (top = front, as on the TV); click to
  select, eye to show/hide, arrows to bring forward / send backward.
- **Click again on the same spot** to cycle through stacked elements; **Tab / Shift+Tab** selects the next / previous one.

## v0.17.0 (2026-10-31)
- **Admin reorganised:** six areas instead of 14 tabs – Overview, TVs, Content (layouts, data sources, media, clips),
  Video & sound (streams, rules, search, radio), Settings (general, Home Assistant, notifications), System (updates,
  backup; Docker: access). Every page has its own address (e.g. `…#benachrichtigung`) for reload and bookmarks; on a
  phone the areas become one menu. Old remembered tabs are redirected.
- **To-do list** on the overview: problems first, then tips – each entry links to the right page.
- **Unsaved changes** are marked on their card; you are asked before leaving the page.
- Rarely needed options are folded under **“Advanced”** (stream rules, radio buffer, e-mail encryption and sender).
- **Setup assistant** on a new installation: language, location, Home Assistant (optional), address for the TV.
  Existing installations are not affected.
- “?” in the navigation opens the manual.

## v0.16.0 (2026-10-30)
- **Severe weather warnings (DWD):** new layout element with the official warnings of the Deutscher Wetterdienst for
  the location (Germany only), coloured by level; hidden without a warning or “show also without warning”. Fetched
  every 10 minutes, only while a layout uses it.
- **Message via webhook:** other systems (e.g. Home Assistant) can put a short banner on all or one TV –
  `POST http://<IP>:8890/meldung` with a secret key created in Connection (shown only once). Text, duration, style
  info/warning; wrong keys get 403 after a delay, rate limit 20 per minute and address. Port `SC_WEBHOOK_PORT`.
- **Notifications** via Telegram, e-mail (SMTP) and Home Assistant (notify service) when a TV fails, an update fails
  or is rolled back, the automatic backup fails, or Home Assistant is unreachable for more than 5 minutes – once per
  event with an all-clear. Test button per channel; bot token and SMTP password are masked and kept out of backups
  without secrets.
- **Manual and FAQ:** [docs/MANUAL.md](docs/MANUAL.md).

## v0.15.0 (2026-10-30)
- **Own media** (new tab “Media”): upload pictures (JPG, PNG) and videos (MP4/H.264, WebM), also large files (in
  pieces, up to 1 GB). Type is detected from the content; H.265 videos are refused with a hint (the browser in the
  container cannot play them). Pictures stay for their duration, videos play completely.
- **Per TV:** the video window shows live streams (YouTube), only own media, or mixed (every N-th time own media).
- **Layout carousel** per TV: switch between chosen layouts every N minutes; a schedule (e.g. black at night) still
  has priority.
- Backups contain pictures always and videos up to 200 MB in total.
- Fix: the stream announced as “Up next” is now really shown next (unless it became unavailable meanwhile – then
  the announcement changes immediately). Before, a changed stream list (strike, night at the location, new streams)
  could lead to a different stream.

## v0.14.0 (2026-10-30)
- **Automatic tests** (`tests/`, Python standard library): curl import, paths and templates, number format, iCal
  recurrences, masking of secrets, backup password rules and AES-256 ZIP, settings and all layout elements.
- **CI on GitHub** for every push: tests and shellcheck in Debian 13, plus a test run of the container image
  (starts, admin page reachable, software encoding detected, no errors).
- **Release script** `release.sh vX.Y.Z` (for maintainers): checks version, changelog, tests and the signing key,
  then tags, builds, signs, uploads and verifies the uploaded files; `--trocken` for a dry run.
- **Issue templates** for bug reports and feature requests (with a reminder not to post passwords or private data).

## v0.13.1 (2026-10-30)
- **Layouts as portable templates:** “Export” in the layout editor now includes all pictures the layout uses (logo,
  background picture, pictures per time of day). “Import” uploads them on the other installation and links them –
  a layout can be taken to another SignageCast as a complete template. Old exports without pictures still import.

## v0.13.0 (2026-10-29)
- **Updates tab** (LXC/native): check for Debian and SignageCast updates, install all or security updates only,
  update SignageCast, return to the previous version. **Automatic** per type (system: notify / security only / all;
  SignageCast: notify / automatic) within a maintenance window and only while nobody is watching; default notify only.
- **Signed releases** (minisign). The in-app update and `install.sh` require a valid signature for releases from
  v0.13.0 on; older releases are installed with a note.
- **Safe update:** backup of settings and data before the update, previous version kept (`/opt/signagecast.vorher`),
  automatic return if the service does not run within 60 s.
- Privilege separation: the admin drops a request file; a systemd path unit starts the fixed root script
  `werkzeug/aktualisieren.sh` (only fixed actions, symlink-safe, own root-only folder).
- New dependency: `minisign` (Debian package).

## v0.12.0 (2026-10-29)
- **Backup as ZIP** (Backup tab): settings, stream list, strikes, **uploaded pictures** and **chart history**
  (Docker: also the admin password). When creating a backup the admin asks explicitly whether credentials and passwords
  should be included – then the ZIP is **AES-256 encrypted** (WinZip AES via python3-pyzipper, the password never
  appears on a command line) and a **strong password is required** (12+ characters, three character classes, or a
  passphrase of 20+ characters). Opens with SignageCast, 7-Zip or WinRAR.
- **Automatic backups** daily or weekly at a set time, stored in the container (folder only readable by the service),
  keeping the last N; optionally with credentials (then with its own strong password, shown as •••• in the admin).
- **Restore** in the admin (ZIP or old .json, password if encrypted) or directly when installing a new instance:
  `SC_SICHERUNG=/path/backup.zip SC_SICHERUNG_PASSWORT=… sh installieren.sh` (also via install.sh).
- New dependency: `python3-pyzipper` (Debian package).

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
