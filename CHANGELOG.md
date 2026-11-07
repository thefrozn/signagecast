# Changelog

## Unreleased
- **Minimum quality shown as resolution:** the setting and the TV overview show 360p, 720p, 1080p … instead of
  YouTube's internal names (medium, hd720, hd1080 …). Stored values are unchanged.
- **General failures no longer use up the stream list:** if 3 different streams fail for the same reason within
  10 minutes, it is not the streams' fault (e.g. YouTube delivers only 360p everywhere, as seen on 2026-11-07 – a TV
  then skipped every 20 s and paused 27 streams). The TV now stops giving strikes, the data service takes back the
  strikes and pauses of that series, and *To do* in the overview shows a warning. With *resolution too low* the stream
  keeps playing instead of skipping. It ends as soon as a stream runs fine again for a minute.
- **Admin reorganised:** *Content* now holds radio stations and announcements (panel, emergency screen and messages via
  webhook – the webhook receives messages, so it left *Notifications*, which only sends). *Video & sound* became
  *Live videos* (Streams · Rotation & quality · Search). *Access* (Docker) moved to *Settings*, *switch off without
  viewers* to *System → Performance*. Each TV card is split into Display, Live video and Sound; its categories sit with
  the live video. Page addresses (`#video`, `#pult` …) stay the same.
- **One switch for live videos:** the global *show live videos* is gone, only the switch per TV remains. If it was off,
  every TV gets its switch off on update (also when the global value is set via the API).
- **Backup page on phones:** long checkbox texts wrap instead of widening the page.

## v0.31.0 (2026-11-07)
- **Night list instead of lost places:** every stream now has a state – ready, night (with “daylight in …”), not live,
  resolution too low, paused after strike, blocked, location unknown, not checked yet, inactive. Night streams stay out
  of the rotation but are kept and checked now and then (every 6 h), so dead ones do not only show up in the morning.
  Streams where daylight starts within 30 minutes are checked first, so they are ready at sunrise.
- **Found streams: the limit counts only streams in daylight.** Night streams and streams without a location no longer
  use up places of *maximum found streams*; a hard limit of 80 found streams applies (location unknown goes first).
- **Next stream checked in advance:** the TV reports its next and the one after; the data service checks them on
  YouTube right away (live, embeddable, offered resolution – read from the same page, no extra request), independent
  of the switch. If one fails, the TV announces another one long before the switch instead of skipping after it.
  Pre-checks are limited to 10 per 5 minutes on top of the regular 6; HTTP 429 still pauses everything for an hour.
- **Quality before playing:** streams that offer less than the minimum resolution are not put into the rotation
  (protected streams still are). A strike now pauses the stream for all TVs for the configured time.
- **The announcement holds:** “Next: …” only shows checked streams, and the announced stream is the one that comes –
  also if it got dark there a few minutes before (up to 15 min).
- **Admin – Streams:** filter by state (with counts, click to filter) and origin (fixed / found), besides text and
  category; the browser remembers the filter. Cards show the state, “daylight in …” and the offered resolution.

## v0.30.0 (2026-11-06)
- **Software bill of materials (SBOM):** every release now carries `signagecast-vX.Y.Z.cdx.json` (CycloneDX 1.5) –
  bundled third-party components with checksums (Material Design Icons, qrcode-generator, hls.js), MediaMTX and the
  Debian packages the installation adds; listed in `SHA256SUMS` and signed with minisign like the package. Generated
  by `werkzeug/sbom.py` (standard library only, repeatable) from `werkzeug/komponenten.json`; a test keeps it in line
  with `NOTICE.md`, `installieren.sh` and the `Dockerfile`.
- **Raspberry Pi image SBOM:** `signagecast-player-vX.Y.Z.cdx.json` lists every package of the image with version;
  its checksum is part of the signed image description and the file itself is signed too.
- **Container image:** SPDX SBOM and provenance (build attestations) on GHCR.

## v0.29.1 (2026-11-06)
- **Live videos stay H.264:** the render extension now reports VP9 and AV1 as unsupported (also to
  `MediaSource.isTypeSupported` and `canPlayType`, like h264ify). Reporting them only as “not smooth” was not enough –
  YouTube still picked AV1 or VP9 for some streams, and decoding AV1 in software cost about 40 % more CPU (measured
  1080p: ~160 % instead of ~113 % of one core).
- Calendar element, icons only: the labels below the icons (e.g. *Tomorrow* twice) no longer run into each other – the
  text shrinks to fit its icon and the icons get spacing.
- Screenshot tour renewed with 0.29 (new: waste icons on the TV, CSV import with row filter, capture size).

## v0.29.0 (2026-11-06)
Performance release – stability, security and performance rank equally in SignageCast.
- **Capture size per TV:** TVs → Video stream → *Capture (browser)*: 720p, 1080p (default) or 1440p. The browser draws
  the TV page in this size (the layout stays 1920 × 1080 points); the graphics unit converts it to the output. 720p
  saves CPU and fetches live videos in 720p, 1440p is sharper for text on 4K output. A change restarts the stream.
- **Full HD is the new default output** for new installations and new TVs (8 Mbit/s, H.264). The browser draws in
  1080p anyway – a 4K TV upscales itself, Full HD saves bitrate and graphics work. Existing TVs keep their setting.
- **Live videos as H.264 in capture size:** the render extension reports VP9/AV1 as “not smooth” (the CPU decodes them
  far more expensively than H.264) and H.264 only up to the capture height.
- Measured, not changed: drawing without the browser's OpenGL emulation (`--disable-gpu`) used about 8 % more CPU at
  the same power draw (3 rounds each, i5-7500T) – the emulation stays; `GPU=aus` in `tv-render.sh` only for comparisons.
- **Browser background services off** in the render chain (background networking, component updates, sync,
  default apps, domain reliability) – less CPU and network traffic.
- **Announcements and emergency screen by long polling:** the TV page no longer asks every 2 s; the request waits until
  something changes (at most 20 s) – still shown at once, about 90 % fewer requests.
- **Measuring tool** `werkzeug/leistung_messen.py`: CPU and memory (PSS) of the render chains, MediaMTX and the
  service, frame rate and duplicated/lost frames per TV; `--vergleich` compares with an earlier measurement and returns
  1 when it got worse. Every release is measured with it before publishing.
- README: section *Principles* (rock-stable, secure, light).

## v0.28.1 (2026-11-06)
- **TV page reloads after an update:** the page compares the version reported by the service and reloads at once when it
  changes – before, new display features only appeared after the page's 6-hour reload. Static files (`seite.js`,
  `stil.css` …) are now sent with `Cache-Control: no-cache`, so the browser always checks for the new version (usually a
  quick 304). Takes effect from the next update after 0.28.1.

## v0.28.0 (2026-11-06)
- **Calendar element – icons only:** new display *icons only*. Each upcoming event becomes one icon, chosen by rules
  *title contains … → icon and colour* (first match wins, case-insensitive); the same icon appears once (earliest date),
  optionally with *Today*, *Tomorrow* or the weekday below. Events without a matching rule get a default icon or are left
  out. *Insert waste template* adds residual (bin), organic (leaf), paper (newspaper), recycling, bulky and hazardous
  waste. In this display the element may be as small as one grid cell – e.g. a bin in the top right corner, shown
  together with *Days* and *only show when events are due*.

## v0.27.0 (2026-11-06)
- **CSV import – row filter:** only import rows that match all rules. Rules per field: *contains*, *does not contain*,
  *equals*, *does not equal*, *is empty*, *is not empty* (case-insensitive). The import shows how many rows match and
  previews only those. Applies to calendar events too – e.g. a town waste calendar that also lists bulky-waste and
  hazardous-waste dates for other districts: keep only rows whose location column is empty. Part of the reusable
  CSV import module (`app/csvimport.py`, `csvimport.js`); existing sources keep working unchanged.

## v0.26.1 (2026-11-06)
- **Calendar element – only when events are due:** new option *only show when events are due in this period*. The
  element is hidden while there is no event within *Days* – e.g. with 3 days the waste collection appears three days
  before the pickup, stays until the pickup day and disappears afterwards.

## v0.26.0 (2026-11-06)
- **Data sources from a file:** instead of an address, upload a file (up to 1 MB) – iCal (`.ics`), CSV, JSON, RSS or
  text. Useful when your town only offers the waste collection calendar as a download. The type is detected; upload
  again for new dates. Files are part of backups.
- **CSV import:** new type *Table (CSV)*, from a file or an address. Delimiter (comma, semicolon, tab, bar, space),
  quote character (double, single, none), header row and character set (UTF-8, Windows/Excel, ISO-8859-1) are
  detected and can be changed; choose which columns to import and rename them; preview of the first rows. Data appear
  as `zeilen` (list for *API list*, values for placeholders). With a **date column** (e.g. `Mi 07.01.2026`,
  `2026-01-07`, optionally with a time) the rows become events (`termine`) for the *Calendar / waste collection*
  element; past ones are dropped. The import is a separate module (`app/csvimport.py`, `csvimport.js`) for reuse.
- **Removed:** the *Departures (bus & train)* element (hidden since 0.21). There is no open timetable service for
  Germany that allows commercial use; existing elements are dropped silently when loading.

## v0.25.0 (2026-11-06)
- **Raspberry Pi player – one image for several Pis:** *Pair a Pi* → *Download image for several Pis* (server address
  and Wi-Fi, no key). Flash it onto any number of cards; each Pi shows a 6-digit code on the TV, enter it in the admin
  with name and TV → paired. The key is negotiated with Diffie-Hellman (RFC 3526, 2048 bit) and never travels over the
  network; the code is derived from it, so a device intercepting the exchange would show a different code. Codes are
  valid for 10 minutes; at most 20 open and 60 new requests per hour. Needs an image from 0.25; per-screen images keep
  working as before.
- **Data sources – iCal:** an address that returns a web page instead of a calendar (e.g. a login or error page with
  status 200) now shows “no iCal data” instead of silently showing no events.

## v0.24.0 (2026-11-06)
- **Raspberry Pi player – direct mode (experimental):** per Pi under *Settings → Display*. A Pi 4/5 shows the TV page
  itself (Chromium in the kiosk shell cage, no desktop) instead of the stream – sharp text, no stream delay, and the
  server renders and encodes nothing for this Pi. Sound comes from the Pi's HDMI. Full HD by default (4K TVs upscale).
  Pi 3/Zero 2 W always use the stream.
- **Fallback:** three browser crashes or page-load failures within 10 minutes → the Pi shows the stream for one hour
  (note in the admin; *Restart player* retries at once).
- **Access:** the Pi opens `/anzeige/<key>` on port 8890; the key is derived from the device key and only gives access
  to the page of its own TV – no admin API, only the cameras in that TV's layout (camera streams stay closed to the
  network otherwise). Removing the Pi revokes it.
- The player image now contains Chromium, cage, seatd, grim and wlr-randr (larger download). Images from 0.23 keep
  working with the stream; for direct mode flash a new image (the admin says so).

## v0.23.3 (2026-11-05)
- Radio → playlist import: the list of rejected entries is now shown in the admin language (was always German).
- Announcement panel and emergency screen: the preset templates follow the admin language. Templates you changed
  yourself stay as they are.
- Docs: rootless Podman should run with host networking (`--network host`) – its default port forwarder can hide the
  client address, so camera streams would be readable from the network (command in docs/INSTALL.md).

## v0.23.2 (2026-11-05)
- Raspberry Pi player: the Wi-Fi name is quoted as usual in the admin language (English “Office” instead of the German
  „Office“).
- Times in the admin follow the admin language and always use 24 hours (before: player page partly in the browser's
  format, e.g. “since 03:52 PM” next to “Last: 15:52”; also the overview's pause time and the preview time).

## v0.23.1 (2026-11-05)
- Raspberry Pi player: “Download player image” failed with “HTTP Error 415” – the request to GitHub's release list
  sent the wrong Accept header.

## v0.23.0 (2026-11-05)
- **Raspberry Pi as player (experimental):** TVs → *Players (Raspberry Pi)*. A Pi at the TV plays the finished stream
  via HDMI (mpv directly on the screen, no desktop). The admin downloads a signed base image once (Raspberry Pi OS Lite
  64 bit with the player, built by GitHub Actions for each release) and creates a ready SD card image per screen –
  server address, device key and Wi-Fi are written into it on download (no mounting, works in Docker/NAS too). Write it
  with Raspberry Pi Imager or balenaEtcher, plug in, done. Pi 5/4/400 up to 4K (H.265), Pi 3/Zero 2 W Full HD with H.264.
- **Central management:** status (online, model, IP, Wi-Fi signal, screen, video, temperature, under-voltage), warnings
  for settings that do not fit the model, screenshot, show name on the TV, TV on/off via HDMI-CEC (also by the TV's
  schedule), restart, weekly or manual system updates, log; rotation, output resolution, volume, write protection
  (overlayroot, on by default). Notification when a Pi has not reported for 5 minutes. The player updates itself.
- **Wi-Fi:** change it from the admin – the Pi tries the new network and returns to the old one if it cannot reach the
  server. Without network the Pi opens a hotspot and shows a QR code on the TV; the setup page opens on the phone.
  The Wi-Fi password is never stored in plain text (only the WPA key); saving it in the admin is optional.
- **Security:** the Pis only pull (no open port), every request and answer is signed per device (HMAC-SHA256), removed
  players are locked out. Uses the webhook port 8890 – with Docker/NAS publish it (`-p 8890:8890`).
- New package `minisign` in the container image (checks the player image).

## v0.22.0 (2026-11-05)
- **Encoding per TV (advanced):** TVs → Video stream → *Encoding (advanced)*: encoder (Automatic, Intel/AMD graphics
  via VAAPI, Intel Quick Sync, NVIDIA NVENC – experimental, untested –, software libx264), preset (ultrafast …
  medium, default veryfast), tune (zerolatency or none) and B-frames (0–4, default 0), each with an explanation.
  Encoders that do not work on this computer are greyed out with the reason; a changed setting is test-encoded for one
  second first and the TV stays on *Automatic* (with a note) if it fails. Saving restarts the stream of that TV. The
  performance test shows the encoder per TV.
- New package `libmfx-gen1.2` (Intel Quick Sync runtime for Intel graphics of the 11th/12th generation and newer).

## v0.21.2 (2026-11-05)
- Docker/NAS: the log line with the initial admin password is now in German and English and names the right place
  to change it (System → Access); the installer points to Settings → Home Assistant.

## v0.21.1 (2026-11-04)
- Switching TVs via Home Assistant: a clear message when the device cannot be switched on or off by HA (e.g. Samsung/LG
  without Wake-on-LAN) instead of “HA answers 400”.

## v0.21.0 (2026-11-04)
- **PDF element:** upload a PDF (price list, menu, notice, presentation – up to 50 pages) in the layout editor; it is
  converted into pictures once (`pdftoppm`, new package `poppler-utils`) and shown page by page, changing by the clock
  so all TVs turn pages together. Pages are part of the backup.
- **Elements with a period:** every element can get *from*/*until* (date, optionally with time), e.g. “Closed from
  23 Dec to 2 Jan” appears and disappears by itself. Marked with ⏱ in the editor.
- **Emergency screen:** a red full screen with a text (optional warning tone every 10 s) above every layout, also at
  night, until someone ends it – from the admin (Settings → Announcements), from the panel for accounts with the new
  right “may trigger the emergency screen”, or by webhook (`POST /alarm` with the webhook key, `{"aus": true}` ends
  it). Survives a restart of the service.
- **Switch TVs via Home Assistant:** per TV an entity (media_player, switch or remote). When “black” starts in the
  schedule the TV is switched off, afterwards (or for an emergency screen) on again – only at the change, so switching
  on by hand is kept. Test buttons in the TV settings.

## v0.20.0 (2026-11-04)
- **Web page element: new display “Screenshot”** for pages that forbid embedding (X-Frame-Options, CSP
  frame-ancestors). SignageCast loads the page in a short-lived headless Chromium (fresh profile, low priority, one at
  a time) and shows a picture refreshed every *reload* minutes (0 = hourly), with the same zoom and crop as live
  pages. Only while a TV shows the layout; the last picture stays on disk so it appears right after switching on.
  The *Check* button suggests this display when a page forbids embedding.

## v0.19.3 (2026-11-04)
- **Validation messages in English:** errors when saving layouts, TVs, schedules, clips, video streams, radio stations
  and announcements now carry an identifier, so the English admin shows them in English (before: German only).
  Nested messages such as “Layout Hall: colour as #rrggbb” are translated as a whole.
- **Notifications in the admin language:** Telegram, e-mail and Home Assistant notifications (failure, stutter, update,
  backup, Home Assistant) and the test message are sent in the language set in the admin.
- **Connection:** if Home Assistant cannot be reached yet, the setup guide uses the address from the browser instead of
  “?” and a German placeholder; without an IPv4 address it shows a placeholder in the admin language.
- Performance test: the hint for duplicated frames names CPU/graphics shortage as the usual cause (since 0.19.2).

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
