// SignageCast – Reiter „Datenquellen“: eigene API-Abfragen (JSON/Text), RSS-/Atom-Feeds, Kalender, Tabellen, Bilder, Kameras.
// Der Datendienst holt sie im eingestellten Abstand; die Bausteine im Layout zeigen Werte daraus (Pfad aus dem Antwort-Baum).
// Seit 0.57: Liste mit Ampel, letztem Wert und „benutzt in“, Details im Seitenfeld, Assistent Was? → Woher? → Werte;
// Technik (Kennung, Methode, Kopfzeilen) unter „Erweitert“. Seitenfeld und ⋯-Menü kommen aus live.js.
// Nutzt die Hilfsfunktionen aus tv.js (holen, senden, aktion, esc, el, $, schalter, melden, E) und live.js (seitenfeld, mehrMenue).
"use strict";

const QTEXTE = {
  de: {
    text: "Eigene Daten für die Bausteine: Der Container fragt die Adresse im eingestellten Abstand ab (API-Schlüssel bleiben im Container). " +
      "In den Layout-Bausteinen „API-Wert“, „API-Liste“, „API-Bild“, „Anzeige“, „Countdown“, „QR-Code“ und im freien Text wählst du dann einen Wert daraus.",
    neu: "Neue Quelle", ausCurl: "Aus curl übernehmen", beispiel: "Beispiel einfügen …", keine: "Noch keine Datenquelle.",
    curlText: "curl-Befehl hier einfügen (z. B. aus einer API-Anleitung). Er wird nur gelesen, nicht ausgeführt.", uebernehmen: "Übernehmen",
    name: "Name", kennung: "Kennung (a–z, 0–9, _ – steht in Platzhaltern)", art: "Art", artName: { json: "JSON-API", text: "Text", rss: "RSS-/Atom-Feed", bild: "Bild", ical: "Kalender (iCal)", video: "Kamera (Video)", csv: "Tabelle (CSV)" },
    format: "Format", formatName: { auto: "automatisch", rtsp: "RTSP", hls: "HLS (.m3u8)", mjpeg: "MJPEG" },
    videoHinweis: "Kamera: RTSP oder HLS holt der Container nur, solange ein Fernseher sie zeigt (H.264 nötig); MJPEG wird durchgereicht. Zugangsdaten in der Adresse (rtsp://benutzer:passwort@…) bleiben im Container und erscheinen hier als ••••.",
    url: "Adresse", methode: "Methode", intervall: "Abrufen alle", einheit: { 1: "Sekunden", 60: "Minuten", 3600: "Stunden" }, aktiv: "aktiv",
    kopf: "Kopfzeilen (z. B. Authorization, X-API-Key)", kopfNeu: "Kopfzeile hinzufügen", geheim: "geheim", inhalt: "Inhalt (bei POST)",
    testen: "Testen", speichern: "Speichern", abbrechen: "Abbrechen", bearbeiten: "Bearbeiten", loeschen: "Löschen", jetzt: "Jetzt abrufen",
    daten: "Daten ansehen", wirklichLoeschen: "Datenquelle löschen? Bausteine, die sie benutzen, bleiben leer.",
    letzter: "zuletzt", naechster: "nächster", nie: "noch nie", fehler: "Fehler", ms: "ms", versuche: "Versuche",
    antwort: "Antwort – auf einen Wert tippen, um seinen Pfad zu übernehmen", pfad: "Pfad", kopiert: "Pfad kopiert",
    platzhalterHilfe: (id, p) => `Im Baustein: Pfad „${p}“ · im freien Text: {${id}:${p}}`, hinweise: "Hinweise",
    leer: "(leer)", eintraege: "Einträge", geheimHinweis: "Geheime Werte werden nach dem Speichern nur als •••• angezeigt und nicht in Sicherungen übernommen (außer du wählst es).",
    beispiele: { pegel: "Pegelstand (PEGELONLINE, Rhein bei Köln)", news: "Nachrichten (tagesschau.de RSS)", kurs: "Bitcoin-Kurs in Euro (CoinGecko)",
                 pollen: "Pollenflug (Deutscher Wetterdienst)", feiertage: "Feiertage (Google-Kalender, iCal)" },
    herkunft: "Herkunft", herkunftName: { url: "Adresse abrufen", datei: "Datei hochladen", speicherort: "Datei aus Speicherort" }, datei: "Datei (bis 1 MB)",
    dateiHinweis: "Zum Beispiel der Abfuhrkalender deiner Stadt als .ics oder .csv, wenn es keine Abo-Adresse gibt. Neue Termine: Datei wieder hochladen.",
    hochgeladen: "hochgeladen", felderLesen: "Spalten lesen", csvFelder: "Spalten der CSV",
    termine: "Als Termine (für den Baustein „Kalender / Müllabfuhr“)", termineHinweis: "Datumsspalte wählen – dann zeigt der Kalender-Baustein die Zeilen als Termine. Vergangene fallen weg.",
    tDatum: "Datum", tZeit: "Uhrzeit (leer = ganztägig oder aus der Datumsspalte)", tTitel: "Titel", tOrt: "Ort", ohne: "– keine –",
    // seit 0.57
    titel: "Datenquellen", neuKnopf: "+ Datenquelle hinzufügen", mehrCurl: "Aus curl-Befehl übernehmen …",
    leerText: "Noch keine Datenquelle. Lege eine an – zum Beispiel Nachrichten als Laufschrift oder einen Pegelstand als Zahl.",
    benutztIn: (l) => `in ${l}`, unbenutzt: "in keinem Layout", benutztLang: "Benutzt in", keinLayout: "Noch in keinem Layout – im Layout-Editor einen Baustein wie „API-Wert“ hinzufügen und diese Quelle wählen.",
    zustand: { ok: "aktuell", fehler: "Fehler", warten: "wartet auf den ersten Abruf", aus: "ausgeschaltet", kamera: "wird geholt, wenn ein Kanal sie zeigt" },
    vor: (t) => `vor ${t}`, wert: "Wert", anzahlName: { eintraege: "Einträge", termine: "Termine", zeilen: "Zeilen" },
    werteAnsehen: "Werte ansehen", werteText: "Auf einen Wert tippen: dann siehst du, wie du ihn im Layout benutzt.",
    loeschenBenutzt: (l) => `Datenquelle löschen? Sie wird benutzt in: ${l}. Diese Bausteine bleiben dann leer.`,
    schritt: ["Was?", "Woher?", "Werte"], zurueck: "← Zurück", wasTitel: "Was möchtest du anzeigen?",
    oder: "Oder", bspTitel: "Mit einem Beispiel ausprobieren",
    kachel: {
      rss: ["Nachrichten / Feed", "RSS- oder Atom-Adresse einer Webseite – für Laufschrift oder Liste"],
      json: ["Wert aus dem Netz", "Zahl oder Text von einer Web-API (JSON), z. B. Pegel, Kurs, Zähler"],
      ical: ["Kalender", "Termine aus einer iCal-Adresse oder .ics-Datei, z. B. Feiertage, Müllabfuhr"],
      csv: ["Tabelle", "CSV-Datei oder -Adresse, z. B. Speisekarte, Preise, Abfuhrkalender"],
      bild: ["Bild", "Ein Bild, das sich ändert, z. B. Wetterkarte oder Diagramm"],
      video: ["Kamera", "Live-Bild einer Kamera (RTSP, HLS oder MJPEG)"],
      text: ["Text", "Reiner Text von einer Adresse"],
    },
    urlHinweis: { rss: "Meist zu finden über das RSS-Symbol oder als …/feed, …/rss.xml.", json: "Die Adresse steht in der Anleitung der API. Braucht sie einen Schlüssel: unter „Erweitert“ als Kopfzeile eintragen.",
                  ical: "Bei Google-Kalender: Einstellungen → „Öffentliche Adresse im iCal-Format“.", bild: "Direkte Adresse eines Bildes (.jpg, .png …).", text: "", csv: "", video: "" },
    abstand: "Neu holen alle", weiterTesten: "Testen", testOk: (ms) => `Hat geklappt (${ms} ms).`,
    gespeichert: "Datenquelle gespeichert", zuLayout: "Zum Layout-Editor",
    sofort: "Jetzt abrufen", abgerufen: "Wird gleich neu geholt",
  },
  en: {
    text: "Your own data for the elements: the container queries the address at the interval you set (API keys stay in the container). " +
      "In the layout elements “API value”, “API list”, “API picture”, “Gauge”, “Countdown”, “QR code” and in free text you then pick a value from it.",
    neu: "New source", ausCurl: "Import from curl", beispiel: "Insert example …", keine: "No data source yet.",
    curlText: "Paste a curl command here (e.g. from an API guide). It is only read, never executed.", uebernehmen: "Import",
    name: "Name", kennung: "Identifier (a–z, 0–9, _ – used in placeholders)", art: "Type", artName: { json: "JSON API", text: "Text", rss: "RSS/Atom feed", bild: "Picture", ical: "Calendar (iCal)", video: "Camera (video)", csv: "Table (CSV)" },
    format: "Format", formatName: { auto: "automatic", rtsp: "RTSP", hls: "HLS (.m3u8)", mjpeg: "MJPEG" },
    videoHinweis: "Camera: RTSP or HLS is only fetched by the container while a TV shows it (H.264 required); MJPEG is passed through. Credentials in the address (rtsp://user:password@…) stay in the container and show as •••• here.",
    url: "Address", methode: "Method", intervall: "Fetch every", einheit: { 1: "seconds", 60: "minutes", 3600: "hours" }, aktiv: "active",
    kopf: "Headers (e.g. Authorization, X-API-Key)", kopfNeu: "Add header", geheim: "secret", inhalt: "Body (for POST)",
    testen: "Test", speichern: "Save", abbrechen: "Cancel", bearbeiten: "Edit", loeschen: "Delete", jetzt: "Fetch now",
    daten: "View data", wirklichLoeschen: "Delete data source? Elements using it stay empty.",
    letzter: "last", naechster: "next", nie: "never", fehler: "Error", ms: "ms", versuche: "attempts",
    antwort: "Response – tap a value to take its path", pfad: "Path", kopiert: "Path copied",
    platzhalterHilfe: (id, p) => `In an element: path “${p}” · in free text: {${id}:${p}}`, hinweise: "Notes",
    leer: "(empty)", eintraege: "entries", geheimHinweis: "Secret values are shown as •••• after saving and are not included in backups (unless you choose so).",
    beispiele: { pegel: "Water level (PEGELONLINE, Rhine at Cologne)", news: "News (tagesschau.de RSS)", kurs: "Bitcoin price in euro (CoinGecko)",
                 pollen: "Pollen forecast (German Weather Service)", feiertage: "Public holidays Germany (Google calendar, iCal)" },
    herkunft: "Source", herkunftName: { url: "Fetch address", datei: "Upload file", speicherort: "File from storage location" }, datei: "File (up to 1 MB)",
    dateiHinweis: "For example your town's waste collection calendar as .ics or .csv when there is no subscription address. New dates: upload the file again.",
    hochgeladen: "uploaded", felderLesen: "Read columns", csvFelder: "CSV columns",
    termine: "As events (for the “Calendar / waste collection” element)", termineHinweis: "Choose the date column – the calendar element then shows the rows as events. Past ones are dropped.",
    tDatum: "Date", tZeit: "Time (empty = all day or from the date column)", tTitel: "Title", tOrt: "Location", ohne: "– none –",
    titel: "Data sources", neuKnopf: "+ Add data source", mehrCurl: "Import from a curl command …",
    leerText: "No data source yet. Add one – for example news as a ticker or a water level as a number.",
    benutztIn: (l) => `in ${l}`, unbenutzt: "in no layout", benutztLang: "Used in", keinLayout: "Not in any layout yet – in the layout editor add an element such as “API value” and pick this source.",
    zustand: { ok: "up to date", fehler: "Error", warten: "waiting for the first fetch", aus: "switched off", kamera: "fetched while a channel shows it" },
    vor: (t) => `${t} ago`, wert: "Value", anzahlName: { eintraege: "entries", termine: "events", zeilen: "rows" },
    werteAnsehen: "View values", werteText: "Tap a value to see how to use it in a layout.",
    loeschenBenutzt: (l) => `Delete data source? It is used in: ${l}. Those elements stay empty then.`,
    schritt: ["What?", "Where from?", "Values"], zurueck: "← Back", wasTitel: "What do you want to show?",
    oder: "Or", bspTitel: "Try an example",
    kachel: {
      rss: ["News / feed", "RSS or Atom address of a website – for a ticker or a list"],
      json: ["Value from the web", "Number or text from a web API (JSON), e.g. water level, price, counter"],
      ical: ["Calendar", "Events from an iCal address or .ics file, e.g. holidays, waste collection"],
      csv: ["Table", "CSV file or address, e.g. menu, prices, collection calendar"],
      bild: ["Picture", "A picture that changes, e.g. weather map or chart"],
      video: ["Camera", "Live picture of a camera (RTSP, HLS or MJPEG)"],
      text: ["Text", "Plain text from an address"],
    },
    urlHinweis: { rss: "Usually found via the RSS icon or as …/feed, …/rss.xml.", json: "The address is in the API's guide. If it needs a key: add it as a header under “Advanced”.",
                  ical: "Google Calendar: settings → “Public address in iCal format”.", bild: "Direct address of a picture (.jpg, .png …).", text: "", csv: "", video: "" },
    abstand: "Fetch again every", weiterTesten: "Test", testOk: (ms) => `It worked (${ms} ms).`,
    gespeichert: "Data source saved", zuLayout: "To the layout editor",
    sofort: "Fetch now", abgerufen: "Will be fetched again shortly",
  },
};
const QBEISPIELE = {
  pegel: { id: "pegel", name: "Pegel Köln", art: "json", intervall_s: 900,
           url: "https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/K%C3%96LN/W/currentmeasurement.json" },
  news: { id: "news", name: "tagesschau.de", art: "rss", intervall_s: 900, url: "https://www.tagesschau.de/index~rss2.xml" },
  kurs: { id: "kurs", name: "Bitcoin", art: "json", intervall_s: 600, url: "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur" },
  pollen: { id: "pollen", name: "Pollenflug DWD", art: "json", intervall_s: 3600, url: "https://opendata.dwd.de/climate_environment/health/alerts/s31fg.json" },
  feiertage: { id: "feiertage", name: "Feiertage", art: "ical", intervall_s: 86400,
               url: "https://calendar.google.com/calendar/ical/de.german%23holiday%40group.v.calendar.google.com/public/basic.ics" },
};
const QT = () => QTEXTE[E.sprache] || QTEXTE.de;

// ---------- Antwort als Baum; ein Klick auf einen Wert liefert seinen Pfad ----------
function baumHtml(w, pfad, tiefe) {
  const blatt = (p, schluessel, wert) => `<button type="button" class="blatt" data-pfad="${esc(p)}"><span class="schluessel">${esc(schluessel)}</span>` +
    `<span class="wertq">${esc(wert === "" ? QT().leer : String(wert).slice(0, 120))}</span></button>`;
  if (w === null || typeof w !== "object") return blatt(pfad, pfad || "·", w === null ? "null" : w);
  const eintraege = Array.isArray(w) ? w.map((v, i) => [`[${i}]`, pfad + `[${i}]`, v])
    : Object.entries(w).map(([k, v]) => [k, pfad ? `${pfad}.${k}` : k, v]);
  return eintraege.map(([name, p, v]) => (v !== null && typeof v === "object")
    ? `<details ${tiefe < 1 ? "open" : ""}><summary><span class="schluessel">${esc(name)}</span>` +
      `<span class="leise">${Array.isArray(v) ? `[${v.length}]` : "{…}"}</span>` +
      (Array.isArray(v) ? ` <button type="button" class="blatt mini" data-pfad="${esc(p)}">${esc(QT().pfad)}</button>` : "") +
      `</summary><div class="kinder">${baumHtml(v, p, tiefe + 1)}</div></details>`
    : blatt(p, name, v)).join("");
}
function baumZeigen(ziel, daten, beiWahl) {
  ziel.innerHTML = `<div class="baum">${typeof daten === "string" ? `<pre>${esc(daten.slice(0, 3000))}</pre>` : baumHtml(daten, "", 0)}</div>`;
  ziel.querySelectorAll(".blatt").forEach((b) => {
    b.onclick = (ev) => { ev.preventDefault(); ev.stopPropagation(); beiWahl(b.dataset.pfad); };
  });
}
// Für den Layout-Editor: gespeicherte Daten einer Quelle laden und Pfad wählen lassen
async function pfadWaehlen(ziel, quelleId, beiWahl) {
  if (!quelleId) { ziel.innerHTML = ""; return; }
  const d = await holen("/api/quellen/daten?id=" + encodeURIComponent(quelleId));
  if (!d.ok) { ziel.innerHTML = `<p class="schlecht">${esc(d.fehler ? meldungText(d.fehler_m, d.fehler) : QT().nie)}</p>`; return; }
  baumZeigen(ziel, d.daten, (p) => { ziel.innerHTML = ""; beiWahl(p); });
}

function zeitText(ts) {
  return ts ? new Date(ts * 1000).toLocaleString([], { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }) : QT().nie;
}

// ---------- seit 0.57: Liste, Seitenfeld, Assistent ----------
const QSYMBOL = { rss: "📰", json: "🔢", ical: "📅", csv: "📋", bild: "🖼", video: "📹", text: "📝" };
let QSTATUS = {};

// Layouts, die eine Quelle benutzen: Baustein-Quelle, Bedingung oder Platzhalter {id:pfad} in einem Text
function quelleBenutzt(id) {
  const platzhalter = new RegExp(`\\{\\s*${id}:`);
  return (E.layouts || []).filter((l) => (l.elemente || []).some((e) => {
    const o = e.optionen || {};
    return o.quelle === id || (e.bedingung && e.bedingung.quelle === id) || platzhalter.test(JSON.stringify(o));
  })).map((l) => l.name || l.id);
}
function vorZeit(ts) {
  const s = Math.max(0, Date.now() / 1000 - ts);
  const t = s < 90 ? `${Math.round(s)} s` : s < 5400 ? `${Math.round(s / 60)} min` : s < 172800 ? `${Math.round(s / 3600)} h` : `${Math.round(s / 86400)} d`;
  return QT().vor(t);
}
function quelleZustand(q) {
  const Q = QT(), s = QSTATUS[q.id] || {};
  if (!q.aktiv) return ["aus", Q.zustand.aus, ""];
  if (q.art === "video") return ["kamera", Q.zustand.kamera, "gut"];
  if (s.fehler) return ["fehler", `${Q.zustand.fehler}: ${meldungText(s.fehler_m, s.fehler)}`, "schlecht"];
  if (!s.abruf) return ["warten", Q.zustand.warten, "warn"];
  return ["ok", `${Q.zustand.ok} · ${vorZeit(s.abruf)}`, "gut"];
}
function kurzText(s) {
  const Q = QT(), k = s && s.kurz;
  if (!k) return "";
  if (k.n != null) return `${k.n} ${Q.anzahlName[k.liste] || Q.eintraege}${k.text ? " · " + k.text : ""}`;
  return k.text ? (k.pfad ? `${k.pfad} = ${k.text}` : k.text) : "";
}
function herkunftKurz(q) {
  if (q.herkunft === "datei") return "📄 " + (q.datei ? q.datei.name : "");
  if (q.herkunft === "speicherort" && q.speicherort) return "📁 " + soName(q.speicherort.ort) + ": " + q.speicherort.pfad;
  try { return new URL(q.url).host || q.url; } catch (_) { return q.url || ""; }
}
const intervallText = (s) => (s % 3600 === 0 ? `${s / 3600} h` : s % 60 === 0 ? `${s / 60} min` : `${s} s`);

async function quellenSeite(inhalt) {
  const Q = QT();
  inhalt.innerHTML = `<div class="karte"><div class="lv-kopf"><div><h2>${esc(Q.titel)}</h2><p class="leise">${esc(Q.text)}</p></div>
      <div class="zeile" id="qKopfKnoepfe"><button type="button" class="knopf haupt" id="qNeu">${esc(Q.neuKnopf)}</button></div></div></div>
    <div class="lliste" id="qListe"></div>`;
  $("#qKopfKnoepfe").appendChild(mehrMenue([[Q.mehrCurl, () => quelleAssistent("curl")]]));
  $("#qNeu").onclick = () => quelleAssistent();
  try { await soLaden(); } catch (_) { /* Namen der Speicherorte fehlen dann */ }
  try { QPZ = (await holen("/api/protokoll")).zuletzt || {}; } catch (_) { /* „Letzte Änderung“ fehlt dann */ }
  await quellenLaden();
  timer = setInterval(() => { if (!document.querySelector(".seitenfeld")) quellenLaden().catch(() => {}); }, 15000);
}
let QPZ = {};                // letzte Änderung je Quelle aus dem Protokoll (seit 0.66)
async function quellenLaden() {
  QSTATUS = (await holen("/api/quellen/status")).status || {};
  const ziel = $("#qListe"), Q = QT();
  if (!ziel) return;
  ziel.innerHTML = "";
  if (!E.quellen.length) {
    const leer = el(`<div class="karte"><p>${esc(Q.leerText)}</p><div class="zeile"><button type="button" class="knopf haupt">${esc(Q.neuKnopf)}</button></div></div>`);
    leer.querySelector("button").onclick = () => quelleAssistent();
    ziel.appendChild(leer);
    return;
  }
  const gewaehlt = document.querySelector(".seitenfeld") && document.querySelector(".lzeile.gewaehlt");
  for (const q of E.quellen) {
    const z = quelleZeile(q);
    if (gewaehlt && gewaehlt.dataset.id === q.id) z.classList.add("gewaehlt");
    ziel.appendChild(z);
  }
}
function quelleZeile(q) {
  const Q = QT(), [, zt, stil] = quelleZustand(q), b = quelleBenutzt(q.id), wert = kurzText(QSTATUS[q.id]);
  const z = el(`<div class="lzeile" tabindex="0" role="button" data-id="${esc(q.id)}">
    <div class="lz-haupt"><div class="lz-name">${QSYMBOL[q.art] || ""} ${esc(q.name || q.id)}</div>
      <div class="lz-info">${esc(Q.artName[q.art])} · ${esc(herkunftKurz(q))}${q.art === "video" ? "" : " · " + esc(intervallText(q.intervall_s))}
        · ${b.length ? esc(Q.benutztIn(b.join(", "))) : `<span class="warn">${esc(Q.unbenutzt)}</span>`}
        · ${esc(T.ding.zuletzt)}: ${esc(zuletztText(QPZ, "quelle:" + q.id))}</div>
      ${wert ? `<div class="lz-info qwert">${esc(wert)}</div>` : ""}</div>
    <div class="lz-status ${stil}">${stil ? "● " : ""}${esc(zt)}</div>
    <div class="lz-aktion">${schalter("aktiv", q.aktiv)}</div></div>`);
  const sw = z.querySelector(".schalter");
  sw.title = Q.aktiv;
  sw.addEventListener("click", (e) => e.stopPropagation());
  sw.querySelector("input").onchange = (e) => aktion(null, async () => {
    await quellenSpeichern(E.quellen.map((x) => (x.id === q.id ? Object.assign({}, x, { aktiv: e.target.checked }) : x)));
  });
  const knoepfe = [];
  if (q.art !== "video") knoepfe.push([Q.sofort, (k) => aktion(k, async () => { await senden("/api/quellen/jetzt", { id: q.id }); setTimeout(() => quellenLaden().catch(() => {}), 3000); }, Q.abgerufen)]);
  knoepfe.push([Q.loeschen, (k) => quelleLoeschen(q, k), true]);
  z.querySelector(".lz-aktion").appendChild(mehrMenue(knoepfe));
  const oeffnen = () => { quelleDetails(q); z.classList.add("gewaehlt"); };
  z.onclick = oeffnen;
  z.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); oeffnen(); } };
  return z;
}
async function quellenSpeichern(neu) {
  const d = await senden("/api/einstellungen", { quellen: neu });
  E = d.einstellungen;
  await quellenLaden();
}
function quelleLoeschen(q, knopf) {
  const Q = QT(), b = quelleBenutzt(q.id);
  if (!confirm(b.length ? Q.loeschenBenutzt(b.join(", ")) : Q.wirklichLoeschen)) return;
  aktion(knopf, async () => { seitenfeldZu(); await quellenSpeichern(E.quellen.filter((x) => x.id !== q.id)); });
}
function pfadHinweis(ziel, id, p) {
  if (navigator.clipboard) navigator.clipboard.writeText(p).catch(() => {});      // geht nur im Fokus / über HTTPS
  ziel.querySelectorAll(".pfadHinweis").forEach((x) => x.remove());
  ziel.prepend(el(`<p class="gut pfadHinweis">${esc(QT().platzhalterHilfe(id, p))}</p>`));
  melden(QT().kopiert);
}

// Details einer vorhandenen Quelle: Zustand, Werte, Benutzt in – darunter das Formular
function quelleDetails(q) {
  const Q = QT(), s = QSTATUS[q.id] || {}, [, zt, stil] = quelleZustand(q), b = quelleBenutzt(q.id);
  const k = el(`<div>
    <p><span class="marke ${stil}">${esc(zt)}</span></p>
    ${q.art !== "video" ? `<p class="leise">${esc(Q.letzter)}: ${esc(zeitText(s.abruf))}${s.dauer_ms != null ? ` (${s.dauer_ms} ${Q.ms})` : ""} · ${esc(Q.naechster)}: ${esc(zeitText(s.naechster))}${s.versuche ? ` · ${s.versuche} ${esc(Q.versuche)}` : ""}</p>` : ""}
    ${kurzText(s) ? `<p>${esc(Q.wert)}: <b>${esc(kurzText(s))}</b></p>` : ""}
    <div class="feld"><label>${esc(Q.benutztLang)}</label>${b.length ? `<p>${esc(b.join(", "))}</p>` : `<p class="leise">${esc(Q.keinLayout)}</p>`}</div>
    ${q.art !== "video" && s.hat_daten ? `<details class="feld" id="qWerte"><summary>${esc(Q.werteAnsehen)}</summary><p class="leise">${esc(Q.werteText)}</p><div class="qDaten"></div></details>` : ""}
    <div id="qForm"></div>
    <details class="feld" id="qVerlauf"><summary>${esc(T.ding.verlauf)}</summary><div data-verlauf></div></details>
    <div class="loeschen"><p class="leise">${esc(b.length ? T.ding.verwendetVon(b.join(", ")) : T.ding.nichtVerwendet)}</p>
      <button type="button" class="knopf gefahr" id="qWeg">${esc(Q.loeschen)}</button></div></div>`);
  const v = k.querySelector("#qVerlauf");
  v.addEventListener("toggle", () => { if (v.open) verlaufZeichnen(v.querySelector("[data-verlauf]"), "quelle:" + q.id).catch(() => {}); });
  k.querySelector("#qWeg").onclick = (ev) => quelleLoeschen(q, ev.target);     // seit 0.66 unten (UI-Regel Punkt 2)
  const w = k.querySelector("#qWerte");
  if (w) w.addEventListener("toggle", () => {
    if (w.open) aktion(null, () => pfadWaehlen(w.querySelector(".qDaten"), q.id, (p) => { pfadHinweis(w, q.id, p); }), null);
  });
  seitenfeld(q.name || q.id, k);
  quelleFormular(JSON.parse(JSON.stringify(q)), q.id, $("#qForm"), {});
}

// Neue Quelle: 1 Was? (Kacheln, Beispiel, curl) → 2 Woher? (Formular, Testen) → 3 Werte (Antwort-Baum)
function quelleAssistent(start) {
  const Q = QT();
  const k = el(`<div><ol class="schritte">${Q.schritt.map((t, i) => `<li data-schritt="${i + 1}">${esc(t)}</li>`).join("")}</ol><div id="qSchritt"></div></div>`);
  const schritt = (n) => k.querySelectorAll(".schritte li").forEach((li) => {
    li.classList.toggle("an", Number(li.dataset.schritt) === n); li.classList.toggle("fertig", Number(li.dataset.schritt) < n);
  });
  const was = () => {
    schritt(1);
    const z = k.querySelector("#qSchritt");
    z.innerHTML = `<h3>${esc(Q.wasTitel)}</h3><div class="kacheln">${Object.keys(Q.kachel).map((a) =>
      `<button type="button" class="kachel" data-art="${a}"><span class="kachel-symbol">${QSYMBOL[a]}</span><b>${esc(Q.kachel[a][0])}</b><span class="leise">${esc(Q.kachel[a][1])}</span></button>`).join("")}</div>
      <h3>${esc(Q.bspTitel)}</h3><div class="bsp-liste">${Object.keys(QBEISPIELE).map((b) => `<button type="button" class="knopf klein" data-bsp="${b}">${esc(Q.beispiele[b])}</button>`).join("")}</div>
      <details class="erweitert" id="qCurlBox"><summary>${esc(Q.ausCurl)}</summary><p class="leise">${esc(Q.curlText)}</p>
        <textarea id="qCurlText" rows="5" class="voll" spellcheck="false"></textarea>
        <div class="zeile"><button type="button" class="knopf haupt" id="qCurlOk">${esc(Q.uebernehmen)}</button></div></details>`;
    z.querySelectorAll("[data-art]").forEach((b) => { b.onclick = () => woher({ art: b.dataset.art, intervall_s: b.dataset.art === "ical" ? 3600 : 300 }); });
    z.querySelectorAll("[data-bsp]").forEach((b) => { b.onclick = () => woher(JSON.parse(JSON.stringify(QBEISPIELE[b.dataset.bsp]))); });
    z.querySelector("#qCurlOk").onclick = (ev) => aktion(ev.target, async () => {
      const r = await senden("/api/quellen/curl", { befehl: $("#qCurlText").value }).catch((e) => ({ ok: false, fehler: e.message }));
      if (!r.ok) throw new Error(r.fehler);
      woher(r.quelle, r.hinweise);
    }, null);
    if (start === "curl") { z.querySelector("#qCurlBox").open = true; z.querySelector("#qCurlText").focus(); start = null; }
  };
  const woher = (q, hinweise) => {
    schritt(2);
    const z = k.querySelector("#qSchritt");
    z.innerHTML = `<div class="zeile"><button type="button" class="knopf klein" id="qZurueck">${esc(Q.zurueck)}</button>
      <b>${QSYMBOL[q.art] || ""} ${esc((Q.kachel[q.art] || [Q.artName[q.art]])[0])}</b></div><div id="qForm"></div>`;
    z.querySelector("#qZurueck").onclick = was;
    quelleFormular(q, null, z.querySelector("#qForm"), {
      hinweise, beimTest: (ok) => schritt(ok ? 3 : 2),
      gespeichert: (neu) => { seitenfeldZu(); melden(Q.gespeichert); const r = document.querySelector(`.lzeile[data-id="${CSS.escape(neu.id)}"]`); if (r) r.scrollIntoView({ block: "nearest" }); },
    });
  };
  seitenfeld(Q.neuKnopf.replace(/^\+\s*/, ""), k);
  was();
}

// ---------- Formular (Seitenfeld): Wichtiges oben, Technik unter „Erweitert“ ----------
function quelleFormular(q0, altId, z, opt) {
  const Q = QT();
  const q = Object.assign({ id: "", name: "", art: "json", url: "https://", methode: "GET", kopf: [], inhalt: "", intervall_s: 300, aktiv: true, format: "auto",
                            herkunft: "url", datei: null, speicherort: null, csv: null }, q0);
  let csvImp = null;
  const einheitVon = (s) => (s % 3600 === 0 ? 3600 : s % 60 === 0 ? 60 : 1);
  const zeichnen = () => {
    const ein = einheitVon(q.intervall_s);
    const technikOffen = q.kopf.length || q.methode === "POST" || (opt.hinweise && opt.hinweise.length);
    z.innerHTML = `<div class="feld"><label for="qName">${esc(Q.name)}</label><input type="text" id="qName" value="${esc(q.name)}"></div>
      <div class="feld" data-nicht="video"><label for="qHerkunft">${esc(Q.herkunft)}</label><select id="qHerkunft">${Object.keys(Q.herkunftName).map((k) =>
        `<option value="${k}" ${k === q.herkunft ? "selected" : ""}>${esc(Q.herkunftName[k])}</option>`).join("")}</select></div>
      <div class="feld" data-nur="datei"><label for="qDatei">${esc(Q.datei)}</label><input type="file" id="qDatei" accept=".ics,.csv,.tsv,.txt,.json,.xml,text/calendar,text/csv">
        <span class="leise" id="qDateiStand">${q.datei ? "✓ " + esc(q.datei.name) : ""}</span><p class="leise">${esc(Q.dateiHinweis)}</p></div>
      <div class="feld" data-nur="so"><label>${esc(Q.datei.replace(/ \(.*\)$/, ""))}</label><div class="zeile"><button type="button" class="knopf" id="qSoWahl">📁 ${esc(SOT().qWahl)}</button>
        <span class="leise" id="qSoStand">${q.speicherort ? "✓ " + esc(soName(q.speicherort.ort)) + ": " + esc(q.speicherort.pfad) : ""}</span></div><p class="leise">${esc(SOT().qHinweis)}</p></div>
      <div class="feld" data-nicht="keinurl"><label for="qUrl">${esc(Q.url)}</label><input type="text" id="qUrl" value="${esc(q.url)}" spellcheck="false">
        ${Q.urlHinweis[q.art] ? `<p class="leise">${esc(Q.urlHinweis[q.art])}</p>` : ""}</div>
      <div class="feld" data-nur="video"><label for="qFormat">${esc(Q.format)}</label><select id="qFormat">${Object.keys(Q.formatName).map((k) => `<option value="${k}" ${k === q.format ? "selected" : ""}>${esc(Q.formatName[k])}</option>`).join("")}</select>
        <p class="leise">${esc(Q.videoHinweis)}</p></div>
      <div class="feld" data-nicht="video"><label for="qIv">${esc(Q.abstand)}</label><div class="zeile"><input type="number" id="qIv" min="1" class="b120" value="${q.intervall_s / ein}">
        <select id="qIvE" aria-label="${esc(Q.abstand)}">${[1, 60, 3600].map((e) => `<option value="${e}" ${e === ein ? "selected" : ""}>${esc(Q.einheit[e])}</option>`).join("")}</select></div></div>
      <div class="zeile">${schalter("qAktiv", q.aktiv)}<span>${esc(Q.aktiv)}</span></div>
      <div data-nur="csv"><h3>${esc(Q.csvFelder)}</h3><div class="zeile" data-nicht="keinurl"><button type="button" class="knopf" id="qCsvLesen">${esc(Q.felderLesen)}</button></div>
        <div id="qCsv"></div><h3>${esc(Q.termine)}</h3><p class="leise">${esc(Q.termineHinweis)}</p><div id="qCsvKal"></div></div>
      <details class="erweitert" ${technikOffen ? "open" : ""}><summary>${esc(LT().erweitert)}</summary>
        <div class="feld"><label for="qId">${esc(Q.kennung)}</label><input type="text" id="qId" value="${esc(q.id)}" class="b160" pattern="[a-z0-9_]{2,16}"></div>
        <div class="feld"><label for="qArt">${esc(Q.art)}</label><select id="qArt">${Object.keys(Q.artName).map((k) => `<option value="${k}" ${k === q.art ? "selected" : ""}>${esc(Q.artName[k])}</option>`).join("")}</select></div>
        <div class="feld" data-nicht="keinurl"><label for="qMethode">${esc(Q.methode)}</label><select id="qMethode">${["GET", "POST"].map((m) => `<option ${m === q.methode ? "selected" : ""}>${m}</option>`).join("")}</select></div>
        <div class="feld" data-nicht="keinurl"><label>${esc(Q.kopf)}</label><div id="qKopf">${q.kopf.map((k) => `<div class="zeile qkopf"><input type="text" name="kn" value="${esc(k.name)}" placeholder="Name" aria-label="Name" class="b120">
            <input type="${k.geheim ? "password" : "text"}" name="kw" value="${esc(k.wert)}" placeholder="Wert" aria-label="Wert" autocomplete="off" class="b160">
            <label><input type="checkbox" name="kg" ${k.geheim ? "checked" : ""}> ${esc(Q.geheim)}</label><button type="button" class="knopf gefahr klein" name="kx" aria-label="${esc(Q.loeschen)}">✕</button></div>`).join("")}</div>
          <div class="zeile"><button type="button" class="knopf klein" id="qKopfNeu">${esc(Q.kopfNeu)}</button></div><p class="leise">${esc(Q.geheimHinweis)}</p></div>
        <div class="feld" id="qInhaltZeile" ${q.methode === "POST" ? "" : "hidden"}><label for="qInhalt">${esc(Q.inhalt)}</label><textarea id="qInhalt" rows="4" class="voll" spellcheck="false">${esc(q.inhalt)}</textarea></div>
      </details>
      ${opt.hinweise && opt.hinweise.length ? `<p class="warn">${esc(Q.hinweise)}: ${esc(opt.hinweise.join(" · "))}</p>` : ""}
      <div class="zeile"><button type="button" class="knopf" id="qTest">${esc(Q.weiterTesten)}</button><button type="button" class="knopf haupt" id="qOk">${esc(Q.speichern)}</button>
</div>
      <div id="qTestErg"></div>`;
    verdrahten();
  };
  const lesen = () => {
    q.name = $("#qName").value.trim(); q.id = $("#qId").value.trim().toLowerCase();
    q.art = $("#qArt").value; q.methode = $("#qMethode").value; q.url = $("#qUrl").value.trim();
    q.intervall_s = Math.max(30, Math.round(Number($("#qIv").value) * Number($("#qIvE").value)));
    q.format = $("#qFormat").value;
    q.aktiv = z.querySelector("[name=qAktiv]").checked;
    q.kopf = [...z.querySelectorAll(".qkopf")].map((r) => ({ name: r.querySelector("[name=kn]").value.trim(), wert: r.querySelector("[name=kw]").value,
                                                            geheim: r.querySelector("[name=kg]").checked })).filter((k) => k.name);
    q.inhalt = $("#qInhalt").value;
    q.herkunft = q.art === "video" || q.art === "bild" ? "url" : $("#qHerkunft").value;
    if (q.art === "csv" && csvImp) {
      const k = {};
      z.querySelectorAll("#qCsvKal select").forEach((s) => { k[s.name] = s.value; });
      q.csv = Object.assign(csvImp.optionen(), { kalender: k });
    }
    if (!q.id) q.id = (q.name || "quelle").toLowerCase().normalize("NFD").replace(/[^a-z0-9]/g, "").slice(0, 16) || "quelle";
    if (q.id.length < 2) q.id = (q.id + "_q").slice(0, 16);
    return q;
  };
  const lesenOhneCsv = () => { const alt = csvImp; csvImp = null; const r = lesen(); csvImp = alt; return JSON.parse(JSON.stringify(r)); };
  const verdrahten = () => {
    $("#qMethode").onchange = () => { $("#qInhaltZeile").hidden = $("#qMethode").value !== "POST"; };
    const artZeigen = () => {                    // Video: kein Intervall/keine Methode, dafür Format; Datei: keine Adresse/Kopfzeilen
      const art = $("#qArt").value, v = art === "video", nurUrl = v || art === "bild";
      if (nurUrl) $("#qHerkunft").value = "url";
      $("#qHerkunft").disabled = nurUrl;
      const datei = $("#qHerkunft").value === "datei", so = $("#qHerkunft").value === "speicherort";
      const zeigen = { video: v, datei, so, keinurl: datei || so, csv: art === "csv" };
      z.querySelectorAll("[data-nur]").forEach((x) => { x.hidden = !zeigen[x.dataset.nur]; });
      z.querySelectorAll("[data-nicht]").forEach((x) => { x.hidden = zeigen[x.dataset.nicht]; });
      $("#qMethode").disabled = v || datei || so;
    };
    $("#qArt").onchange = () => { lesen(); zeichnen(); if (q.art === "csv" && ["datei", "speicherort"].includes(q.herkunft)) csvStarten(); };
    soLaden().then((d) => { const o = $("#qHerkunft") && $("#qHerkunft").querySelector('[value="speicherort"]'); if (o && !d.orte.length && q.herkunft !== "speicherort") o.remove(); }).catch(() => {});
    $("#qHerkunft").onchange = () => { artZeigen(); csvImp = null; $("#qCsv").innerHTML = ""; if ($("#qArt").value === "csv") csvStarten(); };
    artZeigen();
    $("#qCsvLesen").onclick = (ev) => aktion(ev.target, csvStarten, null);
    $("#qDatei").onchange = (ev) => aktion(null, async () => {
      const f = ev.target.files[0]; if (!f) return;
      const r = await senden("/api/quellen/datei", { name: f.name, daten: await dateiBase64(f, 1000000) });
      lesen(); q.datei = r.datei;
      if (!["json", "text", "rss", "ical", "csv"].includes(q.art) || q.art !== r.art) q.art = r.art;
      if (!q.name) q.name = f.name.replace(/\.[^.]+$/, "").slice(0, 40);
      if (q.art === "csv") q.csv = { kalender: (q.csv && q.csv.kalender) || {} };     // neue Datei: Trennzeichen und Spalten neu erkennen
      csvImp = null; zeichnen(); if (q.art === "csv") csvStarten();
    }, null);
    $("#qSoWahl").onclick = async () => {        // seit 0.48: Datei in einem Speicherort, bei jedem Abruf neu gelesen
      const w = await soWaehlen({ filter: /\.(ics|csv|tsv|txt|json|xml|rss|atom)$/i });
      if (!w || !w.length) return;
      lesen(); q.speicherort = { ort: w[0].ort, pfad: w[0].pfad };
      const art = { ics: "ical", csv: "csv", tsv: "csv", json: "json", xml: "rss", rss: "rss", atom: "rss", txt: "text" }[w[0].name.split(".").pop().toLowerCase()];
      if (art) q.art = art;
      if (!q.name) q.name = w[0].name.replace(/\.[^.]+$/, "").slice(0, 40);
      if (q.art === "csv") q.csv = { kalender: (q.csv && q.csv.kalender) || {} };
      csvImp = null; zeichnen(); if (q.art === "csv") csvStarten();
    };
    $("#qName").onchange = () => { if (!altId && !$("#qId").value) $("#qId").value = $("#qName").value.toLowerCase().normalize("NFD").replace(/[^a-z0-9]/g, "").slice(0, 16); };
    z.querySelectorAll("[name=kg]").forEach((c) => { c.onchange = () => { c.closest(".qkopf").querySelector("[name=kw]").type = c.checked ? "password" : "text"; }; });
    z.querySelectorAll("[name=kx]").forEach((b) => { b.onclick = () => { b.closest(".qkopf").remove(); lesen(); zeichnen(); }; });
    $("#qKopfNeu").onclick = () => { lesen(); q.kopf.push({ name: "", wert: "", geheim: false }); zeichnen(); z.querySelector(".erweitert").open = true; };
    $("#qTest").onclick = (ev) => aktion(ev.target, async () => {
      const r = await senden("/api/quellen/test", { quelle: lesen() }).catch((e) => ({ ok: false, fehler: e.message }));
      const ziel = $("#qTestErg");
      if (opt.beimTest) opt.beimTest(!!r.ok);
      if (!r.ok) { ziel.innerHTML = `<p class="schlecht">${esc(r.fehler)}</p>`; return; }
      ziel.innerHTML = `<p class="gut">✓ ${esc(Q.testOk(r.dauer_ms))}</p>${r.bild ? `<img src="${esc(r.bild)}" alt="" class="testbild">` : ""}
        <h3>${esc(Q.antwort)}</h3><div id="qBaum"></div>`;
      baumZeigen($("#qBaum"), r.daten, (p) => pfadHinweis(ziel, q.id, p));
      ziel.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }, null);
    $("#qOk").onclick = (ev) => aktion(ev.target, async () => {
      lesen();
      const rest = E.quellen.filter((x) => x.id !== altId);
      if (rest.some((x) => x.id === q.id)) throw new Error(`${q.id}: ${Q.kennung}`);
      const liste = altId ? E.quellen.map((x) => (x.id === altId ? q : x)) : [...rest, q];
      await quellenSpeichern(liste);
      if (opt.gespeichert) opt.gespeichert(q);
      else seitenfeldZu();
    });
  };
  // CSV (seit 0.26): Spalten über den allgemeinen Import wählen (csvimport.js), danach die Spalten für Termine
  const kalZeichnen = (felder) => {
    const k = (q.csv && q.csv.kalender) || {};
    const sel = (name, label) => `<div class="feld"><label>${esc(label)}</label><select name="${name}"><option value="">${esc(Q.ohne)}</option>
      ${felder.map((f) => `<option value="${esc(f)}" ${f === k[name] ? "selected" : ""}>${esc(f)}</option>`).join("")}</select></div>`;
    $("#qCsvKal").innerHTML = sel("datum", Q.tDatum) + sel("zeit", Q.tZeit) + sel("titel", Q.tTitel) + sel("ort", Q.tOrt);
    $("#qCsvKal").querySelectorAll("select").forEach((s) => { s.onchange = () => { lesen(); }; });
  };
  const csvStarten = async () => {
    const h = $("#qHerkunft").value;
    const herkunft = h === "datei" ? (q.datei ? { datei: q.datei.hash } : null) : h === "speicherort" ? (q.speicherort ? { speicherort: q.speicherort } : null)
      : { quelle: Object.assign({}, lesenOhneCsv(), { art: "text" }) };
    if (!herkunft) return;
    try {
      csvImp = await csvImport($("#qCsv"), herkunft, q.csv || {}, (o) => { q.csv = Object.assign(o, { kalender: (q.csv && q.csv.kalender) || {} }); kalZeichnen(o.felder.map((f) => f.name)); });
    } catch (e) { csvImp = null; }
  };
  zeichnen();
  if (q.art === "csv" && (q.herkunft === "datei" ? q.datei : q.herkunft === "speicherort" ? q.speicherort : q.csv && q.csv.felder && q.csv.felder.length)) csvStarten();
}
