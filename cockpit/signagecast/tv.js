// SignageCast – Verwaltung als Cockpit-Erweiterung. Spricht nur mit dem Datendienst im Container (127.0.0.1:8080).
// Ohne Fremd-Bibliotheken; Texte Deutsch/Englisch (Sprache aus den Einstellungen).
"use strict";

const KOPF = { "X-SignageCast": "1", "Content-Type": "application/json" };
const dienst = cockpit.http(8080, { address: "127.0.0.1" });
const dienstBinaer = cockpit.http(8080, { address: "127.0.0.1", binary: true });

// ---------- Texte ----------
const TEXTE = {
  de: {
    reiter: { uebersicht: "Übersicht", fernseher: "Fernseher", layout: "Layout", streams: "Streams", radio: "Radio", einspieler: "Einspieler", anzeige: "Anzeige",
              video: "Video & Regeln", suche: "Stream-Suche", verbindung: "Verbindung", sicherung: "Sicherung" },
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
    platte: "Speicher frei", laufzeit: "Laufzeit", ha: "Home Assistant", verbunden: "verbunden", getrennt: "nicht verbunden",
    rotation: "In Rotation", liste: "Streamliste", zuletzt: "zuletzt", pause: "YouTube-Pause bis", suche: "Stream-Suche",
    vorschau: "Bild am Fernseher", vorschauNeu: "Bild aktualisieren", keineVorschau: "Kein Bild – der Stream läuft gerade nicht.",
    seiteNeu: "TV-Seite neu laden", ketteNeu: "Stream neu starten", listeNeu: "Liste neu berechnen", erledigt: "Erledigt",
    neueVersion: (v) => `Neue Version ${v} verfügbar`, updateText: "Zum Aktualisieren den Befehl als root im Container ausführen (Einstellungen und Daten bleiben).",
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
    mitStrikes: "auch Strikes übernehmen", eingespielt: "Eingespielt", sicherungText: "Die Sicherung enthält Einstellungen, " +
      "Streamliste (mit Schutz-, Sperr- und Fundliste) und Strikes. Ein Profil ist eine Sicherung als Vorlage für eine neue Installation.",
    wirklichEinspielen: "Einstellungen und Streamliste werden ersetzt. Fortfahren?",
    kat: { safari: "Safari Afrika", affen: "Affen", meer: "Unterwasser & Meer", vogel: "Vögel", baer: "Bären, Wölfe, Eisbären",
           wald: "Wald & Wildtiere", zoo: "Zoo & Exoten", neu: "Neu gefunden" },
    aufgabe: { streamliste: "Streamliste prüfen", suche: "Neue Streams suchen", wache: "Qualität messen" },
  },
  en: {
    reiter: { uebersicht: "Overview", fernseher: "TVs", layout: "Layout", streams: "Streams", radio: "Radio", einspieler: "Clips", anzeige: "Display",
              video: "Video & rules", suche: "Stream search", verbindung: "Connection", sicherung: "Backup" },
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
    platte: "Disk free", laufzeit: "Uptime", ha: "Home Assistant", verbunden: "connected", getrennt: "not connected",
    rotation: "In rotation", liste: "Stream list", zuletzt: "last", pause: "YouTube pause until", suche: "Stream search",
    vorschau: "Picture on the TV", vorschauNeu: "Refresh picture", keineVorschau: "No picture – the stream is not running.",
    seiteNeu: "Reload TV page", ketteNeu: "Restart stream", listeNeu: "Rebuild list", erledigt: "Done",
    neueVersion: (v) => `New version ${v} available`, updateText: "To update, run this command as root inside the container (settings and data are kept).",
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
    mitStrikes: "also restore strikes", eingespielt: "Restored", sicherungText: "The backup contains settings, stream list " +
      "(with protected, rejected and found streams) and strikes. A profile is a backup used as a template for a new installation.",
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
async function senden(pfad, daten) {
  const t = await dienst.post(pfad, JSON.stringify(daten || {}), KOPF);
  const d = JSON.parse(t);
  if (!d.ok) throw new Error(d.fehler || T.fehler);
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
const SEITEN = { uebersicht, fernseher: fernseherSeite, layout: layoutSeite, streams: streamsSeite, radio: radioSeite, einspieler: einspielerSeite, anzeige, video,
                 suche: sucheSeite, verbindung, sicherung: sicherungSeite };
let aktiv = "uebersicht", timer = null;
function reiterZeichnen() {
  const nav = $("#reiter");
  nav.innerHTML = "";
  for (const k of Object.keys(SEITEN)) {
    const b = el(`<button class="${k === aktiv ? "an" : ""}">${esc(T.reiter[k])}</button>`);
    b.onclick = () => zeigeSeite(k);
    nav.appendChild(b);
  }
}
function zeigeSeite(k) {
  aktiv = k;
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
        <p class="leise">${esc(T.systemSeiten)}</p>
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
        esc(s.wetter.quelle === "met" ? `MET Norway · ${s.wetter.abruf || ""}${s.wetter.fehler ? " · " + s.wetter.fehler : ""}` : T.wetterQuelleArt.ha)],
      [T.zeitKarte, s.zeit_quelle && s.zeit_quelle.abweichung_s != null ? `${s.zeit_quelle.abweichung_s > 0 ? "+" : ""}${s.zeit_quelle.abweichung_s} s` : "–",
        esc((s.zeit_quelle || {}).korrektur === false && (s.zeit_quelle || {}).host_synchronisiert ? T.hostSync
            : (s.zeit_quelle || {}).korrektur ? T.hostNichtSync : "") + "<br>" +
        esc(`${(s.zeit_quelle || {}).server || ""} · ${(s.zeit_quelle || {}).zeitzone || ""}`) +
        (Math.abs((s.zeit_quelle || {}).abweichung_s || 0) > 2 ? `<br><span class="warn">${esc(T.zeitWarnung)}</span>` : "")],
      [T.ha, s.ha.ok ? `<span class="gut">${esc(T.verbunden)}</span>` : `<span class="schlecht">${esc(T.getrennt)}</span>`, esc(s.ha.fehler || s.ha.url)],
      [T.rotation, String(s.anzahl_in_rotation), `${esc(T.liste)} ${esc(T.zuletzt)} ${esc(s.liste.zeit || "–")}` +
        (s.liste.pause_bis > Date.now() / 1000 ? ` · <span class="warn">${esc(T.pause)} ${uhrzeit(s.liste.pause_bis)}</span>` : "")],
      [T.cpu, s.cpu_prozent != null ? s.cpu_prozent + " %" : "–", `Last ${s.last.map((x) => x.toFixed(2)).join(" / ")} · ${s.kerne} Kerne`],
      [T.ram, `${s.ram_mb.frei} MB`, `von ${s.ram_mb.gesamt} MB · ${esc(T.platte)} ${s.platte_gb.frei} / ${s.platte_gb.gesamt} GB`],
      [T.laufzeit, dauer(s.laufzeit_s), `Version ${esc(s.version)}`],
    ];
    const hinweis = $("#updateHinweis");
    if (hinweis) hinweis.innerHTML = s.neue_version ? `<div class="karte warn"><b>${esc(T.neueVersion(s.neue_version))}</b>
      <pre>curl -fsSL https://raw.githubusercontent.com/thefrozn/signagecast/main/install.sh | sh</pre>
      <p class="leise">${esc(T.updateText)} <a href="${esc(s.projekt)}/releases" target="_blank" rel="noopener">${esc(T.aenderungen)}</a></p></div>` : "";
    $("#kacheln").innerHTML = k.map(([t, w2, u]) => `<div class="karte"><div class="leise">${esc(t)}</div><div class="wert">${w2}</div><div class="leise">${u}</div></div>`).join("");
    $("#aufgaben").innerHTML = s.aufgaben.map((a) => `<div class="zeile"><b>${esc(T.aufgabe[a.name] || a.name)}</b>
      <span class="leise">${esc(a.wann || T.deaktiviert)}${a.zuletzt ? " · " + esc(T.zuletzt) + " " + esc(a.zuletzt.zeit || "") : ""}</span></div>`).join("");
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
      <div class="zeile"><label>${esc(T.wetterQuelle)}</label><select id="quelle" class="breit">${Object.keys(T.wetterQuelleArt).map((k) =>
        `<option value="${k}" ${k === E.anzeige.wetter_quelle ? "selected" : ""}>${esc(T.wetterQuelleArt[k])}</option>`).join("")}</select></div>
      <p class="leise" id="metText">${esc(T.metText)}</p>
      <div class="zeile" id="haZeile"><label>${esc(T.wetter)}</label><input type="text" id="wetter" list="ents" value="${esc(E.anzeige.wetter)}"></div>
      <p class="leise">${esc(T.wetterText)}</p></div>
    <div class="zeile"><button class="knopf haupt" id="ok">${esc(T.speichern)}</button></div>`;
  $("#sprache").value = E.sprache || "de";
  const sicht = () => { const ha = $("#quelle").value === "ha"; $("#haZeile").style.display = ha ? "" : "none"; $("#metText").style.display = ha ? "none" : ""; };
  $("#quelle").onchange = sicht; sicht();
  $("#ok").onclick = async (e) => {
    await speichernE({ sprache: $("#sprache").value, anzeige: { wetter_quelle: $("#quelle").value, wetter: $("#wetter").value } }, e.target);
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
async function verbindung(inhalt) {
  const info = await holen("/api/ha/einrichtung");
  const yaml = `homeassistant:
  auth_providers:
    - type: trusted_networks
      trusted_networks:
        - ${info.eigene_ip || "IP-DES-CONTAINERS"}/32
      trusted_users:
        ${info.eigene_ip || "IP-DES-CONTAINERS"}/32: ${E.sprache === "en" ? "USER-ID" : "BENUTZER-ID"}
      allow_bypass_login: true
    - type: homeassistant`;
  inhalt.innerHTML = `<div class="karte">
      <div class="zeile"><label>${esc(T.haUrl)}</label><input type="url" id="url" value="${esc(E.ha.url)}"></div>
      <div class="zeile"><button class="knopf haupt" id="ok">${esc(T.speichern)}</button><button class="knopf" id="test">${esc(T.testen)}</button></div>
      <p id="testErg"></p></div>
    <div class="karte"><h2>${esc(T.standort)}</h2>
      <div class="zeile"><input type="text" id="ortText" placeholder="${esc(T.ortSuche)}" value="${esc(E.standort.name || "")}">
        <button class="knopf" id="ortSuchen">${esc(T.suchen)}</button></div>
      <div id="orte"></div>
      <div class="zeile"><input type="number" step="0.0001" id="breite" value="${E.standort.breite}" aria-label="${esc(T.breite)}">
        <input type="number" step="0.0001" id="laenge" value="${E.standort.laenge}" aria-label="${esc(T.laenge)}">
        <button class="knopf" id="ausHA">${esc(T.standortAusHA)}</button><button class="knopf haupt" id="okOrt">${esc(T.speichern)}</button></div></div>
    <div class="karte"><h2>${esc(T.zeitTitel)}</h2><p class="leise">${esc(T.zeitText)}</p>
      <div class="zeile"><label>${esc(T.ntpServer)}</label><input type="text" id="ntp" value="${esc(E.zeit.ntp)}" placeholder="${esc(T.ntpAuto)}"></div>
      <div class="zeile"><label>${esc(T.zeitzone)}</label><select id="zone" class="breit"><option value="">${esc(T.systemZone)}</option></select></div>
      <div class="zeile"><button class="knopf haupt" id="okZeit">${esc(T.speichern)}</button><span class="leise" id="zeitStand"></span></div></div>
    <div class="karte"><h2>${esc(T.anleitung)}</h2>${T.anleitungText(info.eigene_ip).map((z) => `<p>${esc(z)}</p>`).join("")}
      <pre>${esc(yaml)}</pre><p>${esc(T.anleitungEnde)}</p></div>`;
  const test = async () => {
    const r = await holen("/api/ha/test");
    $("#testErg").innerHTML = r.ok ? `<span class="gut">${esc(T.testOk(r.version))}</span> · ${esc(r.ort || "")}` : `<span class="schlecht">${esc(r.fehler)}</span>`;
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
    $("#zeitStand").textContent = (z.host_synchronisiert && !z.korrektur ? T.hostSync + " · " : z.korrektur ? T.hostNichtSync + " · " : "") +
      (z.server ? `${z.server}: ${T.abweichung} ${z.abweichung_s ?? "?"} s · ${z.gemessen || ""}${z.fehler ? " · " + z.fehler : ""}` : "");
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
        <div class="zeile"><label>${esc(T.adresse)}</label><code>http://${esc(ip)}:8888/${esc(t.id)}</code></div>
        <div class="zeile"><label>${esc(T.layoutWahl)}</label><select name="layout">${E.layouts.map((l) => `<option value="${esc(l.id)}" ${l.id === t.layout ? "selected" : ""}>${esc(l.name)}</option>`).join("")}</select></div>
        <details ${(t.zeitplan || []).length ? "open" : ""}><summary>${esc(T.zeitplan)} (${(t.zeitplan || []).length})</summary>
          <p class="leise">${esc(T.zeitplanText)}</p><div name="zeiten">${(t.zeitplan || []).map((z) => zeitZeile(z)).join("")}</div>
          <button class="knopf" name="zeitPlus">${esc(T.zeitNeu)}</button></details>
        <div class="zeile"><label>${esc(T.videoZeigen)}</label>${schalter("video", t.video)}</div>
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
        <div class="zeile"><span class="leise">${st.stand ? esc(T.epStand) + ": " + esc(st.stand.replace("T", " ")) : ""}${st.fehler ? ` <span class="schlecht">${esc(T.epFehler)}: ${esc(st.fehler)}</span>` : ""}</span>
          <button class="knopf" name="jetzt">${esc(T.epJetzt)}</button><button class="knopf gefahr" name="weg">${esc(T.entfernen)}</button></div></div>`);
      const urlSicht = () => { k.querySelector("[name=urlZeile]").style.display = k.querySelector("[name=quelle]").value === "tagesschau100" ? "none" : ""; };
      k.querySelector("[name=quelle]").onchange = urlSicht; urlSicht();
      k.querySelector("[name=weg]").onclick = () => k.remove();
      k.querySelector("[name=jetzt]").onclick = (e) => aktion(e.target, () => senden(`/api/einspieler/${encodeURIComponent(x.id)}/jetzt`), T.epJetztOk);
      return k;
    };
    liste.forEach((x) => ziel.appendChild(karte(x)));
    $("#epPlus").onclick = () => {
      const p = ziel.querySelector("p"); if (p) p.remove();
      ziel.appendChild(karte({ id: Math.random().toString(36).slice(2, 10).replace(/[^a-z0-9]/g, "a").padEnd(8, "x"), name: "tagesschau in 100 Sekunden",
        quelle: "tagesschau100", url: "", minuten: [0, 30], von: "06:00", bis: "23:00", ton: true, fernseher: [], aktiv: true }));
    };
    $("#epOk").onclick = async (e) => {
      const neu = [...ziel.querySelectorAll(".ep")].map((k) => {
        const w = (n) => k.querySelector(`[name=${n}]`);
        const minuten = [0, 15, 30, 45].filter((m) => w("m" + m).checked)
          .concat(w("andere").value.split(",").map((x) => parseInt(x, 10)).filter((x) => x >= 0 && x <= 59));
        return { id: k.dataset.id, name: w("name").value, quelle: w("quelle").value, url: w("url").value.trim(), minuten: minuten.length ? minuten : [0],
                 von: w("von").value, bis: w("bis").value, ton: w("ton").checked, aktiv: w("aktiv").checked,
                 fernseher: E.fernseher.filter((t) => w("tv_" + t.id).checked).map((t) => t.id) };
      });
      await speichernE({ einspieler: neu }, e.target);
      setTimeout(() => zeichnen().catch(() => {}), 4000);         // Stand/Fehler der Quellen nachladen
    };
  };
  await zeichnen();
}

// ---------- Sicherung ----------
async function sicherungSeite(inhalt) {
  inhalt.innerHTML = `<div class="karte"><p>${esc(T.sicherungText)}</p>
      <div class="zeile"><button class="knopf haupt" id="laden">${esc(T.sicherungLaden)}</button></div></div>
    <div class="karte"><h2>${esc(T.sicherungEinspielen)}</h2>
      <div class="zeile"><input type="file" id="datei" accept=".json,application/json"></div>
      <div class="zeile"><label><input type="checkbox" id="mitStrikes"> ${esc(T.mitStrikes)}</label></div>
      <div class="zeile"><button class="knopf" id="ein">${esc(T.sicherungEinspielen)}</button></div></div>`;
  $("#laden").onclick = (e) => aktion(e.target, async () => {
    const d = await holen("/api/sicherung");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 1)], { type: "application/json" }));
    a.download = `signagecast-sicherung-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a); a.click(); a.remove();
  }, null);
  $("#ein").onclick = (e) => aktion(e.target, async () => {
    const f = $("#datei").files[0]; if (!f) throw new Error("–");
    if (!confirm(T.wirklichEinspielen)) return;
    const d = JSON.parse(await f.text());
    if (!$("#mitStrikes").checked) delete d.strikes;
    await senden("/api/sicherung", d);
    await einstellungenLaden(); reiterZeichnen(); hinweiseZeichnen();
  }, T.eingespielt);
}

// ---------- Start ----------
document.addEventListener("DOMContentLoaded", async () => {
  try { await einstellungenLaden(); } catch (e) {
    $("#inhalt").innerHTML = `<div class="karte schlecht">SignageCast-Dienst nicht erreichbar / service not reachable: ${esc(e.message || e)}</div>`;
    return;
  }
  hinweiseZeichnen();
  let start = "uebersicht";
  try { start = localStorage.getItem("signagecast-reiter") || start; } catch (_) { /* egal */ }
  zeigeSeite(SEITEN[start] ? start : "uebersicht");
});
