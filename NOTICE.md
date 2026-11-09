# Third-party components / Fremdkomponenten

SignageCast itself is licensed under the MIT License (see `LICENSE`). It contains or uses (machine-readable in
`werkzeug/komponenten.json` and in the SBOM `signagecast-vX.Y.Z.cdx.json` of every release since v0.30.0):

| Component | Where | License |
|---|---|---|
| [Material Design Icons](https://pictogrammers.com/library/mdi/) 7.4.47 (Pictogrammers) | `www/mdi/`, `cockpit/signagecast/mdi/` | Apache License 2.0 |
| Weather pictures | `www/bilder/*.jpg`, `www/bilder/verlauf.png` | CC0 / public domain – sources in `www/bilder/QUELLEN.md` |
| Background picture sets (20 pictures) | `www/bilder/stile/` | CC0 / public domain – sources in `www/bilder/stile/QUELLEN.md` |
| [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 (Kazuhiko Arase) | `www/qrcode.js` | MIT License |
| [hls.js](https://github.com/video-dev/hls.js) 1.5.20 (light build) | `www/hls/` (with its `LICENSE`) | Apache License 2.0 |
| [xterm.js](https://github.com/xtermjs/xterm.js) 5.5.0 with addon-fit 0.10.0 (The xterm.js authors) – terminal for remote maintenance | `cockpit/signagecast/xterm/` (with its `LICENSE` files) | MIT License |
| [MediaMTX](https://github.com/bluenviron/mediamtx) v1.21.3 | downloaded by `installieren.sh` (checksum verified), not included | MIT License |
| Chromium, ffmpeg, Xvfb, PulseAudio, Cockpit, fonts | Debian packages, installed by `installieren.sh` | their respective licenses |

Logo (`docs/logo/`, `www/favicon.svg`, `cockpit/signagecast/logo.svg`): own design, MIT like the rest. The word mark uses
letter shapes of the font [Sora](https://github.com/sora-xor/sora-font) (SIL Open Font License 1.1), converted to paths;
the font itself is not included.

Online services used at runtime (public endpoints, no account): YouTube (official embed player, public pages and oEmbed),
radio-browser.info (station directory), OpenStreetMap Nominatim (place search, only on demand), tagesschau.de API
(optional clip), GitHub API (update notice), MET Norway Locationforecast (weather, data licensed CC BY 4.0 –
credit “Weather data: MET Norway” is shown on the TV), NTP pool (time check, UDP 123). Please respect their terms of use.

Live streams shown are third-party content and remain the property of their operators; SignageCast only embeds them
with the official YouTube player and only if the operator allows embedding.
