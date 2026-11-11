// SignageCast – Verwaltung als Cockpit-Erweiterung. Spricht nur mit dem Datendienst im Container (127.0.0.1:8080).
// Im Docker-/Podman-Betrieb liefert app/verwaltung.py dieselbe Seite mit einem Cockpit-Ersatz aus (CONTAINER = true).
// Ohne Fremd-Bibliotheken; Texte Deutsch/Englisch (Sprache aus den Einstellungen).
"use strict";

const KOPF = { "X-SignageCast": "1", "Content-Type": "application/json" };
// Wer angemeldet ist – nur für das Änderungsprotokoll (seit 0.38); im Container gibt es nur einen Zugang
try { if (cockpit.user) cockpit.user().then((u) => { if (u && /^[\w.@ -]{1,40}$/.test(u.name || "")) KOPF["X-SignageCast-Benutzer"] = u.name; }).catch(() => {}); } catch (_) { /* egal */ }
const dienst = cockpit.http(8080, { address: "127.0.0.1" });
const dienstBinaer = cockpit.http(8080, { address: "127.0.0.1", binary: true });
const CONTAINER = !!cockpit.signagecastContainer;
const hostSync = () => CONTAINER ? T.hostSync.replace(" (Proxmox)", "") : T.hostSync;   // im Container ist der Host selten Proxmox
const IMAGE = "ghcr.io/thefrozn/signagecast:latest";

// ---------- Texte ----------
const TEXTE = {
  de: {
    reiter: { uebersicht: "Übersicht", fernseher: "Fernseher", player: "Player", layout: "Layout", quellen: "Datenquellen", streams: "Streams", kategorien: "Kategorien", radio: "Radio", einspieler: "Einspieler", anzeige: "Anzeige",
              video: "Rotation & Qualität", suche: "Suche", verbindung: "Verbindung", medien: "Medien", updates: "Updates", sicherung: "Sicherung",
              allgemein: "Allgemein", ha: "Home Assistant", benachrichtigung: "Benachrichtigungen", zugang: "Zugang", leistung: "Leistung", pult: "Durchsagen", protokoll: "Protokoll", ki: "KI-Assistenten", fern: "Fernstandorte" },
    pu: { titel: "Durchsage-Pult", text: "Eine eigene Seite, z. B. für die Rezeption: nur Meldungen und Durchsagen an ausgewählte Fernseher – keine Einstellungen. Adresse:",
          stimme: "Stimme", stimmeText: "Die Sprache wird offline auf diesem Server erzeugt (Piper). Stimmen werden einmalig geladen (ca. 90 MB mit Programm).",
          geladen: "geladen", nichtGeladen: "nicht geladen", laden: "Stimme laden", laedtGerade: "wird geladen …", vorlesen: "Durchsagen vorlesen",
          gong: "Gong vor der Durchsage", dauer: "Standard-Anzeigedauer (s)", zugaenge: "Zugänge", zugangText: "Jeder Zugang hat ein eigenes Passwort und darf nur die angehakten Fernseher erreichen (keiner angehakt = alle).",
          name: "Name", pwNeu: "neues Passwort", pwGesetzt: "Passwort gesetzt", pwFehlt: "noch kein Passwort", zugangNeu: "Zugang hinzufügen",
          entfernen: "Entfernen", vorlagen: "Vorlagen", vorlagenText: "Eine Vorlage je Zeile; „…“ markiert die Lücke für den Namen.",
          art: { weiblich: "weiblich", "männlich": "männlich" }, probe: "Probedurchsage", probeOk: "Probedurchsage gesendet", tonHinweis: "Fernseher mit Pult-Zugang nehmen echten Ton auf (für das Vorlesen).",
          darfAlarm: "darf das Notfall-Vollbild auslösen",
          recht: { meldung: "darf Laufschrift-Meldungen senden", layout: "darf das Layout vorübergehend umschalten", schalten: "darf Fernseher ein- und ausschalten (HA)" } },
    al: { titel: "Notfall-Vollbild", text: "Zeigt einen Text rot über den ganzen Bildschirm – über jedem Layout, auch nachts („schwarz“); ausgeschaltete Fernseher werden über Home Assistant eingeschaltet (Fernseher → „Über HA schalten“). Bleibt, bis jemand es beendet (Verwaltung, Pult oder Webhook).",
          vorlagen: "Vorlagen (eine je Zeile)", ton: "Warnton alle 10 Sekunden (hörbar auf Fernsehern mit Ton oder Pult-Vorlesen)", an: "Jetzt auslösen", aus: "Beenden", alle: "alle Fernseher",
          wirklich: "Notfall-Vollbild wirklich jetzt auf den Fernsehern zeigen?", laeuft: (z, v) => `Notfall-Vollbild läuft seit ${z} Uhr (${v})`,
          webhook: "Per Webhook (Schlüssel aus „Meldung per Webhook“):", beendet: "Notfall-Vollbild beendet", ausgeloest: "Notfall-Vollbild ausgelöst" },
    lt: { server: "Server: Erzeugung und Kodierung", serverText: "Misst 10 Sekunden lang, wie flüssig SignageCast die Bilder erzeugt und kodiert – am besten, während der ruckelnde Fernseher läuft.",
          start: "Test starten (10 s)", laeuftTest: "Test läuft …", system: "System", cpu: "CPU", kerne: "Kerne", ram: "Speicher frei", gpu: "Grafikeinheit",
          seite: "Bilder/s TV-Seite", kodierung: "Bilder/s Kodierung", tempo: "Tempo", verloren: "verworfen/doppelt", cpuKette: "CPU (Kerne)", aus: "läuft nicht",
          ziel: "Ziel: 25 Bilder/s, Tempo 1,0×", tonNeu: "Ton und Stream neu starten", tonNeuText: "Hilft, wenn die Aufnahme viele Bilder doppelt (Ruckeln trotz flüssiger Seite). Die Fernseher sind dabei kurz schwarz.", tonNeuOk: "Ton und Stream werden neu gestartet", geraet: "Auf dem Abspielgerät testen", geraetText: "Übertragung und Wiedergabe lassen sich nur auf dem Gerät messen, auf dem es ruckelt. Öffne diese Adresse dort im Browser (gleiches Netz):",
          letzteGeraete: "Ergebnisse von Geräten", keine: "noch keine", empfehlungen: "Empfehlungen",
          empf: {
            keine_kette: () => "Gerade läuft kein Fernseher. Erst den Stream auf dem Fernseher (oder im Browser) öffnen, dann testen.",
            seite_langsam: (p) => `„${p.tv}“: Die TV-Seite schafft nur ${p.fps} Bilder/s (Ziel 25). Das Layout ist zu aufwendig für die CPU – Webseiten-, Kamera- und Diagramm-Bausteine kosten am meisten. Layout entschlacken, weniger Fernseher gleichzeitig oder dem Container mehr Kerne geben.`,
            kodierung_langsam: (p) => `„${p.tv}“: Die Kodierung läuft nur mit ${p.tempo}× Echtzeit. ${p.aufloesung === 2160 ? "Ausgabe auf Full HD stellen oder " : ""}Bitrate senken; bei mehreren Fernsehern ist die Grafikeinheit ausgelastet.`,
            bilder_verloren: (p) => `„${p.tv}“: ${p.n} Bilder verworfen oder doppelt – die Erzeugung hält nicht Schritt. Meist CPU-Last (siehe oben).`,
            ton_doppelt: (p) => `„${p.tv}“: ${p.n} Bilder doppelt, obwohl die Seite flüssig läuft – die Aufnahme bekommt zu wenig Rechenzeit (z. B. andere Gäste auf demselben Host) oder die Grafikeinheit ist am Limit. Abhilfe: dem Container Vorrang geben (Proxmox: cpuunits), Ausgabe auf Full HD; einmalig hilft „Ton und Stream neu starten“.`,
            cpu_hoch: (p) => `CPU zu ${p.cpu} % ausgelastet (${p.kerne} Kerne, ${p.ketten} Fernseher). Je Fernseher etwa 1 Kern einplanen – in Proxmox mehr Kerne zuweisen oder weniger Fernseher gleichzeitig.`,
            cpu_knapp: (p) => `CPU zu ${p.cpu} % ausgelastet (${p.kerne} Kerne, ${p.ketten} Fernseher) – wenig Reserve. Ein weiterer Fernseher oder ein aufwendiges Layout kann zum Ruckeln führen.`,
            ram_knapp: (p) => `Nur noch ${p.frei} MB Speicher frei. Je Fernseher etwa 0,9 GB einplanen – dem Container mehr Speicher geben.`,
            gpu_hoch: (p) => `Die Grafikeinheit läuft mit ${p.gpu} % ihres Höchsttakts – nahe an der Grenze. Bitrate oder Auflösung senken.`,
            software: () => "Keine Grafikeinheit – Video wird per CPU kodiert (nur Full HD, H.264). Für 4K oder mehrere Fernseher die Intel-/AMD-Grafik an den Container durchreichen.",
            mediamtx_langsam: (p) => `MediaMTX hat in den letzten 10 Minuten ${p.n}-mal Bilder weggeworfen („reader is too slow“) – sichtbar als Sprung um etwa eine Sekunde. Abhilfe: Update auf SignageCast 0.19.2 (größere Warteschlange) bzw. Ausgabe auf Full HD oder niedrigere Bitrate.`,
            server_ok: () => "Server in Ordnung: Erzeugung und Kodierung schaffen Echtzeit. Ruckelt es trotzdem, liegt es an Übertragung oder Abspielgerät – Test auf dem Gerät (unten).",
          } },
    as: { titel: "Willkommen bei SignageCast", schritt: (n) => `Schritt ${n} von 5`, sprache: "Sprache der Verwaltung und der Fernseher",
          ort: "Wo steht der Fernseher? Der Ort bestimmt Wetter, Sonnenzeiten und Warnungen.", ha: "Home Assistant verbinden (optional) – für Werte aus dem Haus. Die Anleitung steht danach unter Einstellungen → Home Assistant.",
          weg: "Wie kommt das Bild auf den Fernseher?", wege: {
            browser: ["Browser des Fernsehers", "Smart-TV, Fire TV, Android-TV-Box oder ein Tablet: eine Adresse als Startseite."],
            pi: ["Raspberry Pi", "Für Fernseher ohne brauchbaren Browser: fertiges Image auf eine SD-Karte schreiben, per HDMI anschließen."],
            pc: ["PC", "Mini-PC oder alter Laptop: fertiges Image auf einen USB-Stick, startet direkt in die Anzeige."] },
          fertig: "Fertig! Öffne diese Adresse im Browser des Fernsehers und setze sie als Startseite:", fertigText: "Alles Weitere – Layout, Streams, Radio, mehr Fernseher – findest du in den Bereichen oben.",
          fertigPlayer: "Fertig! Lege jetzt den Player an: Image erstellen, schreiben, einstecken – er meldet sich danach von selbst unter „Player“.",
          zumPlayer: "Player anlegen", lokal: "„localhost“ erreicht der Fernseher nicht – nimm die IP dieses Computers im Heimnetz (Docker: SC_HOST_IP setzen).",
          mehr: "Außerdem möglich", mehrListe: { fern: "Fernstandorte – Player an anderen Orten über Tailscale oder Headscale", ki: "KI-Assistenten – Claude & Co. bauen Layouts und schreiben Laufschriften", pult: "Durchsage-Pult – eine eigene Seite nur für Meldungen, z. B. am Empfang" },
          weiter: "Weiter", zurueck: "Zurück", ueberspringen: "Überspringen", spaeter: "Später einrichten", los: "Zur Übersicht" },
    pl: { titel: "Player: Raspberry Pi, PC oder Browser", zitat: (s) => `„${s}“`, text: "Ein Raspberry Pi am Fernseher zeigt den Stream per HDMI – auch an Fernsehern ohne brauchbaren Browser. Du erstellst hier ein fertiges Image, schreibst es auf eine SD-Karte, steckst sie ein – fertig. Danach verwaltest du alle Pis hier.",
          modelle: "Pi 5, Pi 4, Pi 400: bis 4K (H.265). Pi 3 und Zero 2 W: nur Full HD mit H.264 – den Fernseher dann auf Codec „H.264“ und Auflösung „Full HD“ stellen.",
          ram: "Arbeitsspeicher: Für den Stream reicht 1 GB (Zero 2 W: 512 MB). Für den Direktmodus mindestens 2 GB, besser 4 GB – vor allem mit Videos, Kameras, Webseiten oder 4K-Ausgabe; mit Schreibschutz liegt auch alles, was der Browser speichert, im Arbeitsspeicher. Schätzwerte, auf echten Pis noch nicht gemessen.",
          bedarf: "Dazu: SD-Karte ab 8 GB (Markenkarte, A1/A2), für den Direktmodus einen Pi 4/5 mit mindestens 2 GB (besser 4 GB), offizielles Netzteil, HDMI-Kabel (Zero 2 W: Mini-HDMI). Zum Schreiben der Karte: Raspberry Pi Imager oder balenaEtcher.",
          experimentell: "Neu in 0.23 und noch experimentell: Image-Bau und Verwaltung sind getestet, die Wiedergabe auf echten Pis noch nicht auf allen Modellen. Seit 0.24 kann ein Pi 4/5 die Seite auch direkt zeigen (Einstellungen → Anzeige).",
          basis: "Player-Image", basisFehlt: "noch nicht geladen – einmalig etwa 850 MB", basisLaden: "Player-Image laden", basisNeu: "Neu laden",
          basisLaedt: (a, b) => `wird geladen … ${a} von ${b} MB`, basisBereit: (v, d) => `Version ${v} vom ${d} – bereit`, basisFehler: "Laden fehlgeschlagen",
          port: (p) => `Die Pis erreichen den Server über Port ${p} – im Docker-/NAS-Betrieb muss er freigegeben sein (Zeile "${p}:${p}" unter ports).`,
          koppeln: "Player koppeln (ein Image für mehrere Geräte)", koppelnText: "Ein Image für beliebig viele Pis oder PCs: Es enthält Server-Adresse und WLAN, aber noch keinen Schlüssel. Jedes Gerät zeigt beim Start einen 6-stelligen Code auf dem Fernseher – hier eingeben, Name und Fernseher wählen, fertig. Der Schlüssel wird dabei sicher ausgehandelt und geht nie übers Netz.",
          sammelImage: "Image für mehrere Geräte herunterladen", fuer: "Für", code: "Code vom Fernseher", codePlatz: "123 456", koppelnKnopf: "Koppeln",
          gekoppelt: "Gekoppelt – der Pi startet in wenigen Sekunden.", wartend: (n) => n === 1 ? "1 Pi zeigt gerade einen Code" : `${n} Pis zeigen gerade einen Code`,
          keinerWartet: "Gerade zeigt kein Pi einen Code.",
          neu: "Player hinzufügen", name: "Name", namePlatz: "z. B. Wartezimmer", tv: "Zeigt den Fernseher", keinTv: "– noch keiner –", modell: "Modell",
          m: { pi45: "Pi 5, Pi 4 oder Pi 400", pi3: "Pi 3 oder Zero 2 W" }, netz: "Netzwerk", kabel: "LAN-Kabel", wlan: "WLAN",
          wlanGesp: "Gespeichertes WLAN", wlanNeu: "neues WLAN eingeben", ssid: "WLAN-Name (SSID)", pw: "WLAN-Passwort", merken: "WLAN in der Verwaltung speichern (für weitere Pis)",
          merkenText: "Gespeichert wird nur der WPA-Schlüssel, nicht das Passwort selbst. Er gibt trotzdem Zugang zum WLAN – Sicherungen enthalten ihn nur „mit Zugangsdaten“.",
          erweitert: "Erweitert", server: "Server-Adresse für die Pis", serverText: "Leer = automatisch. Ändern, wenn die Pis den Server unter einer anderen Adresse erreichen (z. B. anderer Port im Container).",
          streamPort: "Stream-Port von außen", streamPortText: "Leer = wie eingestellt. Nur nötig, wenn der Container den Stream-Port auf einen anderen Port abbildet.",
          gespeicherte: "Gespeicherte WLANs", vergessen: "Vergessen", erstellen: "Image erstellen und herunterladen", laedtHerunter: "Download startet …",
          schritte: "So geht es weiter", s1: "Raspberry Pi Imager öffnen → Gerät wählen → Betriebssystem: ganz unten „Eigenes Image“ (Use custom) → die heruntergeladene Datei → SD-Karte → Weiter.",
          s2: "Fragt der Imager nach „OS-Anpassungen“: Nein – alles steht schon im Image. (balenaEtcher: Datei wählen, Karte wählen, Flash.)",
          s3: "Karte in den Pi stecken, HDMI an den Fernseher, Strom an. Der erste Start dauert 2–3 Minuten (der Pi startet einmal neu), dann erscheint das Bild.",
          s4: "Findet der Pi kein Netz, öffnet er nach 2 Minuten einen Hotspot und zeigt auf dem Fernseher einen QR-Code – mit dem Handy scannen und das WLAN auswählen.",
          liste: "Player", keine: "Noch kein Player.", online: "online", offline: "offline", nieGesehen: "hat sich noch nie gemeldet",
          zuletzt: (z) => `zuletzt ${z}`, seit: (z) => `seit ${z}`, ip: "IP", netzArt: { kabel: "Kabel", wlan: "WLAN", hotspot: "Hotspot (Einrichtung)", keins: "kein Netz" },
          temp: "Temperatur", version: "Player", hdmi: "Bildschirm", keinHdmi: "kein Bildschirm erkannt", video: "Video",
          zustand: { start: "startet", fern_link: "wartet auf Freigabe in Tailscale", koppeln: "wartet auf Kopplung", spielt: "spielt", verbinde: "verbindet …", kein_tv: "kein Fernseher zugewiesen", aus: "Bildschirm aus (Zeitplan)",
                     stream_fehler: "Stream-Fehler", gesperrt: "entfernt", unbekannt: "dem Server unbekannt", direkt: "zeigt die Seite direkt", direkt_start: "Browser startet …" },
          drehung: "Drehung", aufloesung: "Ausgabe", a: { auto: "wie der Fernseher meldet", "720": "720p", "1080": "Full HD", "2160": "4K" },
          lautstaerke: "Lautstärke (%)", cec: "Fernseher nach Zeitplan ein- und ausschalten (HDMI-CEC)", cecText: "Wenn das Layout „schwarz“ ist (Zeitplan des Fernsehers), schaltet der Pi den Fernseher per HDMI aus und danach wieder ein. Am Fernseher muss CEC an sein (Samsung „Anynet+“, LG „SimpLink“, Sony „Bravia Sync“).",
          schreibschutz: "Schreibschutz (empfohlen)", schreibschutzText: "Das System läuft im Arbeitsspeicher, die SD-Karte bleibt unverändert – Stromausfall und Ausstecken schaden ihr nicht. Ändern startet den Pi neu.",
          systemupdate: "Systemupdates", su: { woechentlich: "wöchentlich (So 3 Uhr)", aus: "nur von Hand" }, hwdec: "Video-Dekodierung", hw: { auto: "Hardware (Standard)", aus: "nur CPU (bei Bildfehlern)" },
          anzeige: "Anzeige", am: { stream: "Stream vom Server (Standard)", direkt: "Direkt: Pi zeigt die Seite selbst (experimentell)" },
          anzeigeText: "Direkt: Der Pi öffnet die TV-Seite selbst im Browser – gestochen scharf, ohne Verzögerung, und der Server muss für diesen Pi nichts kodieren. Der Pi zeichnet in Full HD (4K-Fernseher rechnen hoch). Nur Pi 4/5 mit mindestens 2 GB Arbeitsspeicher (besser 4 GB); Videos und Kameras können ruckeln. Macht der Browser Probleme, nimmt der Pi für eine Stunde den Stream.",
          direktModus: "Direktmodus (Browser)",
          b: { bild: "Bildschirmfoto", erkennen: "Name anzeigen", cec_an: "TV ein", cec_aus: "TV aus", player_neu: "Player neu starten", neustart: "Pi neu starten",
               systemupdate: "Systemupdate jetzt", protokoll: "Protokoll holen" },
          bText: { erkennen: "Zeigt 30 Sekunden Name und IP auf dem Fernseher – so findest du den richtigen Pi.", systemupdate: "Der Pi lädt Updates (Schreibschutz kurz aus) und startet zweimal neu – etwa 5–15 Minuten." },
          wartet: (a) => `wartet auf den Pi: ${a}`, ergebnis: "Zuletzt", ok: "ok", fehlgeschlagen: "fehlgeschlagen",
          vor: (t) => `letzte Meldung vor ${t}`,
          fv: { titel: "Fernverwaltung", unterwegs: (n) => `${n} unterwegs`, zuletzt: (w, z) => `zuletzt: ${w} ${z}`, leer: "Noch nichts an diesen Player geschickt.",
            text: "Alles, was an diesen Player geschickt wurde: gesendet → vom Player abgeholt (er meldet sich alle 15 s) → Ergebnis. Die letzten 20 Einträge.",
            wartet: "wartet auf den Player", offline: "noch nicht abgeholt – ist der Player online?", abgeholt: (s) => `abgeholt nach ${s}`,
            umsetzen: "wird umgesetzt …", uebernommen: "übernommen", ok: "erledigt", fehler: "fehlgeschlagen", auto: "automatisch",
            terminal: "Terminal", laeuft: "läuft",
            e: { tv: "Fernseher", anzeige_modus: "Anzeige", drehung: "Drehung", aufloesung: "Ausgabe", lautstaerke: "Lautstärke", hwdec: "Video-Dekodierung",
                 schreibschutz: "Schreibschutz", wlan: "WLAN" },
            modus: { stream: "Stream", direkt: "Direkt" }, an: "an", aus: "aus",
            h: { ersetzt: "durch eine neuere Änderung ersetzt", dienst_neu: "verworfen – SignageCast wurde neu gestartet, bevor der Player es abholte",
                 keine_bestaetigung: "keine Bestätigung vom Player", kein_browser: "auf dem Image fehlt der Browser – bleibt beim Stream",
                 rueckfall: "der Browser hatte Probleme – Stream für 1 Stunde", nur_stream: "Pi 3/Zero 2 W: bleibt beim Stream",
                 nicht_erreichbar: "Server damit nicht erreichbar – zurück zum alten WLAN", kabel: "hängt am Kabel – WLAN gespeichert, aber nicht getestet",
                 pc_image: "PC: Updates kommen mit einem neuen Image", unbekannt: "der Agent kennt den Befehl nicht" },
            modusOk: (m) => `Player zeigt jetzt ${m}` },
          fw: { knopf: "Terminal", knopfText: "Shell (root) auf diesem Pi im Browser – wie das Terminal in Cockpit",
            aus: "Fernwartung ist auf diesem Pi aus. Einschalten: beim Erstellen des Images ankreuzen oder auf der Einrichtungsseite des Pi.",
            alt: "Der Agent auf diesem Pi kann noch keine Fernwartung – er aktualisiert sich bei der nächsten Meldung selbst.",
            laeuft: (seit, wer) => `Fernwartung läuft seit ${seit} (${wer})`,
            image: "Fernwartung erlauben (Terminal aus der Verwaltung, root)",
            imageText: "Ab Werk aus. Der Player lässt eine Sitzung nur zu, wenn das hier oder auf seiner Einrichtungsseite eingeschaltet ist – so kommt auch jemand, der den Server übernimmt, nicht auf Player, die es nicht erlauben.",
            titel: (n) => `Terminal – ${n}`, schliessen: "Sitzung beenden", zu: "Schließen", verbinde: "Verbinde mit dem Pi … (bis zu 15 s)", verbunden: "verbunden",
            beendet: (g) => `Sitzung beendet: ${g}`,
            schreibschutz: "Schreibschutz ist an: Änderungen sind nach einem Neustart weg – vorher in den Einstellungen dieses Pi ausschalten.",
            hinweis: "Auf dem Fernseher steht solange „Fernwartung aktiv“. Nach 10 min ohne Eingabe oder spätestens nach 60 min endet die Sitzung.",
            protokoll: "Letzte Fernwartungen", verloren: "… (ältere Ausgabe übersprungen)",
            gruende: { verwaltung: "beendet", leerlauf: "10 min ohne Eingabe", zeitgrenze: "60 min erreicht", verwaltung_weg: "Fenster geschlossen",
              pi_antwortet_nicht: "der Pi hat sich nicht gemeldet", neue_sitzung: "neue Sitzung", geraet_entfernt: "Pi entfernt",
              pi_beendet: "Shell beendet (exit)", pi_leerlauf: "10 min ohne Eingabe", pi_zeitgrenze: "60 min erreicht",
              pi_abgeschaltet: "am Pi abgeschaltet", unbekannt: "Sitzung unbekannt" } },
          protokollZeigen: "Protokoll anzeigen", wlanAendern: "WLAN ändern", wlanAendernText: "Der Pi probiert das neue WLAN aus. Erreicht er den Server damit nicht, kehrt er zum bisherigen zurück. Bisherige WLANs bleiben als Ersatz gespeichert.",
          wlanOffen: (s) => `WLAN-Wechsel zu „${s}“ wartet auf den Pi`, wlanSenden: "An den Pi senden", wlanGesendet: "Gesendet – der Pi übernimmt es bei der nächsten Meldung",
          imageNeu: "Image erneut herunterladen", imageNeuText: "Für eine neue SD-Karte. Der Schlüssel bleibt gleich – eine alte Karte mit diesem Player funktioniert weiter.",
          entfernen: "Entfernen", entfernenFrage: (n) => `Player „${n}“ entfernen? Sein Schlüssel wird ungültig, der Pi zeigt dann nur noch einen Hinweis.`,
          befehlOk: "Befehl gesendet – der Player holt ihn in wenigen Sekunden ab", bildAlt: (z) => `Bildschirmfoto von ${z}`, netzwerke: "WLANs auf dem Player",
          update: "Letztes Systemupdate",
          h: { pi_kein_tv: "Kein Fernseher zugewiesen – der Pi zeigt nur einen Hinweis.", pi_h265: "Pi 3/Zero 2 W kann H.265 nicht flüssig abspielen: beim Fernseher den Codec „H.264“ wählen.",
               pi_4k: "Pi 3/Zero 2 W schafft kein 4K: beim Fernseher die Auflösung „Full HD“ wählen.", pi5_h264_4k: "Der Pi 5 dekodiert H.264 nur per CPU – 4K ruckelt. Beim Fernseher „H.265“ oder „Full HD“ wählen.",
               pi_strom: "Der Pi meldet Unterspannung oder Drosselung – offizielles Netzteil nehmen.", pi_heiss: "Der Pi ist sehr warm (über 80 °C) – Gehäuse mit Kühlung oder Lüfter.",
               pi_kein_hdmi: "Kein Bildschirm erkannt – HDMI-Kabel prüfen (Pi 4/5: den Anschluss neben dem Strom nehmen).",
               pi_direkt_pi3: "Der Direktmodus braucht einen Pi 4 oder Pi 5 – dieser Pi zeigt den Stream.",
               pi_direkt_kein_browser: "Das Image dieses Pi hat noch keinen Browser (vor 0.24 erstellt): für den Direktmodus ein neues Image herunterladen und flashen. Bis dahin zeigt er den Stream.",
               pi_direkt_ram: "Dieser Pi hat weniger als 2 GB Arbeitsspeicher – für den Direktmodus knapp (Browser und Cache liegen mit Schreibschutz im Arbeitsspeicher). Ruckelt die Seite oder startet sie neu: Anzeige auf „Stream“ stellen oder einen Pi mit 4 GB nehmen.",
               pi_direkt_rueckfall: "Der Browser hatte Probleme – der Player zeigt für eine Stunde den Stream. „Player neu starten“ versucht es sofort wieder.",
               pc_kein_bildschirm: "Kein Bildschirm erkannt – Kabel prüfen (HDMI, DisplayPort) und den Bildschirm einschalten.",
               pc_ist_pi: "Dieses Gerät meldet sich als Raspberry Pi – in den Einstellungen das Modell auf den passenden Pi stellen.",
               pi_ist_pc: "Dieses Gerät meldet sich als PC – in den Einstellungen das Modell auf „PC“ stellen." },
          pc: { titel: "PC als Player (seit 0.36, experimentell)",
            text: "Ein normaler PC, Mini-PC oder Thin Client (x86-64 mit UEFI) wird zum Player: Er startet vom USB-Stick, ohne etwas auf seiner Festplatte zu ändern, und zeigt die Seite im Direktmodus selbst – gestochen scharf, ohne Verzögerung, und der Server muss für ihn nichts kodieren. Verwaltet wird er hier wie ein Pi.",
            bedarf: "Dazu: 64-Bit-PC mit UEFI (etwa ab 2013; Secure Boot darf an bleiben), mindestens 4 GB Arbeitsspeicher, Intel- oder AMD-Grafik (NVIDIA geht, Videos aber ohne Hardware-Dekodierung), USB-Stick ab 4 GB, LAN-Kabel oder WLAN. Kein HDMI-CEC (TV ein/aus) und keine Systemupdates – neue Software kommt mit einem neuen Image.",
            basis: "PC-Image", basisFehlt: "noch nicht geladen – einmalig etwa 1 GB",
            format: "Format", f: { gz: "USB-Stick (.img.gz – balenaEtcher, Raspberry Pi Imager, Rufus)", iso: "ISO (.iso, ungepackt – Ventoy, CD, virtuelle Maschine)" },
            formatText: "Beides ist dasselbe System. Vom USB-Stick merkt sich der PC Kopplung, WLAN und Updates des Players auf dem Stick; von CD oder Ventoy nur bis zum Neustart (die Einstellungen kommen ohnehin vom Server).",
            s1: "USB-Stick mit balenaEtcher, Raspberry Pi Imager („Eigenes Image“) oder Rufus beschreiben – Rufus fragt nach dem Modus: „DD-Image“ wählen. Ventoy: die .iso einfach auf den Stick kopieren.",
            s2: "Stick in den PC stecken, Bildschirm anschließen, einschalten und vom Stick starten (Startmenü meist mit F12, F11, F8 oder Esc; sonst im UEFI-Setup USB an die erste Stelle).",
            s3: "Der erste Start dauert 1–2 Minuten, dann erscheint die Seite. Auf der Festplatte des PCs ändert sich nichts.",
            s4: "Mit LAN-Kabel ist nichts weiter zu tun. Mit WLAN: Findet der PC kein Netz, öffnet er nach 2 Minuten einen Hotspot (wenn seine WLAN-Karte das kann) und zeigt einen QR-Code.",
            live: "Live-System: läuft schreibgeschützt (Stromausfälle schaden nicht). Systemupdates gibt es nicht – für neue Software „Image erneut herunterladen“ und den Stick neu beschreiben.",
            neustart: "PC neu starten", m: "PC (x86-64, UEFI) – experimentell" },
          br: { m: "Browser-Gerät (nur Link, ohne Image)", titel: "Browser-Gerät",
            text: "Für Geräte, die schon einen Browser haben: Smart-TV, Fire-TV-Stick, ein PC mit fertiger Kiosk-Live-CD (z. B. Porteus Kiosk) oder einfach ein Browser im Vollbild (F11). Es gibt kein Image – du bekommst einen geheimen Link, der genau diesen Fernseher zeigt. Ohne Bildschirmfoto, Rückfall auf den Stream und Fernwartung; „online“ heißt: die Seite holt ihre Daten (alle 15 s).",
            erstellen: "Link erstellen", link: "Link", kopieren: "Kopieren", kopiert: "Kopiert",
            neu: "Neuen Link erzeugen", neuFrage: "Neuen Link erzeugen? Der bisherige gilt dann sofort nicht mehr – Geräte damit zeigen einen Fehler, bis der neue eingetragen ist.", neuOk: "Neuer Link erstellt",
            linkText: "Im Browser des Geräts als Startseite setzen (Kiosk-CD: als Startadresse). Wer den Link kennt, sieht diesen Fernseher – nicht die Verwaltung. Wie ein Passwort behandeln; Port 8890 ist unverschlüsseltes HTTP, also nur im eigenen Netz verwenden." } },
    fern: { titel: "Player an anderem Standort", text: "Ein Pi oder PC an einem anderen Ort (Praxis, Ferienwohnung, Filiale) erreicht SignageCast über Tailscale. An keinem Router wird ein Port geöffnet; Anzeige, Befehle und das Terminal laufen wie zu Hause.",
          link: { s1: "1. Tailscale auf diesem Server", s2: "2. Mit deinem Tailscale-Konto verbinden", s3: "3. Einschalten",
                  einrichten: "Tailscale einrichten", einrichtenText: "Installiert Tailscale aus dem offiziellen Paketarchiv (etwa 1 Minute).", laeuft: "wird eingerichtet …",
                  fehler: { kein_tun: "Diesem Container fehlt /dev/net/tun. Auf dem Proxmox-Host einmal ausführen (Container-ID statt <ID>), dann hier noch einmal:", schluessel: "Der Signaturschlüssel von Tailscale stimmt nicht – abgebrochen.", installation: "Installation fehlgeschlagen – Internet erreichbar?", operator: "Tailscale läuft, erlaubt SignageCast aber die Anmeldung nicht." },
                  container: "Im Container: Tailscale auf dem Host installieren und dort anmelden – siehe Anleitung. Dann weiter mit „Einschalten“ (erweitert, mit Adresse).",
                  verbinden: "Mit Tailscale verbinden", verbindenText: "Öffnet die Anmeldung bei Tailscale in einem neuen Fenster – melde dich an und bestätige. Diese Seite merkt es von selbst.",
                  oeffnen: "Anmelde-Link öffnen", wartet: "Warte auf die Anmeldung …",
                  verbunden: (n, ip, k) => `Verbunden als „${n}“ (${ip})${k ? " · " + k : ""}`,
                  einschalten: "Fernstandorte einschalten", an: "Eingeschaltet – beim Player „An einem anderen Standort“ ankreuzen.", aus: "Ausschalten" },
          erweitert: "Erweitert: OAuth-Client oder Headscale",
          anleitung: "Anleitung", art: "Dienst", arten: { aus: "aus", link: "Tailscale – per Anmelde-Link", tailscale: "Tailscale – mit OAuth-Client", headscale: "Headscale (selbst betrieben)" },
          server: "SignageCast im Tailnet", serverText: "Die Tailnet-IP dieses Servers (100.x.y.z). Tailscale muss hier laufen – siehe Anleitung.", vorschlag: (ip) => `Erkannt: ${ip} – übernehmen`,
          clientId: "OAuth-Client-ID", clientSecret: "OAuth-Client-Secret", clientText: "In der Tailscale-Verwaltung unter Settings → Trust credentials → OAuth client anlegen: Rechte „Auth Keys: Write“ und „Devices Core: Write“, Tag wie unten.",
          url: "Headscale-Adresse", apiKey: "API-Schlüssel", apiText: "headscale apikeys create --expiration 365d", benutzer: "Benutzer-ID (optional)",
          tag: "Tag der Player", tagText: "Die Player bekommen diesen Tag. In der Zugriffsregel darf er nur SignageCast erreichen.",
          pruefen: "Verbindung prüfen", geprueft: (n, name) => n == null ? `Verbindung ok – SignageCast ist als „${name}“ im Tailnet.` : `Verbindung ok – ${n} Geräte im Tailnet, SignageCast als „${name}“ gefunden.`,
          regel: "Zugriffsregel – empfohlen", regelText: "Ohne Regel darf in Tailscale jedes Gerät alle anderen erreichen – ein Player in fremden Räumen käme an alle deine Geräte. Mit dieser Regel erreichen Player nur SignageCast, deine eigenen Geräte weiter alles. Kopieren, im Regel-Editor einfügen (hast du schon eigene Regeln, nur die Teile ergänzen), speichern.",
          kopieren: "Kopieren", kopiert: "Kopiert", editor: "Regel-Editor von Tailscale öffnen",
          box: "An einem anderen Standort (über Tailscale)", boxHs: "An einem anderen Standort (über Headscale)",
          boxText: (ip) => `Der Player tritt beim ersten Start mit einem Einmal-Schlüssel (7 Tage gültig) dem Tailnet bei und spricht SignageCast unter ${ip} an. Nur mit dem Image für genau dieses Gerät.`,
          boxLink: "Beim ersten Start meldet sich der Player per Link an: Steht er noch hier, erscheint auf seiner Karte „Player freigeben“; am anderen Ort zeigt der Fernseher einen QR-Code. Nur mit dem Image für genau dieses Gerät.",
          freigeben: "Player freigeben (Tailscale)", freigebenText: "Öffnet Tailscale – anmelden und bestätigen. Danach verbindet sich der Player von selbst.",
          ohneTag: "Ohne Tag angemeldet: Die Zugriffsregel fehlt – dieser Player kann alle Geräte in deinem Tailnet erreichen, und seine Anmeldung läuft nach 180 Tagen ab. Regel einfügen (Einstellungen → Fernstandorte), dann neues Image.",
          zeile: "Anderer Standort", wartet: "Image erstellt – noch nicht beigetreten", direkt: "direkt", relay: (r) => `über Relay ${r}`,
          fehler: { fehlt: "Image vor 0.41 ohne Tailscale – neues Image erstellen", abgemeldet: "vom Tailnet abgemeldet – neues Image erstellen", startet: "startet …" },
          entfernt: "Player entfernt – auch aus dem Tailnet", nichtGefunden: "Player entfernt – im Tailnet nicht (mehr) gefunden",
          entferntLink: "Player entfernt – er meldet sich beim nächsten Kontakt selbst aus Tailscale ab. Ist er nicht mehr erreichbar, in Tailscale unter Machines löschen.",
          entferntFehler: (t) => `Player entfernt, aber nicht aus dem Tailnet: ${t} – bitte dort von Hand löschen`,
          userspace: "Tailscale läuft auf diesem Server im Userspace-Modus. Dann ist die Verwaltung aus dem Tailnet ohne Anmeldung erreichbar – Fernstandorte bleiben gesperrt. Bitte /dev/net/tun einrichten und den Userspace-Modus abschalten (Anleitung)." },
    ki: { titel: "KI-Assistenten im Heimnetz", text: "Claude oder ein anderer KI-Assistent verwaltet die Inhalte direkt: Layouts bauen und ändern, Vorschau ansehen, Laufschrift, Durchsagen, Streams. Jeder Computer bekommt einen eigenen Zugang, den du hier jederzeit entfernen kannst – er gilt dann sofort nicht mehr. Nur im Heimnetz; jede Änderung steht im Protokoll („MCP <Computer>“).",
          liste: "Verbundene Computer", keine: "Noch kein Computer verbunden – die Schnittstelle ist aus.", name: "Name des Computers", programm: "Programm", recht: "Darf",
          rechte: { aendern: "Inhalte ändern", lesen: "nur lesen" }, arten: { desktop: "Claude Desktop", code: "Claude Code", cursor: "Cursor", vscode: "VS Code" },
          zuletzt: "Zuletzt benutzt", nie: "noch nie", wartet: "wartet auf den ersten Start der Datei (1 Stunde gültig)", abgelaufen: "Datei nicht rechtzeitig gestartet – entfernen und neu verbinden",
          entfernen: "Entfernen", entfernenFrage: (n) => `Computer „${n}“ entfernen? Der KI-Assistent dort hat danach sofort keinen Zugriff mehr.`, entfernt: "Entfernt – kein Zugriff mehr",
          neu: "Computer verbinden", adresse: "Adresse dieses Rechners", adresseText: "So erreicht der Computer SignageCast im Heimnetz (IP oder Name).", verbinden: "Verbinden",
          namePlatz: "z. B. Laptop Büro", keinHttps: "Für Claude Desktop fehlt das Zertifikat (openssl) – bitte Claude Code, Cursor oder VS Code wählen oder per SSH verbinden.",
          fertig: (n) => `„${n}“ ist eingetragen.`,
          desktop: ["Die Datei wurde heruntergeladen – doppelt anklicken (oder in Claude Desktop: Einstellungen → Erweiterungen → hineinziehen) und „Installieren“ wählen.",
                    "Innerhalb einer Stunde Claude Desktop starten bzw. die Erweiterung einschalten – beim ersten Start verbindet sie sich und ist danach dauerhaft eingerichtet.",
                    "Fragen, z. B.: „Zeig mir den Status von SignageCast und ein Vorschaubild.“"],
          desktopSicher: "Verschlüsselt (HTTPS); die Datei vertraut nur diesem SignageCast. Sie enthält keinen dauerhaften Schlüssel – nach dem ersten Start ist sie wertlos.",
          nochmal: "Datei nochmal herunterladen",
          befehl: "Im Terminal ausführen:", link: "In Cursor öffnen", linkText: "Cursor fragt nach und trägt den Server ein. Alternativ den Eintrag für die mcp.json kopieren:",
          einmal: "Der Schlüssel wird nur jetzt angezeigt. Wer ihn hat, kann die Inhalte ändern – nicht weitergeben; bei Verlust den Computer entfernen.",
          unverschluesselt: "Diese Programme verbinden sich im Heimnetz unverschlüsselt (wie das Pult) – nur in einem vertrauenswürdigen Netz verwenden. Verschlüsselt: Claude Desktop oder SSH (siehe Anleitung).",
          vscodeWin: "Windows-PowerShell verschluckt Anführungszeichen – dort besser den Eintrag in die mcp.json kopieren:",
          kopieren: "Kopieren", kopiert: "Kopiert", anleitung: "Anleitung (auch Verbindung per SSH)" },
    prot: { titel: "Änderungsprotokoll", text: "Wer hat wann was geändert – in der Verwaltung, am Pult, per Webhook oder durch SignageCast selbst. Festgehalten werden nur Art und Bereich, keine Werte (keine Passwörter, keine Texte von Durchsagen). Die letzten 500 Einträge; Teil der Sicherung.",
            quelle: "Herkunft", alle: "alle", zeit: "Zeit", wer: "Wer", was: "Was", leer: "Noch keine Einträge.", mehr: "Ältere zeigen",
            quellen: { verwaltung: "Verwaltung", pult: "Pult", webhook: "Webhook", system: "SignageCast" }, befund: { schwarz: "nur Schwarz", steht: "Bild stand still" },
            layouts: { neu: "neue Layouts", geaendert: "Layouts geändert", geloescht: "Layouts gelöscht" },
            bereich: { fernseher: "Fernseher", layouts: "Layouts", video: "Video", medien: "Medien", quellen: "Datenquellen", radio: "Radio", einspieler: "Einspieler",
                       kategorien: "Kategorien", standort: "Standort", anzeige: "Anzeige", ha: "Home Assistant", benachrichtigung: "Benachrichtigungen",
                       sicherung: "Sicherung", pult: "Durchsage-Pult", alarm: "Notfall-Vollbild", webhook: "Webhook", stream: "Stream", sprache: "Sprache", updates: "Updates" },
            aktion: { einstellungen: "Einstellungen gespeichert", webhook_neu: "neuer Webhook-Schlüssel", medien_neu: "Medium hochgeladen", medien_loeschen: "Medium gelöscht",
                      schalten: "Fernseher geschaltet", nach_einschalten: "Quelle/Seite am Fernseher ausprobiert", update: "Update angefordert",
                      update_ergebnis: "Update", sicherung_erstellen: "Sicherung erstellt", sicherung_loeschen: "Sicherung gelöscht",
                      sicherung_einspielen: "Sicherung eingespielt", quelle_datei: "Datei für Datenquelle hochgeladen", kategorie_loeschen: "Kategorie gelöscht",
                      stream_neu: "Stream hinzugefügt", suche: "Suche gestartet", radio_neu: "Radiosender hinzugefügt", seite_neu_laden: "TV-Seite neu geladen",
                      kette_neu: "Wiedergabe neu gestartet", ton_neu: "Ton und Stream neu gestartet", layout_wiederherstellen: "Layout-Version wiederhergestellt",
                      stimme_laden: "Stimme geladen", probedurchsage: "Probedurchsage", einspieler_jetzt: "Einspieler jetzt gezeigt", stream_freigeben: "abgelehnten Stream freigegeben",
                      alarm_an: "Notfall-Vollbild ausgelöst", alarm_aus: "Notfall-Vollbild beendet", durchsage: "Durchsage gesendet", meldung: "Laufschrift-Meldung gesendet",
                      meldung_aus: "Laufschrift-Meldung beendet", layout: "Layout umgeschaltet", layout_aus: "Layout zurückgeschaltet",
                      internet_weg: "Internet nicht erreichbar seit", internet_wieder: "Internet wieder da (Ausfall)",
                      bild_neu_laden: "Bildprüfung: TV-Seite neu geladen", bild_kette_neu: "Bildprüfung: Wiedergabe neu gestartet",
                      ki_neu: "Computer für KI-Assistenten verbunden", ki_entfernen: "Computer für KI-Assistenten entfernt", ki_gekoppelt: "Claude Desktop hat sich verbunden", fernnetz: "Fernstandorte geändert",
                      "stream_*": (a) => `Stream: ${{ aendern: "geändert", entfernen: "entfernt", zeigen: "jetzt gezeigt", "strikes-zuruecksetzen": "Strikes zurückgesetzt" }[a] || a}`,
                      "radio_*": (a) => `Radiosender ${a === "entfernen" ? "entfernt" : "geändert"}`,
                      "player_*": (a) => `Player: ${{ neu: "neu angelegt", koppeln: "gekoppelt", einstellungen: "Einstellungen", wlan: "WLAN", image: "Image erstellt", entfernen: "entfernt", aendern: "geändert", befehl: "Befehl", "link-neu": "neuer Link" }[a] || a}`,
                      "terminal_*": (a) => a === "start" ? "Terminal geöffnet" : "Terminal beendet" } },
    internet: "Internet", online: "erreichbar", offline: "nicht erreichbar", onlineText: "Live-Kameras laufen",
    offlineSeit: (z) => `seit ${z} – die Fernseher zeigen eigene Medien bzw. ein Ersatzbild`,
    bildBefund: { schwarz: "Bildprüfung: zeigt nur Schwarz", steht: "Bildprüfung: Bild steht still" },
    pultLayout: (n, bis, von) => `Layout „${n}“ vom Pult (${von}) bis ${bis}`,
    todoTitel: "Zu erledigen", todoOk: "Alles in Ordnung.",
    todoAus: { tipp: "Ausblenden (dauerhaft, bis du ihn wieder einblendest)", update: "Ausblenden (bis zur nächsten Version)",
               warn: "Ausblenden (bis das Problem einmal behoben war – tritt es wieder auf, erscheint es wieder)" },
    todoVersteckt: (n) => n === 1 ? "1 ausgeblendet – anzeigen" : `${n} ausgeblendet – anzeigen`, todoVerbergen: "Ausgeblendete verbergen",
    todoEin: "Wieder einblenden", todoAusgeblendet: "ausgeblendet",
    todo: { internet: (s) => `Internet seit ${s} nicht erreichbar – die Fernseher zeigen eigene Medien bzw. ein Ersatzbild`,
            bild: (n, b) => b === "steht" ? `Bild von „${n}“ stand still – Seite neu geladen bzw. Wiedergabe neu gestartet` : `„${n}“ zeigte nur Schwarz – Seite neu geladen bzw. Wiedergabe neu gestartet`,
            player: (n) => `Player „${n}“ meldet sich nicht`, update: (v) => `Neue Version ${v} verfügbar`, ha: "Home Assistant ist nicht erreichbar", wetter: "Wetter konnte nicht geladen werden",
            sicherung: "Automatische Sicherung ist ausgeschaltet", sicherungFehler: "Letzte automatische Sicherung fehlgeschlagen",
            benachrichtigung: "Noch keine Benachrichtigung eingerichtet (z. B. bei Ausfall)", bnFehler: "Benachrichtigung konnte nicht gesendet werden",
            software: "Keine Grafikeinheit erkannt – Video wird in Software kodiert", passwort: "Startpasswort ändern",
            bildrate: (n) => `„${n}“ ruckelt: zu wenige Bilder/s – Leistungstest starten`,
            allgemein: (g, seit) => `Seit ${seit} fallen alle Streams durch (${{ aufloesung: "Auflösung zu niedrig", puffert: "puffert", steht: "Bild steht", fehler: "Fehler", startet_nicht: "startet nicht" }[g] || g}) – keine Strikes, vermutlich Störung bei YouTube oder im Browser`,
            doppelt: (n) => `„${n}“ ruckelt: Aufnahme verdoppelt Bilder – im Leistungstest „Ton und Stream neu starten“` },
    erweitert: "Erweitert", ungespeichert: "nicht gespeichert", ungespeichertFrage: "Es gibt nicht gespeicherte Änderungen. Trotzdem weiter?",
    bereiche: { uebersicht: "Übersicht", fernseher: "Fernseher", inhalte: "Inhalte", videoton: "Live-Videos", einstellungen: "Einstellungen", system: "System" },
    fernseherText: "Jeder Fernseher öffnet im Browser seine eigene Adresse und kann eigenen Ton, Sender und eigene Kategorien haben.",
    adresse: "Adresse am Fernseher", ton: "Ton", tonArt: { aus: "aus", radio: "Radio", tiere: "Originalton der Tiervideos" },
    sender: "Sender", keinSender: "– Sender wählen –", lautstaerke: "Lautstärke", videoZeigen: "Live-Videos zeigen",
    kennung: "Kennung (a–z, 0–9, steht in der Adresse)", fernseherNeu: "Fernseher hinzufügen", fernseherWeg: "Fernseher entfernen",
    schalten: "Über HA schalten", schaltenText: "Entität des Fernsehers in Home Assistant (media_player, switch oder remote). Beginnt im Zeitplan „schwarz“, wird er ausgeschaltet, danach wieder eingeschaltet – nur beim Wechsel, Einschalten von Hand bleibt also. Einschalten klappt nur, wenn es in HA geht (Samsung/LG oft nur mit Wake-on-LAN). Erst speichern, dann testen.",
    schaltenAus: "Aus (Test)", schaltenAn: "An (Test)", schaltenOk: "An Home Assistant geschickt",
    haQuelle: "Quelle wählen", quellenHolen: "Quellen aus HA holen",
    quelleText: "Optional, nur für media_player: z. B. „HDMI 2“ (dort hängt der Player). SignageCast wartet nach dem Einschalten (Zeitplan, Notfall, Test-Knopf), bis der Fernseher bereit ist (bis 90 s), wählt die Quelle und öffnet danach auf Wunsch die TV-Seite.",
    quelleNurMp: "Quellen gibt es nur bei media_player-Entitäten", keineQuellen: "Home Assistant meldet für dieses Gerät keine Quellen (oft erst, wenn es eingeschaltet ist).",
    quellenGefunden: (l, a) => `Quellen: ${l} – gerade: ${a}`,
    nachEin: "Nach dem Einschalten", nachTest: "Jetzt ausführen (Test)",
    oeffnen: "Danach TV-Seite öffnen", haDienst: "HA-Dienst",
    oeffnenArt: { "": "nein", lg: "LG webOS – Browser", android: "Android TV / Google TV / Fire TV (ADB)", eigen: "Eigener HA-Dienst" },
    oeffnenText: {
      lg: (u) => `Öffnet den Browser des Fernsehers mit ${u} (Integration „LG webOS TV“).`,
      android: (u) => `Öffnet ${u} im Standard-Browser (Integration „Android TV“ mit ADB, nicht „Android TV Remote“). Besser: eine Kiosk-App als Standard-Browser.`,
      eigen: (u) => `Ruft den Dienst mit diesen Daten (JSON) auf; {url} wird zu ${u}, {entity} zur Entität. Fehlt entity_id, wird die Entität ergänzt. Für Samsung z. B. ein Skript in HA.`,
    },
    haZustand: { an: "an", aus: "aus", weg: "nicht erreichbar", fehler: "HA-Fehler" }, geraetHa: "Gerät (HA)",
    haZustandNoch: "Zustand laut Home Assistant: wird abgefragt (einmal je Minute) …",
    haZustandLang: (z, roh, q, zeit) => `Zustand laut Home Assistant: ${z} (${roh}${q ? ", Quelle " + q : ""}), Stand ${zeit}.`,
    nachZuletzt: (n) => `Zuletzt ${n.zeit}: ${n.fehler ? "nicht ausgeführt – " + n.fehler : (n.schritte.length ? n.schritte.map((x) => x === "quelle" ? "Quelle gewählt" : "Seite geöffnet").join(", ") : "nichts nötig")}`,
    wirklichTvWeg: "Diesen Fernseher entfernen? Seine Adresse funktioniert dann nicht mehr.", weitererTv: "Weiterer Fernseher",
    tvHinweis: "Ton, Sender, Lautstärke und Videos wirken sofort; Ausgabe und Bitrate beim nächsten Start des Streams.",
    meineSender: "Meine Sender", keineSender: "Noch keine Sender – unten Vorschläge laden oder eine eigene Adresse eintragen.",
    senderNutzung: "Welcher Fernseher welchen Sender spielt, stellst du im Reiter „Fernseher“ ein (Ton = Radio).",
    eigenerSender: "Eigenen Sender hinzufügen", senderAdresse: "Stream-Adresse (MP3/AAC, auch .m3u/.pls)", senderName: "Name",
    senderAnzeigen: "Sendernamen am Fernseher zeigen", puffer: "Puffer (Vorlauf)",
    pufferText: "Überbrückt Aussetzer des Senders bis zu dieser Länge. Das Radio startet um diese Zeit verzögert (auch beim Senderwechsel). 0 = ohne Puffer, direkt vom Sender.", inNaehe: "Sender passend zum Standort", regionWoerter:
      "Zusätzliche Suchwörter für die Region (z. B. Oberpfalz), mit Komma getrennt", vorschlaegeLaden: "Vorschläge laden",
    vorschlaegeDauer: "Lädt (ca. 5–15 s) …", gruppe: { naehe: "In der Nähe / Region", region: "Bundesland", land: "Ganzes Land" },
    senderSuche: "Sender nach Namen suchen", suchen: "Suchen", hinzu: "Hinzufügen", hinzugefuegt: "Hinzugefügt",
    quelle: "Quelle: radio-browser.info (freies Senderverzeichnis); Ort: OpenStreetMap.", gefundenFuer: "Gesucht für",
    playlist: "Playlist einfügen (M3U/PLS)", playlistText: "Inhalt einer .m3u- oder .pls-Datei hier einfügen oder die Datei auswählen – jeder Eintrag wird ein eigener Sender (Name aus #EXTINF).",
    playlistUebernehmen: "Sender übernehmen", playlistPruefen: "Prüfe die Einträge …",
    playlistErgebnis: (n, d) => `${n} Sender übernommen${d ? `, ${d} schon vorhanden` : ""}.`,
    ortSuche: "Ort suchen (z. B. Köln)", ortGesetzt: "Standort gespeichert", zeigenAuf: "„Jetzt zeigen“ auf",
    alleTv: "allen Fernsehern", tonAnzeige: "Ton",
    epText: "Zu festen Minuten unterbricht ein Beitrag die Rotation im Videofenster und läuft ganz durch – z. B. „tagesschau in 100 Sekunden“ zur vollen und halben Stunde. Mit Ton ist das Radio solange stumm.",
    epNeu: "Einspieler hinzufügen", epQuelle: "Quelle", epQuelleArt: { tagesschau100: "tagesschau in 100 Sekunden (immer die aktuelle Ausgabe)", video: "Video-Adresse (MP4)", youtube: "YouTube-Video oder Kanal (neuestes Video)" },
    epUrl: "Adresse / Link", epMinuten: "Minuten der Stunde", epAndere: "andere (z. B. 0,20,40)", epZeit: "nur zwischen", epTon: "mit Ton",
    epFernseher: "Fernseher (keiner gewählt = alle)", epAktiv: "aktiv", epJetzt: "Jetzt zeigen", epJetztOk: "Läuft in bis zu 15 s am Fernseher",
    epStand: "Stand", epFehler: "Fehler", epKeine: "Noch keine Einspieler.",
    wetterQuelle: "Wetterquelle", wetterQuelleArt: { met: "Eigenes Wetter (MET Norway, für den Standort)", ha: "Home Assistant (Wetter-Entität)" },
    metText: "Wetter, Wetterbild und Vorhersage kommen direkt von MET Norway (kostenlos, weltweit) für den Standort (unten auf dieser Seite) – Home Assistant ist dafür nicht nötig. Am Fernseher steht klein „Wetterdaten: MET Norway“ (Lizenzbedingung).",
    bnTitel: "Benachrichtigungen", bnText: "SignageCast meldet sich bei Ausfall eines Fernsehers, fehlgeschlagenem Update oder Sicherung und wenn Home Assistant länger als 5 Minuten nicht erreichbar ist – jeweils einmal, mit Entwarnung.",
    bnTelegram: "Telegram", bnBotToken: "Bot-Token", bnChatId: "Chat-ID", bnEmail: "E-Mail (SMTP)", bnServer: "SMTP-Server", bnPort: "Port",
    bnSicherheit: "Verschlüsselung", bnBenutzer: "Benutzer", bnPasswort: "Passwort", bnAbsender: "Absender", bnEmpfaenger: "Empfänger (mit Komma trennen)",
    bnHA: "Home Assistant", bnDienst: "Benachrichtigungsdienst", bnAktiv: "aktiv", bnTest: "Testnachricht", bnTestOk: "Testnachricht gesendet",
    bnEreignisse: "Melden bei", bnEr: { ausfall: "Ausfall eines Fernsehers", update: "Update fehlgeschlagen", sicherung: "Sicherung fehlgeschlagen", ha: "Home Assistant getrennt", leistung: "Fernseher ruckelt (zu wenige Bilder/s)", internet: "Internet nicht erreichbar (Entwarnung mit Zeitraum)" },
    bnLetzte: "Zuletzt gesendet",
    whTitel: "Meldung per Webhook", whText: "Andere Systeme (z. B. Home Assistant) können eine kurze Meldung als Banner auf die Fernseher legen – über jedes Layout. Nur mit geheimem Schlüssel; der Schlüssel wird nur einmal nach dem Erzeugen angezeigt.",
    whAktiv: "Meldungen annehmen", whNeu: "Neuen Schlüssel erzeugen", whVorhanden: "Schlüssel gesetzt (••••)", whKeiner: "noch kein Schlüssel",
    whEinmal: "Nur jetzt sichtbar – bitte sicher ablegen:", whBeispiel: "Beispiel (Text, Dauer in Sekunden, Stil info/warnung, optional tv=<Kennung>):",
    whNeuFrage: "Neuen Schlüssel erzeugen? Der alte gilt danach nicht mehr.",
    zeitTitel: "Zeitquelle", ntpServer: "NTP-Server", ntpAuto: "automatisch", zeitzone: "Zeitzone", systemZone: "automatisch",
    zeitText: "Der Container nimmt die Uhrzeit des Hosts (z. B. Proxmox). SignageCast prüft alle 30 Minuten gegen die Zeitquelle: Ist die Uhr des Hosts synchronisiert, bleibt alles, wie es ist; sonst (oder bei mehr als 1 s Abweichung) korrigiert SignageCast Uhr, Takt und Einspieler. NTP-Server leer = Länder-Pool zum Standort (z. B. de.pool.ntp.org). Zeitzone automatisch = die des Systems, bei UTC die des Landes am Standort.",
    hostSync: "Zeit vom Host (Proxmox), synchronisiert – keine Korrektur nötig", hostNichtSync: "Uhr des Hosts nicht synchronisiert – SignageCast korrigiert per NTP",
    abweichung: "Abweichung", zeitWarnung: "Mehr als 2 s Abweichung – bitte die Uhr des Hosts prüfen (z. B. chrony/NTP auf Proxmox).",
    wetterKarte: "Wetter", zeitKarte: "Zeit", layoutWahl: "Layout", zeitplan: "Zeitplan (optional)",
    zeitplanText: "Zu bestimmten Zeiten ein anderes Layout zeigen, z. B. nachts nur die Uhr oder ganz schwarz (spart Strom).",
    schwarz: "schwarz (aus)", von: "von", bis: "bis", zeitNeu: "Zeitraum hinzufügen", wetterText: "Wetterbild, Temperatur und Vorhersage kommen von dieser Entität; Räume, Kacheln und alles andere stellst du im Reiter „Layout“ ein.",
    speichern: "Speichern", gespeichert: "Gespeichert", deaktiviert: "ausgeschaltet", fehler: "Fehler", laedt: "Lädt …", ja: "ja", nein: "nein",
    passwortHinweis: "Hinweis: Wenn du dich noch mit dem Startpasswort anmeldest, ändere es bitte (oben rechts im Menü → " +
      "Konten → tvadmin → Passwort festlegen).", ausblenden: "Ausblenden",
    stream: "Videostream", laeuft: "läuft", aus: "aus (niemand schaut)", zuschauer: "Zuschauer", aktuell: "Gerade",
    qualitaet: "Qualität", codec: "Codec", verloren: "verlorene Bilder", bandbreite: "Bandbreite", cpu: "CPU", ram: "RAM frei",
    platte: "Speicher frei", laufzeit: "Laufzeit", last: "Last", kerne: "Kerne", von: "von",
    alleSek: (s) => (s % 60 ? `alle ${s} s` : `alle ${s / 60} min`), nurStream: "nur bei laufendem Stream",
    haFehler: { nicht_erreichbar: "HA nicht erreichbar", kein_trusted: "HA bietet dieser Adresse keine Anmeldung über vertrauenswürdige Netzwerke an (trusted_networks fehlt oder die IP ist nicht eingetragen)",
                kein_benutzer: "trusted_networks: kein Benutzer für diese IP zugeordnet", abgelehnt: "Anmeldung abgelehnt", http: "HA antwortet mit Fehler" }, ha: "Home Assistant", verbunden: "verbunden", getrennt: "nicht verbunden",
    rotation: "In Rotation", liste: "Streamliste", zuletzt: "zuletzt", pause: "YouTube-Pause bis", suche: "Stream-Suche",
    vorschau: "Bild am Fernseher", vorschauNeu: "Bild aktualisieren", keineVorschau: "Kein Bild – der Stream läuft gerade nicht.",
    seiteNeu: "TV-Seite neu laden", ketteNeu: "Stream neu starten", listeNeu: "Liste neu berechnen", erledigt: "Erledigt",
    neueVersion: (v) => `Neue Version ${v} verfügbar`, updateText: "Zum Aktualisieren den Befehl als root im Container ausführen (Einstellungen und Daten bleiben).",
    updateTextContainer: "Zum Aktualisieren das neue Image holen und den Container neu erstellen (Einstellungen und Daten im Volume bleiben):",
    systemSeitenContainer: "Protokolle: docker logs signagecast (bzw. podman logs). Neustart und Update über Docker/Podman.",
    passwortHinweisContainer: "Hinweis: Du meldest dich noch mit dem Startpasswort aus dem Protokoll an – bitte unter System → Zugang ein eigenes festlegen.",
    verwaltungTitel: "Anmeldung an der Verwaltung", pwAlt: "Bisheriges Passwort", pwNeu: "Neues Passwort (mind. 8 Zeichen)",
    pwAendern: "Passwort ändern", pwGeaendert: "Passwort geändert", abmelden: "Abmelden",
    kodierungKarte: "Videokodierung", kodierungArt: { vaapi: "Grafikeinheit (VAAPI)", software: "Software (CPU)" },
    kodierungSoftware: "Keine nutzbare Grafik – Notbetrieb: H.264 in Full HD per CPU (ca. 1–2 Kerne, solange jemand zuschaut).",
    epPuffer: "Puffer", epPufferArt: { vorab: "im Container vorab laden (empfohlen)", vorlauf: "Vorlauf im Browser", aus: "aus (direkt vom Server)" },
    epMenge: "Menge", epKomplett: "komplett", epMb: "nur den Anfang (MB)", epVorlauf: "Vorlauf (s)",
    epPufferText: "Vorab laden: Der Container holt jede neue Ausgabe, sobald sie erscheint, und der Fernseher spielt sie von dort – kein Hängen. " +
      "Bei „nur den Anfang“ kommt der Rest beim Abspielen vom Server (weniger Platz, der Vorsprung überbrückt Aussetzer). Nicht für YouTube.",
    epVorab: (mb, ges, st) => `vorab geladen: ${mb} MB${ges ? " von " + ges + " MB" : ""}${st ? " · Ausgabe " + st : ""}`,
    aenderungen: "Was ist neu?", projektseite: "Projektseite (GitHub)", fehlerMelden: "Fehler melden / Wunsch äußern",
    aufgaben: "Geplante Aufgaben", systemSeiten: "Dienste, Protokolle und Zeitpläne des Containers stehen im Cockpit-Menü " +
      "links unter „Dienste“ und „Protokolle“.",
    hinzufuegen: "Stream hinzufügen", link: "YouTube-Link oder Video-ID", name: "Name (leer = Titel)", kategorie: "Kategorie",
    breite: "Breite", laenge: "Länge", ortAuto: "leer = aus dem Titel erkennen", filter: "Suchen …", alle: "alle Kategorien",
    herkunftAlle: "fest und gefunden", nurFeste: "nur feste", nurGefundene: "nur gefundene", aktiv: "aktiv", geschuetzt: "geschützt",
    zustandAlle: "alle", zustand: { rotation: "in Rotation", bereit: "bereit", nacht: "Nacht", nicht_live: "nicht live",
      qualitaet: "Auflösung zu gering", pause: "Pause nach Strike", gesperrt: "gesperrt", strikes: "mit Strikes", ohne_ort: "Ort unbekannt",
      ungeprueft: "noch nicht geprüft", inaktiv: "inaktiv", kategorie_aus: "Kategorie aus" },
    hellIn: (d) => `hell in ${d}`, laeuftAus: "läuft aus (gerade dunkel)", pauseBis: (z) => `bis ${z}`, angebot: (p) => `Angebot ${p}`,
    vorab: (z, n) => `Vorabprüfung ${z}: ${n} geprüft`,
    zeigen: "Jetzt zeigen", uebernehmen: "Übernehmen", bearbeiten: "Bearbeiten", entfernen: "Entfernen", ablehnen: "Ablehnen",
    strikesWeg: "Strikes zurücksetzen", inRotation: "in Rotation",
    gefunden: "gefunden", fest: "fest", proben: "Proben", strikes: "Strikes",
    abgelehnt: "Abgelehnte Streams (werden bei der Suche nie wieder aufgenommen)", freigeben: "Freigeben",
    wirklichEntfernen: "Stream wirklich entfernen?", wirklichAblehnen: "Stream entfernen und nie wieder aufnehmen?",
    zeigenOk: "Läuft gleich am Fernseher (für einen Takt)", anzahl: (n, g) => `${n} Streams, davon ${g} gerade in Rotation`,
    sprache: "Sprache", wetter: "Wetter-Entität", vorhersage: "3-Tage-Vorhersage zeigen", raeume: "Räume (links, bis 4)",
    kacheln: "Kacheln (unten, bis 8)", icon: "Symbol (mdi-…)", zeileNeu: "Zeile hinzufügen", entitaetenFehlen:
      "Liste der Entitäten aus HA nicht verfügbar – Namen bitte von Hand eintragen.", iconsListe: "Symbolnamen: pictogrammers.com/library/mdi",
    videoAktiv: "Live-Videos zeigen", takt: "Minuten je Stream", nurTag: "nur Streams, wo vor Ort Tag ist",
    sonne: "Mindest-Sonnenhöhe (Grad)", mindeststufe: "Mindestqualität", schlecht: "so lange darunter, dann weiter (s)",
    grenze: "Strikes bis ein Stream nicht mehr läuft", sperre: "nach Strike überspringen für (Stunden)",
    kod: { titel: "Kodierung (für Fortgeschrittene)", encoder: "Encoder", preset: "Preset", tune: "Tune", bframes: "B-Frames",
      text: "Normalerweise passt „Automatisch“. Eine Änderung startet den Stream dieses Fernsehers neu (ein paar Sekunden schwarz); SignageCast probiert sie vorher kurz aus und bleibt bei „Automatisch“, wenn sie hier nicht läuft. Danach unter System → Leistungstest prüfen, ob die Kodierung mithält.",
      art: { auto: "Automatisch (empfohlen)", vaapi: "Intel/AMD-Grafik (VAAPI)", qsv: "Intel Quick Sync (QSV)", nvenc: "NVIDIA NVENC (experimentell)", software: "Software (libx264)" },
      info: { auto: "Nimmt die Grafikeinheit per VAAPI, ohne nutzbare Grafik Software.",
        vaapi: "Video-Einheit der Intel- oder AMD-Grafik über die offene Schnittstelle VAAPI – sparsam, 4K, H.264 und H.265. Kennt kein Preset und kein Tune.",
        qsv: "Intels eigener Weg zur selben Video-Einheit (Quick Sync über oneVPL), mit Presets. Braucht Intel-Grafik ab der 11./12. Generation (z. B. N100, Core ab Tiger Lake); bei älterer Intel-Grafik VAAPI nehmen.",
        nvenc: "Video-Einheit einer NVIDIA-Grafikkarte. Experimentell und ungetestet: Karte und NVIDIA-Treiber müssen im Container verfügbar sein (/dev/nvidia*, bei Docker --gpus all) – das richtet SignageCast nicht selbst ein.",
        software: "Der Prozessor kodiert H.264 (libx264): geht überall, kostet aber etwa 1–2 Kerne je Fernseher; immer Full HD und höchstens 8 Mbit/s." },
      grund: { keine_grafik: "keine Grafik (/dev/dri) gefunden", qsv_alt: "braucht Intel-Grafik ab der 11./12. Generation", keine_nvidia: "keine NVIDIA-Karte gefunden" },
      presetInfo: "Wie gründlich der Encoder rechnet: ultrafast ist am schnellsten, medium liefert bei gleicher Bitrate das schönste Bild, braucht aber deutlich mehr Rechenzeit – schafft der Rechner es nicht, ruckelt das Bild. Quick Sync und NVENC bekommen die passende eigene Stufe.",
      tuneArt: { zerolatency: "zerolatency (empfohlen)", keins: "keins" },
      tuneInfo: "zerolatency trimmt den Encoder auf geringe Verzögerung (kein Vorausschauen, jedes Bild sofort raus) – für Live-Bilder empfohlen, kostet etwas Bildqualität. „keins“ schaut einige Bilder voraus: etwas schöner, aber träger.",
      bfInfo: "B-Frames sind Zwischenbilder, die auch auf spätere Bilder verweisen: etwa 5–15 % weniger Daten, aber mehr Verzögerung, und manche Fernseher-Browser ruckeln damit. 0 ist für Live-Streams die sichere Wahl.",
      ohne: "VAAPI kennt kein Preset und kein Tune – die Felder wirken nur bei Software, Quick Sync und NVENC.",
      fehler: (enc, g) => `Die Einstellung läuft hier nicht (${enc}: ${g}) – dieser Fernseher nutzt deshalb „Automatisch“.`,
      aktiv: "Derzeit aktiv", std: "Standard", standard: "Zurück auf Standard" },
    codec: "Codec", codecArt: { auto: "Automatisch (empfohlen)", h265: "H.265 / HEVC", h264: "H.264 / AVC" },
    codecText: "Automatisch: 4K als H.265 (halbe Datenmenge, können fast alle 4K-Fernseher), Full HD als H.264 (läuft auf praktisch jedem Fernseher, Browser und Player). H.264 wählen, wenn ein Gerät ruckelt oder kein Bild zeigt – z. B. ältere Fernseher, Firefox; H.265 braucht bei gleicher Qualität etwa 30–40 % weniger Bitrate.",
    kategorien: "Kategorien", kategorienAlle: "Kategorien (für alle Fernseher)", streamTechnik: "Videostream", abschaltenTitel: "Videostream ohne Zuschauer",
    abschnitt: { anzeige: "Anzeige", video: "Live-Video", ton: "Ton" }, aufloesung: "Ausgabe", bitrate: "Bitrate (Mbit/s)",
    aufnahme: "Aufnahme (Browser)", aufnahmeArt: { 720: "720p – spart CPU", 1080: "1080p (empfohlen)", 1440: "1440p – schärfer, braucht mehr CPU" },
    aufnahmeText: "Größe, in der der Browser die TV-Seite zeichnet; die Grafikeinheit rechnet auf die Ausgabe um. Mehr als die Ausgabe bringt nichts. Live-Videos im Layout folgen der Aufnahme (720p holt von YouTube 720p). Eine Änderung startet den Stream kurz neu.",
    abschalten: "Abschalten ohne Zuschauer nach (s)", technikHinweis: "Ausgabe und Bitrate wirken beim nächsten Start des Streams.",
    sucheAktiv: "täglich nach neuen Streams suchen", uhrzeit: "Uhrzeit", max: "höchstens gefundene Streams",
    behalten: "Tage behalten, wenn nicht mehr gefunden", begriffe: "Suchbegriffe (je Zeile einer)",
    tierwoerter: "Titel muss eines dieser Wörter enthalten (je Zeile eines, reguläre Ausdrücke erlaubt)",
    ausschluss: "Titel darf keines dieser Wörter enthalten", orte: "Ortserkennung aus dem Titel: Muster ; Breite ; Länge (je Zeile)",
    jetztSuchen: "Jetzt suchen", sucheLaeuft: "Suche läuft (bis ca. 1 min) …", sucheErgebnis: (n, g) => `${g} Live-Streams gefunden, ${n} neu`,
    haUrl: "Adresse von Home Assistant", testen: "Verbindung testen", standort: "Standort (für Wetter-Bezug und Anzeige)",
    standortAusHA: "Aus HA übernehmen", testOk: (v) => `Verbunden – Home Assistant ${v}`, anleitung: "Einrichtung in Home Assistant", ipPlatzhalter: "IP-DES-CONTAINERS", benutzerIdPlatzhalter: "BENUTZER-ID",
    anleitungText: (ip) => [
      "SignageCast meldet sich ohne Passwort bei Home Assistant an – über „vertrauenswürdige Netzwerke“. HA erkennt den Container an seiner IP-Adresse.",
      "1. In HA unter Einstellungen → Personen einen Benutzer anlegen, z. B. „Fernseher“ (kein Administrator, „Nur lokal anmelden“ an).",
      "2. Den Benutzer öffnen – die lange Kennung am Ende der Adresszeile ist die Benutzer-ID.",
      `3. In der Datei configuration.yaml (z. B. mit dem File-Editor-Add-on) diesen Abschnitt ergänzen, BENUTZER-ID ersetzen. Die IP dieses Containers ist ${ip || "unbekannt (Home Assistant nicht erreichbar) – IP-DES-CONTAINERS ersetzen"}:`,
    ], anleitungEnde: "4. Konfiguration prüfen (Entwicklerwerkzeuge → YAML → Konfiguration prüfen) und HA neu starten. Danach hier „Verbindung testen“. " +
      "Wichtig: trusted_networks muss als erster Eintrag stehen, sonst erscheint eine Anmeldeseite. Steht dort schon ein homeassistant:-Abschnitt, nur die Zeilen darunter ergänzen.",
    sicherungLaden: "Sicherung herunterladen", sicherungEinspielen: "Sicherung oder Profil einspielen",
    mitGeheim: "mit Geheimnissen (API-Schlüssel, Passwörter der Datenquellen) – Datei dann nicht weitergeben",
    sichNeu: "Sicherung erstellen", mitGeheimFrage: "Zugangsdaten und Passwörter mitnehmen? (API-Schlüssel, Kamera-Passwörter, Passwort der automatischen Sicherung)",
    pwPflicht: "Dann wird die ZIP mit AES-256 verschlüsselt – ein starkes Passwort ist Pflicht (mind. 12 Zeichen, Groß/klein, Ziffern, Sonderzeichen; oder Passphrase ab 20 Zeichen). Öffnen geht mit SignageCast, 7-Zip oder WinRAR. Ohne das Passwort ist die Sicherung verloren.",
    pw1: "Passwort", pw2: "Passwort wiederholen", pwGut: "Passwort stark genug", pwSchwach: "Passwort zu schwach", pwUngleich: "Die Passwörter sind verschieden",
    sichErstellen: "Sicherung erstellen und herunterladen", sichFertig: "Sicherung erstellt", sichListe: "Gespeicherte Sicherungen (im Container)",
    sichAuto: "automatisch", sichManuell: "von Hand", sichMitGeheim: "mit Zugangsdaten", sichKeine: "Noch keine Sicherung gespeichert.",
    sichLetzteAuto: "Letzte automatische Sicherung", sichWegFrage: "Diese Sicherung löschen?", herunterladen: "Herunterladen",
    sichAutoTitel: "Automatisch sichern", sichPlan: "Wann", sichPlanArt: { aus: "aus", taeglich: "täglich", woechentlich: "wöchentlich" },
    wochentage: ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"], sichBehalten: "Aufheben (Anzahl)",
    sichAutoText: "Die automatischen Sicherungen liegen im Container; lade ab und zu eine herunter, damit sie auch einen Ausfall des Containers überstehen.",
    pwEinspielen: "Passwort (falls verschlüsselt)",
    karussell: "Layout-Karussell", karussellText: "Wechselt alle paar Minuten zwischen den gewählten Layouts (mindestens zwei). Ein Zeitplan hat Vorrang.",
    karussellAn: "an", karussellMin: "alle (min)", videoQuelle: "Videofenster zeigt",
    videoQuelleArt: { youtube: "Live-Streams (YouTube)", medien: "nur eigene Medien", gemischt: "gemischt" }, medienAlle: "jedes N-te Mal ein eigenes Medium",
    medText: "Eigene Bilder (JPG, PNG) und Videos (MP4/H.264, WebM) für das Videofenster – je Fernseher unter „Fernseher“ einstellen: nur eigene Medien oder gemischt mit den Live-Streams. Bilder stehen für ihre Anzeigedauer, Videos laufen ganz.",
    medHoch: "Dateien hochladen", medLaedt: (n, p) => `Lade ${n} … ${p} %`, medKeine: "Noch keine eigenen Medien.", medDauer: "Anzeigedauer (s)",
    medSicherung: "In die Sicherung kommen Bilder immer, Videos nur bis zusammen 200 MB – große Videos bitte zusätzlich selbst aufbewahren.",
    medWeg: "Dieses Medium löschen?",
    upSc: "SignageCast", upInstalliert: "installiert", upNeueste: "neueste", upAktuell: "aktuell", upJetzt: "Jetzt aktualisieren",
    upZurueck: (v) => `Zurück zu ${v}`, upZurueckFrage: "Zur vorigen Version zurückkehren? Einstellungen von vor dem letzten Update werden wiederhergestellt.",
    upScText: "Vor dem Update werden Einstellungen und Daten gesichert. Installiert wird nur ein Release mit gültiger Signatur. Läuft SignageCast danach nicht innerhalb einer Minute, geht es automatisch zurück. Der Fernseher kann dabei kurz neu verbinden.",
    upSystem: "System (Debian)", upPruefen: "Jetzt prüfen", upAlle: "Alle installieren", upNurSicher: "Nur Sicherheitsupdates",
    upKeine: "Keine System-Updates verfügbar.", upAnzahl: (n, s) => `${n} Update${n === 1 ? "" : "s"}${s ? `, davon ${s} Sicherheit` : ""}`,
    upGeprueft: "zuletzt geprüft", upNie: "noch nicht geprüft", upNeustart: "Neustart nötig, damit Kernel-Updates wirken",
    upLetzte: "Letzte Aktion", upPhase: { laeuft: "läuft …", ok: "erledigt", fehler: "Fehler", zurueck: "zurückgekehrt" },
    upAktion: { pruefen: "Prüfen", system: "System-Updates", sicherheit: "Sicherheitsupdates", signagecast: "SignageCast-Update", zurueck: "Zurück zur vorigen Version", unbekannt: "–" },
    upAuto: "Automatik", upAutoSystem: "System", upAutoSc: "SignageCast", upModus: { melden: "nur melden", sicherheit: "Sicherheitsupdates automatisch", auto: "automatisch" },
    upFenster: "Wartungsfenster", upAutoText: "Automatisch nur im Wartungsfenster und nur, wenn gerade niemand zuschaut. Geprüft wird einmal am Tag.",
    upGestartet: "Gestartet – der Stand aktualisiert sich hier",
    upContainer: "Im Docker-/Podman-Betrieb aktualisiert man über das Image – System und SignageCast stecken beide darin:",
    mitStrikes: "auch Strikes übernehmen", eingespielt: "Eingespielt", sicherungText: "Die Sicherung (ZIP) enthält Einstellungen, " +
      "Streamliste (mit Schutz-, Sperr- und Fundliste), Strikes, hochgeladene Bilder und den Verlauf der Diagramme – alles für eine neue Installation. Alte .json-Sicherungen und Profile lassen sich weiter einspielen.",
    wirklichEinspielen: "Einstellungen und Streamliste werden ersetzt. Fortfahren?",
    kat: { safari: "Safari Afrika", affen: "Affen", meer: "Unterwasser & Meer", vogel: "Vögel", baer: "Bären, Wölfe, Eisbären",
           wald: "Wald & Wildtiere", zoo: "Zoo & Exoten", neu: "Neu gefunden",
           stadt: "Städte & Plätze", strand: "Strände & Küsten", berge: "Berge & Ski", hafen: "Häfen & Schiffe",
           flug: "Flughäfen & Flugzeuge", bahn: "Züge & Bahn", weltraum: "Weltraum & Erde", natur: "Naturschauspiele" },
    katGruppe: { tiere: "Tiere", themen: "Weitere Themen" },
    katText: "Hier legst du fest, was eine Kategorie ausmacht: eigene YouTube-Suchbegriffe, Wörter, die im Titel stehen müssen, und ob Tag/Nacht am Ort zählt. Gefundene Tier-Streams werden über die Wörter einsortiert (erste passende Kategorie, sonst „Neu gefunden“). Ein- und ausschalten geht für alle Fernseher oder je Fernseher.",
    katNeu: "Neue Kategorie", katEigene: "eigene", katGeaendert: "geändert", katNamePflicht: "Name (Pflicht)", katGruppeWahl: "Gruppe",
    katNeuText: "Hier landen gefundene Tier-Streams, die zu keiner Kategorie passen. Sie hat keine eigene Suche.",
    katWo: "Eingeschaltet", katAlle: "Für alle Fernseher", katStreams: (n) => `${n} Streams`, katEinStream: "1 Stream",
    katAusAlle: "aus", katAusBei: (l) => `aus bei ${l}`, katMitSuche: (n) => n === 1 ? "1 Suchbegriff" : `${n} Suchbegriffe`, katNameFeld: "Name",
    katBegriffe: (n) => `Suchbegriffe (je Zeile einer, höchstens ${n})`,
    katBegriffeTiere: "Leer = nur die allgemeine Tiersuche (Seite Suche) füllt diese Kategorie. Jeder Begriff ist eine Anfrage bei YouTube pro Suchlauf.",
    katBegriffeThemen: "Jeder Begriff ist eine Anfrage bei YouTube pro Suchlauf. Gesucht wird nur, solange die Kategorie für alle Fernseher eingeschaltet ist.",
    katWoerter: "Wörter im Titel (je Zeile eines, reguläre Ausdrücke erlaubt)",
    katWoerterTiere: "Ein Wort muss im Titel stehen. Sortiert auch Funde der allgemeinen Tiersuche hierher.",
    katWoerterThemen: "Ein Wort muss im Titel stehen. Leer = jeder Titel (außer Musik, Spiele u. Ä.).",
    katOhneTag: "Tag/Nacht am Ort egal", katOhneTagWoerter: "Tag/Nacht egal nur bei diesen Wörtern im Titel",
    katStreamsZeigen: "Streams zeigen", katStandard: "Auf Standard zurücksetzen",
    katVerschieben: (n) => n ? `${n} Streams verschieben nach` : "Löschen", katWirklich: "Endgültig löschen",
    kategorienWoanders: "Kategorien ein- und ausschalten und bearbeiten:",
    aufgabe: { streamliste: "Streamliste prüfen", suche: "Neue Streams suchen", wache: "Qualität messen" },
  },
  en: {
    reiter: { uebersicht: "Overview", fernseher: "TVs", player: "Players", layout: "Layout", quellen: "Data sources", streams: "Streams", kategorien: "Categories", radio: "Radio", einspieler: "Clips", anzeige: "Display",
              video: "Rotation & quality", suche: "Search", verbindung: "Connection", medien: "Media", updates: "Updates", sicherung: "Backup",
              allgemein: "General", ha: "Home Assistant", benachrichtigung: "Notifications", zugang: "Access", leistung: "Performance", pult: "Announcements", protokoll: "Log", ki: "AI assistants", fern: "Remote sites" },
    pu: { titel: "Announcement panel", text: "A separate page, e.g. for the reception: only messages and announcements to chosen TVs – no settings. Address:",
          stimme: "Voice", stimmeText: "Speech is generated offline on this server (Piper). Voices are downloaded once (approx. 90 MB including the program).",
          geladen: "downloaded", nichtGeladen: "not downloaded", laden: "Download voice", laedtGerade: "downloading …", vorlesen: "Read announcements aloud",
          gong: "Chime before the announcement", dauer: "Default display time (s)", zugaenge: "Accounts", zugangText: "Each account has its own password and may only reach the ticked TVs (none ticked = all).",
          name: "Name", pwNeu: "new password", pwGesetzt: "password set", pwFehlt: "no password yet", zugangNeu: "Add account",
          entfernen: "Remove", vorlagen: "Templates", vorlagenText: "One template per line; “…” marks the gap for the name.",
          art: { weiblich: "female", "männlich": "male" }, probe: "Test announcement", probeOk: "Test announcement sent", tonHinweis: "TVs with a panel account record real sound (for reading aloud).",
          darfAlarm: "may trigger the emergency screen",
          recht: { meldung: "may send ticker messages", layout: "may switch the layout for a while", schalten: "may switch TVs on and off (HA)" } },
    al: { titel: "Emergency screen", text: "Shows a text in red across the whole screen – above any layout, also at night (“black”); switched-off TVs are switched on via Home Assistant (TVs → “Switch via HA”). Stays until someone ends it (admin, panel or webhook).",
          vorlagen: "Templates (one per line)", ton: "Warning tone every 10 seconds (audible on TVs with sound or panel read-aloud)", an: "Trigger now", aus: "End", alle: "all TVs",
          wirklich: "Really show the emergency screen on the TVs now?", laeuft: (z, v) => `Emergency screen showing since ${z} (${v === "Verwaltung" ? "admin" : v})`,
          webhook: "Via webhook (key from “Message via webhook”):", beendet: "Emergency screen ended", ausgeloest: "Emergency screen triggered" },
    lt: { server: "Server: rendering and encoding", serverText: "Measures for 10 seconds how smoothly SignageCast renders and encodes the picture – best while the stuttering TV is running.",
          start: "Start test (10 s)", laeuftTest: "Test running …", system: "System", cpu: "CPU", kerne: "cores", ram: "Memory free", gpu: "Graphics unit",
          seite: "Frames/s TV page", kodierung: "Frames/s encoding", tempo: "Speed", verloren: "dropped/duplicated", cpuKette: "CPU (cores)", aus: "not running",
          ziel: "Target: 25 frames/s, speed 1.0×", tonNeu: "Restart sound and stream", tonNeuText: "Helps when the capture duplicates many frames (stutter although the page renders smoothly). The TVs go black briefly.", tonNeuOk: "Sound and stream are restarting", geraet: "Test on the playback device", geraetText: "Transfer and playback can only be measured on the device that stutters. Open this address there in the browser (same network):",
          letzteGeraete: "Results from devices", keine: "none yet", empfehlungen: "Recommendations",
          empf: {
            keine_kette: () => "No TV is running right now. Open the stream on the TV (or in a browser) first, then test.",
            seite_langsam: (p) => `“${p.tv}”: the TV page reaches only ${p.fps} frames/s (target 25). The layout is too heavy for the CPU – web page, camera and chart elements cost the most. Simplify the layout, run fewer TVs at once or give the container more cores.`,
            kodierung_langsam: (p) => `“${p.tv}”: encoding runs at only ${p.tempo}× real time. ${p.aufloesung === 2160 ? "Set the output to Full HD or " : ""}lower the bitrate; with several TVs the graphics unit is at its limit.`,
            bilder_verloren: (p) => `“${p.tv}”: ${p.n} frames dropped or duplicated – rendering cannot keep up. Usually CPU load (see above).`,
            ton_doppelt: (p) => `“${p.tv}”: ${p.n} frames duplicated although the page renders smoothly – the capture gets too little CPU time (e.g. other guests on the same host) or the graphics unit is at its limit. Remedy: give the container priority (Proxmox: cpuunits), Full HD output; once: “Restart sound and stream”.`,
            cpu_hoch: (p) => `CPU at ${p.cpu} % (${p.kerne} cores, ${p.ketten} TVs). Plan about 1 core per TV – assign more cores in Proxmox or run fewer TVs at once.`,
            cpu_knapp: (p) => `CPU at ${p.cpu} % (${p.kerne} cores, ${p.ketten} TVs) – little headroom. Another TV or a heavy layout may cause stutter.`,
            ram_knapp: (p) => `Only ${p.frei} MB memory free. Plan about 0.9 GB per TV – give the container more memory.`,
            gpu_hoch: (p) => `The graphics unit runs at ${p.gpu} % of its maximum clock – close to the limit. Lower bitrate or resolution.`,
            software: () => "No graphics unit – video is encoded by the CPU (Full HD, H.264 only). For 4K or several TVs pass the Intel/AMD graphics through to the container.",
            mediamtx_langsam: (p) => `MediaMTX discarded frames ${p.n} times in the last 10 minutes (“reader is too slow”) – visible as a jump of about one second. Remedy: update to SignageCast 0.19.2 (larger queue) or Full HD output / lower bitrate.`,
            server_ok: () => "Server is fine: rendering and encoding keep up with real time. If it still stutters, transfer or the playback device is the cause – test on the device (below).",
          } },
    as: { titel: "Welcome to SignageCast", schritt: (n) => `Step ${n} of 5`, sprache: "Language of the admin and the TVs",
          ort: "Where is the TV? The place sets weather, sun times and warnings.", ha: "Connect Home Assistant (optional) – for values from your home. The guide is under Settings → Home Assistant afterwards.",
          weg: "How does the picture get onto the TV?", wege: {
            browser: ["TV browser", "Smart TV, Fire TV, Android TV box or a tablet: one address as start page."],
            pi: ["Raspberry Pi", "For TVs without a usable browser: write a ready image to an SD card, connect via HDMI."],
            pc: ["PC", "Mini PC or old laptop: write a ready image to a USB stick, starts straight into the display."] },
          fertig: "Done! Open this address in the TV's browser and set it as start page:", fertigText: "Everything else – layout, streams, radio, more TVs – is in the areas above.",
          fertigPlayer: "Done! Now add the player: create the image, write it, plug it in – it then shows up under “Players” by itself.",
          zumPlayer: "Add player", lokal: "The TV cannot reach “localhost” – use this computer's IP in your home network (Docker: set SC_HOST_IP).",
          mehr: "Also possible", mehrListe: { fern: "Remote sites – players in other places via Tailscale or Headscale", ki: "AI assistants – Claude & co. build layouts and write tickers", pult: "Announcement desk – a page just for messages, e.g. at the reception" },
          weiter: "Next", zurueck: "Back", ueberspringen: "Skip", spaeter: "Set up later", los: "Go to overview" },
    pl: { titel: "Players: Raspberry Pi, PC or browser", zitat: (s) => `“${s}”`, text: "A Raspberry Pi at the TV shows the stream via HDMI – also on TVs without a usable browser. Create a ready image here, write it to an SD card, plug it in – done. Afterwards you manage all Pis here.",
          modelle: "Pi 5, Pi 4, Pi 400: up to 4K (H.265). Pi 3 and Zero 2 W: Full HD with H.264 only – then set the TV to codec “H.264” and resolution “Full HD”.",
          ram: "Memory: 1 GB is enough for the stream (Zero 2 W: 512 MB). Direct mode needs at least 2 GB, better 4 GB – especially with videos, cameras, web pages or 4K output; with write protection everything the browser stores is kept in memory too. Estimates, not yet measured on real Pis.",
          bedarf: "You also need: SD card of 8 GB or more (brand card, A1/A2), for direct mode a Pi 4/5 with at least 2 GB (better 4 GB), official power supply, HDMI cable (Zero 2 W: mini HDMI). To write the card: Raspberry Pi Imager or balenaEtcher.",
          experimentell: "New in 0.23 and still experimental: image building and management are tested, playback on real Pis not yet on all models. Since 0.24 a Pi 4/5 can also show the page directly (Settings → Display).",
          basis: "Player image", basisFehlt: "not downloaded yet – about 850 MB once", basisLaden: "Download player image", basisNeu: "Download again",
          basisLaedt: (a, b) => `downloading … ${a} of ${b} MB`, basisBereit: (v, d) => `version ${v} from ${d} – ready`, basisFehler: "Download failed",
          port: (p) => `The Pis reach the server on port ${p} – with Docker/NAS it must be published (line "${p}:${p}" under ports).`,
          koppeln: "Pair a player (one image for several devices)", koppelnText: "One image for any number of Pis or PCs: it contains the server address and Wi-Fi, but no key yet. At startup each device shows a 6-digit code on the TV – enter it here, choose name and TV, done. The key is negotiated securely and never travels over the network.",
          sammelImage: "Download image for several devices", fuer: "For", code: "Code from the TV", codePlatz: "123 456", koppelnKnopf: "Pair",
          gekoppelt: "Paired – the Pi starts in a few seconds.", wartend: (n) => n === 1 ? "1 Pi is showing a code" : `${n} Pis are showing a code`,
          keinerWartet: "No Pi is showing a code right now.",
          neu: "Add player", name: "Name", namePlatz: "e.g. waiting room", tv: "Shows the TV", keinTv: "– none yet –", modell: "Model",
          m: { pi45: "Pi 5, Pi 4 or Pi 400", pi3: "Pi 3 or Zero 2 W" }, netz: "Network", kabel: "LAN cable", wlan: "Wi-Fi",
          wlanGesp: "Saved Wi-Fi", wlanNeu: "enter new Wi-Fi", ssid: "Wi-Fi name (SSID)", pw: "Wi-Fi password", merken: "Save the Wi-Fi in the admin (for more Pis)",
          merkenText: "Only the WPA key is stored, not the password itself. It still grants access to the Wi-Fi – backups contain it only “with credentials”.",
          erweitert: "Advanced", server: "Server address for the Pis", serverText: "Empty = automatic. Change it if the Pis reach the server under a different address (e.g. other port in a container).",
          streamPort: "Stream port from outside", streamPortText: "Empty = as configured. Only needed if the container maps the stream port to a different port.",
          gespeicherte: "Saved Wi-Fi networks", vergessen: "Forget", erstellen: "Create and download image", laedtHerunter: "Download starting …",
          schritte: "Next steps", s1: "Open Raspberry Pi Imager → choose device → operating system: at the bottom “Use custom” → the downloaded file → SD card → Next.",
          s2: "If the Imager asks about “OS customisation”: No – everything is already in the image. (balenaEtcher: choose file, choose card, Flash.)",
          s3: "Put the card into the Pi, HDMI to the TV, power on. The first start takes 2–3 minutes (the Pi restarts once), then the picture appears.",
          s4: "If the Pi finds no network, after 2 minutes it opens a hotspot and shows a QR code on the TV – scan it with your phone and choose the Wi-Fi.",
          liste: "Players", keine: "No player yet.", online: "online", offline: "offline", nieGesehen: "has never reported",
          zuletzt: (z) => `last seen ${z}`, seit: (z) => `since ${z}`, ip: "IP", netzArt: { kabel: "cable", wlan: "Wi-Fi", hotspot: "hotspot (setup)", keins: "no network" },
          temp: "Temperature", version: "Player", hdmi: "Screen", keinHdmi: "no screen detected", video: "Video",
          zustand: { start: "starting", fern_link: "waiting for approval in Tailscale", koppeln: "waiting for pairing", spielt: "playing", verbinde: "connecting …", kein_tv: "no TV assigned", aus: "screen off (schedule)",
                     stream_fehler: "stream error", gesperrt: "removed", unbekannt: "unknown to the server", direkt: "shows the page directly", direkt_start: "browser starting …" },
          drehung: "Rotation", aufloesung: "Output", a: { auto: "as the TV reports", "720": "720p", "1080": "Full HD", "2160": "4K" },
          lautstaerke: "Volume (%)", cec: "Switch the TV on and off by schedule (HDMI-CEC)", cecText: "When the layout is “black” (schedule of the TV), the Pi switches the TV off via HDMI and on again later. CEC must be enabled on the TV (Samsung “Anynet+”, LG “SimpLink”, Sony “Bravia Sync”).",
          schreibschutz: "Write protection (recommended)", schreibschutzText: "The system runs in memory, the SD card stays unchanged – power cuts and unplugging do not harm it. Changing it restarts the Pi.",
          systemupdate: "System updates", su: { woechentlich: "weekly (Sun 3 am)", aus: "manual only" }, hwdec: "Video decoding", hw: { auto: "hardware (default)", aus: "CPU only (on picture errors)" },
          anzeige: "Display", am: { stream: "stream from the server (default)", direkt: "direct: the Pi shows the page itself (experimental)" },
          anzeigeText: "Direct: the Pi opens the TV page itself in a browser – sharp, without delay, and the server does not need to encode anything for this Pi. The Pi draws in Full HD (4K TVs upscale). Pi 4/5 with at least 2 GB of memory only (better 4 GB); videos and cameras may stutter. If the browser has problems, the Pi uses the stream for one hour.",
          direktModus: "direct mode (browser)",
          b: { bild: "Screenshot", erkennen: "Show name", cec_an: "TV on", cec_aus: "TV off", player_neu: "Restart player", neustart: "Restart Pi",
               systemupdate: "System update now", protokoll: "Fetch log" },
          bText: { erkennen: "Shows name and IP on the TV for 30 seconds – so you find the right Pi.", systemupdate: "The Pi installs updates (write protection off for a moment) and restarts twice – about 5–15 minutes." },
          wartet: (a) => `waiting for the Pi: ${a}`, ergebnis: "Last", ok: "ok", fehlgeschlagen: "failed",
          vor: (t) => `last report ${t} ago`,
          fv: { titel: "Remote management", unterwegs: (n) => `${n} on the way`, zuletzt: (w, z) => `last: ${w} ${z}`, leer: "Nothing sent to this player yet.",
            text: "Everything sent to this player: sent → picked up by the player (it reports every 15 s) → result. The last 20 entries.",
            wartet: "waiting for the player", offline: "not picked up yet – is the player online?", abgeholt: (s) => `picked up after ${s}`,
            umsetzen: "being applied …", uebernommen: "applied", ok: "done", fehler: "failed", auto: "automatic",
            terminal: "Terminal", laeuft: "running",
            e: { tv: "TV", anzeige_modus: "Display", drehung: "Rotation", aufloesung: "Output", lautstaerke: "Volume", hwdec: "Video decoding",
                 schreibschutz: "Write protection", wlan: "Wi-Fi" },
            modus: { stream: "stream", direkt: "direct" }, an: "on", aus: "off",
            h: { ersetzt: "replaced by a newer change", dienst_neu: "dropped – SignageCast restarted before the player picked it up",
                 keine_bestaetigung: "no confirmation from the player", kein_browser: "the image has no browser – stays on the stream",
                 rueckfall: "the browser had problems – stream for 1 hour", nur_stream: "Pi 3/Zero 2 W: stays on the stream",
                 nicht_erreichbar: "server not reachable with it – back to the previous Wi-Fi", kabel: "on cable – Wi-Fi saved but not tested",
                 pc_image: "PC: updates come with a new image", unbekannt: "the agent does not know this command" },
            modusOk: (m) => `player now shows ${m}` },
          fw: { knopf: "Terminal", knopfText: "Shell (root) on this Pi in the browser – like the terminal in Cockpit",
            aus: "Remote maintenance is off on this Pi. To switch it on: tick it when creating the image, or on the Pi’s setup page.",
            alt: "The agent on this Pi cannot do remote maintenance yet – it updates itself at its next report.",
            laeuft: (seit, wer) => `Remote maintenance running since ${seit} (${wer})`,
            image: "Allow remote maintenance (terminal from the admin, root)",
            imageText: "Off by default. The player only accepts a session if this or its setup page switched it on – so even someone who takes over the server cannot get onto players that do not allow it.",
            titel: (n) => `Terminal – ${n}`, schliessen: "End session", zu: "Close", verbinde: "Connecting to the Pi … (up to 15 s)", verbunden: "connected",
            beendet: (g) => `Session ended: ${g}`,
            schreibschutz: "Write protection is on: changes are gone after a restart – switch it off in this Pi’s settings first.",
            hinweis: "The TV shows “Remote maintenance active” meanwhile. The session ends after 10 min without input or after 60 min at the latest.",
            protokoll: "Recent remote sessions", verloren: "… (older output skipped)",
            gruende: { verwaltung: "ended", leerlauf: "10 min without input", zeitgrenze: "60 min reached", verwaltung_weg: "window closed",
              pi_antwortet_nicht: "the Pi did not respond", neue_sitzung: "new session", geraet_entfernt: "Pi removed",
              pi_beendet: "shell ended (exit)", pi_leerlauf: "10 min without input", pi_zeitgrenze: "60 min reached",
              pi_abgeschaltet: "switched off on the Pi", unbekannt: "session unknown" } },
          protokollZeigen: "Show log", wlanAendern: "Change Wi-Fi", wlanAendernText: "The Pi tries the new Wi-Fi. If it cannot reach the server with it, it returns to the previous one. Previous networks stay as fallback.",
          wlanOffen: (s) => `Wi-Fi change to “${s}” is waiting for the Pi`, wlanSenden: "Send to the Pi", wlanGesendet: "Sent – the Pi applies it at its next report",
          imageNeu: "Download image again", imageNeuText: "For a new SD card. The key stays the same – an old card with this player keeps working.",
          entfernen: "Remove", entfernenFrage: (n) => `Remove player “${n}”? Its key becomes invalid; the Pi then only shows a note.`,
          befehlOk: "Command sent – the player picks it up within a few seconds", bildAlt: (z) => `Screenshot from ${z}`, netzwerke: "Wi-Fi networks on the player",
          update: "Last system update",
          h: { pi_kein_tv: "No TV assigned – the Pi only shows a note.", pi_h265: "Pi 3/Zero 2 W cannot play H.265 smoothly: choose codec “H.264” for the TV.",
               pi_4k: "Pi 3/Zero 2 W cannot do 4K: choose resolution “Full HD” for the TV.", pi5_h264_4k: "The Pi 5 decodes H.264 on the CPU only – 4K stutters. Choose “H.265” or “Full HD” for the TV.",
               pi_strom: "The Pi reports under-voltage or throttling – use the official power supply.", pi_heiss: "The Pi is very warm (above 80 °C) – use a case with cooling or a fan.",
               pi_kein_hdmi: "No screen detected – check the HDMI cable (Pi 4/5: use the port next to the power).",
               pi_direkt_pi3: "Direct mode needs a Pi 4 or Pi 5 – this Pi shows the stream.",
               pi_direkt_kein_browser: "This Pi’s image has no browser yet (created before 0.24): download and flash a new image for direct mode. Until then it shows the stream.",
               pi_direkt_ram: "This Pi has less than 2 GB of memory – tight for direct mode (with write protection the browser and its cache are kept in memory). If the page stutters or restarts: set the display to “stream” or use a Pi with 4 GB.",
               pi_direkt_rueckfall: "The browser had problems – the player shows the stream for one hour. “Restart player” tries again right away.",
               pc_kein_bildschirm: "No screen detected – check the cable (HDMI, DisplayPort) and switch the screen on.",
               pc_ist_pi: "This device reports as a Raspberry Pi – set the model to the matching Pi in the settings.",
               pi_ist_pc: "This device reports as a PC – set the model to “PC” in the settings." },
          pc: { titel: "PC as player (since 0.36, experimental)",
            text: "An ordinary PC, mini PC or thin client (x86-64 with UEFI) becomes a player: it starts from a USB stick without changing anything on its disk and shows the page itself in direct mode – sharp, without delay, and the server encodes nothing for it. You manage it here like a Pi.",
            bedarf: "You need: 64-bit PC with UEFI (about 2013 or newer; Secure Boot may stay on), at least 4 GB of memory, Intel or AMD graphics (NVIDIA works, but videos without hardware decoding), USB stick of 4 GB or more, LAN cable or Wi-Fi. No HDMI-CEC (TV on/off) and no system updates – new software comes with a new image.",
            basis: "PC image", basisFehlt: "not downloaded yet – about 1 GB once",
            format: "Format", f: { gz: "USB stick (.img.gz – balenaEtcher, Raspberry Pi Imager, Rufus)", iso: "ISO (.iso, uncompressed – Ventoy, CD, virtual machine)" },
            formatText: "Both are the same system. From a USB stick the PC keeps pairing, Wi-Fi and player updates on the stick; from CD or Ventoy only until the next restart (the settings come from the server anyway).",
            s1: "Write the USB stick with balenaEtcher, Raspberry Pi Imager (“Use custom”) or Rufus – when Rufus asks for the mode, choose “DD image”. Ventoy: just copy the .iso to the stick.",
            s2: "Plug the stick into the PC, connect the screen, switch on and start from the stick (boot menu usually F12, F11, F8 or Esc; otherwise put USB first in the UEFI setup).",
            s3: "The first start takes 1–2 minutes, then the page appears. Nothing changes on the PC’s disk.",
            s4: "With a LAN cable there is nothing else to do. With Wi-Fi: if the PC finds no network, after 2 minutes it opens a hotspot (if its Wi-Fi card can) and shows a QR code.",
            live: "Live system: runs write-protected (power cuts do no harm). There are no system updates – for new software use “Download image again” and rewrite the stick.",
            neustart: "Restart PC", m: "PC (x86-64, UEFI) – experimental" },
          br: { m: "Browser device (link only, no image)", titel: "Browser device",
            text: "For devices that already have a browser: smart TV, Fire TV stick, a PC with a ready kiosk live CD (e.g. Porteus Kiosk) or just a browser in full screen (F11). There is no image – you get a secret link that shows exactly this TV. No screenshot, no fallback to the stream, no remote maintenance; “online” means: the page fetches its data (every 15 s).",
            erstellen: "Create link", link: "Link", kopieren: "Copy", kopiert: "Copied",
            neu: "Create new link", neuFrage: "Create a new link? The current one stops working immediately – devices using it show an error until the new one is entered.", neuOk: "New link created",
            linkText: "Set it as the start page in the device’s browser (kiosk CD: as start address). Whoever knows the link sees this TV – not the admin. Treat it like a password; port 8890 is unencrypted HTTP, so only use it in your own network." } },
    fern: { titel: "Players at another site", text: "A Pi or PC at another place (office, holiday flat, branch) reaches SignageCast through Tailscale. No port is opened on any router; display, commands and the terminal work as at home.",
          link: { s1: "1. Tailscale on this server", s2: "2. Connect your Tailscale account", s3: "3. Switch on",
                  einrichten: "Set up Tailscale", einrichtenText: "Installs Tailscale from the official package archive (about 1 minute).", laeuft: "setting up …",
                  fehler: { kein_tun: "This container has no /dev/net/tun. Run once on the Proxmox host (container ID instead of <ID>), then here again:", schluessel: "The signing key of Tailscale does not match – stopped.", installation: "Installation failed – internet reachable?", operator: "Tailscale runs but does not let SignageCast log in." },
                  container: "In a container: install Tailscale on the host and log in there – see the guide. Then “Switch on” under advanced (with the address).",
                  verbinden: "Connect to Tailscale", verbindenText: "Opens the Tailscale login in a new window – log in and confirm. This page notices by itself.",
                  oeffnen: "Open login link", wartet: "Waiting for the login …",
                  verbunden: (n, ip, k) => `Connected as “${n}” (${ip})${k ? " · " + k : ""}`,
                  einschalten: "Switch on remote sites", an: "Switched on – tick “At another site” for a player.", aus: "Switch off" },
          erweitert: "Advanced: OAuth client or Headscale",
          anleitung: "Guide", art: "Service", arten: { aus: "off", link: "Tailscale – login link", tailscale: "Tailscale – OAuth client", headscale: "Headscale (self-hosted)" },
          server: "SignageCast in the tailnet", serverText: "The tailnet IP of this server (100.x.y.z). Tailscale must run here – see the guide.", vorschlag: (ip) => `Detected: ${ip} – use it`,
          clientId: "OAuth client ID", clientSecret: "OAuth client secret", clientText: "In the Tailscale admin under Settings → Trust credentials → create an OAuth client: scopes “Auth Keys: Write” and “Devices Core: Write”, tag as below.",
          url: "Headscale address", apiKey: "API key", apiText: "headscale apikeys create --expiration 365d", benutzer: "User ID (optional)",
          tag: "Tag of the players", tagText: "The players get this tag. In the access rule it may only reach SignageCast.",
          pruefen: "Check connection", geprueft: (n, name) => n == null ? `Connection ok – SignageCast is in the tailnet as “${name}”.` : `Connection ok – ${n} devices in the tailnet, SignageCast found as “${name}”.`,
          regel: "Access rule – recommended", regelText: "Without a rule every device in Tailscale may reach every other one – a player in someone else's rooms could reach all your devices. With this rule players only reach SignageCast, your own devices still everything. Copy, paste into the rule editor (if you already have rules, add just these parts), save.",
          kopieren: "Copy", kopiert: "Copied", editor: "Open the Tailscale rule editor",
          box: "At another site (through Tailscale)", boxHs: "At another site (through Headscale)",
          boxText: (ip) => `On its first start the player joins the tailnet with a one-time key (valid 7 days) and talks to SignageCast at ${ip}. Only with the image for exactly this device.`,
          boxLink: "On its first start the player logs in by link: while it is still here, its card shows “Approve player”; at the other site the TV shows a QR code. Only with the image for exactly this device.",
          freigeben: "Approve player (Tailscale)", freigebenText: "Opens Tailscale – log in and confirm. The player then connects by itself.",
          ohneTag: "Logged in without tag: the access rule is missing – this player can reach all devices in your tailnet, and its login expires after 180 days. Add the rule (Settings → Remote sites), then a new image.",
          zeile: "Other site", wartet: "Image created – not joined yet", direkt: "direct", relay: (r) => `through relay ${r}`,
          fehler: { fehlt: "Image before 0.41 without Tailscale – create a new image", abgemeldet: "logged out of the tailnet – create a new image", startet: "starting …" },
          entfernt: "Player removed – also from the tailnet", nichtGefunden: "Player removed – not (or no longer) found in the tailnet",
          entferntLink: "Player removed – it logs itself out of Tailscale at its next contact. If it is no longer reachable, delete it in Tailscale under Machines.",
          entferntFehler: (t) => `Player removed, but not from the tailnet: ${t} – please delete it there by hand`,
          userspace: "Tailscale runs in userspace mode on this server. Then the admin is reachable from the tailnet without login – remote sites stay blocked. Please set up /dev/net/tun and switch userspace mode off (guide)." },
    ki: { titel: "AI assistants in your home network", text: "Claude or another AI assistant manages the content directly: build and change layouts, look at a preview, ticker, announcements, streams. Every computer gets its own access, which you can remove here at any time – it stops working immediately. Home network only; every change is in the log (“MCP <computer>”).",
          liste: "Connected computers", keine: "No computer connected yet – the interface is off.", name: "Name of the computer", programm: "Program", recht: "May",
          rechte: { aendern: "change content", lesen: "only read" }, arten: { desktop: "Claude Desktop", code: "Claude Code", cursor: "Cursor", vscode: "VS Code" },
          zuletzt: "Last used", nie: "never", wartet: "waiting for the first start of the file (valid 1 hour)", abgelaufen: "File not started in time – remove and connect again",
          entfernen: "Remove", entfernenFrage: (n) => `Remove computer “${n}”? The AI assistant there loses access immediately.`, entfernt: "Removed – no more access",
          neu: "Connect a computer", adresse: "Address of this machine", adresseText: "How the computer reaches SignageCast in your home network (IP or name).", verbinden: "Connect",
          namePlatz: "e.g. office laptop", keinHttps: "Claude Desktop needs a certificate (openssl), which is missing – please choose Claude Code, Cursor or VS Code, or connect via SSH.",
          fertig: (n) => `“${n}” has been added.`,
          desktop: ["The file has been downloaded – double-click it (or in Claude Desktop: Settings → Extensions → drag it in) and choose “Install”.",
                    "Start Claude Desktop or enable the extension within one hour – on its first start it connects and then stays set up.",
                    "Ask, e.g.: “Show me the status of SignageCast and a preview picture.”"],
          desktopSicher: "Encrypted (HTTPS); the file trusts only this SignageCast. It contains no permanent key – after the first start it is worthless.",
          nochmal: "Download the file again",
          befehl: "Run in a terminal:", link: "Open in Cursor", linkText: "Cursor asks and adds the server. Or copy the entry for mcp.json:",
          einmal: "The key is shown only now. Whoever has it can change the content – do not share it; if it is lost, remove the computer.",
          unverschluesselt: "These programs connect unencrypted in your home network (like the panel) – use them only in a trusted network. Encrypted: Claude Desktop or SSH (see guide).",
          vscodeWin: "Windows PowerShell swallows quotes – there, better copy the entry into mcp.json:",
          kopieren: "Copy", kopiert: "Copied", anleitung: "Guide (also connecting via SSH)" },
    prot: { titel: "Change log", text: "Who changed what and when – in the admin, at the panel, via webhook or by SignageCast itself. Only the kind and area are recorded, no values (no passwords, no announcement texts). The last 500 entries; part of the backup.",
            quelle: "Origin", alle: "all", zeit: "Time", wer: "Who", was: "What", leer: "No entries yet.", mehr: "Show older",
            quellen: { verwaltung: "Admin", pult: "Panel", webhook: "Webhook", system: "SignageCast" }, befund: { schwarz: "only black", steht: "picture frozen" },
            layouts: { neu: "new layouts", geaendert: "layouts changed", geloescht: "layouts deleted" },
            bereich: { fernseher: "TVs", layouts: "Layouts", video: "Video", medien: "Media", quellen: "Data sources", radio: "Radio", einspieler: "Clips",
                       kategorien: "Categories", standort: "Location", anzeige: "Display", ha: "Home Assistant", benachrichtigung: "Notifications",
                       sicherung: "Backup", pult: "Announcement panel", alarm: "Emergency screen", webhook: "Webhook", stream: "Stream", sprache: "Language", updates: "Updates" },
            aktion: { einstellungen: "Settings saved", webhook_neu: "new webhook key", medien_neu: "Medium uploaded", medien_loeschen: "Medium deleted",
                      schalten: "TV switched", nach_einschalten: "Source/page tried on the TV", update: "Update requested",
                      update_ergebnis: "Update", sicherung_erstellen: "Backup created", sicherung_loeschen: "Backup deleted",
                      sicherung_einspielen: "Backup restored", quelle_datei: "File for data source uploaded", kategorie_loeschen: "Category deleted",
                      stream_neu: "Stream added", suche: "Search started", radio_neu: "Radio station added", seite_neu_laden: "TV page reloaded",
                      kette_neu: "Playback restarted", ton_neu: "Sound and stream restarted", layout_wiederherstellen: "Layout version restored",
                      stimme_laden: "Voice downloaded", probedurchsage: "Test announcement", einspieler_jetzt: "Clip shown now", stream_freigeben: "Rejected stream released",
                      alarm_an: "Emergency screen triggered", alarm_aus: "Emergency screen ended", durchsage: "Announcement sent", meldung: "Ticker message sent",
                      meldung_aus: "Ticker message ended", layout: "Layout switched", layout_aus: "Layout switched back",
                      internet_weg: "Internet not reachable since", internet_wieder: "Internet back (outage)",
                      bild_neu_laden: "Picture check: TV page reloaded", bild_kette_neu: "Picture check: playback restarted",
                      ki_neu: "Computer for AI assistants connected", ki_entfernen: "Computer for AI assistants removed", ki_gekoppelt: "Claude Desktop connected", fernnetz: "Remote sites changed",
                      "stream_*": (a) => `Stream: ${{ aendern: "changed", entfernen: "removed", zeigen: "shown now", "strikes-zuruecksetzen": "strikes reset" }[a] || a}`,
                      "radio_*": (a) => `Radio station ${a === "entfernen" ? "removed" : "changed"}`,
                      "player_*": (a) => `Player: ${{ neu: "created", koppeln: "paired", einstellungen: "settings", wlan: "Wi-Fi", image: "image created", entfernen: "removed", aendern: "changed", befehl: "command", "link-neu": "new link" }[a] || a}`,
                      "terminal_*": (a) => a === "start" ? "Terminal opened" : "Terminal closed" } },
    internet: "Internet", online: "reachable", offline: "not reachable", onlineText: "Live cams are running",
    offlineSeit: (z) => `since ${z} – the TVs show own media or a fallback picture`,
    bildBefund: { schwarz: "Picture check: shows only black", steht: "Picture check: picture frozen" },
    pultLayout: (n, bis, von) => `Layout “${n}” from the panel (${von}) until ${bis}`,
    todoTitel: "To do", todoOk: "All good.",
    todoAus: { tipp: "Hide (for good, until you show it again)", update: "Hide (until the next version)",
               warn: "Hide (until the problem was solved once – if it comes back, it shows again)" },
    todoVersteckt: (n) => `${n} hidden – show`, todoVerbergen: "Hide the hidden ones",
    todoEin: "Show again", todoAusgeblendet: "hidden",
    todo: { internet: (s) => `Internet not reachable since ${s} – the TVs show own media or a fallback picture`,
            bild: (n, b) => b === "steht" ? `Picture of “${n}” was frozen – page reloaded or playback restarted` : `“${n}” showed only black – page reloaded or playback restarted`,
            player: (n) => `Player “${n}” is not responding`, update: (v) => `New version ${v} available`, ha: "Home Assistant is not reachable", wetter: "Weather could not be loaded",
            sicherung: "Automatic backup is switched off", sicherungFehler: "Last automatic backup failed",
            benachrichtigung: "No notification set up yet (e.g. on failure)", bnFehler: "A notification could not be sent",
            software: "No graphics unit found – video is encoded in software", passwort: "Change the initial password",
            bildrate: (n) => `“${n}” stutters: too few frames/s – run the performance test`,
            allgemein: (g, seit) => `Since ${seit} all streams fail (${{ aufloesung: "resolution too low", puffert: "buffering", steht: "picture frozen", fehler: "error", startet_nicht: "does not start" }[g] || g}) – no strikes, probably a YouTube or browser problem`,
            doppelt: (n) => `“${n}” stutters: capture duplicates frames – “Restart sound and stream” in the performance test` },
    erweitert: "Advanced", ungespeichert: "not saved", ungespeichertFrage: "There are unsaved changes. Continue anyway?",
    bereiche: { uebersicht: "Overview", fernseher: "TVs", inhalte: "Content", videoton: "Live videos", einstellungen: "Settings", system: "System" },
    fernseherText: "Each TV opens its own address in the browser and can have its own sound, station and categories.",
    adresse: "Address on the TV", ton: "Sound", tonArt: { aus: "off", radio: "Radio", tiere: "Original sound of the animal videos" },
    sender: "Station", keinSender: "– choose station –", lautstaerke: "Volume", videoZeigen: "Show live videos",
    kennung: "Identifier (a–z, 0–9, part of the address)", fernseherNeu: "Add TV", fernseherWeg: "Remove TV",
    schalten: "Switch via HA", schaltenText: "The TV's entity in Home Assistant (media_player, switch or remote). When “black” starts in the schedule it is switched off, afterwards on again – only at the change, so switching on by hand stays. Switching on only works if HA can do it (Samsung/LG often only with Wake-on-LAN). Save first, then test.",
    schaltenAus: "Off (test)", schaltenAn: "On (test)", schaltenOk: "Sent to Home Assistant",
    haQuelle: "Select source", quellenHolen: "Get sources from HA",
    quelleText: "Optional, media_player only: e.g. “HDMI 2” (where the player is connected). After switching on (schedule, emergency, test button) SignageCast waits until the TV is ready (up to 90 s), selects the source and then opens the TV page if wanted.",
    quelleNurMp: "Sources exist only for media_player entities", keineQuellen: "Home Assistant reports no sources for this device (often only while it is on).",
    quellenGefunden: (l, a) => `Sources: ${l} – current: ${a}`,
    nachEin: "After switching on", nachTest: "Run now (test)",
    oeffnen: "Then open TV page", haDienst: "HA service",
    oeffnenArt: { "": "no", lg: "LG webOS – browser", android: "Android TV / Google TV / Fire TV (ADB)", eigen: "Own HA service" },
    oeffnenText: {
      lg: (u) => `Opens the TV's browser with ${u} (integration “LG webOS TV”).`,
      android: (u) => `Opens ${u} in the default browser (integration “Android TV” with ADB, not “Android TV Remote”). Better: a kiosk app as default browser.`,
      eigen: (u) => `Calls the service with this data (JSON); {url} becomes ${u}, {entity} the entity. Without entity_id the entity is added. For Samsung e.g. a script in HA.`,
    },
    haZustand: { an: "on", aus: "off", weg: "unreachable", fehler: "HA error" }, geraetHa: "Device (HA)",
    haZustandNoch: "State according to Home Assistant: being queried (once a minute) …",
    haZustandLang: (z, roh, q, zeit) => `State according to Home Assistant: ${z} (${roh}${q ? ", source " + q : ""}), as of ${zeit}.`,
    nachZuletzt: (n) => `Last ${n.zeit}: ${n.fehler ? "not done – " + n.fehler : (n.schritte.length ? n.schritte.map((x) => x === "quelle" ? "source selected" : "page opened").join(", ") : "nothing needed")}`,
    wirklichTvWeg: "Remove this TV? Its address will stop working.", weitererTv: "Another TV",
    tvHinweis: "Sound, station, volume and videos apply immediately; output and bitrate at the next stream start.",
    meineSender: "My stations", keineSender: "No stations yet – load suggestions below or enter your own address.",
    senderNutzung: "Which TV plays which station is set in the “TVs” tab (sound = radio).",
    eigenerSender: "Add your own station", senderAdresse: "Stream address (MP3/AAC, also .m3u/.pls)", senderName: "Name",
    senderAnzeigen: "Show station name on the TV", puffer: "Buffer (lead time)",
    pufferText: "Bridges dropouts of the station up to this length. The radio starts delayed by this time (also when switching stations). 0 = no buffer, directly from the station.", inNaehe: "Stations matching your location", regionWoerter:
      "Additional search words for the region, comma separated", vorschlaegeLaden: "Load suggestions",
    vorschlaegeDauer: "Loading (about 5–15 s) …", gruppe: { naehe: "Nearby / region", region: "State", land: "Whole country" },
    senderSuche: "Search stations by name", suchen: "Search", hinzu: "Add", hinzugefuegt: "Added",
    quelle: "Source: radio-browser.info (free station directory); location: OpenStreetMap.", gefundenFuer: "Searched for",
    playlist: "Paste playlist (M3U/PLS)", playlistText: "Paste the content of an .m3u or .pls file here or choose the file – every entry becomes a station (name from #EXTINF).",
    playlistUebernehmen: "Add stations", playlistPruefen: "Checking the entries …",
    playlistErgebnis: (n, d) => `${n} stations added${d ? `, ${d} already present` : ""}.`,
    ortSuche: "Search place (e.g. Munich)", ortGesetzt: "Location saved", zeigenAuf: "“Show now” on",
    alleTv: "all TVs", tonAnzeige: "Sound",
    epText: "At fixed minutes a clip interrupts the rotation in the video window and plays completely – e.g. the 100-second news on the hour and half hour. With sound, the radio is muted meanwhile.",
    epNeu: "Add clip", epQuelle: "Source", epQuelleArt: { tagesschau100: "tagesschau in 100 Sekunden (always the latest)", video: "Video address (MP4)", youtube: "YouTube video or channel (latest video)" },
    epUrl: "Address / link", epMinuten: "Minutes of the hour", epAndere: "other (e.g. 0,20,40)", epZeit: "only between", epTon: "with sound",
    epFernseher: "TVs (none selected = all)", epAktiv: "active", epJetzt: "Show now", epJetztOk: "Plays on the TV within 15 s",
    epStand: "Version", epFehler: "Error", epKeine: "No clips yet.",
    wetterQuelle: "Weather source", wetterQuelleArt: { met: "Own weather (MET Norway, for the location)", ha: "Home Assistant (weather entity)" },
    metText: "Weather, weather picture and forecast come directly from MET Norway (free, worldwide) for the location (further down on this page) – Home Assistant is not needed for this. The TV shows a small “Weather data: MET Norway” (licence requirement).",
    bnTitel: "Notifications", bnText: "SignageCast reports when a TV fails, an update or backup fails, and when Home Assistant is unreachable for more than 5 minutes – once each, with an all-clear.",
    bnTelegram: "Telegram", bnBotToken: "Bot token", bnChatId: "Chat ID", bnEmail: "E-mail (SMTP)", bnServer: "SMTP server", bnPort: "Port",
    bnSicherheit: "Encryption", bnBenutzer: "User", bnPasswort: "Password", bnAbsender: "Sender", bnEmpfaenger: "Recipients (comma separated)",
    bnHA: "Home Assistant", bnDienst: "Notify service", bnAktiv: "active", bnTest: "Test message", bnTestOk: "Test message sent",
    bnEreignisse: "Notify on", bnEr: { ausfall: "TV failure", update: "Update failed", sicherung: "Backup failed", ha: "Home Assistant disconnected", leistung: "TV stutters (too few frames/s)", internet: "Internet not reachable (all-clear with period)" },
    bnLetzte: "Last sent",
    whTitel: "Message via webhook", whText: "Other systems (e.g. Home Assistant) can put a short message as a banner on the TVs – above any layout. Only with a secret key; the key is shown only once after it is created.",
    whAktiv: "Accept messages", whNeu: "Create new key", whVorhanden: "Key set (••••)", whKeiner: "no key yet",
    whEinmal: "Visible only now – please store it safely:", whBeispiel: "Example (text, duration in seconds, style info/warnung, optional tv=<id>):",
    whNeuFrage: "Create a new key? The old one stops working.",
    zeitTitel: "Time source", ntpServer: "NTP server", ntpAuto: "automatic", zeitzone: "Time zone", systemZone: "automatic",
    zeitText: "The container uses the host clock (e.g. Proxmox). Every 30 minutes SignageCast checks it against the time source: if the host clock is synchronised, nothing changes; otherwise (or if it is more than 1 s off) SignageCast corrects clock, rotation and clips. Empty NTP server = country pool for the location (e.g. de.pool.ntp.org). Automatic time zone = the system's, or the location's country if the system runs in UTC.",
    hostSync: "Time from the host (Proxmox), synchronised – no correction needed", hostNichtSync: "Host clock not synchronised – SignageCast corrects via NTP",
    abweichung: "Offset", zeitWarnung: "Offset above 2 s – please check the host clock (e.g. chrony/NTP on Proxmox).",
    wetterKarte: "Weather", zeitKarte: "Time", layoutWahl: "Layout", zeitplan: "Schedule (optional)",
    zeitplanText: "Show another layout at certain times, e.g. only the clock or completely black at night (saves power).",
    schwarz: "black (off)", von: "from", bis: "to", zeitNeu: "Add period", wetterText: "Weather picture, temperature and forecast come from this entity; rooms, tiles and everything else are set in the “Layout” tab.",
    speichern: "Save", gespeichert: "Saved", deaktiviert: "switched off", fehler: "Error", laedt: "Loading …", ja: "yes", nein: "no",
    passwortHinweis: "Note: if you still log in with the initial password, please change it (menu top right → Accounts → " +
      "tvadmin → Set password).", ausblenden: "Dismiss",
    stream: "Video stream", laeuft: "running", aus: "off (nobody watching)", zuschauer: "Viewers", aktuell: "Now",
    qualitaet: "Quality", codec: "Codec", verloren: "dropped frames", bandbreite: "Bandwidth", cpu: "CPU", ram: "RAM free",
    platte: "Disk free", laufzeit: "Uptime", last: "Load", kerne: "cores", von: "of",
    alleSek: (s) => (s % 60 ? `every ${s} s` : `every ${s / 60} min`), nurStream: "only while the stream runs",
    vorabFehler: "Preload",
    // Meldungen des Dienstes nach Kennung (app/meldung.py); auf Deutsch zeigt die Verwaltung den Text des Dienstes
    meldung: {
      q_kennung: "Data source: invalid or duplicate identifier {id} (2–16 characters a–z, 0–9, _)",
      q_art: "Data source: type json, text, rss, bild, ical or video",
      q_adresse_video: "Data source {id}: camera address with rtsp://, rtsps://, http:// or https://",
      q_adresse: "Data source {id}: address must start with http:// or https://",
      q_kopfname: "Data source {id}: invalid header name {name}", q_kopfwert: "Data source {id}: invalid value for {name}",
      q_intervall: "Data source: interval in seconds",
      curl_lesbar: "curl command not readable: {d}", curl_wert: "curl: value missing after {opt}", curl_adresse: "curl: no address found",
      nur_http: "only http/https", http: "HTTP {code} {grund}", nicht_erreichbar: "not reachable: {d}",
      zu_gross: "response larger than {mb} MB", kein_bild: "not a picture (Content-Type {typ})", kein_json: "not valid JSON: {d}",
      kein_ical: "no iCal data (Content-Type {typ}) – check the address, it often returns a login or error page",
      kein_feed: "not a valid feed: {d}",
      kam_http: "Camera: HTTP {code} {grund}", kam_nicht_erreichbar: "Camera not reachable: {d}", kein_mjpeg: "not MJPEG (Content-Type {typ})",
      kam_zeit: "Camera does not answer (25 s)", kam_fehler: "Camera: {d}",
      met_http: "MET Norway answers {code}", met_nicht_erreichbar: "MET Norway not reachable: {d}",
      ntp_stumm: "{server} does not answer", ntp_ungueltig: "invalid NTP answer",
      kein_youtube: "not a YouTube link", kein_video_kanal: "no video found in the channel",
      ep_kein_range: "the server cannot deliver parts (no Range) – please choose “complete”", ep_zu_gross: "clip larger than 500 MB",
      ep_keine_groesse: "the server gives no total size – only “complete” possible",
      ep_nicht_bereit: "clip not ready yet – try again in a few seconds",
      sich_pw_kurz: "Password too short – at least 12 characters",
      sich_pw_schwach: "Password too weak – mix upper and lower case, digits and symbols (or a passphrase of 20+ characters)",
      sich_pw_fehlt: "The backup is encrypted – please enter the password", sich_pw_falsch: "Wrong password for the backup",
      sich_ungueltig: "Not a SignageCast backup", sich_zu_gross: "Backup too large", sich_kein_aes: "Encryption not available (package python3-pyzipper missing)",
      todo_unbekannt: "This entry cannot be hidden",
      sich_geheim_ohne_pw: "With credentials and passwords only with a password (AES-256)", sich_name: "Unknown backup",
      med_art: "Only pictures (JPG, PNG) and videos (MP4, WebM)", med_kaputt: "Video not readable",
      med_hevc: "The video is H.265 – the browser in the container cannot play it; please save it as H.264 (MP4)",
      med_upload: "Upload interrupted – please try again", med_gross: "File larger than 1 GB", med_unbekannt: "Unknown medium",
      upd_laeuft: "An update is already running – please wait", upd_aktion: "Unknown update action",
      upd_container: "With Docker/Podman update via the image (docker pull)",
      e_zahl: "not a number: {w}", e_bereich: "{w} is not between {lo} and {hi}", e_wert: "invalid value: {w}",
      e_objekt: "settings must be an object", e_layout: "Layout {name}: {d}", e_layout_doppelt: "duplicate layout identifier: {id}",
      e_tv_doppelt: "duplicate TV identifier: {id}", e_ton: "sound only off, radio or animals", e_aufloesung: "resolution only 1080 or 2160", e_aufnahme: "capture only 720, 1080 or 1440",
      e_tv_fehlt: "at least one TV is required", e_zeitzone: "unknown time zone {zz}", e_stufe: "unknown level",
      e_suchmuster: "invalid search pattern: {x}", e_ortsmuster: "invalid place pattern: {m}",
      e_kat_doppelt: "duplicate category identifier: {id}", e_kat_name: "Own category needs a name", e_kat_max: "At most {n} categories",
      e_kat_begriffe: "{name}: at most {n} search terms", e_kat_unbekannt: "Unknown category", e_kat_eingebaut: "Built-in categories cannot be deleted",
      e_ep_quelle: "Clip: unknown source", e_ep_adresse: "Clip: address missing", e_medium_art: "Media: type picture or video",
      e_pult_pw: "Panel password: at least 6 characters", e_bild_gross: "Picture too large (max. 8 MB)", e_bild_art: "Only JPG or PNG",
      e_einspielen: "Not a SignageCast backup or profile", e_streamliste: "stream list missing", e_stream_id: "invalid ID {id}",
      l_entitaet: "invalid entity {w}", l_symbol: "icon must be mdi-…", l_farbe: "colour as #rrggbb", l_bild: "invalid picture",
      l_quelle: "invalid data source", l_pfad: "path too long", l_adresse: "address with http:// or https://", l_wahl: "allowed: {werte}",
      l_vergleich: "unknown comparison", l_kennung: "invalid layout identifier {id}", l_hintergrund: "background: wetter, stil, farbe or bild",
      l_hg_bild: "invalid background picture", l_schema: "scheme light, dark or dimmed", l_schrift: "unknown font",
      l_baustein: "unknown element {typ}", l_baustein_id: "invalid or duplicate element identifier {id}",
      l_imp_kein: "This is not a SignageCast layout (the list “elemente” is missing)", l_imp_json: "No valid JSON: {d}",
      l_imp_typ: "Element {nr}: unknown type “{typ}” – left out", l_imp_raster: "Element {b}: reached beyond the edge – fitted in",
      l_imp_option: "Element {b}: unknown option “{o}” – left out", l_imp_wert: "{feld}: invalid value “{w}” – default used",
      l_imp_bild: "Picture/PDF “{w}” does not exist here – please upload it in the editor",
      l_imp_quelle: "Element {b}: data source “{q}” does not exist here – please create it or choose one in the editor",
      l_imp_bedingung: "Element {b}: invalid condition – left out", l_version_fehlt: "This version no longer exists",
      p_recht: "This account may not do that", p_kein_schalten: "No switch from Home Assistant is set for this TV",
      ki_name: "Please enter a name for the computer (letters, digits, spaces, . @ -)", ki_doppelt: "There is already a computer with this name",
      ki_max: "At most {n} computers", ki_adresse: "Invalid address of this machine",
      fn_art: "Unknown kind for remote sites", fn_server: "Address of SignageCast in the tailnet: the tailnet IP (100.x.y.z)",
      fn_tag: "Tag as tag:name (lower-case letters, digits, hyphen)", fn_zugang: "Access data incomplete",
      fn_benutzer: "Headscale user: the number (ID) from “headscale users list” – or leave empty",
      fn_api: "Tailscale/Headscale refuses: {d}", fn_nicht_erreichbar: "Tailscale/Headscale not reachable: {d}",
      fn_aus: "Remote sites are not set up (Settings → Remote sites)",
      fn_server_fehlt: "SignageCast ({d}) is not in this tailnet – check the address or set up Tailscale on this server",
      fn_userspace: "Tailscale runs in userspace mode on this server – then the admin is reachable from the tailnet without login. Please set up /dev/net/tun (guide REMOTE.md) and switch userspace mode off",
      fn_kein_tailscale: "Tailscale is not set up on this server – first “Set up Tailscale”",
      fn_operator: "Tailscale does not let SignageCast log in – please run “Set up Tailscale” again",
      fn_anmeldung: "Login to Tailscale not started: {d}", fn_nicht_verbunden: "First connect to Tailscale (login link), then switch on",
      fn_nur_geraet: "Another site only works with the image for exactly this device (not with a pairing code)",
      z_uhrzeit: "Schedule: time as HH:MM", z_layout: "Schedule: unknown layout {id}",
      s_kein_link: "No YouTube video or channel link recognised", s_nicht_einbettbar: "This video may not be embedded (or does not exist)",
      s_ort: "invalid location ({k})",
      r_adresse: "Address must start with http:// or https://", r_nicht_erreichbar: "Address not reachable: {d}",
      r_hls: "HLS radio (m3u8) is not supported – please use an MP3/AAC address", r_keine_adresse: "Playlist contains no stream address",
      r_kein_audio: "Not an audio stream (content: {typ})", r_verschachtelt: "Too many nested playlists",
      r_playlist_leer: "No stream address (http/https) found in the playlist",
      d_text_tv: "Text and at least one TV required", d_stimme_fehlt: "Voice not loaded yet (Admin → Settings → Announcement panel)",
      d_stimme: "unknown voice", bn_kanal: "unknown channel",
      l_pdf: "invalid PDF", l_zeitraum: "Period: date as YYYY-MM-DD, optionally with time",
      pdf_art: "Not a PDF file", pdf_werkzeug: "pdftoppm missing (package poppler-utils) – please update SignageCast",
      pdf_zeit: "Converting takes longer than {s} s – please use a smaller PDF", pdf_kaputt: "PDF not readable: {d}",
      al_text: "Text for the emergency screen missing",
      sch_entitaet: "No entity for switching is set for this TV",
      sch_keine_ip: "The address of this server is unknown (Docker: set SC_HOST_IP)", sch_nichts: "Nothing is set for this TV after switching on",
      e_ha_daten: "Data for the HA service must be a JSON object (at most 1000 characters)",
      sch_an_nicht: "Home Assistant cannot switch {e} on – the device does not offer it (Samsung/LG often only with Wake-on-LAN)",
      sch_aus_nicht: "Home Assistant cannot switch {e} off – the device does not offer it",
      pi_ssid: "Wi-Fi name missing or longer than 32 characters", pi_wlan_pw: "Wi-Fi password: 8 to 63 characters",
      pi_wlan_unbekannt: "This Wi-Fi is not saved (any more)", pi_name: "Player name missing", pi_tv: "Unknown TV", pi_lautstaerke: "Volume 0 to 100",
      pi_unbekannt: "Player not found", pi_befehl: "Unknown command", pi_offline: "The Pi is not reachable right now",
      pi_fernwartung_aus: "This Pi does not allow remote maintenance – switch it on on the SD card (when creating the image) or on its setup page",
      pi_fernwartung_alt: "The agent on this Pi cannot do remote maintenance yet – it updates itself at its next report, please try again shortly", pi_server: "Server address as http://IP:port",
      pi_server_lokal: "The Pi cannot find the server with this address – enter the IP in your home network under Advanced (e.g. http://192.168.1.20:8890)", pi_port: "Port 1 to 65535",
      pi_kein_image: "No player image yet – first “Download player image”", pi_signatur: "Signature of the player image invalid – not used",
      pi_pruefsumme: "Checksum of the player image wrong – please download again", pi_platz: "Not enough disk space – about {mb} MB needed",
      pi_konfig_gross: "Too much data for the device file", pi_link_alt: "Download link expired – click “Download image” again",
      pi_platzhalter: "Player image damaged – please download again",
      pi_koppel_ungueltig: "Invalid pairing request", pi_koppel_voll: "Too many pairing requests – try again in an hour",
      pi_basis_alt: "The downloaded player image ({v}) cannot pair yet – click “Download again” above (0.25 or later)",
      pi_code: "No player shows this code – check the code on the TV (it is valid for 10 minutes)",
      pi_browser_befehl: "A browser device has no player – it only shows the page behind its link",
      csv_kodierung: "Unknown character set", csv_trenner: "Unknown delimiter", csv_anfuehrung: "Unknown quote character",
      csv_spalte: "Invalid column number", csv_feldname: "Field name missing or duplicate: {name}", csv_keine_felder: "Please choose at least one field",
      csv_kaputt: "CSV not readable: {d}", csv_leer: "No data in the CSV file",
      csv_filter: "Invalid filter rule (field {name} selected?)",
      csv_kein_datum: "Column “{feld}” contains no readable date (e.g. 07.01.2026 or 2026-01-07)",
      q_datei: "{id}: file missing – please upload it", q_datei_art: "{id}: this type cannot come from a file",
      q_datei_leer: "The file is empty", q_datei_fehlt: "The uploaded file is gone – please upload it again",
    },
    haFehler: { nicht_erreichbar: "HA not reachable", kein_trusted: "HA offers no login via trusted networks for this address (trusted_networks missing or IP not listed)",
                kein_benutzer: "trusted_networks: no user assigned to this IP", abgelehnt: "Login rejected", http: "HA answered with an error" }, ha: "Home Assistant", verbunden: "connected", getrennt: "not connected",
    rotation: "In rotation", liste: "Stream list", zuletzt: "last", pause: "YouTube pause until", suche: "Stream search",
    vorschau: "Picture on the TV", vorschauNeu: "Refresh picture", keineVorschau: "No picture – the stream is not running.",
    seiteNeu: "Reload TV page", ketteNeu: "Restart stream", listeNeu: "Rebuild list", erledigt: "Done",
    neueVersion: (v) => `New version ${v} available`, updateText: "To update, run this command as root inside the container (settings and data are kept).",
    updateTextContainer: "To update, pull the new image and recreate the container (settings and data in the volume are kept):",
    systemSeitenContainer: "Logs: docker logs signagecast (or podman logs). Restart and update via Docker/Podman.",
    passwortHinweisContainer: "Note: you are still using the initial password from the log – please set your own under System → Access.",
    verwaltungTitel: "Admin login", pwAlt: "Current password", pwNeu: "New password (min. 8 characters)",
    pwAendern: "Change password", pwGeaendert: "Password changed", abmelden: "Log out",
    kodierungKarte: "Video encoding", kodierungArt: { vaapi: "Graphics unit (VAAPI)", software: "Software (CPU)" },
    kodierungSoftware: "No usable graphics – fallback: H.264 in Full HD on the CPU (about 1–2 cores while someone is watching).",
    epPuffer: "Buffer", epPufferArt: { vorab: "preload in the container (recommended)", vorlauf: "buffer ahead in the browser", aus: "off (directly from the server)" },
    epMenge: "Amount", epKomplett: "complete", epMb: "only the beginning (MB)", epVorlauf: "Buffer ahead (s)",
    epPufferText: "Preload: the container fetches every new edition as soon as it appears and the TV plays it from there – no stalling. " +
      "With “only the beginning” the rest comes from the server while playing (less space, the head start bridges dropouts). Not for YouTube.",
    epVorab: (mb, ges, st) => `preloaded: ${mb} MB${ges ? " of " + ges + " MB" : ""}${st ? " · edition " + st : ""}`,
    aenderungen: "What's new?", projektseite: "Project page (GitHub)", fehlerMelden: "Report a bug / request a feature",
    aufgaben: "Scheduled tasks", systemSeiten: "Services, logs and timers of the container are in the Cockpit menu on the left.",
    hinzufuegen: "Add stream", link: "YouTube link or video ID", name: "Name (empty = title)", kategorie: "Category",
    breite: "Latitude", laenge: "Longitude", ortAuto: "empty = detect from title", filter: "Search …", alle: "all categories",
    herkunftAlle: "fixed and found", nurFeste: "fixed only", nurGefundene: "found only", aktiv: "active", geschuetzt: "protected",
    zustandAlle: "all", zustand: { rotation: "in rotation", bereit: "ready", nacht: "night", nicht_live: "not live",
      qualitaet: "resolution too low", pause: "paused after strike", gesperrt: "blocked", strikes: "with strikes", ohne_ort: "location unknown",
      ungeprueft: "not checked yet", inaktiv: "inactive", kategorie_aus: "category off" },
    hellIn: (d) => `daylight in ${d}`, laeuftAus: "ending (just got dark)", pauseBis: (z) => `until ${z}`, angebot: (p) => `offers ${p}`,
    vorab: (z, n) => `Pre-check ${z}: ${n} checked`,
    zeigen: "Show now", uebernehmen: "Keep", bearbeiten: "Edit", entfernen: "Remove", ablehnen: "Reject",
    strikesWeg: "Reset strikes", inRotation: "in rotation",
    gefunden: "found", fest: "fixed", proben: "samples", strikes: "Strikes",
    abgelehnt: "Rejected streams (never added again by the search)", freigeben: "Allow again",
    wirklichEntfernen: "Really remove this stream?", wirklichAblehnen: "Remove this stream and never add it again?",
    zeigenOk: "Coming up on the TV (for one slot)", anzahl: (n, g) => `${n} streams, ${g} currently in rotation`,
    sprache: "Language", wetter: "Weather entity", vorhersage: "Show 3-day forecast", raeume: "Rooms (left, up to 4)",
    kacheln: "Tiles (bottom, up to 8)", icon: "Icon (mdi-…)", zeileNeu: "Add row", entitaetenFehlen:
      "Entity list from HA not available – please type the names.", iconsListe: "Icon names: pictogrammers.com/library/mdi",
    videoAktiv: "Show live videos", takt: "Minutes per stream", nurTag: "only streams where it is daytime",
    sonne: "Minimum sun elevation (degrees)", mindeststufe: "Minimum quality", schlecht: "below it for this long, then skip (s)",
    grenze: "Strikes until a stream stops playing", sperre: "after a strike skip for (hours)",
    kod: { titel: "Encoding (advanced)", encoder: "Encoder", preset: "Preset", tune: "Tune", bframes: "B-frames",
      text: "“Automatic” is normally right. A change restarts this TV's stream (black for a few seconds); SignageCast tries it briefly first and stays with “Automatic” if it does not work here. Afterwards check under System → Performance whether encoding keeps up.",
      art: { auto: "Automatic (recommended)", vaapi: "Intel/AMD graphics (VAAPI)", qsv: "Intel Quick Sync (QSV)", nvenc: "NVIDIA NVENC (experimental)", software: "Software (libx264)" },
      info: { auto: "Uses the graphics unit via VAAPI, software without usable graphics.",
        vaapi: "Video unit of Intel or AMD graphics via the open VAAPI interface – efficient, 4K, H.264 and H.265. Has no preset and no tune.",
        qsv: "Intel's own way to the same video unit (Quick Sync via oneVPL), with presets. Needs Intel graphics of the 11th/12th generation or newer (e.g. N100, Core from Tiger Lake); with older Intel graphics use VAAPI.",
        nvenc: "Video unit of an NVIDIA graphics card. Experimental and untested: card and NVIDIA driver must be available in the container (/dev/nvidia*, Docker --gpus all) – SignageCast does not set this up itself.",
        software: "The processor encodes H.264 (libx264): works everywhere but costs about 1–2 cores per TV; always Full HD and at most 8 Mbit/s." },
      grund: { keine_grafik: "no graphics (/dev/dri) found", qsv_alt: "needs Intel graphics of the 11th/12th generation or newer", keine_nvidia: "no NVIDIA card found" },
      presetInfo: "How thoroughly the encoder works: ultrafast is the fastest, medium gives the nicest picture at the same bitrate but needs much more computing time – if the computer cannot keep up, the picture stutters. Quick Sync and NVENC get their matching own level.",
      tuneArt: { zerolatency: "zerolatency (recommended)", keins: "none" },
      tuneInfo: "zerolatency tunes the encoder for low delay (no look-ahead, every frame out at once) – recommended for live pictures, costs a little quality. “none” looks a few frames ahead: slightly nicer but slower to react.",
      bfInfo: "B-frames are in-between frames that also refer to later frames: about 5–15 % less data, but more delay, and some TV browsers stutter with them. 0 is the safe choice for live streams.",
      ohne: "VAAPI has no preset and no tune – the fields only apply to software, Quick Sync and NVENC.",
      fehler: (enc, g) => `The setting does not work here (${enc}: ${g}) – this TV therefore uses “Automatic”.`,
      aktiv: "Currently active", std: "default", standard: "Back to default" },
    codec: "Codec", codecArt: { auto: "Automatic (recommended)", h265: "H.265 / HEVC", h264: "H.264 / AVC" },
    codecText: "Automatic: 4K as H.265 (half the data, supported by almost all 4K TVs), Full HD as H.264 (plays on practically every TV, browser and player). Choose H.264 if a device stutters or shows no picture – e.g. older TVs, Firefox; H.265 needs about 30–40 % less bitrate for the same quality.",
    kategorien: "Categories", kategorienAlle: "Categories (for all TVs)", streamTechnik: "Video stream", abschaltenTitel: "Video stream without viewers",
    abschnitt: { anzeige: "Display", video: "Live video", ton: "Sound" }, aufloesung: "Output", bitrate: "Bitrate (Mbit/s)",
    aufnahme: "Capture (browser)", aufnahmeArt: { 720: "720p – saves CPU", 1080: "1080p (recommended)", 1440: "1440p – sharper, needs more CPU" },
    aufnahmeText: "Size in which the browser draws the TV page; the graphics unit converts it to the output. More than the output brings nothing. Live videos in the layout follow the capture (720p fetches 720p from YouTube). A change briefly restarts the stream.",
    abschalten: "Switch off without viewers after (s)", technikHinweis: "Output and bitrate apply at the next stream start.",
    sucheAktiv: "search for new streams daily", uhrzeit: "Time", max: "maximum found streams",
    behalten: "days to keep when no longer found", begriffe: "Search terms (one per line)",
    tierwoerter: "Title must contain one of these words (one per line, regular expressions allowed)",
    ausschluss: "Title must not contain any of these words", orte: "Location from title: pattern ; latitude ; longitude (one per line)",
    jetztSuchen: "Search now", sucheLaeuft: "Searching (up to about 1 min) …", sucheErgebnis: (n, g) => `${g} live streams found, ${n} new`,
    haUrl: "Home Assistant address", testen: "Test connection", standort: "Location",
    standortAusHA: "Take from HA", testOk: (v) => `Connected – Home Assistant ${v}`, anleitung: "Setup in Home Assistant", ipPlatzhalter: "CONTAINER-IP", benutzerIdPlatzhalter: "USER-ID",
    anleitungText: (ip) => [
      "SignageCast logs in to Home Assistant without a password – via “trusted networks”. HA recognises the container by its IP address.",
      "1. In HA under Settings → People create a user, e.g. “TV” (no administrator, “Can only log in from the local network” on).",
      "2. Open the user – the long identifier at the end of the address bar is the user ID.",
      `3. Add this section to configuration.yaml (e.g. with the File editor add-on) and replace USER-ID. The IP of this container is ${ip || "unknown (Home Assistant not reachable) – replace CONTAINER-IP"}:`,
    ], anleitungEnde: "4. Check the configuration (Developer tools → YAML → Check configuration) and restart HA. Then press “Test connection” here. " +
      "Important: trusted_networks must be the first provider, otherwise a login page appears. If there is already a homeassistant: section, only add the lines below it.",
    sicherungLaden: "Download backup", sicherungEinspielen: "Restore backup or profile",
    mitGeheim: "include secrets (API keys, passwords of data sources) – then do not share the file",
    sichNeu: "Create backup", mitGeheimFrage: "Include credentials and passwords? (API keys, camera passwords, password of the automatic backup)",
    pwPflicht: "The ZIP is then encrypted with AES-256 – a strong password is required (min. 12 characters, upper/lower case, digits, symbols; or a passphrase of 20+ characters). It opens with SignageCast, 7-Zip or WinRAR. Without the password the backup is lost.",
    pw1: "Password", pw2: "Repeat password", pwGut: "Password strong enough", pwSchwach: "Password too weak", pwUngleich: "The passwords differ",
    sichErstellen: "Create and download backup", sichFertig: "Backup created", sichListe: "Stored backups (in the container)",
    sichAuto: "automatic", sichManuell: "manual", sichMitGeheim: "with credentials", sichKeine: "No backup stored yet.",
    sichLetzteAuto: "Last automatic backup", sichWegFrage: "Delete this backup?", herunterladen: "Download",
    sichAutoTitel: "Automatic backup", sichPlan: "When", sichPlanArt: { aus: "off", taeglich: "daily", woechentlich: "weekly" },
    wochentage: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], sichBehalten: "Keep (number)",
    sichAutoText: "Automatic backups are stored in the container; download one now and then so it survives a loss of the container.",
    pwEinspielen: "Password (if encrypted)",
    karussell: "Layout carousel", karussellText: "Switches between the chosen layouts every few minutes (at least two). A schedule takes priority.",
    karussellAn: "on", karussellMin: "every (min)", videoQuelle: "Video window shows",
    videoQuelleArt: { youtube: "live streams (YouTube)", medien: "own media only", gemischt: "mixed" }, medienAlle: "every N-th time own media",
    medText: "Your own pictures (JPG, PNG) and videos (MP4/H.264, WebM) for the video window – set per TV under “TVs”: own media only or mixed with the live streams. Pictures stay for their duration, videos play completely.",
    medHoch: "Upload files", medLaedt: (n, p) => `Uploading ${n} … ${p} %`, medKeine: "No own media yet.", medDauer: "Duration (s)",
    medSicherung: "Backups always contain pictures, videos only up to 200 MB in total – please keep large videos yourself as well.",
    medWeg: "Delete this medium?",
    upSc: "SignageCast", upInstalliert: "installed", upNeueste: "latest", upAktuell: "up to date", upJetzt: "Update now",
    upZurueck: (v) => `Back to ${v}`, upZurueckFrage: "Return to the previous version? Settings from before the last update are restored.",
    upScText: "Settings and data are backed up before the update. Only a release with a valid signature is installed. If SignageCast does not run within a minute afterwards, it returns to the previous version automatically. The TV may reconnect briefly.",
    upSystem: "System (Debian)", upPruefen: "Check now", upAlle: "Install all", upNurSicher: "Security updates only",
    upKeine: "No system updates available.", upAnzahl: (n, s) => `${n} update${n === 1 ? "" : "s"}${s ? `, ${s} security` : ""}`,
    upGeprueft: "last checked", upNie: "not checked yet", upNeustart: "Restart needed for kernel updates",
    upLetzte: "Last action", upPhase: { laeuft: "running …", ok: "done", fehler: "error", zurueck: "returned" },
    upAktion: { pruefen: "Check", system: "System updates", sicherheit: "Security updates", signagecast: "SignageCast update", zurueck: "Back to previous version", unbekannt: "–" },
    upAuto: "Automatic", upAutoSystem: "System", upAutoSc: "SignageCast", upModus: { melden: "notify only", sicherheit: "security updates automatically", auto: "automatically" },
    upFenster: "Maintenance window", upAutoText: "Automatic only within the maintenance window and only while nobody is watching. Checked once a day.",
    upGestartet: "Started – the status updates here",
    upContainer: "With Docker/Podman you update via the image – system and SignageCast are both inside:",
    mitStrikes: "also restore strikes", eingespielt: "Restored", sicherungText: "The backup (ZIP) contains settings, stream list " +
      "(with protected, rejected and found streams), strikes, uploaded pictures and the chart history – everything for a new installation. Old .json backups and profiles can still be restored.",
    wirklichEinspielen: "Settings and stream list will be replaced. Continue?",
    kat: { safari: "Safari Africa", affen: "Apes & monkeys", meer: "Underwater & sea", vogel: "Birds", baer: "Bears, wolves, polar bears",
           wald: "Forest & wildlife", zoo: "Zoo & exotic", neu: "Newly found",
           stadt: "Cities & squares", strand: "Beaches & coasts", berge: "Mountains & ski", hafen: "Harbours & ships",
           flug: "Airports & planes", bahn: "Trains & railways", weltraum: "Space & Earth", natur: "Natural wonders" },
    katGruppe: { tiere: "Animals", themen: "More topics" },
    katText: "Define what a category is: its own YouTube search terms, words that must appear in the title and whether day/night at the location matters. Found animal streams are sorted by the words (first matching category, otherwise “Newly found”). Switch categories on and off for all TVs or per TV.",
    katNeu: "New category", katEigene: "own", katGeaendert: "changed", katNamePflicht: "Name (required)", katGruppeWahl: "Group",
    katNeuText: "Found animal streams that match no category end up here. It has no search of its own.",
    katWo: "Switched on", katAlle: "For all TVs", katStreams: (n) => `${n} streams`, katEinStream: "1 stream",
    katAusAlle: "off", katAusBei: (l) => `off on ${l}`, katMitSuche: (n) => n === 1 ? "1 search term" : `${n} search terms`, katNameFeld: "Name",
    katBegriffe: (n) => `Search terms (one per line, at most ${n})`,
    katBegriffeTiere: "Empty = only the general animal search (Search page) fills this category. Each term is one YouTube request per search run.",
    katBegriffeThemen: "Each term is one YouTube request per search run. The search only runs while the category is on for all TVs.",
    katWoerter: "Words in the title (one per line, regular expressions allowed)",
    katWoerterTiere: "One word must appear in the title. Also sorts finds of the general animal search into this category.",
    katWoerterThemen: "One word must appear in the title. Empty = any title (except music, games and the like).",
    katOhneTag: "Ignore day/night at the location", katOhneTagWoerter: "Ignore day/night only with these words in the title",
    katStreamsZeigen: "Show streams", katStandard: "Reset to default",
    katVerschieben: (n) => n ? `Move ${n} streams to` : "Delete", katWirklich: "Delete for good",
    kategorienWoanders: "Switch categories on and off and edit them:",
    aufgabe: { streamliste: "Check stream list", suche: "Search new streams", wache: "Measure quality" },
  },
};
let T = TEXTE[(cockpit.language || "de").startsWith("de") ? "de" : "en"];

// ---------- Hilfsfunktionen ----------
const $ = (sel, wurzel = document) => wurzel.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// Arbeitsspeicher eines Pi als Nenngröße: MemTotal liegt etwas darunter (z. B. 2-GB-Pi ≈ 1850 MB)
const ramNenn = (mb) => { const n = [512, 1024, 2048, 4096, 8192, 16384].find((x) => mb <= x); return !n ? Math.round(mb / 1024) + " GB" : n < 1024 ? n + " MB" : n / 1024 + " GB"; };
function el(html) { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; }

async function holen(pfad) {
  const t = await dienst.get(pfad, {}, KOPF);
  return JSON.parse(t);
}
// Meldung des Dienstes in der Sprache der Verwaltung (Kennung + Werte), sonst der Text des Dienstes
function meldungText(m, rueckfall) {
  const vorlage = m && m.code && T.meldung && T.meldung[m.code];
  const p = m && m.innen ? { ...m.p, d: meldungText(m.innen) } : (m && m.p) || {};    // innere Meldung, z. B. „Layout X: …“
  return vorlage ? vorlage.replace(/\{(\w+)\}/g, (_, k) => (p[k] ?? "")) : (rueckfall || (m && m.text) || "");
}
async function senden(pfad, daten) {
  const t = await dienst.post(pfad, JSON.stringify(daten || {}), KOPF);
  const d = JSON.parse(t);
  if (!d.ok) throw new Error(meldungText(d, d.fehler) || T.fehler);
  return d;
}
let meldungZeit;
function melden(text, fehler) {
  const m = $("#meldung");
  m.textContent = (fehler ? T.fehler + ": " : "") + text;
  m.classList.add("an");
  clearTimeout(meldungZeit);
  meldungZeit = setTimeout(() => m.classList.remove("an"), fehler ? 6000 : 2500);
}
async function aktion(knopf, fn, okText) {
  if (knopf) knopf.disabled = true;
  try { const r = await fn(); if (okText !== null) melden(okText || T.gespeichert); if (knopf) gespeichert(knopf); return r; }
  catch (e) { melden(e.message || String(e), true); }
  finally { if (knopf) knopf.disabled = false; }
}
const schalter = (name, an) => `<label class="schalter"><input type="checkbox" name="${esc(name)}" ${an ? "checked" : ""}><span></span></label>`;
const dauer = (s) => { const t = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60); return (t ? t + " d " : "") + h + " h " + m + " min"; };
const ORT = () => E.sprache === "en" ? "en-GB" : "de-DE";   // Zeitformat nach Sprache der Verwaltung, 24 h (seit 0.23.2)
const uhrzeit = (ts) => ts ? new Date(ts * 1000).toLocaleTimeString(ORT(), { hour: "2-digit", minute: "2-digit" }) : "–";

let E = null, KAT_STANDARD = [], KAT_GRENZEN = [40, 6], STUFEN = [], ENTITAETEN = null, BAUSTEINE = {}, SCHRIFTEN = ["Roboto"];
// YouTube-Qualitätsstufen als Auflösung anzeigen (intern bleiben die YouTube-Namen)
const STUFE_P = { tiny: "144p", small: "240p", medium: "360p", large: "480p", hd720: "720p", hd1080: "1080p",
                  hd1440: "1440p", hd2160: "2160p", highres: "4320p" };
const stufeText = (x) => STUFE_P[x] || x;
// Kategorien (seit 0.37 editierbar, in E.kategorien): Kennungen, Name (eigener oder übersetzter Standard), Gruppen
const katIds = () => E.kategorien.map((k) => k.id);
const katName = (id) => { const k = E.kategorien.find((x) => x.id === id); return (k && k.name) || T.kat[id] || id; };
const katOptionen = (gewaehlt) => E.kategorien.map((k) => `<option value="${esc(k.id)}" ${k.id === gewaehlt ? "selected" : ""}>${esc(katName(k.id))}</option>`).join("");
// Kategorie-Schalter in zwei Gruppen (seit 0.32): Tiere und weitere Themen
const katSchalter = (prefix, aus, h = "h4") => ["tiere", "themen"].map((g) => [g, E.kategorien.filter((k) => k.gruppe === g).map((k) => k.id)])
  .filter(([, ks]) => ks.length).map(([g, ks]) => `<${h}>${esc(T.katGruppe[g])}</${h}>` +
    ks.map((k) => `<div class="zeile"><label>${esc(katName(k))}</label>${schalter(prefix + k, !aus.includes(k))}</div>`).join("")).join("");

// ---------- Nicht gespeicherte Änderungen (seit 0.17) ----------
// Eine Eingabe markiert ihre Karte; ein erfolgreicher Speichern-Knopf hebt die Markierung seiner Karte auf
// (liegt der Knopf außerhalb einer Karte: aller Karten daneben). Datei-Auswahl und reine Suchfelder zählen nicht.
const istSpeichern = (b) => b.tagName === "BUTTON" && b.textContent.trim() === T.speichern;
function aenderungMerken(ev) {
  const z = ev.target;
  if (!z.matches("input, select, textarea") || z.type === "file" || z.dataset.frei !== undefined) return;
  const karte = z.closest(".karte");
  if (!karte) return;
  const mitKnopf = [...karte.querySelectorAll("button")].some(istSpeichern) ||
                   [...karte.parentElement.querySelectorAll(":scope > .zeile button")].some(istSpeichern);
  if (mitKnopf) { karte.classList.add("geaendert"); karte.dataset.ungespeichert = T.ungespeichert; }
}
function gespeichert(knopf) {
  const karte = knopf.closest(".karte");
  for (const k of karte ? [karte] : knopf.closest(".zeile")?.parentElement?.querySelectorAll(".karte.geaendert") || []) k.classList.remove("geaendert");
}
const ungespeichert = () => !!document.querySelector("#inhalt .karte.geaendert");
window.addEventListener("beforeunload", (e) => { if (ungespeichert()) { e.preventDefault(); e.returnValue = ""; } });

// ---------- Reiter ----------
// Zwei Teile auf einer Seite: jeder zeichnet in seinen eigenen Kasten (seit 0.31.1)
const zweiTeile = (a, b) => async (i) => {
  i.innerHTML = `<div id="teilA"></div><div id="teilB"></div>`;
  await a($("#teilA")); await b($("#teilB"));
};
const SEITEN = { uebersicht, fernseher: fernseherSeite, player: playerSeite, layout: layoutSeite, quellen: quellenSeite, medien: medienSeite, einspieler: einspielerSeite,
                 streams: streamsSeite, kategorien: kategorienSeite, video, suche: sucheSeite, radio: radioSeite,
                 allgemein: allgemeinSeite, ha: (i) => verbindung(i, "ha"), benachrichtigung: (i) => verbindung(i, "benachrichtigung"),
                 pult: zweiTeile(pultSeite, webhookKarte),
                 updates: updatesSeite, sicherung: sicherungSeite, leistung: zweiTeile(leistungSeite, abschaltenKarte), zugang: (i) => verbindung(i, "zugang"),
                 protokoll: protokollSeite, ki: kiSeite, fern: fernSeite };
// Bereiche (seit 0.17) – je Bereich seine Unterseiten; Adresse je Seite als #<seite>
// Seit 0.31.1 neu geordnet: Inhalte (was gezeigt/gespielt wird), Live-Videos (Streams und ihre Regeln), Einstellungen
// (Grundlagen und Verbindungen), System (Betrieb). Die Kennungen der Seiten (#video, #pult …) bleiben gleich.
const BEREICHE = [["uebersicht", ["uebersicht"]], ["fernseher", ["fernseher", "player"]],
                  ["inhalte", ["layout", "quellen", "medien", "einspieler", "radio", "pult"]],
                  ["videoton", ["streams", "kategorien", "video", "suche"]],
                  ["einstellungen", CONTAINER ? ["allgemein", "ha", "benachrichtigung", "ki", "fern", "zugang"] : ["allgemein", "ha", "benachrichtigung", "ki", "fern"]],
                  ["system", ["updates", "sicherung", "leistung", "protokoll"]]];
const ALT = { anzeige: "allgemein", verbindung: "ha" };              // gemerkte Reiter bis 0.16
let aktiv = "uebersicht", timer = null;
const bereichVon = (k) => BEREICHE.find(([, s]) => s.includes(k)) || BEREICHE[0];
function reiterZeichnen() {
  const [bereich, unter] = bereichVon(aktiv);
  const nav = $("#reiter"), sub = $("#unter"), menue = $("#menue");
  nav.innerHTML = ""; sub.innerHTML = "";
  for (const [b, seiten] of BEREICHE) {
    const k = el(`<button class="${b === bereich ? "an" : ""}">${esc(T.bereiche[b])}</button>`);
    k.onclick = () => zeigeSeite(b === bereich ? aktiv : merk[b] || seiten[0]);
    nav.appendChild(k);
  }
  const anker = { benachrichtigung: "#get-notified-when-something-breaks", medien: "#own-pictures-and-videos-instead-of-or-between-live-cams",
                  fernseher: "#show-something-different-at-night" }[aktiv] || "";
  nav.appendChild(el(`<a class="hilfe" title="?" target="_blank" rel="noopener"
    href="https://github.com/thefrozn/signagecast/blob/main/docs/${aktiv === "player" ? "PLAYER.md" + (E && E.sprache === "de" ? "#deutsch-raspberry-pi-als-player" : "") : "MANUAL.md" + anker}">?</a>`));
  sub.hidden = unter.length < 2;
  for (const s of unter) {
    const k = el(`<button class="${s === aktiv ? "an" : ""}">${esc(T.reiter[s])}</button>`);
    k.onclick = () => zeigeSeite(s);
    sub.appendChild(k);
  }
  menue.innerHTML = BEREICHE.map(([b, seiten]) => seiten.length < 2
    ? `<option value="${seiten[0]}">${esc(T.bereiche[b])}</option>`
    : `<optgroup label="${esc(T.bereiche[b])}">${seiten.map((s) => `<option value="${s}">${esc(T.reiter[s])}</option>`).join("")}</optgroup>`).join("");
  menue.value = aktiv;
  menue.onchange = () => zeigeSeite(menue.value);
}
const merk = {};                                                       // zuletzt offene Unterseite je Bereich
function zeigeSeite(k) {
  k = ALT[k] || k;
  if (!SEITEN[k]) k = "uebersicht";
  if (k !== aktiv && ungespeichert() && !confirm(T.ungespeichertFrage)) { history.replaceState(null, "", "#" + aktiv); reiterZeichnen(); return; }
  aktiv = k;
  merk[bereichVon(k)[0]] = k;
  if (location.hash !== "#" + k) history.replaceState(null, "", "#" + k);
  clearInterval(timer); timer = null;
  reiterZeichnen();
  const inhalt = $("#inhalt");
  inhalt.innerHTML = `<p class="leise">${esc(T.laedt)}</p>`;
  SEITEN[k](inhalt).catch((e) => { inhalt.innerHTML = `<div class="karte schlecht">${esc(e.message || e)}</div>`; });
  try { localStorage.setItem("signagecast-reiter", k); } catch (_) { /* egal */ }
}
function hinweiseZeichnen() {
  const h = $("#hinweise");
  h.innerHTML = "";
  let weg = false;
  try { weg = localStorage.getItem("signagecast-pw-hinweis") === "weg"; } catch (_) { /* egal */ }
  if (CONTAINER) {                          // Container: nur solange das Startpasswort aus dem Protokoll gilt
    fetch("/verwaltung/info", { credentials: "same-origin" }).then((r) => r.json()).then((i) => {
      if (i.startpasswort) h.appendChild(el(`<div class="hinweis">${esc(T.passwortHinweisContainer)}</div>`));
    }).catch(() => {});
    return;
  }
  if (weg) return;
  const n = el(`<div class="hinweis"><button class="knopf">${esc(T.ausblenden)}</button>${esc(T.passwortHinweis)}</div>`);
  n.querySelector("button").onclick = () => { try { localStorage.setItem("signagecast-pw-hinweis", "weg"); } catch (_) { /* egal */ } n.remove(); };
  h.appendChild(n);
}

async function einstellungenLaden() {
  const d = await holen("/api/einstellungen");
  E = d.einstellungen; KAT_STANDARD = d.kategorien_standard || []; KAT_GRENZEN = [d.kategorien_max || 40, d.kategorien_begriffe_max || 6]; STUFEN = d.stufen;
  if (!E.sprache) {                         // Neuinstallation: Sprache aus dem Browser übernehmen und merken
    E.sprache = (cockpit.language || navigator.language || "en").startsWith("de") ? "de" : "en";
    try { await senden("/api/einstellungen", { sprache: E.sprache }); } catch (_) { /* nächstes Mal */ }
  } BAUSTEINE = d.bausteine || {}; SCHRIFTEN = d.schriften || SCHRIFTEN;
  T = TEXTE[E.sprache] || TEXTE.de;
}
async function speichernE(teil, knopf) {
  if (!("layouts" in teil)) LS = null;      // Layout-Editor beim nächsten Öffnen frisch laden
  return aktion(knopf, async () => { const d = await senden("/api/einstellungen", teil); E = d.einstellungen; });
}
async function entitaeten() {
  if (ENTITAETEN) return ENTITAETEN;
  try { const d = await holen("/api/ha/entitaeten"); ENTITAETEN = d.ok ? d.entitaeten : []; } catch (_) { ENTITAETEN = []; }
  return ENTITAETEN;
}

// ---------- Übersicht ----------
// Einrichtungs-Assistent (seit 0.17): nur bei Neuinstallation (assistent_fertig = false); jeder Schritt speichert sofort
let asWeg = "browser";   // Schritt 4 (seit 0.44): Browser, Raspberry Pi oder PC
async function assistent(inhalt, n = 1) {
  const fertig = async (ziel = "uebersicht") => { E = (await senden("/api/einstellungen", { assistent_fertig: true })).einstellungen; zeigeSeite(ziel); };
  const kopf = `<h2>${esc(T.as.titel)}</h2><p class="leise">${esc(T.as.schritt(n))}</p>`;
  const fuss = (weiter = true, ueber = false) => `<div class="zeile">${n > 1 ? `<button class="knopf" id="asZur">${esc(T.as.zurueck)}</button>` : ""}
    ${ueber ? `<button class="knopf" id="asUeber">${esc(T.as.ueberspringen)}</button>` : ""}
    ${weiter ? `<button class="knopf haupt" id="asWeiter">${esc(T.as.weiter)}</button>` : ""}</div>
    ${n < 5 ? `<p class="leise"><a href="#" id="asSpaeter">${esc(T.as.spaeter)}</a></p>` : ""}`;
  const geh = (m) => assistent(inhalt, m);
  if (n === 1) {
    inhalt.innerHTML = `<div class="karte assistent">${kopf}<p>${esc(T.as.sprache)}</p>
      <div class="zeile"><select id="asSprache"><option value="de">Deutsch</option><option value="en">English</option></select></div>${fuss()}</div>`;
    $("#asSprache").value = E.sprache || "de";
    $("#asSprache").onchange = async () => { E = (await senden("/api/einstellungen", { sprache: $("#asSprache").value })).einstellungen;
      T = TEXTE[E.sprache] || TEXTE.de; reiterZeichnen(); hinweiseZeichnen(); geh(1); };
    $("#asWeiter").onclick = () => geh(2);
  } else if (n === 2) {
    inhalt.innerHTML = `<div class="karte assistent">${kopf}<p>${esc(T.as.ort)}</p>
      <div class="zeile"><input type="text" id="asOrt" data-frei placeholder="${esc(T.ortSuche)}" value="${esc(E.standort.name || "")}">
        <button class="knopf" id="asSuchen">${esc(T.suchen)}</button></div><div id="asOrte"></div>
      <p class="leise" id="asStand">${E.standort.name ? esc(E.standort.name) + " · " : ""}${E.standort.breite} / ${E.standort.laenge}</p>${fuss()}</div>`;
    const suchen = (e) => aktion(e.target, async () => {
      const r = await holen("/api/ort/suche?q=" + encodeURIComponent($("#asOrt").value));
      if (!r.ok) throw new Error(r.fehler);
      const ziel = $("#asOrte"); ziel.innerHTML = "";
      for (const o of r.orte.slice(0, 6)) {
        const z = el(`<div class="zeile eintrag"><span>${esc(o.name)}</span><button class="knopf haupt">${esc(T.uebernehmen)}</button></div>`);
        z.querySelector("button").onclick = (ev) => aktion(ev.target, async () => {
          E = (await senden("/api/einstellungen", { standort: { breite: o.breite, laenge: o.laenge, name: o.name.split(",")[0] } })).einstellungen;
          geh(3);
        }, T.ortGesetzt);
        ziel.appendChild(z);
      }
    }, null);
    $("#asSuchen").onclick = suchen;
    $("#asOrt").onkeydown = (e) => { if (e.key === "Enter") suchen({ target: $("#asSuchen") }); };
    $("#asWeiter").onclick = () => geh(3);
  } else if (n === 3) {
    inhalt.innerHTML = `<div class="karte assistent">${kopf}<p>${esc(T.as.ha)}</p>
      <div class="zeile"><label>${esc(T.haUrl)}</label><input type="url" id="asHa" data-frei placeholder="http://homeassistant.local:8123" value="${esc(E.ha.url)}"></div>
      <p id="asHaErg"></p>${fuss(true, true)}</div>`;
    $("#asWeiter").onclick = (e) => aktion(e.target, async () => {
      const url = $("#asHa").value.trim();
      if (!url) return geh(4);
      E = (await senden("/api/einstellungen", { ha: { url } })).einstellungen; ENTITAETEN = null;
      const r = await holen("/api/ha/test");
      if (r.ok) return geh(4);
      $("#asHaErg").innerHTML = `<span class="schlecht">${esc(T.haFehler[r.code] ? T.haFehler[r.code] : r.fehler)}</span> – ${esc(T.as.ueberspringen)}?`;
    }, null);
  } else if (n === 4) {
    inhalt.innerHTML = `<div class="karte assistent">${kopf}<p>${esc(T.as.weg)}</p><div class="as-wege">${Object.entries(T.as.wege).map(([k, [titel, text]]) =>
      `<label class="as-weg"><input type="radio" name="asWeg" value="${k}"${k === asWeg ? " checked" : ""}><span><b>${esc(titel)}</b><br><span class="leise">${esc(text)}</span></span></label>`).join("")}</div>${fuss()}</div>`;
    inhalt.querySelectorAll("input[name=asWeg]").forEach((r) => { r.onchange = () => { asWeg = r.value; }; });
    $("#asWeiter").onclick = () => geh(5);
  } else {
    let oben;
    if (asWeg === "browser") {
      const st = await holen("/api/ha/einrichtung");
      const t = E.fernseher[0];
      const host = st.eigene_ip || location.hostname;
      const adr = `http://${host.includes(":") ? `[${host}]` : host}:${st.stream_port || 8888}/${t.id}`;
      const lokal = !st.eigene_ip && /^(localhost|127\.|\[?::1\]?$)/.test(location.hostname);
      oben = `<p>${esc(T.as.fertig)}</p><pre>${esc(adr)}</pre>${lokal ? `<p class="schlecht">${esc(T.as.lokal)}</p>` : ""}`;
    } else {
      oben = `<p>${esc(T.as.fertigPlayer)}</p><div class="zeile"><button class="knopf haupt" id="asPlayer">${esc(T.as.zumPlayer)}</button></div>`;
    }
    inhalt.innerHTML = `<div class="karte assistent">${kopf}${oben}<p class="leise">${esc(T.as.fertigText)}</p>
      <p><b>${esc(T.as.mehr)}</b></p><ul class="as-mehr">${Object.entries(T.as.mehrListe).map(([k, t]) => `<li><a href="#" data-ziel="${k}">${esc(t)}</a></li>`).join("")}</ul>
      ${fuss(false)}<div class="zeile"><button class="knopf${asWeg === "browser" ? " haupt" : ""}" id="asLos">${esc(T.as.los)}</button></div></div>`;
    $("#asLos").onclick = (e) => aktion(e.target, () => fertig(), null);
    if ($("#asPlayer")) $("#asPlayer").onclick = (e) => aktion(e.target, () => fertig("player"), null);
    inhalt.querySelectorAll("a[data-ziel]").forEach((a) => { a.onclick = (e) => { e.preventDefault(); aktion(null, () => fertig(a.dataset.ziel), null); }; });
  }
  if ($("#asZur")) $("#asZur").onclick = () => geh(n - 1);
  if ($("#asUeber")) $("#asUeber").onclick = () => geh(n + 1);
  if ($("#asSpaeter")) $("#asSpaeter").onclick = (e) => { e.preventDefault(); aktion(null, () => fertig(), null); };
}

// ---------- Durchsage-Pult (seit 0.19) ----------
async function pultSeite(inhalt) {
  const [info, al] = await Promise.all([holen("/api/pult"), holen("/api/alarm")]);
  const P = JSON.parse(JSON.stringify(E.pult)), A = JSON.parse(JSON.stringify(E.alarm));
  const adresse = `http://${info.eigene_ip || location.hostname}:${info.port}/pult`;
  const zeichnen = () => {
    inhalt.innerHTML = `<div class="karte"><h2>${esc(T.pu.titel)}</h2><p class="leise">${esc(T.pu.text)}</p><pre>${esc(adresse)}</pre>
        <p class="leise">${esc(T.pu.tonHinweis)}</p></div>
      <div class="karte"><h2>${esc(T.pu.stimme)}</h2><p class="leise">${esc(T.pu.stimmeText)}</p>
        ${Object.entries(info.stimmen).map(([k, v]) => `<div class="zeile"><label><input type="radio" name="stimme" value="${k}" ${P.stimme === k ? "checked" : ""}>
          ${esc(v.name)} (${esc(T.pu.art[v.art] || v.art)})</label><span class="${v.bereit ? "gut" : "leise"}">${esc(v.bereit ? T.pu.geladen : T.pu.nichtGeladen)}</span>
          ${v.bereit ? "" : `<button class="knopf" data-laden="${k}" ${info.laden.laeuft ? "disabled" : ""}>${esc(info.laden.laeuft ? T.pu.laedtGerade : T.pu.laden)}</button>`}</div>`).join("")}
        ${info.laden.fehler ? `<p class="schlecht">${esc(info.laden.fehler)}</p>` : ""}
        <div class="zeile"><label><input type="checkbox" id="puVorlesen" ${P.vorlesen ? "checked" : ""}> ${esc(T.pu.vorlesen)}</label></div>
        <div class="zeile"><label><input type="checkbox" id="puGong" ${P.gong ? "checked" : ""}> ${esc(T.pu.gong)}</label></div>
        <div class="zeile"><label>${esc(T.pu.dauer)}</label><input type="number" id="puDauer" min="10" max="3600" value="${P.dauer_s}"></div></div>
      <div class="karte"><h2>${esc(T.pu.zugaenge)}</h2><p class="leise">${esc(T.pu.zugangText)}</p>
        ${P.zugaenge.map((z, i) => `<div class="eintrag" data-i="${i}">
          <div class="zeile"><label>${esc(T.pu.name)}</label><input type="text" name="zName" value="${esc(z.name)}"></div>
          <div class="zeile">${E.fernseher.map((t) => `<label><input type="checkbox" name="zTv" value="${esc(t.id)}" ${z.fernseher.includes(t.id) ? "checked" : ""}> ${esc(t.name)}</label>`).join(" ")}</div>
          <div class="zeile"><label><input type="checkbox" name="zAlarm" ${z.alarm ? "checked" : ""}> ${esc(T.pu.darfAlarm)}</label></div>
          <div class="zeile">${["meldung", "layout", "schalten"].map((r) => `<label><input type="checkbox" name="zRecht" value="${r}" ${z[r] ? "checked" : ""}> ${esc(T.pu.recht[r])}</label>`).join(" ")}</div>
          <div class="zeile"><input type="password" name="zPw" placeholder="${esc(T.pu.pwNeu)}" autocomplete="new-password">
            <span class="leise">${esc(z.passwort ? T.pu.pwGesetzt : T.pu.pwFehlt)}</span><button class="knopf gefahr" name="zWeg">${esc(T.pu.entfernen)}</button></div></div>`).join("")}
        <div class="zeile"><button class="knopf" id="zNeu">${esc(T.pu.zugangNeu)}</button></div></div>
      <div class="karte"><h2>${esc(T.pu.vorlagen)}</h2><p class="leise">${esc(T.pu.vorlagenText)}</p>
        <textarea id="puVorlagen" rows="5" class="breit">${esc(P.vorlagen.join("\n"))}</textarea>
        <div class="zeile"><button class="knopf haupt" id="puOk">${esc(T.speichern)}</button>
          <select id="puProbeTv">${E.fernseher.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select>
          <button class="knopf" id="puProbe">${esc(T.pu.probe)}</button></div></div>
      <div class="karte"><h2>⚠ ${esc(T.al.titel)}</h2><p class="leise">${esc(T.al.text)}</p>
        ${al.jetzt ? `<p class="schlecht"><b>${esc(T.al.laeuft(al.jetzt.zeit, al.jetzt.von))}:</b> ${esc(al.jetzt.text)}</p>` : ""}
        <label>${esc(T.al.vorlagen)}</label><textarea id="alVorlagen" rows="3" class="breit">${esc(A.vorlagen.join("\n"))}</textarea>
        <div class="zeile"><label><input type="checkbox" id="alTon" ${A.ton ? "checked" : ""}> ${esc(T.al.ton)}</label></div>
        <div class="zeile"><button class="knopf haupt" id="alOk">${esc(T.speichern)}</button>
          <select id="alTv"><option value="">${esc(T.al.alle)}</option>${E.fernseher.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select>
          <button class="knopf gefahr" id="alAn">${esc(T.al.an)}</button><button class="knopf" id="alAus" ${al.jetzt ? "" : "disabled"}>${esc(T.al.aus)}</button></div>
        <p class="leise">${esc(T.al.webhook)}</p><pre>curl -X POST http://${esc(info.eigene_ip || location.hostname)}:${esc(info.port)}/alarm -H "Authorization: Bearer …" -d '{"text": "…"}'
curl -X POST http://${esc(info.eigene_ip || location.hostname)}:${esc(info.port)}/alarm -H "Authorization: Bearer …" -d '{"aus": true}'</pre></div>`;
    const lesen = () => {                       // Eingaben in P übernehmen (vor Neuzeichnen und Speichern)
      P.stimme = (inhalt.querySelector("[name=stimme]:checked") || {}).value || P.stimme;
      P.vorlesen = $("#puVorlesen").checked; P.gong = $("#puGong").checked; P.dauer_s = Number($("#puDauer").value) || 60;
      P.vorlagen = $("#puVorlagen").value.split("\n").map((x) => x.trim()).filter(Boolean);
      A.vorlagen = $("#alVorlagen").value.split("\n").map((x) => x.trim()).filter(Boolean); A.ton = $("#alTon").checked;
      inhalt.querySelectorAll("[data-i]").forEach((el) => {
        const z = P.zugaenge[Number(el.dataset.i)];
        z.name = el.querySelector("[name=zName]").value.trim() || "Pult";
        z.fernseher = [...el.querySelectorAll("[name=zTv]:checked")].map((c) => c.value);
        z.alarm = el.querySelector("[name=zAlarm]").checked;
        el.querySelectorAll("[name=zRecht]").forEach((c) => { z[c.value] = c.checked; });
        const pw = el.querySelector("[name=zPw]").value;
        if (pw) z.passwort_neu = pw;
      });
    };
    inhalt.querySelectorAll("[name=zWeg]").forEach((b) => { b.onclick = () => { lesen(); P.zugaenge.splice(Number(b.closest("[data-i]").dataset.i), 1); zeichnen(); }; });
    $("#zNeu").onclick = () => { lesen(); P.zugaenge.push({ id: Math.random().toString(36).slice(2, 10).padEnd(8, "0"), name: "Rezeption", passwort: "", fernseher: [] }); zeichnen(); };
    $("#puOk").onclick = (e) => { lesen(); speichernE({ pult: P, alarm: A }, e.target).then(() => { Object.assign(P, JSON.parse(JSON.stringify(E.pult))); zeichnen(); }); };
    $("#alOk").onclick = $("#puOk").onclick;
    $("#alAn").onclick = (e) => {
      lesen();
      const text = A.vorlagen[0];
      if (!text || !confirm(T.al.wirklich + "\n\n" + text)) return;
      aktion(e.target, async () => { const r = await senden("/api/alarm", { text, fernseher: $("#alTv").value ? [$("#alTv").value] : [] });
        al.jetzt = r.jetzt; zeichnen(); }, T.al.ausgeloest);
    };
    $("#alAus").onclick = (e) => { lesen(); aktion(e.target, async () => { await senden("/api/alarm", { aus: true }); al.jetzt = null; zeichnen(); }, T.al.beendet); };
    $("#puProbe").onclick = (e) => aktion(e.target, () => senden("/api/pult/probe", { tv: $("#puProbeTv").value }), T.pu.probeOk);
    inhalt.querySelectorAll("[data-laden]").forEach((b) => { b.onclick = (e) => aktion(e.target, async () => {
      await senden("/api/pult/stimme-laden", { stimme: b.dataset.laden });
      clearInterval(timer);
      timer = setInterval(async () => { const i = await holen("/api/pult"); Object.assign(info, i); lesen(); zeichnen(); if (!i.laden.laeuft) clearInterval(timer); }, 3000);
    }, null); });
  };
  zeichnen();
}

// ---------- Downloads ----------
// Echter Download vom Datendienst: in Cockpit als „externer Kanal“ (https, der Browser speichert direkt, nichts im Speicher),
// im Docker-Betrieb über /laden/… der eigenen Verwaltung. Keine im Browser erzeugten Dateien (blob:) – die lädt Safari in
// der Cockpit-Verwaltung nicht herunter (seit 0.40.1 für alle Downloads).
const LADEN = { "/api/player/image": "/laden/player-image", "/api/ki/datei": "/laden/ki-datei", "/api/sicherung/datei": "/laden/sicherung",
                "/api/ablage": "/laden/ablage" };
function herunterladen(pfad, abfrage, datei, typ) {
  const q = new URLSearchParams(abfrage).toString();
  let url;
  if (CONTAINER) url = LADEN[pfad] + "?" + q;
  else {
    const opt = { payload: "http-stream2", address: "127.0.0.1", port: 8080, method: "GET", path: pfad + "?" + q,
                  headers: { "X-SignageCast": "1" }, binary: "raw",
                  external: { "content-disposition": `attachment; filename="${datei}"`, "content-type": typ } };
    url = "/cockpit/channel/" + cockpit.transport.csrf_token + "?" + window.btoa(JSON.stringify(opt));
  }
  const a = document.createElement("a");
  a.href = url; a.download = datei; document.body.appendChild(a); a.click(); a.remove();
}

// Im Browser erzeugte Datei (Layout-Export, KI-Anleitung): kurz beim Datendienst ablegen, dann echt herunterladen.
async function ablageLaden(datei, typ, text) {
  const r = await senden("/api/ablage", { name: datei, typ, inhalt: text });
  herunterladen("/api/ablage", { id: r.id }, datei, typ);
}

// ---------- Raspberry-Pi-Player (seit 0.23) ----------
function plHerunterladen(kennung, datei) {
  herunterladen("/api/player/image", { t: kennung }, datei, datei.endsWith(".iso") ? "application/octet-stream" : "application/gzip");
}
// Netzwerk-Auswahl (neu, Image erneut, WLAN ändern): Kabel | gespeichertes WLAN | neues WLAN
function plNetz(px, gespeichert, mitKabel) {
  return `<div class="zeile"><label>${esc(T.pl.netz)}</label><select name="${px}Art">
      ${mitKabel ? `<option value="kabel">${esc(T.pl.kabel)}</option>` : ""}
      ${gespeichert.map((s) => `<option value="g:${esc(s)}">${esc(T.pl.wlanGesp)}: ${esc(s)}</option>`).join("")}
      <option value="neu" ${!gespeichert.length && !mitKabel ? "selected" : ""}>${esc(T.pl.wlanNeu)}</option></select></div>
    <div data-neu="${px}"><div class="zeile"><label>${esc(T.pl.ssid)}</label><input type="text" name="${px}Ssid" maxlength="32" autocomplete="off"></div>
      <div class="zeile"><label>${esc(T.pl.pw)}</label><input type="password" name="${px}Pw" maxlength="63" autocomplete="new-password"></div>
      <div class="zeile"><label><input type="checkbox" name="${px}Merken"> ${esc(T.pl.merken)}</label></div>
      <p class="leise">${esc(T.pl.merkenText)}</p></div>`;
}
function plNetzAnbinden(wurzel, px) {
  const art = wurzel.querySelector(`[name=${px}Art]`), neu = wurzel.querySelector(`[data-neu=${px}]`);
  const sicht = () => { neu.hidden = art.value !== "neu"; };
  art.onchange = sicht; sicht();
  return () => art.value === "kabel" ? null : art.value.startsWith("g:") ? { gespeichert: art.value.slice(2) }
    : { ssid: wurzel.querySelector(`[name=${px}Ssid]`).value.trim(), passwort: wurzel.querySelector(`[name=${px}Pw]`).value,
        speichern: wurzel.querySelector(`[name=${px}Merken]`).checked };
}

// ---------- Fernwartung (seit 0.33): Terminal zum Pi, gezeichnet mit xterm.js (wie das Terminal in Cockpit) ----------
// Anderer Standort (seit 0.41) – nur, wenn Fernstandorte eingerichtet sind (P = Antwort von /api/player)
const fernBox = (P, id, an) => !P.fern ? "" : `<div class="zeile"><label><input type="checkbox" id="${id}" ${an ? "checked" : ""}> ${esc(P.fern.art === "headscale" ? T.fern.boxHs : T.fern.box)}</label></div>
  <p class="leise">${esc(P.fern.art === "link" ? T.fern.boxLink : T.fern.boxText(P.fern.server))}</p>`;
const fernAntwort = (r) => r && r.fern ? melden(r.fern === "entfernt" ? T.fern.entfernt : r.fern === "link" ? T.fern.entferntLink : r.fern === "nicht_gefunden" ? T.fern.nichtGefunden : T.fern.entferntFehler(r.fern_text), r.fern === "fehler") : null;
const fwBox = (id, an) => `<div class="zeile"><label><input type="checkbox" id="${id}" ${an ? "checked" : ""}> ${esc(T.pl.fw.image)}</label></div>
  <p class="leise">${esc(T.pl.fw.imageText)}</p>`;
let xtermGeladen = null;
function xtermLaden() {
  const datei = (src) => new Promise((ok, f) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = f; document.head.appendChild(s); });
  if (!xtermGeladen) {
    const css = document.createElement("link"); css.rel = "stylesheet"; css.href = "xterm/xterm.css"; document.head.appendChild(css);
    xtermGeladen = datei("xterm/xterm.js").then(() => datei("xterm/addon-fit.js"));
  }
  return xtermGeladen;
}
// xterm.js legt seine Maße und Farben als <style>-Elemente an; die Sicherheitsrichtlinie von Cockpit (style-src 'self')
// blockiert solche eingebetteten Stile. Statt sie zu lockern: Inhalt in ein programmatisch erzeugtes Stylesheet
// spiegeln (adoptedStyleSheets, von der Richtlinie nicht betroffen) und bei jeder Änderung nachziehen.
function xtermStileSpiegeln(wurzel) {
  const blatt = new CSSStyleSheet();
  document.adoptedStyleSheets = [...document.adoptedStyleSheets, blatt];
  const nachziehen = () => { try { blatt.replaceSync([...wurzel.querySelectorAll("style")].map((s) => s.textContent).join("\n")); } catch (_) { /* nächste Änderung */ } };
  const mo = new MutationObserver(nachziehen);
  mo.observe(wurzel, { subtree: true, childList: true, characterData: true });
  nachziehen();
  return () => { mo.disconnect(); document.adoptedStyleSheets = document.adoptedStyleSheets.filter((x) => x !== blatt); };
}
async function terminalOeffnen(g) {
  if (document.querySelector(".fw-fenster")) return;
  await xtermLaden();
  const f = document.createElement("div");
  f.className = "fw-fenster";
  f.innerHTML = `<div class="fw-kopf"><b>${esc(T.pl.fw.titel(g.name))}</b> <span class="leise" data-fw-status>${esc(T.pl.fw.verbinde)}</span>
      <button class="knopf gefahr" data-fw-ende>${esc(T.pl.fw.schliessen)}</button></div>
    <p class="leise fw-hinweis">${esc(T.pl.fw.hinweis)}</p><div class="fw-term"></div>`;
  document.body.appendChild(f);
  const term = new Terminal({ cursorBlink: true, fontSize: 14, scrollback: 5000, convertEol: false,
    fontFamily: '"DejaVu Sans Mono", "Liberation Mono", Menlo, Consolas, monospace', theme: { background: "#1e1e1e", foreground: "#e6e6e6" } });
  const fit = new FitAddon.FitAddon();
  term.loadAddon(fit);
  const stileEnde = xtermStileSpiegeln(f.querySelector(".fw-term"));
  term.open(f.querySelector(".fw-term"));
  fit.fit();
  term.focus();
  const status = (t) => { f.querySelector("[data-fw-status]").textContent = t; };
  const gelb = (t) => term.write(`\x1b[33m${t}\x1b[0m\r\n`);
  if (g.bericht && g.bericht.schreibschutz) gelb(T.pl.fw.schreibschutz);
  let sid = null, offen = true, puffer = "", sendet = false, groesse = null;
  const pfad = (x) => `/api/player/${g.id}/terminal/${x}`;
  const schliessen = async (grund) => {
    if (!offen) return;
    offen = false;
    status(T.pl.fw.beendet(T.pl.fw.gruende[grund] || grund));
    gelb("\r\n" + T.pl.fw.beendet(T.pl.fw.gruende[grund] || grund));
    window.removeEventListener("resize", anpassen);
    f.querySelector("[data-fw-ende]").textContent = T.pl.fw.zu;
    f.querySelector("[data-fw-ende]").onclick = () => { term.dispose(); stileEnde(); f.remove(); };
  };
  const senden_ = async () => {           // Eingaben bündeln: höchstens eine Anfrage gleichzeitig
    if (sendet || !sid || !offen || (!puffer && !groesse)) return;
    sendet = true;
    const text = puffer, gr = groesse;
    puffer = ""; groesse = null;
    try { await senden(pfad("ein"), Object.assign({ sid, text }, gr ? { spalten: gr.cols, zeilen: gr.rows } : {})); }
    catch (_) { /* nächster Versuch mit der nächsten Eingabe */ }
    sendet = false;
    if (puffer || groesse) senden_();
  };
  term.onData((t) => { puffer += t; senden_(); });
  term.onResize((r) => { groesse = r; senden_(); });
  const anpassen = () => { try { fit.fit(); } catch (_) { /* Fenster zu */ } };
  window.addEventListener("resize", anpassen);
  f.querySelector("[data-fw-ende]").onclick = async () => {
    if (sid) { try { await senden(pfad("ende"), { sid }); } catch (_) { /* egal */ } }
    schliessen("verwaltung");
  };
  let wer = "";
  try { wer = cockpit.user ? ((await cockpit.user()) || {}).name || "" : ""; } catch (_) { wer = ""; }
  try {
    sid = (await senden(pfad("start"), { spalten: term.cols, zeilen: term.rows, wer: wer || (CONTAINER ? "verwaltung" : "cockpit") })).sid;
  } catch (e) {
    gelb(e.message);
    return schliessen("unbekannt");
  }
  let ab = 0, verbunden = false;
  while (offen) {
    let d;
    try { d = JSON.parse(await dienst.get(pfad("aus"), { sid, ab }, KOPF)); }
    catch (_) { await new Promise((r) => setTimeout(r, 1500)); continue; }
    if (d.verloren) gelb(T.pl.fw.verloren);
    if (d.daten) {
      const roh = atob(d.daten), bytes = new Uint8Array(roh.length);
      for (let i = 0; i < roh.length; i++) bytes[i] = roh.charCodeAt(i);
      term.write(bytes);
    }
    ab = d.ab;
    if (!verbunden && d.zustand === "offen") { verbunden = true; status(T.pl.fw.verbunden); }
    if (d.zustand === "zu") return schliessen(d.grund || "unbekannt");
  }
}

async function playerSeite(inhalt) {
  const holenP = async () => Object.assign(await holen("/api/player"), { _geholt: Date.now() });     // Zeitpunkt für „vor X s“
  let P = await holenP();
  const tvOpt = (w) => `<option value="">${esc(T.pl.keinTv)}</option>` + E.fernseher.map((t) => `<option value="${esc(t.id)}" ${t.id === w ? "selected" : ""}>${esc(t.name)}</option>`).join("");
  const opt = (werte, w, texte) => werte.map((x) => `<option value="${esc(x)}" ${String(x) === String(w) ? "selected" : ""}>${esc(texte ? texte[x] : x)}</option>`).join("");
  const mb = (b) => Math.round(b / 1e6);
  const basisText = (pc) => {
    const b = pc ? P.basis_pc : P.basis;
    if (b.phase === "laedt") return `<span class="warn">${esc(T.pl.basisLaedt(mb(b.geladen), mb(b.gesamt) || "…"))}</span>`;
    const f = b.phase === "fehler" ? `<span class="schlecht">${esc(T.pl.basisFehler)}: ${esc(meldungText(b, b.fehler))}</span> ` : "";
    return f + (b.vorhanden ? `<span class="gut">${esc(T.pl.basisBereit(b.vorhanden.version, b.vorhanden.erstellt || ""))}</span>` : esc(pc ? T.pl.pc.basisFehlt : T.pl.basisFehlt));
  };
  // Modelle (seit 0.36 auch PC und Browser-Gerät); ein Browser-Gerät bleibt eines, andere werden keines
  const MT = () => Object.assign({}, T.pl.m, { pc: T.pl.pc.m, browser: T.pl.br.m });
  const bereitFuer = (m) => m === "browser" || !!(m === "pc" ? P.basis_pc : P.basis).vorhanden;
  const laedt = () => P.basis.phase === "laedt" || P.basis_pc.phase === "laedt";
  const formWahl = (id) => `<div class="zeile" data-nur-pc><label>${esc(T.pl.pc.format)}</label><select id="${id}">${opt(["gz", "iso"], "gz", T.pl.pc.f)}</select></div>
    <p class="leise" data-nur-pc>${esc(T.pl.pc.formatText)}</p>`;
  const schritteHtml = (pc) => { const q = pc ? T.pl.pc : T.pl; return `<h3>${esc(T.pl.schritte)}</h3><ol><li>${esc(q.s1)}</li><li>${esc(q.s2)}</li><li>${esc(q.s3)}</li><li>${esc(q.s4)}</li></ol>`; };
  const wartendText = () => (P.wartend || []).length
    ? T.pl.wartend(P.wartend.length) + ": " + P.wartend.map((w) => [w.modell, w.ip].filter(Boolean).join(" · ")).join(", ") : T.pl.keinerWartet;
  const zeichnen = () => {
    const bereit = !!P.basis.vorhanden;
    inhalt.innerHTML = `<div class="karte"><h2>${esc(T.pl.titel)}</h2><p>${esc(T.pl.text)}</p>
        <p class="leise">${esc(T.pl.modelle)}</p><p class="leise">${esc(T.pl.bedarf)}</p><p class="leise warn">${esc(T.pl.experimentell)}</p>
        <div class="zeile"><label>${esc(T.pl.basis)}</label><span id="plBasis">${basisText(false)}</span>
          <button class="knopf" id="plBasisLaden" ${laedt() ? "disabled" : ""}>${esc(bereit ? T.pl.basisNeu : T.pl.basisLaden)}</button></div>
        <h3>${esc(T.pl.pc.titel)}</h3><p>${esc(T.pl.pc.text)}</p><p class="leise">${esc(T.pl.pc.bedarf)}</p>
        <div class="zeile"><label>${esc(T.pl.pc.basis)}</label><span id="plBasisPc">${basisText(true)}</span>
          <button class="knopf" id="plBasisPcLaden" ${laedt() ? "disabled" : ""}>${esc(P.basis_pc.vorhanden ? T.pl.basisNeu : T.pl.basisLaden)}</button></div>
        <h3>${esc(T.pl.br.titel)}</h3><p class="leise">${esc(T.pl.br.text)}</p>
        ${P.container ? `<p class="leise">${esc(T.pl.port(P.webhook_port))}</p>` : ""}</div>
      <div class="karte" id="plNeu"><h2>${esc(T.pl.neu)}</h2>
        <div class="zeile"><label>${esc(T.pl.name)}</label><input type="text" id="plName" maxlength="40" placeholder="${esc(T.pl.namePlatz)}"></div>
        <div class="zeile"><label>${esc(T.pl.tv)}</label><select id="plTv">${tvOpt(E.fernseher[0] ? E.fernseher[0].id : "")}</select></div>
        <div class="zeile"><label>${esc(T.pl.modell)}</label><select id="plModell">${opt(["pi45", "pi3", "pc", "browser"], "pi45", MT())}</select></div>
        <div data-nur-image><p class="leise" data-nur-pi>${esc(T.pl.ram)}</p>
          ${plNetz("n", P.wlan, true)}
          ${fwBox("plFw")}
          ${fernBox(P, "plFern")}
          ${formWahl("plForm")}</div>
        <div class="zeile"><button class="knopf haupt" id="plErstellen" ${bereit ? "" : "disabled"}>${esc(T.pl.erstellen)}</button></div>
        <div id="plSchritte" hidden></div>
        <details class="erweitert"><summary>${esc(T.pl.erweitert)}</summary>
          <div class="zeile"><label>${esc(T.pl.server)}</label><input type="text" id="plServer" value="${esc(P.server)}" placeholder="${esc(P.server_auto || `http://${location.hostname}:${P.webhook_port}`)}"></div>
          <p class="leise">${esc(T.pl.serverText)}</p>
          <div class="zeile"><label>${esc(T.pl.streamPort)}</label><input type="number" id="plStreamPort" min="1" max="65535" value="${P.stream_port || ""}" placeholder="${P.hls_port}"></div>
          <p class="leise">${esc(T.pl.streamPortText)}</p>
          <div class="zeile"><button class="knopf" id="plServerOk">${esc(T.speichern)}</button></div>
          ${P.wlan.length ? `<h3>${esc(T.pl.gespeicherte)}</h3>${P.wlan.map((s) => `<div class="zeile"><span>${esc(s)}</span>
            <button class="knopf klein" data-vergessen="${esc(s)}">${esc(T.pl.vergessen)}</button></div>`).join("")}` : ""}</details></div>
      <div class="karte" id="plKop"><h2>${esc(T.pl.koppeln)}</h2><p class="leise">${esc(T.pl.koppelnText)}</p>
        <div class="zeile"><label>${esc(T.pl.fuer)}</label><select id="plSArt">${opt(["pi", "pc"], "pi", { pi: "Raspberry Pi", pc: T.pl.pc.m })}</select></div>
        ${plNetz("s", P.wlan, true)}
        ${fwBox("plSFw")}
        ${formWahl("plSForm")}
        <div class="zeile"><button class="knopf" id="plSammel" ${bereit ? "" : "disabled"}>${esc(T.pl.sammelImage)}</button></div>
        <p id="plWartend" class="leise">${wartendText()}</p>
        <div class="zeile"><label>${esc(T.pl.code)}</label><input type="text" id="plCode" inputmode="numeric" maxlength="7" autocomplete="off" placeholder="${esc(T.pl.codePlatz)}"></div>
        <div class="zeile"><label>${esc(T.pl.name)}</label><input type="text" id="plKName" maxlength="40" placeholder="${esc(T.pl.namePlatz)}"></div>
        <div class="zeile"><label>${esc(T.pl.tv)}</label><select id="plKTv">${tvOpt(E.fernseher[0] ? E.fernseher[0].id : "")}</select></div>
        <div class="zeile"><button class="knopf haupt" id="plKoppeln">${esc(T.pl.koppelnKnopf)}</button></div></div>
      <h2>${esc(T.pl.liste)}</h2><div id="plListe"></div>`;
    const netzSammel = plNetzAnbinden($("#plKop"), "s");
    const kopSicht = () => {
      const pc = $("#plSArt").value === "pc";
      $("#plKop").querySelectorAll("[data-nur-pc]").forEach((x) => { x.hidden = !pc; });
      $("#plSammel").disabled = !bereitFuer(pc ? "pc" : "pi45");
    };
    $("#plSArt").onchange = kopSicht; kopSicht();
    $("#plSammel").onclick = (e) => aktion(e.target, async () => {
      const pc = $("#plSArt").value === "pc";
      const d = await senden("/api/player/sammel-image", { wlan: netzSammel(), fernwartung: $("#plSFw").checked, art: pc ? "pc" : "pi", form: $("#plSForm").value,
        server: $("#plServer").value.trim() || P.server_auto || `http://${location.hostname}:${P.webhook_port}` });
      plHerunterladen(d.kennung, d.datei);
      $("#plSchritte").innerHTML = schritteHtml(pc); $("#plSchritte").hidden = false;
    }, T.pl.laedtHerunter);
    $("#plKoppeln").onclick = (e) => aktion(e.target, async () => {
      await senden("/api/player/koppeln", { code: $("#plCode").value, name: $("#plKName").value, tv: $("#plKTv").value });
      $("#plCode").value = ""; $("#plKName").value = "";
      P = await holenP(); $("#plWartend").textContent = wartendText(); listeZeichnen();
    }, T.pl.gekoppelt);
    const netzNeu = plNetzAnbinden($("#plNeu"), "n");
    const neuSicht = () => {
      const m = $("#plModell").value;
      $("#plNeu").querySelector("[data-nur-image]").hidden = m === "browser";
      $("#plNeu").querySelectorAll("[data-nur-pc]").forEach((x) => { x.hidden = m !== "pc"; });
      $("#plNeu").querySelectorAll("[data-nur-pi]").forEach((x) => { x.hidden = m === "pc"; });
      $("#plErstellen").textContent = m === "browser" ? T.pl.br.erstellen : T.pl.erstellen;
      $("#plErstellen").disabled = !bereitFuer(m);
    };
    $("#plModell").onchange = neuSicht; neuSicht();
    const basisLaden = (art) => (e) => aktion(e.target, async () => {
      await senden("/api/player/basis-laden", { art }); (art === "pc" ? P.basis_pc : P.basis).phase = "laedt"; zeichnen(); beobachten(); }, null);
    $("#plBasisLaden").onclick = basisLaden("pi");
    $("#plBasisPcLaden").onclick = basisLaden("pc");
    $("#plErstellen").onclick = (e) => {
      const m = $("#plModell").value;
      aktion(e.target, async () => {
        const r = await senden("/api/player/neu", { name: $("#plName").value, tv: $("#plTv").value, modell: m });
        if (m !== "browser") {
          const wlan = netzNeu();
          let d;
          try { d = await senden(`/api/player/${r.geraet}/image`, { wlan, fernwartung: $("#plFw").checked, fern: !!($("#plFern") && $("#plFern").checked), form: $("#plForm").value, server: $("#plServer").value.trim() || P.server_auto || `http://${location.hostname}:${P.webhook_port}` }); }
          catch (f) { await senden(`/api/player/${r.geraet}/entfernen`); throw f; }        // ohne Image kein halbes Gerät zurücklassen
          plHerunterladen(d.kennung, d.datei);
          $("#plSchritte").innerHTML = schritteHtml(m === "pc"); $("#plSchritte").hidden = false;
        }
        $("#plName").value = "";
        P = await holenP(); listeZeichnen();
      }, m === "browser" ? null : T.pl.laedtHerunter);
    };
    $("#plServerOk").onclick = (e) => aktion(e.target, async () => {
      await senden("/api/player/einstellungen", { server: $("#plServer").value.trim(), stream_port: Number($("#plStreamPort").value) || 0 });
      P = await holenP();
    });
    inhalt.querySelectorAll("[data-vergessen]").forEach((b) => { b.onclick = (e) => aktion(e.target, async () => {
      await senden("/api/player/wlan-vergessen", { ssid: b.dataset.vergessen }); P = await holenP(); zeichnen(); }); });
    listeZeichnen();
  };
  const linkUrl = (g) => (P.server || P.server_auto || `http://${location.hostname}:${P.webhook_port}`) + g.link_pfad;
  const karteBrowser = (g) => {           // Browser-Gerät (seit 0.36): nur Link, Status aus den Datenabrufen der Seite
    const ort = ORT();
    const zeit = (ts) => ts ? new Date(ts * 1000).toLocaleString(ort, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "–";
    const status = g.online ? `<span class="gut">● ${esc(T.pl.online)}</span>`
      : g.zuletzt ? `<span class="schlecht">● ${esc(T.pl.offline)}</span> <span class="leise">${esc(T.pl.zuletzt(zeit(g.zuletzt)))}</span>`
      : `<span class="leise">● ${esc(T.pl.nieGesehen)}</span>`;
    return `<div class="karte" data-g="${g.id}"><h2>${esc(g.name)} <small>${status}</small></h2>
      <p class="leise">${esc(T.pl.br.titel)}</p>
      ${g.hinweise.map((h) => `<p class="warn">⚠ ${esc(T.pl.h[h] || h)}</p>`).join("")}
      <div class="zeile"><label>${esc(T.pl.br.link)}</label><input type="text" readonly data-link value="${esc(linkUrl(g))}">
        <button class="knopf" data-kopieren>${esc(T.pl.br.kopieren)}</button></div>
      <p class="leise">${esc(T.pl.br.linkText)}</p>
      <details class="erweitert"><summary>${esc(T.bereiche.einstellungen)}</summary>
        <div class="zeile"><label>${esc(T.pl.name)}</label><input type="text" name="name" maxlength="40" value="${esc(g.name)}"></div>
        <div class="zeile"><label>${esc(T.pl.tv)}</label><select name="tv">${tvOpt(g.tv)}</select></div>
        <div class="zeile"><button class="knopf haupt" data-speichern>${esc(T.speichern)}</button></div>
        <div class="zeile"><button class="knopf" data-link-neu>${esc(T.pl.br.neu)}</button>
          <button class="knopf gefahr" data-entfernen>${esc(T.pl.entfernen)}</button></div></details></div>`;
  };
  const browserAnbinden = (k, g) => {
    k.querySelector("[data-kopieren]").onclick = async (e) => {
      const f = k.querySelector("[data-link]");
      f.select();
      try { await navigator.clipboard.writeText(f.value); } catch (_) { document.execCommand("copy"); }
      e.target.textContent = T.pl.br.kopiert;
      setTimeout(() => { e.target.textContent = T.pl.br.kopieren; }, 2000);
    };
    k.querySelector("[data-speichern]").onclick = (e) => aktion(e.target, async () => {
      await senden(`/api/player/${g.id}/aendern`, { name: k.querySelector("[name=name]").value, tv: k.querySelector("[name=tv]").value });
      P = await holenP(); listeZeichnen();
    });
    k.querySelector("[data-link-neu]").onclick = (e) => {
      if (!confirm(T.pl.br.neuFrage)) return;
      aktion(e.target, async () => { await senden(`/api/player/${g.id}/link-neu`); P = await holenP(); listeZeichnen(); }, T.pl.br.neuOk);
    };
    k.querySelector("[data-entfernen]").onclick = (e) => {
      if (!confirm(T.pl.entfernenFrage(g.name))) return;
      aktion(e.target, async () => { await senden(`/api/player/${g.id}/entfernen`); P = await holenP(); listeZeichnen(); });
    };
  };
  // Fernverwaltung (seit 0.43): letzte Meldung live und was an den Player ging – gesendet → abgeholt → Ergebnis
  const jetztS = () => (P.jetzt || Date.now() / 1000) + (Date.now() - (P._geholt || Date.now())) / 1000;
  const dauer = (s) => { s = Math.max(0, Math.round(s)); return s < 90 ? `${s} s` : s < 5400 ? `${Math.round(s / 60)} min` : `${Math.round(s / 3600)} h`; };
  const vorHtml = (g) => {
    const vor = g.zuletzt_vor + (Date.now() - (P._geholt || Date.now())) / 1000;
    const k = vor <= 30 ? "gut" : vor <= 60 ? "warn" : "schlecht";
    return `<span class="${k}">● ${esc(vor <= 60 ? T.pl.online : T.pl.offline)}</span> <span class="leise">${esc(T.pl.vor(dauer(vor)))}</span>`;
  };
  const fvOffen = new Set(), fvStand = new WeakMap();
  const fvUhr = (ts) => ts ? new Date(ts * 1000).toLocaleTimeString(ORT(), { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : "";
  const fvTag = (ts) => { const d = new Date(ts * 1000); return d.toDateString() === new Date().toDateString() ? fvUhr(ts)
    : d.toLocaleString(ORT(), { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }); };
  const fvWert = (was, w) => was === "anzeige_modus" ? T.pl.fv.modus[w] || w : was === "drehung" ? `${w}°` : was === "aufloesung" ? T.pl.a[w] || w
    : was === "lautstaerke" ? `${w} %` : was === "hwdec" ? T.pl.hw[w] || w : was === "schreibschutz" ? (w ? T.pl.fv.an : T.pl.fv.aus)
    : was === "tv" ? ((E.fernseher.find((t) => t.id === w) || {}).name || w || "–") : String(w ?? "–");
  const fvWas = (e) => e.art === "befehl" ? T.pl.b[e.was] || e.was : e.art === "wlan" ? `${T.pl.fv.e.wlan} ${T.pl.zitat(e.wert)}`
    : `${T.pl.fv.e[e.was] || e.was}: ${fvWert(e.was, e.alt)} → ${fvWert(e.was, e.wert)}`;
  const fvOffenE = (e) => !e.fertig;
  const fvKopf = (g) => {
    const n = g.verlauf.filter(fvOffenE).length;
    if (n) return `<span class="warn">· ${esc(T.pl.fv.unterwegs(n))}</span>`;
    const e = g.verlauf[0];
    if (!e) return "";
    const z = e.ok === true ? `<span class="gut">✓</span>` : e.ok === false ? `<span class="schlecht">✗</span>` : "–";
    return `<span class="leise">· ${esc(T.pl.fv.zuletzt(fvWas(e), fvTag(e.gesendet)))}</span> ${z}`;
  };
  const fvStufe = (e) => {
    const jetzt = jetztS();
    if (!e.abgeholt && !e.fertig) return jetzt - e.gesendet > 120 ? `<span class="warn">⚠ ${esc(T.pl.fv.offline)}</span>` : `<span class="warn">… ${esc(T.pl.fv.wartet)}</span>`;
    const ab = e.abgeholt ? `<span class="leise">${esc(T.pl.fv.abgeholt(dauer(e.abgeholt - e.gesendet)))}</span>` : "";
    const h = e.hinweis ? ` (${esc(T.pl.fv.h[e.hinweis] || e.hinweis)})` : "";
    if (!e.fertig) return `${ab} → <span class="warn">${esc(T.pl.fv.umsetzen)}</span>`;
    if (e.ok === null) return `<span class="leise">${ab ? ab + " → " : ""}${esc(T.pl.fv.h[e.hinweis] || e.hinweis || "–")}</span>`;
    if (e.ok === false) return `${ab} → <span class="schlecht">✗ ${esc(T.pl.fv.fehler)}</span>${h}`;
    const text = e.was === "anzeige_modus" ? T.pl.fv.modusOk(fvWert(e.was, e.hinweis === "nur_stream" ? "stream" : e.wert))
      : e.art === "einstellung" && e.was !== "schreibschutz" ? T.pl.fv.uebernommen : T.pl.fv.ok;
    return `${ab} → <span class="gut">✓ ${esc(text)}</span>${e.hinweis === "nur_stream" ? h : ""}`;
  };
  const fvListe = (g) => {
    const zeilen = g.verlauf.map((e) => ({ t: e.gesendet, html: `<b>${esc(fvWas(e))}</b> <span class="leise">${esc(e.wer === "auto" ? T.pl.fv.auto : e.wer)}</span> – ${fvStufe(e)}` }));
    for (const x of g.fernwartung_protokoll || [])
      zeilen.push({ t: x.start, html: `<b>${esc(T.pl.fv.terminal)}</b> <span class="leise">${esc(x.wer)}</span> – ${dauer(x.ende - x.start)} · ${esc(T.pl.fw.gruende[x.grund] || x.grund)}` });
    if (g.terminal) zeilen.push({ t: g.terminal.start, html: `<b>${esc(T.pl.fv.terminal)}</b> <span class="leise">${esc(g.terminal.wer)}</span> – <span class="warn">${esc(T.pl.fv.laeuft)}</span>` });
    zeilen.sort((a, b) => b.t - a.t);
    return zeilen.length ? `<ul class="fv-liste">${zeilen.map((z) => `<li><span class="leise">${esc(fvTag(z.t))}</span> ${z.html}</li>`).join("")}</ul>`
      : `<p class="leise">${esc(T.pl.fv.leer)}</p>`;
  };
  // jede Sekunde: Alter der Meldung und offene Einträge nachführen, ohne die Karte neu zu zeichnen
  const fvTicken = () => {
    for (const g of P.geraete) {
      const k = inhalt.querySelector(`[data-g="${g.id}"]`);
      if (!k) continue;
      const v = k.querySelector("[data-vor]");
      if (v && g.zuletzt_vor != null) v.innerHTML = vorHtml(g);
      for (const [sel, html] of [["[data-fv-kopf]", fvKopf(g)], ["[data-fv-liste]", fvListe(g)]]) {
        const x = k.querySelector(sel);
        if (x && fvStand.get(x) !== html) { x.innerHTML = html; fvStand.set(x, html); }
      }
    }
  };
  const karte = (g) => {
    if (g.modell === "browser") return karteBrowser(g);
    const pc = g.modell === "pc";
    const b = g.bericht || {}, v = b.video || {};
    const ort = ORT();
    const zeit = (ts) => ts ? new Date(ts * 1000).toLocaleString(ort, { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "–";
    const uhr = (e) => e.ts ? new Date(e.ts * 1000).toLocaleTimeString(ort, { hour: "2-digit", minute: "2-digit" }) : e.zeit;
    const status = g.zuletzt_vor != null ? `<span data-vor="${g.id}">${vorHtml(g)}</span>`
      : g.zuletzt ? `<span class="schlecht">● ${esc(T.pl.offline)}</span> <span class="leise">${esc(T.pl.zuletzt(zeit(g.zuletzt)))}</span>`
      : `<span class="leise">● ${esc(T.pl.nieGesehen)}</span>`;
    const netz = b.netz ? (T.pl.netzArt[b.netz] || b.netz) + (b.ssid ? " " + T.pl.zitat(b.ssid) : "") + (b.signal != null ? ` ${b.signal} %` : "") : "–";
    const zeilen = g.zuletzt ? [[T.pl.modell, b.modell + (b.ram_mb > 0 ? " · " + (pc ? (Math.round(b.ram_mb / 102.4) / 10).toLocaleString(ORT()) + " GB" : ramNenn(b.ram_mb)) : "")], [T.pl.ip, g.ip], [T.pl.netz, netz],
      [T.pl.hdmi, b.hdmi ? (b.tv_name || "HDMI") + (b.ausgang ? ` (${b.ausgang})` : "") : T.pl.keinHdmi],
      [T.pl.video, b.modus_ist === "direkt" ? T.pl.direktModus : v.codec ? `${v.codec} ${v.breite}×${v.hoehe}${v.hwdec && v.hwdec !== "no" ? " · " + v.hwdec : ""}` : (T.pl.zustand[b.zustand] || b.zustand || "–") + (b.zustand_text ? ` – ${b.zustand_text}` : "")],
      [T.pl.temp, b.temperatur ? b.temperatur + " °C" : "–"], [T.pl.version, b.version], [T.pl.netzwerke, (b.netze || []).join(", ") || "–"],
      [T.pl.update, b.letztes_update ? zeit(b.letztes_update.zeit) + (b.letztes_update.ok ? "" : " – " + T.pl.fehlgeschlagen) : "–"]] : [];
    if (g.fern) {                         // anderer Standort (seit 0.41)
      const f = b.fern || {};
      zeilen.push([T.fern.zeile, f.fehler ? "⚠ " + (T.fern.fehler[f.fehler] || f.fehler) : f.ip ? `${f.ip}${f.weg ? " · " + (f.weg === "direkt" ? T.fern.direkt : T.fern.relay(f.weg.replace(/^relay:/, ""))) : ""}`
        : g.fern.ip ? g.fern.ip : T.fern.wartet]);
    }
    return `<div class="karte" data-g="${g.id}"><h2>${esc(g.name)} <small>${status}</small></h2>
      ${g.online ? `<p><b>${esc(T.pl.zustand[b.zustand] || b.zustand || "")}</b>${b.zustand === "stream_fehler" && b.zustand_text ? ` – ${esc(b.zustand_text)}` : ""}</p>` : ""}
      ${g.hinweise.map((h) => `<p class="warn">⚠ ${esc(T.pl.h[h] || h)}</p>`).join("")}
      ${g.wlan_offen && !g.verlauf.some((e) => e.art === "wlan" && !e.fertig) ? `<p class="warn">${esc(T.pl.wlanOffen(g.wlan_offen))}</p>` : ""}
      ${g.fern && b.fern && b.fern.url && !b.fern.ip ? `<div class="zeile"><a class="knopf haupt" href="${esc(b.fern.url)}" target="_blank" rel="noopener">${esc(T.fern.freigeben)}</a></div><p class="leise">${esc(T.fern.freigebenText)}</p>` : ""}
      ${g.fern && b.fern && b.fern.ohne_tag ? `<p class="warn">⚠ ${esc(T.fern.ohneTag)}</p>` : ""}
      ${g.bild ? `<p><img src="" data-bild="${g.id}" alt="${esc(T.pl.bildAlt(zeit(g.bild)))}" title="${esc(T.pl.bildAlt(zeit(g.bild)))}" class="pl-bild"></p>` : ""}
      ${zeilen.length ? `<div class="tabelle-rahmen"><table class="tabelle">${zeilen.map(([k, w]) => `<tr><td class="leise">${esc(k)}</td><td>${esc(w ?? "–")}</td></tr>`).join("")}</table></div>` : ""}
      ${pc ? `<p class="leise">${esc(T.pl.pc.live)}</p>` : ""}
      <div class="zeile">${["bild", "erkennen", "cec_an", "cec_aus", "player_neu", "neustart", "systemupdate", "protokoll"].filter((a) => !pc || (a !== "systemupdate" && (b.cec || !a.startsWith("cec")))).map((a) =>
        `<button class="knopf" data-befehl="${a}" title="${esc(T.pl.bText[a] || "")}">${esc(pc && a === "neustart" ? T.pl.pc.neustart : T.pl.b[a])}</button>`).join("")}
        ${g.protokoll ? `<button class="knopf" data-protokoll>${esc(T.pl.protokollZeigen)}</button>` : ""}</div>
      ${g.online ? (g.fernwartung ? `<div class="zeile"><button class="knopf haupt" data-terminal title="${esc(T.pl.fw.knopfText)}"><span class="mdi mdi-console"></span> ${esc(T.pl.fw.knopf)}</button>
        ${g.terminal ? `<span class="warn">${esc(T.pl.fw.laeuft(zeit(g.terminal.start), g.terminal.wer))}</span>` : ""}</div>`
        : `<p class="leise">${esc("fernwartung" in b ? T.pl.fw.aus : T.pl.fw.alt)}</p>`) : ""}
      <details class="erweitert" data-fv="${g.id}" ${fvOffen.has(g.id) ? "open" : ""}><summary>${esc(T.pl.fv.titel)} <span data-fv-kopf>${fvKopf(g)}</span></summary>
        <p class="leise">${esc(T.pl.fv.text)}</p><div data-fv-liste>${fvListe(g)}</div></details>
      <pre data-log hidden class="pl-log"></pre>
      <details class="erweitert"><summary>${esc(T.bereiche.einstellungen)}</summary>
        <div class="zeile"><label>${esc(T.pl.name)}</label><input type="text" name="name" maxlength="40" value="${esc(g.name)}"></div>
        <div class="zeile"><label>${esc(T.pl.tv)}</label><select name="tv">${tvOpt(g.tv)}</select></div>
        <div class="zeile"><label>${esc(T.pl.modell)}</label><select name="modell">${opt(["pi45", "pi3", "pc"], g.modell, MT())}</select></div>${pc ? "" : `<p class="leise">${esc(T.pl.ram)}</p>`}
        <div class="zeile"><label>${esc(T.pl.drehung)}</label><select name="drehung">${opt([0, 90, 180, 270], g.drehung, { 0: "0°", 90: "90°", 180: "180°", 270: "270°" })}</select></div>
        <div class="zeile"><label>${esc(T.pl.aufloesung)}</label><select name="aufloesung">${opt(["auto", "720", "1080", "2160"], g.aufloesung, T.pl.a)}</select></div>
        <div class="zeile"><label>${esc(T.pl.lautstaerke)}</label><input type="number" name="lautstaerke" min="0" max="100" value="${g.lautstaerke}"></div>
        <div class="zeile"><label><input type="checkbox" name="cec_zeitplan" ${g.cec_zeitplan ? "checked" : ""}> ${esc(T.pl.cec)}</label></div><p class="leise">${esc(T.pl.cecText)}</p>
        <div ${pc ? "hidden" : ""}><div class="zeile"><label><input type="checkbox" name="schreibschutz" ${g.schreibschutz ? "checked" : ""}> ${esc(T.pl.schreibschutz)}</label></div><p class="leise">${esc(T.pl.schreibschutzText)}</p>
        <div class="zeile"><label>${esc(T.pl.systemupdate)}</label><select name="systemupdate">${opt(["woechentlich", "aus"], g.systemupdate, T.pl.su)}</select></div></div>
        <div class="zeile"><label>${esc(T.pl.hwdec)}</label><select name="hwdec">${opt(["auto", "aus"], g.hwdec, T.pl.hw)}</select></div>
        <div class="zeile" data-anzeige ${g.modell === "pi3" ? "hidden" : ""}><label>${esc(T.pl.anzeige)}</label><select name="anzeige_modus">${opt(["stream", "direkt"], g.anzeige_modus || "stream", T.pl.am)}</select></div>
        <p class="leise" data-anzeige ${g.modell === "pi3" ? "hidden" : ""}>${esc(T.pl.anzeigeText)}</p>
        <div class="zeile"><button class="knopf haupt" data-speichern>${esc(T.speichern)}</button></div></details>
      <details class="erweitert" data-wlan><summary>${esc(T.pl.wlanAendern)}</summary><p class="leise">${esc(T.pl.wlanAendernText)}</p>
        ${plNetz("w" + g.id, P.wlan, false)}<div class="zeile"><button class="knopf" data-wlan-senden>${esc(T.pl.wlanSenden)}</button></div></details>
      <details class="erweitert" data-image><summary>${esc(T.pl.imageNeu)}</summary><p class="leise">${esc(T.pl.imageNeuText)}</p>
        ${plNetz("i" + g.id, P.wlan, true)}${fwBox("plIFw" + g.id, g.fernwartung)}${fernBox(P, "plIFern" + g.id, !!g.fern)}${pc ? formWahl("plIForm" + g.id) : ""}<div class="zeile"><button class="knopf" data-image-laden ${bereitFuer(g.modell) ? "" : "disabled"}>${esc(T.pl.erstellen)}</button>
        <button class="knopf gefahr" data-entfernen>${esc(T.pl.entfernen)}</button></div></details></div>`;
  };
  const bilderLaden = () => inhalt.querySelectorAll("img[data-bild]").forEach(async (i) => {
    try {
      const roh = await dienstBinaer.get(`/api/player/${i.dataset.bild}/bild`, { t: Date.now() }, { "X-SignageCast": "1" });
      const png = roh && roh[0] === 0x89 && roh[1] === 0x50;          // Direktmodus: PNG (grim ohne JPEG, seit 0.36)
      i.src = URL.createObjectURL(new Blob([roh], { type: png ? "image/png" : "image/jpeg" }));
    }
    catch (_) { i.remove(); }
  });
  const listeZeichnen = () => {
    const ziel = $("#plListe");
    if (!ziel) return;
    ziel.innerHTML = P.geraete.length ? P.geraete.map(karte).join("") : `<p class="leise">${esc(T.pl.keine)}</p>`;
    ziel.querySelectorAll("details[data-fv]").forEach((d) => { d.ontoggle = () => { if (d.open) fvOffen.add(d.dataset.fv); else fvOffen.delete(d.dataset.fv); }; });
    bilderLaden();
    for (const g of P.geraete) {
      const k = ziel.querySelector(`[data-g="${g.id}"]`);
      if (g.modell === "browser") { browserAnbinden(k, g); continue; }
      const wlanLesen = plNetzAnbinden(k, "w" + g.id), imageLesen = plNetzAnbinden(k, "i" + g.id);
      k.querySelectorAll("[data-befehl]").forEach((b) => { b.onclick = (e) => aktion(e.target, async () => {
        await senden(`/api/player/${g.id}/befehl`, { art: b.dataset.befehl }); fvOffen.add(g.id); P = await holenP(); listeZeichnen(); }, T.pl.befehlOk); });
      const term = k.querySelector("[data-terminal]");
      if (term) term.onclick = () => terminalOeffnen(g);
      const log = k.querySelector("[data-protokoll]");
      if (log) log.onclick = (e) => aktion(e.target, async () => {
        const p = k.querySelector("[data-log]"); p.textContent = await dienst.get(`/api/player/${g.id}/protokoll`, {}, KOPF); p.hidden = false; p.scrollTop = p.scrollHeight; }, null);
      k.querySelector("[data-speichern]").onclick = (e) => aktion(e.target, async () => {
        const w = (n) => k.querySelector(`[name=${n}]`);
        await senden(`/api/player/${g.id}/aendern`, { name: w("name").value, tv: w("tv").value, modell: w("modell").value, drehung: Number(w("drehung").value),
          aufloesung: w("aufloesung").value, lautstaerke: Number(w("lautstaerke").value), cec_zeitplan: w("cec_zeitplan").checked,
          schreibschutz: w("schreibschutz").checked, systemupdate: w("systemupdate").value, hwdec: w("hwdec").value,
          anzeige_modus: w("modell").value === "pi3" ? "stream" : w("anzeige_modus").value });
        fvOffen.add(g.id); P = await holenP(); listeZeichnen();
      });
      k.querySelector("[name=modell]").onchange = (e) => k.querySelectorAll("[data-anzeige]").forEach((x) => { x.hidden = e.target.value === "pi3"; });
      k.querySelector("[data-wlan-senden]").onclick = (e) => aktion(e.target, async () => {
        await senden(`/api/player/${g.id}/wlan`, { wlan: wlanLesen() }); fvOffen.add(g.id); P = await holenP(); listeZeichnen(); }, T.pl.wlanGesendet);
      k.querySelector("[data-image-laden]").onclick = (e) => aktion(e.target, async () => {
        const fo = k.querySelector(`#plIForm${g.id}`);
        const fe = k.querySelector(`#plIFern${g.id}`);
        const d = await senden(`/api/player/${g.id}/image`, { wlan: imageLesen(), fernwartung: k.querySelector(`#plIFw${g.id}`).checked, fern: !!(fe && fe.checked), form: fo ? fo.value : "gz", server: P.server || P.server_auto || `http://${location.hostname}:${P.webhook_port}` });
        plHerunterladen(d.kennung, d.datei); }, T.pl.laedtHerunter);
      k.querySelector("[data-entfernen]").onclick = (e) => {
        if (!confirm(T.pl.entfernenFrage(g.name))) return;
        aktion(e.target, async () => { const r = await senden(`/api/player/${g.id}/entfernen`); P = await holenP(); listeZeichnen(); fernAntwort(r); }, g.fern ? null : undefined);
      };
    }
  };
  // alle 10 s auffrischen – nicht, solange jemand in einer Karte tippt oder ein Formular offen ist
  // seit 0.43: jede Sekunde „vor X s“ und die Fernverwaltung nachführen; abfragen alle 10 s, solange etwas unterwegs ist alle 3 s
  let holt = false;
  const beobachten = () => {
    clearInterval(timer);
    timer = setInterval(async () => {
      if (aktiv !== "player" || holt) return;
      fvTicken();
      const unterwegs = P.geraete.some((g) => (g.verlauf || []).some(fvOffenE));
      if (Date.now() - P._geholt < (laedt() ? 2000 : unterwegs ? 3000 : 10000)) return;
      const alt = laedt();
      holt = true;
      try { P = await holenP(); } finally { holt = false; }
      if (alt || laedt()) {
        $("#plBasis").innerHTML = basisText(false);
        $("#plBasisPc").innerHTML = basisText(true);
        if (alt && !laedt()) zeichnen();
      }
      const w = $("#plWartend");
      if (w) w.textContent = wartendText();
      if (!inhalt.querySelector("#plListe :focus, #plListe details[open]:not([data-fv]), #plListe pre:not([hidden]), #plListe .geaendert")) listeZeichnen();
      else fvTicken();
    }, 1000);
  };
  zeichnen();
  beobachten();
}

// ---------- Leistungstest (seit 0.18) ----------
async function leistungSeite(inhalt) {
  const info = await holen("/api/leistung");
  const host = info.eigene_ip || location.hostname;
  inhalt.innerHTML = `<div class="karte"><h2>${esc(T.lt.server)}</h2><p class="leise">${esc(T.lt.serverText)}</p>
      <div class="zeile"><button class="knopf haupt" id="ltStart">${esc(T.lt.start)}</button><span class="leise">${esc(T.lt.ziel)}</span></div>
      <div id="ltErg"></div>
      <div class="zeile"><button class="knopf" id="ltTon">${esc(T.lt.tonNeu)}</button><span class="leise">${esc(T.lt.tonNeuText)}</span></div></div>
    <div class="karte"><h2>${esc(T.lt.geraet)}</h2><p class="leise">${esc(T.lt.geraetText)}</p>
      ${E.fernseher.map((t) => `<div class="zeile"><b>${esc(t.name)}</b><code>http://${esc(host)}:${info.port}/test?tv=${esc(t.id)}</code></div>`).join("")}
      <h3>${esc(T.lt.letzteGeraete)}</h3><div id="ltGeraete"></div></div>`;
  const zeigen = (erg) => {
    if (!erg) return;
    const s = erg.system, z = (w, ok) => `<td class="${ok ? "gut" : "schlecht"}">${w ?? "–"}</td>`;
    $("#ltErg").innerHTML = `<p class="leise">${esc(erg.zeit)}</p><div class="tabelle-rahmen"><table class="tabelle">
      <tr><th></th><th>${esc(T.lt.seite)}</th><th>${esc(T.lt.kodierung)}</th><th>${esc(T.lt.tempo)}</th><th>${esc(T.lt.verloren)}</th><th>${esc(T.lt.cpuKette)}</th></tr>
      ${erg.fernseher.map((t) => `<tr><td><b>${esc(t.name)}</b><br><span class="leise">${t.aufloesung === 2160 ? "4K" : "Full HD"} · ${t.codec === "h265" ? "H.265" : "H.264"} · ${ENC_KURZ[t.encoder] || ""} · ${t.bitrate_mbit} Mbit/s</span></td>
        ${t.laeuft ? z(t.fps_seite, (t.fps_seite ?? 25) >= 22) + z(t.fps_kodierung, (t.fps_kodierung ?? 25) >= 24) + z(t.tempo != null ? t.tempo + "×" : null, (t.tempo ?? 1) >= 0.97)
          + z((t.verworfen ?? 0) + (t.doppelt ?? 0), (t.verworfen ?? 0) + (t.doppelt ?? 0) <= erg.dauer_s * 2) + `<td>${t.cpu_kerne ?? "–"}</td>`
          : `<td colspan="5" class="leise">${esc(T.lt.aus)}</td>`}</tr>`).join("")}</table></div>
      <p>${esc(T.lt.system)}: ${esc(T.lt.cpu)} <b class="${(s.cpu ?? 0) > 85 ? "schlecht" : (s.cpu ?? 0) > 70 ? "warn" : "gut"}">${s.cpu ?? "–"} %</b> (${s.kerne} ${esc(T.lt.kerne)}) ·
        ${esc(T.lt.ram)} <b class="${s.ram_frei_mb < 400 ? "schlecht" : "gut"}">${s.ram_frei_mb} MB</b> / ${s.ram_gesamt_mb} MB${s.gpu_last != null ? ` · ${esc(T.lt.gpu)} ${s.gpu_last} %` : ""}</p>
      <h3>${esc(T.lt.empfehlungen)}</h3><ul class="todo">${erg.empfehlungen.map((x) =>
        `<li class="${x.stufe === "gut" ? "gut" : x.stufe === "info" ? "info" : "warn"}">${esc((T.lt.empf[x.code] || (() => x.code))(x.p || {}))}</li>`).join("")}</ul>`;
  };
  const geraete = (l) => {
    $("#ltGeraete").innerHTML = l.length ? `<ul class="todo">${l.map((g) => {
      const tv = (E.fernseher.find((t) => t.id === g.tv) || {}).name || g.tv;
      const ok = (g.verloren || 0) <= (g.dekodiert || 0) * 0.02 && !g.stocken;
      return `<li class="${ok ? "gut" : "warn"}">${esc(g.zeit)} · <b>${esc(tv)}</b> · ${g.mbit ?? "–"} Mbit/s · ${g.verloren}/${g.dekodiert} · ${g.stocken}×<br>
        <span class="leise">${esc(g.geraet)}</span></li>`; }).join("")}</ul>` : `<p class="leise">${esc(T.lt.keine)}</p>`;
  };
  zeigen(info.letzte); geraete(info.geraete);
  $("#ltTon").onclick = (e) => aktion(e.target, () => senden("/api/aktion/ton-neu", {}), T.lt.tonNeuOk);
  $("#ltStart").onclick = (e) => aktion(e.target, async () => {
    e.target.textContent = T.lt.laeuftTest;
    try { zeigen((await senden("/api/leistung/test", {})).ergebnis); } finally { e.target.textContent = T.lt.start; }
  }, null);
  clearInterval(timer);
  timer = setInterval(() => holen("/api/leistung").then((d) => geraete(d.geraete)).catch(() => {}), 10000);
}

// „Zu erledigen“ (seit 0.17): wichtig (warn) zuerst, Tipps danach; jeder Eintrag führt zur passenden Seite
// „Zu erledigen“: Warnungen berechnet der Dienst (todo_warn, mit Kennung), Hinweise und Tipps die Verwaltung. Seit 0.35
// lässt sich jeder Eintrag außer dem Startpasswort ausblenden (todo_aus, gespeichert beim Dienst):
// Tipp dauerhaft, Update nur für diese Version, Warnung bis das Problem einmal weg war.
let TODO_ZEIGEN = false;
const TODO_WARN = {
  ha: () => [T.todo.ha, "ha"], bildrate: (w) => [T.todo.bildrate(w.name), "leistung"],
  allgemein: (w) => [T.todo.allgemein(w.grund, String(w.seit || "").slice(11)), "streams"], doppelt: (w) => [T.todo.doppelt(w.name), "leistung"],
  player: (w) => [T.todo.player(w.name), "player"], sicherung_fehler: () => [T.todo.sicherungFehler, "sicherung"],
  bn_fehler: () => [T.todo.bnFehler, "benachrichtigung"], wetter: () => [T.todo.wetter, "allgemein"],
  internet: (w) => [T.todo.internet(w.seit), "uebersicht"], bild: (w) => [T.todo.bild(w.name, w.befund), "leistung"],
};
async function todoZeichnen(s) {
  const l = [];
  const neu = (stufe, text, seite, key, art) => l.push({ stufe, text, seite, key, art });
  for (const w of s.todo_warn || []) {
    const f = TODO_WARN[w.key.split(":")[0]];
    if (f) { const [text, seite] = f(w); neu("warn", text, seite, w.key, "warn"); }
  }
  if (s.neue_version) neu("info", T.todo.update(s.neue_version), CONTAINER ? "uebersicht" : "updates", "update:" + s.neue_version, "update");
  if (s.kodierung && s.kodierung.art === "software") neu("info", T.todo.software, "uebersicht", "software", "tipp");
  if (E.sicherung.plan === "aus") neu("tipp", T.todo.sicherung, "sicherung", "sicherung", "tipp");
  const B = E.benachrichtigung;
  if (!B.telegram.aktiv && !B.email.aktiv && !B.ha.aktiv) neu("tipp", T.todo.benachrichtigung, "benachrichtigung", "benachrichtigung", "tipp");
  if (CONTAINER) {                          // Sicherheitslücke: nicht ausblendbar (kein key)
    try { if ((await (await fetch("/verwaltung/info", { credentials: "same-origin" })).json()).startpasswort) neu("warn", T.todo.passwort, "zugang"); } catch (_) { /* egal */ }
  }
  const ziel = $("#todo");
  if (!ziel) return;
  const aus = new Set(s.todo_aus || []);
  const rang = { warn: 0, info: 1, tipp: 2 };
  l.sort((a, b) => rang[a.stufe] - rang[b.stufe]);
  const sichtbar = l.filter((x) => !x.key || !aus.has(x.key)), versteckt = l.filter((x) => x.key && aus.has(x.key));
  const zeile = (x, ist_aus) => `<li class="${x.stufe}${ist_aus ? " aus" : ""}">${x.seite === "uebersicht" ? esc(x.text)
    : `<a href="#${x.seite}">${esc(x.text)}</a>`}${ist_aus ? ` <span class="leise">(${esc(T.todoAusgeblendet)})</span>
      <button class="todo-knopf todo-ein" data-todo-ein="${esc(x.key)}">${esc(T.todoEin)}</button>`
    : x.key ? `<button class="todo-knopf todo-x" data-todo-aus="${esc(x.key)}" title="${esc(T.todoAus[x.art])}" aria-label="${esc(T.todoAus[x.art])}">✕</button>` : ""}</li>`;
  ziel.innerHTML = (sichtbar.length ? sichtbar.map((x) => zeile(x, false)).join("") : `<li class="gut">${esc(T.todoOk)}</li>`)
    + (versteckt.length ? `<li class="todo-versteckt"><a href="#" data-todo-zeigen>${esc(TODO_ZEIGEN ? T.todoVerbergen : T.todoVersteckt(versteckt.length))}</a></li>`
      + (TODO_ZEIGEN ? versteckt.map((x) => zeile(x, true)).join("") : "") : "");
  const umschalten = async (pfad, key, knopf) => {
    knopf.disabled = true;
    try { s.todo_aus = (await senden(pfad, { key })).todo_aus; } catch (f) { knopf.disabled = false; melden(f.message, true); return; }
    todoZeichnen(s);
  };
  ziel.querySelectorAll("[data-todo-aus]").forEach((b) => { b.onclick = () => umschalten("/api/todo/aus", b.dataset.todoAus, b); });
  ziel.querySelectorAll("[data-todo-ein]").forEach((b) => { b.onclick = () => umschalten("/api/todo/ein", b.dataset.todoEin, b); });
  const z = ziel.querySelector("[data-todo-zeigen]");
  if (z) z.onclick = (ev) => { ev.preventDefault(); TODO_ZEIGEN = !TODO_ZEIGEN; todoZeichnen(s); };
}

async function uebersicht(inhalt) {
  inhalt.innerHTML = `
    <div id="alarmHinweis"></div>
    <div class="karte" id="todoKarte"><h2>${esc(T.todoTitel)}</h2><ul class="todo" id="todo"></ul></div>
    <div id="updateHinweis"></div>
    <div class="raster" id="tvs"></div>
    <div class="raster" id="kacheln"></div>
    <div class="raster">
      <div class="karte"><h2>${esc(T.vorschau)}</h2>
        ${E.fernseher.length > 1 ? `<div class="zeile"><select id="vTv">${E.fernseher.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select></div>` : ""}
        <img class="vorschau" id="vorschau" alt="">
        <p class="leise" id="vorschauText"></p>
        <div class="zeile"><button class="knopf" id="vNeu">${esc(T.vorschauNeu)}</button></div></div>
      <div class="karte"><h2>${esc(T.aufgaben)}</h2><div id="aufgaben"></div>
        <div class="zeile"><button class="knopf" id="sNeu">${esc(T.seiteNeu)}</button>
          <button class="knopf" id="kNeu">${esc(T.ketteNeu)}</button><button class="knopf" id="lNeu">${esc(T.listeNeu)}</button></div>
        <p class="leise">${esc(CONTAINER ? T.systemSeitenContainer : T.systemSeiten)}</p>
        <p class="leise"><a href="https://github.com/thefrozn/signagecast" target="_blank" rel="noopener">${esc(T.projektseite)}</a> ·
          <a href="https://github.com/thefrozn/signagecast/issues" target="_blank" rel="noopener">${esc(T.fehlerMelden)}</a></p></div>
    </div>`;
  $("#vNeu").onclick = () => vorschau();
  if ($("#vTv")) $("#vTv").onchange = () => vorschau();
  $("#sNeu").onclick = (e) => aktion(e.target, () => senden("/api/aktion/seite-neu-laden"), T.erledigt);
  $("#kNeu").onclick = (e) => aktion(e.target, () => senden("/api/aktion/kette-neu-starten"), T.erledigt);
  $("#lNeu").onclick = (e) => aktion(e.target, () => senden("/api/liste/neu"), T.erledigt);
  const zeichnen = async () => {
    const s = await holen("/api/status");
    $("#tvs").innerHTML = s.fernseher.map((t) => {
      const w = t.wache;
      return `<div class="karte"><div class="leise">${esc(t.name)} · /${esc(t.id)}</div>
        <div class="wert">${t.laeuft ? `<span class="gut">${esc(T.laeuft)}</span>` : esc(T.aus)}</div>
        <div class="leise">${t.aktuell ? esc(t.aktuell.name) : ""}${w ? ` · <b class="${/hd/.test(w.stufe) ? "gut" : "schlecht"}">${esc(stufeText(w.stufe))}</b> ${esc((w.codec || "").split(".")[0])}${w.kbps ? " · " + Math.round(w.kbps / 1000) + " Mbit/s" : ""}` : ""}</div>
        <div class="leise">${esc(T.tonAnzeige)}: ${esc(T.tonArt[t.ton])}${t.sender ? " · ♪ " + esc(t.sender) : ""}${t.video ? "" : " · " + esc(T.videoZeigen) + ": " + esc(T.nein)}</div>
        ${((s.schalten || {})[t.id] || {}).ha ? (() => { const h = s.schalten[t.id].ha;
          return `<div class="leise">${esc(T.geraetHa)}: <b class="${h.zustand === "an" ? "gut" : h.zustand === "aus" ? "" : "schlecht"}">${esc(T.haZustand[h.zustand] || h.zustand)}</b>${h.quelle ? " · " + esc(h.quelle) : ""}</div>`; })() : ""}
        ${t.bild === "schwarz" || t.bild === "steht" ? `<div class="schlecht">${esc(T.bildBefund[t.bild])}</div>` : ""}
        ${t.pult_layout ? `<div class="leise">${esc(T.pultLayout(t.pult_layout.name, uhrzeit(t.pult_layout.bis), t.pult_layout.von))}</div>` : ""}</div>`;
    }).join("");
    const k = [
      [T.zuschauer, String(s.stream.zuschauer), ""],
      [T.internet, s.netz && s.netz.offline ? `<span class="schlecht">${esc(T.offline)}</span>` : `<span class="gut">${esc(T.online)}</span>`,
        esc(s.netz && s.netz.offline ? T.offlineSeit(uhrzeit(s.netz.seit)) : T.onlineText)],
      [T.wetterKarte, s.wetter.jetzt ? `${s.wetter.jetzt.temperatur} °C` : (s.wetter.quelle === "ha" ? "HA" : "–"),
        esc(s.wetter.quelle === "met" ? `MET Norway · ${s.wetter.abruf || ""}${s.wetter.fehler ? " · " + meldungText(s.wetter.fehler_m, s.wetter.fehler) : ""}` : T.wetterQuelleArt.ha)],
      [T.zeitKarte, s.zeit_quelle && s.zeit_quelle.abweichung_s != null ? `${s.zeit_quelle.abweichung_s > 0 ? "+" : ""}${s.zeit_quelle.abweichung_s} s` : "–",
        esc((s.zeit_quelle || {}).korrektur === false && (s.zeit_quelle || {}).host_synchronisiert ? hostSync()
            : (s.zeit_quelle || {}).korrektur ? T.hostNichtSync : "") + "<br>" +
        esc(`${(s.zeit_quelle || {}).server || ""} · ${(s.zeit_quelle || {}).zeitzone || ""}`) +
        (Math.abs((s.zeit_quelle || {}).abweichung_s || 0) > 2 ? `<br><span class="warn">${esc(T.zeitWarnung)}</span>` : "")],
      [T.ha, s.ha.ok ? `<span class="gut">${esc(T.verbunden)}</span>` : `<span class="schlecht">${esc(T.getrennt)}</span>`,
        esc(s.ha.ok ? s.ha.url : T.haFehler[s.ha.code] ? T.haFehler[s.ha.code] + (s.ha.detail ? ": " + s.ha.detail : "") : (s.ha.fehler || s.ha.url))],
      [T.rotation, String(s.anzahl_in_rotation), `${esc(T.liste)} ${esc(T.zuletzt)} ${esc(s.liste.zeit || "–")}` +
        (s.liste.pause_bis > Date.now() / 1000 ? ` · <span class="warn">${esc(T.pause)} ${uhrzeit(s.liste.pause_bis)}</span>` : "")],
      [T.cpu, s.cpu_prozent != null ? s.cpu_prozent + " %" : "–", `${esc(T.last)} ${s.last.map((x) => x.toFixed(2)).join(" / ")} · ${s.kerne} ${esc(T.kerne)}`],
      [T.ram, `${s.ram_mb.frei} MB`, `${esc(T.von)} ${s.ram_mb.gesamt} MB · ${esc(T.platte)} ${s.platte_gb.frei} / ${s.platte_gb.gesamt} GB`],
      [T.laufzeit, dauer(s.laufzeit_s), `Version ${esc(s.version)}`],
    ];
    if (s.kodierung) k.splice(3, 0, [T.kodierungKarte, esc(T.kodierungArt[s.kodierung.art] || s.kodierung.art),
      esc(`${s.kodierung.codec}, ${s.kodierung.max_hoehe === 2160 ? "4K" : "Full HD"}${s.kodierung.treiber ? " · " + s.kodierung.treiber : ""}`) +
      (s.kodierung.art === "software" ? `<br><span class="warn">${esc(T.kodierungSoftware)}</span>` : "")]);
    const hinweis = $("#updateHinweis");
    if (hinweis) hinweis.innerHTML = s.neue_version ? `<div class="karte warn"><b>${esc(T.neueVersion(s.neue_version))}</b>
      ${CONTAINER ? `<p class="leise">${esc(T.updateTextContainer)}</p><pre>docker pull ${IMAGE}\ndocker compose up -d   # oder: docker rm -f signagecast &amp;&amp; docker run …</pre>`
        : `<pre>curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh</pre><p class="leise">${esc(T.updateText)}</p>`}
      <p class="leise"><a href="${esc(s.projekt)}/releases" target="_blank" rel="noopener">${esc(T.aenderungen)}</a></p></div>` : "";
    todoZeichnen(s);
    holen("/api/alarm").then((a) => {
      const z = $("#alarmHinweis");
      if (!z) return;
      z.innerHTML = a.jetzt ? `<div class="karte warn"><b>⚠ ${esc(T.al.laeuft(a.jetzt.zeit, a.jetzt.von))}</b><p>${esc(a.jetzt.text)}</p>
        <button class="knopf gefahr" id="alarmBeenden">${esc(T.al.aus)}</button></div>` : "";
      const k2 = $("#alarmBeenden");
      if (k2) k2.onclick = (ev) => aktion(ev.target, async () => { await senden("/api/alarm", { aus: true }); z.innerHTML = ""; }, T.al.beendet);
    }).catch(() => {});
    $("#kacheln").innerHTML = k.map(([t, w2, u]) => `<div class="karte"><div class="leise">${esc(t)}</div><div class="wert">${w2}</div><div class="leise">${u}</div></div>`).join("");
    $("#aufgaben").innerHTML = s.aufgaben.map((a) => `<div class="zeile"><b>${esc(T.aufgabe[a.name] || a.name)}</b>
      <span class="leise">${esc(a.alle_s ? T.alleSek(a.alle_s) + (a.nur_stream ? ", " + T.nurStream : "") : a.wann || T.deaktiviert)}${a.zuletzt ? " · " + esc(T.zuletzt) + " " + esc(a.zuletzt.zeit || "") : ""}</span></div>`).join("");
  };
  await zeichnen();
  vorschau();
  timer = setInterval(() => zeichnen().catch(() => {}), 5000);
}
async function vorschau() {
  const img = $("#vorschau"), txt = $("#vorschauText");
  if (!img) return;
  try {
    const tv = $("#vTv") ? $("#vTv").value : E.fernseher[0].id;
    const daten = await dienstBinaer.get("/api/vorschau.jpg", { tv }, { "X-SignageCast": "1" });
    const url = URL.createObjectURL(new Blob([daten], { type: "image/jpeg" }));
    img.onload = () => URL.revokeObjectURL(url);
    img.src = url; img.style.display = ""; txt.textContent = new Date().toLocaleTimeString(ORT());
  } catch (_) { img.style.display = "none"; txt.textContent = T.keineVorschau; }
}

// ---------- Streams ----------
// Filter der Streamliste (seit 0.31: Zustand und Herkunft); merkt sich der Browser
let filter = { text: "", kat: "", herkunft: "", zustand: "" };
try { filter = Object.assign(filter, JSON.parse(localStorage.getItem("signagecast-streamfilter") || "{}")); } catch (_) { /* egal */ }
function filterMerken() { try { localStorage.setItem("signagecast-streamfilter", JSON.stringify(filter)); } catch (_) { /* egal */ } }
const ZUSTAENDE = ["rotation", "bereit", "nacht", "nicht_live", "qualitaet", "pause", "gesperrt", "strikes", "ohne_ort", "ungeprueft", "inaktiv", "kategorie_aus"];
function passtZustand(s, z) { return !z || (z === "rotation" ? s.in_rotation : z === "strikes" ? s.strikes > 0 : s.zustand === z); }
function dauerText(s) { const m = Math.max(0, Math.round(s / 60)); return m >= 60 ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")} h` : `${m} min`; }
async function streamsSeite(inhalt) {
  inhalt.innerHTML = `
    <div class="karte"><h2>${esc(T.hinzufuegen)}</h2>
      <div class="zeile"><input type="url" id="nLink" placeholder="https://www.youtube.com/watch?v=…" aria-label="${esc(T.link)}"></div>
      <div class="zeile"><input type="text" id="nName" placeholder="${esc(T.name)}">
        <select id="nKat">${katOptionen("neu")}</select></div>
      <div class="zeile"><input type="number" step="0.01" id="nBreite" placeholder="${esc(T.breite)}">
        <input type="number" step="0.01" id="nLaenge" placeholder="${esc(T.laenge)}"><span class="leise">${esc(T.ortAuto)}</span></div>
      <div class="zeile"><button class="knopf haupt" id="nOk">${esc(T.hinzufuegen)}</button></div></div>
    <div class="karte">
      <div class="zeile"><input type="text" id="fText" placeholder="${esc(T.filter)}" value="${esc(filter.text)}">
        <select id="fKat"><option value="">${esc(T.alle)}</option>${katOptionen(filter.kat)}</select>
        <select id="fHerk">${[["", T.herkunftAlle], ["fest", T.nurFeste], ["entdeckt", T.nurGefundene]].map(([w, n]) =>
          `<option value="${w}" ${filter.herkunft === w ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></div>
      <div class="marken" id="fZust" role="group" aria-label="${esc(T.zustandAlle)}"></div>
      ${E.fernseher.length > 1 ? `<div class="zeile"><label>${esc(T.zeigenAuf)}</label><select id="zeigenTv"><option value="">${esc(T.alleTv)}</option>
        ${E.fernseher.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select></div>` : ""}
      <div class="leise" id="zahl"></div></div>
    <div id="liste"></div>
    <div class="karte"><h3>${esc(T.abgelehnt)}</h3><div id="abgelehnt"></div></div>`;
  $("#nKat").value = "neu";
  $("#nOk").onclick = (e) => aktion(e.target, async () => {
    const b = $("#nBreite").value, l = $("#nLaenge").value;
    await senden("/api/streams", { link: $("#nLink").value, name: $("#nName").value, kategorie: $("#nKat").value,
      breite: b === "" ? null : Number(b), laenge: l === "" ? null : Number(l) });
    $("#nLink").value = ""; $("#nName").value = "";
    await streamsLaden();
  });
  for (const [id, feld, art] of [["#fText", "text", "input"], ["#fKat", "kat", "change"], ["#fHerk", "herkunft", "change"]])
    $(id).addEventListener(art, (e) => { filter[feld] = e.target.value; filterMerken(); listeZeichnen(); });
  await streamsLaden();
}
let STREAMS = null;
async function streamsLaden() { STREAMS = await holen("/api/streams"); listeZeichnen(); }
function listeZeichnen() {
  const liste = $("#liste"); if (!liste || !STREAMS) return;
  const t = filter.text.toLowerCase();
  const vorauswahl = STREAMS.streams.filter((s) => (!t || (s.name + " " + (s.titel || "") + " " + s.id).toLowerCase().includes(t))
    && (!filter.kat || s.kategorie === filter.kat) && (!filter.herkunft || s.herkunft === filter.herkunft));
  const gezeigt = vorauswahl.filter((s) => passtZustand(s, filter.zustand));
  // Zähler je Zustand (über Text, Kategorie und Herkunft gefiltert) – anklicken filtert, nochmal klicken hebt auf
  const fz = $("#fZust"); fz.innerHTML = "";
  for (const z of [""].concat(ZUSTAENDE)) {
    const n = z ? vorauswahl.filter((s) => passtZustand(s, z)).length : vorauswahl.length;
    if (z && !n && filter.zustand !== z) continue;
    const b = el(`<button type="button" class="knopf klein ${filter.zustand === z ? "haupt" : ""}" aria-pressed="${filter.zustand === z}">${esc(z ? T.zustand[z] : T.zustandAlle)} ${n}</button>`);
    b.onclick = () => { filter.zustand = filter.zustand === z ? "" : z; filterMerken(); listeZeichnen(); };
    fz.appendChild(b);
  }
  const vb = STREAMS.vorab;
  $("#zahl").textContent = T.anzahl(STREAMS.streams.length, STREAMS.streams.filter((s) => s.in_rotation).length)
    + (vb && vb.zeit && vb.geprueft != null ? " · " + T.vorab(vb.zeit, vb.geprueft) : "");
  liste.innerHTML = "";
  for (const s of gezeigt) liste.appendChild(streamKarte(s));
  $("#abgelehnt").innerHTML = STREAMS.abgelehnt.length ? "" : "–";
  for (const a of STREAMS.abgelehnt) {
    const z = el(`<div class="zeile"><code>${esc(a)}</code><button class="knopf">${esc(T.freigeben)}</button></div>`);
    z.querySelector("button").onclick = (e) => aktion(e.target, async () => { await senden(`/api/abgelehnt/${encodeURIComponent(a)}/freigeben`); await streamsLaden(); });
    $("#abgelehnt").appendChild(z);
  }
}
function zustandMarke(s) {
  const z = s.zustand; if (!z) return "";
  const stil = { bereit: "gut", ohne_ort: "warn", ungeprueft: "warn", qualitaet: "schlecht", pause: "warn", gesperrt: "schlecht", nicht_live: "" }[z] ?? "";
  let text = T.zustand[z] || z;
  if (z === "nacht" && s.nachlauf) text = T.laeuftAus;
  else if (z === "nacht" && s.hell_ab) text += " · " + T.hellIn(dauerText(s.hell_ab - Date.now() / 1000));
  if (z === "pause" && s.pause_bis) text += " " + T.pauseBis(new Date(s.pause_bis * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }));
  return `<span class="marke ${stil}">${esc(text)}</span>`;
}
function streamKarte(s) {
  const q = s.qualitaet || {};
  const anteil = q.anteil_720p_plus != null ? Math.round(q.anteil_720p_plus * 100) : null;
  const marken = [
    `<span class="marke">${esc(katName(s.kategorie))}</span>`,
    `<span class="marke">${esc(s.herkunft === "entdeckt" ? T.gefunden : T.fest)}</span>`,
    zustandMarke(s),
    s.in_rotation ? `<span class="marke gut">${esc(T.inRotation)}</span>` : "",
    s.angeboten_hoehe ? `<span class="marke ${s.zustand === "qualitaet" ? "schlecht" : ""}">${esc(T.angebot(s.angeboten_hoehe + "p"))}</span>` : "",
    anteil != null ? `<span class="marke ${anteil >= 90 ? "gut" : anteil >= 50 ? "warn" : "schlecht"}">≥720p ${anteil} % · ${q.proben} ${esc(T.proben)}${q.codecs && q.codecs.length ? " · " + esc(q.codecs.map((c) => c.split(".")[0]).join("/")) : ""}</span>` : "",
    s.strikes ? `<span class="marke schlecht" title="${esc((s.strike_gruende || []).join("\n"))}">${esc(T.strikes)}: ${s.strikes}</span>` : "",
  ].join("");
  const k = el(`<div class="karte stream">
    <div><div class="titel">${esc(s.name)}</div><div class="leise">${esc(s.titel && s.titel !== s.name ? s.titel : "")}</div>
      <div class="leise"><a href="https://www.youtube.com/watch?v=${encodeURIComponent(s.video_id || s.id)}" target="_blank" rel="noopener">${esc(s.id)}</a>
        ${s.breite != null ? ` · ${Number(s.breite).toFixed(2)} / ${Number(s.laenge).toFixed(2)}` : ""}</div>
      <div class="marken">${marken}</div></div>
    <div class="schalterspalte"><label>${esc(T.aktiv)} ${schalter("aktiv", s.aktiv !== false)}</label>
      <label>${esc(T.geschuetzt)} ${schalter("geschuetzt", s.geschuetzt)}</label></div>
    <div class="aktionen">
      <button class="knopf" data-a="zeigen">${esc(T.zeigen)}</button>
      ${s.herkunft === "entdeckt" ? `<button class="knopf" data-a="uebernehmen">${esc(T.uebernehmen)}</button>` : ""}
      <button class="knopf" data-a="bearbeiten">${esc(T.bearbeiten)}</button>
      ${s.strikes ? `<button class="knopf" data-a="strikes">${esc(T.strikesWeg)}</button>` : ""}
      <button class="knopf gefahr" data-a="entfernen">${esc(T.entfernen)}</button>
      <button class="knopf gefahr" data-a="ablehnen">${esc(T.ablehnen)}</button></div></div>`);
  const pfad = `/api/streams/${encodeURIComponent(s.id)}`;
  k.querySelectorAll(".schalter input").forEach((i) => { i.onchange = () => aktion(null, () => senden(pfad, { [i.name]: i.checked })); });
  k.querySelectorAll("[data-a]").forEach((b) => {
    b.onclick = () => {
      const a = b.dataset.a;
      if (a === "zeigen") return aktion(b, () => senden(pfad + "/zeigen", { video_id: s.video_id, tv: ($("#zeigenTv") || {}).value || null }), T.zeigenOk);
      if (a === "uebernehmen") return aktion(b, async () => { await senden(pfad, { herkunft: "fest" }); await streamsLaden(); });
      if (a === "strikes") return aktion(b, async () => { await senden(pfad + "/strikes-zuruecksetzen", { video_id: s.video_id }); await streamsLaden(); });
      if (a === "entfernen" && confirm(T.wirklichEntfernen)) return aktion(b, async () => { await senden(pfad + "/entfernen"); await streamsLaden(); });
      if (a === "ablehnen" && confirm(T.wirklichAblehnen)) return aktion(b, async () => { await senden(pfad + "/entfernen", { ablehnen: true }); await streamsLaden(); });
      if (a === "bearbeiten") {
        if (k.querySelector(".bearbeiten")) return k.querySelector(".bearbeiten").remove();
        const f = el(`<div class="bearbeiten">
          <div class="zeile"><input type="text" name="name" value="${esc(s.name)}" aria-label="${esc(T.name)}">
            <select name="kategorie">${katOptionen(s.kategorie)}</select></div>
          <div class="zeile"><input type="number" step="0.01" name="breite" value="${s.breite ?? ""}" placeholder="${esc(T.breite)}">
            <input type="number" step="0.01" name="laenge" value="${s.laenge ?? ""}" placeholder="${esc(T.laenge)}">
            <button class="knopf haupt">${esc(T.speichern)}</button></div></div>`);
        f.querySelector("button").onclick = (e) => aktion(e.target, async () => {
          const d = { name: f.querySelector("[name=name]").value, kategorie: f.querySelector("[name=kategorie]").value };
          if (f.querySelector("[name=breite]").value !== "") { d.breite = Number(f.querySelector("[name=breite]").value); d.laenge = Number(f.querySelector("[name=laenge]").value); }
          await senden(pfad, d); await streamsLaden();
        });
        k.appendChild(f);
      }
    };
  });
  return k;
}

// ---------- Kategorien (seit 0.37) ----------
// Jede Kategorie: Name, Gruppe, eigene Suchbegriffe, Titelwörter, Tag/Nacht. Dazu, wo sie eingeschaltet ist (für alle /
// je Fernseher) und wie viele Streams drin sind. Eingebaute lassen sich zurücksetzen, eigene löschen (Streams wandern um).
async function kategorienSeite(inhalt) {
  const st = await holen("/api/streams");
  const anzahl = {};
  for (const x of st.streams) anzahl[x.kategorie] = (anzahl[x.kategorie] || 0) + 1;
  let ks = JSON.parse(JSON.stringify(E.kategorien));
  const offen = new Set();
  const zeilenText = (l) => (l || []).join("\n");
  const zeilen = (t) => t.value.split("\n").map((x) => x.trim()).filter(Boolean);
  const zeichnen = () => {
    inhalt.innerHTML = `<div class="karte"><h2>${esc(T.reiter.kategorien)}</h2><p class="leise">${esc(T.katText)}</p>
        <div class="zeile"><button class="knopf" id="katNeu" ${ks.length >= KAT_GRENZEN[0] ? "disabled" : ""}>${esc(T.katNeu)}</button></div></div>
      <div id="katListe"></div>`;
    const liste = $("#katListe");
    for (const g of ["tiere", "themen"]) {
      const inGruppe = ks.filter((k) => k.gruppe === g);
      if (!inGruppe.length) continue;
      liste.appendChild(el(`<h3>${esc(T.katGruppe[g])}</h3>`));
      for (const k of inGruppe) liste.appendChild(karte(k));
    }
    // Knopf in der Liste: Änderungen markieren ihre Karte als „nicht gespeichert“ (aenderungMerken)
    liste.appendChild(el(`<div class="zeile"><button class="knopf haupt" id="katOk">${esc(T.speichern)}</button></div>`));
    $("#katNeu").onclick = () => {
      lesen();
      let id; do { id = "k" + Math.random().toString(36).slice(2, 7).replace(/[^a-z0-9]/g, "0"); } while (ks.some((x) => x.id === id));
      ks.push({ id, eingebaut: false, name: "", gruppe: "themen", begriffe: [], woerter: [], ohne_tag: false, ohne_tag_woerter: [], neu: true });
      offen.add(id); zeichnen();
      const f = liste.querySelector(`[data-id="${id}"] [name=name]`); if (f) { f.focus(); f.closest(".karte").scrollIntoView({ block: "center" }); }
    };
    $("#katOk").onclick = (e) => { lesen(); speichern(e.target); };
  };
  const karte = (k) => {
    const aus = E.video.kategorien_aus.includes(k.id);
    const tvAus = E.fernseher.filter((t) => t.kategorien_aus.includes(k.id));
    const n = anzahl[k.id] || 0;
    const std = KAT_STANDARD.find((x) => x.id === k.id);
    const istNeu = k.id === "neu";
    const kurz = [n === 1 ? T.katEinStream : T.katStreams(n),
      aus ? T.katAusAlle : tvAus.length ? T.katAusBei(tvAus.map((t) => t.name).join(", ")) : "",
      k.begriffe.length ? T.katMitSuche(k.begriffe.length) : ""].filter(Boolean).join(" · ");
    const d = el(`<details class="karte" data-id="${esc(k.id)}" ${offen.has(k.id) ? "open" : ""}>
      <summary><b>${esc(k.name || T.kat[k.id] || k.id)}</b>${k.eingebaut ? (k.standard === false ? ` <span class="marke">${esc(T.katGeaendert)}</span>` : "")
        : ` <span class="marke">${esc(T.katEigene)}</span>`}
        <span class="leise"> – ${esc(kurz)}</span></summary>
      <div class="zeile"><label>${esc(T.katNameFeld)}</label><input type="text" name="name" maxlength="40" value="${esc(k.name)}"
        placeholder="${esc(k.eingebaut ? T.kat[k.id] || k.id : T.katNamePflicht)}"></div>
      ${istNeu ? `<p class="leise">${esc(T.katNeuText)}</p>` : `
      <div class="zeile"><label>${esc(T.katGruppeWahl)}</label><select name="gruppe">${["tiere", "themen"].map((g) =>
        `<option value="${g}" ${g === k.gruppe ? "selected" : ""}>${esc(T.katGruppe[g])}</option>`).join("")}</select></div>`}
      <h4>${esc(T.katWo)}</h4>
      <div class="zeile"><label>${esc(T.katAlle)}</label>${schalter("alle", !aus)}</div>
      ${E.fernseher.length > 1 ? E.fernseher.map((t, i) => `<div class="zeile"><label>${esc(t.name)}</label>${schalter("tv" + i, !t.kategorien_aus.includes(k.id))}</div>`).join("") : ""}
      ${istNeu ? "" : `
      <h4>${esc(T.katBegriffe(KAT_GRENZEN[1]))}</h4><p class="leise">${esc(k.gruppe === "tiere" ? T.katBegriffeTiere : T.katBegriffeThemen)}</p>
      <textarea name="begriffe" rows="3" spellcheck="false">${esc(zeilenText(k.begriffe))}</textarea>
      <h4>${esc(T.katWoerter)}</h4><p class="leise">${esc(k.gruppe === "tiere" ? T.katWoerterTiere : T.katWoerterThemen)}</p>
      <textarea name="woerter" rows="3" spellcheck="false">${esc(zeilenText(k.woerter))}</textarea>
      <div class="zeile"><label>${esc(T.katOhneTag)}</label>${schalter("ohne_tag", k.ohne_tag)}</div>
      <details class="erweitert"><summary>${esc(T.katOhneTagWoerter)}</summary>
        <textarea name="ohne_tag_woerter" rows="2" spellcheck="false">${esc(zeilenText(k.ohne_tag_woerter))}</textarea></details>`}
      <div class="zeile">
        ${n ? `<button class="knopf" data-a="streams">${esc(T.katStreamsZeigen)}</button>` : ""}
        ${std && !istNeu ? `<button class="knopf" data-a="standard">${esc(T.katStandard)}</button>` : ""}
        ${!k.eingebaut ? `<button class="knopf gefahr" data-a="loeschen">${esc(T.entfernen)}</button>` : ""}</div>
      <div class="zeile" data-loeschen hidden><label>${esc(T.katVerschieben(n))}</label>
        <select name="ziel">${ks.filter((x) => x.id !== k.id && !x.neu).map((x) => `<option value="${esc(x.id)}" ${x.id === "neu" ? "selected" : ""}>${esc(x.name || T.kat[x.id] || x.id)}</option>`).join("")}</select>
        <button class="knopf gefahr" data-a="wirklich">${esc(T.katWirklich)}</button></div></details>`);
    d.addEventListener("toggle", () => { if (d.open) offen.add(k.id); else offen.delete(k.id); });
    d.querySelectorAll("[data-a]").forEach((b) => {
      b.onclick = () => {
        const a = b.dataset.a;
        if (a === "streams") { filter = Object.assign(filter, { kat: k.id, text: "", zustand: "" }); filterMerken(); return zeigeSeite("streams"); }
        if (a === "standard") {
          d.querySelector("[name=name]").value = "";
          d.querySelector("[name=gruppe]").value = std.gruppe;
          d.querySelector("[name=begriffe]").value = zeilenText(std.begriffe);
          d.querySelector("[name=woerter]").value = zeilenText(std.woerter);
          d.querySelector("[name=ohne_tag]").checked = std.ohne_tag;
          d.querySelector("[name=ohne_tag_woerter]").value = zeilenText(std.ohne_tag_woerter);
          d.querySelector("[name=name]").dispatchEvent(new Event("input", { bubbles: true }));
          return;
        }
        if (a === "loeschen") {
          if (k.neu) { lesen(); ks = ks.filter((x) => x.id !== k.id); return zeichnen(); }   // noch nicht gespeichert
          d.querySelector("[data-loeschen]").hidden = false; return;
        }
        if (a === "wirklich") return aktion(b, async () => {
          const r = await senden("/api/kategorien/loeschen", { id: k.id, ziel: d.querySelector("[name=ziel]").value });
          E = r.einstellungen;
          await kategorienSeite(inhalt);
        });
      };
    });
    return d;
  };
  // Formular -> ks (Text bleibt beim Neuzeichnen erhalten)
  const lesen = () => {
    for (const d of inhalt.querySelectorAll("#katListe > details[data-id]")) {
      const k = ks.find((x) => x.id === d.dataset.id); if (!k) continue;
      const w = (n) => d.querySelector(`[name=${n}]`);
      k.name = w("name").value.trim();
      if (w("gruppe")) {
        k.gruppe = w("gruppe").value; k.begriffe = zeilen(w("begriffe")); k.woerter = zeilen(w("woerter"));
        k.ohne_tag = w("ohne_tag").checked; k.ohne_tag_woerter = zeilen(w("ohne_tag_woerter"));
      }
      k._alle = w("alle").checked;
      k._tv = E.fernseher.map((_, i) => (w("tv" + i) ? w("tv" + i).checked : k._alle));
    }
  };
  const speichern = (knopf) => {
    const an = (k, i) => (i == null ? k._alle !== false : (k._tv ? k._tv[i] : true));
    const teil = {
      kategorien: ks.map(({ id, name, gruppe, begriffe, woerter, ohne_tag, ohne_tag_woerter }) => ({ id, name, gruppe, begriffe, woerter, ohne_tag, ohne_tag_woerter })),
      video: { kategorien_aus: ks.filter((k) => !an(k)).map((k) => k.id) },
      fernseher: E.fernseher.map((t, i) => ({ ...t, kategorien_aus: ks.filter((k) => !an(k, i)).map((k) => k.id) })),
    };
    return aktion(knopf, async () => {
      E = (await senden("/api/einstellungen", teil)).einstellungen;
      await kategorienSeite(inhalt);
    });
  };
  zeichnen();
}

// ---------- Anzeige ----------
async function anzeige(inhalt) {
  const ents = await entitaeten();
  inhalt.innerHTML = `<datalist id="ents">${ents.filter((x) => x.id.startsWith("weather.")).map((x) => `<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("")}</datalist>
    <div class="karte"><h2>${esc(T.reiter.anzeige)}</h2>
      <div class="zeile"><label>${esc(T.sprache)}</label><select id="sprache"><option value="de">Deutsch</option><option value="en">English</option></select></div>
      <div class="zeile"><label>${esc(T.wetterQuelle)}</label><select id="wetterQ" class="breit">${Object.keys(T.wetterQuelleArt).map((k) =>
        `<option value="${k}" ${k === E.anzeige.wetter_quelle ? "selected" : ""}>${esc(T.wetterQuelleArt[k])}</option>`).join("")}</select></div>
      <p class="leise" id="metText">${esc(T.metText)}</p>
      <div class="zeile" id="haZeile"><label>${esc(T.wetter)}</label><input type="text" id="wetter" list="ents" value="${esc(E.anzeige.wetter)}"></div>
      <p class="leise" id="haText">${esc(T.wetterText)}</p>
      <div class="zeile"><button class="knopf haupt" id="okAnz">${esc(T.speichern)}</button></div></div>`;
  $("#sprache").value = E.sprache || "de";
  const sicht = () => { const ha = $("#wetterQ").value === "ha"; $("#haZeile").style.display = ha ? "" : "none"; $("#haText").style.display = ha ? "" : "none"; $("#metText").style.display = ha ? "none" : ""; };
  $("#wetterQ").onchange = sicht; sicht();
  $("#okAnz").onclick = async (e) => {
    await speichernE({ sprache: $("#sprache").value, anzeige: { wetter_quelle: $("#wetterQ").value, wetter: $("#wetter").value } }, e.target);
    T = TEXTE[E.sprache] || TEXTE.de; reiterZeichnen(); hinweiseZeichnen();
  };
}

// ---------- Video & Regeln ----------
async function video(inhalt) {
  const v = E.video;
  const zahlFeld = (id, w, min, max, step) => `<input type="number" id="${id}" value="${w}" min="${min}" max="${max}" step="${step || 1}">`;
  inhalt.innerHTML = `<div class="karte">
      <div class="zeile"><label>${esc(T.takt)}</label>${zahlFeld("takt", v.takt_min, 1, 30)}</div>
      <div class="zeile"><label>${esc(T.nurTag)}</label>${schalter("nurTag", v.nur_tag)}</div>
      <div class="zeile"><label>${esc(T.sonne)}</label>${zahlFeld("sonne", v.min_sonnenhoehe, -18, 30, 0.5)}</div>
      <details class="erweitert"><summary>${esc(T.erweitert)}</summary>
      <div class="zeile"><label>${esc(T.mindeststufe)}</label><select id="stufe">${STUFEN.map((x) => `<option value="${x}" ${x === v.mindeststufe ? "selected" : ""}>${esc(stufeText(x))}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(T.schlecht)}</label>${zahlFeld("schlecht", v.schlecht_s, 5, 170)}</div>
      <div class="zeile"><label>${esc(T.grenze)}</label>${zahlFeld("grenze", v.strike_grenze, 1, 20)}</div>
      <div class="zeile"><label>${esc(T.sperre)}</label>${zahlFeld("sperre", v.sperre_h, 0, 72, 0.5)}</div></details>
      <p class="leise">${esc(T.kategorienWoanders)} <a href="#kategorien">${esc(T.reiter.kategorien)}</a></p></div>
    <div class="zeile"><button class="knopf haupt" id="ok">${esc(T.speichern)}</button></div>`;
  const n = (id) => Number($("#" + id).value);
  $("#ok").onclick = (e) => speichernE({
    video: { takt_min: n("takt"), nur_tag: $("[name=nurTag]").checked, min_sonnenhoehe: n("sonne"),
             mindeststufe: $("#stufe").value, schlecht_s: n("schlecht"), strike_grenze: n("grenze"), sperre_h: n("sperre") },
  }, e.target);
}

// ---------- Stream-Suche ----------
async function sucheSeite(inhalt) {
  const s = E.suche;
  const st = await holen("/api/status");
  const letzte = st.liste.suche;
  inhalt.innerHTML = `<div class="karte">
      <div class="zeile"><label>${esc(T.sucheAktiv)}</label>${schalter("aktiv", s.aktiv)}</div>
      <div class="zeile"><label>${esc(T.uhrzeit)}</label><input type="time" id="uhrzeit" value="${esc(s.uhrzeit)}"></div>
      <div class="zeile"><label>${esc(T.max)}</label><input type="number" id="max" value="${s.max}" min="0" max="200"></div>
      <div class="zeile"><label>${esc(T.behalten)}</label><input type="number" id="behalten" value="${s.behalten_tage}" min="1" max="365"></div>
      <div class="zeile"><button class="knopf" id="jetzt">${esc(T.jetztSuchen)}</button>
        <span class="leise" id="ergebnis">${letzte ? esc(T.zuletzt + " " + (letzte.zeit || "")) + (letzte.neu ? " · " + esc(T.sucheErgebnis(letzte.neu.length, letzte.gefunden ?? "?")) : "") : ""}</span></div></div>
    <div class="karte"><h3>${esc(T.begriffe)}</h3><textarea id="begriffe">${esc(s.begriffe.join("\n"))}</textarea>
      <h3>${esc(T.tierwoerter)}</h3><textarea id="tier">${esc(s.tierwoerter.join("\n"))}</textarea>
      <h3>${esc(T.ausschluss)}</h3><textarea id="nein">${esc(s.ausschluss.join("\n"))}</textarea>
      <h3>${esc(T.orte)}</h3><textarea id="orte">${esc(s.orte.map((o) => `${o.muster} ; ${o.breite} ; ${o.laenge}`).join("\n"))}</textarea></div>
    <div class="zeile"><button class="knopf haupt" id="ok">${esc(T.speichern)}</button></div>`;
  const zeilen = (id) => $("#" + id).value.split("\n").map((x) => x.trim()).filter(Boolean);
  $("#ok").onclick = (e) => speichernE({ suche: {
    aktiv: $("[name=aktiv]").checked, uhrzeit: $("#uhrzeit").value, max: Number($("#max").value), behalten_tage: Number($("#behalten").value),
    begriffe: zeilen("begriffe"), tierwoerter: zeilen("tier"), ausschluss: zeilen("nein"),
    orte: zeilen("orte").map((z) => { const t = z.split(";").map((x) => x.trim()); return { muster: t[0], breite: Number(t[1]), laenge: Number(t[2]) }; }),
  } }, e.target);
  $("#jetzt").onclick = (e) => aktion(e.target, async () => {
    $("#ergebnis").textContent = T.sucheLaeuft;
    const r = await senden("/api/suche/starten");
    $("#ergebnis").textContent = r.suche.pause ? T.pause : T.sucheErgebnis((r.suche.neu || []).length, r.suche.gefunden ?? "?");
  }, null);
}

// ---------- Verbindung ----------
// Meldungen per Webhook (seit 0.31.1 bei den Durchsagen: nimmt Meldungen für die Fernseher an, schickt nichts hinaus)
async function webhookKarte(inhalt) {
  const info = await holen("/api/ha/einrichtung");
  inhalt.innerHTML = `<div class="karte"><h2>${esc(T.whTitel)}</h2><p class="leise">${esc(T.whText)}</p>
      <div class="zeile"><label><input type="checkbox" id="whAktiv" ${E.webhook.aktiv ? "checked" : ""}> ${esc(T.whAktiv)}</label>
        <span class="leise" id="whStand">${esc(E.webhook.token ? T.whVorhanden : T.whKeiner)}</span></div>
      <div class="zeile"><button class="knopf" id="whNeu">${esc(T.whNeu)}</button></div><div id="whErg"></div></div>`;
  $("#whAktiv").onchange = (e) => speichernE({ webhook: { aktiv: e.target.checked } }, e.target);
  $("#whNeu").onclick = (e) => {
    if (E.webhook.token && !confirm(T.whNeuFrage)) return;
    aktion(e.target, async () => {
      const r = await senden("/api/webhook/neu", {});
      E = r.einstellungen; $("#whAktiv").checked = true; $("#whStand").textContent = T.whVorhanden;
      const host = info.eigene_ip || location.hostname;
      const beispiel = `curl -X POST http://${host}:${r.port}/meldung \\\n  -H "Authorization: Bearer ${r.token}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"text": "Hallo", "dauer": 60, "stil": "info"}'`;
      $("#whErg").innerHTML = `<p>${esc(T.whEinmal)}</p><pre>${esc(r.token)}</pre><p class="leise">${esc(T.whBeispiel)}</p><pre>${esc(beispiel)}</pre>`;
    }, null);
  };
}

// „Abschalten ohne Zuschauer“ (seit 0.31.1 unter System → Leistung)
function abschaltenKarte(inhalt) {
  inhalt.innerHTML = `<div class="karte"><h2>${esc(T.abschaltenTitel)}</h2>
      <div class="zeile"><label>${esc(T.abschalten)}</label><input type="number" id="abschalten" value="${E.stream.abschalten_s}" min="10" max="3600"></div>
      <div class="zeile"><button class="knopf haupt" id="okAbs">${esc(T.speichern)}</button></div></div>`;
  $("#okAbs").onclick = (e) => speichernE({ stream: { abschalten_s: Number($("#abschalten").value) } }, e.target);
}

async function verbindung(inhalt, teil = "ha") {
  const info = await holen("/api/ha/einrichtung");
  // Ohne erreichbares HA kennt der Dienst seine IP nicht: dann die Adresse aus dem Browser (bei Docker die des Hosts,
  // die HA ohnehin sieht), sofern sie eine IPv4-Adresse ist – sonst ein Platzhalter
  if (!info.eigene_ip && /^\d{1,3}(\.\d{1,3}){3}$/.test(location.hostname)) info.eigene_ip = location.hostname;
  const ip = info.eigene_ip || T.ipPlatzhalter;
  const yaml = `homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - ${ip}/32
      trusted_users:
        ${ip}/32: ${T.benutzerIdPlatzhalter}
      allow_bypass_login: true
    - type: homeassistant`;
  const B = E.benachrichtigung;
  inhalt.innerHTML = `<div class="karte" data-teil="ha">
      <div class="zeile"><label>${esc(T.haUrl)}</label><input type="url" id="url" value="${esc(E.ha.url)}"></div>
      <div class="zeile"><button class="knopf haupt" id="ok">${esc(T.speichern)}</button><button class="knopf" id="test">${esc(T.testen)}</button></div>
      <p id="testErg"></p></div>
    <div class="karte" data-teil="allgemein"><h2>${esc(T.standort)}</h2>
      <div class="zeile"><input type="text" id="ortText" placeholder="${esc(T.ortSuche)}" value="${esc(E.standort.name || "")}">
        <button class="knopf" id="ortSuchen">${esc(T.suchen)}</button></div>
      <div id="orte"></div>
      <div class="zeile"><input type="number" step="0.0001" id="breite" value="${E.standort.breite}" aria-label="${esc(T.breite)}">
        <input type="number" step="0.0001" id="laenge" value="${E.standort.laenge}" aria-label="${esc(T.laenge)}">
        <button class="knopf" id="ausHA">${esc(T.standortAusHA)}</button><button class="knopf haupt" id="okOrt">${esc(T.speichern)}</button></div></div>
    <div class="karte" data-teil="allgemein"><h2>${esc(T.zeitTitel)}</h2><p class="leise">${esc(T.zeitText)}</p>
      <div class="zeile"><label>${esc(T.ntpServer)}</label><input type="text" id="ntp" value="${esc(E.zeit.ntp)}" placeholder="${esc(T.ntpAuto)}"></div>
      <div class="zeile"><label>${esc(T.zeitzone)}</label><select id="zone" class="breit"><option value="">${esc(T.systemZone)}</option></select></div>
      <div class="zeile"><button class="knopf haupt" id="okZeit">${esc(T.speichern)}</button><span class="leise" id="zeitStand"></span></div></div>
    <div class="karte" data-teil="benachrichtigung"><h2>${esc(T.bnTitel)}</h2><p class="leise">${esc(T.bnText)}</p>
      <h3>${esc(T.bnTelegram)}</h3>
      <div class="zeile"><label><input type="checkbox" id="bnTgAktiv" ${B.telegram.aktiv ? "checked" : ""}> ${esc(T.bnAktiv)}</label></div>
      <div class="zeile"><label>${esc(T.bnBotToken)}</label><input type="password" id="bnTgToken" value="${esc(B.telegram.token)}" autocomplete="off"></div>
      <div class="zeile"><label>${esc(T.bnChatId)}</label><input type="text" id="bnTgChat" value="${esc(B.telegram.chat_id)}"></div>
      <div class="zeile"><button class="knopf" data-test="telegram">${esc(T.bnTest)}</button></div>
      <h3>${esc(T.bnEmail)}</h3>
      <div class="zeile"><label><input type="checkbox" id="bnEmAktiv" ${B.email.aktiv ? "checked" : ""}> ${esc(T.bnAktiv)}</label></div>
      <div class="zeile"><label>${esc(T.bnServer)}</label><input type="text" id="bnEmServer" value="${esc(B.email.server)}">
        <input type="number" id="bnEmPort" min="1" max="65535" value="${B.email.port}" aria-label="${esc(T.bnPort)}"></div>
      <div class="zeile"><label>${esc(T.bnBenutzer)}</label><input type="text" id="bnEmBenutzer" value="${esc(B.email.benutzer)}" autocomplete="off"></div>
      <div class="zeile"><label>${esc(T.bnPasswort)}</label><input type="password" id="bnEmPw" value="${esc(B.email.passwort)}" autocomplete="new-password"></div>
      <div class="zeile"><label>${esc(T.bnEmpfaenger)}</label><input type="text" id="bnEmAn" value="${esc(B.email.empfaenger)}"></div>
      <details class="erweitert"><summary>${esc(T.erweitert)}</summary>
      <div class="zeile"><label>${esc(T.bnSicherheit)}</label><select id="bnEmSich">${["starttls", "ssl", "keine"].map((v) =>
        `<option value="${v}" ${B.email.sicherheit === v ? "selected" : ""}>${v === "keine" ? "–" : v.toUpperCase()}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(T.bnAbsender)}</label><input type="text" id="bnEmVon" value="${esc(B.email.absender)}"></div></details>
      <div class="zeile"><button class="knopf" data-test="email">${esc(T.bnTest)}</button></div>
      <h3>${esc(T.bnHA)}</h3>
      <div class="zeile"><label><input type="checkbox" id="bnHaAktiv" ${B.ha.aktiv ? "checked" : ""}> ${esc(T.bnAktiv)}</label></div>
      <div class="zeile"><label>${esc(T.bnDienst)}</label><input type="text" id="bnHaDienst" value="${esc(B.ha.dienst)}" placeholder="notify.notify"></div>
      <div class="zeile"><button class="knopf" data-test="ha">${esc(T.bnTest)}</button></div>
      <h3>${esc(T.bnEreignisse)}</h3>
      ${Object.keys(T.bnEr).map((k) => `<div class="zeile"><label><input type="checkbox" data-er="${k}" ${B.ereignisse[k] ? "checked" : ""}> ${esc(T.bnEr[k])}</label></div>`).join("")}
      <div class="zeile"><button class="knopf haupt" id="bnOk">${esc(T.speichern)}</button></div><div id="bnLetzte" class="leise"></div></div>
    <div class="karte" data-teil="ha"><h2>${esc(T.anleitung)}</h2>${T.anleitungText(info.eigene_ip).map((z) => `<p>${esc(z)}</p>`).join("")}
      <pre>${esc(yaml)}</pre><p>${esc(T.anleitungEnde)}</p></div>
    ${CONTAINER ? `<div class="karte" data-teil="zugang"><h2>${esc(T.verwaltungTitel)}</h2>
      <div class="zeile"><label>${esc(T.pwAlt)}</label><input type="password" id="pwAlt" autocomplete="current-password"></div>
      <div class="zeile"><label>${esc(T.pwNeu)}</label><input type="password" id="pwNeu" autocomplete="new-password" minlength="8"></div>
      <div class="zeile"><button class="knopf haupt" id="pwOk">${esc(T.pwAendern)}</button>
        <form method="post" action="/abmelden"><button class="knopf" type="submit">${esc(T.abmelden)}</button></form></div></div>` : ""}`;
  const bnDaten = () => ({ benachrichtigung: {
    telegram: { aktiv: $("#bnTgAktiv").checked, token: $("#bnTgToken").value.trim(), chat_id: $("#bnTgChat").value.trim() },
    email: { aktiv: $("#bnEmAktiv").checked, server: $("#bnEmServer").value.trim(), port: Number($("#bnEmPort").value),
      sicherheit: $("#bnEmSich").value, benutzer: $("#bnEmBenutzer").value.trim(), passwort: $("#bnEmPw").value,
      absender: $("#bnEmVon").value.trim(), empfaenger: $("#bnEmAn").value.trim() },
    ha: { aktiv: $("#bnHaAktiv").checked, dienst: $("#bnHaDienst").value.trim() || "notify.notify" },
    ereignisse: Object.fromEntries([...inhalt.querySelectorAll("[data-er]")].map((x) => [x.dataset.er, x.checked])) } });
  $("#bnOk").onclick = (e) => speichernE(bnDaten(), e.target);
  for (const k of inhalt.querySelectorAll("[data-test]")) {
    k.onclick = (e) => aktion(e.target, async () => {          // erst speichern, dann mit den gespeicherten Daten testen
      E = (await senden("/api/einstellungen", bnDaten())).einstellungen;
      await senden("/api/benachrichtigung/test", { kanal: k.dataset.test });
    }, T.bnTestOk);
  }
  holen("/api/status").then((s) => {
    const l = s.benachrichtigung || [];
    if (l.length) $("#bnLetzte").textContent = T.bnLetzte + ": " + l.slice(0, 3).map((x) => `${x.zeit} ${x.betreff}` +
      Object.entries(x.ergebnis).map(([k, f]) => ` · ${k} ${f ? "✗ " + f : "✓"}`).join("")).join(" | ");
  }).catch(() => {});
  if (CONTAINER) $("#pwOk").onclick = (e) => aktion(e.target, async () => {
    const r = await fetch("/verwaltung/passwort", { method: "POST", credentials: "same-origin",
      headers: { "X-SignageCast": "1", "Content-Type": "application/json" },
      body: JSON.stringify({ alt: $("#pwAlt").value, neu: $("#pwNeu").value }) });
    const d = await r.json();
    if (!d.ok) throw new Error(d.fehler);
    $("#pwAlt").value = ""; $("#pwNeu").value = ""; hinweiseZeichnen();
  }, T.pwGeaendert);
  const test = async () => {
    const r = await holen("/api/ha/test");
    $("#testErg").innerHTML = r.ok ? `<span class="gut">${esc(T.testOk(r.version))}</span> · ${esc(r.ort || "")}` : `<span class="schlecht">${esc(T.haFehler[r.code] ? T.haFehler[r.code] + (r.detail ? ": " + r.detail : "") : r.fehler)}</span>`;
    return r;
  };
  $("#ok").onclick = (e) => aktion(e.target, async () => { const d = await senden("/api/einstellungen", { ha: { url: $("#url").value } }); E = d.einstellungen; ENTITAETEN = null; await test(); });
  $("#test").onclick = (e) => aktion(e.target, test, null);
  $("#ausHA").onclick = (e) => aktion(e.target, async () => {
    const r = await test(); if (!r.ok) throw new Error(r.fehler);
    $("#breite").value = r.breite; $("#laenge").value = r.laenge;
  }, null);
  holen("/api/zeitzonen").then((z) => {
    $("#zone").options[0].textContent = `${T.systemZone} (${z.system})`;
    for (const n of z.zeitzonen) $("#zone").add(new Option(n, n, false, n === E.zeit.zeitzone));
  }).catch(() => {});
  const zeitStand = async () => {
    const s = await holen("/api/status"), z = s.zeit_quelle || {};
    $("#zeitStand").textContent = (z.host_synchronisiert && !z.korrektur ? hostSync() + " · " : z.korrektur ? T.hostNichtSync + " · " : "") +
      (z.server ? `${z.server}: ${T.abweichung} ${z.abweichung_s ?? "?"} s · ${z.gemessen || ""}${z.fehler ? " · " + meldungText(z.fehler_m, z.fehler) : ""}` : "");
  };
  zeitStand();
  $("#okZeit").onclick = (e) => aktion(e.target, async () => {
    const d = await senden("/api/einstellungen", { zeit: { ntp: $("#ntp").value.trim(), zeitzone: $("#zone").value } });
    E = d.einstellungen; setTimeout(() => zeitStand().catch(() => {}), 5000);
  });
  $("#okOrt").onclick = (e) => speichernE({ standort: { breite: Number($("#breite").value), laenge: Number($("#laenge").value), name: $("#ortText").value } }, e.target);
  const ortSuchen = (e) => aktion(e.target, async () => {
    const r = await holen("/api/ort/suche?q=" + encodeURIComponent($("#ortText").value));
    if (!r.ok) throw new Error(r.fehler);
    const ziel = $("#orte"); ziel.innerHTML = "";
    for (const o of r.orte) {
      const z = el(`<div class="zeile eintrag"><span>${esc(o.name)}</span><span class="leise">${o.breite} / ${o.laenge}</span>
        <button class="knopf haupt">${esc(T.uebernehmen)}</button></div>`);
      z.querySelector("button").onclick = (ev) => aktion(ev.target, async () => {
        $("#breite").value = o.breite; $("#laenge").value = o.laenge; $("#ortText").value = o.name.split(",")[0];
        const d = await senden("/api/einstellungen", { standort: { breite: o.breite, laenge: o.laenge, name: o.name.split(",")[0] } });
        E = d.einstellungen; ziel.innerHTML = "";
      }, T.ortGesetzt);
      ziel.appendChild(z);
    }
  }, null);
  $("#ortSuchen").onclick = ortSuchen;
  $("#ortText").onkeydown = (e) => { if (e.key === "Enter") ortSuchen({ target: $("#ortSuchen") }); };
  // Eine Seite je Teil: die übrigen Karten bleiben unsichtbar im DOM (ihre Knöpfe sind schon verbunden)
  for (const k of inhalt.querySelectorAll("[data-teil]")) k.hidden = k.dataset.teil !== teil;
}
async function allgemeinSeite(inhalt) {
  inhalt.innerHTML = `<div id="tAnz"></div><div id="tVerb"></div>`;
  await anzeige($("#tAnz"));
  await verbindung($("#tVerb"), "allgemein");
}

// ---------- Fernseher ----------
function zeitZeile(z) {
  return `<div class="zeile eintrag"><label>${esc(T.von)}</label><input type="time" name="zvon" value="${esc(z.von)}">
    <label>${esc(T.bis)}</label><input type="time" name="zbis" value="${esc(z.bis)}">
    <select name="zlayout"><option value="schwarz" ${z.layout === "schwarz" ? "selected" : ""}>${esc(T.schwarz)}</option>
      ${E.layouts.map((l) => `<option value="${esc(l.id)}" ${l.id === z.layout ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select>
    <button class="knopf gefahr" name="zweg">✕</button></div>`;
}
// Seit 0.22: Kodierung je Fernseher (Encoder, Preset, Tune, B-Frames) – was hier nicht geht, ist ausgegraut
const ENC_KURZ = { vaapi: "VAAPI", qsv: "QSV", nvenc: "NVENC", software: "Software" };
function kodierungTeil(t, sta) {
  const verf = ((sta.kodierung || {}).encoder) || {};
  const ts = (sta.fernseher || []).find((x) => x.id === t.id) || {};
  const grund = (g) => T.kod.grund[g] || g;
  const f = ts.kodier_fehler;
  return `<h3>${esc(T.kod.titel)}</h3><p class="leise">${esc(T.kod.text)}</p>
    ${f ? `<p class="warn">${esc(T.kod.fehler(T.kod.art[f.encoder] || f.encoder, grund(f.grund)))}</p>` : ""}
    ${ts.encoder ? `<p class="leise">${esc(T.kod.aktiv)}: <b>${esc(T.kod.art[ts.encoder] || ts.encoder)}</b></p>` : ""}
    <div class="zeile"><label>${esc(T.kod.encoder)}</label><select name="encoder">${Object.keys(T.kod.art).map((x) => {
      const v = verf[x], nicht = x !== "auto" && v && !v.ok;
      return `<option value="${x}" ${x === (t.encoder || "auto") ? "selected" : ""} ${nicht && x !== t.encoder ? "disabled" : ""}>${esc(T.kod.art[x])}${nicht ? " – " + esc(grund(v.grund)) : ""}</option>`;
    }).join("")}</select></div>
    <p class="leise" name="encInfo"></p>
    <div class="zeile"><label>${esc(T.kod.preset)}</label><select name="preset">${["ultrafast", "superfast", "veryfast", "fast", "medium"].map((x) =>
      `<option value="${x}" ${x === (t.preset || "veryfast") ? "selected" : ""}>${x}${x === "veryfast" ? ` (${esc(T.kod.std)})` : ""}</option>`).join("")}</select></div>
    <p class="leise">${esc(T.kod.presetInfo)}</p>
    <div class="zeile"><label>${esc(T.kod.tune)}</label><select name="tune">${Object.keys(T.kod.tuneArt).map((x) =>
      `<option value="${x}" ${x === (t.tune || "zerolatency") ? "selected" : ""}>${esc(T.kod.tuneArt[x])}</option>`).join("")}</select></div>
    <p class="leise">${esc(T.kod.tuneInfo)}</p><p class="leise" name="ohneInfo"></p>
    <div class="zeile"><label>${esc(T.kod.bframes)}</label><input type="number" name="bframes" min="0" max="4" value="${t.bframes || 0}" style="width:70px"></div>
    <p class="leise">${esc(T.kod.bfInfo)}</p>
    <div class="zeile"><button class="knopf" name="kodStandard">${esc(T.kod.standard)}</button></div>`;
}
function kodierungAnbinden(k, sta) {
  const w = (n) => k.querySelector(`[name=${n}]`);
  const auto = ((sta.kodierung || {}).art) === "software" ? "software" : "vaapi";
  const zeigen = () => {
    const enc = w("encoder").value, wirk = enc === "auto" ? auto : enc;
    w("encInfo").textContent = T.kod.info[enc];
    w("preset").disabled = w("tune").disabled = wirk === "vaapi";
    w("ohneInfo").textContent = wirk === "vaapi" ? T.kod.ohne : "";
  };
  w("encoder").onchange = zeigen; zeigen();
  w("kodStandard").onclick = () => { w("encoder").value = "auto"; w("preset").value = "veryfast"; w("tune").value = "zerolatency"; w("bframes").value = 0; zeigen(); };
}
// Zustand des Fernsehers laut Home Assistant (seit 0.37) und Ergebnis von „nach dem Einschalten“
function haZustandText(sta, t, lang) {
  const h = (((sta || {}).schalten || {})[t.id] || {}).ha;
  if (!t.ha_schalten || !h) return lang && t.ha_schalten ? T.haZustandNoch : "";
  const kurz = T.haZustand[h.zustand] || h.zustand;
  if (!lang) return kurz;
  return T.haZustandLang(kurz, h.roh, h.quelle, new Date(h.zeit * 1000).toLocaleTimeString(ORT(), { hour: "2-digit", minute: "2-digit" }));
}
function nachText(sta, t) {
  const n = (((sta || {}).schalten || {})[t.id] || {}).nach;
  return n ? T.nachZuletzt(n) : "";
}
async function fernseherSeite(inhalt) {
  const st = await holen("/api/ha/einrichtung");
  let sta = await holen("/api/status").catch(() => ({}));
  const ip = st.eigene_ip || location.hostname;
  const zeichnen = () => {
    inhalt.innerHTML = `<p class="leise">${esc(T.fernseherText)} ${esc(T.tvHinweis)}</p><div id="tvListe"></div>
      <div class="zeile"><button class="knopf" id="tvPlus">${esc(T.fernseherNeu)}</button>
        <button class="knopf haupt" id="ok">${esc(T.speichern)}</button></div>`;
    const liste = $("#tvListe");
    E.fernseher.forEach((t, i) => {
      const k = el(`<div class="karte" data-i="${i}">
        <div class="zeile"><label>${esc(T.senderName)}</label><input type="text" name="name" value="${esc(t.name)}"></div>
        <div class="zeile"><label>${esc(T.kennung)}</label><input type="text" name="id" value="${esc(t.id)}" pattern="[a-z][a-z0-9]{0,11}" style="width:140px"></div>
        <div class="zeile"><label>${esc(T.adresse)}</label><code>http://${esc(ip)}:${esc(st.stream_port || 8888)}/${esc(t.id)}</code></div>
        <h3>${esc(T.abschnitt.anzeige)}</h3>
        <div class="zeile"><label>${esc(T.layoutWahl)}</label><select name="layout">${E.layouts.map((l) => `<option value="${esc(l.id)}" ${l.id === t.layout ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select></div>
        <details ${(t.zeitplan || []).length ? "open" : ""}><summary>${esc(T.zeitplan)} (${(t.zeitplan || []).length})</summary>
          <p class="leise">${esc(T.zeitplanText)}</p><div name="zeiten">${(t.zeitplan || []).map((z) => zeitZeile(z)).join("")}</div>
          <button class="knopf" name="zeitPlus">${esc(T.zeitNeu)}</button></details>
        <details ${(t.karussell || {}).aktiv ? "open" : ""}><summary>${esc(T.karussell)}${(t.karussell || {}).aktiv ? " ✓" : ""}</summary>
          <p class="leise">${esc(T.karussellText)}</p>
          <div class="zeile"><label>${esc(T.karussellAn)}</label>${schalter("k_aktiv", (t.karussell || {}).aktiv)}
            <label>${esc(T.karussellMin)}</label><input type="number" name="k_min" min="1" max="1440" value="${(t.karussell || {}).minuten || 5}" style="width:80px"></div>
          ${E.layouts.map((l) => `<label style="margin-right:12px"><input type="checkbox" name="k_l" value="${esc(l.id)}" ${((t.karussell || {}).layouts || []).includes(l.id) ? "checked" : ""}> ${esc(l.name)}</label>`).join("")}</details>
        <details ${t.ha_schalten ? "open" : ""}><summary>${esc(T.schalten)}${t.ha_schalten ? " ✓" : ""}${haZustandText(sta, t) ? " · " + esc(haZustandText(sta, t)) : ""}</summary><p class="leise">${esc(T.schaltenText)}</p>
          <div class="zeile"><input type="text" name="ha_schalten" value="${esc(t.ha_schalten || "")}" placeholder="media_player.tv_wohnzimmer" spellcheck="false" class="breit">
            <button class="knopf" name="schAus">${esc(T.schaltenAus)}</button><button class="knopf" name="schAn">${esc(T.schaltenAn)}</button></div>
          <p class="leise" name="haZustand">${esc(haZustandText(sta, t, true))}</p>
          <h4>${esc(T.nachEin)}</h4>
          <div class="zeile"><label>${esc(T.haQuelle)}</label><input type="text" name="ha_quelle" value="${esc(t.ha_quelle || "")}" list="quellen-${esc(t.id)}" placeholder="HDMI 2" spellcheck="false">
            <datalist id="quellen-${esc(t.id)}"></datalist><button class="knopf" name="quellenHolen">${esc(T.quellenHolen)}</button></div>
          <p class="leise" name="quelleInfo">${esc(T.quelleText)}</p>
          <div class="zeile"><label>${esc(T.oeffnen)}</label><select name="ha_oeffnen">${["", "lg", "android", "eigen"].map((x) =>
            `<option value="${x}" ${x === (t.ha_oeffnen || "") ? "selected" : ""}>${esc(T.oeffnenArt[x])}</option>`).join("")}</select></div>
          <div name="eigenTeil"><div class="zeile"><label>${esc(T.haDienst)}</label><input type="text" name="ha_dienst" value="${esc(t.ha_dienst || "")}" placeholder="script.turn_on" spellcheck="false"></div>
            <textarea name="ha_daten" rows="3" spellcheck="false" placeholder='{"entity_id": "script.tv_seite", "variables": {"adresse": "{url}"}}'>${esc(t.ha_daten || "")}</textarea></div>
          <p class="leise" name="oeffnenInfo"></p>
          <div class="zeile"><button class="knopf" name="nachTest">${esc(T.nachTest)}</button><span class="leise" name="nachErg">${esc(nachText(sta, t))}</span></div></details>
        <h3>${esc(T.abschnitt.video)}</h3>
        <div class="zeile"><label>${esc(T.videoZeigen)}</label>${schalter("video", t.video)}</div>
        <div class="zeile"><label>${esc(T.videoQuelle)}</label><select name="video_quelle">${Object.keys(T.videoQuelleArt).map((x) => `<option value="${x}" ${x === (t.video_quelle || "youtube") ? "selected" : ""}>${esc(T.videoQuelleArt[x])}</option>`).join("")}</select>
          <span name="alleTeil"><label>${esc(T.medienAlle)}</label><input type="number" name="medien_alle" min="1" max="20" value="${t.medien_alle || 3}" style="width:70px"></span></div>
        <details><summary>${esc(T.kategorien)} (${katIds().length - t.kategorien_aus.length}/${katIds().length})</summary>
        ${katSchalter("kat_", t.kategorien_aus)}</details>
        <h3>${esc(T.abschnitt.ton)}</h3>
        <div class="zeile"><label>${esc(T.ton)}</label><select name="ton">${Object.keys(T.tonArt).map((x) => `<option value="${x}" ${x === t.ton ? "selected" : ""}>${esc(T.tonArt[x])}</option>`).join("")}</select></div>
        <div class="zeile" name="senderZeile"><label>${esc(T.sender)}</label><select name="radio_sender" class="breit"><option value="">${esc(T.keinSender)}</option>
          ${E.radio.sender.map((x) => `<option value="${esc(x.id)}" ${x.id === t.radio_sender ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select></div>
        <div class="zeile"><label>${esc(T.lautstaerke)}</label><input type="range" name="lautstaerke" min="0" max="100" value="${t.lautstaerke}"><span class="leise" name="lw">${t.lautstaerke} %</span></div>
        <details><summary>${esc(T.streamTechnik)}: ${t.aufloesung === 2160 ? "4K" : "Full HD"}${(t.aufnahme || 1080) !== 1080 ? " (" + esc(T.aufnahme) + " " + t.aufnahme + "p)" : ""}, ${t.bitrate_mbit} Mbit/s, ${
          (t.codec === "auto" ? (t.aufloesung === 2160 ? "H.265" : "H.264") + " (auto)" : t.codec === "h264" ? "H.264" : "H.265")}${
          t.encoder && t.encoder !== "auto" ? ", " + ENC_KURZ[t.encoder] : ""}</summary>
        <div class="zeile"><label>${esc(T.aufloesung)}</label><select name="aufloesung"><option value="2160" ${t.aufloesung === 2160 ? "selected" : ""}>4K (3840×2160)</option>
          <option value="1080" ${t.aufloesung === 1080 ? "selected" : ""}>Full HD (1920×1080)</option></select></div>
        <div class="zeile"><label>${esc(T.aufnahme)}</label><select name="aufnahme">${[720, 1080, 1440].map((h) =>
          `<option value="${h}" ${h === (t.aufnahme || 1080) ? "selected" : ""}>${esc(T.aufnahmeArt[h])}</option>`).join("")}</select></div>
        <p class="leise">${esc(T.aufnahmeText)}</p>
        <div class="zeile"><label>${esc(T.bitrate)}</label><input type="number" name="bitrate_mbit" min="2" max="40" value="${t.bitrate_mbit}"></div>
        <div class="zeile"><label>${esc(T.codec)}</label><select name="codec">${Object.keys(T.codecArt).map((k) =>
          `<option value="${k}" ${k === (t.codec || "auto") ? "selected" : ""}>${esc(T.codecArt[k])}</option>`).join("")}</select></div>
        <p class="leise">${esc(T.codecText)}</p>${kodierungTeil(t, sta)}</details>
        ${E.fernseher.length > 1 ? `<div class="zeile"><button class="knopf gefahr" name="weg">${esc(T.fernseherWeg)}</button></div>` : ""}</div>`);
      const zeitenAnbinden = () => k.querySelectorAll("[name=zweg]").forEach((b) => { b.onclick = () => b.closest(".zeile").remove(); });
      zeitenAnbinden();
      k.querySelector("[name=zeitPlus]").onclick = () => { k.querySelector("[name=zeiten]").insertAdjacentHTML("beforeend", zeitZeile({ von: "23:00", bis: "06:00", layout: "schwarz" })); zeitenAnbinden(); };
      const senderSichtbar = () => { k.querySelector("[name=senderZeile]").style.display = k.querySelector("[name=ton]").value === "radio" ? "" : "none"; };
      k.querySelector("[name=ton]").onchange = senderSichtbar; senderSichtbar();
      const alleSichtbar = () => { k.querySelector("[name=alleTeil]").style.display = k.querySelector("[name=video_quelle]").value === "gemischt" ? "" : "none"; };
      k.querySelector("[name=video_quelle]").onchange = alleSichtbar; alleSichtbar();
      kodierungAnbinden(k, sta);
      k.querySelector("[name=lautstaerke]").oninput = (e) => { k.querySelector("[name=lw]").textContent = e.target.value + " %"; };
      const oeffnenSichtbar = () => {
        const art = k.querySelector("[name=ha_oeffnen]").value;
        k.querySelector("[name=eigenTeil]").style.display = art === "eigen" ? "" : "none";
        k.querySelector("[name=oeffnenInfo]").textContent = art ? T.oeffnenText[art](`http://${ip}:${st.stream_port || 8888}/${t.id}`) : "";
      };
      k.querySelector("[name=ha_oeffnen]").onchange = oeffnenSichtbar; oeffnenSichtbar();
      k.querySelector("[name=nachTest]").onclick = (ev) => aktion(ev.target, async () => {
        const r = await senden("/api/fernseher/nach-einschalten", { tv: t.id });
        k.querySelector("[name=nachErg]").textContent = nachText({ schalten: { [t.id]: { nach: r.nach } } }, t);
        if (r.fehler) throw new Error(r.fehler);
      }, T.schaltenOk);
      k.querySelector("[name=quellenHolen]").onclick = (ev) => aktion(ev.target, async () => {
        const ent = k.querySelector("[name=ha_schalten]").value.trim();
        const r = await holen("/api/ha/quellen?entity=" + encodeURIComponent(ent));
        if (!r.ok) throw new Error(r.fehler === "media_player" ? T.quelleNurMp : r.fehler);
        k.querySelector(`#quellen-${t.id}`).innerHTML = r.quellen.map((x) => `<option value="${esc(x)}">`).join("");
        k.querySelector("[name=quelleInfo]").textContent = r.quellen.length ? T.quellenGefunden(r.quellen.join(", "), r.aktuell || "–") : T.keineQuellen;
      }, null);
      for (const [n, an] of [["schAus", false], ["schAn", true]])
        k.querySelector(`[name=${n}]`).onclick = (ev) => aktion(ev.target, () => senden("/api/fernseher/schalten", { tv: t.id, an }), T.schaltenOk);
      const weg = k.querySelector("[name=weg]");
      if (weg) weg.onclick = () => { if (confirm(T.wirklichTvWeg)) { E.fernseher = lesen().filter((_, j) => j !== i); zeichnen(); } };
      liste.appendChild(k);
    });
    const lesen = () => [...liste.children].map((k) => {
      const t = E.fernseher[Number(k.dataset.i)];
      const w = (n) => k.querySelector(`[name=${n}]`);
      return { ...t, name: w("name").value, id: w("id").value.trim().toLowerCase(), video: w("video").checked, ton: w("ton").value,
               radio_sender: w("radio_sender").value, lautstaerke: Number(w("lautstaerke").value),
               kategorien_aus: katIds().filter((x) => !w("kat_" + x).checked), aufloesung: Number(w("aufloesung").value),
               aufnahme: Number(w("aufnahme").value), bitrate_mbit: Number(w("bitrate_mbit").value), codec: w("codec").value, layout: w("layout").value,
               encoder: w("encoder").value, preset: w("preset").value, tune: w("tune").value, bframes: Number(w("bframes").value) || 0,
               video_quelle: w("video_quelle").value, medien_alle: Number(w("medien_alle").value) || 3, ha_schalten: w("ha_schalten").value.trim(),
               ha_quelle: w("ha_quelle").value.trim(), ha_oeffnen: w("ha_oeffnen").value, ha_dienst: w("ha_dienst").value.trim(),
               ha_daten: w("ha_daten").value.trim(),
               karussell: { aktiv: w("k_aktiv").checked, minuten: Number(w("k_min").value) || 5,
                            layouts: [...k.querySelectorAll("[name=k_l]:checked")].map((c) => c.value) },
               zeitplan: [...k.querySelectorAll("[name=zeiten] .zeile")].map((z) => ({ von: z.querySelector("[name=zvon]").value,
                 bis: z.querySelector("[name=zbis]").value, layout: z.querySelector("[name=zlayout]").value })) };
    });
    $("#tvPlus").onclick = () => {
      const alt = lesen();
      let n = 2; while (alt.some((t) => t.id === "tv" + n)) n++;
      E.fernseher = [...alt, { id: "tv" + n, name: T.weitererTv + " " + n, video: true, ton: "aus", radio_sender: "", lautstaerke: 70,
                                kategorien_aus: [], aufloesung: 1080, aufnahme: 1080, bitrate_mbit: 8, codec: "auto",
                                encoder: "auto", preset: "veryfast", tune: "zerolatency", bframes: 0 }];
      zeichnen();
    };
    $("#ok").onclick = async (e) => {
      await speichernE({ fernseher: lesen() }, e.target);
      sta = await holen("/api/status").catch(() => sta);     // Ergebnis der Probe-Kodierung anzeigen
      zeichnen();
    };
  };
  zeichnen();
}

// ---------- Radio ----------
async function radioSeite(inhalt) {
  inhalt.innerHTML = `<div class="karte"><h2>${esc(T.meineSender)}</h2><p class="leise">${esc(T.senderNutzung)}</p><div id="meine"></div>
      <div class="zeile"><label>${esc(T.senderAnzeigen)}</label>${schalter("anzeigen", E.radio.anzeigen)}</div>
      <details class="erweitert"><summary>${esc(T.erweitert)}</summary>
      <div class="zeile"><label>${esc(T.puffer)}</label><input type="number" id="puffer" min="0" max="120" value="${E.radio.puffer_s}"><span class="leise">s</span>
        <button class="knopf" id="pufferOk">${esc(T.speichern)}</button></div><p class="leise">${esc(T.pufferText)}</p></details></div>
    <div class="karte"><h2>${esc(T.eigenerSender)}</h2>
      <div class="zeile"><input type="url" id="sUrl" placeholder="${esc(T.senderAdresse)}"></div>
      <div class="zeile"><input type="text" id="sName" placeholder="${esc(T.senderName)}"><button class="knopf haupt" id="sOk">${esc(T.hinzu)}</button></div>
      <h3>${esc(T.playlist)}</h3><p class="leise">${esc(T.playlistText)}</p>
      <textarea id="plText" placeholder="#EXTM3U&#10;#EXTINF:-1,Mein Sender&#10;https://…/stream.mp3"></textarea>
      <div class="zeile"><input type="file" id="plDatei" accept=".m3u,.m3u8,.pls,audio/x-mpegurl,audio/x-scpls,text/plain">
        <button class="knopf haupt" id="plOk">${esc(T.playlistUebernehmen)}</button></div><div id="plErg"></div></div>
    <div class="karte"><h2>${esc(T.inNaehe)}${E.standort.name ? ": " + esc(E.standort.name) : ""}</h2>
      <div class="zeile"><input type="text" id="woerter" placeholder="${esc(T.regionWoerter)}" value="${esc(E.radio.region_woerter.join(", "))}">
        <button class="knopf" id="vLaden">${esc(T.vorschlaegeLaden)}</button></div>
      <p class="leise" id="vInfo">${esc(T.quelle)}</p><div id="vorschlaege"></div></div>
    <div class="karte"><h2>${esc(T.senderSuche)}</h2>
      <div class="zeile"><input type="text" id="nameSuche" data-frei placeholder="Antenne Bayern"><button class="knopf" id="nOk">${esc(T.suchen)}</button></div>
      <div id="suchErg"></div></div>`;
  const meineZeichnen = () => {
    const m = $("#meine"); m.innerHTML = E.radio.sender.length ? "" : `<p class="leise">${esc(T.keineSender)}</p>`;
    for (const x of E.radio.sender) {
      const nutzer = E.fernseher.filter((t) => t.radio_sender === x.id && t.ton === "radio").map((t) => t.name);
      const z = el(`<div class="zeile eintrag"><b>${esc(x.name)}</b><span class="leise" style="word-break:break-all">${esc(x.url)}</span>
        ${nutzer.length ? `<span class="marke gut">♪ ${esc(nutzer.join(", "))}</span>` : ""}
        <button class="knopf" name="bearbeiten">${esc(T.bearbeiten)}</button><button class="knopf gefahr" name="weg">${esc(T.entfernen)}</button></div>`);
      z.querySelector("[name=weg]").onclick = (e) => aktion(e.target, async () => {
        const d = await senden(`/api/radio/sender/${encodeURIComponent(x.id)}/entfernen`); E = d.einstellungen; meineZeichnen();
      });
      z.querySelector("[name=bearbeiten]").onclick = () => {
        if (z.nextElementSibling && z.nextElementSibling.classList.contains("bearbeiten")) return z.nextElementSibling.remove();
        const f = el(`<div class="bearbeiten eintrag">
          <div class="zeile"><input type="text" name="name" value="${esc(x.name)}" aria-label="${esc(T.senderName)}"></div>
          <div class="zeile"><input type="url" name="url" value="${esc(x.url)}" aria-label="${esc(T.senderAdresse)}"></div>
          <div class="zeile"><button class="knopf haupt">${esc(T.speichern)}</button></div></div>`);
        f.querySelector("button").onclick = (e) => aktion(e.target, async () => {
          const d = await senden(`/api/radio/sender/${encodeURIComponent(x.id)}`,
                                 { name: f.querySelector("[name=name]").value, url: f.querySelector("[name=url]").value });
          E = d.einstellungen; meineZeichnen();
        });
        z.after(f);
      };
      m.appendChild(z);
    }
  };
  meineZeichnen();
  $("[name=anzeigen]").onchange = (e) => speichernE({ radio: { anzeigen: e.target.checked } });
  $("#pufferOk").onclick = (e) => speichernE({ radio: { puffer_s: Number($("#puffer").value) } }, e.target);
  const hinzufuegen = (knopf, url, name) => aktion(knopf, async () => {
    const d = await senden("/api/radio/sender", { url, name }); E = d.einstellungen; meineZeichnen();
  }, T.hinzugefuegt);
  $("#sOk").onclick = (e) => hinzufuegen(e.target, $("#sUrl").value, $("#sName").value);
  $("#plDatei").onchange = async (e) => { const f = e.target.files[0]; if (f) $("#plText").value = (await f.text()).slice(0, 200000); };
  $("#plOk").onclick = (e) => aktion(e.target, async () => {
    $("#plErg").textContent = T.playlistPruefen;
    const d = await senden("/api/radio/playlist", { text: $("#plText").value });
    E = d.einstellungen; meineZeichnen();
    $("#plErg").innerHTML = `<p>${esc(T.playlistErgebnis(d.neu.length, d.doppelt))}</p>` +
      (d.fehler.length ? `<p class="warn">${(d.fehler_m || []).length
        ? d.fehler_m.map((m) => esc(`${m.name}: ${meldungText(m, m.text)}`)).join("<br>") : d.fehler.map(esc).join("<br>")}</p>` : "");
    if (d.neu.length) $("#plText").value = "";
  }, null);
  const senderListe = (ziel, liste) => {
    for (const x of liste) {
      const z = el(`<div class="zeile eintrag"><b>${esc(x.name)}</b>
        <span class="leise">${esc([x.region, x.codec, x.bitrate ? x.bitrate + " kbit/s" : "", x.stichworte].filter(Boolean).join(" · "))}</span>
        <button class="knopf">${esc(T.hinzu)}</button></div>`);
      z.querySelector("button").onclick = (e) => hinzufuegen(e.target, x.url, x.name);
      ziel.appendChild(z);
    }
  };
  $("#vLaden").onclick = (e) => aktion(e.target, async () => {
    const woerter = $("#woerter").value.split(",").map((w) => w.trim()).filter(Boolean);
    const d = await senden("/api/einstellungen", { radio: { region_woerter: woerter } }); E = d.einstellungen;
    $("#vInfo").textContent = T.vorschlaegeDauer;
    const r = await holen("/api/radio/vorschlaege");
    if (!r.ok) throw new Error(r.fehler);
    $("#vInfo").textContent = `${T.gefundenFuer}: ${[...r.woerter, ...(r.ort.laender || [])].join(", ")} · ${T.quelle}`;
    const ziel = $("#vorschlaege"); ziel.innerHTML = "";
    for (const g of ["naehe", "region", "land"]) {
      if (!r.gruppen[g].length) continue;
      ziel.appendChild(el(`<h3>${esc(T.gruppe[g])} (${r.gruppen[g].length})</h3>`));
      senderListe(ziel, r.gruppen[g]);
    }
  }, null);
  const nameSuchen = (e) => aktion(e.target, async () => {
    const r = await holen("/api/radio/suche?name=" + encodeURIComponent($("#nameSuche").value));
    if (!r.ok) throw new Error(r.fehler);
    $("#suchErg").innerHTML = ""; senderListe($("#suchErg"), r.sender);
  }, null);
  $("#nOk").onclick = nameSuchen;
  $("#nameSuche").onkeydown = (e) => { if (e.key === "Enter") nameSuchen({ target: $("#nOk") }); };
}

// ---------- Einspieler ----------
async function einspielerSeite(inhalt) {
  const zeichnen = async () => {
    const d = await holen("/api/einspieler");
    const liste = d.einspieler;
    inhalt.innerHTML = `<p class="leise">${esc(T.epText)}</p><div id="epListe">${liste.length ? "" : `<p class="leise">${esc(T.epKeine)}</p>`}</div>
      <div class="zeile"><button class="knopf" id="epPlus">${esc(T.epNeu)}</button><button class="knopf haupt" id="epOk">${esc(T.speichern)}</button></div>`;
    const ziel = $("#epListe");
    const karte = (x) => {
      const st = d.stand[x.id] || {};
      const andere = x.minuten.filter((m) => ![0, 15, 30, 45].includes(m));
      const k = el(`<div class="karte ep" data-id="${esc(x.id)}">
        <div class="zeile"><label>${esc(T.epAktiv)}</label>${schalter("aktiv", x.aktiv)}<input type="text" name="name" value="${esc(x.name)}" placeholder="Name"></div>
        <div class="zeile"><label>${esc(T.epQuelle)}</label><select name="quelle" class="breit">${Object.keys(T.epQuelleArt).map((q) => `<option value="${q}" ${q === x.quelle ? "selected" : ""}>${esc(T.epQuelleArt[q])}</option>`).join("")}</select></div>
        <div class="zeile" name="urlZeile"><label>${esc(T.epUrl)}</label><input type="url" name="url" value="${esc(x.url)}"></div>
        <div class="zeile"><label>${esc(T.epMinuten)}</label>${[0, 15, 30, 45].map((m) => `<label><input type="checkbox" name="m${m}" ${x.minuten.includes(m) ? "checked" : ""}> :${String(m).padStart(2, "0")}</label>`).join("")}
          <input type="text" name="andere" value="${esc(andere.join(","))}" placeholder="${esc(T.epAndere)}" style="width:150px"></div>
        <div class="zeile"><label>${esc(T.epZeit)}</label><input type="time" name="von" value="${esc(x.von)}"> – <input type="time" name="bis" value="${esc(x.bis)}">
          <label><input type="checkbox" name="ton" ${x.ton ? "checked" : ""}> ${esc(T.epTon)}</label></div>
        <div class="zeile"><label>${esc(T.epFernseher)}</label>${E.fernseher.map((t) => `<label><input type="checkbox" name="tv_${esc(t.id)}" ${x.fernseher.includes(t.id) ? "checked" : ""}> ${esc(t.name)}</label>`).join("")}</div>
        <div class="zeile" name="pufferZeile"><label>${esc(T.epPuffer)}</label><select name="puffer">${Object.keys(T.epPufferArt).map((k) => `<option value="${k}" ${k === (x.puffer || "vorab") ? "selected" : ""}>${esc(T.epPufferArt[k])}</option>`).join("")}</select>
          <span name="mengeTeil"><label>${esc(T.epMenge)}</label><select name="menge"><option value="komplett" ${x.vorab_mb ? "" : "selected"}>${esc(T.epKomplett)}</option>
            <option value="mb" ${x.vorab_mb ? "selected" : ""}>${esc(T.epMb)}</option></select>
            <input type="number" name="vorab_mb" min="1" max="2000" value="${x.vorab_mb || 20}" style="width:90px"></span>
          <span name="vorlaufTeil"><label>${esc(T.epVorlauf)}</label><input type="number" name="vorlauf_s" min="0" max="60" value="${x.vorlauf_s ?? 10}" style="width:80px"></span></div>
        <p class="leise" name="pufferText">${esc(T.epPufferText)}</p>
        <div class="zeile"><span class="leise">${st.stand ? esc(T.epStand) + ": " + esc(st.stand.replace("T", " ")) : ""}${st.fehler ? ` <span class="schlecht">${esc(T.epFehler)}: ${esc(meldungText(st.fehler_m, st.fehler))}</span>` : ""}
          ${st.vorab ? " · " + esc(T.epVorab((st.vorab.groesse / 1048576).toFixed(1), st.vorab.komplett ? 0 : (st.vorab.gesamt / 1048576).toFixed(1), (st.vorab.stand || "").replace("T", " ").slice(0, 16))) : ""}
          ${st.vorab_fehler ? ` <span class="schlecht">${esc(T.vorabFehler ? T.vorabFehler + ": " + meldungText(st.vorab_fehler_m, st.vorab_fehler) : st.vorab_fehler)}</span>` : ""}</span>
          <button class="knopf" name="jetzt">${esc(T.epJetzt)}</button><button class="knopf gefahr" name="weg">${esc(T.entfernen)}</button></div></div>`);
      const urlSicht = () => {
        const q = k.querySelector("[name=quelle]").value, p = k.querySelector("[name=puffer]").value;
        k.querySelector("[name=urlZeile]").style.display = q === "tagesschau100" ? "none" : "";
        // YouTube lässt sich nicht puffern; Menge nur bei „vorab“, Sekunden nur bei „Vorlauf“
        k.querySelector("[name=pufferZeile]").style.display = q === "youtube" ? "none" : "";
        k.querySelector("[name=pufferText]").style.display = q === "youtube" ? "none" : "";
        k.querySelector("[name=mengeTeil]").style.display = p === "vorab" ? "" : "none";
        k.querySelector("[name=vorab_mb]").style.display = k.querySelector("[name=menge]").value === "mb" ? "" : "none";
        k.querySelector("[name=vorlaufTeil]").style.display = p === "vorlauf" ? "" : "none";
      };
      for (const n of ["quelle", "puffer", "menge"]) k.querySelector(`[name=${n}]`).onchange = urlSicht;
      urlSicht();
      k.querySelector("[name=weg]").onclick = () => k.remove();
      k.querySelector("[name=jetzt]").onclick = (e) => aktion(e.target, () => senden(`/api/einspieler/${encodeURIComponent(x.id)}/jetzt`), T.epJetztOk);
      return k;
    };
    liste.forEach((x) => ziel.appendChild(karte(x)));
    $("#epPlus").onclick = () => {
      const p = ziel.querySelector("p"); if (p) p.remove();
      ziel.appendChild(karte({ id: Math.random().toString(36).slice(2, 10).replace(/[^a-z0-9]/g, "a").padEnd(8, "x"), name: "tagesschau in 100 Sekunden",
        quelle: "tagesschau100", url: "", minuten: [0, 30], von: "06:00", bis: "23:00", ton: true, fernseher: [], aktiv: true,
        puffer: "vorab", vorab_mb: 0, vorlauf_s: 10 }));
    };
    $("#epOk").onclick = async (e) => {
      const neu = [...ziel.querySelectorAll(".ep")].map((k) => {
        const w = (n) => k.querySelector(`[name=${n}]`);
        const minuten = [0, 15, 30, 45].filter((m) => w("m" + m).checked)
          .concat(w("andere").value.split(",").map((x) => parseInt(x, 10)).filter((x) => x >= 0 && x <= 59));
        return { id: k.dataset.id, name: w("name").value, quelle: w("quelle").value, url: w("url").value.trim(), minuten: minuten.length ? minuten : [0],
                 von: w("von").value, bis: w("bis").value, ton: w("ton").checked, aktiv: w("aktiv").checked,
                 fernseher: E.fernseher.filter((t) => w("tv_" + t.id).checked).map((t) => t.id),
                 puffer: w("puffer").value, vorlauf_s: Number(w("vorlauf_s").value) || 0,
                 vorab_mb: w("menge").value === "mb" ? Math.max(1, Number(w("vorab_mb").value) || 20) : 0 };
      });
      await speichernE({ einspieler: neu }, e.target);
      setTimeout(() => zeichnen().catch(() => {}), 4000);         // Stand/Fehler der Quellen nachladen
    };
  };
  await zeichnen();
}

// ---------- Sicherung ----------
// Änderungsprotokoll (seit 0.38): wer hat wann was geändert – Verwaltung, Pult, Webhook, System. Nur Art und Bereich.
async function protokollSeite(inhalt) {
  const d = await holen("/api/protokoll"), P = T.prot;
  let filter = "", n = 100;
  const aktionText = (x) => {
    const k = x.aktion, m = k.match(/^(stream|radio|player|terminal)_(.+)$/);
    return P.aktion[k] || (m && P.aktion[m[1] + "_*"] ? P.aktion[m[1] + "_*"](m[2]) : k);
  };
  const werText = (x) => x.wer === "Verwaltung" ? P.quellen.verwaltung : x.wer;
  const detailText = (x) => {
    if (/^bild_/.test(x.aktion)) return x.detail.replace(/: (schwarz|steht)$/, (_, b) => ": " + P.befund[b]);
    if (x.aktion !== "einstellungen") return x.detail;
    return x.detail.split("; ").map((teil) => {
      const m = teil.match(/^layouts\.(neu|geaendert|geloescht): (.*)$/);
      if (m) return `${P.layouts[m[1]]}: ${m[2]}`;
      return teil.split(", ").map((b) => P.bereich[b] || b).join(", ");
    }).join(" · ");
  };
  const zeichnen = () => {
    const l = d.eintraege.filter((x) => !filter || x.quelle === filter);
    inhalt.innerHTML = `<div class="karte"><h2>${esc(P.titel)}</h2><p class="leise">${esc(P.text)}</p>
      <div class="zeile"><label for="prFilter">${esc(P.quelle)}</label><select id="prFilter"><option value="">${esc(P.alle)}</option>
        ${["verwaltung", "pult", "webhook", "system"].map((q) => `<option value="${q}" ${q === filter ? "selected" : ""}>${esc(P.quellen[q])}</option>`).join("")}</select></div>
      ${l.length ? `<div class="tabelle-rahmen"><table class="tabelle"><thead><tr><th>${esc(P.zeit)}</th><th>${esc(P.wer)}</th><th>${esc(P.was)}</th></tr></thead><tbody>
        ${l.slice(0, n).map((x) => `<tr><td class="leise">${esc(x.zeit.slice(0, 16))}</td><td>${esc(werText(x))}${(P.quellen[x.quelle] || x.quelle) !== werText(x) ? `<br><span class="leise">${esc(P.quellen[x.quelle] || x.quelle)}</span>` : ""}</td>
          <td>${esc(aktionText(x))}${x.detail ? `<br><span class="leise">${esc(detailText(x))}</span>` : ""}</td></tr>`).join("")}</tbody></table></div>
        ${l.length > n ? `<div class="zeile"><button class="knopf" id="prMehr">${esc(P.mehr)}</button></div>` : ""}` : `<p class="leise">${esc(P.leer)}</p>`}</div>`;
    $("#prFilter").onchange = (e) => { filter = e.target.value; n = 100; zeichnen(); };
    if ($("#prMehr")) $("#prMehr").onclick = () => { n += 200; zeichnen(); };
  };
  zeichnen();
}

// KI-Assistenten im Heimnetz (seit 0.40): Computer verbinden (Datei für Claude Desktop, Befehl/Link für Claude Code,
// Cursor, VS Code) und wieder entfernen. Der Schlüssel wird nur direkt nach dem Verbinden gezeigt.
// ---------- Fernstandorte (seit 0.41; seit 0.42 einfach per Anmelde-Link) ----------
async function fernSeite(inhalt) {
  const F = T.fern, FL = F.link;
  let d = await holen("/api/fernnetz"), pruefung = null, link = "", timer = null, wahl = null;
  const PVE = "lxc.cgroup2.devices.allow: c 10:200 rwm\nlxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file";
  const neu = async () => { d = await holen("/api/fernnetz"); zeichnen(); };
  const beobachten = (bis) => { clearInterval(timer); timer = setInterval(async () => {
    if (!document.body.contains(inhalt.firstElementChild)) { clearInterval(timer); return; }
    d = await holen("/api/fernnetz"); if (bis(d)) { clearInterval(timer); link = ""; } zeichnen(); }, 3000); };
  const kopierFeld = (text, zeilen) => `<div class="zeile"><textarea readonly rows="${zeilen}" style="flex:1;font-family:monospace;font-size:12px">${esc(text)}</textarea>
      <button class="knopf" data-kopieren>${esc(F.kopieren)}</button></div>`;
  const linkHtml = () => {
    const h = d.hier, e = d.einrichtung || {};
    let x = `<h3>${esc(FL.s1)}</h3>`;
    if (!h) {
      if (!d.einrichten_moeglich) x += `<p class="leise">${esc(FL.container)}</p>`;
      else if (e.phase === "laeuft") x += `<p>${esc(FL.laeuft)}</p>`;
      else {
        if (e.phase === "fehler") x += `<p class="schlecht">⚠ ${esc(FL.fehler[e.meldung] || e.meldung)}</p>` + (e.meldung === "kein_tun" || !d.tun ? kopierFeld(PVE.replace(/^/gm, "") + "\n# /etc/pve/lxc/<ID>.conf, dann: pct reboot <ID>", 4) : "");
        else if (!d.tun) x += `<p class="leise">${esc(FL.fehler.kein_tun)}</p>` + kopierFeld(PVE + "\n# /etc/pve/lxc/<ID>.conf, dann: pct reboot <ID>", 4);
        x += `<div class="zeile"><button class="knopf haupt" id="fnEinrichten">${esc(FL.einrichten)}</button></div><p class="leise">${esc(FL.einrichtenText)}</p>`;
      }
      return x;
    }
    x += `<p class="gut">✓ Tailscale ${esc(e.version || "")}</p><h3>${esc(FL.s2)}</h3>`;
    if (!h.laeuft) {
      const url = link || h.url;
      x += `<div class="zeile"><button class="knopf haupt" id="fnVerbinden">${esc(FL.verbinden)}</button></div><p class="leise">${esc(FL.verbindenText)}</p>`
        + (url ? `<p><a class="knopf" href="${esc(url)}" target="_blank" rel="noopener">${esc(FL.oeffnen)}</a> <span class="leise">${esc(FL.wartet)}</span></p>` : "");
      return x;
    }
    x += `<p class="gut">✓ ${esc(FL.verbunden(h.name, h.ip, h.konto))}</p><h3>${esc(FL.s3)}</h3>`;
    x += d.fernnetz.art === "link" && d.fernnetz.server === h.ip
      ? `<p class="gut">✓ ${esc(FL.an)}</p><div class="zeile"><button class="knopf" id="fnPruefen">${esc(F.pruefen)}</button><button class="knopf" id="fnAus">${esc(FL.aus)}</button></div>`
      : `<div class="zeile"><button class="knopf haupt" id="fnEin">${esc(FL.einschalten)}</button></div>`;
    return x;
  };
  const zeichnen = () => {
    const k = d.fernnetz, art = wahl || (k.art === "aus" ? "link" : k.art);
    inhalt.innerHTML = `<div class="karte"><h2>${esc(F.titel)}</h2><p class="leise">${esc(F.text)}</p>
        <p><a href="https://github.com/thefrozn/signagecast/blob/main/docs/REMOTE.md" target="_blank" rel="noopener">${esc(F.anleitung)}</a></p>
        ${d.userspace ? `<p class="schlecht">⚠ ${esc(F.userspace)}</p>` : ""}
        <div class="zeile"><label for="fnArt">${esc(F.art)}</label><select id="fnArt">${["link", "tailscale", "headscale", "aus"].map((a) =>
          `<option value="${a}" ${a === art ? "selected" : ""}>${esc(F.arten[a])}</option>`).join("")}</select></div>
        ${art === "link" ? linkHtml() : art === "aus" ? `<div class="zeile"><button class="knopf haupt" id="fnSpeichern">${esc(T.speichern)}</button></div>` : `
          <div class="zeile"><label for="fnServer">${esc(F.server)}</label><input type="text" id="fnServer" value="${esc(k.server)}" placeholder="100.64.0.1" inputmode="decimal"></div>
          <p class="leise">${esc(F.serverText)}${d.tailnet_ip && d.tailnet_ip !== k.server ? ` <button class="knopf klein" id="fnVorschlag">${esc(F.vorschlag(d.tailnet_ip))}</button>` : ""}</p>
          <div data-fn="tailscale" ${art === "tailscale" ? "" : "hidden"}>
            <div class="zeile"><label for="fnCid">${esc(F.clientId)}</label><input type="text" id="fnCid" value="${esc(k.client_id)}" autocomplete="off"></div>
            <div class="zeile"><label for="fnCsec">${esc(F.clientSecret)}</label><input type="password" id="fnCsec" value="${esc(k.client_secret)}" autocomplete="new-password"></div>
            <p class="leise">${esc(F.clientText)}</p></div>
          <div data-fn="headscale" ${art === "headscale" ? "" : "hidden"}>
            <div class="zeile"><label for="fnUrl">${esc(F.url)}</label><input type="text" id="fnUrl" value="${esc(k.url)}" placeholder="https://headscale.example.org"></div>
            <div class="zeile"><label for="fnKey">${esc(F.apiKey)}</label><input type="password" id="fnKey" value="${esc(k.api_key)}" autocomplete="new-password"></div>
            <p class="leise"><code>${esc(F.apiText)}</code></p>
            <div class="zeile"><label for="fnBen">${esc(F.benutzer)}</label><input type="text" id="fnBen" value="${esc(k.benutzer)}" inputmode="numeric"></div></div>
          <div class="zeile"><label for="fnTag">${esc(F.tag)}</label><input type="text" id="fnTag" value="${esc(k.tag)}"></div>
          <p class="leise">${esc(F.tagText)}</p>
          <div class="zeile"><button class="knopf haupt" id="fnSpeichern">${esc(T.speichern)}</button>
            ${k.art === art && k.server ? `<button class="knopf" id="fnPruefen">${esc(F.pruefen)}</button>` : ""}</div>`}
        ${pruefung ? `<p class="gut">✓ ${esc(F.geprueft(pruefung.geraete, pruefung.server_name))}</p>` : ""}</div>
      ${art !== "aus" ? `<div class="karte"><h2>${esc(F.regel)}</h2><p class="leise">${esc(F.regelText)}</p>
        ${kopierFeld(JSON.stringify(d.regel, null, 2), 12)}
        ${art !== "headscale" ? `<p><a href="https://login.tailscale.com/admin/acls/file" target="_blank" rel="noopener">${esc(F.editor)}</a></p>` : ""}</div>` : ""}`;
    $("#fnArt").onchange = () => { wahl = $("#fnArt").value; pruefung = null; zeichnen(); };
    inhalt.querySelectorAll("[data-kopieren]").forEach((b) => { b.onclick = async () => {
      const t = b.parentElement.querySelector("textarea"); t.select();
      try { await navigator.clipboard.writeText(t.value); } catch (_) { document.execCommand("copy"); }
      b.textContent = F.kopiert; setTimeout(() => { b.textContent = F.kopieren; }, 2000); }; });
    if ($("#fnVorschlag")) $("#fnVorschlag").onclick = () => { $("#fnServer").value = d.tailnet_ip; };
    if ($("#fnEinrichten")) $("#fnEinrichten").onclick = (e) => aktion(e.target, async () => {
      await senden("/api/updates/anfrage", { aktion: "tailscale" });
      d.einrichtung = { phase: "laeuft" }; zeichnen();
      beobachten((x) => x.hier || (x.einrichtung && x.einrichtung.phase === "fehler"));
    }, null);
    if ($("#fnVerbinden")) $("#fnVerbinden").onclick = (e) => {
      const fenster = window.open("about:blank", "_blank");          // im Klick öffnen – sonst blockiert der Browser
      aktion(e.target, async () => {
        const h = (await senden("/api/fernnetz/anmelden", {})).hier;
        link = h.url || "";
        if (fenster) { if (link) fenster.location = link; else fenster.close(); }
        d.hier = h; zeichnen();
        beobachten((x) => x.hier && x.hier.laeuft);
      }, null).then(() => { if (fenster && !link) try { fenster.close(); } catch (_) { /* egal */ } });
    };
    const speichern = async (daten) => { const r = await senden("/api/fernnetz", daten); d.fernnetz = r.fernnetz; d.regel = r.regel; wahl = null; pruefung = null; zeichnen(); };
    if ($("#fnEin")) $("#fnEin").onclick = (e) => aktion(e.target, () => speichern({ art: "link" }));
    if ($("#fnAus")) $("#fnAus").onclick = (e) => aktion(e.target, () => speichern({ art: "aus" }));
    if ($("#fnSpeichern")) $("#fnSpeichern").onclick = (e) => aktion(e.target, () => speichern(art === "aus" ? { art: "aus" } : {
      art, server: $("#fnServer").value.trim(), tag: $("#fnTag").value.trim(), client_id: $("#fnCid").value.trim(), client_secret: $("#fnCsec").value,
      url: $("#fnUrl").value.trim(), api_key: $("#fnKey").value, benutzer: $("#fnBen").value.trim() }));
    if ($("#fnPruefen")) $("#fnPruefen").onclick = (e) => aktion(e.target, async () => {
      pruefung = (await senden("/api/fernnetz/pruefen", {})).pruefung; zeichnen(); }, null);
  };
  zeichnen();
  if ((d.einrichtung || {}).phase === "laeuft") beobachten((x) => x.hier || (x.einrichtung && x.einrichtung.phase !== "laeuft"));
}

async function kiSeite(inhalt) {
  const K = T.ki;
  let d = await holen("/api/ki"), ergebnis = null;
  const lokal = /^(localhost|127\.|\[?::1)/.test(location.hostname);
  let adresse = (!lokal && location.hostname) || d.eigene_ip || "";
  if (adresse.includes(":") && !adresse.startsWith("[")) adresse = `[${adresse}]`;
  const b64 = (t) => btoa(String.fromCharCode(...new TextEncoder().encode(t)));
  const laden = (e) => herunterladen("/api/ki/datei", { id: e.id }, e.datei, "application/octet-stream");   // seit 0.40.1
  const feld = (wert, zeilen) => `<div class="zeile"><textarea readonly rows="${zeilen || 2}" style="flex:1;font-family:monospace;font-size:12px">${esc(wert)}</textarea>
      <button class="knopf" data-kopieren>${esc(K.kopieren)}</button></div>`;
  const ergebnisHtml = (e) => {
    if (!e) return "";
    let h = `<div class="karte"><h2>✓ ${esc(K.fertig(e.name))}</h2>`;
    if (e.art === "desktop") {
      h += `<ol>${K.desktop.map((s) => `<li>${esc(s)}</li>`).join("")}</ol><p class="leise">🔒 ${esc(K.desktopSicher)}</p>
        <div class="zeile"><button class="knopf" id="kiNochmal">${esc(K.nochmal)}</button></div>`;
    } else {
      const kopf = { Authorization: "Bearer " + e.schluessel };
      if (e.art === "code") {
        h += `<p>${esc(K.befehl)}</p>` + feld(`claude mcp add --transport http signagecast ${e.url} --header "Authorization: Bearer ${e.schluessel}"`, 3);
      } else if (e.art === "cursor") {
        const cfg = { url: e.url, headers: kopf };
        h += `<div class="zeile"><a class="knopf haupt" href="cursor://anysphere.cursor-deeplink/mcp/install?name=signagecast&config=${encodeURIComponent(b64(JSON.stringify(cfg)))}">${esc(K.link)}</a></div>
          <p class="leise">${esc(K.linkText)}</p>` + feld(JSON.stringify({ mcpServers: { signagecast: cfg } }, null, 1), 6);
      } else {
        const cfg = { type: "http", url: e.url, headers: kopf };
        h += `<p>${esc(K.befehl)}</p>` + feld(`code --add-mcp '${JSON.stringify(Object.assign({ name: "signagecast" }, cfg))}'`, 3)
          + `<p class="leise">${esc(K.vscodeWin)}</p>` + feld(JSON.stringify({ servers: { signagecast: cfg } }, null, 1), 6);
      }
      h += `<p class="warn">⚠ ${esc(K.einmal)}</p><p class="leise">${esc(K.unverschluesselt)}</p>`;
    }
    return h + `</div>`;
  };
  const zeichnen = () => {
    const c = d.computer;
    inhalt.innerHTML = `<div class="karte"><h2>${esc(K.titel)}</h2><p class="leise">${esc(K.text)}</p>
        <p><a href="https://github.com/thefrozn/signagecast/blob/main/docs/MCP.md" target="_blank" rel="noopener">${esc(K.anleitung)}</a></p></div>
      ${ergebnisHtml(ergebnis)}
      <div class="karte"><h2>${esc(K.liste)}</h2>
        ${c.length ? `<div class="tabelle-rahmen"><table class="tabelle"><thead><tr><th>${esc(K.name)}</th><th>${esc(K.programm)}</th><th>${esc(K.zuletzt)}</th><th></th></tr></thead><tbody>
          ${c.map((x) => `<tr><td><b>${esc(x.name)}</b><br><span class="leise">${esc(x.erstellt)}</span></td><td>${esc(K.arten[x.art] || x.art)}<br><span class="leise">${esc(K.rechte[x.recht])}</span></td>
            <td>${x.wartet ? `<span class="leise">${esc(K.wartet)}</span>` : x.abgelaufen ? `<span class="schlecht">${esc(K.abgelaufen)}</span>`
              : `${esc(x.zuletzt || K.nie)}${x.ip ? `<br><span class="leise">${esc(x.ip)}</span>` : ""}`}</td>
            <td><button class="knopf gefahr" data-weg="${esc(x.id)}">${esc(K.entfernen)}</button></td></tr>`).join("")}</tbody></table></div>`
          : `<p class="leise">${esc(K.keine)}</p>`}</div>
      <div class="karte"><h2>${esc(K.neu)}</h2>
        <div class="zeile"><label for="kiName">${esc(K.name)}</label><input type="text" id="kiName" maxlength="30" placeholder="${esc(K.namePlatz)}"></div>
        <div class="zeile"><label for="kiArt">${esc(K.programm)}</label><select id="kiArt">
          ${["desktop", "code", "cursor", "vscode"].map((a) => `<option value="${a}" ${a === "desktop" && !d.https ? "disabled" : ""}>${esc(K.arten[a])}</option>`).join("")}</select></div>
        ${d.https ? "" : `<p class="leise">${esc(K.keinHttps)}</p>`}
        <div class="zeile"><label for="kiRecht">${esc(K.recht)}</label><select id="kiRecht">
          ${["aendern", "lesen"].map((r) => `<option value="${r}">${esc(K.rechte[r])}</option>`).join("")}</select></div>
        <div class="zeile"><label for="kiAdresse">${esc(K.adresse)}</label><input type="text" id="kiAdresse" value="${esc(adresse)}"></div>
        <p class="leise">${esc(K.adresseText)}</p>
        <div class="zeile"><button class="knopf haupt" id="kiVerbinden">${esc(K.verbinden)}</button></div></div>`;
    if (!d.https) $("#kiArt").value = "code";
    inhalt.querySelectorAll("[data-kopieren]").forEach((k) => {
      k.onclick = async () => {
        const f = k.parentElement.querySelector("textarea");
        f.select();
        try { await navigator.clipboard.writeText(f.value); } catch (_) { document.execCommand("copy"); }
        k.textContent = K.kopiert;
        setTimeout(() => { k.textContent = K.kopieren; }, 2000);
      };
    });
    if ($("#kiNochmal")) $("#kiNochmal").onclick = () => laden(ergebnis);
    inhalt.querySelectorAll("[data-weg]").forEach((k) => {
      k.onclick = () => {
        const x = d.computer.find((y) => y.id === k.dataset.weg);
        if (!x || !confirm(K.entfernenFrage(x.name))) return;
        aktion(k, async () => {
          d.computer = (await senden("/api/ki/entfernen", { id: x.id })).computer;
          if (ergebnis && ergebnis.id === x.id) ergebnis = null;
          zeichnen();
        }, K.entfernt);
      };
    });
    $("#kiVerbinden").onclick = (e) => aktion(e.target, async () => {
      const name = $("#kiName").value.trim(), art = $("#kiArt").value;
      adresse = $("#kiAdresse").value.trim();
      const r = await senden("/api/ki/neu", { name, art, recht: $("#kiRecht").value, adresse });
      d.computer = r.computer;
      ergebnis = { id: r.id, name: d.computer.find((y) => y.id === r.id).name, art: r.datei ? "desktop" : art, url: r.url, schluessel: r.schluessel, datei: r.datei };
      if (r.datei) laden(ergebnis);
      zeichnen();
      inhalt.scrollIntoView({ behavior: "smooth" });
    }, null);
  };
  zeichnen();
}

async function sicherungSeite(inhalt) {
  // Sicherung als ZIP (seit 0.12): Einstellungen, Streams, Strikes, Bilder, Verlauf. Mit Zugangsdaten und Passwörtern nur
  // AES-256-verschlüsselt mit starkem Passwort. Alte .json-Sicherungen lassen sich weiter einspielen.
  const S = E.sicherung;
  const groesse = (b) => (b > 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB");
  const zeichnen = async () => {
    const d = await holen("/api/sicherungen");
    inhalt.innerHTML = `<div class="karte"><h2>${esc(T.sichNeu)}</h2><p class="leise">${esc(T.sicherungText)}</p>
        <div class="zeile"><label><input type="checkbox" id="mitGeheim"> <b>${esc(T.mitGeheimFrage)}</b></label></div>
        <div id="pwBlock" hidden><p class="leise">${esc(T.pwPflicht)}</p>
          <div class="zeile"><label>${esc(T.pw1)}</label><input type="password" id="pw1" autocomplete="new-password"></div>
          <div class="zeile"><label>${esc(T.pw2)}</label><input type="password" id="pw2" autocomplete="new-password"></div>
          <p class="leise" id="pwStaerke"></p></div>
        <div class="zeile"><button class="knopf haupt" id="erstellen">${esc(T.sichErstellen)}</button></div></div>
      <div class="karte"><h2>${esc(T.sichListe)}</h2>
        ${d.liste.length ? d.liste.map((x) => `<div class="zeile eintrag"><span style="flex:1">${esc(x.zeit)} · ${esc(x.auto ? T.sichAuto : T.sichManuell)} · ${groesse(x.groesse)}
            ${x.verschluesselt ? " · 🔒 AES-256" : ""}${x.geheim ? " · " + esc(T.sichMitGeheim) : ""}</span>
            <button class="knopf" data-laden="${esc(x.name)}">${esc(T.herunterladen)}</button><button class="knopf gefahr" data-weg="${esc(x.name)}">✕</button></div>`).join("")
          : `<p class="leise">${esc(T.sichKeine)}</p>`}
        ${d.auto ? `<p class="leise">${esc(T.sichLetzteAuto)}: ${esc(d.auto.zeit)}${d.auto.fehler ? ` <span class="schlecht">${esc(meldungText(d.auto.fehler_m, d.auto.fehler))}</span>` : ""}</p>` : ""}</div>
      <div class="karte"><h2>${esc(T.sichAutoTitel)}</h2>
        <div class="zeile"><label>${esc(T.sichPlan)}</label><select id="plan">${["aus", "taeglich", "woechentlich"].map((k) => `<option value="${k}" ${k === S.plan ? "selected" : ""}>${esc(T.sichPlanArt[k])}</option>`).join("")}</select>
          <select id="wtag">${T.wochentage.map((w, i) => `<option value="${i}" ${i === S.wochentag ? "selected" : ""}>${esc(w)}</option>`).join("")}</select>
          <input type="time" id="uhr" value="${esc(S.uhrzeit)}"></div>
        <div class="zeile"><label>${esc(T.sichBehalten)}</label><input type="number" id="behalten" min="1" max="60" value="${S.behalten}"></div>
        <div class="zeile"><label><input type="checkbox" id="autoGeheim" ${S.mit_geheimnissen ? "checked" : ""}> ${esc(T.mitGeheimFrage)}</label></div>
        <div id="autoPw" ${S.mit_geheimnissen ? "" : "hidden"}><div class="zeile"><label>${esc(T.pw1)}</label><input type="password" id="apw1" value="${esc(S.passwort)}" autocomplete="new-password"></div>
          <div class="zeile"><label>${esc(T.pw2)}</label><input type="password" id="apw2" value="${esc(S.passwort)}" autocomplete="new-password"></div></div>
        <p class="leise">${esc(T.sichAutoText)}</p>
        <div class="zeile"><button class="knopf haupt" id="autoOk">${esc(T.speichern)}</button></div></div>
      <div class="karte"><h2>${esc(T.sicherungEinspielen)}</h2>
        <div class="zeile"><input type="file" id="datei" accept=".zip,.json,application/zip,application/json"></div>
        <div class="zeile"><label>${esc(T.pwEinspielen)}</label><input type="password" id="pwEin" autocomplete="off"></div>
        <div class="zeile"><label><input type="checkbox" id="mitStrikes"> ${esc(T.mitStrikes)}</label></div>
        <div class="zeile"><button class="knopf" id="ein">${esc(T.sicherungEinspielen)}</button></div></div>`;
    const staerke = () => {
      const p = $("#pw1").value, arten = [/[a-z]/, /[A-Z]/, /\d/, /[^a-zA-Z\d]/].filter((r) => r.test(p)).length;
      const gut = p.length >= 12 && (arten >= 3 || p.length >= 20) && new Set(p).size >= 6;
      $("#pwStaerke").innerHTML = !p ? "" : gut ? `<span class="gut">${esc(T.pwGut)}</span>` : `<span class="schlecht">${esc(T.pwSchwach)}</span>`;
      return gut;
    };
    $("#mitGeheim").onchange = () => { $("#pwBlock").hidden = !$("#mitGeheim").checked; };
    $("#pw1").oninput = staerke;
    $("#autoGeheim").onchange = () => { $("#autoPw").hidden = !$("#autoGeheim").checked; };
    const planSicht = () => { $("#wtag").hidden = $("#plan").value !== "woechentlich"; $("#uhr").hidden = $("#plan").value === "aus"; };
    $("#plan").onchange = planSicht; planSicht();
    const laden = async (name) => herunterladen("/api/sicherung/datei", { name }, `signagecast-${name}`, "application/zip");
    $("#erstellen").onclick = (e) => aktion(e.target, async () => {
      const geheim = $("#mitGeheim").checked;
      let pw = "";
      if (geheim) {
        pw = $("#pw1").value;
        if (pw !== $("#pw2").value) throw new Error(T.pwUngleich);
        if (!staerke()) throw new Error(T.pwSchwach);
      }
      const r = await senden("/api/sicherung/erstellen", { mit_geheimnissen: geheim, passwort: pw });
      await laden(r.name);
      await zeichnen();
    }, T.sichFertig);
    inhalt.querySelectorAll("[data-laden]").forEach((k) => { k.onclick = (e) => aktion(e.target, () => laden(k.dataset.laden), null); });
    inhalt.querySelectorAll("[data-weg]").forEach((k) => {
      k.onclick = (e) => { if (confirm(T.sichWegFrage)) aktion(e.target, async () => { await senden("/api/sicherung/loeschen", { name: k.dataset.weg }); await zeichnen(); }); };
    });
    $("#autoOk").onclick = (e) => aktion(e.target, async () => {
      const geheim = $("#autoGeheim").checked;
      if (geheim && $("#apw1").value !== $("#apw2").value) throw new Error(T.pwUngleich);
      await speichernE({ sicherung: { plan: $("#plan").value, wochentag: Number($("#wtag").value), uhrzeit: $("#uhr").value,
                                      behalten: Number($("#behalten").value) || 7, mit_geheimnissen: geheim, passwort: geheim ? $("#apw1").value : "" } }, null);
    });
    $("#ein").onclick = (e) => aktion(e.target, async () => {
      const f = $("#datei").files[0]; if (!f) throw new Error("–");
      if (!confirm(T.wirklichEinspielen)) return;
      if (/\.json$/i.test(f.name)) {                     // alte Sicherung / Profil
        const d = JSON.parse(await f.text());
        if (!$("#mitStrikes").checked) delete d.strikes;
        await senden("/api/sicherung", d);
      } else {
        const b64 = await new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(r.result); r.readAsDataURL(f); });
        await senden("/api/sicherung/zip", { daten: b64, passwort: $("#pwEin").value, strikes: $("#mitStrikes").checked });
      }
      await einstellungenLaden(); reiterZeichnen(); hinweiseZeichnen();
    }, T.eingespielt);
  };
  await zeichnen();
}

// ---------- Eigene Medien (seit 0.15): hochladen in Stücken, Liste mit Name, Dauer, an/aus ----------
async function medienSeite(inhalt) {
  const STUECK = 3 * 1024 * 1024;               // 3 MB je Stück (als Base64 unter der Grenze des Dienstes)
  const zeichnen = () => {
    inhalt.innerHTML = `<div class="karte"><p class="leise">${esc(T.medText)}</p>
        <div class="zeile"><input type="file" id="medDatei" multiple accept="image/jpeg,image/png,video/mp4,video/webm"><button class="knopf haupt" id="medHoch">${esc(T.medHoch)}</button></div>
        <p class="leise" id="medStand"></p><p class="leise">${esc(T.medSicherung)}</p></div>
      <div class="karte"><div id="medListe">${E.medien.length ? "" : `<p class="leise">${esc(T.medKeine)}</p>`}</div>
        ${E.medien.length ? `<div class="zeile"><button class="knopf haupt" id="medOk">${esc(T.speichern)}</button></div>` : ""}</div>`;
    const liste = $("#medListe");
    E.medien.forEach((m) => {
      const z = el(`<div class="zeile eintrag" data-id="${esc(m.id)}"><span class="medvorschau">${m.art === "bild" ? "🖼" : "🎬"}</span>
        <input type="text" name="name" value="${esc(m.name)}" style="flex:1">
        ${m.art === "bild" ? `<label>${esc(T.medDauer)}</label><input type="number" name="dauer" min="1" max="3600" value="${m.dauer_s}" style="width:80px">`
                           : `<span class="leise">${Math.floor(m.dauer_s / 60)}:${String(Math.round(m.dauer_s % 60)).padStart(2, "0")}</span>`}
        ${schalter("aktiv", m.aktiv)}<button class="knopf gefahr" name="weg">✕</button></div>`);
      if (m.art === "bild") dienstBinaer.get(`/medien/${m.datei}`, {}, {}).then((d) => {
        const b = document.createElement("img"); b.src = URL.createObjectURL(new Blob([d])); b.style.cssText = "height:40px;border-radius:4px";
        z.querySelector(".medvorschau").replaceChildren(b);
      }).catch(() => {});
      z.querySelector("[name=weg]").onclick = (e) => { if (confirm(T.medWeg)) aktion(e.target, async () => { const d = await senden("/api/medien/loeschen", { id: m.id }); E = d.einstellungen; zeichnen(); }); };
      liste.appendChild(z);
    });
    const ok = $("#medOk");
    if (ok) ok.onclick = (e) => speichernE({ medien: E.medien.map((m) => {
      const z = liste.querySelector(`[data-id="${m.id}"]`);
      return { ...m, name: z.querySelector("[name=name]").value, aktiv: z.querySelector("[name=aktiv]").checked,
               dauer_s: m.art === "bild" ? Number(z.querySelector("[name=dauer]").value) || 15 : m.dauer_s };
    }) }, e.target);
    $("#medHoch").onclick = (e) => aktion(e.target, async () => {
      for (const f of $("#medDatei").files) {
        const kennung = Math.random().toString(36).slice(2, 12).replace(/[^a-z0-9]/g, "a").padEnd(10, "x");
        const teile = Math.max(1, Math.ceil(f.size / STUECK));
        let d = null;
        for (let nr = 0; nr < teile; nr++) {
          const roh = new Uint8Array(await f.slice(nr * STUECK, (nr + 1) * STUECK).arrayBuffer());
          let bin = ""; for (let i = 0; i < roh.length; i += 0x8000) bin += String.fromCharCode(...roh.subarray(i, i + 0x8000));
          d = await senden("/api/medien/teil", { kennung, nr, daten: btoa(bin), fertig: nr === teile - 1, name: f.name.replace(/\.[^.]+$/, "") });
          $("#medStand").textContent = T.medLaedt(f.name, Math.round((nr + 1) / teile * 100));
        }
        if (d && d.einstellungen) E = d.einstellungen;
      }
      zeichnen();
    });
  };
  zeichnen();
}

// ---------- Updates (seit 0.13): Anfrage an das root-Skript, Stand aus dessen Statusdateien ----------
async function updatesSeite(inhalt) {
  // Zeit aus dem Zeitstempel in Ortszeit (das root-Skript läuft in der Systemzeit des Containers, oft UTC)
  const wann = (x) => (x && x.ts ? new Date(x.ts * 1000).toLocaleString(E.sprache === "en" ? "en-GB" : "de-DE", { dateStyle: "short", timeStyle: "short" }) : (x && x.zeit) || "");
  const zeichnen = async () => {
    const d = await holen("/api/updates");
    if (!d.moeglich) {
      inhalt.innerHTML = `<div class="karte"><h2>Updates</h2><p>${esc(T.upContainer)}</p>
        <pre>docker pull ghcr.io/thefrozn/signagecast:latest\ndocker compose up -d</pre><p class="leise">Podman: podman auto-update</p></div>`;
      return;
    }
    const p = d.pruefung || {}, pakete = p.pakete || [], sicher = pakete.filter((x) => x.sicherheit).length;
    const neueste = d.neue_version || p.neueste || "";
    const neuer = d.neue_version && d.neue_version !== "v" + d.version;
    const l = d.letzte, laeuft = (l && l.phase === "laeuft") || d.anfrage_offen;
    const U = E.updates;
    inhalt.innerHTML = `<div class="karte"><h2>${esc(T.upSc)}</h2>
        <p>${esc(T.upInstalliert)}: <b>${esc(d.version)}</b> · ${esc(T.upNeueste)}: <b>${esc(neueste || "–")}</b>${neuer ? "" : ` <span class="gut">${esc(T.upAktuell)}</span>`}</p>
        <p class="leise">${esc(T.upScText)}</p>
        <div class="zeile">${neuer ? `<button class="knopf haupt" data-a="signagecast" ${laeuft ? "disabled" : ""}>${esc(T.upJetzt)}</button>` : ""}
          ${d.vorher ? `<button class="knopf" data-a="zurueck" ${laeuft ? "disabled" : ""}>${esc(T.upZurueck(d.vorher))}</button>` : ""}
          <a href="https://github.com/thefrozn/signagecast/releases" target="_blank" rel="noopener">${esc(T.aenderungen)}</a></div></div>
      <div class="karte"><h2>${esc(T.upSystem)}</h2>
        <p>${p.zeit ? `${pakete.length ? esc(T.upAnzahl(pakete.length, sicher)) : esc(T.upKeine)} · ${esc(T.upGeprueft)} ${esc(wann(p))}` : esc(T.upNie)}
          ${p.neustart_noetig ? `<br><span class="warn">${esc(T.upNeustart)}</span>` : ""}</p>
        ${pakete.length ? `<details><summary>${pakete.length}</summary>${pakete.map((x) => `<div class="leise">${x.sicherheit ? "🔒 " : ""}${esc(x.name)} ${esc(x.alt)} → ${esc(x.neu)}</div>`).join("")}</details>` : ""}
        <div class="zeile"><button class="knopf" data-a="pruefen" ${laeuft ? "disabled" : ""}>${esc(T.upPruefen)}</button>
          ${pakete.length ? `<button class="knopf haupt" data-a="system" ${laeuft ? "disabled" : ""}>${esc(T.upAlle)}</button>` : ""}
          ${sicher ? `<button class="knopf" data-a="sicherheit" ${laeuft ? "disabled" : ""}>${esc(T.upNurSicher)}</button>` : ""}</div></div>
      <div class="karte"><h2>${esc(T.upLetzte)}</h2><p>${l ? `<b>${esc(T.upAktion[l.aktion] || l.aktion)}</b> · ${esc(T.upPhase[l.phase] || l.phase)}${E.sprache === "de" || l.phase === "fehler" ? " · " + esc(l.meldung) : ""} · ${esc(wann(l))}` : "–"}</p></div>
      <div class="karte"><h2>${esc(T.upAuto)}</h2>
        <div class="zeile"><label>${esc(T.upAutoSystem)}</label><select id="upSys">${["melden", "sicherheit", "auto"].map((k) => `<option value="${k}" ${k === U.system ? "selected" : ""}>${esc(T.upModus[k])}</option>`).join("")}</select></div>
        <div class="zeile"><label>${esc(T.upAutoSc)}</label><select id="upSc">${["melden", "auto"].map((k) => `<option value="${k}" ${k === U.signagecast ? "selected" : ""}>${esc(T.upModus[k])}</option>`).join("")}</select></div>
        <div class="zeile"><label>${esc(T.upFenster)}</label><input type="time" id="upVon" value="${esc(U.fenster_von)}"> – <input type="time" id="upBis" value="${esc(U.fenster_bis)}"></div>
        <p class="leise">${esc(T.upAutoText)}</p>
        <div class="zeile"><button class="knopf haupt" id="upOk">${esc(T.speichern)}</button></div></div>`;
    inhalt.querySelectorAll("[data-a]").forEach((k) => {
      k.onclick = (e) => {
        if (k.dataset.a === "zurueck" && !confirm(T.upZurueckFrage)) return;
        aktion(e.target, async () => { await senden("/api/updates/anfrage", { aktion: k.dataset.a }); setTimeout(() => zeichnen().catch(() => {}), 1500); }, T.upGestartet);
      };
    });
    $("#upOk").onclick = (e) => speichernE({ updates: { system: $("#upSys").value, signagecast: $("#upSc").value,
                                                        fenster_von: $("#upVon").value, fenster_bis: $("#upBis").value } }, e.target);
    clearInterval(timer);
    timer = setInterval(() => { if (laeuft) zeichnen().catch(() => {}); }, 3000);   // während einer Aktion mitlaufen
  };
  await zeichnen();
}

// ---------- Start ----------
document.addEventListener("DOMContentLoaded", async () => {
  try { await einstellungenLaden(); } catch (e) {
    $("#inhalt").innerHTML = `<div class="karte schlecht">SignageCast-Dienst nicht erreichbar / service not reachable: ${esc(e.message || e)}</div>`;
    return;
  }
  hinweiseZeichnen();
  $("#inhalt").addEventListener("input", aenderungMerken);
  $("#inhalt").addEventListener("change", aenderungMerken);
  let start = location.hash.slice(1);
  try { start = start || localStorage.getItem("signagecast-reiter") || "uebersicht"; } catch (_) { /* egal */ }
  if (E.assistent_fertig === false) { reiterZeichnen(); assistent($("#inhalt")); } else zeigeSeite(start);
  window.addEventListener("hashchange", () => { if (location.hash.slice(1) !== aktiv) zeigeSeite(location.hash.slice(1)); });
});
