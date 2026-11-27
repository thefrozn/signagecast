# SignageCast – glossary / Glossar

[UI rules](UI-RULES.md) · [UI-Regel](UI-RULES.de.md) · [← README](../README.md)

One term per thing, the same in the admin page, the TV page, the documentation and the tour. Internal IDs in code,
API and MCP (e.g. `fernseher`, `tv`, `kategorien`) do not change; this list is about the words people read.

Ein Begriff pro Sache, gleich in Verwaltung, TV-Seite, Doku und Tour. Interne Kennungen in Code, API und MCP
(z. B. `fernseher`, `tv`, `kategorien`) bleiben; diese Liste regelt die Wörter, die Menschen lesen.

## Things / Dinge

| English | Deutsch | Meaning / Bedeutung | Not / Nicht |
|---|---|---|---|
| Channel | Kanal | What one TV shows: layout, schedule, live video, sound, output stream. Was ein Fernseher zeigt. | TV, Fernseher (for the output / für die Ausgabe) |
| Device | Gerät | The hardware at the TV that plays a channel: Raspberry Pi, PC or browser device. Die Hardware am Fernseher. | Player (as a noun in the UI / als Hauptwort in der Oberfläche) |
| Pairing code | Kopplungscode | 6-digit code a new device shows; compare it and click Accept under Devices (since 0.70). Code, den ein neues Gerät zeigt – vergleichen und unter Geräte annehmen. | PIN, Passwort |
| TV | Fernseher | The real screen (switched on/off via Home Assistant or CEC). Der echte Bildschirm. | – |
| Layout | Layout | Arrangement of elements on the screen. Anordnung der Bausteine. | Seite, Ansicht |
| Template | Vorlage | A ready layout to start from. Fertiges Layout als Ausgangspunkt. | Muster |
| Element | Baustein | One part of a layout (clock, weather, list …). Ein Teil eines Layouts. | Widget, Kachel |
| Data source | Datenquelle | Where an element gets its values (JSON, feed, iCal, CSV, camera). | Quelle (alone / allein), Feed |
| Media | Medien | Own pictures and videos. Eigene Bilder und Videos. | Dateien |
| Gallery | Galerie | A folder of pictures/PDFs shown as a slideshow. | Album |
| Clip | Einspieler | A video fetched from an address and played at set times. | Spot |
| Live video | Live-Video | A live stream from YouTube shown in the video window. | Stream (in the UI / in der Oberfläche) |
| Topic | Thema | Group of live videos with search terms. Gruppe von Live-Videos. | Kategorie |
| Radio station | Radiosender | An audio stream played as sound. | Radio (for one station / für einen Sender) |
| Storage location | Speicherort | An SMB/WebDAV/server folder used in file dialogs. | Freigabe, Laufwerk |
| Remote site | Fernstandort | A place outside the home network reached via Tailscale/Headscale. | VPN |
| Access | Zugang | A login for a person or computer (panel, AI assistant, admin). Anmeldung für Person oder Computer. | Konto (for machines / für Rechner), Benutzer |
| Backup | Sicherung | Encrypted copy of all settings. | Export |
| Log | Protokoll | List of changes and events. | Verlauf (page-wide / seitenweit) |
| History | Verlauf | The log of one thing on its detail page. Protokoll eines einzelnen Dings. | – |

## Actions / Aktionen

| English | Deutsch | Meaning / Bedeutung |
|---|---|---|
| Announcement | Durchsage | Large text in the middle of the picture, optionally read aloud. |
| Ticker | Laufschrift | A message running along the bottom edge. |
| Emergency screen | Notfall-Vollbild | Red full-screen text over every layout until someone ends it. |
| Announcement panel | Durchsage-Pult | Separate page (e.g. reception) that may only send announcements, tickers and emergencies. |

## Technical terms kept on purpose / Bewusst behaltene Fachwörter

| English | Deutsch | Where / Wo |
|---|---|---|
| Video stream | Videostream | The HLS output of a channel (stream mode). Only in the channel’s “Video stream” tab. Die Ausgabe eines Kanals. |
| Direct mode / stream mode | Direktmodus / Streammodus | How a device shows a channel: page in the device’s browser or finished video from the server. |
| Player image | Player-Image | The system image written to a Raspberry Pi or PC. |

## Kept on purpose / Bewusst so belassen (since 0.68)

- **Player** stays in *player image* and where the official YouTube or TV app is meant (“official player on the TV”).
  *Restart playback* (Wiedergabe neu starten) restarts the player software on a device.
- **Stream** alone still names the output of a channel where the context is clear (*Restart stream*, *stream mode*,
  *stream from the server*, *stream port*). Live videos from YouTube are never called “stream” in the admin page.
- Internal IDs in code, API and MCP (`player`, `streams`, `kategorie`, `category`) do not change, so existing
  automations and AI assistants keep working.
