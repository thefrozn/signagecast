# SignageCast layout format

A layout describes what a TV shows. It is a JSON object. Screen 1920 × 1080 px, divided into a grid of **48 columns × 27 rows** (one cell = 40 × 40 px). Every element has a position `x`, `y` (top-left cell, 0-based) and a size `w`, `h` in cells. Elements may overlap; later elements in the list are drawn on top. Unknown fields are ignored, invalid values fall back to the default on import (the admin lists every repair).

## Layout

```json
{"art": "signagecast-layout", "version": 2, "layout": {
  "id": "lobby", "name": "Lobby",
  "hintergrund": {"art": "stil", "stil": "natur"},
  "thema": {"schema": "dunkel", "akzent": "#3d8cd0", "schrift": "Roboto"},
  "elemente": [
    {"id": "uhr", "typ": "uhr", "x": 1, "y": 1, "w": 8, "h": 3},
    {"id": "video", "typ": "video", "x": 11, "y": 1, "w": 36, "h": 20, "karte": true}
  ]}}
```

The wrapper (`art`, `version`, `layout`) is optional – a bare layout object works too.

| Field | Meaning |
|---|---|
| `id` | 2–16 characters a–z, 0–9 (a new one is assigned on import if it exists already) |
| `name` | display name, max 40 characters |
| `hintergrund.art` | `"wetter"` (picture matching the current weather), `"stil"` (picture set), `"farbe"` (plain colour), `"bild"` (uploaded picture), `"galerie"` (slideshow of a gallery folder) |
| `hintergrund.galerie`, `hintergrund.galerie_s` | for art `galerie`: folder id ("" – the user picks it) and seconds per picture (5–3600) |
| `hintergrund.stil` | `natur`, `stadt`, `himmel`, `berge`, `meer`, `gemischt` – picture changes with the time of day |
| `hintergrund.farbe` | `"#rrggbb"` for art `farbe` |
| `hintergrund.abdunkeln` | true = darken the picture a little so text stays readable |
| `hintergrund.nachts_dunkler` | true = darker at night |
| `thema.schema` | `"dunkel"` (light text on dark), `"hell"` (dark text on light), `"gedimmt"` (very dim, for night) |
| `thema.akzent` | accent colour `"#rrggbb"` |
| `thema.schrift` | font: `Roboto`, `Noto Sans`, `Noto Serif`, `Open Sans`, `Lato`, `Montserrat`, `Ubuntu`, `Cantarell`, `DejaVu Sans`, `DejaVu Serif`, `DejaVu Sans Mono`, `Fira Code`, `Comic Neue` |

## Element

| Field | Meaning | Default |
|---|---|---|
| `id` | 1–16 characters a–z, 0–9, unique in the layout | – |
| `typ` | element type, see below | – |
| `x`, `y`, `w`, `h` | position and size in cells (x + w ≤ 48, y + h ≤ 27) | 0, 0, 4, 2 |
| `sichtbar` | false = hidden | true |
| `karte` | true = drawn on a semi-transparent card | true for kachel, vorhersage, kalender |
| `ausrichtung` | text position: `oben-links`, `oben-mitte`, `oben-rechts`, `links`, `mitte`, `rechts`, `unten-links`, `unten-mitte`, `unten-rechts` | `links` |
| `schrift` | font of this element (see above), "" = layout font | "" |
| `gewicht` | `duenn`, `normal`, `fett` or "" (normal) | "" |
| `textfarbe` | `"#rrggbb"`, "" = colour scheme | "" |
| `optionen` | options of the type, see below | defaults |
| `bedingung` | show only when …: `{"entity": "binary_sensor.door", "op": "an"}` or `{"quelle": "id", "pfad": "a.b", "op": ">", "wert": "5"}`; op: `=`, `!=`, `>`, `<`, `an`, `aus` | null |
| `ab`, `bis` | show only in this period: `"YYYY-MM-DD"` or `"YYYY-MM-DDTHH:MM"` (local time) | "" |

## Element types and options

### `uhr` – clock (HH:MM)

No minimum size.

| Option | Value | Default |
|---|---|---|
| `sekunden` | true or false | `false` |

### `datum` – date

No minimum size.

| Option | Value | Default |
|---|---|---|
| `wochentag` | true or false | `true` |
| `jahr` | true or false | `true` |

### `temperatur` – current outside temperature

No minimum size.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (weather.*, sensor.*), empty = none | `""` |

### `wetterlage` – current weather condition (icon and text)

No minimum size.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (weather.*), empty = none | `""` |

### `feuchte` – humidity

No minimum size.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (weather.*, sensor.*), empty = none | `""` |

### `wind` – wind speed and direction

No minimum size.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (weather.*, sensor.*), empty = none | `""` |

### `vorhersage` – weather forecast for the next days

Minimum size 4 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `tage` | integer 1–5 | `3` |

### `raeume` – list of room temperatures from Home Assistant

Minimum size 4 × 2 cells.

| Option | Value | Default |
|---|---|---|
| `liste` | list of {"name": "Living room", "entity": "sensor.living_room_temperature"} (max 8) | `[]` |

### `kachel` – tile with one Home Assistant value (name, icon, value)

No minimum size.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id, empty = none | `""` |
| `name` | text (max 30 characters) | `""` |
| `icon` | Material Design Icon name "mdi-…" (e.g. "mdi-thermometer") | `"mdi-information-outline"` |

### `video` – live video window: rotating YouTube nature/wildlife live cams or own media (at most one per layout makes sense)

Minimum size 8 × 5 cells.

| Option | Value | Default |
|---|---|---|
| `leiste` | true or false | `true` |

### `sender` – name of the current live cam or radio station

No minimum size.

### `text` – free text; laufband = scrolling ticker; placeholders {source:path} insert values of own data sources

No minimum size.

| Option | Value | Default |
|---|---|---|
| `text` | text (max 300 characters) | `""` |
| `laufband` | true or false | `false` |

### `logo` – picture (e.g. company logo)

Minimum size 2 × 1 cells.

| Option | Value | Default |
|---|---|---|
| `bild` | file name of an uploaded picture ("" = none; the user uploads it later in the editor) | `""` |

### `kamera` – Home Assistant camera picture

Minimum size 4 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (camera.*), empty = none | `""` |
| `intervall` | integer 1–60 | `2` |

### `kalender` – calendar (Home Assistant calendar or iCal data source) as list or symbols

Minimum size 6 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (calendar.*), empty = none | `""` |
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `anzahl` | integer 1–10 | `4` |
| `tage` | integer 1–60 | `14` |
| `nur_mit_terminen` | true or false | `false` |
| `titel` | text (max 40 characters) | `""` |
| `ansicht` | one of "liste", "symbole" | `"liste"` |
| `symbole` | list of rules {"text": "word in the title", "icon": "mdi-…", "farbe": "#rrggbb"} (max 12) | `[]` |
| `ohne_symbol` | Material Design Icon name "mdi-…" or "" for none | `"mdi-calendar"` |
| `wann` | true or false | `true` |

### `meldung` – message banner from a Home Assistant text entity

No minimum size.

| Option | Value | Default |
|---|---|---|
| `entity` | Home Assistant entity id (input_text.*, sensor.*, text.*), empty = none | `""` |
| `dauer` | integer 3–600 | `20` |

### `flaeche` – coloured rectangle, e.g. as panel behind other elements

No minimum size.

| Option | Value | Default |
|---|---|---|
| `farbe` | colour "#rrggbb" or "" for the default | `"#f0f0f0"` |
| `deckkraft` | integer 0–100 | `100` |

### `apiwert` – one value from an own data source

No minimum size.

| Option | Value | Default |
|---|---|---|
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `pfad` | path into the data source answer, e.g. "current.temp" or "items.0.title" | `""` |
| `vorlage` | text (max 300 characters) | `""` |
| `name` | text (max 30 characters) | `""` |
| `icon` | Material Design Icon name "mdi-…" or "" for none | `"mdi-api"` |
| `einheit` | text (max 12 characters) | `""` |
| `nachkomma` | integer -1–6 | `-1` |
| `faktor` | text (max 16 characters) | `"1"` |

### `apiliste` – list or feed from an own data source

Minimum size 4 × 1 cells.

| Option | Value | Default |
|---|---|---|
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `pfad` | path into the data source answer, e.g. "current.temp" or "items.0.title" | `"eintraege"` |
| `zeile` | text (max 300 characters) | `"{titel}"` |
| `anzahl` | integer 1–20 | `5` |
| `titel` | text (max 40 characters) | `""` |
| `laufband` | true or false | `false` |
| `nachkomma` | integer -1–6 | `-1` |
| `faktor` | text (max 16 characters) | `"1"` |

### `apibild` – picture from an own data source

Minimum size 2 × 2 cells.

| Option | Value | Default |
|---|---|---|
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `pfad` | path into the data source answer, e.g. "current.temp" or "items.0.title" | `""` |
| `anpassung` | one of "einpassen", "fuellen" | `"einpassen"` |

### `anzeige` – gauge (bar or traffic light) for a value

No minimum size.

| Option | Value | Default |
|---|---|---|
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `pfad` | path into the data source answer, e.g. "current.temp" or "items.0.title" | `""` |
| `name` | text (max 30 characters) | `""` |
| `darstellung` | one of "balken", "ampel" | `"balken"` |
| `min` | number | `0.0` |
| `max` | number | `100.0` |
| `gelb` | number | `60.0` |
| `rot` | number | `80.0` |
| `umkehren` | true or false | `false` |
| `einheit` | text (max 12 characters) | `""` |
| `nachkomma` | integer -1–6 | `-1` |
| `faktor` | text (max 16 characters) | `"1"` |

### `countdown` – countdown to a date (ziel: YYYY-MM-DD or YYYY-MM-DDTHH:MM)

No minimum size.

| Option | Value | Default |
|---|---|---|
| `ziel` | text (max 40 characters) | `""` |
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `pfad` | path into the data source answer, e.g. "current.temp" or "items.0.title" | `""` |
| `vorlage` | text (max 120 characters) | `"noch {tage} Tage"` |
| `ende` | text (max 60 characters) | `"Heute!"` |

### `qrcode` – QR code

Minimum size 2 × 2 cells.

| Option | Value | Default |
|---|---|---|
| `inhalt` | text (max 900 characters) | `""` |
| `beschriftung` | text (max 60 characters) | `""` |

### `webcam` – IP camera (own data source of type video)

Minimum size 4 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `ton` | true or false | `false` |
| `anpassung` | one of "fuellen", "einpassen" | `"fuellen"` |

### `diagramm` – history chart of a value

Minimum size 4 × 2 cells.

| Option | Value | Default |
|---|---|---|
| `quelle` | id of one of your own data sources (Content → Data sources), "" = none | `""` |
| `pfad` | path into the data source answer, e.g. "current.temp" or "items.0.title" | `""` |
| `entity` | Home Assistant entity id (sensor.*, input_number.*, number.*, counter.*), empty = none | `""` |
| `stunden` | integer 1–168 | `24` |
| `name` | text (max 30 characters) | `""` |
| `einheit` | text (max 12 characters) | `""` |
| `nachkomma` | integer -1–6 | `1` |
| `faktor` | text (max 16 characters) | `"1"` |

### `unwetter` – official severe weather warnings (Germany, DWD)

No minimum size.

| Option | Value | Default |
|---|---|---|
| `anzahl` | integer 1–3 | `1` |
| `immer` | true or false | `false` |

### `webseite` – web page (embedded or as screenshot)

Minimum size 4 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `url` | web address starting with http:// or https:// | `""` |
| `modus` | one of "einbetten", "bild" | `"einbetten"` |
| `neu_laden_min` | integer 0–1440 | `15` |
| `zoom` | integer 25–300 | `100` |
| `versatz_x` | integer 0–10000 | `0` |
| `versatz_y` | integer 0–10000 | `0` |

### `pdf` – PDF shown page by page

Minimum size 3 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `datei` | 16 hex characters of an uploaded PDF ("" = none; the user uploads it later) | `""` |
| `sekunden` | integer 3–3600 | `15` |
| `anpassung` | one of "einpassen", "fuellen" | `"einpassen"` |

### `galerie` – slideshow of a gallery folder (pictures and PDF pages uploaded under Content → Media library → Galleries); the user picks the folder

Minimum size 3 × 3 cells.

| Option | Value | Default |
|---|---|---|
| `ordner` | id of a gallery folder (Content → Media library → Galleries), "" = none; the user picks it later in the editor | `""` |
| `sekunden` | integer 3–3600 | `10` |
| `anpassung` | one of "einpassen", "fuellen" | `"einpassen"` |
| `rand` | one of "schwarz", "unscharf" | `"schwarz"` |
| `reihenfolge` | one of "eigene", "name", "neu", "zufall" | `"eigene"` |
| `uebergang` | one of "blenden", "hart" | `"blenden"` |

## Rules for good layouts

- Leave a margin of 1 cell at the screen edges (TVs often cut off the border).
- Text needs height: a clock of 3 rows is easy to read from 3 m, a text line needs at least 1 row.
- Only reference Home Assistant entities, data sources, pictures and PDFs that exist; otherwise leave them empty ("") – the user fills them in the editor.
- Use `flaeche` with `deckkraft` 40–80 as a calm panel behind text on pictures or video.
- Answer with the JSON only.
