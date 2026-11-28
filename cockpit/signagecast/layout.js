// SignageCast – Layout-Editor (Reiter „Layout“). Wird vor tv.js geladen und nutzt dessen Hilfsfunktionen zur Laufzeit.
// PC/Tablet: Bausteine auf einer verkleinerten Fläche ziehen (verschieben) und an der Ecke größer/kleiner ziehen,
// alles rastet im Raster 48 x 27 ein. Handy: Liste mit Ein/Aus, Größe −/+ und Einstellungen.
"use strict";

const LTEXTE = {
  de: {
    alleLayouts: "Alle Layouts", ausgangspunkt: "Ausgangspunkt", leeresLayout: "leer", vorlagenGruppe: "Vorlagen", kopieVon: "Kopie von",
    erstellen: "Erstellen", abbrechen: "Abbrechen", designer: "Designer", vwDirekt: "Kanal", vwZeitplan: "Zeitplan", vwKarussell: "Karussell", bausteine: "Bausteine", nichtGespeichert: "nicht gespeichert", bearbeitenL: "Bearbeiten", mehr: "Mehr", nichtVerwendet: "nicht verwendet",
    laeuftAuf: (n) => `läuft auf: ${n}`, laeuftHinweis: "Änderungen sind nach dem Speichern sofort auf dem Fernseher zu sehen.",
    nameFehlt: "Bitte einen Namen eingeben.", verwerfen: "Ungespeicherte Änderungen verwerfen?", hgFarben: "Hintergrund & Farben",
    layout: "Layout", neu: "Neues Layout", ausVorlage: "aus Vorlage", duplizieren: "Kopieren", loeschen: "Löschen",
    exportieren: "Exportieren", importieren: "Importieren", rueckgaengig: "Rückgängig", speichern: "Speichern",
    name: "Name", hintergrund: "Hintergrund", hgArt: { wetter: "Wetterbild (nach Wetter)", stil: "Bilderset (nach Tageszeit)", bild: "eigene Bilder", galerie: "Galerie-Ordner (Diashow)", farbe: "Farbe" },
    stil: "Stil", stilArt: { natur: "Natur", stadt: "Stadt", himmel: "Himmel", berge: "Berge", meer: "Meer", essen: "Essen (Imbiss, Restaurant)", sport: "Sport (Fitness)", architektur: "Architektur (hell, ruhig)", gemischt: "gemischt (Landschaften, jeden Tag eine andere)" },
    wechsel: "Wechsel", wechselArt: { tageszeit: "nach Tageszeit", tageszeit_wetter: "nach Tageszeit, bei Regen/Schnee/Nebel Wetterbild", diashow: "Diashow" },
    diashowMin: "Diashow: Sekunden je Bild", bewegen: "Bilder langsam bewegen (sanfter Zoom)", nachtsDunkler: "abends/nachts dunkler", jeZeit: "Eigenes Bild je Tageszeit (leer = Hauptbild)",
    zeitName: { morgen: "Sonnenaufgang", tag: "Tag", abend: "Sonnenuntergang", nacht: "Nacht" },
    bereich: "Bildbereich (Felder ← ↓ ↔ ↕; ganze Fläche = 0 0 48 27)", anpassung: "Füllart", anpassungArt: { fuellen: "füllen (zuschneiden)", einpassen: "einpassen (ganz sichtbar)", strecken: "strecken" },
    ausschnitt: "Ausschnitt", ausschnittArt: { mitte: "Mitte", oben: "oben", unten: "unten", links: "links", rechts: "rechts" }, ganzeFlaeche: "ganze Fläche", hauptbild: "Hauptbild", entfernenKurz: "✕",
    tzHinweis: "Tageszeit nach dem Sonnenstand am Standort (Reiter Verbindung): Sonnenaufgang und -untergang je etwa eine Stunde um den Zeitpunkt, dazwischen Tag bzw. Nacht.",
    abdunkeln: "links abdunkeln", bildHochladen: "Bild hochladen (JPG/PNG)", schema: "Farbschema",
    schemaArt: { dunkel: "hell auf dunkel", hell: "dunkel auf hell", gedimmt: "gedimmt (Nacht)" }, akzent: "Akzentfarbe",
    karten: "Karten", kartenArt: { weiss: "weiß", glas_hell: "durchscheinend hell", glas_dunkel: "durchscheinend dunkel" },
    schrift: "Schrift", bausteinNeu: "Baustein hinzufügen", hinzu: "Hinzufügen", keinerGewaehlt: "Baustein antippen, um ihn einzustellen.",
    ansicht: "Ansicht", ansichtArt: { vorschau: "Live-Vorschau", skizze: "Skizze" }, tzVorschau: "Tageszeit der Vorschau",
    rand: "Sicherer Rand", randHilfe: "Zeigt den Rand, den manche Fernseher abschneiden (Overscan). Wichtiges besser innerhalb lassen.",
    tzAuto: "Tageszeit: jetzt", vorschauHinweis: "Live-Vorschau: So sieht es am Fernseher aus – auch ungespeichert. Live-Videos erscheinen als Platzhalter.",
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
    benutzt: "wird benutzt von", nichtLoeschbar: "Das Layout wird noch von einem Kanal benutzt (auch im Zeitplan).",
    letztes: "Das letzte Layout kann nicht gelöscht werden.", importOk: "Layout importiert – Speichern nicht vergessen",
    versionen: "Versionen", versionenText: "Vor jeder Änderung hebt SignageCast die alte Fassung auf (je Layout die letzten 10). Wiederherstellen ersetzt das Layout – die jetzige Fassung wird dabei selbst zur Version.",
    keineVersionen: "Noch keine älteren Fassungen.", wiederherstellen: "Wiederherstellen", herunterladen: "Herunterladen", schliessen: "Schließen",
    bausteineN: (n) => n === 1 ? "1 Baustein" : `${n} Bausteine`, wiederhergestellt: "Fassung wiederhergestellt",
    wirklichWiederherstellen: "Diese Fassung wiederherstellen? Die jetzige wird als Version aufgehoben.",
    geloeschte: (n) => `Gelöschte Layouts (${n})`, geloeschtAm: "gelöscht",
    einfuegen: "Text einfügen …", einfuegenText: "JSON eines Layouts hier einfügen – z. B. die Antwort einer KI. Text davor oder danach und ```-Zäune stören nicht.",
    uebernehmen: "Übernehmen", kiHilfe: "Mit KI erstellen …",
    kiText: "So lässt du ein Layout von einer KI (z. B. ChatGPT, Claude, Gemini) bauen: Anleitung kopieren, in die KI einfügen, deinen Wunsch an der markierten Stelle beschreiben, die Antwort (JSON) hier mit „Text einfügen …“ übernehmen. Danach im Editor Bilder hochladen und Entitäten wählen.",
    kiKopieren: "Anleitung kopieren", kiKopiert: "Anleitung kopiert", kiDatei: "Als Datei laden",
    kiWunsch: "MEIN WUNSCH: (hier beschreiben, z. B. „Wartezimmer einer Zahnarztpraxis, hell und ruhig, Logo oben links, große Uhr, Video rechts, unten ein Laufband mit Öffnungszeiten“)",
    kiEinleitung: "Du gestaltest Bildschirm-Layouts für SignageCast. Erstelle genau ein Layout im unten beschriebenen JSON-Format. Texte auf dem Bildschirm auf Deutsch. Antworte nur mit dem JSON-Objekt.",
    hinweiseTitel: "Beim Import angepasst:", importGespeichert: "Layout übernommen und gespeichert",
    ungespeichert: "Es gibt ungespeicherte Änderungen. Trotzdem wechseln?",
    typ: { uhr: "Uhr", datum: "Datum", temperatur: "Temperatur", wetterlage: "Wetterlage", feuchte: "Luftfeuchte", wind: "Wind",
           vorhersage: "Vorhersage", raeume: "Räume", kachel: "Kachel (HA-Wert)", video: "Live-Video", sender: "Radio-Sender",
           text: "Freier Text", logo: "Logo / Bild", kamera: "Kamera (HA)", kalender: "Kalender / Müllabfuhr", meldung: "Meldung von HA", flaeche: "Fläche (Farbe)",
           apiwert: "API-Wert", apiliste: "API-Liste / Feed", apibild: "API-Bild", anzeige: "Anzeige (Balken/Ampel)", countdown: "Countdown", qrcode: "QR-Code",
           webcam: "Kamera (Video)", diagramm: "Verlauf / Diagramm", webseite: "Webseite", unwetter: "Unwetterwarnung (DWD)",
           pdf: "PDF (Seite für Seite)", galerie: "Galerie (Bilder/PDFs)", liste: "Liste (Speisekarte, Zeiten, Wegweiser)" },
    opt: { sekunden: "mit Sekunden", wochentag: "mit Wochentag", jahr: "mit Jahr", entity: "Entität (aus HA)", tage: "Tage",
           liste: "Räume", name: "Beschriftung", icon: "Symbol (mdi-…)", leiste: "LIVE-Leiste zeigen", herkunft: "Was zeigen", text: "Text",
           bild: "Bild hochladen (PNG mit durchsichtigem Hintergrund oder JPG)", laufband: "als Laufband (läuft durch)", nur_mit_terminen: "nur zeigen, wenn in diesem Zeitraum Termine anstehen",
           ansicht: "Darstellung", symbole: "Symbole je Termin (erste passende Regel gilt)", ohne_symbol: "Symbol für andere Termine (leer = weglassen)", wann: "Tag unter dem Symbol (Heute, Morgen, Di …)",
           intervall: "Bild erneuern alle (s)", anzahl: "Einträge", titel: "Überschrift", dauer: "anzeigen für (s)", farbe: "Farbe", deckkraft: "Deckkraft (%)",
           quelle: "Datenquelle", pfad: "Pfad in der Antwort", vorlage: "Vorlage (leer = nur der Wert)", einheit: "Einheit", nachkomma: "Nachkommastellen (-1 = wie geliefert)",
           faktor: "Faktor (z. B. 0,01 für cm → m)", zeile: "Zeile (Platzhalter je Eintrag)", anpassung: "Bild", darstellung: "Darstellung", min: "Minimum", max: "Maximum",
           gelb: "gelb ab", rot: "rot ab", umkehren: "umgekehrt (niedrige Werte schlecht)", ziel: "Ziel (Datum/Uhrzeit)", ende: "Text nach Ablauf",
           inhalt: "Inhalt (Text, Link oder WLAN-Daten)", beschriftung: "Beschriftung",
           immer: "auch ohne Warnung zeigen", ton: "mit Ton", stunden: "Zeitraum (Stunden)", url: "Adresse", neu_laden_min: "neu laden alle (min, 0 = nie; Foto: stündlich)", modus: "Darstellung", zoom: "Zoom (%)",
           versatz_x: "Ausschnitt: von links (px)", versatz_y: "Ausschnitt: von oben (px)",
           datei: "PDF hochladen", sekunden: "Sekunden je Seite",
           ordner: "Ordner", rand: "Rand (bei „einpassen“)", reihenfolge: "Reihenfolge", uebergang: "Wechsel",
           zeilen: "Zeilen", spalten: "Spalten", punkte: "Punktlinie zum Wert", spalte_text: "Text (Platzhalter je Zeile)", spalte_info: "Zusatz (Platzhalter)", spalte_wert: "Wert rechts (Platzhalter)" },
    optHilfe: { temperatur: "leer = Wetter aus Einstellungen → Allgemein; oder ein Temperatur-Sensor", kamera: "z. B. Türklingel – mit Bedingung nur bei Klingeln zeigen",
                meldung: "Text-Entität in HA (z. B. input_text.tv_meldung). Ändert sich der Text, erscheint er als Banner.",
                kalender: "Kalender-Entität, z. B. Müllabfuhr (Waste Collection Schedule) oder Familienkalender – oder eine Datenquelle (iCal oder CSV mit Datumsspalte, dann ohne HA)",
                apiwert: "Wert aus einer Datenquelle (Reiter „Datenquellen“). Vorlage mit Platzhaltern, z. B. „{value} cm“ oder „{a.b} · {c}“; {quelle:pfad} holt Werte aus anderen Quellen.",
                apiliste: "Liste aus einer Datenquelle, z. B. RSS (Pfad „eintraege“, Zeile „{titel}“) oder eine JSON-Liste. In der Zeile beziehen sich Platzhalter auf den Eintrag, {.} = der Eintrag selbst.",
                apibild: "Bild-Quelle oder eine JSON-Quelle mit Pfad zu einer Bild-Adresse.",
                anzeige: "Zahl aus einer Datenquelle als Balken (Minimum–Maximum) oder Ampel (grün, gelb ab, rot ab).",
                countdown: "Ziel fest eintragen oder aus einer Datenquelle. Platzhalter: {tage}, {stunden}, {minuten}, {sekunden}.",
                qrcode: "Wird auf dem Fernseher erzeugt. WLAN: WIFI:T:WPA;S:Name;P:Passwort;; – Platzhalter {quelle:pfad} möglich.",
                text: "Platzhalter wie {quelle:pfad} werden durch Werte aus Datenquellen ersetzt.",
                webcam: "Kamera aus „Datenquellen“ (Art Kamera). Läuft nur, solange der Baustein sichtbar ist – z. B. mit Bedingung nur beim Klingeln.",
                diagramm: "Entweder eine HA-Entität (Verlauf aus der HA-Historie) oder Datenquelle + Pfad – deren Werte merkt sich SignageCast ab jetzt (bis 7 Tage).",
                webseite: "„Einbetten“ zeigt die Seite live, geht aber nur, wenn sie es erlaubt („Prüfen“). „Bildschirmfoto“ geht mit fast jeder öffentlichen Seite: SignageCast lädt sie selbst und zeigt alle paar Minuten ein Foto (ohne Bewegung und Anmeldung, Cookie-Hinweise bleiben sichtbar). Zoom und Ausschnitt wählen den sichtbaren Teil.",
                unwetter: "Amtliche Warnungen des Deutschen Wetterdienstes für den Standort (nur Deutschland). Ohne Warnung unsichtbar – oder „auch ohne Warnung zeigen“.",
                pdf: "Preisliste, Speisekarte, Aushang oder Präsentation (als PDF speichern). Bis 50 Seiten; die Seiten wechseln nach der Uhr – alle Fernseher blättern gleich.",
                galerie: "Zeigt einen Ordner aus Medien → Galerien: Bilder und PDF-Seiten nacheinander, nach der Uhr – alle Fernseher zeigen dasselbe Bild. Neue Bilder im Ordner erscheinen von selbst. Für Vollbild den Baustein auf 0 0 48 27 ziehen.",
                liste: "Zeilen mit Text links, kleinem Zusatz darunter (z. B. Allergene) und Wert rechts (Preis, Uhrzeit, Ebene). Hervorgehobene Zeilen in der Akzentfarbe. Statt fester Zeilen geht auch eine Datenquelle, z. B. eine CSV-Datei mit den Spalten text, info, wert – dann pflegt man nur die Datei." },
    wahl: { kanal: "wie im Kanal eingestellt", medien: "nur eigene Medien (ohne YouTube)", liste: "Liste", symbole: "nur Symbole", balken: "Balken", ampel: "Ampel", einpassen: "einpassen (ganzes Bild)", fuellen: "füllen (zuschneiden)", einbetten: "einbetten (live)", bild: "Bildschirmfoto",
            schwarz: "schwarz", unscharf: "Bild unscharf dahinter", eigene: "wie im Ordner", name: "nach Name", neu: "neueste zuerst", zufall: "zufällig",
            blenden: "überblenden", hart: "direkt" },
    galSekunden: "Sekunden je Bild", galKeinOrdner: "– Ordner wählen –", galOrdnerAnlegen: "Ordner anlegen und Bilder hochladen: Medien → Galerien",
    galHg: "Ordner", galHgSek: "Sekunden je Bild",
    keineQuelle: "– Datenquelle wählen –", waehlen: "wählen …", bedQuelle: "Wert aus", bedHA: "Home Assistant", bedPfad: "Pfad",
    pruefen: "Prüfen", einbettbarJa: "Seite erlaubt das Einbetten", einbettbarNein: "Seite verbietet das Einbetten", einbettbarUnklar: "nicht prüfbar", tippFoto: "– Tipp: Darstellung „Bildschirmfoto“ wählen.",
    zeitraum: "Nur im Zeitraum …", zeitraumText: "Zum Beispiel „Praxis vom 23.12. bis 2.1. geschlossen“: erscheint und verschwindet von selbst. Ohne Uhrzeit gilt der ganze Tag.",
    ab: "ab", bis: "bis", zeitraumAus: "außerhalb des Zeitraums", seiten: (n) => `${n} Seiten`, laedt: "Lade hoch und wandle um …",
    raumNeu: "Raum hinzufügen", zl: { text: "Text", info: "Zusatz", wert: "Wert", hervor: "hervorheben", neu: "Zeile hinzufügen", hoch: "nach oben", quelleStatt: "Die Zeilen kommen aus der Datenquelle – feste Zeilen werden dann nicht gezeigt." }, op: { "=": "ist gleich", "!=": "ist nicht", ">": "größer als", "<": "kleiner als", an: "ist an/offen", aus: "ist aus/zu" },
  },
  en: {
    alleLayouts: "All layouts", ausgangspunkt: "Start from", leeresLayout: "empty", vorlagenGruppe: "Templates", kopieVon: "Copy of",
    erstellen: "Create", abbrechen: "Cancel", designer: "Designer", vwDirekt: "Channel", vwZeitplan: "Schedule", vwKarussell: "Carousel", bausteine: "Elements", nichtGespeichert: "not saved", bearbeitenL: "Edit", mehr: "More", nichtVerwendet: "not used",
    laeuftAuf: (n) => `shown on: ${n}`, laeuftHinweis: "Changes are visible on the TV right after saving.",
    nameFehlt: "Please enter a name.", verwerfen: "Discard unsaved changes?", hgFarben: "Background & colours",
    layout: "Layout", neu: "New layout", ausVorlage: "from template", duplizieren: "Copy", loeschen: "Delete",
    exportieren: "Export", importieren: "Import", rueckgaengig: "Undo", speichern: "Save",
    name: "Name", hintergrund: "Background", hgArt: { wetter: "Weather picture (by weather)", stil: "Picture set (by time of day)", bild: "own pictures", galerie: "Gallery folder (slideshow)", farbe: "Colour" },
    stil: "Style", stilArt: { natur: "Nature", stadt: "City", himmel: "Sky", berge: "Mountains", meer: "Sea", essen: "Food (snack bar, restaurant)", sport: "Sport (gym)", architektur: "Architecture (bright, calm)", gemischt: "mixed (landscapes, different every day)" },
    wechsel: "Change", wechselArt: { tageszeit: "by time of day", tageszeit_wetter: "by time of day, weather picture when rain/snow/fog", diashow: "Slideshow" },
    diashowMin: "Slideshow: seconds per picture", bewegen: "Move pictures slowly (gentle zoom)", nachtsDunkler: "darker in the evening/at night", jeZeit: "Own picture per time of day (empty = main picture)",
    zeitName: { morgen: "Sunrise", tag: "Day", abend: "Sunset", nacht: "Night" },
    bereich: "Picture area (cells ← ↓ ↔ ↕; whole screen = 0 0 48 27)", anpassung: "Fit", anpassungArt: { fuellen: "fill (crop)", einpassen: "fit (whole picture)", strecken: "stretch" },
    ausschnitt: "Crop position", ausschnittArt: { mitte: "centre", oben: "top", unten: "bottom", links: "left", rechts: "right" }, ganzeFlaeche: "whole screen", hauptbild: "Main picture", entfernenKurz: "✕",
    tzHinweis: "Time of day from the sun position at your location (Connection tab): sunrise and sunset about one hour around the moment, otherwise day or night.",
    abdunkeln: "darken left side", bildHochladen: "Upload picture (JPG/PNG)", schema: "Colour scheme",
    schemaArt: { dunkel: "light on dark", hell: "dark on light", gedimmt: "dimmed (night)" }, akzent: "Accent colour",
    karten: "Cards", kartenArt: { weiss: "white", glas_hell: "see-through light", glas_dunkel: "see-through dark" },
    schrift: "Font", bausteinNeu: "Add element", hinzu: "Add", keinerGewaehlt: "Tap an element to configure it.",
    ansicht: "View", ansichtArt: { vorschau: "Live preview", skizze: "Sketch" }, tzVorschau: "Time of day in the preview",
    rand: "Safe area", randHilfe: "Shows the edge some TVs cut off (overscan). Better keep important things inside.",
    tzAuto: "Time of day: now", vorschauHinweis: "Live preview: this is how it looks on the TV – even unsaved. Live videos show as placeholders.",
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
    benutzt: "used by", nichtLoeschbar: "This layout is still used by a channel (also in a schedule).",
    letztes: "The last layout cannot be deleted.", importOk: "Layout imported – don't forget to save",
    versionen: "Versions", versionenText: "Before every change SignageCast keeps the old version (the last 10 per layout). Restoring replaces the layout – the current one becomes a version itself.",
    keineVersionen: "No older versions yet.", wiederherstellen: "Restore", herunterladen: "Download", schliessen: "Close",
    bausteineN: (n) => n === 1 ? "1 element" : `${n} elements`, wiederhergestellt: "Version restored",
    wirklichWiederherstellen: "Restore this version? The current one is kept as a version.",
    geloeschte: (n) => `Deleted layouts (${n})`, geloeschtAm: "deleted",
    einfuegen: "Paste text …", einfuegenText: "Paste the JSON of a layout here – e.g. the answer of an AI. Text before or after it and ``` fences do no harm.",
    uebernehmen: "Apply", kiHilfe: "Create with AI …",
    kiText: "To have an AI (e.g. ChatGPT, Claude, Gemini) build a layout: copy the instructions, paste them into the AI, describe your wish at the marked place, and apply the answer (JSON) here with “Paste text …”. Then upload pictures and choose entities in the editor.",
    kiKopieren: "Copy instructions", kiKopiert: "Instructions copied", kiDatei: "Download as file",
    kiWunsch: "MY WISH: (describe it here, e.g. “waiting room of a dental practice, light and calm, logo top left, large clock, video on the right, a ticker with opening hours at the bottom”)",
    kiEinleitung: "You design screen layouts for SignageCast. Create exactly one layout in the JSON format described below. Screen texts in English. Answer with the JSON object only.",
    hinweiseTitel: "Adjusted on import:", importGespeichert: "Layout applied and saved",
    ungespeichert: "There are unsaved changes. Switch anyway?",
    typ: { uhr: "Clock", datum: "Date", temperatur: "Temperature", wetterlage: "Weather", feuchte: "Humidity", wind: "Wind",
           vorhersage: "Forecast", raeume: "Rooms", kachel: "Tile (HA value)", video: "Live video", sender: "Radio station",
           text: "Free text", logo: "Logo / picture", kamera: "Camera (HA)", kalender: "Calendar / waste collection", meldung: "Message from HA", flaeche: "Area (colour)",
           apiwert: "API value", apiliste: "API list / feed", apibild: "API picture", anzeige: "Gauge (bar/traffic light)", countdown: "Countdown", qrcode: "QR code",
           webcam: "Camera (video)", diagramm: "History / chart", webseite: "Web page", unwetter: "Weather warning (DWD)",
           pdf: "PDF (page by page)", galerie: "Gallery (pictures/PDFs)", liste: "List (menu, times, directory)" },
    opt: { sekunden: "with seconds", wochentag: "with weekday", jahr: "with year", entity: "Entity (from HA)", tage: "Days",
           liste: "Rooms", name: "Label", icon: "Icon (mdi-…)", leiste: "show LIVE bar", herkunft: "What to show", text: "Text",
           bild: "Upload picture (PNG with transparent background or JPG)", laufband: "as ticker (scrolling)", nur_mit_terminen: "only show when events are due in this period",
           ansicht: "Display", symbole: "Icon per event (first matching rule wins)", ohne_symbol: "Icon for other events (empty = leave out)", wann: "day below the icon (Today, Tomorrow, Tue …)",
           intervall: "refresh picture every (s)", anzahl: "Entries", titel: "Heading", dauer: "show for (s)", farbe: "Colour", deckkraft: "Opacity (%)",
           quelle: "Data source", pfad: "Path in the response", vorlage: "Template (empty = value only)", einheit: "Unit", nachkomma: "Decimals (-1 = as delivered)",
           faktor: "Factor (e.g. 0.01 for cm → m)", zeile: "Row (placeholders per entry)", anpassung: "Picture", darstellung: "Display", min: "Minimum", max: "Maximum",
           gelb: "yellow from", rot: "red from", umkehren: "reversed (low values are bad)", ziel: "Target (date/time)", ende: "Text when reached",
           inhalt: "Content (text, link or Wi-Fi data)", beschriftung: "Caption",
           immer: "show also without warning", ton: "with sound", stunden: "Period (hours)", url: "Address", neu_laden_min: "reload every (min, 0 = never; picture: hourly)", modus: "Display", zoom: "Zoom (%)",
           versatz_x: "Crop: from left (px)", versatz_y: "Crop: from top (px)",
           datei: "Upload PDF", sekunden: "Seconds per page",
           ordner: "Folder", rand: "Border (with “fit”)", reihenfolge: "Order", uebergang: "Change",
           zeilen: "Rows", spalten: "Columns", punkte: "Dotted line to the value", spalte_text: "Text (placeholder per row)", spalte_info: "Extra line (placeholder)", spalte_wert: "Value right (placeholder)" },
    optHilfe: { temperatur: "empty = weather from Settings → General; or a temperature sensor", kamera: "e.g. doorbell – with a condition only when it rings",
                meldung: "Text entity in HA (e.g. input_text.tv_message). When the text changes it appears as a banner.",
                kalender: "Calendar entity, e.g. waste collection or family calendar – or a data source (iCal or CSV with a date column, then without HA)",
                apiwert: "Value from a data source (tab “Data sources”). Template with placeholders, e.g. “{value} cm” or “{a.b} · {c}”; {source:path} takes values from other sources.",
                apiliste: "List from a data source, e.g. RSS (path “eintraege”, row “{titel}”) or a JSON list. In the row placeholders refer to the entry, {.} = the entry itself.",
                apibild: "Picture source, or a JSON source with a path to a picture address.",
                anzeige: "Number from a data source as a bar (minimum–maximum) or traffic light (green, yellow from, red from).",
                countdown: "Enter the target or take it from a data source. Placeholders: {tage} (days), {stunden} (hours), {minuten}, {sekunden}.",
                qrcode: "Generated on the TV. Wi-Fi: WIFI:T:WPA;S:name;P:password;; – placeholders {source:path} possible.",
                text: "Placeholders like {source:path} are replaced with values from data sources.",
                webcam: "Camera from “Data sources” (type camera). Only runs while the element is visible – e.g. with a condition only when the doorbell rings.",
                diagramm: "Either an HA entity (history from HA) or data source + path – SignageCast records its values from now on (up to 7 days).",
                webseite: "“Embed” shows the page live but only works if it allows embedding (“Check”). “Screenshot” works with almost any public page: SignageCast loads it itself and shows a fresh picture every few minutes (no motion, no login, cookie notices stay visible). Zoom and crop choose the visible part.",
                unwetter: "Official warnings of the German Weather Service for the location (Germany only). Hidden without a warning – or “show also without warning”.",
                pdf: "Price list, menu, notice or presentation (saved as PDF). Up to 50 pages; pages change by the clock – all TVs turn pages together.",
                galerie: "Shows a folder from Media → Galleries: pictures and PDF pages one after another, by the clock – all TVs show the same picture. New pictures in the folder appear by themselves. For full screen set the element to 0 0 48 27.",
                liste: "Rows with text on the left, a small extra line below (e.g. allergens) and a value on the right (price, time, floor). Highlighted rows use the accent colour. Instead of fixed rows a data source works too, e.g. a CSV file with the columns text, info, wert – then you only maintain the file." },
    wahl: { kanal: "as set for the channel", medien: "own media only (no YouTube)", liste: "List", symbole: "icons only", balken: "Bar", ampel: "Traffic light", einpassen: "fit (whole picture)", fuellen: "fill (crop)", einbetten: "embed (live)", bild: "Screenshot",
            schwarz: "black", unscharf: "blurred picture behind", eigene: "as in the folder", name: "by name", neu: "newest first", zufall: "random",
            blenden: "cross-fade", hart: "cut" },
    galSekunden: "Seconds per picture", galKeinOrdner: "– choose folder –", galOrdnerAnlegen: "Create folders and upload pictures: Media → Galleries",
    galHg: "Folder", galHgSek: "Seconds per picture",
    keineQuelle: "– choose data source –", waehlen: "pick …", bedQuelle: "Value from", bedHA: "Home Assistant", bedPfad: "Path",
    pruefen: "Check", einbettbarJa: "page allows embedding", einbettbarNein: "page forbids embedding", einbettbarUnklar: "could not check", tippFoto: "– tip: choose display “Screenshot”.",
    zeitraum: "Only during …", zeitraumText: "For example “Closed from 23 Dec to 2 Jan”: appears and disappears by itself. Without a time the whole day counts.",
    ab: "from", bis: "until", zeitraumAus: "outside the period", seiten: (n) => `${n} pages`, laedt: "Uploading and converting …",
    raumNeu: "Add room", zl: { text: "Text", info: "Extra", wert: "Value", hervor: "highlight", neu: "Add row", hoch: "move up", quelleStatt: "The rows come from the data source – fixed rows are not shown then." }, op: { "=": "equals", "!=": "is not", ">": "greater than", "<": "less than", an: "is on/open", aus: "is off/closed" },
  },
};
const STD_GROESSE = { logo: [8, 4], uhr: [8, 3], datum: [9, 1], temperatur: [8, 2], wetterlage: [9, 1], feuchte: [9, 1], wind: [9, 1],
  vorhersage: [8, 5], raeume: [9, 5], kachel: [5, 5], video: [24, 14], sender: [9, 1], text: [12, 2], kamera: [12, 7],
  kalender: [10, 5], meldung: [24, 3], flaeche: [12, 4], apiwert: [8, 3], apiliste: [14, 6], apibild: [10, 8], anzeige: [8, 3],
  countdown: [10, 2], qrcode: [5, 6], webcam: [16, 9], diagramm: [12, 6], webseite: [16, 12], unwetter: [20, 3],
  pdf: [16, 20], galerie: [24, 14], liste: [16, 12] };
// ---------- Bedienung (seit 0.58): Bausteine-Leiste, Mehrfachauswahl, Kurzbefehle, Wiederholen, Warnungen ----------
const LBED = {
  de: {
    baustein: "+ Baustein", leisteTitel: "Bausteine – anklicken oder auf die Leinwand ziehen",
    gruppen: { zeit: "Zeit & Wetter", text: "Text & Bild", medien: "Video & Medien", daten: "Daten", ha: "Home Assistant" },
    wiederholen: "Wiederholen", kurz: "Strg+Z / Strg+Y",
    mehr: (n) => `${n} Bausteine gewählt`, mehrText: "Zusammen verschieben (ziehen oder Pfeiltasten), ausrichten oder verteilen. Klick auf einen einzelnen Baustein zeigt seine Einstellungen.",
    ausrichten: "Ausrichten", verteilen: "Gleich verteilen",
    ri: { links: "links", hmitte: "Mitte (waagrecht)", rechts: "rechts", oben: "oben", vmitte: "Mitte (senkrecht)", unten: "unten" },
    vt: { x: "waagrecht", y: "senkrecht" }, duplizieren: "Duplizieren", entfernen: "Entfernen",
    tasten: "Umschalt+Klick oder Rahmen aufziehen: mehrere wählen · Strg+D duplizieren · Strg+C/V kopieren/einfügen · Entf entfernen · Strg+Z/Y rückgängig/wiederholen",
    w: { klein: (px) => `Schrift klein (${px} px) – aus 3 m schwer lesbar`, kontrast: (r) => `wenig Kontrast (${r}:1) zwischen Schrift und Hintergrund`,
         ueberlauf: "Inhalt passt nicht ganz hinein", verdeckt: "ganz verdeckt von einem anderen Baustein",
         videos: (n) => `${n} Live-Videos im Layout – jedes kostet Rechenzeit (Server bzw. Player)` },
    hinweise: (n) => (n === 1 ? "1 Hinweis" : `${n} Hinweise`),
    reiter: { inhalt: "Inhalt", aussehen: "Aussehen", wann: "Wann" }, wannAktiv: "Zeitraum oder Bedingung gesetzt",
    seite: { baustein: "Baustein", layout: "Layout" }, bausteinErst: "Erst einen Baustein auf der Leinwand anklicken",
    layoutText: "Gilt für das ganze Layout. Einen Baustein auf der Leinwand anklicken, um ihn einzustellen.",
    zoom: "Zoom", einpassen: "Einpassen", zoomHilfe: "Strg+Mausrad über der Leinwand zoomt", hilfe: "Hilfe",
    h: { herkunft: "YouTube erlaubt nur private, nicht-gewerbliche Nutzung. In Praxis, Laden, Hotel oder Verein „nur eigene Medien“ wählen – "
           + "die Medien lädst du unter Medien → Dateien hoch. Ohne Medien zeigt das Fenster ein ruhiges Bild.",
         sichtbar: "Ausgeschaltet bleibt der Baustein im Layout, der Fernseher zeigt ihn aber nicht.",
         karte: "Legt eine halbdurchsichtige Karte hinter den Inhalt – besser lesbar auf unruhigem Hintergrund.",
         ausrichtung: "Wo der Inhalt innerhalb des Bausteins sitzt.",
         schrift: "Eigene Schrift nur für diesen Baustein. „Wie Layout“ nimmt die Schrift aus dem Reiter Layout.",
         textfarbe: "Eigene Textfarbe. Mit Haken gilt die Farbe aus dem Farbschema des Layouts.",
         gewicht: "Strichstärke der Schrift.",
         position: "Lage und Größe in Rasterfeldern: 48 × 27 Felder sind der ganze Bildschirm, ein Feld sind 40 Bildpunkte.",
         bedingung: "Der Baustein erscheint nur, wenn der Wert passt – zum Beispiel ein Regenhinweis nur, wenn ein Sensor Regen meldet.",
         quelle: "Woher die Werte kommen. Neue Datenquellen legst du unter Datenquellen an.",
         pfad: "Welcher Wert aus der Antwort gezeigt wird. Mit „Wählen“ anklicken statt tippen.",
         entity: "Entität aus Home Assistant, zum Beispiel sensor.wohnzimmer_temperatur. Beim Tippen erscheinen Vorschläge.",
         vorlage: "Text mit {wert} als Platzhalter, zum Beispiel „Pegel: {wert}“.",
         faktor: "Der Wert wird damit malgenommen, zum Beispiel 0,01, um Zentimeter in Meter umzurechnen.",
         nachkomma: "Wie viele Stellen nach dem Komma. -1 zeigt den Wert so, wie die Quelle ihn liefert.",
         url: "Adresse der Webseite. „Prüfen“ zeigt, ob sich die Seite einbetten lässt.",
         neu_laden_min: "Wie oft die Seite neu geladen wird. 0 heißt nie.",
         intervall: "Wie oft das Kamerabild neu geholt wird. Kürzer heißt mehr Netzlast.",
         laufband: "Langer Text läuft von rechts nach links durch, statt abgeschnitten zu werden.",
         deckkraft: "0 % ist ganz durchsichtig, 100 % deckt ganz.",
         ziel: "Bis zu diesem Zeitpunkt zählt der Countdown herunter.", ende: "Erscheint, wenn der Countdown abgelaufen ist.",
         inhalt: "Was der QR-Code enthält: ein Link, ein Text oder die WLAN-Zugangsdaten.",
         stunden: "Wie weit die Kurve zurückreicht.", anzahl: "Wie viele Einträge höchstens gezeigt werden.",
         dauer: "Wie lange jedes Bild oder jede Seite zu sehen ist." },
  },
  en: {
    baustein: "+ Element", leisteTitel: "Elements – click or drag onto the canvas",
    gruppen: { zeit: "Time & weather", text: "Text & picture", medien: "Video & media", daten: "Data", ha: "Home Assistant" },
    wiederholen: "Redo", kurz: "Ctrl+Z / Ctrl+Y",
    mehr: (n) => `${n} elements selected`, mehrText: "Move them together (drag or arrow keys), align or distribute. Click a single element to see its settings.",
    ausrichten: "Align", verteilen: "Distribute evenly",
    ri: { links: "left", hmitte: "centre (horizontal)", rechts: "right", oben: "top", vmitte: "middle (vertical)", unten: "bottom" },
    vt: { x: "horizontally", y: "vertically" }, duplizieren: "Duplicate", entfernen: "Remove",
    tasten: "Shift+click or drag a frame: select several · Ctrl+D duplicate · Ctrl+C/V copy/paste · Del remove · Ctrl+Z/Y undo/redo",
    w: { klein: (px) => `small text (${px} px) – hard to read from 3 m`, kontrast: (r) => `low contrast (${r}:1) between text and background`,
         ueberlauf: "content does not fit completely", verdeckt: "completely covered by another element",
         videos: (n) => `${n} live videos in the layout – each one costs computing time (server or player)` },
    hinweise: (n) => (n === 1 ? "1 note" : `${n} notes`),
    reiter: { inhalt: "Content", aussehen: "Look", wann: "When" }, wannAktiv: "Period or condition set",
    seite: { baustein: "Element", layout: "Layout" }, bausteinErst: "Click an element on the canvas first",
    layoutText: "Applies to the whole layout. Click an element on the canvas to configure it.",
    zoom: "Zoom", einpassen: "Fit", zoomHilfe: "Ctrl+mouse wheel over the canvas zooms", hilfe: "Help",
    h: { herkunft: "YouTube only allows private, non-commercial use. In a practice, shop, hotel or club choose “own media only” – "
           + "upload the media under Media → Files. Without media the window shows a calm picture.",
         sichtbar: "When switched off the element stays in the layout, but the TV does not show it.",
         karte: "Puts a semi-transparent card behind the content – easier to read on a busy background.",
         ausrichtung: "Where the content sits inside the element.",
         schrift: "Own font for this element only. “As layout” uses the font from the Layout tab.",
         textfarbe: "Own text colour. When ticked, the colour comes from the layout's colour scheme.",
         gewicht: "Stroke weight of the font.",
         position: "Position and size in grid cells: 48 × 27 cells are the whole screen, one cell is 40 pixels.",
         bedingung: "The element only appears when the value matches – for example a rain notice only when a sensor reports rain.",
         quelle: "Where the values come from. Add new data sources under Data sources.",
         pfad: "Which value of the answer is shown. Click “Choose” instead of typing.",
         entity: "Entity from Home Assistant, for example sensor.living_room_temperature. Suggestions appear while typing.",
         vorlage: "Text with {wert} as placeholder, for example “Level: {wert}”.",
         faktor: "The value is multiplied by this, for example 0.01 to turn centimetres into metres.",
         nachkomma: "How many decimal places. -1 shows the value as the source delivers it.",
         url: "Address of the web page. “Check” tells whether the page can be embedded.",
         neu_laden_min: "How often the page is reloaded. 0 means never.",
         intervall: "How often the camera picture is fetched. Shorter means more network load.",
         laufband: "Long text scrolls from right to left instead of being cut off.",
         deckkraft: "0 % is fully transparent, 100 % fully opaque.",
         ziel: "The countdown counts down to this moment.", ende: "Shown when the countdown has run out.",
         inhalt: "What the QR code contains: a link, a text or the Wi-Fi credentials.",
         stunden: "How far back the curve reaches.", anzahl: "How many entries are shown at most.",
         dauer: "How long each picture or page is shown." },
  },
};
const LB = () => LBED[E && E.sprache === "en" ? "en" : "de"];
const PALETTE = {
  zeit: ["uhr", "datum", "countdown", "temperatur", "wetterlage", "feuchte", "wind", "vorhersage", "unwetter"],
  text: ["text", "liste", "logo", "flaeche", "qrcode"],
  medien: ["video", "galerie", "pdf", "webseite", "webcam", "sender"],
  daten: ["apiwert", "apiliste", "apibild", "anzeige", "diagramm", "kalender"],
  ha: ["kachel", "raeume", "kamera", "meldung"],
};
const TYP_SYMBOL = { uhr: "clock-outline", datum: "calendar-today", countdown: "timer-sand", temperatur: "thermometer", wetterlage: "weather-partly-cloudy",
  feuchte: "water-percent", wind: "weather-windy", vorhersage: "calendar-week", unwetter: "alert", text: "format-text", liste: "format-list-bulleted",
  logo: "image", flaeche: "square", qrcode: "qrcode", video: "video", galerie: "image-multiple", pdf: "file-pdf-box", webseite: "web", webcam: "cctv",
  sender: "radio", apiwert: "numeric", apiliste: "rss", apibild: "image-area", anzeige: "gauge", diagramm: "chart-line", kalender: "calendar",
  kachel: "home-thermometer-outline", raeume: "floor-plan", kamera: "camera", meldung: "message-alert" };
let AUSWAHL = new Set();    // Mehrfachauswahl (GEWAEHLT = der Baustein, dessen Einstellungen rechts stehen)
let VORWAERTS = [];         // Wiederholen
let WARN = {};              // Warnungen je Baustein: { id: [Text, …] }
let LTASTEN = null;         // Kurzbefehle (document-weit, nur im Editor)

// Freie Stelle für einen neuen Baustein (zeilenweise, innerhalb des sicheren Rands), sonst leicht versetzt oben links
function freieStelle(els, w, h) {
  const frei = (x, y) => els.every((o) => !o.sichtbar || x + w <= o.x || o.x + o.w <= x || y + h <= o.y || o.y + o.h <= y);
  for (let y = 1; y + h <= 26; y++) for (let x = 1; x + w <= 47; x++) if (frei(x, y)) return [x, y];
  const n = els.length % 10;
  return [klemm(1 + n, 0, 48 - w), klemm(1 + n, 0, 27 - h)];
}
// Kontrast nach WCAG aus zwei CSS-Farben (rgb/rgba)
// Warnungen aus dem Layout selbst (auch ohne Vorschau): verdeckt, mehrere Live-Videos
function warnGeometrie(l) {
  const B = LB(), w = {}, els = l.elemente, dazu = (id, t) => { (w[id] = w[id] || []).push(t); };
  els.forEach((e, i) => {
    if (!e.sichtbar) return;
    const drueber = els.slice(i + 1).find((o) => o.sichtbar && (o.typ === "video" || o.typ === "flaeche" && (o.optionen.deckkraft ?? 100) >= 90 || o.karte) &&
      o.x <= e.x && o.y <= e.y && o.x + o.w >= e.x + e.w && o.y + o.h >= e.y + e.h);
    if (drueber) dazu(e.id, B.w.verdeckt);
  });
  const videos = els.filter((e) => e.sichtbar && e.typ === "video");
  if (videos.length > 1) videos.forEach((e) => dazu(e.id, B.w.videos(videos.length)));
  return w;
}
// Warnungen aus der Live-Vorschau (echte Schriftgrößen und Farben der TV-Seite). Seit 0.60 misst www/hinweise.js in der
// Vorschau selbst – dieselben Regeln gelten für das MCP-Werkzeug „preview“.
function warnVorschau(f) {
  const B = LB(), w = {};
  let roh = {};
  try { roh = f && f.contentWindow && typeof f.contentWindow.scHinweise === "function" ? f.contentWindow.scHinweise() : {}; } catch (_) { return w; }
  for (const [id, liste] of Object.entries(roh || {})) {
    const t = liste.map((h) => (h.art === "klein" ? B.w.klein(h.px) : h.art === "kontrast" ? B.w.kontrast(h.wert) : h.art === "ueberlauf" ? B.w.ueberlauf : "")).filter(Boolean);
    if (t.length) w[id] = t;
  }
  return w;
}
// welche Arten von Datenquellen ein Baustein anbietet
// Kalender als Symbole (seit 0.28): Vorschläge und Müll-Vorlage
const SYM_VORSCHLAG = ["mdi-trash-can", "mdi-trash-can-outline", "mdi-delete-variant", "mdi-leaf", "mdi-flower", "mdi-newspaper-variant",
  "mdi-package-variant", "mdi-recycle", "mdi-bottle-soda", "mdi-sofa", "mdi-biohazard", "mdi-pine-tree", "mdi-calendar", "mdi-calendar-star",
  "mdi-cake-variant", "mdi-school", "mdi-briefcase", "mdi-bell"];
const SYM_TEXTE = {
  de: { text: "Titel enthält", icon: "Symbol", farbe: "Farbe", neu: "Regel hinzufügen", vorlage: "Müll-Vorlage einfügen", weg: "entfernen",
        hilfe: "Für Termine, deren Titel den Text enthält (ohne Groß-/Kleinschreibung). Gleiche Symbole erscheinen nur einmal.",
        muell: [["Rest", "mdi-trash-can", "#9e9e9e"], ["Bio", "mdi-leaf", "#5aa646"], ["Papier", "mdi-newspaper-variant", "#3d8cd0"],
                ["Gelb", "mdi-recycle", "#f2c200"], ["Wertstoff", "mdi-recycle", "#f2c200"], ["Sperr", "mdi-sofa", "#a07850"], ["Problem", "mdi-biohazard", "#e05050"]] },
  en: { text: "Title contains", icon: "Icon", farbe: "Colour", neu: "Add rule", vorlage: "Insert waste template", weg: "remove",
        hilfe: "For events whose title contains the text (case-insensitive). The same icon appears only once.",
        muell: [["Residual", "mdi-trash-can", "#9e9e9e"], ["Organic", "mdi-leaf", "#5aa646"], ["Paper", "mdi-newspaper-variant", "#3d8cd0"],
                ["Recycl", "mdi-recycle", "#f2c200"], ["Bulky", "mdi-sofa", "#a07850"], ["Hazard", "mdi-biohazard", "#e05050"]] },
};
const QUELL_ARTEN = { webcam: ["video"], kalender: ["ical", "csv"], apibild: ["bild", "json"], apiliste: ["json", "rss", "ical", "text", "csv"],
  diagramm: ["json", "text", "csv"], apiwert: ["json", "text", "rss", "ical", "csv"], anzeige: ["json", "text", "csv"], countdown: ["json", "text", "ical", "csv"], liste: ["csv", "json"] };
const WAHL = { herkunft: ["kanal", "medien"], ansicht: ["liste", "symbole"], darstellung: ["balken", "ampel"], anpassung: ["einpassen", "fuellen"], modus: ["einbetten", "bild"],
  rand: ["schwarz", "unscharf"], reihenfolge: ["eigene", "name", "neu", "zufall"], uebergang: ["blenden", "hart"] };   // Galerie seit 0.45
// Schriftvorschau in Auswahllisten (seit 0.45.1 per Skript – Cockpit lässt style="…" im HTML nicht zu)
const schriftVorschau = (w) => w.querySelectorAll("option[data-schrift]").forEach((o) => { o.style.fontFamily = `'${o.dataset.schrift}'`; });
const galerieOptionen = (w, leer) => `<option value="">${esc(leer)}</option>` + ((E.galerie && E.galerie.ordner) || [])
  .map((o) => `<option value="${esc(o.id)}" ${o.id === w ? "selected" : ""}>${esc(o.name)}</option>`).join("");
const ENT_DOMAINS = { temperatur: ["weather", "sensor"], wetterlage: ["weather"], feuchte: ["weather", "sensor"], wind: ["weather", "sensor"],
  kamera: ["camera"], kalender: ["calendar"], meldung: ["input_text", "sensor", "text"] };

let LS = null;            // Arbeitskopie aller Layouts
let LI = 0;               // gewähltes Layout
let GEWAEHLT = null;      // gewählter Baustein (id)
let letzterKlick = null;  // Stelle des letzten Klicks auf die Leinwand (Durchschalten übereinanderliegender Bausteine)
let VERLAUF = [];         // Rückgängig
let GEAENDERT = false;
let VORSCHAU = null;      // Werte für die Vorschau

// ---------- Live-Vorschau (seit 0.55) ----------
// Die echte TV-Seite läuft verkleinert unter der Leinwand (www/vorschau.html in einem eingebetteten Fenster). Der Entwurf
// geht ungespeichert an den Dienst (/api/vorschau/entwurf, nur im Speicher), die Seite holt ihn mit ?entwurf=<Kennung>.
// Adressen: in Cockpit externe Kanäle (gleicher Ursprung, kein Kopf X-SignageCast), im Docker-Betrieb /tvseite/.
window.SC_VORSCHAU = {
  param: "",
  adr: (p) => (CONTAINER ? "/tvseite" + p : "/cockpit/channel/" + cockpit.transport.csrf_token + "?" + window.btoa(JSON.stringify(
    { payload: "http-stream2", address: "127.0.0.1", port: 8080, method: "GET", path: p, headers: {}, binary: "raw", external: {} }))),
};
let EIG_REITER = "inhalt";  // seit 0.59: Reiter der Baustein-Eigenschaften (Inhalt, Aussehen, Wann)
try { EIG_REITER = localStorage.getItem("signagecast-eig-reiter") || "inhalt"; } catch (_) { /* egal */ }
let ZOOM = 0;               // seit 0.59: 0 = einpassen, sonst Maßstab zur echten Größe (1 = 1920 px breit)
const ZOOM_STUFEN = [0.5, 0.75, 1, 1.5, 2];
const AUSSEHEN_OPT = ["farbe", "deckkraft", "anpassung", "laufband", "zoom"];
const VS = { an: true, id: "", tageszeit: "", takt: null, fenster: null, rand: false, warnTakt: null, nachLaden: null };
try { VS.an = localStorage.getItem("signagecast-vorschau") !== "skizze"; VS.rand = localStorage.getItem("signagecast-rand") === "1"; } catch (_) { /* egal */ }
// Hilfslinien (seit 0.55): beim Verschieben/Größe ändern Linien, wo Kanten oder Mitten mit anderen Bausteinen oder der
// Bildmitte übereinstimmen. Das Raster (48 × 27 Felder) bleibt die Einheit – es wird nichts verschoben, nur gezeigt.
function hilfslinien(lw, e, alle) {
  lw.querySelectorAll(".lw-linie").forEach((x) => x.remove());
  if (!e) return;
  const andere = alle.filter((o) => o.id !== e.id && o.sichtbar);
  const achsen = [["x", "w", 48, 24], ["y", "h", 27, 13.5]];
  for (const [p, g, max, mitte] of achsen) {
    const eig = [e[p], e[p] + e[g] / 2, e[p] + e[g]];
    const ziele = new Map([[mitte, [0, p === "x" ? 27 : 48]]]);
    for (const o of andere) {
      for (const v of [o[p], o[p] + o[g] / 2, o[p] + o[g]]) {
        const q = p === "x" ? "y" : "x", h = p === "x" ? "h" : "w";
        const [a, b] = ziele.get(v) || [Infinity, -Infinity];
        ziele.set(v, [Math.min(a, o[q], e[q]), Math.max(b, o[q] + o[h], e[q] + e[h])]);
      }
    }
    for (const v of new Set(eig)) {
      if (!ziele.has(v) || v <= 0 || v >= max) continue;
      const [a, b] = ziele.get(v), li = document.createElement("div");
      li.className = "lw-linie " + (p === "x" ? "senkrecht" : "waagrecht") + (v === mitte ? " mitte" : "");
      const quer = p === "x" ? 27 : 48;
      Object.assign(li.style, p === "x" ? { left: v / 48 * 100 + "%", top: a / quer * 100 + "%", height: (b - a) / quer * 100 + "%" }
                                         : { top: v / 27 * 100 + "%", left: a / quer * 100 + "%", width: (b - a) / quer * 100 + "%" });
      lw.appendChild(li);
    }
  }
}
function vorschauFenster(huelle) {
  if (!huelle) return;
  let f = huelle.querySelector("iframe.lw-vorschau");
  if (!VS.an || !VS.id) { if (f) f.remove(); VS.fenster = null; return; }
  if (!f) {
    window.SC_VORSCHAU.param = `tv=${encodeURIComponent(E.fernseher[0].id)}&vorschau=1&entwurf=${VS.id}`;
    f = document.createElement("iframe");
    f.className = "lw-vorschau"; f.title = "Vorschau"; f.tabIndex = -1;
    f.setAttribute("aria-hidden", "true");
    f.src = window.SC_VORSCHAU.adr("/vorschau.html");
    huelle.prepend(f);
  }
  VS.fenster = f;
  const lw = huelle.querySelector(".leinwand");
  const passen = () => { if (lw) f.style.transform = `scale(${lw.clientWidth / 1920})`; };
  passen();
  if (!huelle.dataset.beobachtet && window.ResizeObserver) { huelle.dataset.beobachtet = "1"; new ResizeObserver(passen).observe(huelle); }
}
function vorschauSenden(layout) {
  if (!VS.an) return;
  clearTimeout(VS.takt);
  VS.takt = setTimeout(async () => {
    try {
      const r = await senden("/api/vorschau/entwurf", { id: VS.id, layout, tageszeit: VS.tageszeit });
      const neu = r.id !== VS.id;
      VS.id = r.id;
      const f = VS.fenster, w = f && f.isConnected && f.contentWindow;
      if (!neu && w && typeof w.laden === "function") w.laden();
      else vorschauFenster(document.querySelector(".lw-huelle"));
      clearTimeout(VS.warnTakt);                 // seit 0.58: Warnungen aus der fertig gezeichneten Vorschau
      VS.warnTakt = setTimeout(() => { if (VS.nachLaden) VS.nachLaden(); }, neu ? 4000 : 1800);
    } catch (_) { /* Vorschau ist Komfort – Fehler nicht melden */ }
  }, 250);
}
let ANSICHT = "liste";
let LTEIL = "designer", LSUCHE = "";   // seit 0.66: Reiter des offenen Layouts (uebersicht | designer | verlauf) und Suche in der Liste    // seit 0.17.2: „liste“ (Kacheln aller Layouts) oder „editor“ (ein Layout)

async function layoutSeite(inhalt) {
  const L = LTEXTE[E.sprache] || LTEXTE.de;
  if (!LS) { LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; ANSICHT = "liste"; }
  const [ents, vorl, vd] = await Promise.all([entitaeten(), holen("/api/vorlagen"), holen("/api/vorschau/daten?tv=" + encodeURIComponent(E.fernseher[0].id)).catch(() => null)]);
  VORSCHAU = vd && vd.ok ? vd : null;
  const handy = () => window.innerWidth < 700;
  const lay = () => LS[LI];
  const merken = () => { VERLAUF.push(JSON.stringify(LS)); if (VERLAUF.length > 40) VERLAUF.shift(); VORWAERTS = []; GEAENDERT = true; };
  const B = LB();
  const zurueck = () => { if (!VERLAUF.length) return; VORWAERTS.push(JSON.stringify(LS)); LS = JSON.parse(VERLAUF.pop()); LI = Math.min(LI, LS.length - 1); GEAENDERT = true; zeichnen(); };
  const vor = () => { if (!VORWAERTS.length) return; VERLAUF.push(JSON.stringify(LS)); LS = JSON.parse(VORWAERTS.pop()); LI = Math.min(LI, LS.length - 1); GEAENDERT = true; zeichnen(); };
  const gewaehlte = () => lay().elemente.filter((x) => AUSWAHL.has(x.id));
  const neuZeichnen = () => { if (handy()) listeZeichnen(); else leinwandZeichnen(); eigenschaftenZeichnen(); const s = $("#lSpeichern"); if (s && GEAENDERT) s.textContent = L.speichern + " *"; };
  const nutzer = (id) => E.fernseher.filter((t) => t.layout === id || (t.zeitplan || []).some((z) => z.layout === id)).map((t) => t.name);

  const offen = () => {};     // seit 0.59 steht der Hintergrund im Reiter „Layout“ statt in einem zugeklappten Bereich
  const zeichnen = () => {
    const l = lay();
    if (LTEIL !== "designer") return nebenZeichnen();
    inhalt.innerHTML = `<datalist id="ents">${ents.map((x) => `<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("")}</datalist>
      <div class="karte">
        <div class="zeile layoutkopf"><button class="knopf" id="lListe">← ${esc(L.alleLayouts)}</button>
          <input type="text" id="lName" class="layoutname" value="${esc(l.name)}" aria-label="${esc(L.name)}">
          <span class="leer"></span>
          <button class="knopf" id="lZurueck" title="Strg+Z" ${VERLAUF.length ? "" : "disabled"}><i class="mdi mdi-undo"></i> ${esc(L.rueckgaengig)}</button>
          <button class="knopf" id="lVor" title="Strg+Y" ${VORWAERTS.length ? "" : "disabled"}><i class="mdi mdi-redo"></i> ${esc(B.wiederholen)}</button>
          <button class="knopf haupt" id="lSpeichern">${esc(L.speichern)}${GEAENDERT ? " *" : ""}</button></div>
        ${lReiter()}
        ${nutzer(l.id).length ? `<p class="laeuft">● ${esc(L.laeuftAuf(nutzer(l.id).join(", ")))} – ${esc(L.laeuftHinweis)}</p>` : `<p class="leise">${esc(L.nichtVerwendet)}</p>`}
        <div class="zeile"><button class="knopf haupt" id="bPalette" aria-expanded="false" aria-controls="palette">${esc(B.baustein)}</button>
          ${handy() ? "" : `<span class="leer"></span><label for="lAnsicht">${esc(L.ansicht)}</label><select id="lAnsicht">${Object.keys(L.ansichtArt).map((k) => `<option value="${k}" ${(k === "vorschau") === VS.an ? "selected" : ""}>${esc(L.ansichtArt[k])}</option>`).join("")}</select>
          <label for="lZoom" title="${esc(B.zoomHilfe)}">${esc(B.zoom)}</label><select id="lZoom" title="${esc(B.zoomHilfe)}"><option value="0">${esc(B.einpassen)}</option>${ZOOM_STUFEN.map((z) => `<option value="${z}" ${z === ZOOM ? "selected" : ""}>${z * 100} %</option>`).join("")}</select>
          <label title="${esc(L.randHilfe)}"><input type="checkbox" id="lRand" ${VS.rand ? "checked" : ""}> ${esc(L.rand)}</label>
          <select id="lTz" aria-label="${esc(L.tzVorschau)}" ${VS.an ? "" : "hidden"}><option value="">${esc(L.tzAuto)}</option>${["morgen", "tag", "abend", "nacht"].map((z) => `<option value="${z}" ${z === VS.tageszeit ? "selected" : ""}>${esc(L.zeitName[z])}</option>`).join("")}</select>`}</div>
        <div class="palette" id="palette" hidden><p class="leise">${esc(B.leisteTitel)}</p>
          ${Object.keys(PALETTE).map((g) => `<div class="pal-gruppe"><h4>${esc(B.gruppen[g])}</h4><div class="pal-kacheln">${PALETTE[g].filter((t) => L.typ[t]).map((t) =>
            `<button type="button" class="pal-kachel" draggable="${!handy()}" data-typ="${t}" title="${esc(L.typ[t])}"><i class="mdi mdi-${TYP_SYMBOL[t] || "plus"}"></i><span>${esc(L.typ[t])}</span></button>`).join("")}</div></div>`).join("")}
          ${Object.keys(L.typ).filter((t) => !Object.values(PALETTE).flat().includes(t)).map((t) =>
            `<button type="button" class="pal-kachel" data-typ="${t}"><i class="mdi mdi-plus"></i><span>${esc(L.typ[t])}</span></button>`).join("")}</div>
        <p class="leise">${esc(handy() ? L.hinweisHandy : L.hinweisZiehen)}${!handy() && VS.an ? " " + esc(L.vorschauHinweis) : ""}</p>
        ${handy() ? "" : `<p class="leise">${esc(B.tasten)}</p>`}
        <div id="lWarn"></div>
      </div>
      <div class="layoutbereich"><div id="leinwandRahmen"></div><div class="lw-seite">${handy() ? "" : `<div class="karte" id="ebenen"></div>`}
        <div class="reiter seitenreiter" role="tablist">${["baustein", "layout"].map((r) => `<button type="button" role="tab" class="reiter-knopf" data-seite="${r}" aria-selected="false">${esc(B.seite[r])}</button>`).join("")}</div>
        <div class="karte" id="eigenschaften" role="tabpanel"></div>
        <div class="karte" id="layoutEig" role="tabpanel" hidden><h2>${esc(L.hgFarben)}</h2><p class="leise">${esc(B.layoutText)}</p>
          <div class="zeile"><label>${esc(L.hintergrund)}</label><select id="hgArt">${Object.keys(L.hgArt).map((k) => `<option value="${k}" ${k === l.hintergrund.art ? "selected" : ""}>${esc(L.hgArt[k])}</option>`).join("")}</select></div>
          <div class="eintrag" id="hgStil" ${l.hintergrund.art === "stil" ? "" : "hidden"}>
            <div class="zeile"><label>${esc(L.stil)}</label><select id="hgStilWahl">${Object.keys(L.stilArt).map((k) => `<option value="${k}" ${k === l.hintergrund.stil ? "selected" : ""}>${esc(L.stilArt[k])}</option>`).join("")}</select></div>
            <div class="stilbilder" id="stilBilder"></div>
            <div class="zeile"><label>${esc(L.wechsel)}</label><select id="hgWechsel">${Object.keys(L.wechselArt).map((k) => `<option value="${k}" ${k === l.hintergrund.wechsel ? "selected" : ""}>${esc(L.wechselArt[k])}</option>`).join("")}</select></div>
            <div class="zeile" ${l.hintergrund.wechsel === "diashow" ? "" : "hidden"} id="hgDiaZeile"><label>${esc(L.diashowMin)}</label><input type="number" id="hgDia" min="10" max="7200" value="${l.hintergrund.diashow_s || l.hintergrund.diashow_min * 60}"></div>
            <p class="leise">${esc(L.tzHinweis)}</p></div>
          <div class="eintrag" id="hgEigen" ${l.hintergrund.art === "bild" ? "" : "hidden"}>
            <div class="zeile"><label>${esc(L.hauptbild)}</label><input type="file" data-zeit="" accept="image/jpeg,image/png"><span class="leise">${esc(l.hintergrund.bild || "")}</span></div>
            <p class="leise">${esc(L.jeZeit)}</p>
            ${["morgen", "tag", "abend", "nacht"].map((z) => `<div class="zeile"><label>${esc(L.zeitName[z])}</label><input type="file" data-zeit="${z}" accept="image/jpeg,image/png">
              <span class="leise">${esc(l.hintergrund.bilder_tageszeit[z] || "")}</span>${l.hintergrund.bilder_tageszeit[z] ? `<button class="knopf gefahr" data-weg="${z}">${esc(L.entfernenKurz)}</button>` : ""}</div>`).join("")}</div>
          <div class="eintrag" id="hgGalerie" ${l.hintergrund.art === "galerie" ? "" : "hidden"}>
            <div class="zeile"><label>${esc(L.galHg)}</label><select id="hgGalOrdner">${galerieOptionen(l.hintergrund.galerie, L.galKeinOrdner)}</select>
              <label>${esc(L.galHgSek)}</label><input type="number" id="hgGalSek" min="5" max="3600" value="${l.hintergrund.galerie_s || 60}"></div>
            <p class="leise"><a href="#galerie">${esc(L.galOrdnerAnlegen)}</a></p></div>
          <div class="zeile" id="hgFarbZeile" ${l.hintergrund.art === "farbe" ? "" : "hidden"}><label>${esc(L.hgArt.farbe)}</label><input type="color" id="hgFarbe" value="${esc(l.hintergrund.farbe)}"></div>
          <div class="zeile"><label>${esc(L.bereich)}</label></div>
          <div class="zeile pos">${["x", "y", "w", "h"].map((k) => `<label>${{ x: "←", y: "↓", w: "↔", h: "↕" }[k]}<input type="number" data-bereich="${k}" value="${l.hintergrund.bereich[k]}"></label>`).join("")}
            <button class="knopf" id="hgGanz">${esc(L.ganzeFlaeche)}</button></div>
          <div class="zeile"><label>${esc(L.anpassung)}</label><select id="hgAnpassung">${Object.keys(L.anpassungArt).map((k) => `<option value="${k}" ${k === l.hintergrund.anpassung ? "selected" : ""}>${esc(L.anpassungArt[k])}</option>`).join("")}</select>
            <label>${esc(L.ausschnitt)}</label><select id="hgAusschnitt">${Object.keys(L.ausschnittArt).map((k) => `<option value="${k}" ${k === l.hintergrund.ausschnitt ? "selected" : ""}>${esc(L.ausschnittArt[k])}</option>`).join("")}</select></div>
          <div class="zeile"><label><input type="checkbox" id="hgNacht" ${l.hintergrund.nachts_dunkler ? "checked" : ""}> ${esc(L.nachtsDunkler)}</label>
            <label><input type="checkbox" id="hgDunkel" ${l.hintergrund.abdunkeln ? "checked" : ""}> ${esc(L.abdunkeln)}</label>
            <label ${l.hintergrund.art === "farbe" ? "hidden" : ""}><input type="checkbox" id="hgBewegen" ${l.hintergrund.bewegen ? "checked" : ""}> ${esc(L.bewegen)}</label></div>
          <div class="zeile"><label>${esc(L.schema)}</label><select id="thSchema">${Object.keys(L.schemaArt).map((k) => `<option value="${k}" ${k === l.thema.schema ? "selected" : ""}>${esc(L.schemaArt[k])}</option>`).join("")}</select>
            <label>${esc(L.karten)}</label><select id="thKarte">${Object.keys(L.kartenArt).map((k) => `<option value="${k}" ${k === (l.thema.karte || "weiss") ? "selected" : ""}>${esc(L.kartenArt[k])}</option>`).join("")}</select>
            <label>${esc(L.akzent)}</label><input type="color" id="thAkzent" value="${esc(l.thema.akzent)}">
            <label>${esc(L.schrift)}</label><select id="thSchrift">${SCHRIFTEN.map((k) => `<option data-schrift="${esc(k)}" ${k === l.thema.schrift ? "selected" : ""}>${esc(k)}</option>`).join("")}</select></div>
        </div></div></div>`;
    inhalt.insertAdjacentHTML("beforeend", lLoeschenHtml(l));
    lReiterAnbinden(); lLoeschenAnbinden(l);
    schriftVorschau(inhalt);
    if (handy()) listeZeichnen(); else leinwandZeichnen();
    eigenschaftenZeichnen();
    // Kopf
    $("#lListe").onclick = () => {
      if (GEAENDERT && !confirm(L.verwerfen)) return;
      LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; VORWAERTS = []; GEWAEHLT = null; AUSWAHL.clear(); ANSICHT = "liste"; listeAlle();
    };
    $("#lSpeichern").onclick = (e) => aktion(e.target, async () => {
      await speichernE({ layouts: LS }); LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; VORWAERTS = []; zeichnen();
    }, L.gespeichert);
    $("#lZurueck").onclick = zurueck;
    $("#lVor").onclick = vor;
    const kopf = (f) => () => { merken(); f(); GEAENDERT = true; $("#lSpeichern").textContent = L.speichern + " *"; if (!handy()) leinwandZeichnen(); };
    $("#lName").oninput = kopf(() => { lay().name = $("#lName").value; });
    $("#hgArt").onchange = () => { merken(); lay().hintergrund.art = $("#hgArt").value; zeichnen(); offen(); };
    $("#hgStilWahl").onchange = () => { merken(); lay().hintergrund.stil = $("#hgStilWahl").value; zeichnen(); offen(); };
    $("#hgWechsel").onchange = () => { merken(); lay().hintergrund.wechsel = $("#hgWechsel").value; zeichnen(); offen(); };
    $("#hgDia").onchange = kopf(() => { const sek = klemm(Number($("#hgDia").value) || 600, 10, 7200); lay().hintergrund.diashow_s = sek; lay().hintergrund.diashow_min = klemm(Math.round(sek / 60), 1, 120); });
    $("#hgBewegen").onchange = kopf(() => { lay().hintergrund.bewegen = $("#hgBewegen").checked; });
    $("#hgGalOrdner").onchange = kopf(() => { lay().hintergrund.galerie = $("#hgGalOrdner").value; });
    $("#hgGalSek").onchange = kopf(() => { lay().hintergrund.galerie_s = Number($("#hgGalSek").value) || 60; });
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
    $("#thKarte").onchange = kopf(() => { lay().thema.karte = $("#thKarte").value; });
    $("#thAkzent").oninput = kopf(() => { lay().thema.akzent = $("#thAkzent").value; });
    $("#thSchrift").onchange = kopf(() => { lay().thema.schrift = $("#thSchrift").value; });
    if ($("#lAnsicht")) $("#lAnsicht").onchange = () => {
      VS.an = $("#lAnsicht").value === "vorschau";
      try { localStorage.setItem("signagecast-vorschau", VS.an ? "vorschau" : "skizze"); } catch (_) { /* egal */ }
      zeichnen();
    };
    if ($("#lRand")) $("#lRand").onchange = () => {
      VS.rand = $("#lRand").checked;
      try { localStorage.setItem("signagecast-rand", VS.rand ? "1" : "0"); } catch (_) { /* egal */ }
      leinwandZeichnen();
    };
    if ($("#lZoom")) $("#lZoom").onchange = () => zoomSetzen(Number($("#lZoom").value));
    const rz = $("#leinwandRahmen");
    if (!handy()) rz.addEventListener("wheel", (ev) => {      // Strg+Mausrad: zoomen, die Stelle unter dem Mauszeiger bleibt stehen
      if (!(ev.ctrlKey || ev.metaKey)) return;
      ev.preventDefault();
      const passt = rz.clientWidth / 1920, jetzt = ZOOM || passt;
      let neu = ev.deltaY < 0 ? ZOOM_STUFEN.find((z) => z > jetzt * 1.01) : [...ZOOM_STUFEN].reverse().find((z) => z < jetzt * 0.99);
      if (neu === undefined) neu = ev.deltaY < 0 ? ZOOM_STUFEN[ZOOM_STUFEN.length - 1] : 0;
      if (neu && neu <= passt) neu = 0;
      const r = rz.getBoundingClientRect(), mx = ev.clientX - r.left, my = ev.clientY - r.top;
      const fx = (rz.scrollLeft + mx) / (jetzt * 1920), fy = (rz.scrollTop + my) / (jetzt * 1080);
      zoomSetzen(neu);
      const m = ZOOM || rz.clientWidth / 1920;
      rz.scrollLeft = fx * m * 1920 - mx; rz.scrollTop = fy * m * 1080 - my;
    }, { passive: false });
    inhalt.querySelectorAll("[data-seite]").forEach((k) => {
      k.onclick = () => { if (k.dataset.seite === "layout") { GEWAEHLT = null; AUSWAHL.clear(); neuZeichnen(); } };
    });
    if ($("#lTz")) $("#lTz").onchange = () => { VS.tageszeit = $("#lTz").value; vorschauSenden(lay()); };
    const pal = $("#palette");
    let palOffen = false;
    try { palOffen = localStorage.getItem("signagecast-palette") === "1"; } catch (_) { /* egal */ }
    const palZeigen = (an) => { pal.hidden = !an; $("#bPalette").setAttribute("aria-expanded", String(an)); try { localStorage.setItem("signagecast-palette", an ? "1" : "0"); } catch (_) { /* egal */ } };
    palZeigen(palOffen);
    $("#bPalette").onclick = () => palZeigen(pal.hidden);
    pal.querySelectorAll(".pal-kachel").forEach((k) => {
      k.onclick = () => { palZeigen(false); neuerBaustein(k.dataset.typ); };   // zu, damit der neue Baustein zu sehen ist
      k.ondragstart = (ev) => { ev.dataTransfer.setData("text/plain", "sc-baustein:" + k.dataset.typ); ev.dataTransfer.effectAllowed = "copy"; };
    });
  };
  // Zoom (seit 0.59): Hülle in echter Breite × Maßstab, der Rahmen scrollt; Vorschau und Bausteine skalieren mit
  const zoomSetzen = (z) => {
    ZOOM = z || 0;
    const rz = $("#leinwandRahmen"), h = rz && rz.querySelector(".lw-huelle");
    if (!h) return;
    rz.classList.toggle("gezoomt", !!ZOOM);
    h.style.width = ZOOM ? ZOOM * 1920 + "px" : "";
    const w = $("#lZoom"); if (w) w.value = String(ZOOM);
  };
  // Neuer Baustein an einer freien Stelle oder dort, wo er hingezogen wurde (x, y = Mitte in Feldern)
  const neuerBaustein = (typ, mx, my) => {
    merken();
    const [w, h] = STD_GROESSE[typ] || [6, 2];
    const [x, y] = mx == null ? freieStelle(lay().elemente, w, h) : [klemm(Math.round(mx - w / 2), 0, 48 - w), klemm(Math.round(my - h / 2), 0, 27 - h)];
    const e = { id: neueId().slice(0, 8), typ, x, y, w, h, sichtbar: true, karte: ["kachel", "vorhersage", "kalender"].includes(typ),
                ausrichtung: typ === "liste" ? "oben-links" : "links", optionen: JSON.parse(JSON.stringify(BAUSTEINE[typ] || {})), bedingung: null };
    lay().elemente.push(e); GEWAEHLT = e.id; AUSWAHL = new Set([e.id]); zeichnen();
  };
  // Mehrfachauswahl: duplizieren, kopieren/einfügen, entfernen, ausrichten, verteilen
  const kopien = (els, versatz) => els.map((x) => Object.assign(JSON.parse(JSON.stringify(x)), { id: neueId().slice(0, 8),
    x: klemm(x.x + versatz, 0, 48 - x.w), y: klemm(x.y + versatz, 0, 27 - x.h) }));
  const einfuegen = (neu) => {
    if (!neu.length) return;
    merken(); lay().elemente.push(...neu);
    AUSWAHL = new Set(neu.map((x) => x.id)); GEWAEHLT = neu[neu.length - 1].id; zeichnen();
  };
  const duplizieren = () => einfuegen(kopien(gewaehlte(), 1));
  const kopieren = () => { const g = gewaehlte(); if (!g.length) return false; try { localStorage.setItem("signagecast-ablage", JSON.stringify(g)); } catch (_) { /* egal */ } return true; };
  const ablageEinfuegen = () => {
    let g = null;
    try { g = JSON.parse(localStorage.getItem("signagecast-ablage") || "null"); } catch (_) { g = null; }
    if (Array.isArray(g)) einfuegen(kopien(g.filter((x) => x && L.typ[x.typ]), 1));
  };
  const entfernen = () => {
    if (!AUSWAHL.size) return;
    merken(); lay().elemente = lay().elemente.filter((x) => !AUSWAHL.has(x.id)); AUSWAHL.clear(); GEWAEHLT = null; zeichnen();
  };
  const ausrichten = (art) => {
    const g = gewaehlte(); if (g.length < 2) return;
    merken();
    const x0 = Math.min(...g.map((e) => e.x)), x1 = Math.max(...g.map((e) => e.x + e.w)), y0 = Math.min(...g.map((e) => e.y)), y1 = Math.max(...g.map((e) => e.y + e.h));
    for (const e of g) {
      if (art === "links") e.x = x0; else if (art === "rechts") e.x = x1 - e.w; else if (art === "hmitte") e.x = klemm(Math.round((x0 + x1 - e.w) / 2), 0, 48 - e.w);
      else if (art === "oben") e.y = y0; else if (art === "unten") e.y = y1 - e.h; else if (art === "vmitte") e.y = klemm(Math.round((y0 + y1 - e.h) / 2), 0, 27 - e.h);
    }
    neuZeichnen(); vorschauSenden(lay());
  };
  const verteilen = (p) => {
    const g = gewaehlte(), q = p === "x" ? "w" : "h"; if (g.length < 3) return;
    merken();
    g.sort((a, b) => a[p] - b[p]);
    const anfang = g[0][p], ende = Math.max(...g.map((e) => e[p] + e[q])), luecke = (ende - anfang - g.reduce((s, e) => s + e[q], 0)) / (g.length - 1);
    let pos = anfang;
    for (const e of g) { e[p] = Math.round(pos); pos += e[q] + luecke; }
    neuZeichnen(); vorschauSenden(lay());
  };
  // Warnungen zeigen: Zeichen am Baustein, Liste unter der Werkzeugzeile, Hinweise in den Einstellungen
  const warnZeigen = () => {
    const l = lay(); if (!l) return;
    const g = warnGeometrie(l), v = VS.an && !handy() ? warnVorschau(VS.fenster) : {};
    WARN = {};
    for (const q of [g, v]) for (const [id, t] of Object.entries(q)) WARN[id] = [...(WARN[id] || []), ...t];
    const lw = $("#leinwand");
    if (lw) lw.querySelectorAll(".lw-baustein").forEach((b) => {
      b.querySelectorAll(".lw-warn").forEach((x) => x.remove());
      const w = WARN[b.dataset.id];
      if (w) b.appendChild(el(`<span class="lw-warn" title="${esc(w.join(" · "))}">⚠</span>`));
    });
    const ziel = $("#lWarn"); if (!ziel) return;
    const ids = l.elemente.filter((e) => WARN[e.id]).map((e) => e.id);
    ziel.innerHTML = ids.length ? `<details class="warnliste"><summary class="warn">⚠ ${esc(B.hinweise(ids.reduce((s, id) => s + WARN[id].length, 0)))}</summary>
      ${ids.map((id) => { const e = l.elemente.find((x) => x.id === id); return `<button type="button" class="knopf klein warnzeile" data-id="${esc(id)}"><b>${esc(L.typ[e.typ] || e.typ)}</b> ${esc(WARN[id].join(" · "))}</button>`; }).join("")}</details>` : "";
    ziel.querySelectorAll("[data-id]").forEach((k) => { k.onclick = () => { GEWAEHLT = k.dataset.id; AUSWAHL = new Set([GEWAEHLT]); neuZeichnen(); }; });
    const hier = $("#eigenschaften [data-warn]");
    if (hier) hier.innerHTML = GEWAEHLT && WARN[GEWAEHLT] ? WARN[GEWAEHLT].map((t) => `<p class="warn">⚠ ${esc(t)}</p>`).join("") : "";
  };
  VS.nachLaden = warnZeigen;

  // ---------- Gerüst des offenen Layouts (seit 0.66, UI-Regel Punkt 2 und 8.7): Übersicht → Designer → Verlauf, Löschen unten ----------
  const D = T.ding;
  const lReiter = () => `<nav class="kanal-reiter">${["uebersicht", "designer", "verlauf"].map((x) =>
    `<button type="button" data-lteil="${x}" class="${x === LTEIL ? "an" : ""}">${esc(x === "designer" ? L.designer : D[x])}</button>`).join("")}</nav>`;
  const lReiterAnbinden = () => inhalt.querySelectorAll("[data-lteil]").forEach((b) => { b.onclick = () => { LTEIL = b.dataset.lteil; zeichnen(); }; });
  const verwendung = (l) => {
    const direkt = E.fernseher.filter((t) => t.layout === l.id).map((t) => t.name);
    const zeit = E.fernseher.filter((t) => (t.zeitplan || []).some((z) => z.layout === l.id)).map((t) => t.name);
    const kar = E.fernseher.filter((t) => ((t.karussell || {}).aktiv && ((t.karussell || {}).layouts || []).includes(l.id))).map((t) => t.name);
    return [[L.vwDirekt, direkt], [L.vwZeitplan, zeit], [L.vwKarussell, kar]].filter(([, n]) => n.length);
  };
  const lLoeschenHtml = (l) => {
    const v = verwendung(l);
    return `<div class="karte"><div class="loeschen"><p class="leise">${esc(v.length ? D.verwendetVon(v.map(([k, n]) => k + ": " + n.join(", ")).join("; "))
      : LS.length < 2 ? L.letztes : D.nichtVerwendet)}</p>
      <button class="knopf gefahr" id="lLoeschen" ${v.length || LS.length < 2 ? "disabled" : ""}>${esc(L.loeschen)}</button></div></div>`;
  };
  const lLoeschenAnbinden = (l) => {
    const b = $("#lLoeschen");
    if (!b) return;
    b.onclick = (ev) => {
      if (GEAENDERT && !confirm(L.verwerfen)) return;
      if (!confirm(L.wirklichLoeschen + " „" + l.name + "“")) return;
      aktion(ev.target, async () => {
        LS = JSON.parse(JSON.stringify(E.layouts)).filter((x) => x.id !== l.id); LI = 0;
        await sofortSpeichern(); VORWAERTS = []; ANSICHT = "liste"; LTEIL = "designer"; listeAlle();
      });
    };
  };
  // Reiter „Übersicht“ und „Verlauf“ (der Designer zeichnet sich selbst)
  const nebenZeichnen = () => {
    const l = lay(), v = verwendung(l);
    inhalt.innerHTML = `<div class="karte"><div class="zeile layoutkopf"><button class="knopf" id="lListe">← ${esc(L.alleLayouts)}</button>
        <b class="layoutname">${esc(l.name)}</b>${GEAENDERT ? `<span class="warn">${esc(L.nichtGespeichert)}</span>` : ""}</div>
      ${lReiter()}<div id="lTeil"></div></div>${lLoeschenHtml(l)}`;
    const z = $("#lTeil");
    if (LTEIL === "uebersicht") {
      z.innerHTML = `<div class="raster"><div class="mini lk-gross"></div><div><div class="tabelle-rahmen"><table class="tabelle">
          <tr><td class="leise">${esc(D.status)}</td><td class="${v.length ? "gut" : ""}">${esc(v.length ? L.laeuftAuf(v.map(([, n]) => n.join(", ")).join(", ")) : L.nichtVerwendet)}</td></tr>
          ${v.map(([k, n]) => `<tr><td class="leise">${esc(k)}</td><td>${esc(n.join(", "))}</td></tr>`).join("")}
          <tr><td class="leise">${esc(L.bausteine)}</td><td>${l.elemente.length}</td></tr>
          <tr><td class="leise">${esc(D.zuletzt)}</td><td>${esc(zuletztText(LPZ, "layout:" + l.id))}</td></tr></table></div>
        <h3>${esc(D.schnell)}</h3><div class="zeile"><button class="knopf haupt" data-lteil="designer">${esc(L.bearbeitenL)}</button>
          <button class="knopf" id="lKopie">${esc(L.duplizieren)}</button><button class="knopf" id="lExport">${esc(L.exportieren)}</button>
          <button class="knopf" id="lVers">${esc(L.versionen)}</button></div></div></div>`;
      miniVorschau(z.querySelector(".mini"), l);
      $("#lKopie").onclick = (ev) => aktion(ev.target, async () => {
        if (GEAENDERT && !confirm(L.verwerfen)) return;
        LS = JSON.parse(JSON.stringify(E.layouts)); const c = JSON.parse(JSON.stringify(LS.find((x) => x.id === l.id) || l));
        c.id = neueId(); c.name += " (2)"; LS.push(c); await sofortSpeichern(); LI = LS.length - 1; zeichnen(); }, null);
      $("#lExport").onclick = () => exportieren(l);
      $("#lVers").onclick = () => aktion(null, () => versionenZeigen(l.id, l.name), null);
    } else {
      z.innerHTML = `<div data-verlauf></div><div class="zeile"><button class="knopf" id="lVers">${esc(L.versionen)}</button></div>`;
      verlaufZeichnen(z.querySelector("[data-verlauf]"), "layout:" + l.id).catch(() => {});
      $("#lVers").onclick = () => aktion(null, () => versionenZeigen(l.id, l.name), null);
    }
    lReiterAnbinden(); lLoeschenAnbinden(l);
    $("#lListe").onclick = () => {
      if (GEAENDERT && !confirm(L.verwerfen)) return;
      LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; VORWAERTS = []; GEWAEHLT = null; AUSWAHL.clear(); ANSICHT = "liste"; LTEIL = "designer"; listeAlle();
    };
  };
  let LPZ = {};
  holen("/api/protokoll").then((d) => { LPZ = d.zuletzt || {}; if (ANSICHT === "liste" && aktiv === "layout" && document.body.contains(inhalt)) listeAlle(); }).catch(() => {});

  // ---------- Übersicht aller Layouts (seit 0.17.2) – Aktionen hier speichern sofort ----------
  const sofortSpeichern = async () => { await speichernE({ layouts: LS }); LS = JSON.parse(JSON.stringify(E.layouts)); GEAENDERT = false; VERLAUF = []; };
  const oeffnen = (i) => { LI = i; GEWAEHLT = null; ANSICHT = "editor"; LTEIL = "designer"; zeichnen(); window.scrollTo(0, 0); };
  // Mini-Vorschau: Stile per JavaScript setzen – Cockpits CSP verbietet style-Attribute im HTML-Text
  const miniVorschau = (ziel, l) => {
    ziel.style.background = l.hintergrund.art === "farbe" ? l.hintergrund.farbe : "linear-gradient(160deg,#55606b,#2b3138)";
    for (const x of l.elemente.filter((y) => y.sichtbar)) {
      const sp = document.createElement("span");
      sp.className = "mini-el " + (x.typ === "video" ? "video" : x.karte || x.typ === "flaeche" ? "karte" : "");
      Object.assign(sp.style, { left: x.x / 48 * 100 + "%", top: x.y / 27 * 100 + "%", width: x.w / 48 * 100 + "%", height: x.h / 27 * 100 + "%" });
      ziel.appendChild(sp);
    }
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
    await ablageLaden(`signagecast-layout-${l.name.replace(/[^A-Za-z0-9-]+/g, "_")}.json`, "application/json",
                      JSON.stringify({ art: "signagecast-layout", version: 2, layout: l, bilder }, null, 1));
  }, null);
  const importieren = async (datei) => aktion(null, async () => {
    const roh = await datei.text();
    let d; try { d = JSON.parse(roh); } catch (_) { return uebernehmen({ text: roh }); }     // z. B. Antwort einer KI mit Text drumherum
    const l2 = d && ["signagecast-layout", "tv-stream-layout"].includes(d.art) ? d.layout : d;
    if (!l2 || !Array.isArray(l2.elemente)) return uebernehmen({ layout: d });             // der Dienst sagt, was fehlt
    // mitgelieferte Bilder hochladen und Namen im Layout anpassen (der Name ergibt sich aus dem Inhalt)
    const neu = {};
    for (const [n, daten] of Object.entries(d.bilder || {})) neu[n] = (await senden("/api/bilder", { daten })).bild;
    const um = (n) => neu[n] || n;
    l2.hintergrund = l2.hintergrund || {};
    if (l2.hintergrund.bild) l2.hintergrund.bild = um(l2.hintergrund.bild);
    for (const k of Object.keys(l2.hintergrund.bilder_tageszeit || {})) l2.hintergrund.bilder_tageszeit[k] = um(l2.hintergrund.bilder_tageszeit[k]);
    for (const x of l2.elemente) if (x.optionen && x.optionen.bild) x.optionen.bild = um(x.optionen.bild);
    await uebernehmen({ layout: l2 });
  }, null);
  // Layout prüfen lassen (seit 0.38: fehlertolerant, nennt jede Reparatur), anhängen, speichern, Hinweise zeigen
  const uebernehmen = async (anfrage) => {
    const r = await senden("/api/layouts/pruefen", anfrage);
    LS.push(r.layout); await sofortSpeichern(); listeAlle();
    extra(r.hinweise.length ? `<p><b>${esc(L.importGespeichert)}: ${esc(r.layout.name)}</b></p><p>${esc(L.hinweiseTitel)}</p><ul>${r.hinweise.map((h) => `<li>${esc(meldungText(h, h.text))}</li>`).join("")}</ul>` : "", true);
    melden(L.importGespeichert);
  };
  // Zusatzkarte über den Layouts (Versionen, Einfügen, KI-Anleitung, Hinweise nach dem Import)
  const extra = (html, schliessbar) => {
    const z = $("#lExtra"); if (!z) return null;
    z.innerHTML = html ? `<div class="karte">${html}${schliessbar ? `<div class="zeile"><button class="knopf" id="lxZu">${esc(L.schliessen)}</button></div>` : ""}</div>` : "";
    if ($("#lxZu")) $("#lxZu").onclick = () => { z.innerHTML = ""; };
    if (html) z.scrollIntoView({ block: "nearest" });
    return z;
  };
  const versionLaden = (l) => ablageLaden(`signagecast-layout-${l.name.replace(/[^A-Za-z0-9-]+/g, "_")}.json`, "application/json",
                                          JSON.stringify({ art: "signagecast-layout", version: 2, layout: l }, null, 1));
  const zeit = (t) => new Date(t * 1000).toLocaleString(E.sprache === "en" ? "en-GB" : "de-DE", { dateStyle: "short", timeStyle: "short" });
  const versionenZeigen = async (lid, name) => {
    const d = await holen("/api/layouts/versionen?id=" + encodeURIComponent(lid));
    extra(`<h2>${esc(L.versionen)}: ${esc(name)}</h2><p class="leise">${esc(L.versionenText)}</p>
      ${d.versionen.length ? `<div class="tabelle-rahmen"><table class="tabelle">${d.versionen.map((v) => `<tr><td>${esc(zeit(v.zeit))}</td><td>${esc(v.wer)}</td>
        <td>${esc(v.name)} · ${esc(L.bausteineN(v.bausteine))}</td><td><button class="knopf" data-vw="${v.nr}">${esc(L.wiederherstellen)}</button>
        <button class="knopf" data-vd="${v.nr}">${esc(L.herunterladen)}</button></td></tr>`).join("")}</table></div>` : `<p class="leise">${esc(L.keineVersionen)}</p>`}`, true);
    document.querySelectorAll("[data-vw]").forEach((b) => { b.onclick = (ev) => {
      if (!confirm(L.wirklichWiederherstellen)) return;
      aktion(ev.target, async () => {
        await senden("/api/layouts/wiederherstellen", { id: lid, nr: Number(b.dataset.vw) });
        E = (await holen("/api/einstellungen")).einstellungen; LS = JSON.parse(JSON.stringify(E.layouts)); listeAlle();
      }, L.wiederhergestellt);
    }; });
    document.querySelectorAll("[data-vd]").forEach((b) => { b.onclick = (ev) => aktion(ev.target, async () => {
      await versionLaden((await holen(`/api/layouts/version?id=${encodeURIComponent(lid)}&nr=${b.dataset.vd}`)).layout); }, null); });
  };
  const geloeschteZeigen = (liste) => {
    extra(`<h2>${esc(L.geloeschte(liste.length))}</h2><div class="tabelle-rahmen"><table class="tabelle">${liste.map((g) => `<tr><td>${esc(g.name)}</td>
      <td class="leise">${esc(L.geloeschtAm)} ${esc(zeit(g.zeit))}</td><td><button class="knopf" data-gw="${esc(g.id)}">${esc(L.wiederherstellen)}</button>
      <button class="knopf" data-gv="${esc(g.id)}" data-gn="${esc(g.name)}">${esc(L.versionen)}</button></td></tr>`).join("")}</table></div>`, true);
    document.querySelectorAll("[data-gw]").forEach((b) => { b.onclick = (ev) => aktion(ev.target, async () => {
      await senden("/api/layouts/wiederherstellen", { id: b.dataset.gw, nr: 0 });
      E = (await holen("/api/einstellungen")).einstellungen; LS = JSON.parse(JSON.stringify(E.layouts)); listeAlle();
    }, L.wiederhergestellt); });
    document.querySelectorAll("[data-gv]").forEach((b) => { b.onclick = () => aktion(null, () => versionenZeigen(b.dataset.gv, b.dataset.gn), null); });
  };
  const einfuegenZeigen = () => {
    extra(`<h2>${esc(L.einfuegen.replace(" …", ""))}</h2><p class="leise">${esc(L.einfuegenText)}</p>
      <textarea id="lxText" rows="10" class="breit" spellcheck="false"></textarea>
      <div class="zeile"><button class="knopf haupt" id="lxOk">${esc(L.uebernehmen)}</button></div>`, true);
    $("#lxText").focus();
    $("#lxOk").onclick = (ev) => aktion(ev.target, () => uebernehmen({ text: $("#lxText").value }), null);
  };
  const kiZeigen = async () => {
    const format = await dienst.get("/api/layouts/format", {}, KOPF);
    const anleitung = `${L.kiEinleitung}\n\n${L.kiWunsch}\n\n${format}`;
    extra(`<h2>${esc(L.kiHilfe.replace(" …", ""))}</h2><p class="leise">${esc(L.kiText)}</p>
      <textarea id="lxKi" rows="8" class="breit" readonly spellcheck="false">${esc(anleitung)}</textarea>
      <div class="zeile"><button class="knopf haupt" id="lxKopieren">${esc(L.kiKopieren)}</button><button class="knopf" id="lxDatei">${esc(L.kiDatei)}</button>
        <button class="knopf" id="lxEinfuegen">${esc(L.einfuegen)}</button></div>`, true);
    $("#lxKopieren").onclick = async () => {
      const t = $("#lxKi");
      try { await navigator.clipboard.writeText(anleitung); } catch (_) { t.focus(); t.select(); document.execCommand("copy"); }
      melden(L.kiKopiert);
    };
    $("#lxDatei").onclick = (e) => aktion(e.target, () => ablageLaden("signagecast-layout-ki.md", "text/markdown", anleitung), null);
    $("#lxEinfuegen").onclick = einfuegenZeigen;
  };
  const listeAlle = () => {
    const treffer = (l) => !LSUCHE || l.name.toLowerCase().includes(LSUCHE.toLowerCase());
    inhalt.innerHTML = `<div class="kopfzeile"><h2>${esc(T.bereiche.layout)}</h2><button class="knopf" id="lNeuOben">+ ${esc(L.neu)}</button></div>
      <div class="zeile"><input type="search" id="lSuche" placeholder="${esc(T.ding.suchen)}" aria-label="${esc(T.ding.suchen)}" value="${esc(LSUCHE)}"></div>
      <div id="lExtra"></div><div class="layoutkacheln">${LS.map((l, i) => {
      if (!treffer(l)) return "";
      const n = nutzer(l.id);
      return `<div class="karte layoutkachel" data-i="${i}"><div class="mini"></div>
        <b class="lk-name">${esc(l.name)}</b>
        <span class="${n.length ? "laeuft" : "leise"}">${n.length ? esc(L.laeuftAuf(n.join(", "))) : esc(L.nichtVerwendet)}</span>
        <span class="leise">${esc(T.ding.zuletzt)}: ${esc(zuletztText(LPZ, "layout:" + l.id))}</span>
        <div class="zeile"><button class="knopf haupt" data-a="b">${esc(L.bearbeitenL)}</button>
          <details class="mehr"><summary class="knopf">⋯</summary><div class="mehr-menue">
            <button class="knopf" data-a="k">${esc(L.duplizieren)}</button><button class="knopf" data-a="x">${esc(L.exportieren)}</button>
            <button class="knopf" data-a="v">${esc(L.versionen)}</button></div></details></div></div>`;
    }).join("")}
      <div class="karte layoutkachel neu" id="lNeuKachel"><button class="neu-knopf" id="lNeu"><i class="mdi mdi-plus-circle-outline"></i>${esc(L.neu)}</button>
        <label class="leise importlink">${esc(L.importieren)} …<input type="file" id="lImport" accept=".json,.txt" hidden></label>
        <a href="#" class="leise importlink" id="lEinfuegen">${esc(L.einfuegen)}</a>
        <a href="#" class="leise importlink" id="lKi">${esc(L.kiHilfe)}</a></div></div>
      <p class="leise" id="lGeloescht"></p>`;
    inhalt.querySelectorAll(".layoutkachel[data-i]").forEach((k) => {
      const i = Number(k.dataset.i), l = LS[i];
      miniVorschau(k.querySelector(".mini"), l);
      k.querySelector(".mini").onclick = () => oeffnen(i);
      k.querySelectorAll("[data-a]").forEach((b) => { b.onclick = (ev) => {
        const a = b.dataset.a;
        if (a === "b") return oeffnen(i);
        if (a === "x") return exportieren(l);
        if (a === "v") return aktion(null, () => versionenZeigen(l.id, l.name), null);
        if (a === "k") return aktion(ev.target, async () => {
          const c = JSON.parse(JSON.stringify(l)); c.id = neueId(); c.name += " (2)"; LS.push(c); await sofortSpeichern(); listeAlle(); });
      }; });
    });
    $("#lNeuOben").onclick = () => { $("#lNeu").click(); $("#lNeuKachel").scrollIntoView({ block: "center" }); };
    $("#lSuche").oninput = (e) => { LSUCHE = e.target.value; listeAlle(); const f = $("#lSuche"); f.focus(); f.setSelectionRange(f.value.length, f.value.length); };
    $("#lImport").onchange = (e) => { if (e.target.files[0]) importieren(e.target.files[0]); };
    $("#lEinfuegen").onclick = (e) => { e.preventDefault(); einfuegenZeigen(); };
    $("#lKi").onclick = (e) => { e.preventDefault(); aktion(null, kiZeigen, null); };
    holen("/api/layouts/versionen?id=").then((d) => {            // gelöschte Layouts, die sich zurückholen lassen
      const z = $("#lGeloescht");
      if (!z || !d.geloescht.length) return;
      z.innerHTML = `<a href="#">${esc(L.geloeschte(d.geloescht.length))}</a>`;
      z.querySelector("a").onclick = (e) => { e.preventDefault(); geloeschteZeigen(d.geloescht); };
    }).catch(() => {});
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
    let lw = $("#leinwand");
    if (lw) lw.replaceChildren();               // seit 0.55: die Hülle mit der Live-Vorschau bleibt, nur die Bausteine neu
    else {
      rahmen.innerHTML = `<div class="lw-huelle"><div class="leinwand" id="leinwand" tabindex="0"></div></div>`;
      lw = $("#leinwand");
      zoomSetzen(ZOOM);
    }
    const massstab = () => lw.clientWidth / 1920;
    // Auswahl abgleichen (seit 0.58): GEWAEHLT gehört immer zur Auswahl, gelöschte Bausteine fallen heraus
    const ids = new Set(l.elemente.map((x) => x.id));
    AUSWAHL = new Set([...AUSWAHL].filter((id) => ids.has(id)));
    if (GEWAEHLT && !ids.has(GEWAEHLT)) GEWAEHLT = null;
    if (GEWAEHLT && !AUSWAHL.has(GEWAEHLT)) AUSWAHL = new Set([GEWAEHLT]);
    if (!GEWAEHLT) AUSWAHL.clear();
    lw.classList.toggle("mit-vorschau", VS.an && !handy());
    lw.style.background = VS.an && !handy() ? "transparent"
      : l.hintergrund.art === "farbe" ? l.hintergrund.farbe : "linear-gradient(160deg,#55606b,#2b3138)";
    if (VS.an && !handy()) { vorschauFenster(rahmen.querySelector(".lw-huelle")); vorschauSenden(l); }
    l.elemente.forEach((e, idx) => {
      const b = document.createElement("div");
      b.className = "lw-baustein" + (AUSWAHL.has(e.id) ? " gewaehlt" : "") + (e.sichtbar ? "" : " aus") + (e.karte ? " karte" : "") +
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
    for (const x of l.elemente.filter((y) => AUSWAHL.has(y.id) && y.id !== GEWAEHLT)) {   // weitere gewählte Bausteine
      const m = document.createElement("div");
      m.className = "lw-mit"; m.dataset.mit = x.id;
      setzen(m, x);
      lw.appendChild(m);
    }
    // Rahmen aufziehen auf freier Fläche: Bausteine darin wählen (mit Umschalt dazu); einfacher Klick hebt die Auswahl auf
    lw.onpointerdown = (ev) => {
      if (ev.target !== lw || ev.button !== 0) return;
      ev.preventDefault();
      const r = lw.getBoundingClientRect(), feld = r.width / 48, sx = ev.clientX, sy = ev.clientY, dazu = ev.shiftKey || ev.ctrlKey || ev.metaKey;
      const vorher = dazu ? new Set(AUSWAHL) : new Set();
      let lasso = null;
      lw.setPointerCapture(ev.pointerId);
      const grenzen = (mv) => [Math.min(sx, mv.clientX), Math.min(sy, mv.clientY), Math.max(sx, mv.clientX), Math.max(sy, mv.clientY)];
      lw.onpointermove = (mv) => {
        if (!lasso && Math.abs(mv.clientX - sx) + Math.abs(mv.clientY - sy) < 6) return;
        if (!lasso) { lasso = document.createElement("div"); lasso.className = "lw-lasso"; lw.appendChild(lasso); }
        const [a, b, c, d] = grenzen(mv);
        Object.assign(lasso.style, { left: a - r.left + "px", top: b - r.top + "px", width: c - a + "px", height: d - b + "px" });
      };
      lw.onpointerup = (mv) => {
        lw.onpointermove = null; lw.onpointerup = null;
        if (!lasso) { if (!dazu) { GEWAEHLT = null; AUSWAHL.clear(); leinwandZeichnen(); eigenschaftenZeichnen(); } lw.focus(); return; }
        const [a, b, c, d] = grenzen(mv).map((v, i) => (v - (i % 2 ? r.top : r.left)) / feld);
        const drin = l.elemente.filter((e) => e.x < c && e.x + e.w > a && e.y < d && e.y + e.h > b).map((e) => e.id);
        AUSWAHL = new Set([...vorher, ...drin]);
        GEWAEHLT = drin.length ? drin[drin.length - 1] : GEWAEHLT && AUSWAHL.has(GEWAEHLT) ? GEWAEHLT : null;
        leinwandZeichnen(); eigenschaftenZeichnen(); lw.focus();
      };
    };
    // Bausteine aus der Leiste hineinziehen
    lw.ondragover = (ev) => { if ([...ev.dataTransfer.types].includes("text/plain")) { ev.preventDefault(); ev.dataTransfer.dropEffect = "copy"; } };
    lw.ondrop = (ev) => {
      const d = ev.dataTransfer.getData("text/plain");
      if (!d.startsWith("sc-baustein:")) return;
      ev.preventDefault();
      const r = lw.getBoundingClientRect(), feld = r.width / 48;
      neuerBaustein(d.slice(12), (ev.clientX - r.left) / feld, (ev.clientY - r.top) / feld);
    };
    if (VS.rand) {                                 // sicherer Rand (Overscan): außen je 1 Feld ≈ 2–4 %
      const rd = document.createElement("div");
      rd.className = "lw-rand";
      lw.appendChild(rd);
    }
    ebenenZeichnen();
    warnZeigen();
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
      const g = gewaehlte();
      if (ev.shiftKey) for (const x of g) { x.w = klemm(x.w + d[0], 1, 48 - x.x); x.h = klemm(x.h + d[1], 1, 27 - x.y); }
      else {                                        // die Gruppe bleibt als Ganzes auf der Fläche
        const dx = klemm(d[0], -Math.min(...g.map((x) => x.x)), 48 - Math.max(...g.map((x) => x.x + x.w)));
        const dy = klemm(d[1], -Math.min(...g.map((x) => x.y)), 27 - Math.max(...g.map((x) => x.y + x.h)));
        for (const x of g) { x.x += dx; x.y += dy; }
      }
      leinwandZeichnen(); eigenschaftenZeichnen(); $("#leinwand").focus(); vorschauSenden(lay());
      hilfslinien($("#leinwand"), e, lay().elemente);
      clearTimeout(VS.linienWeg); VS.linienWeg = setTimeout(() => { const w = $("#leinwand"); if (w) hilfslinien(w, null); }, 1200);
    };
    function setzen(b, e) {
      const m = 100 / 48, n = 100 / 27;
      Object.assign(b.style, { left: e.x * m + "%", top: e.y * n + "%", width: e.w * m + "%", height: e.h * n + "%" });
    }
    // Klick auf die Leinwand: oberster Baustein an der Stelle; erneuter Klick auf dieselbe Stelle wählt den darunter
    function klicken(ev, b) {
      if (ev.shiftKey || ev.ctrlKey || ev.metaKey) {             // seit 0.58: Baustein zur Auswahl dazu / heraus
        ev.preventDefault();
        const id = b.dataset.id;
        if (AUSWAHL.has(id)) { AUSWAHL.delete(id); if (GEWAEHLT === id) GEWAEHLT = [...AUSWAHL].pop() || null; }
        else { AUSWAHL.add(id); GEWAEHLT = id; }
        leinwandZeichnen(); eigenschaftenZeichnen(); $("#leinwand").focus();
        return;
      }
      const stapel = document.elementsFromPoint(ev.clientX, ev.clientY).filter((x) => x.classList.contains("lw-baustein"));
      const nah = letzterKlick && Math.abs(letzterKlick[0] - ev.clientX) < 5 && Math.abs(letzterKlick[1] - ev.clientY) < 5;
      const vorher = stapel.findIndex((x) => x.dataset.id === GEWAEHLT);
      const ziel = nah && vorher >= 0 && stapel.length > 1 ? stapel[(vorher + 1) % stapel.length] : stapel[0] || b;
      letzterKlick = [ev.clientX, ev.clientY];
      ziehen(ev, lay().elemente.find((x) => x.id === ziel.dataset.id), ziel, false);
    }
    function ziehen(ev, e, b, groesse) {
      ev.preventDefault();
      const warSchonGewaehlt = AUSWAHL.has(e.id);
      if (!warSchonGewaehlt) AUSWAHL = new Set([e.id]);
      if (GEWAEHLT !== e.id || !warSchonGewaehlt) { GEWAEHLT = e.id; leinwandZeichnen(); eigenschaftenZeichnen(); b = $("#leinwand").querySelector(`[data-id="${e.id}"]`); }
      const rahmen = $("#lwAuswahl");
      const feld = 40 * massstab(), sx = ev.clientX, sy = ev.clientY, start = { ...e };
      const gruppe = groesse ? [] : gewaehlte().filter((x) => x.id !== e.id).map((x) => [x, { ...x }, $("#leinwand").querySelector(`[data-id="${x.id}"]`), $("#leinwand").querySelector(`[data-mit="${x.id}"]`)]);
      const alle = [start, ...gruppe.map((g) => g[1])];
      const grenze = { x0: -Math.min(...alle.map((x) => x.x)), x1: 48 - Math.max(...alle.map((x) => x.x + x.w)),
                       y0: -Math.min(...alle.map((x) => x.y)), y1: 27 - Math.max(...alle.map((x) => x.y + x.h)) };
      let bewegt = false;
      const fang = ev.target.isConnected ? ev.target : rahmen;
      fang.setPointerCapture(ev.pointerId);
      fang.onpointermove = (mv) => {
        const dx = Math.round((mv.clientX - sx) / feld), dy = Math.round((mv.clientY - sy) / feld);
        if (!bewegt && (dx || dy)) { merken(); bewegt = true; }
        if (groesse) { e.w = klemm(start.w + dx, 1, 48 - e.x); e.h = klemm(start.h + dy, 1, 27 - e.y); }
        else {
          const gx = klemm(dx, grenze.x0, grenze.x1), gy = klemm(dy, grenze.y0, grenze.y1);
          e.x = start.x + gx; e.y = start.y + gy;
          for (const [x, s0, xb, xm] of gruppe) { x.x = s0.x + gx; x.y = s0.y + gy; if (xb) setzen(xb, x); if (xm) setzen(xm, x); }
        }
        setzen(b, e); if (rahmen) setzen(rahmen, e);
        if (bewegt) hilfslinien(lw, e, lay().elemente);
      };
      fang.onpointerup = () => {
        fang.onpointermove = null; fang.onpointerup = null; hilfslinien(lw, null);
        if (bewegt) { $("#lSpeichern").textContent = L.speichern + " *"; eigenschaftenZeichnen(); vorschauSenden(lay()); warnZeigen(); }
        else if (warSchonGewaehlt && AUSWAHL.size > 1 && !groesse) { AUSWAHL = new Set([e.id]); leinwandZeichnen(); eigenschaftenZeichnen(); }   // Klick ohne Ziehen: nur dieser
        $("#leinwand").focus();
      };
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
      const z = el(`<div class="ebene ${AUSWAHL.has(e.id) ? "gewaehlt" : ""} ${e.sichtbar ? "" : "aus"}">
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
        if (ev.shiftKey || ev.ctrlKey || ev.metaKey) { if (AUSWAHL.has(e.id) && AUSWAHL.size > 1) { AUSWAHL.delete(e.id); if (GEWAEHLT === e.id) GEWAEHLT = [...AUSWAHL].pop(); } else { AUSWAHL.add(e.id); GEWAEHLT = e.id; } }
        else if (!a) { GEWAEHLT = e.id; AUSWAHL = new Set([e.id]); }
        else GEWAEHLT = e.id;
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
      const z = el(`<div class="eintrag zeile ${e.id === GEWAEHLT ? "gewaehlt" : ""}"><b class="flex1">${esc(L.typ[e.typ] || e.typ)}</b>
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
  const seiteZeigen = (hatWahl) => {         // seit 0.59: Reiter „Baustein“ (gewählter Baustein) oder „Layout“ (nichts gewählt)
    const le = $("#layoutEig"); if (!le) return;
    $("#eigenschaften").hidden = !hatWahl; le.hidden = hatWahl;
    inhalt.querySelectorAll("[data-seite]").forEach((k) => {
      const an = (k.dataset.seite === "baustein") === hatWahl;
      k.setAttribute("aria-selected", String(an)); k.classList.toggle("an", an);
      if (k.dataset.seite === "baustein") { k.disabled = !hatWahl; k.title = hatWahl ? "" : B.bausteinErst; }
    });
  };
  const eigenschaftenZeichnen = () => {
    const ziel = $("#eigenschaften");
    const e = lay().elemente.find((x) => x.id === GEWAEHLT);
    seiteZeigen(!!e || AUSWAHL.size > 1);
    if (AUSWAHL.size > 1) {                           // seit 0.58: mehrere gewählt – ausrichten, verteilen, duplizieren, entfernen
      const n = AUSWAHL.size, sym = { links: "align-horizontal-left", hmitte: "align-horizontal-center", rechts: "align-horizontal-right",
                                      oben: "align-vertical-top", vmitte: "align-vertical-center", unten: "align-vertical-bottom" };
      ziel.innerHTML = `<h3>${esc(B.mehr(n))}</h3><p class="leise">${esc(B.mehrText)}</p>
        <div class="feld"><label>${esc(B.ausrichten)}</label><div class="zeile">${Object.keys(sym).map((k) =>
          `<button type="button" class="knopf klein" data-ri="${k}" title="${esc(B.ri[k])}" aria-label="${esc(B.ri[k])}"><i class="mdi mdi-${sym[k]}"></i></button>`).join("")}</div></div>
        <div class="feld"><label>${esc(B.verteilen)}</label><div class="zeile">${["x", "y"].map((k) =>
          `<button type="button" class="knopf klein" data-vt="${k}" ${n < 3 ? "disabled" : ""}><i class="mdi mdi-distribute-${k === "x" ? "horizontal" : "vertical"}-center"></i> ${esc(B.vt[k])}</button>`).join("")}</div></div>
        <div class="zeile"><button type="button" class="knopf" data-m="dup" title="Strg+D"><i class="mdi mdi-content-duplicate"></i> ${esc(B.duplizieren)}</button>
          <button type="button" class="knopf gefahr" data-m="weg" title="Entf"><i class="mdi mdi-delete"></i> ${esc(B.entfernen)}</button></div>`;
      ziel.querySelectorAll("[data-ri]").forEach((k) => { k.onclick = () => ausrichten(k.dataset.ri); });
      ziel.querySelectorAll("[data-vt]").forEach((k) => { k.onclick = () => verteilen(k.dataset.vt); });
      ziel.querySelector("[data-m=dup]").onclick = duplizieren;
      ziel.querySelector("[data-m=weg]").onclick = entfernen;
      return;
    }
    if (!e) { ziel.innerHTML = `<p class="leise">${esc(L.keinerGewaehlt)}</p>`; return; }
    const o = e.optionen, b = e.bedingung || {};
    const hi = (k) => (B.h[k] ? ` <button type="button" class="ihilfe" data-hilfe="${k}" aria-label="${esc(B.hilfe)}" aria-expanded="false" title="${esc(B.hilfe)}">ⓘ</button>` : "");
    const feld = (k) => {
      const w = o[k], lab = esc(e.typ === "galerie" && k === "sekunden" ? L.galSekunden : L.opt[k] || k) + hi(k);
      if (k === "ordner") return `<div class="zeile"><label>${lab}</label><select name="o_ordner">${galerieOptionen(w, L.galKeinOrdner)}</select></div>
        <p class="leise"><a href="#galerie">${esc(L.galOrdnerAnlegen)}</a></p>`;
      if (k === "liste") return `<h3>${lab}</h3><div id="raumListe">${(w || []).map((r, i) => `<div class="zeile" data-i="${i}">
          <input type="text" name="rn" value="${esc(r.name)}" placeholder="Name" class="b120"><input type="text" name="re" list="ents" value="${esc(r.entity)}" placeholder="sensor.…">
          <button class="knopf gefahr" name="rw">✕</button></div>`).join("")}</div><button class="knopf" id="raumPlus">${esc(L.raumNeu)}</button>`;
      if (e.typ === "kalender" && ["symbole", "ohne_symbol", "wann"].includes(k) && o.ansicht !== "symbole") return "";
      if (e.typ === "liste" && ["pfad", "spalte_text", "spalte_info", "spalte_wert"].includes(k) && !o.quelle) return "";
      if (k === "zeilen") {             // seit 0.53: Zeilen des Bausteins „Liste“
        const Z = L.zl;
        return `<h3>${lab}</h3>${o.quelle ? `<p class="leise">${esc(Z.quelleStatt)}</p>` : ""}<div id="zlListe">${(w || []).map((r, i) => `<div class="zeile listenzeile" data-i="${i}">
          <input type="text" name="zText" value="${esc(r.text)}" placeholder="${esc(Z.text)}" aria-label="${esc(Z.text)}" maxlength="60">
          <input type="text" name="zInfo" value="${esc(r.info)}" placeholder="${esc(Z.info)}" aria-label="${esc(Z.info)}" maxlength="120">
          <input type="text" name="zWert" value="${esc(r.wert)}" placeholder="${esc(Z.wert)}" aria-label="${esc(Z.wert)}" maxlength="24" class="b70">
          <input type="text" name="zIcon" list="symVorschlag" value="${esc(r.icon)}" placeholder="mdi-…" aria-label="${esc(L.opt.icon)}" spellcheck="false" class="b120">
          <label><input type="checkbox" name="zHervor" ${r.hervor ? "checked" : ""}> ${esc(Z.hervor)}</label>
          <button class="knopf klein" name="zHoch" title="${esc(Z.hoch)}" ${i ? "" : "disabled"}><i class="mdi mdi-arrow-up"></i></button>
          <button class="knopf gefahr" name="zWeg">✕</button></div>`).join("")}</div>
          <datalist id="symVorschlag">${SYM_VORSCHLAG.map((s) => `<option value="${s}">`).join("")}</datalist>
          <div class="zeile"><button class="knopf" id="zlPlus" ${(w || []).length >= 20 ? "disabled" : ""}>${esc(Z.neu)}</button></div>`;
      }
      if (k === "symbole") {
        const S = SYM_TEXTE[E.sprache] || SYM_TEXTE.de;
        return `<h3>${lab}</h3><p class="leise">${esc(S.hilfe)}</p><datalist id="symVorschlag">${SYM_VORSCHLAG.map((s) => `<option value="${s}">`).join("")}</datalist>
          <div id="symListe">${(w || []).map((r, i) => `<div class="zeile symregel" data-i="${i}">
          <input type="text" name="sText" value="${esc(r.text)}" placeholder="${esc(S.text)}" aria-label="${esc(S.text)}">
          <input type="text" name="sIcon" list="symVorschlag" value="${esc(r.icon)}" placeholder="mdi-…" aria-label="${esc(S.icon)}" spellcheck="false">
          <span class="icon mdi ${esc(r.icon)}"></span>
          <input type="color" name="sFarbe" value="${esc(r.farbe || "#ffffff")}" aria-label="${esc(S.farbe)}">
          <button class="knopf gefahr" name="sWeg" title="${esc(S.weg)}">✕</button></div>`).join("")}</div>
          <div class="zeile"><button class="knopf" id="symPlus">${esc(S.neu)}</button><button class="knopf" id="symVorlage">${esc(S.vorlage)}</button></div>`;
      }
      if (typeof w === "boolean") return `<div class="zeile"><label>${lab}</label>${schalter("o_" + k, w)}</div>`;
      if (k === "quelle") return `<div class="zeile"><label>${lab}</label><select name="o_quelle"><option value="">${esc(L.keineQuelle)}</option>
        ${(E.quellen || []).filter((q) => !QUELL_ARTEN[e.typ] || QUELL_ARTEN[e.typ].includes(q.art) || q.id === w)
            .map((q) => `<option value="${esc(q.id)}" ${q.id === w ? "selected" : ""}>${esc(q.name)} (${esc(q.id)})</option>`).join("")}</select></div>`;
      if (k === "url") return `<div class="zeile"><label>${lab}</label><input type="text" name="o_url" value="${esc(w ?? "")}" spellcheck="false" class="voll">
        <button class="knopf" type="button" name="urlPruefen">${esc(L.pruefen)}</button><span class="leise" id="urlErg"></span></div>`;
      if (k === "pfad") return `<div class="zeile"><label>${lab}</label><input type="text" name="o_pfad" value="${esc(w ?? "")}" spellcheck="false">
        <button class="knopf" type="button" name="pfadWahl">${esc(L.waehlen)}</button></div><div class="pfadBaum"></div>`;
      if (WAHL[k]) return `<div class="zeile"><label>${lab}</label><select name="o_${k}">${WAHL[k].map((x) => `<option value="${x}" ${x === w ? "selected" : ""}>${esc(L.wahl[x] || x)}</option>`).join("")}</select></div>`;
      if (k === "datei") return `<div class="zeile"><label>${lab}</label><input type="file" name="o_pdfDatei" accept="application/pdf">
        <span class="leise" name="pdfStand">${esc(w ? "✓ " + w : "")}</span></div>`;
      if (k === "ziel") return `<div class="zeile"><label>${lab}</label><input type="datetime-local" name="o_ziel" value="${esc(w || "")}"></div>`;
      if (k === "bild") return `<div class="zeile"><label>${lab}</label><input type="file" name="o_bildDatei" accept="image/png,image/jpeg">
        <span class="leise">${esc(w || "")}</span></div>`;
      if (k === "farbe") return `<div class="zeile"><label>${lab}</label><input type="color" name="o_${k}" value="${esc(w || "#f0f0f0")}"></div>`;
      if (typeof w === "number") return `<div class="zeile"><label>${lab}</label><input type="number" step="any" name="o_${k}" value="${w}"></div>`;
      const liste = k === "entity" ? ' list="ents"' : "";
      return `<div class="zeile"><label>${lab}</label><input type="text" name="o_${k}" value="${esc(w ?? "")}"${liste}>${k === "icon" || k === "ohne_symbol" ? `<span class="icon mdi ${esc(w || "")}"></span>` : ""}</div>`;
    };
    const wannAn = !!(e.ab || e.bis || b.entity || b.quelle);
    if (!B.reiter[EIG_REITER]) EIG_REITER = "inhalt";
    const feldReiter = (r, html) => `<div class="reiter-feld" role="tabpanel" data-feld="${r}" ${r === EIG_REITER ? "" : "hidden"}>${html}</div>`;
    ziel.innerHTML = `<div data-warn></div><h2>${esc(L.typ[e.typ] || e.typ)}</h2>${L.optHilfe[e.typ] ? `<p class="leise">${esc(L.optHilfe[e.typ])}</p>` : ""}
      <div class="reiter" role="tablist">${Object.keys(B.reiter).map((r) => `<button type="button" role="tab" class="reiter-knopf ${r === EIG_REITER ? "an" : ""}" data-reiter="${r}"
        aria-selected="${r === EIG_REITER}">${esc(B.reiter[r])}${r === "wann" && wannAn ? ` <span class="punkt" title="${esc(B.wannAktiv)}">●</span>` : ""}</button>`).join("")}</div>
      ${feldReiter("inhalt", `${Object.keys(o).filter((k) => !AUSSEHEN_OPT.includes(k)).map(feld).join("")}
        <div class="zeile"><label>${esc(L.sichtbar)}${hi("sichtbar")}</label>${schalter("sichtbar", e.sichtbar)}</div>`)}
      ${feldReiter("aussehen", `${Object.keys(o).filter((k) => AUSSEHEN_OPT.includes(k)).map(feld).join("")}
      <div class="zeile"><label>${esc(L.karte)}${hi("karte")}</label>${schalter("karte", e.karte)}</div>
      <div class="zeile"><label>${esc(L.schriftPos)}${hi("ausrichtung")}</label><input type="hidden" name="ausrichtung" value="${esc(e.ausrichtung || "links")}">
        <div class="neuner">${["oben-links", "oben-mitte", "oben-rechts", "links", "mitte", "rechts", "unten-links", "unten-mitte", "unten-rechts"].map((k) =>
          `<button type="button" class="${k === (e.ausrichtung || "links") ? "an" : ""}" data-pos="${k}" title="${esc(L.ausrichtungArt[k])}" aria-label="${esc(L.ausrichtungArt[k])}"></button>`).join("")}</div></div>
      <div class="zeile"><label>${esc(L.schriftEl)}${hi("schrift")}</label><select name="schrift"><option value="">${esc(L.wieLayout)}</option>
        ${SCHRIFTEN.map((k) => `<option value="${esc(k)}" data-schrift="${esc(k)}" ${k === e.schrift ? "selected" : ""}>${esc(k)}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(L.textfarbe)}${hi("textfarbe")}</label><input type="color" name="textfarbe" value="${esc(e.textfarbe || "#ffffff")}">
        <label><input type="checkbox" name="textfarbeStd" ${e.textfarbe ? "" : "checked"}> ${esc(L.textfarbeStd)}</label></div>
      <div class="zeile"><label>${esc(L.gewicht)}${hi("gewicht")}</label><select name="gewicht">${Object.keys(L.gewichtArt).map((k) => `<option value="${k}" ${k === (e.gewicht || "") ? "selected" : ""}>${esc(L.gewichtArt[k])}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(L.position)}${hi("position")}</label></div>
      <div class="zeile pos">${["x", "y", "w", "h"].map((k) => `<label>${{ x: "←", y: "↓", w: "↔", h: "↕" }[k]}<input type="number" name="p_${k}" value="${e[k]}" aria-label="${k}"></label>`).join("")}</div>`)}
      ${feldReiter("wann", `<h3>${esc(L.zeitraum)}</h3><p class="leise">${esc(L.zeitraumText)}</p>
        ${["ab", "bis"].map((k) => `<div class="zeile"><label>${esc(L[k])}</label><input type="date" name="z_${k}_tag" value="${esc((e[k] || "").slice(0, 10))}">
          <input type="time" name="z_${k}_zeit" value="${esc((e[k] || "").slice(11, 16))}"></div>`).join("")}
        <h3>${esc(L.bedingung)}${hi("bedingung")}</h3>
        <div class="zeile"><label>${esc(L.bedQuelle)}</label><select name="b_quelle"><option value="">${esc(L.bedHA)}</option>
          ${(E.quellen || []).map((q) => `<option value="${esc(q.id)}" ${q.id === b.quelle ? "selected" : ""}>${esc(q.name)} (${esc(q.id)})</option>`).join("")}</select></div>
        <div class="zeile" data-bed="ha" ${b.quelle ? "hidden" : ""}><input type="text" name="b_entity" list="ents" value="${esc(b.entity || "")}" placeholder="${esc(L.bedingungEntity)}"></div>
        <div class="zeile" data-bed="api" ${b.quelle ? "" : "hidden"}><input type="text" name="b_pfad" value="${esc(b.pfad || "")}" placeholder="${esc(L.bedPfad)}" spellcheck="false">
          <button class="knopf" type="button" name="bPfadWahl">${esc(L.waehlen)}</button></div><div class="bPfadBaum"></div>
        <div class="zeile"><select name="b_op">${Object.keys(L.op).map((k) => `<option value="${esc(k)}" ${k === (b.op || "=") ? "selected" : ""}>${esc(L.op[k])}</option>`).join("")}</select>
          <input type="text" name="b_wert" value="${esc(b.wert || "")}" class="b140"></div>`)}
      <div class="zeile eig-fuss"><button class="knopf" name="vorne">${esc(L.vorne)}</button><button class="knopf" name="hinten">${esc(L.hinten)}</button>
        <button class="knopf" name="dup" title="Strg+D"><i class="mdi mdi-content-duplicate"></i> ${esc(B.duplizieren)}</button>
        <button class="knopf gefahr" name="weg">${esc(L.entfernen)}</button></div>`;
    ziel.querySelectorAll("[data-reiter]").forEach((k) => {
      k.onclick = () => {
        EIG_REITER = k.dataset.reiter;
        try { localStorage.setItem("signagecast-eig-reiter", EIG_REITER); } catch (_) { /* egal */ }
        ziel.querySelectorAll("[data-reiter]").forEach((x) => { const an = x === k; x.classList.toggle("an", an); x.setAttribute("aria-selected", String(an)); });
        ziel.querySelectorAll("[data-feld]").forEach((f) => { f.hidden = f.dataset.feld !== EIG_REITER; });
      };
    });
    ziel.querySelectorAll(".ihilfe").forEach((k) => {
      k.onclick = (ev) => {
        ev.preventDefault();
        const z = k.closest(".zeile, h3"), da = z.nextElementSibling;
        if (da && da.classList.contains("hilfetext")) { da.remove(); k.setAttribute("aria-expanded", "false"); return; }
        const t = document.createElement("p"); t.className = "leise hilfetext"; t.textContent = B.h[k.dataset.hilfe];
        z.after(t); k.setAttribute("aria-expanded", "true");
      };
    });
    schriftVorschau(ziel);
    const aendern = () => {
      merken();
      for (const k of Object.keys(o)) {
        if (k === "liste" || k === "bild" || k === "datei" || k === "symbole" || k === "zeilen") continue;
        const inp = ziel.querySelector(`[name=o_${k}]`); if (!inp) continue;
        o[k] = inp.type === "checkbox" ? inp.checked : inp.type === "number" ? Number(inp.value) : inp.value;
        if (k === "pfad") o[k] = o[k].trim();
      }
      if (o.symbole && ziel.querySelector("#symListe")) o.symbole = [...ziel.querySelectorAll("#symListe .zeile")].map((z) => ({ text: z.querySelector("[name=sText]").value,
        icon: z.querySelector("[name=sIcon]").value.trim(), farbe: z.querySelector("[name=sFarbe]").value }));
      ziel.querySelectorAll("#symListe .zeile").forEach((z, i) => { const s = z.querySelector(".icon"), r = o.symbole[i];
        s.className = "icon mdi " + r.icon; s.style.color = r.farbe; });
      if (o.zeilen && ziel.querySelector("#zlListe")) o.zeilen = [...ziel.querySelectorAll("#zlListe .zeile")].map((z) => ({ text: z.querySelector("[name=zText]").value,
        info: z.querySelector("[name=zInfo]").value, wert: z.querySelector("[name=zWert]").value, icon: z.querySelector("[name=zIcon]").value.trim(),
        hervor: z.querySelector("[name=zHervor]").checked }));
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
      for (const k of ["ab", "bis"]) {                  // Zeitraum (seit 0.21): Datum, optional mit Uhrzeit
        const tag = ziel.querySelector(`[name=z_${k}_tag]`).value, zeit = ziel.querySelector(`[name=z_${k}_zeit]`).value;
        e[k] = tag ? tag + (zeit ? "T" + zeit : "") : "";
      }
      ziel.querySelector("[data-bed=ha]").hidden = !!bq; ziel.querySelector("[data-bed=api]").hidden = !bq;
      $("#lSpeichern").textContent = L.speichern + " *";
      if (handy()) listeZeichnen(); else leinwandZeichnen();
      for (const k of ["icon", "ohne_symbol"]) { const ic = ziel.querySelector(`[name=o_${k}] + .icon`); if (ic) ic.className = "icon mdi " + (o[k] || ""); }
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
    // PDF hochladen (seit 0.21): in Stücken wie eigene Medien; der Dienst wandelt die Seiten in Bilder um
    const pd = ziel.querySelector("[name=o_pdfDatei]");
    if (pd) pd.onchange = () => aktion(null, async () => {
      const f = pd.files[0]; if (!f) return;
      const STUECK = 3 * 1024 * 1024, teile = Math.max(1, Math.ceil(f.size / STUECK));
      const kennung = Math.random().toString(36).slice(2, 12).replace(/[^a-z0-9]/g, "a").padEnd(10, "x");
      ziel.querySelector("[name=pdfStand]").textContent = L.laedt;
      let d = null;
      for (let nr = 0; nr < teile; nr++) {
        const roh = new Uint8Array(await f.slice(nr * STUECK, (nr + 1) * STUECK).arrayBuffer());
        let bin = ""; for (let i = 0; i < roh.length; i += 0x8000) bin += String.fromCharCode(...roh.subarray(i, i + 0x8000));
        d = await senden("/api/medien/teil", { kennung, nr, daten: btoa(bin), fertig: nr === teile - 1, zweck: "pdf", gesamt: f.size });
      }
      merken(); o.datei = d.pdf; $("#lSpeichern").textContent = L.speichern + " *"; eigenschaftenZeichnen();
      ziel.querySelector("[name=pdfStand]").textContent = "✓ " + L.seiten(d.seiten);
      if (handy()) listeZeichnen(); else leinwandZeichnen();
    });
    // Pfad aus der letzten Antwort der Datenquelle wählen (Baum)
    const up = ziel.querySelector("[name=urlPruefen]");
    if (up) up.onclick = (ev) => aktion(ev.target, async () => {
      const r = await senden("/api/webseite/pruefen", { url: ziel.querySelector("[name=o_url]").value });
      ziel.querySelector("#urlErg").innerHTML = r.einbettbar === true ? `<span class="gut">${esc(L.einbettbarJa)}</span>`
        : r.einbettbar === false ? `<span class="schlecht">${esc(L.einbettbarNein)}: ${esc(r.grund)}</span> ${esc(L.tippFoto)}` : `${esc(L.einbettbarUnklar)}: ${esc(r.grund)}`;
    }, null);
    const pw = ziel.querySelector("[name=pfadWahl]");
    if (pw) pw.onclick = (ev) => aktion(ev.target, () => pfadWaehlen(ziel.querySelector(".pfadBaum"), ziel.querySelector("[name=o_quelle]").value,
      (p) => { ziel.querySelector("[name=o_pfad]").value = p; aendern(); }), null);
    ziel.querySelector("[name=bPfadWahl]").onclick = (ev) => aktion(ev.target, () => pfadWaehlen(ziel.querySelector(".bPfadBaum"), ziel.querySelector("[name=b_quelle]").value,
      (p) => { ziel.querySelector("[name=b_pfad]").value = p; aendern(); }), null);
    const tf = ziel.querySelector("[name=textfarbe]");
    if (tf) tf.oninput = () => { ziel.querySelector("[name=textfarbeStd]").checked = false; };
    // Kalender-Symbole (seit 0.28): Darstellung umschalten zeigt/versteckt die Symbol-Optionen; Farbe der Vorschau per JS (CSP)
    ziel.querySelectorAll("#symListe .zeile").forEach((z, i) => { z.querySelector(".icon").style.color = (o.symbole[i] || {}).farbe || ""; });
    const an = ziel.querySelector("[name=o_ansicht]");
    if (an && e.typ === "kalender") an.onchange = () => { aendern(); eigenschaftenZeichnen(); };
    const sp = ziel.querySelector("#symPlus");
    if (sp) sp.onclick = () => { aendern(); o.symbole.push({ text: "", icon: "mdi-calendar", farbe: "" }); eigenschaftenZeichnen(); };
    const sv = ziel.querySelector("#symVorlage");
    if (sv) sv.onclick = () => { aendern(); const S = SYM_TEXTE[E.sprache] || SYM_TEXTE.de;
      const da = new Set(o.symbole.map((r) => r.text.toLowerCase()));
      S.muell.forEach(([text, icon, farbe]) => { if (!da.has(text.toLowerCase())) o.symbole.push({ text, icon, farbe }); });
      o.symbole = o.symbole.slice(0, 12); eigenschaftenZeichnen(); if (handy()) listeZeichnen(); else leinwandZeichnen(); };
    ziel.querySelectorAll("[name=sWeg]").forEach((k) => { k.onclick = () => { k.closest(".zeile").remove(); aendern(); }; });
    const zp = ziel.querySelector("#zlPlus");
    if (zp) zp.onclick = () => { aendern(); o.zeilen.push({ text: "", info: "", wert: "", icon: "", hervor: false }); eigenschaftenZeichnen(); };
    ziel.querySelectorAll("[name=zWeg]").forEach((k) => { k.onclick = () => { k.closest(".zeile").remove(); aendern(); }; });
    ziel.querySelectorAll("[name=zHoch]").forEach((k) => { k.onclick = () => { const z = k.closest(".zeile"); z.previousElementSibling?.before(z); aendern(); eigenschaftenZeichnen(); }; });
    const lq = ziel.querySelector("[name=o_quelle]");
    if (lq && e.typ === "liste") lq.onchange = () => { aendern(); eigenschaftenZeichnen(); };
    const rp = ziel.querySelector("#raumPlus");
    if (rp) rp.onclick = () => { aendern(); o.liste.push({ name: "", entity: "" }); eigenschaftenZeichnen(); };
    ziel.querySelectorAll("[name=rw]").forEach((k) => { k.onclick = () => { k.closest(".zeile").remove(); aendern(); }; });
    const els = lay().elemente, i = els.indexOf(e);
    ziel.querySelector("[name=vorne]").onclick = () => { merken(); els.splice(i, 1); els.push(e); zeichnen(); };
    ziel.querySelector("[name=hinten]").onclick = () => { merken(); els.splice(i, 1); els.unshift(e); zeichnen(); };
    ziel.querySelector("[name=weg]").onclick = () => { merken(); els.splice(i, 1); GEWAEHLT = null; zeichnen(); };
    ziel.querySelector("[name=dup]").onclick = duplizieren;
    if (WARN[e.id]) ziel.querySelector("[data-warn]").innerHTML = WARN[e.id].map((t) => `<p class="warn">⚠ ${esc(t)}</p>`).join("");
  };

  // ---------- Kurzbefehle (seit 0.58), nur im Editor und nicht beim Tippen in Feldern ----------
  if (LTASTEN) document.removeEventListener("keydown", LTASTEN);
  LTASTEN = (ev) => {
    if (ANSICHT !== "editor" || !$("#lSpeichern") || !document.body.contains(inhalt) || document.querySelector(".seitenfeld, dialog[open]")) return;
    const t = ev.target, tippen = t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
    if (tippen) return;
    const strg = ev.ctrlKey || ev.metaKey, k = ev.key.toLowerCase();
    if (strg && k === "z" && !ev.shiftKey) { ev.preventDefault(); zurueck(); }
    else if (strg && (k === "y" || k === "z" && ev.shiftKey)) { ev.preventDefault(); vor(); }
    else if (strg && k === "d") { ev.preventDefault(); duplizieren(); }
    else if (strg && k === "c" && !String(window.getSelection() || "")) { if (kopieren()) ev.preventDefault(); }
    else if (strg && k === "v") { ev.preventDefault(); ablageEinfuegen(); }
    else if (strg && k === "a" && !handy()) { ev.preventDefault(); AUSWAHL = new Set(lay().elemente.map((x) => x.id)); GEWAEHLT = lay().elemente.length ? lay().elemente[lay().elemente.length - 1].id : null; neuZeichnen(); }
    else if ((ev.key === "Delete" || ev.key === "Backspace") && AUSWAHL.size) { ev.preventDefault(); entfernen(); }
    else if (ev.key === "Escape" && AUSWAHL.size) { GEWAEHLT = null; AUSWAHL.clear(); neuZeichnen(); }
  };
  document.addEventListener("keydown", LTASTEN);

  if (ANSICHT === "editor" && LS[LI]) zeichnen(); else { ANSICHT = "liste"; listeAlle(); }
}

async function stilBilderZeigen(stil) {
  const ziel = document.getElementById("stilBilder");
  if (!ziel) return;
  const stile = stil === "gemischt" ? ["natur", "stadt", "himmel", "berge", "meer"] : [stil];   // gemischt = nur Landschaften
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
  return (e.ab || e.bis ? "⏱ " : "") + vorschauInhalt(e, L);        // ⏱ = nur im Zeitraum (seit 0.21)
}
function vorschauInhalt(e, L) {
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
    case "pdf": return "📄 " + (o.datei ? "PDF" : L.typ.pdf);
    case "liste": return "☰ " + (o.titel || (o.zeilen || []).map((r) => r.text).filter(Boolean).slice(0, 3).join(", ") || o.quelle || L.typ.liste);
    case "galerie": return "🖼 " + ((((E.galerie && E.galerie.ordner) || []).find((x) => x.id === o.ordner) || {}).name || L.typ.galerie);
    default: return L.typ[e.typ] || e.typ;
  }
}
