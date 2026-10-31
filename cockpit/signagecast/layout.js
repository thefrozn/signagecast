// SignageCast – Layout-Editor (Reiter „Layout“). Wird vor tv.js geladen und nutzt dessen Hilfsfunktionen zur Laufzeit.
// PC/Tablet: Bausteine auf einer verkleinerten Fläche ziehen (verschieben) und an der Ecke größer/kleiner ziehen,
// alles rastet im Raster 48 x 27 ein. Handy: Liste mit Ein/Aus, Größe −/+ und Einstellungen.
"use strict";

const LTEXTE = {
  de: {
    alleLayouts: "Alle Layouts", ausgangspunkt: "Ausgangspunkt", leeresLayout: "leer", vorlagenGruppe: "Vorlagen", kopieVon: "Kopie von",
    erstellen: "Erstellen", abbrechen: "Abbrechen", bearbeitenL: "Bearbeiten", mehr: "Mehr", nichtVerwendet: "nicht verwendet",
    laeuftAuf: (n) => `läuft auf: ${n}`, laeuftHinweis: "Änderungen sind nach dem Speichern sofort auf dem Fernseher zu sehen.",
    nameFehlt: "Bitte einen Namen eingeben.", verwerfen: "Ungespeicherte Änderungen verwerfen?", hgFarben: "Hintergrund & Farben",
    layout: "Layout", neu: "Neues Layout", ausVorlage: "aus Vorlage", duplizieren: "Kopieren", loeschen: "Löschen",
    exportieren: "Exportieren", importieren: "Importieren", rueckgaengig: "Rückgängig", speichern: "Speichern",
    name: "Name", hintergrund: "Hintergrund", hgArt: { wetter: "Wetterbild (nach Wetter)", stil: "Bilderset (nach Tageszeit)", bild: "eigene Bilder", farbe: "Farbe" },
    stil: "Stil", stilArt: { natur: "Natur", stadt: "Stadt", himmel: "Himmel", berge: "Berge", meer: "Meer", gemischt: "gemischt (jeden Tag ein anderer)" },
    wechsel: "Wechsel", wechselArt: { tageszeit: "nach Tageszeit", tageszeit_wetter: "nach Tageszeit, bei Regen/Schnee/Nebel Wetterbild", diashow: "Diashow" },
    diashowMin: "Diashow: Minuten je Bild", nachtsDunkler: "abends/nachts dunkler", jeZeit: "Eigenes Bild je Tageszeit (leer = Hauptbild)",
    zeitName: { morgen: "Sonnenaufgang", tag: "Tag", abend: "Sonnenuntergang", nacht: "Nacht" },
    bereich: "Bildbereich (Felder ← ↓ ↔ ↕; ganze Fläche = 0 0 48 27)", anpassung: "Füllart", anpassungArt: { fuellen: "füllen (zuschneiden)", einpassen: "einpassen (ganz sichtbar)", strecken: "strecken" },
    ausschnitt: "Ausschnitt", ausschnittArt: { mitte: "Mitte", oben: "oben", unten: "unten", links: "links", rechts: "rechts" }, ganzeFlaeche: "ganze Fläche", hauptbild: "Hauptbild", entfernenKurz: "✕",
    tzHinweis: "Tageszeit nach dem Sonnenstand am Standort (Reiter Verbindung): Sonnenaufgang und -untergang je etwa eine Stunde um den Zeitpunkt, dazwischen Tag bzw. Nacht.",
    abdunkeln: "links abdunkeln", bildHochladen: "Bild hochladen (JPG/PNG)", schema: "Farbschema",
    schemaArt: { dunkel: "hell auf dunkel", hell: "dunkel auf hell", gedimmt: "gedimmt (Nacht)" }, akzent: "Akzentfarbe",
    schrift: "Schrift", bausteinNeu: "Baustein hinzufügen", hinzu: "Hinzufügen", keinerGewaehlt: "Baustein antippen, um ihn einzustellen.",
    sichtbar: "sichtbar", karte: "als Karte (weißer Kasten)", ausrichtung: "Ausrichtung",
    ausrichtungArt: { "oben-links": "oben links", "oben-mitte": "oben Mitte", "oben-rechts": "oben rechts", links: "links", mitte: "Mitte",
                      rechts: "rechts", "unten-links": "unten links", "unten-mitte": "unten Mitte", "unten-rechts": "unten rechts" },
    position: "Position / Größe (Felder)", schriftEl: "Schriftart", wieLayout: "wie im Layout", textfarbe: "Textfarbe", textfarbeStd: "wie Farbschema", gewicht: "Schriftstärke",
    gewichtArt: { "": "automatisch", duenn: "dünn", normal: "normal", fett: "fett" }, schriftPos: "Position der Schrift",
    bedingung: "Nur zeigen, wenn …", bedingungEntity: "Entität (leer = immer zeigen)", vorne: "nach vorne", hinten: "nach hinten",
    entfernen: "Entfernen", groesser: "größer", kleiner: "kleiner", einstellen: "Einstellen",
    hinweisZiehen: "Ziehen = verschieben, Ecke unten rechts = Größe. Pfeiltasten verschieben den gewählten Baustein. Mehrmals auf dieselbe Stelle klicken wählt übereinanderliegende Bausteine nacheinander, Tab den nächsten.",
    ebenen: "Ebenen", ebenenText: "Oben = vorne (wie am Fernseher). Klick wählt aus.", nachVorne: "Nach vorne", nachHinten: "Nach hinten", einAus: "Ein-/ausblenden", verschieben: "Verschieben",
    hinweisHandy: "Auf dem Handy: Bausteine ein-/ausschalten und Größe ändern. Zum Verschieben PC oder Tablet nehmen.",
    gespeichert: "Gespeichert – die Fernseher übernehmen es in bis zu 15 s", wirklichLoeschen: "Layout löschen?",
    benutzt: "wird benutzt von", nichtLoeschbar: "Das Layout wird noch von einem Fernseher benutzt (auch im Zeitplan).",
    letztes: "Das letzte Layout kann nicht gelöscht werden.", importOk: "Layout importiert – Speichern nicht vergessen",
    ungespeichert: "Es gibt ungespeicherte Änderungen. Trotzdem wechseln?",
    typ: { uhr: "Uhr", datum: "Datum", temperatur: "Temperatur", wetterlage: "Wetterlage", feuchte: "Luftfeuchte", wind: "Wind",
           vorhersage: "Vorhersage", raeume: "Räume", kachel: "Kachel (HA-Wert)", video: "Live-Video", sender: "Radio-Sender",
           text: "Freier Text", logo: "Logo / Bild", kamera: "Kamera (HA)", kalender: "Kalender / Müllabfuhr", meldung: "Meldung von HA", flaeche: "Fläche (Farbe)",
           apiwert: "API-Wert", apiliste: "API-Liste / Feed", apibild: "API-Bild", anzeige: "Anzeige (Balken/Ampel)", countdown: "Countdown", qrcode: "QR-Code",
           webcam: "Kamera (Video)", diagramm: "Verlauf / Diagramm", webseite: "Webseite", unwetter: "Unwetterwarnung (DWD)" },
    opt: { sekunden: "mit Sekunden", wochentag: "mit Wochentag", jahr: "mit Jahr", entity: "Entität (aus HA)", tage: "Tage",
           liste: "Räume", name: "Beschriftung", icon: "Symbol (mdi-…)", leiste: "LIVE-Leiste zeigen", text: "Text",
           bild: "Bild hochladen (PNG mit durchsichtigem Hintergrund oder JPG)", laufband: "als Laufband (läuft durch)",
           intervall: "Bild erneuern alle (s)", anzahl: "Einträge", titel: "Überschrift", dauer: "anzeigen für (s)", farbe: "Farbe", deckkraft: "Deckkraft (%)",
           quelle: "Datenquelle", pfad: "Pfad in der Antwort", vorlage: "Vorlage (leer = nur der Wert)", einheit: "Einheit", nachkomma: "Nachkommastellen (-1 = wie geliefert)",
           faktor: "Faktor (z. B. 0,01 für cm → m)", zeile: "Zeile (Platzhalter je Eintrag)", anpassung: "Bild", darstellung: "Darstellung", min: "Minimum", max: "Maximum",
           gelb: "gelb ab", rot: "rot ab", umkehren: "umgekehrt (niedrige Werte schlecht)", ziel: "Ziel (Datum/Uhrzeit)", ende: "Text nach Ablauf",
           inhalt: "Inhalt (Text, Link oder WLAN-Daten)", beschriftung: "Beschriftung",
           immer: "auch ohne Warnung zeigen", ton: "mit Ton", stunden: "Zeitraum (Stunden)", url: "Adresse", neu_laden_min: "neu laden alle (min, 0 = nie)", zoom: "Zoom (%)",
           versatz_x: "Ausschnitt: von links (px)", versatz_y: "Ausschnitt: von oben (px)" },
    optHilfe: { temperatur: "leer = Wetter aus Einstellungen → Allgemein; oder ein Temperatur-Sensor", kamera: "z. B. Türklingel – mit Bedingung nur bei Klingeln zeigen",
                meldung: "Text-Entität in HA (z. B. input_text.tv_meldung). Ändert sich der Text, erscheint er als Banner.",
                kalender: "Kalender-Entität, z. B. Müllabfuhr (Waste Collection Schedule) oder Familienkalender – oder eine iCal-Datenquelle (dann ohne HA)",
                apiwert: "Wert aus einer Datenquelle (Reiter „Datenquellen“). Vorlage mit Platzhaltern, z. B. „{value} cm“ oder „{a.b} · {c}“; {quelle:pfad} holt Werte aus anderen Quellen.",
                apiliste: "Liste aus einer Datenquelle, z. B. RSS (Pfad „eintraege“, Zeile „{titel}“) oder eine JSON-Liste. In der Zeile beziehen sich Platzhalter auf den Eintrag, {.} = der Eintrag selbst.",
                apibild: "Bild-Quelle oder eine JSON-Quelle mit Pfad zu einer Bild-Adresse.",
                anzeige: "Zahl aus einer Datenquelle als Balken (Minimum–Maximum) oder Ampel (grün, gelb ab, rot ab).",
                countdown: "Ziel fest eintragen oder aus einer Datenquelle. Platzhalter: {tage}, {stunden}, {minuten}, {sekunden}.",
                qrcode: "Wird auf dem Fernseher erzeugt. WLAN: WIFI:T:WPA;S:Name;P:Passwort;; – Platzhalter {quelle:pfad} möglich.",
                text: "Platzhalter wie {quelle:pfad} werden durch Werte aus Datenquellen ersetzt.",
                webcam: "Kamera aus „Datenquellen“ (Art Kamera). Läuft nur, solange der Baustein sichtbar ist – z. B. mit Bedingung nur beim Klingeln.",
                diagramm: "Entweder eine HA-Entität (Verlauf aus der HA-Historie) oder Datenquelle + Pfad – deren Werte merkt sich SignageCast ab jetzt (bis 7 Tage).",
                webseite: "Nur Seiten, die das Einbetten erlauben („Prüfen“). Zoom und Ausschnitt wählen den sichtbaren Teil.",
                unwetter: "Amtliche Warnungen des Deutschen Wetterdienstes für den Standort (nur Deutschland). Ohne Warnung unsichtbar – oder „auch ohne Warnung zeigen“." },
    wahl: { balken: "Balken", ampel: "Ampel", einpassen: "einpassen (ganzes Bild)", fuellen: "füllen (zuschneiden)" },
    keineQuelle: "– Datenquelle wählen –", waehlen: "wählen …", bedQuelle: "Wert aus", bedHA: "Home Assistant", bedPfad: "Pfad",
    pruefen: "Prüfen", einbettbarJa: "Seite erlaubt das Einbetten", einbettbarNein: "Seite verbietet das Einbetten", einbettbarUnklar: "nicht prüfbar",
    raumNeu: "Raum hinzufügen", op: { "=": "ist gleich", "!=": "ist nicht", ">": "größer als", "<": "kleiner als", an: "ist an/offen", aus: "ist aus/zu" },
  },
  en: {
    alleLayouts: "All layouts", ausgangspunkt: "Start from", leeresLayout: "empty", vorlagenGruppe: "Templates", kopieVon: "Copy of",
    erstellen: "Create", abbrechen: "Cancel", bearbeitenL: "Edit", mehr: "More", nichtVerwendet: "not used",
    laeuftAuf: (n) => `shown on: ${n}`, laeuftHinweis: "Changes are visible on the TV right after saving.",
    nameFehlt: "Please enter a name.", verwerfen: "Discard unsaved changes?", hgFarben: "Background & colours",
    layout: "Layout", neu: "New layout", ausVorlage: "from template", duplizieren: "Copy", loeschen: "Delete",
    exportieren: "Export", importieren: "Import", rueckgaengig: "Undo", speichern: "Save",
    name: "Name", hintergrund: "Background", hgArt: { wetter: "Weather picture (by weather)", stil: "Picture set (by time of day)", bild: "own pictures", farbe: "Colour" },
    stil: "Style", stilArt: { natur: "Nature", stadt: "City", himmel: "Sky", berge: "Mountains", meer: "Sea", gemischt: "mixed (different every day)" },
    wechsel: "Change", wechselArt: { tageszeit: "by time of day", tageszeit_wetter: "by time of day, weather picture when rain/snow/fog", diashow: "Slideshow" },
    diashowMin: "Slideshow: minutes per picture", nachtsDunkler: "darker in the evening/at night", jeZeit: "Own picture per time of day (empty = main picture)",
    zeitName: { morgen: "Sunrise", tag: "Day", abend: "Sunset", nacht: "Night" },
    bereich: "Picture area (cells ← ↓ ↔ ↕; whole screen = 0 0 48 27)", anpassung: "Fit", anpassungArt: { fuellen: "fill (crop)", einpassen: "fit (whole picture)", strecken: "stretch" },
    ausschnitt: "Crop position", ausschnittArt: { mitte: "centre", oben: "top", unten: "bottom", links: "left", rechts: "right" }, ganzeFlaeche: "whole screen", hauptbild: "Main picture", entfernenKurz: "✕",
    tzHinweis: "Time of day from the sun position at your location (Connection tab): sunrise and sunset about one hour around the moment, otherwise day or night.",
    abdunkeln: "darken left side", bildHochladen: "Upload picture (JPG/PNG)", schema: "Colour scheme",
    schemaArt: { dunkel: "light on dark", hell: "dark on light", gedimmt: "dimmed (night)" }, akzent: "Accent colour",
    schrift: "Font", bausteinNeu: "Add element", hinzu: "Add", keinerGewaehlt: "Tap an element to configure it.",
    sichtbar: "visible", karte: "as card (white box)", ausrichtung: "Alignment",
    ausrichtungArt: { "oben-links": "top left", "oben-mitte": "top centre", "oben-rechts": "top right", links: "left", mitte: "centre",
                      rechts: "right", "unten-links": "bottom left", "unten-mitte": "bottom centre", "unten-rechts": "bottom right" },
    position: "Position / size (cells)", schriftEl: "Font", wieLayout: "as in layout", textfarbe: "Text colour", textfarbeStd: "as colour scheme", gewicht: "Font weight",
    gewichtArt: { "": "automatic", duenn: "thin", normal: "normal", fett: "bold" }, schriftPos: "Text position",
    bedingung: "Only show when …", bedingungEntity: "Entity (empty = always show)", vorne: "to front", hinten: "to back",
    entfernen: "Remove", groesser: "bigger", kleiner: "smaller", einstellen: "Configure",
    hinweisZiehen: "Drag = move, bottom-right corner = resize. Arrow keys move the selected element. Click the same spot repeatedly to cycle through stacked elements, Tab selects the next one.",
    ebenen: "Layers", ebenenText: "Top = front (as on the TV). Click to select.", nachVorne: "Bring forward", nachHinten: "Send backward", einAus: "Show/hide", verschieben: "Move",
    hinweisHandy: "On a phone: switch elements on/off and change their size. Use a PC or tablet to move them.",
    gespeichert: "Saved – the TVs pick it up within 15 s", wirklichLoeschen: "Delete layout?",
    benutzt: "used by", nichtLoeschbar: "This layout is still used by a TV (also in a schedule).",
    letztes: "The last layout cannot be deleted.", importOk: "Layout imported – don't forget to save",
    ungespeichert: "There are unsaved changes. Switch anyway?",
    typ: { uhr: "Clock", datum: "Date", temperatur: "Temperature", wetterlage: "Weather", feuchte: "Humidity", wind: "Wind",
           vorhersage: "Forecast", raeume: "Rooms", kachel: "Tile (HA value)", video: "Live video", sender: "Radio station",
           text: "Free text", logo: "Logo / picture", kamera: "Camera (HA)", kalender: "Calendar / waste collection", meldung: "Message from HA", flaeche: "Area (colour)",
           apiwert: "API value", apiliste: "API list / feed", apibild: "API picture", anzeige: "Gauge (bar/traffic light)", countdown: "Countdown", qrcode: "QR code",
           webcam: "Camera (video)", diagramm: "History / chart", webseite: "Web page", unwetter: "Weather warning (DWD)" },
    opt: { sekunden: "with seconds", wochentag: "with weekday", jahr: "with year", entity: "Entity (from HA)", tage: "Days",
           liste: "Rooms", name: "Label", icon: "Icon (mdi-…)", leiste: "show LIVE bar", text: "Text",
           bild: "Upload picture (PNG with transparent background or JPG)", laufband: "as ticker (scrolling)",
           intervall: "refresh picture every (s)", anzahl: "Entries", titel: "Heading", dauer: "show for (s)", farbe: "Colour", deckkraft: "Opacity (%)",
           quelle: "Data source", pfad: "Path in the response", vorlage: "Template (empty = value only)", einheit: "Unit", nachkomma: "Decimals (-1 = as delivered)",
           faktor: "Factor (e.g. 0.01 for cm → m)", zeile: "Row (placeholders per entry)", anpassung: "Picture", darstellung: "Display", min: "Minimum", max: "Maximum",
           gelb: "yellow from", rot: "red from", umkehren: "reversed (low values are bad)", ziel: "Target (date/time)", ende: "Text when reached",
           inhalt: "Content (text, link or Wi-Fi data)", beschriftung: "Caption",
           immer: "show also without warning", ton: "with sound", stunden: "Period (hours)", url: "Address", neu_laden_min: "reload every (min, 0 = never)", zoom: "Zoom (%)",
           versatz_x: "Crop: from left (px)", versatz_y: "Crop: from top (px)" },
    optHilfe: { temperatur: "empty = weather from Settings → General; or a temperature sensor", kamera: "e.g. doorbell – with a condition only when it rings",
                meldung: "Text entity in HA (e.g. input_text.tv_message). When the text changes it appears as a banner.",
                kalender: "Calendar entity, e.g. waste collection or family calendar – or an iCal data source (then without HA)",
                apiwert: "Value from a data source (tab “Data sources”). Template with placeholders, e.g. “{value} cm” or “{a.b} · {c}”; {source:path} takes values from other sources.",
                apiliste: "List from a data source, e.g. RSS (path “eintraege”, row “{titel}”) or a JSON list. In the row placeholders refer to the entry, {.} = the entry itself.",
                apibild: "Picture source, or a JSON source with a path to a picture address.",
                anzeige: "Number from a data source as a bar (minimum–maximum) or traffic light (green, yellow from, red from).",
                countdown: "Enter the target or take it from a data source. Placeholders: {tage} (days), {stunden} (hours), {minuten}, {sekunden}.",
                qrcode: "Generated on the TV. Wi-Fi: WIFI:T:WPA;S:name;P:password;; – placeholders {source:path} possible.",
                text: "Placeholders like {source:path} are replaced with values from data sources.",
                webcam: "Camera from “Data sources” (type camera). Only runs while the element is visible – e.g. with a condition only when the doorbell rings.",
                diagramm: "Either an HA entity (history from HA) or data source + path – SignageCast records its values from now on (up to 7 days).",
                webseite: "Only pages that allow embedding (“Check”). Zoom and crop choose the visible part.",
                unwetter: "Official warnings of the German Weather Service for the location (Germany only). Hidden without a warning – or “show also without warning”." },
    wahl: { balken: "Bar", ampel: "Traffic light", einpassen: "fit (whole picture)", fuellen: "fill (crop)" },
    keineQuelle: "– choose data source –", waehlen: "pick …", bedQuelle: "Value from", bedHA: "Home Assistant", bedPfad: "Path",
    pruefen: "Check", einbettbarJa: "page allows embedding", einbettbarNein: "page forbids embedding", einbettbarUnklar: "could not check",
    raumNeu: "Add room", op: { "=": "equals", "!=": "is not", ">": "greater than", "<": "less than", an: "is on/open", aus: "is off/closed" },
  },
};
const STD_GROESSE = { logo: [8, 4], uhr: [8, 3], datum: [9, 1], temperatur: [8, 2], wetterlage: [9, 1], feuchte: [9, 1], wind: [9, 1],
  vorhersage: [8, 5], raeume: [9, 5], kachel: [5, 5], video: [24, 14], sender: [9, 1], text: [12, 2], kamera: [12, 7],
  kalender: [10, 5], meldung: [24, 3], flaeche: [12, 4], apiwert: [8, 3], apiliste: [14, 6], apibild: [10, 8], anzeige: [8, 3],
  countdown: [10, 2], qrcode: [5, 6], webcam: [16, 9], diagramm: [12, 6], webseite: [16, 12], unwetter: [20, 3] };
// welche Arten von Datenquellen ein Baustein anbietet
const QUELL_ARTEN = { webcam: ["video"], kalender: ["ical"], apibild: ["bild", "json"], apiliste: ["json", "rss", "ical", "text"],
  diagramm: ["json", "text"], apiwert: ["json", "text", "rss", "ical"], anzeige: ["json", "text"], countdown: ["json", "text", "ical"] };
const WAHL = { darstellung: ["balken", "ampel"], anpassung: ["einpassen", "fuellen"] };
const ENT_DOMAINS = { temperatur: ["weather", "sensor"], wetterlage: ["weather"], feuchte: ["weather", "sensor"], wind: ["weather", "sensor"],
  kamera: ["camera"], kalender: ["calendar"], meldung: ["input_text", "sensor", "text"] };

let LS = null;            // Arbeitskopie aller Layouts
let LI = 0;               // gewähltes Layout
let GEWAEHLT = null;      // gewählter Baustein (id)
let letzterKlick = null;  // Stelle des letzten Klicks auf die Leinwand (Durchschalten übereinanderliegender Bausteine)
let VERLAUF = [];         // Rückgängig
let GEAENDERT = false;
let VORSCHAU = null;      // Werte für die Vorschau
let ANSICHT = "liste";    // seit 0.17.2: „liste“ (Kacheln aller Layouts) oder „editor“ (ein Layout)

async function layoutSeite(inhalt) {
  const L = LTEXTE[E.sprache] || LTEXTE.de;
  if (!LS) { LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; ANSICHT = "liste"; }
  const [ents, vorl, vd] = await Promise.all([entitaeten(), holen("/api/vorlagen"), holen("/api/vorschau/daten?tv=" + encodeURIComponent(E.fernseher[0].id)).catch(() => null)]);
  VORSCHAU = vd && vd.ok ? vd : null;
  const handy = () => window.innerWidth < 700;
  const lay = () => LS[LI];
  const merken = () => { VERLAUF.push(JSON.stringify(LS)); if (VERLAUF.length > 40) VERLAUF.shift(); GEAENDERT = true; };
  const nutzer = (id) => E.fernseher.filter((t) => t.layout === id || (t.zeitplan || []).some((z) => z.layout === id)).map((t) => t.name);

  const offen = () => { const d = inhalt.querySelector("details"); if (d) d.open = true; };
  const zeichnen = () => {
    const l = lay();
    inhalt.innerHTML = `<datalist id="ents">${ents.map((x) => `<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("")}</datalist>
      <div class="karte">
        <div class="zeile layoutkopf"><button class="knopf" id="lListe">← ${esc(L.alleLayouts)}</button>
          <input type="text" id="lName" class="layoutname" value="${esc(l.name)}" aria-label="${esc(L.name)}">
          <span class="leer"></span>
          <button class="knopf" id="lZurueck" ${VERLAUF.length ? "" : "disabled"}>${esc(L.rueckgaengig)}</button>
          <button class="knopf haupt" id="lSpeichern">${esc(L.speichern)}${GEAENDERT ? " *" : ""}</button></div>
        ${nutzer(l.id).length ? `<p class="laeuft">● ${esc(L.laeuftAuf(nutzer(l.id).join(", ")))} – ${esc(L.laeuftHinweis)}</p>` : `<p class="leise">${esc(L.nichtVerwendet)}</p>`}
        <details><summary>${esc(L.hgFarben)}</summary>
          <div class="zeile"><label>${esc(L.hintergrund)}</label><select id="hgArt">${Object.keys(L.hgArt).map((k) => `<option value="${k}" ${k === l.hintergrund.art ? "selected" : ""}>${esc(L.hgArt[k])}</option>`).join("")}</select></div>
          <div class="eintrag" id="hgStil" ${l.hintergrund.art === "stil" ? "" : "hidden"}>
            <div class="zeile"><label>${esc(L.stil)}</label><select id="hgStilWahl">${Object.keys(L.stilArt).map((k) => `<option value="${k}" ${k === l.hintergrund.stil ? "selected" : ""}>${esc(L.stilArt[k])}</option>`).join("")}</select></div>
            <div class="stilbilder" id="stilBilder"></div>
            <div class="zeile"><label>${esc(L.wechsel)}</label><select id="hgWechsel">${Object.keys(L.wechselArt).map((k) => `<option value="${k}" ${k === l.hintergrund.wechsel ? "selected" : ""}>${esc(L.wechselArt[k])}</option>`).join("")}</select></div>
            <div class="zeile" ${l.hintergrund.wechsel === "diashow" ? "" : "hidden"} id="hgDiaZeile"><label>${esc(L.diashowMin)}</label><input type="number" id="hgDia" min="1" max="120" value="${l.hintergrund.diashow_min}"></div>
            <p class="leise">${esc(L.tzHinweis)}</p></div>
          <div class="eintrag" id="hgEigen" ${l.hintergrund.art === "bild" ? "" : "hidden"}>
            <div class="zeile"><label>${esc(L.hauptbild)}</label><input type="file" data-zeit="" accept="image/jpeg,image/png"><span class="leise">${esc(l.hintergrund.bild || "")}</span></div>
            <p class="leise">${esc(L.jeZeit)}</p>
            ${["morgen", "tag", "abend", "nacht"].map((z) => `<div class="zeile"><label>${esc(L.zeitName[z])}</label><input type="file" data-zeit="${z}" accept="image/jpeg,image/png">
              <span class="leise">${esc(l.hintergrund.bilder_tageszeit[z] || "")}</span>${l.hintergrund.bilder_tageszeit[z] ? `<button class="knopf gefahr" data-weg="${z}">${esc(L.entfernenKurz)}</button>` : ""}</div>`).join("")}</div>
          <div class="zeile" id="hgFarbZeile" ${l.hintergrund.art === "farbe" ? "" : "hidden"}><label>${esc(L.hgArt.farbe)}</label><input type="color" id="hgFarbe" value="${esc(l.hintergrund.farbe)}"></div>
          <div class="zeile"><label>${esc(L.bereich)}</label></div>
          <div class="zeile pos">${["x", "y", "w", "h"].map((k) => `<label>${{ x: "←", y: "↓", w: "↔", h: "↕" }[k]}<input type="number" data-bereich="${k}" value="${l.hintergrund.bereich[k]}"></label>`).join("")}
            <button class="knopf" id="hgGanz">${esc(L.ganzeFlaeche)}</button></div>
          <div class="zeile"><label>${esc(L.anpassung)}</label><select id="hgAnpassung">${Object.keys(L.anpassungArt).map((k) => `<option value="${k}" ${k === l.hintergrund.anpassung ? "selected" : ""}>${esc(L.anpassungArt[k])}</option>`).join("")}</select>
            <label>${esc(L.ausschnitt)}</label><select id="hgAusschnitt">${Object.keys(L.ausschnittArt).map((k) => `<option value="${k}" ${k === l.hintergrund.ausschnitt ? "selected" : ""}>${esc(L.ausschnittArt[k])}</option>`).join("")}</select></div>
          <div class="zeile"><label><input type="checkbox" id="hgNacht" ${l.hintergrund.nachts_dunkler ? "checked" : ""}> ${esc(L.nachtsDunkler)}</label>
            <label><input type="checkbox" id="hgDunkel" ${l.hintergrund.abdunkeln ? "checked" : ""}> ${esc(L.abdunkeln)}</label></div>
          <div class="zeile"><label>${esc(L.schema)}</label><select id="thSchema">${Object.keys(L.schemaArt).map((k) => `<option value="${k}" ${k === l.thema.schema ? "selected" : ""}>${esc(L.schemaArt[k])}</option>`).join("")}</select>
            <label>${esc(L.akzent)}</label><input type="color" id="thAkzent" value="${esc(l.thema.akzent)}">
            <label>${esc(L.schrift)}</label><select id="thSchrift">${SCHRIFTEN.map((k) => `<option style="font-family:'${esc(k)}'" ${k === l.thema.schrift ? "selected" : ""}>${esc(k)}</option>`).join("")}</select></div>
        </details>
        <div class="zeile"><select id="bTyp">${Object.keys(L.typ).map((k) => `<option value="${k}">${esc(L.typ[k])}</option>`).join("")}</select>
          <button class="knopf" id="bNeu">${esc(L.bausteinNeu)}</button></div>
        <p class="leise">${esc(handy() ? L.hinweisHandy : L.hinweisZiehen)}</p>
      </div>
      <div class="layoutbereich"><div id="leinwandRahmen"></div><div class="lw-seite">${handy() ? "" : `<div class="karte" id="ebenen"></div>`}<div class="karte" id="eigenschaften"></div></div></div>`;
    if (handy()) listeZeichnen(); else leinwandZeichnen();
    eigenschaftenZeichnen();
    // Kopf
    $("#lListe").onclick = () => {
      if (GEAENDERT && !confirm(L.verwerfen)) return;
      LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; GEWAEHLT = null; ANSICHT = "liste"; listeAlle();
    };
    $("#lSpeichern").onclick = (e) => aktion(e.target, async () => {
      await speichernE({ layouts: LS }); LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; zeichnen();
    }, L.gespeichert);
    $("#lZurueck").onclick = () => { if (VERLAUF.length) { LS = JSON.parse(VERLAUF.pop()); LI = Math.min(LI, LS.length - 1); GEAENDERT = true; zeichnen(); } };
    const kopf = (f) => () => { merken(); f(); GEAENDERT = true; $("#lSpeichern").textContent = L.speichern + " *"; if (!handy()) leinwandZeichnen(); };
    $("#lName").oninput = kopf(() => { lay().name = $("#lName").value; });
    $("#hgArt").onchange = () => { merken(); lay().hintergrund.art = $("#hgArt").value; zeichnen(); offen(); };
    $("#hgStilWahl").onchange = () => { merken(); lay().hintergrund.stil = $("#hgStilWahl").value; zeichnen(); offen(); };
    $("#hgWechsel").onchange = () => { merken(); lay().hintergrund.wechsel = $("#hgWechsel").value; zeichnen(); offen(); };
    $("#hgDia").onchange = kopf(() => { lay().hintergrund.diashow_min = Number($("#hgDia").value); });
    $("#hgNacht").onchange = kopf(() => { lay().hintergrund.nachts_dunkler = $("#hgNacht").checked; });
    $("#hgAnpassung").onchange = kopf(() => { lay().hintergrund.anpassung = $("#hgAnpassung").value; });
    $("#hgAusschnitt").onchange = kopf(() => { lay().hintergrund.ausschnitt = $("#hgAusschnitt").value; });
    inhalt.querySelectorAll("[data-bereich]").forEach((i) => { i.onchange = kopf(() => { lay().hintergrund.bereich[i.dataset.bereich] = Number(i.value) || 0; }); });
    $("#hgGanz").onclick = () => { merken(); lay().hintergrund.bereich = { x: 0, y: 0, w: 48, h: 27 }; zeichnen(); offen(); };
    stilBilderZeigen(lay().hintergrund.stil);
    inhalt.querySelectorAll("#hgEigen input[type=file]").forEach((inp) => {
      inp.onchange = () => aktion(null, async () => {
        const f = inp.files[0]; if (!f) return;
        const b64 = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(r.result); r.readAsDataURL(f); });
        const d = await senden("/api/bilder", { daten: b64 });
        merken();
        if (inp.dataset.zeit) lay().hintergrund.bilder_tageszeit[inp.dataset.zeit] = d.bild; else lay().hintergrund.bild = d.bild;
        zeichnen(); offen();
      });
    });
    inhalt.querySelectorAll("#hgEigen [data-weg]").forEach((k) => {
      k.onclick = () => { merken(); lay().hintergrund.bilder_tageszeit[k.dataset.weg] = ""; zeichnen(); offen(); };
    });
    $("#hgFarbe").oninput = kopf(() => { lay().hintergrund.farbe = $("#hgFarbe").value; });
    $("#hgDunkel").onchange = kopf(() => { lay().hintergrund.abdunkeln = $("#hgDunkel").checked; });
    $("#thSchema").onchange = kopf(() => { lay().thema.schema = $("#thSchema").value; });
    $("#thAkzent").oninput = kopf(() => { lay().thema.akzent = $("#thAkzent").value; });
    $("#thSchrift").onchange = kopf(() => { lay().thema.schrift = $("#thSchrift").value; });
    $("#bNeu").onclick = () => {
      merken();
      const typ = $("#bTyp").value, [w, h] = STD_GROESSE[typ] || [6, 2];
      const e = { id: neueId().slice(0, 8), typ, x: 1, y: 1, w, h, sichtbar: true, karte: ["kachel", "vorhersage", "kalender"].includes(typ),
                  ausrichtung: "links", optionen: JSON.parse(JSON.stringify(BAUSTEINE[typ] || {})), bedingung: null };
      lay().elemente.push(e); GEWAEHLT = e.id; zeichnen();
    };
  };

  // ---------- Übersicht aller Layouts (seit 0.17.2) – Aktionen hier speichern sofort ----------
  const sofortSpeichern = async () => { await speichernE({ layouts: LS }); LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; };
  const oeffnen = (i) => { LI = i; GEWAEHLT = null; ANSICHT = "editor"; zeichnen(); window.scrollTo(0, 0); };
  const miniVorschau = (l) => {
    const hg = l.hintergrund.art === "farbe" ? l.hintergrund.farbe : "linear-gradient(160deg,#55606b,#2b3138)";
    return `<div class="mini" style="background:${esc(hg)}">${l.elemente.filter((x) => x.sichtbar).map((x) =>
      `<span class="mini-el ${x.typ === "video" ? "video" : x.karte || x.typ === "flaeche" ? "karte" : ""}" style="left:${x.x / 48 * 100}%;top:${x.y / 27 * 100}%;width:${x.w / 48 * 100}%;height:${x.h / 27 * 100}%"></span>`).join("")}</div>`;
  };
  const bildNamen = (l) => [...new Set([l.hintergrund.bild, ...Object.values(l.hintergrund.bilder_tageszeit || {}),
    ...l.elemente.map((x) => x.optionen && x.optionen.bild)].filter((n) => /^[0-9a-f]{16}\.(jpg|png)$/.test(n || "")))];
  // Export (seit 0.13.1) mit allen verwendeten Bildern – so lässt sich ein Layout auf eine andere Installation mitnehmen
  const exportieren = (l) => aktion(null, async () => {
    const bilder = {};
    for (const n of bildNamen(l)) {
      const roh = await dienstBinaer.get(`/bild/${n}`, {}, {});
      let bin = ""; for (let i = 0; i < roh.length; i += 0x8000) bin += String.fromCharCode(...roh.subarray(i, i + 0x8000));
      bilder[n] = `data:image/${n.endsWith(".png") ? "png" : "jpeg"};base64,` + btoa(bin);
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify({ art: "signagecast-layout", version: 2, layout: l, bilder }, null, 1)], { type: "application/json" }));
    a.download = `signagecast-layout-${l.name.replace(/[^\w-]+/g, "_")}.json`;
    document.body.appendChild(a); a.click(); a.remove();
  }, null);
  const importieren = async (datei) => aktion(null, async () => {
    const d = JSON.parse(await datei.text());
    const l2 = ["signagecast-layout", "tv-stream-layout"].includes(d.art) ? d.layout : d;
    if (!l2 || !Array.isArray(l2.elemente)) throw new Error("kein Layout");
    // mitgelieferte Bilder hochladen und Namen im Layout anpassen (der Name ergibt sich aus dem Inhalt)
    const neu = {};
    for (const [n, daten] of Object.entries(d.bilder || {})) neu[n] = (await senden("/api/bilder", { daten })).bild;
    const um = (n) => neu[n] || n;
    l2.hintergrund = l2.hintergrund || {};
    if (l2.hintergrund.bild) l2.hintergrund.bild = um(l2.hintergrund.bild);
    for (const k of Object.keys(l2.hintergrund.bilder_tageszeit || {})) l2.hintergrund.bilder_tageszeit[k] = um(l2.hintergrund.bilder_tageszeit[k]);
    for (const x of l2.elemente) if (x.optionen && x.optionen.bild) x.optionen.bild = um(x.optionen.bild);
    l2.id = neueId(); LS.push(l2); await sofortSpeichern(); listeAlle();
  }, L.importOk);
  const listeAlle = () => {
    inhalt.innerHTML = `<div class="layoutkacheln">${LS.map((l, i) => {
      const n = nutzer(l.id);
      return `<div class="karte layoutkachel" data-i="${i}">${miniVorschau(l)}
        <b class="lk-name">${esc(l.name)}</b>
        <span class="${n.length ? "laeuft" : "leise"}">${n.length ? "● " + esc(L.laeuftAuf(n.join(", "))) : esc(L.nichtVerwendet)}</span>
        <div class="zeile"><button class="knopf haupt" data-a="b">${esc(L.bearbeitenL)}</button>
          <details class="mehr"><summary class="knopf">⋯</summary><div class="mehr-menue">
            <button class="knopf" data-a="k">${esc(L.duplizieren)}</button><button class="knopf" data-a="x">${esc(L.exportieren)}</button>
            <button class="knopf gefahr" data-a="l">${esc(L.loeschen)}</button></div></details></div></div>`;
    }).join("")}
      <div class="karte layoutkachel neu" id="lNeuKachel"><button class="neu-knopf" id="lNeu"><span>＋</span>${esc(L.neu)}</button>
        <label class="leise importlink">${esc(L.importieren)} …<input type="file" id="lImport" accept=".json" hidden></label></div></div>`;
    inhalt.querySelectorAll(".layoutkachel[data-i]").forEach((k) => {
      const i = Number(k.dataset.i), l = LS[i];
      k.querySelector(".mini").onclick = () => oeffnen(i);
      k.querySelectorAll("[data-a]").forEach((b) => { b.onclick = (ev) => {
        const a = b.dataset.a;
        if (a === "b") return oeffnen(i);
        if (a === "x") return exportieren(l);
        if (a === "k") return aktion(ev.target, async () => {
          const c = JSON.parse(JSON.stringify(l)); c.id = neueId(); c.name += " (2)"; LS.push(c); await sofortSpeichern(); listeAlle(); });
        if (a === "l") {
          if (LS.length < 2) return melden(L.letztes, true);
          if (nutzer(l.id).length) return melden(L.nichtLoeschbar, true);
          if (!confirm(L.wirklichLoeschen + " „" + l.name + "“")) return;
          aktion(ev.target, async () => { LS.splice(i, 1); LI = 0; await sofortSpeichern(); listeAlle(); });
        }
      }; });
    });
    $("#lImport").onchange = (e) => { if (e.target.files[0]) importieren(e.target.files[0]); };
    $("#lNeu").onclick = () => {
      $("#lNeuKachel").innerHTML = `<h3>${esc(L.neu)}</h3>
        <div class="zeile"><label>${esc(L.name)}</label><input type="text" id="lnName" data-frei></div>
        <div class="zeile"><label>${esc(L.ausgangspunkt)}</label><select id="lnBasis" class="breit">
          <option value="leer">${esc(L.leeresLayout)}</option>
          <optgroup label="${esc(L.vorlagenGruppe)}">${vorl.vorlagen.map((v, j) => `<option value="v${j}">${esc(v.name)}</option>`).join("")}</optgroup>
          <optgroup label="${esc(L.kopieVon)}">${LS.map((x, j) => `<option value="k${j}">${esc(x.name)}</option>`).join("")}</optgroup></select></div>
        <div class="zeile"><button class="knopf" id="lnAb">${esc(L.abbrechen)}</button><button class="knopf haupt" id="lnOk">${esc(L.erstellen)}</button></div>`;
      $("#lnName").focus();
      $("#lnAb").onclick = listeAlle;
      $("#lnOk").onclick = (ev) => aktion(ev.target, async () => {
        const name = $("#lnName").value.trim();
        if (!name) throw new Error(L.nameFehlt);
        const b = $("#lnBasis").value;
        const quelle = b === "leer" ? Object.assign(JSON.parse(JSON.stringify(vorl.vorlagen[0])), { elemente: [] })
          : b[0] === "v" ? vorl.vorlagen[Number(b.slice(1))] : LS[Number(b.slice(1))];
        const l = JSON.parse(JSON.stringify(quelle)); l.id = neueId(); l.name = name;
        LS.push(l); await sofortSpeichern(); oeffnen(LS.length - 1);
      }, null);
      $("#lnName").onkeydown = (e) => { if (e.key === "Enter") $("#lnOk").click(); };
    };
  };

  // ---------- Leinwand (PC/Tablet) ----------
  const leinwandZeichnen = () => {
    const l = lay(), rahmen = $("#leinwandRahmen");
    rahmen.innerHTML = `<div class="leinwand" id="leinwand" tabindex="0"></div>`;
    const lw = $("#leinwand");
    const massstab = () => lw.clientWidth / 1920;
    lw.style.background = l.hintergrund.art === "farbe" ? l.hintergrund.farbe : "linear-gradient(160deg,#55606b,#2b3138)";
    l.elemente.forEach((e, idx) => {
      const b = document.createElement("div");
      b.className = "lw-baustein" + (e.id === GEWAEHLT ? " gewaehlt" : "") + (e.sichtbar ? "" : " aus") + (e.karte ? " karte" : "") +
                    (l.thema.schema === "hell" ? " hell" : "") + " lwtyp-" + e.typ;
      b.style.zIndex = idx + 1;
      if (e.typ === "flaeche") b.style.background = e.optionen.farbe || "#f0f0f0";
      b.dataset.id = e.id;
      b.innerHTML = `<span class="lw-text">${esc(vorschauText(e, L))}</span>`;
      const [v, h] = (e.ausrichtung || "links").includes("-") ? e.ausrichtung.split("-") : ["mitte", e.ausrichtung || "links"];
      const ach = { links: "flex-start", oben: "flex-start", mitte: "center", rechts: "flex-end", unten: "flex-end" };
      Object.assign(b.style, { justifyContent: ach[v], alignItems: ach[h], textAlign: { links: "left", mitte: "center", rechts: "right" }[h],
                               fontFamily: e.schrift ? `'${e.schrift}', sans-serif` : "", fontWeight: { duenn: 200, normal: 400, fett: 700 }[e.gewicht] || "" });
      setzen(b, e);
      b.onpointerdown = (ev) => klicken(ev, b);
      lw.appendChild(b);
    });
    // Auswahlrahmen über allem (seit 0.17.1): der gewählte Baustein bleibt auf seiner Ebene, Rahmen, Griff und
    // Verschiebe-Knopf liegen obenauf – so bleiben kleinere Bausteine davor anklickbar.
    const gew = l.elemente.find((x) => x.id === GEWAEHLT);
    if (gew) {
      const rahmen = document.createElement("div");
      rahmen.className = "lw-auswahl"; rahmen.id = "lwAuswahl";
      rahmen.innerHTML = `<span class="lw-schieber" title="${esc(L.verschieben)}">✥</span><span class="lw-griff"></span>`;
      setzen(rahmen, gew);
      const b = lw.querySelector(`[data-id="${gew.id}"]`);
      rahmen.querySelector(".lw-griff").onpointerdown = (ev) => ziehen(ev, gew, b, true);
      rahmen.querySelector(".lw-schieber").onpointerdown = (ev) => ziehen(ev, gew, b, false);
      lw.appendChild(rahmen);
    }
    ebenenZeichnen();
    lw.onkeydown = (ev) => {
      const e = lay().elemente.find((x) => x.id === GEWAEHLT);
      const d = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[ev.key];
      if (ev.key === "Tab") {                       // Tab / Umschalt+Tab: nächster / voriger Baustein
        const els = lay().elemente;
        if (!els.length) return;
        ev.preventDefault();
        const i = els.findIndex((x) => x.id === GEWAEHLT);
        GEWAEHLT = els[(i + (ev.shiftKey ? -1 : 1) + els.length) % els.length].id;
        leinwandZeichnen(); eigenschaftenZeichnen(); $("#leinwand").focus();
        return;
      }
      if (!e || !d) return;
      ev.preventDefault(); merken();
      if (ev.shiftKey) { e.w = klemm(e.w + d[0], 1, 48 - e.x); e.h = klemm(e.h + d[1], 1, 27 - e.y); }
      else { e.x = klemm(e.x + d[0], 0, 48 - e.w); e.y = klemm(e.y + d[1], 0, 27 - e.h); }
      leinwandZeichnen(); eigenschaftenZeichnen(); $("#leinwand").focus();
    };
    function setzen(b, e) {
      const m = 100 / 48, n = 100 / 27;
      Object.assign(b.style, { left: e.x * m + "%", top: e.y * n + "%", width: e.w * m + "%", height: e.h * n + "%" });
    }
    // Klick auf die Leinwand: oberster Baustein an der Stelle; erneuter Klick auf dieselbe Stelle wählt den darunter
    function klicken(ev, b) {
      const stapel = document.elementsFromPoint(ev.clientX, ev.clientY).filter((x) => x.classList.contains("lw-baustein"));
      const nah = letzterKlick && Math.abs(letzterKlick[0] - ev.clientX) < 5 && Math.abs(letzterKlick[1] - ev.clientY) < 5;
      const vorher = stapel.findIndex((x) => x.dataset.id === GEWAEHLT);
      const ziel = nah && vorher >= 0 && stapel.length > 1 ? stapel[(vorher + 1) % stapel.length] : stapel[0] || b;
      letzterKlick = [ev.clientX, ev.clientY];
      ziehen(ev, lay().elemente.find((x) => x.id === ziel.dataset.id), ziel, false);
    }
    function ziehen(ev, e, b, groesse) {
      ev.preventDefault();
      if (GEWAEHLT !== e.id) { GEWAEHLT = e.id; leinwandZeichnen(); eigenschaftenZeichnen(); b = $("#leinwand").querySelector(`[data-id="${e.id}"]`); }
      const rahmen = $("#lwAuswahl");
      const feld = 40 * massstab(), sx = ev.clientX, sy = ev.clientY, start = { ...e };
      let bewegt = false;
      const fang = ev.target.isConnected ? ev.target : rahmen;
      fang.setPointerCapture(ev.pointerId);
      fang.onpointermove = (mv) => {
        const dx = Math.round((mv.clientX - sx) / feld), dy = Math.round((mv.clientY - sy) / feld);
        if (!bewegt && (dx || dy)) { merken(); bewegt = true; }
        if (groesse) { e.w = klemm(start.w + dx, 1, 48 - e.x); e.h = klemm(start.h + dy, 1, 27 - e.y); }
        else { e.x = klemm(start.x + dx, 0, 48 - e.w); e.y = klemm(start.y + dy, 0, 27 - e.h); }
        setzen(b, e); if (rahmen) setzen(rahmen, e);
      };
      fang.onpointerup = () => { fang.onpointermove = null; fang.onpointerup = null; if (bewegt) { $("#lSpeichern").textContent = L.speichern + " *"; eigenschaftenZeichnen(); } $("#leinwand").focus(); };
    }
  };

  // ---------- Ebenen (seit 0.17.1): oben = vorne; Reihenfolge der Elemente = Reihenfolge am Fernseher ----------
  const ebenenZeichnen = () => {
    const ziel = $("#ebenen");
    if (!ziel) return;
    const els = lay().elemente;
    ziel.innerHTML = `<h3>${esc(L.ebenen)}</h3><p class="leise">${esc(L.ebenenText)}</p><div class="ebenen"></div>`;
    const liste = ziel.querySelector(".ebenen");
    [...els].reverse().forEach((e) => {
      const i = els.indexOf(e);
      const z = el(`<div class="ebene ${e.id === GEWAEHLT ? "gewaehlt" : ""} ${e.sichtbar ? "" : "aus"}">
        <span class="ebene-name"><b>${esc(L.typ[e.typ] || e.typ)}</b> <span class="leise">${esc(vorschauText(e, L)).slice(0, 28)}</span></span>
        <button class="knopf klein" data-a="s" title="${esc(L.einAus)}"><i class="mdi ${e.sichtbar ? "mdi-eye" : "mdi-eye-off"}"></i></button>
        <button class="knopf klein" data-a="v" title="${esc(L.nachVorne)}" ${i === els.length - 1 ? "disabled" : ""}><i class="mdi mdi-arrow-up"></i></button>
        <button class="knopf klein" data-a="h" title="${esc(L.nachHinten)}" ${i === 0 ? "disabled" : ""}><i class="mdi mdi-arrow-down"></i></button></div>`);
      z.onclick = (ev) => {
        const a = ev.target.closest("[data-a]")?.dataset.a;
        if (a) {
          merken(); GEAENDERT = true; $("#lSpeichern").textContent = L.speichern + " *";
          if (a === "s") e.sichtbar = !e.sichtbar;
          else { const j = a === "v" ? i + 1 : i - 1; [els[i], els[j]] = [els[j], els[i]]; }
        }
        GEWAEHLT = e.id;
        leinwandZeichnen(); eigenschaftenZeichnen();
      };
      liste.appendChild(z);
    });
  };

  // ---------- Liste (Handy) ----------
  const listeZeichnen = () => {
    const rahmen = $("#leinwandRahmen");
    rahmen.innerHTML = "";
    lay().elemente.forEach((e) => {
      const z = el(`<div class="eintrag zeile ${e.id === GEWAEHLT ? "gewaehlt" : ""}"><b style="flex:1">${esc(L.typ[e.typ] || e.typ)}</b>
        <span class="leise">${esc(vorschauText(e, L)).slice(0, 24)}</span>${schalter("s", e.sichtbar)}
        <button class="knopf" data-a="-" aria-label="${esc(L.kleiner)}">−</button><button class="knopf" data-a="+" aria-label="${esc(L.groesser)}">+</button>
        <button class="knopf" data-a="e">${esc(L.einstellen)}</button></div>`);
      z.querySelector("input").onchange = (ev) => { merken(); e.sichtbar = ev.target.checked; zeichnen(); };
      z.querySelectorAll("[data-a]").forEach((k) => {
        k.onclick = () => {
          if (k.dataset.a === "e") { GEWAEHLT = e.id; eigenschaftenZeichnen(); $("#eigenschaften").scrollIntoView({ behavior: "smooth" }); return; }
          merken();
          const f = k.dataset.a === "+" ? 1.25 : 0.8;
          e.w = klemm(Math.round(e.w * f) || 1, 1, 48 - e.x); e.h = klemm(Math.round(e.h * f) || 1, 1, 27 - e.y);
          zeichnen();
        };
      });
      rahmen.appendChild(z);
    });
  };

  // ---------- Eigenschaften des gewählten Bausteins ----------
  const eigenschaftenZeichnen = () => {
    const ziel = $("#eigenschaften");
    const e = lay().elemente.find((x) => x.id === GEWAEHLT);
    if (!e) { ziel.innerHTML = `<p class="leise">${esc(L.keinerGewaehlt)}</p>`; return; }
    const o = e.optionen, b = e.bedingung || {};
    const feld = (k) => {
      const w = o[k], lab = esc(L.opt[k] || k);
      if (k === "liste") return `<h3>${lab}</h3><div id="raumListe">${(w || []).map((r, i) => `<div class="zeile" data-i="${i}">
          <input type="text" name="rn" value="${esc(r.name)}" placeholder="Name" style="width:120px"><input type="text" name="re" list="ents" value="${esc(r.entity)}" placeholder="sensor.…">
          <button class="knopf gefahr" name="rw">✕</button></div>`).join("")}</div><button class="knopf" id="raumPlus">${esc(L.raumNeu)}</button>`;
      if (typeof w === "boolean") return `<div class="zeile"><label>${lab}</label>${schalter("o_" + k, w)}</div>`;
      if (k === "quelle") return `<div class="zeile"><label>${lab}</label><select name="o_quelle"><option value="">${esc(L.keineQuelle)}</option>
        ${(E.quellen || []).filter((q) => !QUELL_ARTEN[e.typ] || QUELL_ARTEN[e.typ].includes(q.art) || q.id === w)
            .map((q) => `<option value="${esc(q.id)}" ${q.id === w ? "selected" : ""}>${esc(q.name)} (${esc(q.id)})</option>`).join("")}</select></div>`;
      if (k === "url") return `<div class="zeile"><label>${lab}</label><input type="text" name="o_url" value="${esc(w ?? "")}" spellcheck="false" style="width:100%">
        <button class="knopf" type="button" name="urlPruefen">${esc(L.pruefen)}</button><span class="leise" id="urlErg"></span></div>`;
      if (k === "pfad") return `<div class="zeile"><label>${lab}</label><input type="text" name="o_pfad" value="${esc(w ?? "")}" spellcheck="false">
        <button class="knopf" type="button" name="pfadWahl">${esc(L.waehlen)}</button></div><div class="pfadBaum"></div>`;
      if (WAHL[k]) return `<div class="zeile"><label>${lab}</label><select name="o_${k}">${WAHL[k].map((x) => `<option value="${x}" ${x === w ? "selected" : ""}>${esc(L.wahl[x] || x)}</option>`).join("")}</select></div>`;
      if (k === "ziel") return `<div class="zeile"><label>${lab}</label><input type="datetime-local" name="o_ziel" value="${esc(w || "")}"></div>`;
      if (k === "bild") return `<div class="zeile"><label>${lab}</label><input type="file" name="o_bildDatei" accept="image/png,image/jpeg">
        <span class="leise">${esc(w || "")}</span></div>`;
      if (k === "farbe") return `<div class="zeile"><label>${lab}</label><input type="color" name="o_${k}" value="${esc(w || "#f0f0f0")}"></div>`;
      if (typeof w === "number") return `<div class="zeile"><label>${lab}</label><input type="number" step="any" name="o_${k}" value="${w}"></div>`;
      const liste = k === "entity" ? ' list="ents"' : "";
      return `<div class="zeile"><label>${lab}</label><input type="text" name="o_${k}" value="${esc(w ?? "")}"${liste}>${k === "icon" ? `<span class="icon mdi ${esc(w || "")}"></span>` : ""}</div>`;
    };
    ziel.innerHTML = `<h2>${esc(L.typ[e.typ] || e.typ)}</h2>${L.optHilfe[e.typ] ? `<p class="leise">${esc(L.optHilfe[e.typ])}</p>` : ""}
      ${Object.keys(o).map(feld).join("")}
      <div class="zeile"><label>${esc(L.sichtbar)}</label>${schalter("sichtbar", e.sichtbar)}</div>
      <div class="zeile"><label>${esc(L.karte)}</label>${schalter("karte", e.karte)}</div>
      <div class="zeile"><label>${esc(L.schriftPos)}</label><input type="hidden" name="ausrichtung" value="${esc(e.ausrichtung || "links")}">
        <div class="neuner">${["oben-links", "oben-mitte", "oben-rechts", "links", "mitte", "rechts", "unten-links", "unten-mitte", "unten-rechts"].map((k) =>
          `<button type="button" class="${k === (e.ausrichtung || "links") ? "an" : ""}" data-pos="${k}" title="${esc(L.ausrichtungArt[k])}" aria-label="${esc(L.ausrichtungArt[k])}"></button>`).join("")}</div></div>
      <div class="zeile"><label>${esc(L.schriftEl)}</label><select name="schrift"><option value="">${esc(L.wieLayout)}</option>
        ${SCHRIFTEN.map((k) => `<option value="${esc(k)}" style="font-family:'${esc(k)}'" ${k === e.schrift ? "selected" : ""}>${esc(k)}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(L.textfarbe)}</label><input type="color" name="textfarbe" value="${esc(e.textfarbe || "#ffffff")}">
        <label><input type="checkbox" name="textfarbeStd" ${e.textfarbe ? "" : "checked"}> ${esc(L.textfarbeStd)}</label></div>
      <div class="zeile"><label>${esc(L.gewicht)}</label><select name="gewicht">${Object.keys(L.gewichtArt).map((k) => `<option value="${k}" ${k === (e.gewicht || "") ? "selected" : ""}>${esc(L.gewichtArt[k])}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(L.position)}</label></div>
      <div class="zeile pos">${["x", "y", "w", "h"].map((k) => `<label>${{ x: "←", y: "↓", w: "↔", h: "↕" }[k]}<input type="number" name="p_${k}" value="${e[k]}" aria-label="${k}"></label>`).join("")}</div>
      <details ${b.entity || b.quelle ? "open" : ""}><summary>${esc(L.bedingung)}</summary>
        <div class="zeile"><label>${esc(L.bedQuelle)}</label><select name="b_quelle"><option value="">${esc(L.bedHA)}</option>
          ${(E.quellen || []).map((q) => `<option value="${esc(q.id)}" ${q.id === b.quelle ? "selected" : ""}>${esc(q.name)} (${esc(q.id)})</option>`).join("")}</select></div>
        <div class="zeile" data-bed="ha" ${b.quelle ? "hidden" : ""}><input type="text" name="b_entity" list="ents" value="${esc(b.entity || "")}" placeholder="${esc(L.bedingungEntity)}"></div>
        <div class="zeile" data-bed="api" ${b.quelle ? "" : "hidden"}><input type="text" name="b_pfad" value="${esc(b.pfad || "")}" placeholder="${esc(L.bedPfad)}" spellcheck="false">
          <button class="knopf" type="button" name="bPfadWahl">${esc(L.waehlen)}</button></div><div class="bPfadBaum"></div>
        <div class="zeile"><select name="b_op">${Object.keys(L.op).map((k) => `<option value="${esc(k)}" ${k === (b.op || "=") ? "selected" : ""}>${esc(L.op[k])}</option>`).join("")}</select>
          <input type="text" name="b_wert" value="${esc(b.wert || "")}" style="width:140px"></div></details>
      <div class="zeile"><button class="knopf" name="vorne">${esc(L.vorne)}</button><button class="knopf" name="hinten">${esc(L.hinten)}</button>
        <button class="knopf gefahr" name="weg">${esc(L.entfernen)}</button></div>`;
    const aendern = () => {
      merken();
      for (const k of Object.keys(o)) {
        if (k === "liste" || k === "bild") continue;
        const inp = ziel.querySelector(`[name=o_${k}]`); if (!inp) continue;
        o[k] = inp.type === "checkbox" ? inp.checked : inp.type === "number" ? Number(inp.value) : inp.value;
        if (k === "pfad") o[k] = o[k].trim();
      }
      if (o.liste) o.liste = [...ziel.querySelectorAll("#raumListe .zeile")].map((z) => ({ name: z.querySelector("[name=rn]").value, entity: z.querySelector("[name=re]").value }));
      e.sichtbar = ziel.querySelector("[name=sichtbar]").checked;
      e.karte = ziel.querySelector("[name=karte]").checked;
      e.ausrichtung = ziel.querySelector("[name=ausrichtung]").value;
      e.schrift = ziel.querySelector("[name=schrift]").value;
      e.gewicht = ziel.querySelector("[name=gewicht]").value;
      e.textfarbe = ziel.querySelector("[name=textfarbeStd]").checked ? "" : ziel.querySelector("[name=textfarbe]").value;
      for (const k of ["x", "y", "w", "h"]) e[k] = Number(ziel.querySelector(`[name=p_${k}]`).value) || 0;
      e.w = klemm(e.w, 1, 48); e.h = klemm(e.h, 1, 27); e.x = klemm(e.x, 0, 48 - e.w); e.y = klemm(e.y, 0, 27 - e.h);
      const be = ziel.querySelector("[name=b_entity]").value.trim(), bq = ziel.querySelector("[name=b_quelle]").value;
      const bop = ziel.querySelector("[name=b_op]").value, bw = ziel.querySelector("[name=b_wert]").value;
      e.bedingung = bq ? { quelle: bq, pfad: ziel.querySelector("[name=b_pfad]").value.trim(), op: bop, wert: bw }
        : be ? { entity: be, op: bop, wert: bw } : null;
      ziel.querySelector("[data-bed=ha]").hidden = !!bq; ziel.querySelector("[data-bed=api]").hidden = !bq;
      $("#lSpeichern").textContent = L.speichern + " *";
      if (handy()) listeZeichnen(); else leinwandZeichnen();
      const ic = ziel.querySelector(".icon"); if (ic) ic.className = "icon mdi " + (o.icon || "");
    };
    ziel.querySelectorAll("input, select").forEach((i) => { i.onchange = aendern; });
    ziel.querySelectorAll(".neuner button").forEach((k) => {
      k.onclick = () => { ziel.querySelector("[name=ausrichtung]").value = k.dataset.pos;
        ziel.querySelectorAll(".neuner button").forEach((x) => x.classList.toggle("an", x === k)); aendern(); };
    });
    const bd = ziel.querySelector("[name=o_bildDatei]");
    if (bd) bd.onchange = () => aktion(null, async () => {
      const f = bd.files[0]; if (!f) return;
      const b64 = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(r.result); r.readAsDataURL(f); });
      const d = await senden("/api/bilder", { daten: b64 });
      merken(); o.bild = d.bild; $("#lSpeichern").textContent = L.speichern + " *"; eigenschaftenZeichnen();
      if (handy()) listeZeichnen(); else leinwandZeichnen();
    });
    // Pfad aus der letzten Antwort der Datenquelle wählen (Baum)
    const up = ziel.querySelector("[name=urlPruefen]");
    if (up) up.onclick = (ev) => aktion(ev.target, async () => {
      const r = await senden("/api/webseite/pruefen", { url: ziel.querySelector("[name=o_url]").value });
      ziel.querySelector("#urlErg").innerHTML = r.einbettbar === true ? `<span class="gut">${esc(L.einbettbarJa)}</span>`
        : r.einbettbar === false ? `<span class="schlecht">${esc(L.einbettbarNein)}: ${esc(r.grund)}</span>` : `${esc(L.einbettbarUnklar)}: ${esc(r.grund)}`;
    }, null);
    const pw = ziel.querySelector("[name=pfadWahl]");
    if (pw) pw.onclick = (ev) => aktion(ev.target, () => pfadWaehlen(ziel.querySelector(".pfadBaum"), ziel.querySelector("[name=o_quelle]").value,
      (p) => { ziel.querySelector("[name=o_pfad]").value = p; aendern(); }), null);
    ziel.querySelector("[name=bPfadWahl]").onclick = (ev) => aktion(ev.target, () => pfadWaehlen(ziel.querySelector(".bPfadBaum"), ziel.querySelector("[name=b_quelle]").value,
      (p) => { ziel.querySelector("[name=b_pfad]").value = p; aendern(); }), null);
    const tf = ziel.querySelector("[name=textfarbe]");
    if (tf) tf.oninput = () => { ziel.querySelector("[name=textfarbeStd]").checked = false; };
    const rp = ziel.querySelector("#raumPlus");
    if (rp) rp.onclick = () => { aendern(); o.liste.push({ name: "", entity: "" }); eigenschaftenZeichnen(); };
    ziel.querySelectorAll("[name=rw]").forEach((k) => { k.onclick = () => { k.closest(".zeile").remove(); aendern(); }; });
    const els = lay().elemente, i = els.indexOf(e);
    ziel.querySelector("[name=vorne]").onclick = () => { merken(); els.splice(i, 1); els.push(e); zeichnen(); };
    ziel.querySelector("[name=hinten]").onclick = () => { merken(); els.splice(i, 1); els.unshift(e); zeichnen(); };
    ziel.querySelector("[name=weg]").onclick = () => { merken(); els.splice(i, 1); GEWAEHLT = null; zeichnen(); };
  };

  if (ANSICHT === "editor" && LS[LI]) zeichnen(); else { ANSICHT = "liste"; listeAlle(); }
}

async function stilBilderZeigen(stil) {
  const ziel = document.getElementById("stilBilder");
  if (!ziel) return;
  const stile = stil === "gemischt" ? ["natur", "stadt", "himmel", "berge", "meer"] : [stil];
  ziel.innerHTML = "";
  for (const s of stile) for (const z of ["morgen", "tag", "abend", "nacht"]) {
    const img = document.createElement("img");
    img.alt = `${s} ${z}`; img.title = `${s} · ${z}`;
    ziel.appendChild(img);
    dienstBinaer.get(`/bilder/stile/klein/${s}-${z}.jpg`, {}, {}).then((d) => { img.src = URL.createObjectURL(new Blob([d], { type: "image/jpeg" })); }).catch(() => {});
  }
}

function neueId() { return Math.random().toString(36).slice(2, 10).replace(/[^a-z0-9]/g, "a").padEnd(8, "x"); }
function klemm(w, lo, hi) { return Math.max(lo, Math.min(hi, w)); }

function vorschauText(e, L) {
  const d = VORSCHAU, o = e.optionen;
  const w = (ent, f) => (d && d.werte && d.werte[ent] ? (f ? d.werte[ent][f] : d.werte[ent].state) : null);
  switch (e.typ) {
    case "uhr": return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    case "datum": return new Date().toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" });
    case "temperatur": return d && d.wetter.temperatur != null ? d.wetter.temperatur + " °C" : L.typ.temperatur;
    case "kachel": return `${o.name || o.entity || L.typ.kachel}${o.entity && w(o.entity) != null ? ": " + w(o.entity) + " " + (w(o.entity, "einheit") || "") : ""}`;
    case "raeume": return (o.liste || []).map((r) => r.name).join(", ") || L.typ.raeume;
    case "text": return (o.laufband ? "⟵ " : "") + (o.text || L.typ.text);
    case "logo": return "🖼 " + (o.bild ? "Logo" : L.typ.logo);
    case "kamera": return "📷 " + (o.entity || L.typ.kamera);
    case "kalender": return "📅 " + (o.titel || o.entity || o.quelle || L.typ.kalender);
    case "meldung": return "💬 " + (o.entity || L.typ.meldung);
    case "video": return "▶ " + L.typ.video;
    case "apiwert": return `${o.name ? o.name + ": " : ""}${o.vorlage || (o.pfad ? "{" + o.pfad + "}" : L.typ.apiwert)}${o.einheit ? " " + o.einheit : ""}`;
    case "apiliste": return "☰ " + (o.titel || o.quelle || L.typ.apiliste);
    case "apibild": return "🖼 " + (o.quelle || L.typ.apibild);
    case "anzeige": return (o.darstellung === "ampel" ? "● " : "▬ ") + (o.name || o.pfad || L.typ.anzeige);
    case "countdown": return "⏳ " + (o.vorlage || L.typ.countdown);
    case "qrcode": return "▦ " + (o.beschriftung || L.typ.qrcode);
    case "webcam": return "🎥 " + (o.quelle || L.typ.webcam);
    case "unwetter": return "⚠ " + L.typ.unwetter;
    case "diagramm": return "📈 " + (o.name || o.entity || o.pfad || L.typ.diagramm);
    case "webseite": return "🌐 " + (o.url.replace(/^https?:\/\//, "").slice(0, 30) || L.typ.webseite);
    default: return L.typ[e.typ] || e.typ;
  }
}
