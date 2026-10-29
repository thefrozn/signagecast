# Changelog

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
