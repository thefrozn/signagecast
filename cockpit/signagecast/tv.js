// SignageCast – Verwaltung als Cockpit-Erweiterung. Spricht nur mit dem Datendienst im Container (127.0.0.1:8080).
// Im Docker-/Podman-Betrieb liefert app/verwaltung.py dieselbe Seite mit einem Cockpit-Ersatz aus (CONTAINER = true).
// Ohne Fremd-Bibliotheken; Texte Deutsch/Englisch (Sprache aus den Einstellungen).
"use strict";

const KOPF = { "X-SignageCast": "1", "Content-Type": "application/json" };
const dienst = cockpit.http(8080, { address: "127.0.0.1" });
const dienstBinaer = cockpit.http(8080, { address: "127.0.0.1", binary: true });
const CONTAINER = !!cockpit.signagecastContainer;
const hostSync = () => CONTAINER ? T.hostSync.replace(" (Proxmox)", "") : T.hostSync;   // im Container ist der Host selten Proxmox
const IMAGE = "ghcr.io/thefrozn/signagecast:latest";

// ---------- Texte ----------
const TEXTE = {
  de: {
    reiter: { uebersicht: "Übersicht", fernseher: "Fernseher", layout: "Layout", quellen: "Datenquellen", streams: "Streams", radio: "Radio", einspieler: "Einspieler", anzeige: "Anzeige",
              video: "Regeln", suche: "Suche", verbindung: "Verbindung", medien: "Medien", updates: "Updates", sicherung: "Sicherung",
              allgemein: "Allgemein", ha: "Home Assistant", benachrichtigung: "Benachrichtigungen", zugang: "Zugang" },
    bereiche: { uebersicht: "Übersicht", fernseher: "Fernseher", inhalte: "Inhalte", videoton: "Video & Ton", einstellungen: "Einstellungen", system: "System" },
    fernseherText: "Jeder Fernseher öffnet im Browser seine eigene Adresse und kann eigenen Ton, Sender und eigene Kategorien haben.",
    adresse: "Adresse am Fernseher", ton: "Ton", tonArt: { aus: "aus", radio: "Radio", tiere: "Originalton der Tiervideos" },
    sender: "Sender", keinSender: "– Sender wählen –", lautstaerke: "Lautstärke", videoZeigen: "Live-Videos zeigen",
    kennung: "Kennung (a–z, 0–9, steht in der Adresse)", fernseherNeu: "Fernseher hinzufügen", fernseherWeg: "Fernseher entfernen",
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
    ortSuche: "Ort suchen (z. B. Weiden i.d. OPf.)", ortGesetzt: "Standort gespeichert", zeigenAuf: "„Jetzt zeigen“ auf",
    alleTv: "allen Fernsehern", tonAnzeige: "Ton",
    epText: "Zu festen Minuten unterbricht ein Beitrag die Rotation im Videofenster und läuft ganz durch – z. B. „tagesschau in 100 Sekunden“ zur vollen und halben Stunde. Mit Ton ist das Radio solange stumm.",
    epNeu: "Einspieler hinzufügen", epQuelle: "Quelle", epQuelleArt: { tagesschau100: "tagesschau in 100 Sekunden (immer die aktuelle Ausgabe)", video: "Video-Adresse (MP4)", youtube: "YouTube-Video oder Kanal (neuestes Video)" },
    epUrl: "Adresse / Link", epMinuten: "Minuten der Stunde", epAndere: "andere (z. B. 0,20,40)", epZeit: "nur zwischen", epTon: "mit Ton",
    epFernseher: "Fernseher (keiner gewählt = alle)", epAktiv: "aktiv", epJetzt: "Jetzt zeigen", epJetztOk: "Läuft in bis zu 15 s am Fernseher",
    epStand: "Stand", epFehler: "Fehler", epKeine: "Noch keine Einspieler.",
    wetterQuelle: "Wetterquelle", wetterQuelleArt: { met: "Eigenes Wetter (MET Norway, für den Standort)", ha: "Home Assistant (Wetter-Entität)" },
    metText: "Wetter, Wetterbild und Vorhersage kommen direkt von MET Norway (kostenlos, weltweit) für den Standort im Reiter „Verbindung“ – Home Assistant ist dafür nicht nötig. Am Fernseher steht klein „Wetterdaten: MET Norway“ (Lizenzbedingung).",
    bnTitel: "Benachrichtigungen", bnText: "SignageCast meldet sich bei Ausfall eines Fernsehers, fehlgeschlagenem Update oder Sicherung und wenn Home Assistant länger als 5 Minuten nicht erreichbar ist – jeweils einmal, mit Entwarnung.",
    bnTelegram: "Telegram", bnBotToken: "Bot-Token", bnChatId: "Chat-ID", bnEmail: "E-Mail (SMTP)", bnServer: "SMTP-Server", bnPort: "Port",
    bnSicherheit: "Verschlüsselung", bnBenutzer: "Benutzer", bnPasswort: "Passwort", bnAbsender: "Absender", bnEmpfaenger: "Empfänger (mit Komma trennen)",
    bnHA: "Home Assistant", bnDienst: "Benachrichtigungsdienst", bnAktiv: "aktiv", bnTest: "Testnachricht", bnTestOk: "Testnachricht gesendet",
    bnEreignisse: "Melden bei", bnEr: { ausfall: "Ausfall eines Fernsehers", update: "Update fehlgeschlagen", sicherung: "Sicherung fehlgeschlagen", ha: "Home Assistant getrennt" },
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
    passwortHinweisContainer: "Hinweis: Du meldest dich noch mit dem Startpasswort aus dem Protokoll an – bitte unter „Verbindung“ ein eigenes festlegen.",
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
    nurGefundene: "nur gefundene", nurProbleme: "nur mit Strikes", aktiv: "aktiv", geschuetzt: "geschützt",
    zeigen: "Jetzt zeigen", uebernehmen: "Übernehmen", bearbeiten: "Bearbeiten", entfernen: "Entfernen", ablehnen: "Ablehnen",
    strikesWeg: "Strikes zurücksetzen", tag: "Tag", nacht: "Nacht", ortFehlt: "Ort unbekannt", inRotation: "in Rotation",
    live: "live", nichtLive: "nicht live", gefunden: "gefunden", fest: "fest", proben: "Proben", strikes: "Strikes",
    abgelehnt: "Abgelehnte Streams (werden bei der Suche nie wieder aufgenommen)", freigeben: "Freigeben",
    wirklichEntfernen: "Stream wirklich entfernen?", wirklichAblehnen: "Stream entfernen und nie wieder aufnehmen?",
    zeigenOk: "Läuft gleich am Fernseher (für einen Takt)", anzahl: (n, g) => `${n} Streams, davon ${g} gerade in Rotation`,
    sprache: "Sprache", wetter: "Wetter-Entität", vorhersage: "3-Tage-Vorhersage zeigen", raeume: "Räume (links, bis 4)",
    kacheln: "Kacheln (unten, bis 8)", icon: "Symbol (mdi-…)", zeileNeu: "Zeile hinzufügen", entitaetenFehlen:
      "Liste der Entitäten aus HA nicht verfügbar – Namen bitte von Hand eintragen.", iconsListe: "Symbolnamen: pictogrammers.com/library/mdi",
    videoAktiv: "Live-Videos zeigen", takt: "Minuten je Stream", nurTag: "nur Streams, wo vor Ort Tag ist",
    sonne: "Mindest-Sonnenhöhe (Grad)", mindeststufe: "Mindestqualität", schlecht: "so lange darunter, dann weiter (s)",
    grenze: "Strikes bis ein Stream nicht mehr läuft", sperre: "nach Strike überspringen für (Stunden)",
    kategorien: "Kategorien", streamTechnik: "Videostream", aufloesung: "Ausgabe", bitrate: "Bitrate (Mbit/s)",
    abschalten: "Abschalten ohne Zuschauer nach (s)", technikHinweis: "Ausgabe und Bitrate wirken beim nächsten Start des Streams.",
    sucheAktiv: "täglich nach neuen Streams suchen", uhrzeit: "Uhrzeit", max: "höchstens gefundene Streams",
    behalten: "Tage behalten, wenn nicht mehr gefunden", begriffe: "Suchbegriffe (je Zeile einer)",
    tierwoerter: "Titel muss eines dieser Wörter enthalten (je Zeile eines, reguläre Ausdrücke erlaubt)",
    ausschluss: "Titel darf keines dieser Wörter enthalten", orte: "Ortserkennung aus dem Titel: Muster ; Breite ; Länge (je Zeile)",
    jetztSuchen: "Jetzt suchen", sucheLaeuft: "Suche läuft (bis ca. 1 min) …", sucheErgebnis: (n, g) => `${g} Live-Streams gefunden, ${n} neu`,
    haUrl: "Adresse von Home Assistant", testen: "Verbindung testen", standort: "Standort (für Wetter-Bezug und Anzeige)",
    standortAusHA: "Aus HA übernehmen", testOk: (v) => `Verbunden – Home Assistant ${v}`, anleitung: "Einrichtung in Home Assistant",
    anleitungText: (ip) => [
      "SignageCast meldet sich ohne Passwort bei Home Assistant an – über „vertrauenswürdige Netzwerke“. HA erkennt den Container an seiner IP-Adresse.",
      "1. In HA unter Einstellungen → Personen einen Benutzer anlegen, z. B. „Fernseher“ (kein Administrator, „Nur lokal anmelden“ an).",
      "2. Den Benutzer öffnen – die lange Kennung am Ende der Adresszeile ist die Benutzer-ID.",
      `3. In der Datei configuration.yaml (z. B. mit dem File-Editor-Add-on) diesen Abschnitt ergänzen, BENUTZER-ID ersetzen. Die IP dieses Containers ist ${ip || "?"}:`,
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
           wald: "Wald & Wildtiere", zoo: "Zoo & Exoten", neu: "Neu gefunden" },
    aufgabe: { streamliste: "Streamliste prüfen", suche: "Neue Streams suchen", wache: "Qualität messen" },
  },
  en: {
    reiter: { uebersicht: "Overview", fernseher: "TVs", layout: "Layout", quellen: "Data sources", streams: "Streams", radio: "Radio", einspieler: "Clips", anzeige: "Display",
              video: "Rules", suche: "Search", verbindung: "Connection", medien: "Media", updates: "Updates", sicherung: "Backup",
              allgemein: "General", ha: "Home Assistant", benachrichtigung: "Notifications", zugang: "Access" },
    bereiche: { uebersicht: "Overview", fernseher: "TVs", inhalte: "Content", videoton: "Video & sound", einstellungen: "Settings", system: "System" },
    fernseherText: "Each TV opens its own address in the browser and can have its own sound, station and categories.",
    adresse: "Address on the TV", ton: "Sound", tonArt: { aus: "off", radio: "Radio", tiere: "Original sound of the animal videos" },
    sender: "Station", keinSender: "– choose station –", lautstaerke: "Volume", videoZeigen: "Show live videos",
    kennung: "Identifier (a–z, 0–9, part of the address)", fernseherNeu: "Add TV", fernseherWeg: "Remove TV",
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
    metText: "Weather, weather picture and forecast come directly from MET Norway (free, worldwide) for the location in the “Connection” tab – Home Assistant is not needed for this. The TV shows a small “Weather data: MET Norway” (licence requirement).",
    bnTitel: "Notifications", bnText: "SignageCast reports when a TV fails, an update or backup fails, and when Home Assistant is unreachable for more than 5 minutes – once each, with an all-clear.",
    bnTelegram: "Telegram", bnBotToken: "Bot token", bnChatId: "Chat ID", bnEmail: "E-mail (SMTP)", bnServer: "SMTP server", bnPort: "Port",
    bnSicherheit: "Encryption", bnBenutzer: "User", bnPasswort: "Password", bnAbsender: "Sender", bnEmpfaenger: "Recipients (comma separated)",
    bnHA: "Home Assistant", bnDienst: "Notify service", bnAktiv: "active", bnTest: "Test message", bnTestOk: "Test message sent",
    bnEreignisse: "Notify on", bnEr: { ausfall: "TV failure", update: "Update failed", sicherung: "Backup failed", ha: "Home Assistant disconnected" },
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
      sich_geheim_ohne_pw: "With credentials and passwords only with a password (AES-256)", sich_name: "Unknown backup",
      med_art: "Only pictures (JPG, PNG) and videos (MP4, WebM)", med_kaputt: "Video not readable",
      med_hevc: "The video is H.265 – the browser in the container cannot play it; please save it as H.264 (MP4)",
      med_upload: "Upload interrupted – please try again", med_gross: "File larger than 1 GB", med_unbekannt: "Unknown medium",
      upd_laeuft: "An update is already running – please wait", upd_aktion: "Unknown update action",
      upd_container: "With Docker/Podman update via the image (docker pull)",
    },
    haFehler: { nicht_erreichbar: "HA not reachable", kein_trusted: "HA offers no login via trusted networks for this address (trusted_networks missing or IP not listed)",
                kein_benutzer: "trusted_networks: no user assigned to this IP", abgelehnt: "Login rejected", http: "HA answered with an error" }, ha: "Home Assistant", verbunden: "connected", getrennt: "not connected",
    rotation: "In rotation", liste: "Stream list", zuletzt: "last", pause: "YouTube pause until", suche: "Stream search",
    vorschau: "Picture on the TV", vorschauNeu: "Refresh picture", keineVorschau: "No picture – the stream is not running.",
    seiteNeu: "Reload TV page", ketteNeu: "Restart stream", listeNeu: "Rebuild list", erledigt: "Done",
    neueVersion: (v) => `New version ${v} available`, updateText: "To update, run this command as root inside the container (settings and data are kept).",
    updateTextContainer: "To update, pull the new image and recreate the container (settings and data in the volume are kept):",
    systemSeitenContainer: "Logs: docker logs signagecast (or podman logs). Restart and update via Docker/Podman.",
    passwortHinweisContainer: "Note: you are still using the initial password from the log – please set your own under “Connection”.",
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
    nurGefundene: "found only", nurProbleme: "with strikes only", aktiv: "active", geschuetzt: "protected",
    zeigen: "Show now", uebernehmen: "Keep", bearbeiten: "Edit", entfernen: "Remove", ablehnen: "Reject",
    strikesWeg: "Reset strikes", tag: "day", nacht: "night", ortFehlt: "location unknown", inRotation: "in rotation",
    live: "live", nichtLive: "not live", gefunden: "found", fest: "fixed", proben: "samples", strikes: "Strikes",
    abgelehnt: "Rejected streams (never added again by the search)", freigeben: "Allow again",
    wirklichEntfernen: "Really remove this stream?", wirklichAblehnen: "Remove this stream and never add it again?",
    zeigenOk: "Coming up on the TV (for one slot)", anzahl: (n, g) => `${n} streams, ${g} currently in rotation`,
    sprache: "Language", wetter: "Weather entity", vorhersage: "Show 3-day forecast", raeume: "Rooms (left, up to 4)",
    kacheln: "Tiles (bottom, up to 8)", icon: "Icon (mdi-…)", zeileNeu: "Add row", entitaetenFehlen:
      "Entity list from HA not available – please type the names.", iconsListe: "Icon names: pictogrammers.com/library/mdi",
    videoAktiv: "Show live videos", takt: "Minutes per stream", nurTag: "only streams where it is daytime",
    sonne: "Minimum sun elevation (degrees)", mindeststufe: "Minimum quality", schlecht: "below it for this long, then skip (s)",
    grenze: "Strikes until a stream stops playing", sperre: "after a strike skip for (hours)",
    kategorien: "Categories", streamTechnik: "Video stream", aufloesung: "Output", bitrate: "Bitrate (Mbit/s)",
    abschalten: "Switch off without viewers after (s)", technikHinweis: "Output and bitrate apply at the next stream start.",
    sucheAktiv: "search for new streams daily", uhrzeit: "Time", max: "maximum found streams",
    behalten: "days to keep when no longer found", begriffe: "Search terms (one per line)",
    tierwoerter: "Title must contain one of these words (one per line, regular expressions allowed)",
    ausschluss: "Title must not contain any of these words", orte: "Location from title: pattern ; latitude ; longitude (one per line)",
    jetztSuchen: "Search now", sucheLaeuft: "Searching (up to about 1 min) …", sucheErgebnis: (n, g) => `${g} live streams found, ${n} new`,
    haUrl: "Home Assistant address", testen: "Test connection", standort: "Location",
    standortAusHA: "Take from HA", testOk: (v) => `Connected – Home Assistant ${v}`, anleitung: "Setup in Home Assistant",
    anleitungText: (ip) => [
      "SignageCast logs in to Home Assistant without a password – via “trusted networks”. HA recognises the container by its IP address.",
      "1. In HA under Settings → People create a user, e.g. “TV” (no administrator, “Can only log in from the local network” on).",
      "2. Open the user – the long identifier at the end of the address bar is the user ID.",
      `3. Add this section to configuration.yaml (e.g. with the File editor add-on) and replace USER-ID. The IP of this container is ${ip || "?"}:`,
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
           wald: "Forest & wildlife", zoo: "Zoo & exotic", neu: "Newly found" },
    aufgabe: { streamliste: "Check stream list", suche: "Search new streams", wache: "Measure quality" },
  },
};
let T = TEXTE[(cockpit.language || "de").startsWith("de") ? "de" : "en"];

// ---------- Hilfsfunktionen ----------
const $ = (sel, wurzel = document) => wurzel.querySelector(sel);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function el(html) { const t = document.createElement("template"); t.innerHTML = html.trim(); return t.content.firstElementChild; }

async function holen(pfad) {
  const t = await dienst.get(pfad, {}, KOPF);
  return JSON.parse(t);
}
// Meldung des Dienstes in der Sprache der Verwaltung (Kennung + Werte), sonst der Text des Dienstes
function meldungText(m, rueckfall) {
  const vorlage = m && m.code && T.meldung && T.meldung[m.code];
  return vorlage ? vorlage.replace(/\{(\w+)\}/g, (_, k) => ((m.p || {})[k] ?? "")) : (rueckfall || (m && m.text) || "");
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
  try { const r = await fn(); if (okText !== null) melden(okText || T.gespeichert); return r; }
  catch (e) { melden(e.message || String(e), true); }
  finally { if (knopf) knopf.disabled = false; }
}
const schalter = (name, an) => `<label class="schalter"><input type="checkbox" name="${esc(name)}" ${an ? "checked" : ""}><span></span></label>`;
const dauer = (s) => { const t = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60); return (t ? t + " d " : "") + h + " h " + m + " min"; };
const uhrzeit = (ts) => ts ? new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "–";

let E = null, KATEGORIEN = [], STUFEN = [], ENTITAETEN = null, BAUSTEINE = {}, SCHRIFTEN = ["Roboto"];

// ---------- Reiter ----------
const SEITEN = { uebersicht, fernseher: fernseherSeite, layout: layoutSeite, quellen: quellenSeite, medien: medienSeite, einspieler: einspielerSeite,
                 streams: streamsSeite, video, suche: sucheSeite, radio: radioSeite,
                 allgemein: allgemeinSeite, ha: (i) => verbindung(i, "ha"), benachrichtigung: (i) => verbindung(i, "benachrichtigung"),
                 updates: updatesSeite, sicherung: sicherungSeite, zugang: (i) => verbindung(i, "zugang") };
// Bereiche (seit 0.17) – je Bereich seine Unterseiten; Adresse je Seite als #<seite>
const BEREICHE = [["uebersicht", ["uebersicht"]], ["fernseher", ["fernseher"]], ["inhalte", ["layout", "quellen", "medien", "einspieler"]],
                  ["videoton", ["streams", "video", "suche", "radio"]], ["einstellungen", ["allgemein", "ha", "benachrichtigung"]],
                  ["system", CONTAINER ? ["updates", "sicherung", "zugang"] : ["updates", "sicherung"]]];
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
  E = d.einstellungen; KATEGORIEN = d.kategorien; STUFEN = d.stufen;
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
async function uebersicht(inhalt) {
  inhalt.innerHTML = `
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
        <div class="leise">${t.aktuell ? esc(t.aktuell.name) : ""}${w ? ` · <b class="${/hd/.test(w.stufe) ? "gut" : "schlecht"}">${esc(w.stufe)}</b> ${esc((w.codec || "").split(".")[0])}${w.kbps ? " · " + Math.round(w.kbps / 1000) + " Mbit/s" : ""}` : ""}</div>
        <div class="leise">${esc(T.tonAnzeige)}: ${esc(T.tonArt[t.ton])}${t.sender ? " · ♪ " + esc(t.sender) : ""}${t.video ? "" : " · " + esc(T.videoZeigen) + ": " + esc(T.nein)}</div></div>`;
    }).join("");
    const k = [
      [T.zuschauer, String(s.stream.zuschauer), ""],
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
    img.src = url; img.style.display = ""; txt.textContent = new Date().toLocaleTimeString();
  } catch (_) { img.style.display = "none"; txt.textContent = T.keineVorschau; }
}

// ---------- Streams ----------
let filter = { text: "", kat: "", gefunden: false, probleme: false };
async function streamsSeite(inhalt) {
  inhalt.innerHTML = `
    <div class="karte"><h2>${esc(T.hinzufuegen)}</h2>
      <div class="zeile"><input type="url" id="nLink" placeholder="https://www.youtube.com/watch?v=…" aria-label="${esc(T.link)}"></div>
      <div class="zeile"><input type="text" id="nName" placeholder="${esc(T.name)}">
        <select id="nKat">${KATEGORIEN.map((k) => `<option value="${k}">${esc(T.kat[k] || k)}</option>`).join("")}</select></div>
      <div class="zeile"><input type="number" step="0.01" id="nBreite" placeholder="${esc(T.breite)}">
        <input type="number" step="0.01" id="nLaenge" placeholder="${esc(T.laenge)}"><span class="leise">${esc(T.ortAuto)}</span></div>
      <div class="zeile"><button class="knopf haupt" id="nOk">${esc(T.hinzufuegen)}</button></div></div>
    <div class="karte">
      <div class="zeile"><input type="text" id="fText" placeholder="${esc(T.filter)}" value="${esc(filter.text)}">
        <select id="fKat"><option value="">${esc(T.alle)}</option>${KATEGORIEN.map((k) => `<option value="${k}" ${filter.kat === k ? "selected" : ""}>${esc(T.kat[k] || k)}</option>`).join("")}</select>
        <label><input type="checkbox" id="fGef" ${filter.gefunden ? "checked" : ""}> ${esc(T.nurGefundene)}</label>
        <label><input type="checkbox" id="fProb" ${filter.probleme ? "checked" : ""}> ${esc(T.nurProbleme)}</label></div>
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
  for (const [id, feld, art] of [["#fText", "text", "input"], ["#fKat", "kat", "change"], ["#fGef", "gefunden", "change"], ["#fProb", "probleme", "change"]])
    $(id).addEventListener(art, (e) => { filter[feld] = e.target.type === "checkbox" ? e.target.checked : e.target.value; listeZeichnen(); });
  await streamsLaden();
}
let STREAMS = null;
async function streamsLaden() { STREAMS = await holen("/api/streams"); listeZeichnen(); }
function listeZeichnen() {
  const liste = $("#liste"); if (!liste || !STREAMS) return;
  const t = filter.text.toLowerCase();
  const gezeigt = STREAMS.streams.filter((s) => (!t || (s.name + " " + (s.titel || "") + " " + s.id).toLowerCase().includes(t))
    && (!filter.kat || s.kategorie === filter.kat) && (!filter.gefunden || s.herkunft === "entdeckt") && (!filter.probleme || s.strikes > 0));
  $("#zahl").textContent = T.anzahl(STREAMS.streams.length, STREAMS.streams.filter((s) => s.in_rotation).length);
  liste.innerHTML = "";
  for (const s of gezeigt) liste.appendChild(streamKarte(s));
  $("#abgelehnt").innerHTML = STREAMS.abgelehnt.length ? "" : "–";
  for (const a of STREAMS.abgelehnt) {
    const z = el(`<div class="zeile"><code>${esc(a)}</code><button class="knopf">${esc(T.freigeben)}</button></div>`);
    z.querySelector("button").onclick = (e) => aktion(e.target, async () => { await senden(`/api/abgelehnt/${encodeURIComponent(a)}/freigeben`); await streamsLaden(); });
    $("#abgelehnt").appendChild(z);
  }
}
function streamKarte(s) {
  const q = s.qualitaet || {};
  const anteil = q.anteil_720p_plus != null ? Math.round(q.anteil_720p_plus * 100) : null;
  const marken = [
    `<span class="marke">${esc(T.kat[s.kategorie] || s.kategorie)}</span>`,
    `<span class="marke">${esc(s.herkunft === "entdeckt" ? T.gefunden : T.fest)}</span>`,
    s.tag == null ? `<span class="marke warn">${esc(T.ortFehlt)}</span>` : `<span class="marke">${esc(s.tag ? T.tag : T.nacht)}</span>`,
    s.live == null ? "" : `<span class="marke ${s.live ? "gut" : ""}">${esc(s.live ? T.live : T.nichtLive)}</span>`,
    s.in_rotation ? `<span class="marke gut">${esc(T.inRotation)}</span>` : "",
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
            <select name="kategorie">${KATEGORIEN.map((x) => `<option value="${x}" ${x === s.kategorie ? "selected" : ""}>${esc(T.kat[x] || x)}</option>`).join("")}</select></div>
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

// ---------- Anzeige ----------
async function anzeige(inhalt) {
  const ents = await entitaeten();
  inhalt.innerHTML = `<datalist id="ents">${ents.filter((x) => x.id.startsWith("weather.")).map((x) => `<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("")}</datalist>
    <div class="karte">
      <div class="zeile"><label>${esc(T.sprache)}</label><select id="sprache"><option value="de">Deutsch</option><option value="en">English</option></select></div>
      <div class="zeile"><label>${esc(T.wetterQuelle)}</label><select id="wetterQ" class="breit">${Object.keys(T.wetterQuelleArt).map((k) =>
        `<option value="${k}" ${k === E.anzeige.wetter_quelle ? "selected" : ""}>${esc(T.wetterQuelleArt[k])}</option>`).join("")}</select></div>
      <p class="leise" id="metText">${esc(T.metText)}</p>
      <div class="zeile" id="haZeile"><label>${esc(T.wetter)}</label><input type="text" id="wetter" list="ents" value="${esc(E.anzeige.wetter)}"></div>
      <p class="leise">${esc(T.wetterText)}</p></div>
    <div class="zeile"><button class="knopf haupt" id="okAnz">${esc(T.speichern)}</button></div>`;
  $("#sprache").value = E.sprache || "de";
  const sicht = () => { const ha = $("#wetterQ").value === "ha"; $("#haZeile").style.display = ha ? "" : "none"; $("#metText").style.display = ha ? "none" : ""; };
  $("#wetterQ").onchange = sicht; sicht();
  $("#okAnz").onclick = async (e) => {
    await speichernE({ sprache: $("#sprache").value, anzeige: { wetter_quelle: $("#wetterQ").value, wetter: $("#wetter").value } }, e.target);
    T = TEXTE[E.sprache] || TEXTE.de; reiterZeichnen(); hinweiseZeichnen();
  };
}

// ---------- Video & Regeln ----------
async function video(inhalt) {
  const v = E.video, s = E.stream;
  const zahlFeld = (id, w, min, max, step) => `<input type="number" id="${id}" value="${w}" min="${min}" max="${max}" step="${step || 1}">`;
  inhalt.innerHTML = `<div class="karte">
      <div class="zeile"><label>${esc(T.videoAktiv)}</label>${schalter("aktiv", v.aktiv)}</div>
      <div class="zeile"><label>${esc(T.takt)}</label>${zahlFeld("takt", v.takt_min, 1, 30)}</div>
      <div class="zeile"><label>${esc(T.nurTag)}</label>${schalter("nurTag", v.nur_tag)}</div>
      <div class="zeile"><label>${esc(T.sonne)}</label>${zahlFeld("sonne", v.min_sonnenhoehe, -18, 30, 0.5)}</div>
      <div class="zeile"><label>${esc(T.mindeststufe)}</label><select id="stufe">${STUFEN.map((x) => `<option ${x === v.mindeststufe ? "selected" : ""}>${x}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(T.schlecht)}</label>${zahlFeld("schlecht", v.schlecht_s, 5, 170)}</div>
      <div class="zeile"><label>${esc(T.grenze)}</label>${zahlFeld("grenze", v.strike_grenze, 1, 20)}</div>
      <div class="zeile"><label>${esc(T.sperre)}</label>${zahlFeld("sperre", v.sperre_h, 0, 72, 0.5)}</div>
      <h3>${esc(T.kategorien)}</h3>
      ${KATEGORIEN.map((k) => `<div class="zeile"><label>${esc(T.kat[k] || k)}</label>${schalter("kat_" + k, !v.kategorien_aus.includes(k))}</div>`).join("")}</div>
    <div class="karte"><h2>${esc(T.streamTechnik)}</h2>
      <div class="zeile"><label>${esc(T.abschalten)}</label>${zahlFeld("abschalten", s.abschalten_s, 10, 3600)}</div></div>
    <div class="zeile"><button class="knopf haupt" id="ok">${esc(T.speichern)}</button></div>`;
  const n = (id) => Number($("#" + id).value);
  $("#ok").onclick = (e) => speichernE({
    video: { aktiv: $("[name=aktiv]").checked, takt_min: n("takt"), nur_tag: $("[name=nurTag]").checked, min_sonnenhoehe: n("sonne"),
             mindeststufe: $("#stufe").value, schlecht_s: n("schlecht"), strike_grenze: n("grenze"), sperre_h: n("sperre"),
             kategorien_aus: KATEGORIEN.filter((k) => !$(`[name=kat_${k}]`).checked) },
    stream: { abschalten_s: n("abschalten") },
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
async function verbindung(inhalt, teil = "ha") {
  const info = await holen("/api/ha/einrichtung");
  if (CONTAINER && !info.eigene_ip) info.eigene_ip = location.hostname;   // Docker: HA sieht die IP des Hosts
  const yaml = `homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - ${info.eigene_ip || "IP-DES-CONTAINERS"}/32
      trusted_users:
        ${info.eigene_ip || "IP-DES-CONTAINERS"}/32: ${E.sprache === "en" ? "USER-ID" : "BENUTZER-ID"}
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
      <div class="zeile"><label>${esc(T.bnSicherheit)}</label><select id="bnEmSich">${["starttls", "ssl", "keine"].map((v) =>
        `<option value="${v}" ${B.email.sicherheit === v ? "selected" : ""}>${v === "keine" ? "–" : v.toUpperCase()}</option>`).join("")}</select></div>
      <div class="zeile"><label>${esc(T.bnBenutzer)}</label><input type="text" id="bnEmBenutzer" value="${esc(B.email.benutzer)}" autocomplete="off"></div>
      <div class="zeile"><label>${esc(T.bnPasswort)}</label><input type="password" id="bnEmPw" value="${esc(B.email.passwort)}" autocomplete="new-password"></div>
      <div class="zeile"><label>${esc(T.bnAbsender)}</label><input type="text" id="bnEmVon" value="${esc(B.email.absender)}"></div>
      <div class="zeile"><label>${esc(T.bnEmpfaenger)}</label><input type="text" id="bnEmAn" value="${esc(B.email.empfaenger)}"></div>
      <div class="zeile"><button class="knopf" data-test="email">${esc(T.bnTest)}</button></div>
      <h3>${esc(T.bnHA)}</h3>
      <div class="zeile"><label><input type="checkbox" id="bnHaAktiv" ${B.ha.aktiv ? "checked" : ""}> ${esc(T.bnAktiv)}</label></div>
      <div class="zeile"><label>${esc(T.bnDienst)}</label><input type="text" id="bnHaDienst" value="${esc(B.ha.dienst)}" placeholder="notify.notify"></div>
      <div class="zeile"><button class="knopf" data-test="ha">${esc(T.bnTest)}</button></div>
      <h3>${esc(T.bnEreignisse)}</h3>
      ${Object.keys(T.bnEr).map((k) => `<div class="zeile"><label><input type="checkbox" data-er="${k}" ${B.ereignisse[k] ? "checked" : ""}> ${esc(T.bnEr[k])}</label></div>`).join("")}
      <div class="zeile"><button class="knopf haupt" id="bnOk">${esc(T.speichern)}</button></div><div id="bnLetzte" class="leise"></div></div>
    <div class="karte" data-teil="benachrichtigung"><h2>${esc(T.whTitel)}</h2><p class="leise">${esc(T.whText)}</p>
      <div class="zeile"><label><input type="checkbox" id="whAktiv" ${E.webhook.aktiv ? "checked" : ""}> ${esc(T.whAktiv)}</label>
        <span class="leise" id="whStand">${esc(E.webhook.token ? T.whVorhanden : T.whKeiner)}</span></div>
      <div class="zeile"><button class="knopf" id="whNeu">${esc(T.whNeu)}</button></div><div id="whErg"></div></div>
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
async function fernseherSeite(inhalt) {
  const st = await holen("/api/ha/einrichtung");
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
        <div class="zeile"><label>${esc(T.layoutWahl)}</label><select name="layout">${E.layouts.map((l) => `<option value="${esc(l.id)}" ${l.id === t.layout ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select></div>
        <details ${(t.zeitplan || []).length ? "open" : ""}><summary>${esc(T.zeitplan)} (${(t.zeitplan || []).length})</summary>
          <p class="leise">${esc(T.zeitplanText)}</p><div name="zeiten">${(t.zeitplan || []).map((z) => zeitZeile(z)).join("")}</div>
          <button class="knopf" name="zeitPlus">${esc(T.zeitNeu)}</button></details>
        <details ${(t.karussell || {}).aktiv ? "open" : ""}><summary>${esc(T.karussell)}${(t.karussell || {}).aktiv ? " ✓" : ""}</summary>
          <p class="leise">${esc(T.karussellText)}</p>
          <div class="zeile"><label>${esc(T.karussellAn)}</label>${schalter("k_aktiv", (t.karussell || {}).aktiv)}
            <label>${esc(T.karussellMin)}</label><input type="number" name="k_min" min="1" max="1440" value="${(t.karussell || {}).minuten || 5}" style="width:80px"></div>
          ${E.layouts.map((l) => `<label style="margin-right:12px"><input type="checkbox" name="k_l" value="${esc(l.id)}" ${((t.karussell || {}).layouts || []).includes(l.id) ? "checked" : ""}> ${esc(l.name)}</label>`).join("")}</details>
        <div class="zeile"><label>${esc(T.videoZeigen)}</label>${schalter("video", t.video)}</div>
        <div class="zeile"><label>${esc(T.videoQuelle)}</label><select name="video_quelle">${Object.keys(T.videoQuelleArt).map((x) => `<option value="${x}" ${x === (t.video_quelle || "youtube") ? "selected" : ""}>${esc(T.videoQuelleArt[x])}</option>`).join("")}</select>
          <span name="alleTeil"><label>${esc(T.medienAlle)}</label><input type="number" name="medien_alle" min="1" max="20" value="${t.medien_alle || 3}" style="width:70px"></span></div>
        <div class="zeile"><label>${esc(T.ton)}</label><select name="ton">${Object.keys(T.tonArt).map((x) => `<option value="${x}" ${x === t.ton ? "selected" : ""}>${esc(T.tonArt[x])}</option>`).join("")}</select></div>
        <div class="zeile" name="senderZeile"><label>${esc(T.sender)}</label><select name="radio_sender" class="breit"><option value="">${esc(T.keinSender)}</option>
          ${E.radio.sender.map((x) => `<option value="${esc(x.id)}" ${x.id === t.radio_sender ? "selected" : ""}>${esc(x.name)}</option>`).join("")}</select></div>
        <div class="zeile"><label>${esc(T.lautstaerke)}</label><input type="range" name="lautstaerke" min="0" max="100" value="${t.lautstaerke}"><span class="leise" name="lw">${t.lautstaerke} %</span></div>
        <details><summary>${esc(T.kategorien)} (${KATEGORIEN.length - t.kategorien_aus.length}/${KATEGORIEN.length})</summary>
        ${KATEGORIEN.map((x) => `<div class="zeile"><label>${esc(T.kat[x] || x)}</label>${schalter("kat_" + x, !t.kategorien_aus.includes(x))}</div>`).join("")}</details>
        <details><summary>${esc(T.streamTechnik)}: ${t.aufloesung === 2160 ? "4K" : "Full HD"}, ${t.bitrate_mbit} Mbit/s</summary>
        <div class="zeile"><label>${esc(T.aufloesung)}</label><select name="aufloesung"><option value="2160" ${t.aufloesung === 2160 ? "selected" : ""}>4K (3840×2160)</option>
          <option value="1080" ${t.aufloesung === 1080 ? "selected" : ""}>Full HD (1920×1080)</option></select></div>
        <div class="zeile"><label>${esc(T.bitrate)}</label><input type="number" name="bitrate_mbit" min="2" max="40" value="${t.bitrate_mbit}"></div></details>
        ${E.fernseher.length > 1 ? `<div class="zeile"><button class="knopf gefahr" name="weg">${esc(T.fernseherWeg)}</button></div>` : ""}</div>`);
      const zeitenAnbinden = () => k.querySelectorAll("[name=zweg]").forEach((b) => { b.onclick = () => b.closest(".zeile").remove(); });
      zeitenAnbinden();
      k.querySelector("[name=zeitPlus]").onclick = () => { k.querySelector("[name=zeiten]").insertAdjacentHTML("beforeend", zeitZeile({ von: "23:00", bis: "06:00", layout: "schwarz" })); zeitenAnbinden(); };
      const senderSichtbar = () => { k.querySelector("[name=senderZeile]").style.display = k.querySelector("[name=ton]").value === "radio" ? "" : "none"; };
      k.querySelector("[name=ton]").onchange = senderSichtbar; senderSichtbar();
      const alleSichtbar = () => { k.querySelector("[name=alleTeil]").style.display = k.querySelector("[name=video_quelle]").value === "gemischt" ? "" : "none"; };
      k.querySelector("[name=video_quelle]").onchange = alleSichtbar; alleSichtbar();
      k.querySelector("[name=lautstaerke]").oninput = (e) => { k.querySelector("[name=lw]").textContent = e.target.value + " %"; };
      const weg = k.querySelector("[name=weg]");
      if (weg) weg.onclick = () => { if (confirm(T.wirklichTvWeg)) { E.fernseher = lesen().filter((_, j) => j !== i); zeichnen(); } };
      liste.appendChild(k);
    });
    const lesen = () => [...liste.children].map((k) => {
      const t = E.fernseher[Number(k.dataset.i)];
      const w = (n) => k.querySelector(`[name=${n}]`);
      return { ...t, name: w("name").value, id: w("id").value.trim().toLowerCase(), video: w("video").checked, ton: w("ton").value,
               radio_sender: w("radio_sender").value, lautstaerke: Number(w("lautstaerke").value),
               kategorien_aus: KATEGORIEN.filter((x) => !w("kat_" + x).checked), aufloesung: Number(w("aufloesung").value),
               bitrate_mbit: Number(w("bitrate_mbit").value), layout: w("layout").value,
               video_quelle: w("video_quelle").value, medien_alle: Number(w("medien_alle").value) || 3,
               karussell: { aktiv: w("k_aktiv").checked, minuten: Number(w("k_min").value) || 5,
                            layouts: [...k.querySelectorAll("[name=k_l]:checked")].map((c) => c.value) },
               zeitplan: [...k.querySelectorAll("[name=zeiten] .zeile")].map((z) => ({ von: z.querySelector("[name=zvon]").value,
                 bis: z.querySelector("[name=zbis]").value, layout: z.querySelector("[name=zlayout]").value })) };
    });
    $("#tvPlus").onclick = () => {
      const alt = lesen();
      let n = 2; while (alt.some((t) => t.id === "tv" + n)) n++;
      E.fernseher = [...alt, { id: "tv" + n, name: T.weitererTv + " " + n, video: true, ton: "aus", radio_sender: "", lautstaerke: 70,
                                kategorien_aus: [], aufloesung: 2160, bitrate_mbit: 16 }];
      zeichnen();
    };
    $("#ok").onclick = async (e) => { await speichernE({ fernseher: lesen() }, e.target); zeichnen(); };
  };
  zeichnen();
}

// ---------- Radio ----------
async function radioSeite(inhalt) {
  inhalt.innerHTML = `<div class="karte"><h2>${esc(T.meineSender)}</h2><p class="leise">${esc(T.senderNutzung)}</p><div id="meine"></div>
      <div class="zeile"><label>${esc(T.senderAnzeigen)}</label>${schalter("anzeigen", E.radio.anzeigen)}</div>
      <div class="zeile"><label>${esc(T.puffer)}</label><input type="number" id="puffer" min="0" max="120" value="${E.radio.puffer_s}"><span class="leise">s</span>
        <button class="knopf" id="pufferOk">${esc(T.speichern)}</button></div><p class="leise">${esc(T.pufferText)}</p></div>
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
      <div class="zeile"><input type="text" id="nameSuche" placeholder="Antenne Bayern"><button class="knopf" id="nOk">${esc(T.suchen)}</button></div>
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
      (d.fehler.length ? `<p class="warn">${d.fehler.map(esc).join("<br>")}</p>` : "");
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
    const laden = async (name) => {
      const roh = await dienstBinaer.get("/api/sicherung/datei", { name }, { "X-SignageCast": "1" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([roh], { type: "application/zip" }));
      a.download = `signagecast-${name}`;
      document.body.appendChild(a); a.click(); a.remove();
    };
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
  let start = location.hash.slice(1);
  try { start = start || localStorage.getItem("signagecast-reiter") || "uebersicht"; } catch (_) { /* egal */ }
  zeigeSeite(start);
  window.addEventListener("hashchange", () => { if (location.hash.slice(1) !== aktiv) zeigeSeite(location.hash.slice(1)); });
});
