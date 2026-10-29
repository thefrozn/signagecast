# Third-party components / Fremdkomponenten

SignageCast itself is licensed under the MIT License (see `LICENSE`). It contains or uses:

| Component | Where | License |
|---|---|---|
| [Material Design Icons](https://pictogrammers.com/library/mdi/) 7.4.47 (Pictogrammers) | `www/mdi/`, `cockpit/signagecast/mdi/` | Apache License 2.0 |
| Weather pictures | `www/bilder/*.jpg`, `www/bilder/verlauf.png` | CC0 / public domain – sources in `www/bilder/QUELLEN.md` |
| Background picture sets (20 pictures) | `www/bilder/stile/` | CC0 / public domain – sources in `www/bilder/stile/QUELLEN.md` |
| [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 (Kazuhiko Arase) | `www/qrcode.js` | MIT License |
| [MediaMTX](https://github.com/bluenviron/mediamtx) v1.21.3 | downloaded by `installieren.sh` (checksum verified), not included | MIT License |
| Chromium, ffmpeg, Xvfb, PulseAudio, Cockpit, fonts | Debian packages, installed by `installieren.sh` | their respective licenses |

Online services used at runtime (public endpoints, no account): YouTube (official embed player, public pages and oEmbed),
radio-browser.info (station directory), OpenStreetMap Nominatim (place search, only on demand), tagesschau.de API
(optional clip), GitHub API (update notice), MET Norway Locationforecast (weather, data licensed CC BY 4.0 –
credit “Weather data: MET Norway” is shown on the TV), NTP pool (time check, UDP 123). Please respect their terms of use.

Live streams shown are third-party content and remain the property of their operators; SignageCast only embeds them
with the official YouTube player and only if the operator allows embedding.
