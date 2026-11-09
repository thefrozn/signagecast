# SignageCast – how it works

[← README](../README.md) · [installation](INSTALL.md) · [hardware](HARDWARE.md) · [manual](MANUAL.md)

## Parts

| Part | Where | Task |
|---|---|---|
| Data service `signagecast` | `/opt/signagecast/app/`, only 127.0.0.1:8080 | TV page, Home Assistant values, stream list, search, quality watch, API for the admin |
| Render chain | `/opt/signagecast/render/tv-render.sh` | Xvfb + Chromium (capture size per TV, default Full HD) → ffmpeg → Intel GPU (scale, H.264/H.265) + AAC → MediaMTX |
| MediaMTX `signagecast-mediamtx` | `/opt/mediamtx`, port 8888 | HLS stream, starts rendering on demand |
| Admin | `/usr/share/cockpit/signagecast`, port 9090 | Cockpit extension (Docker/Podman: same page served by `app/verwaltung.py` with its own login) |
| Settings / data | `/etc/signagecast/`, `/var/lib/signagecast/` | backup and restore in the admin |

Only the Python standard library and Debian packages are used. Third-party components and picture sources:
see [NOTICE.md](../NOTICE.md).

## Good to know

- Only public YouTube pages and the **official embed player** are used; streams whose operators do not allow embedding
  are not shown. If YouTube reports too many requests, SignageCast pauses for an hour. Nothing is circumvented.
- **Stream checks (since 0.31):** every 5 minutes up to 6 streams are checked on YouTube – first those where daylight
  starts within 30 minutes, then daytime streams not checked for 2 hours, then night streams not checked for 6 hours.
  Separately, each TV reports its next two streams; the data service checks them if their last check is older than
  20 minutes (at most 10 per 5 minutes). One page request gives live state and offered resolution.
- The small browser extension `render/h264-fluessig` tells YouTube that H.264 up to 1080p plays smoothly – Chromium in
  the container decodes without GPU and would otherwise report “not smooth”, and YouTube would deliver only 144p.
- The admin user `tvadmin` has no administrator rights in the container.
- **Data sources:** only http/https, response at most 1 MB (pictures 5 MB), 10 s timeout, interval 30 s to 24 h; on
  errors the next attempt waits longer (up to 1 h). Secret headers are shown as •••• and left out of backups unless you
  tick “include secrets”. The TV page only receives the finished values, never addresses or keys.
- **Cameras:** RTSP/HLS cameras are pulled by MediaMTX only while a TV shows them and can only be read inside the
  container (not on port 8888 from the network). The camera must deliver **H.264** (Chromium in the container cannot
  decode H.265). Rootless Podman with the default port forwarder may hide the client address – use host networking there.
- **Web pages** are embedded live only if the site allows it (X-Frame-Options / frame-ancestors). The *screenshot* mode
  loads the page in a short-lived headless Chromium inside the container (fresh profile each time, no cookies or
  logins kept) only while a TV shows it, one page at a time at low priority. Please respect the site's terms of use.
- **Internet check (since 0.38):** while a TV shows live videos, the data service opens one TCP connection to the
  YouTube embed host every minute (no HTTP, no data). Two failures in a row = offline: the TV page gets `offline` and
  shows own media or a local picture; strike reports are ignored meanwhile.
- **Picture check (since 0.38):** every 2 minutes per running TV one frame of the virtual screen (Xvfb, what is
  captured) is grabbed at 160 × 90 grey with `ffmpeg -f x11grab` at low priority – not from the stream, because a reader
  there would count as a viewer and keep the chain running. Black or (with a visible clock) unchanged three times in a
  row → reload the TV page; next time restart the chain and notify.
- **Change log and layout versions (since 0.38):** `/var/lib/signagecast/protokoll.json` (last 500 entries, kind and
  area only) and `layout-versionen.json` (10 per layout, 10 deleted layouts); both are in backups. The Cockpit user
  name is sent along for the log only – access is decided by Cockpit as before.

## Updates and backups

**Updates tab** (LXC and native installations): available Debian updates (security updates marked) and the latest
SignageCast release, with buttons to check, install all, install security updates only, update SignageCast and return
to the previous version. Optionally automatic – system (all or security only) and SignageCast separately – but only
within a maintenance window and only while nobody is watching. Default: notify only.

- **Signed releases:** from v0.13.0 every release is signed with [minisign](https://jedisct1.github.io/minisign/).
  The in-app update and `install.sh` only install a package whose signature matches the public key built into
  SignageCast – a checksum alone would not help if the GitHub account were taken over.
  Public key: `RWS+1ozfjYuftY7DYt4RjDJLsJKenGkFL7prSxRjeDuk3c+++cclZqgD`
  (check manually: `minisign -Vm signagecast-vX.Y.Z.tar.gz -P <key>`).
- **Software bill of materials (SBOM, from v0.30.0):** every release carries `signagecast-vX.Y.Z.cdx.json`
  (CycloneDX 1.5: the bundled third-party components with checksums, MediaMTX and the Debian packages the
  installation adds), listed in `SHA256SUMS` and signed like the package. The Raspberry Pi image has its own SBOM with
  every package and version (`signagecast-player-vX.Y.Z.cdx.json`; its checksum is part of the signed image
  description). The container image on GHCR carries an SPDX SBOM and provenance as build attestations
  (`docker buildx imagetools inspect ghcr.io/thefrozn/signagecast:X.Y.Z --format "{{ json .SBOM }}"`). Feed them to
  a scanner such as Grype or Trivy, e.g. `grype sbom:signagecast-player-vX.Y.Z.cdx.json`.
- **Safe update:** settings and data are backed up first; the previous version is kept. If SignageCast does not run
  within a minute after the update, it returns to the previous version automatically.
- **How it works:** the admin page runs without root rights. It only drops a request file with one word (`pruefen`,
  `system`, `sicherheit`, `signagecast`, `zurueck`); a systemd path unit starts the fixed root script
  `werkzeug/aktualisieren.sh`, which accepts only these actions – no sudo, no polkit.
- **Docker / Podman:** updates come with the image (`docker pull …`, `podman auto-update`); the tab shows the commands.

**Backup tab:** ZIP with settings, stream list, pictures and history; credentials only
in an AES-256 encrypted ZIP with a strong password; automatic backups; restore in the admin or when installing
(`SC_SICHERUNG=… SC_SICHERUNG_PASSWORT=…`).

---

## Deutsch (kurz)

**Aufbau:** Datendienst (`app/`, nur 127.0.0.1:8080) liefert TV-Seite und Werte; je Fernseher Xvfb + Chromium (Full HD)
→ ffmpeg → Intel-Grafik (Hochskalieren, H.265) → MediaMTX (HLS auf Port 8888, rendert nur, solange jemand zuschaut);
Verwaltung als Cockpit-Erweiterung (Docker/NAS: eigene Anmeldung auf 19090). Nur Python-Standardbibliothek und
Debian-Pakete.

**Gut zu wissen:** Nur öffentliche YouTube-Seiten und der offizielle Einbett-Player, nichts wird umgangen. Datenquellen
nur http/https mit Größen- und Zeitgrenzen; geheime Kopfzeilen bleiben im Container. Kameras liest nur MediaMTX im
Container (H.264 nötig). Webseiten live nur, wo die Seite das Einbetten erlaubt, sonst als Bildschirmfoto.
Seit 0.38: **Internet-Prüfung** (je Minute eine TCP-Verbindung zum YouTube-Player, nur wenn Live-Videos laufen; offline
→ eigene Medien bzw. lokales Bild, keine Strikes), **Bildprüfung** (alle 2 min ein Graustufenbild 160 × 90 vom
virtuellen Bildschirm, nicht vom Stream – schwarz oder mit Uhr stehend → neu laden, dann Kette neu starten und melden),
**Protokoll** und **Layout-Versionen** in `/var/lib/signagecast/` (Teil der Sicherung).

**Updates & Sicherung:** Reiter „Updates“ (System- und SignageCast-Updates per Knopf oder automatisch im Wartungsfenster,
nur wenn niemand zuschaut; Rückkehr zur vorigen Version, automatisch bei Fehlern) und „Sicherung“ (ZIP, mit Zugangsdaten
nur AES-256 mit starkem Passwort). Ab v0.13.0 sind alle Releases mit minisign **signiert**; Updates installieren nur
Pakete mit gültiger Signatur (öffentlicher Schlüssel `RWS+1ozfjYuftY7DYt4RjDJLsJKenGkFL7prSxRjeDuk3c+++cclZqgD`).
Ab v0.30.0 hat jedes Release eine signierte **SBOM** (CycloneDX) fürs Paket und fürs Pi-Image (alle Pakete mit
Version); das Container-Image trägt eine SPDX-SBOM als Attestierung.
Docker/NAS: Update über ein neues Image.
