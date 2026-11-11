// SignageCast – Reiter „Datenquellen“: eigene API-Abfragen (JSON/Text), RSS-/Atom-Feeds und Bilder. Der Datendienst
// holt sie im eingestellten Abstand; die Bausteine im Layout zeigen Werte daraus (Pfad aus dem Antwort-Baum wählen).
// Nutzt die Hilfsfunktionen aus tv.js (holen, senden, aktion, esc, el, $, schalter, melden, E).
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
    herkunft: "Herkunft", herkunftName: { url: "Adresse abrufen", datei: "Datei hochladen" }, datei: "Datei (bis 1 MB)",
    dateiHinweis: "Zum Beispiel der Abfuhrkalender deiner Stadt als .ics oder .csv, wenn es keine Abo-Adresse gibt. Neue Termine: Datei wieder hochladen.",
    hochgeladen: "hochgeladen", felderLesen: "Spalten lesen", csvFelder: "Spalten der CSV",
    termine: "Als Termine (für den Baustein „Kalender / Müllabfuhr“)", termineHinweis: "Datumsspalte wählen – dann zeigt der Kalender-Baustein die Zeilen als Termine. Vergangene fallen weg.",
    tDatum: "Datum", tZeit: "Uhrzeit (leer = ganztägig oder aus der Datumsspalte)", tTitel: "Titel", tOrt: "Ort", ohne: "– keine –",
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
    herkunft: "Source", herkunftName: { url: "Fetch address", datei: "Upload file" }, datei: "File (up to 1 MB)",
    dateiHinweis: "For example your town's waste collection calendar as .ics or .csv when there is no subscription address. New dates: upload the file again.",
    hochgeladen: "uploaded", felderLesen: "Read columns", csvFelder: "CSV columns",
    termine: "As events (for the “Calendar / waste collection” element)", termineHinweis: "Choose the date column – the calendar element then shows the rows as events. Past ones are dropped.",
    tDatum: "Date", tZeit: "Time (empty = all day or from the date column)", tTitel: "Title", tOrt: "Location", ohne: "– none –",
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

async function quellenSeite(inhalt) {
  const Q = QT();
  let bearbeitet = null;            // Kopie der Quelle im Editor (null = keiner offen)
  let altId = null;
  inhalt.innerHTML = `<div class="karte"><p class="leise">${esc(Q.text)}</p>
      <div class="zeile"><button class="knopf haupt" id="qNeu">${esc(Q.neu)}</button><button class="knopf" id="qCurl">${esc(Q.ausCurl)}</button>
        <select id="qBsp"><option value="">${esc(Q.beispiel)}</option>${Object.keys(QBEISPIELE).map((k) => `<option value="${k}">${esc(Q.beispiele[k])}</option>`).join("")}</select></div>
      <div id="qCurlBox" hidden><p class="leise">${esc(Q.curlText)}</p><textarea id="qCurlText" rows="5" class="voll" spellcheck="false"></textarea>
        <div class="zeile"><button class="knopf haupt" id="qCurlOk">${esc(Q.uebernehmen)}</button></div></div></div>
    <div id="qEditor"></div><div id="qListe"></div>`;

  const liste = async () => {
    const st = (await holen("/api/quellen/status")).status || {};
    const ziel = $("#qListe");
    if (!E.quellen.length) { ziel.innerHTML = `<p class="leise">${esc(Q.keine)}</p>`; return; }
    ziel.innerHTML = E.quellen.map((q) => {
      const s = st[q.id] || {};
      const iv = q.intervall_s % 3600 === 0 ? `${q.intervall_s / 3600} h` : q.intervall_s % 60 === 0 ? `${q.intervall_s / 60} min` : `${q.intervall_s} s`;
      return `<div class="karte" data-id="${esc(q.id)}"><h2>${esc(q.name)} <span class="leise">· ${esc(q.id)} · ${esc(Q.artName[q.art])}${q.art === "video" ? "" : " · " + iv}${q.aktiv ? "" : " · –"}</span></h2>
        <div class="leise umbruch">${q.herkunft === "datei" ? "📄 " + esc(q.datei ? q.datei.name : "") : (q.art === "video" ? "" : esc(q.methode) + " ") + esc(q.url)}</div>
        <div class="leise">${esc(Q.letzter)}: ${esc(zeitText(s.abruf))}${s.dauer_ms != null ? ` (${s.dauer_ms} ${Q.ms})` : ""} · ${esc(Q.naechster)}: ${esc(zeitText(s.naechster))}
          ${s.fehler ? `<br><span class="schlecht">${esc(Q.fehler)}: ${esc(meldungText(s.fehler_m, s.fehler))}${s.versuche ? ` (${s.versuche} ${esc(Q.versuche)})` : ""}</span>` : ""}</div>
        <div class="zeile"><button class="knopf" data-a="bearbeiten">${esc(Q.bearbeiten)}</button><button class="knopf" data-a="daten">${esc(Q.daten)}</button>
          <button class="knopf" data-a="jetzt">${esc(Q.jetzt)}</button><button class="knopf gefahr" data-a="loeschen">${esc(Q.loeschen)}</button></div>
        <div class="qDaten"></div></div>`;
    }).join("");
    ziel.querySelectorAll("[data-a]").forEach((k) => {
      const karte = k.closest(".karte"), id = karte.dataset.id, q = E.quellen.find((x) => x.id === id);
      k.onclick = (ev) => {
        const a = k.dataset.a;
        if (a === "bearbeiten") { oeffnen(JSON.parse(JSON.stringify(q)), id); return; }
        if (a === "daten") return aktion(ev.target, () => pfadWaehlen(karte.querySelector(".qDaten"), id, (p) => pfadGewaehlt(id, p, karte.querySelector(".qDaten"))), null);
        if (a === "jetzt") return aktion(ev.target, async () => { await senden("/api/quellen/jetzt", { id }); setTimeout(() => liste().catch(() => {}), 3000); }, null);
        if (a === "loeschen") {
          if (!confirm(Q.wirklichLoeschen)) return;
          return aktion(ev.target, async () => { await speichernListe(E.quellen.filter((x) => x.id !== id)); });
        }
      };
    });
  };
  const pfadGewaehlt = (id, p, ziel) => {
    if (navigator.clipboard) navigator.clipboard.writeText(p).catch(() => {});      // geht nur im Fokus / über HTTPS
    const hinweis = el(`<p class="gut">${esc(Q.platzhalterHilfe(id, p))}</p>`);
    ziel.prepend(hinweis);
    melden(Q.kopiert);
  };
  const speichernListe = async (neu) => {
    const d = await senden("/api/einstellungen", { quellen: neu });
    E = d.einstellungen;
    await liste();
  };

  // ---------- Editor ----------
  const oeffnen = (q, id) => {
    bearbeitet = Object.assign({ id: "", name: "", art: "json", url: "https://", methode: "GET", kopf: [], inhalt: "", intervall_s: 300, aktiv: true, format: "auto", herkunft: "url", datei: null, csv: null }, q);
    altId = id;
    zeichnen();
    $("#qEditor").scrollIntoView({ behavior: "smooth" });
  };
  const einheitVon = (s) => (s % 3600 === 0 ? 3600 : s % 60 === 0 ? 60 : 1);
  const zeichnen = () => {
    const q = bearbeitet, z = $("#qEditor");
    let csvImp = null;
    if (!q) { z.innerHTML = ""; return; }
    const ein = einheitVon(q.intervall_s);
    z.innerHTML = `<div class="karte"><h2>${esc(altId ? q.name : Q.neu)}</h2>
      <div class="zeile"><label>${esc(Q.name)}</label><input type="text" id="qName" value="${esc(q.name)}"></div>
      <div class="zeile"><label>${esc(Q.kennung)}</label><input type="text" id="qId" value="${esc(q.id)}" class="b160" pattern="[a-z0-9_]{2,16}"></div>
      <div class="zeile"><label>${esc(Q.art)}</label><select id="qArt">${Object.keys(Q.artName).map((k) => `<option value="${k}" ${k === q.art ? "selected" : ""}>${esc(Q.artName[k])}</option>`).join("")}</select>
        <label>${esc(Q.methode)}</label><select id="qMethode">${["GET", "POST"].map((m) => `<option ${m === q.methode ? "selected" : ""}>${m}</option>`).join("")}</select></div>
      <div class="zeile" data-nicht="video"><label>${esc(Q.herkunft)}</label><select id="qHerkunft">${Object.keys(Q.herkunftName).map((k) =>
        `<option value="${k}" ${k === q.herkunft ? "selected" : ""}>${esc(Q.herkunftName[k])}</option>`).join("")}</select></div>
      <div data-nur="datei"><div class="zeile"><label>${esc(Q.datei)}</label><input type="file" id="qDatei" accept=".ics,.csv,.tsv,.txt,.json,.xml,text/calendar,text/csv">
        <span class="leise" id="qDateiStand">${q.datei ? "✓ " + esc(q.datei.name) : ""}</span></div><p class="leise">${esc(Q.dateiHinweis)}</p></div>
      <div class="zeile" data-nicht="datei"><label>${esc(Q.url)}</label><input type="text" id="qUrl" value="${esc(q.url)}" class="voll640" spellcheck="false"></div>
      <div class="zeile" data-nur="video"><label>${esc(Q.format)}</label><select id="qFormat">${Object.keys(Q.formatName).map((k) => `<option value="${k}" ${k === q.format ? "selected" : ""}>${esc(Q.formatName[k])}</option>`).join("")}</select></div>
      <p class="leise" data-nur="video">${esc(Q.videoHinweis)}</p>
      <div class="zeile" data-nicht="video"><label>${esc(Q.intervall)}</label><input type="number" id="qIv" min="1" value="${q.intervall_s / ein}">
        <select id="qIvE">${[1, 60, 3600].map((e) => `<option value="${e}" ${e === ein ? "selected" : ""}>${esc(Q.einheit[e])}</option>`).join("")}</select>
        <label>${esc(Q.aktiv)}</label>${schalter("qAktiv", q.aktiv)}</div>
      <div data-nur="csv"><h3>${esc(Q.csvFelder)}</h3><div class="zeile" data-nicht="datei"><button class="knopf" id="qCsvLesen">${esc(Q.felderLesen)}</button></div>
        <div id="qCsv"></div><h3>${esc(Q.termine)}</h3><p class="leise">${esc(Q.termineHinweis)}</p><div id="qCsvKal"></div></div>
      <div data-nicht="datei"><h3>${esc(Q.kopf)}</h3><div id="qKopf">${q.kopf.map((k) => `<div class="zeile kopfzeile"><input type="text" name="kn" value="${esc(k.name)}" placeholder="Name" class="b180">
          <input type="${k.geheim ? "password" : "text"}" name="kw" value="${esc(k.wert)}" placeholder="Wert" autocomplete="off" class="b280">
          <label><input type="checkbox" name="kg" ${k.geheim ? "checked" : ""}> ${esc(Q.geheim)}</label><button class="knopf gefahr" name="kx">✕</button></div>`).join("")}</div>
      <div class="zeile"><button class="knopf" id="qKopfNeu">${esc(Q.kopfNeu)}</button></div><p class="leise">${esc(Q.geheimHinweis)}</p></div>
      <div id="qInhaltZeile" ${q.methode === "POST" ? "" : "hidden"}><label>${esc(Q.inhalt)}</label><textarea id="qInhalt" rows="4" class="voll" spellcheck="false">${esc(q.inhalt)}</textarea></div>
      <div class="zeile"><button class="knopf" id="qTest">${esc(Q.testen)}</button><button class="knopf haupt" id="qOk">${esc(Q.speichern)}</button>
        <button class="knopf" id="qWeg">${esc(Q.abbrechen)}</button></div>
      <div id="qTestErg"></div></div>`;
    const lesen = () => {
      q.name = $("#qName").value.trim(); q.id = $("#qId").value.trim().toLowerCase();
      q.art = $("#qArt").value; q.methode = $("#qMethode").value; q.url = $("#qUrl").value.trim();
      q.intervall_s = Math.max(30, Math.round(Number($("#qIv").value) * Number($("#qIvE").value)));
      q.format = $("#qFormat").value;
      q.aktiv = z.querySelector("[name=qAktiv]").checked;
      q.kopf = [...z.querySelectorAll(".kopfzeile")].map((r) => ({ name: r.querySelector("[name=kn]").value.trim(), wert: r.querySelector("[name=kw]").value,
                                                                  geheim: r.querySelector("[name=kg]").checked })).filter((k) => k.name);
      q.inhalt = $("#qInhalt").value;
      q.herkunft = q.art === "video" || q.art === "bild" ? "url" : $("#qHerkunft").value;
      if (q.art === "csv" && csvImp) {
        const k = {};
        z.querySelectorAll("#qCsvKal select").forEach((s) => { k[s.name] = s.value; });
        q.csv = Object.assign(csvImp.optionen(), { kalender: k });
      }
      if (!q.id) q.id = (q.name || "quelle").toLowerCase().normalize("NFD").replace(/[^a-z0-9]/g, "").slice(0, 16) || "quelle";
      return q;
    };
    $("#qMethode").onchange = () => { $("#qInhaltZeile").hidden = $("#qMethode").value !== "POST"; };
    const artZeigen = () => {                    // Video: kein Intervall/keine Methode, dafür Format; Datei: keine Adresse/Kopfzeilen
      const art = $("#qArt").value, v = art === "video", nurUrl = v || art === "bild";
      if (nurUrl) $("#qHerkunft").value = "url";
      $("#qHerkunft").disabled = nurUrl;
      const datei = $("#qHerkunft").value === "datei";
      const zeigen = { video: v, datei, csv: art === "csv" };
      z.querySelectorAll("[data-nur]").forEach((x) => { x.hidden = !zeigen[x.dataset.nur]; });
      z.querySelectorAll("[data-nicht]").forEach((x) => { x.hidden = zeigen[x.dataset.nicht]; });
      $("#qMethode").disabled = v || datei;
    };
    $("#qArt").onchange = () => { artZeigen(); if ($("#qArt").value === "csv" && !csvImp && $("#qHerkunft").value === "datei") csvStarten(); };
    $("#qHerkunft").onchange = () => { artZeigen(); csvImp = null; $("#qCsv").innerHTML = ""; if ($("#qArt").value === "csv") csvStarten(); };
    artZeigen();
    // CSV (seit 0.26): Spalten über den allgemeinen Import wählen (csvimport.js), danach die Spalten für Termine
    const kalZeichnen = (felder) => {
      const k = (q.csv && q.csv.kalender) || {};
      const sel = (name, label) => `<div class="zeile"><label>${esc(label)}</label><select name="${name}"><option value="">${esc(Q.ohne)}</option>
        ${felder.map((f) => `<option value="${esc(f)}" ${f === k[name] ? "selected" : ""}>${esc(f)}</option>`).join("")}</select></div>`;
      $("#qCsvKal").innerHTML = sel("datum", Q.tDatum) + sel("zeit", Q.tZeit) + sel("titel", Q.tTitel) + sel("ort", Q.tOrt);
      $("#qCsvKal").querySelectorAll("select").forEach((s) => { s.onchange = () => { lesen(); }; });
    };
    const csvStarten = async () => {
      const herkunft = $("#qHerkunft").value === "datei" ? (q.datei ? { datei: q.datei.hash } : null) : { quelle: Object.assign({}, lesenOhneCsv(), { art: "text" }) };
      if (!herkunft) return;
      try {
        csvImp = await csvImport($("#qCsv"), herkunft, q.csv || {}, (o) => { q.csv = Object.assign(o, { kalender: (q.csv && q.csv.kalender) || {} }); kalZeichnen(o.felder.map((f) => f.name)); });
      } catch (e) { csvImp = null; }
    };
    const lesenOhneCsv = () => { const alt = csvImp; csvImp = null; const r = lesen(); csvImp = alt; return JSON.parse(JSON.stringify(r)); };
    $("#qCsvLesen").onclick = (ev) => aktion(ev.target, csvStarten, null);
    $("#qDatei").onchange = (ev) => aktion(null, async () => {
      const f = ev.target.files[0]; if (!f) return;
      const r = await senden("/api/quellen/datei", { name: f.name, daten: await dateiBase64(f, 1000000) });
      lesen(); q.datei = r.datei;
      if (!["json", "text", "rss", "ical", "csv"].includes(q.art) || q.art !== r.art) q.art = r.art;
      if (!q.name) q.name = f.name.replace(/\.[^.]+$/, "").slice(0, 40);
      if (q.art === "csv") q.csv = { kalender: (q.csv && q.csv.kalender) || {} };     // neue Datei: Trennzeichen und Spalten neu erkennen
      csvImp = null; zeichnen();
    }, null);
    if (q.art === "csv" && (q.herkunft === "datei" ? q.datei : q.csv && q.csv.felder && q.csv.felder.length)) csvStarten();
    $("#qName").onchange = () => { if (!$("#qId").value) $("#qId").value = $("#qName").value.toLowerCase().normalize("NFD").replace(/[^a-z0-9]/g, "").slice(0, 16); };
    z.querySelectorAll("[name=kg]").forEach((c) => { c.onchange = () => { c.closest(".kopfzeile").querySelector("[name=kw]").type = c.checked ? "password" : "text"; }; });
    z.querySelectorAll("[name=kx]").forEach((b) => { b.onclick = () => { lesen(); b.closest(".kopfzeile").remove(); lesen(); zeichnen(); }; });
    $("#qKopfNeu").onclick = () => { lesen(); q.kopf.push({ name: "", wert: "", geheim: false }); zeichnen(); };
    $("#qWeg").onclick = () => { bearbeitet = null; zeichnen(); };
    $("#qTest").onclick = (ev) => aktion(ev.target, async () => {
      const r = await senden("/api/quellen/test", { quelle: lesen() }).catch((e) => ({ ok: false, fehler: e.message }));
      const ziel = $("#qTestErg");
      if (!r.ok) { ziel.innerHTML = `<p class="schlecht">${esc(r.fehler)}</p>`; return; }
      ziel.innerHTML = `<p class="gut">OK · ${r.dauer_ms} ${esc(Q.ms)}</p>${r.bild ? `<img src="${esc(r.bild)}" alt="" class="testbild">` : ""}
        <h3>${esc(Q.antwort)}</h3><div id="qBaum"></div>`;
      baumZeigen($("#qBaum"), r.daten, (p) => pfadGewaehlt(q.id, p, $("#qTestErg")));
    }, null);
    $("#qOk").onclick = (ev) => aktion(ev.target, async () => {
      lesen();
      const rest = E.quellen.filter((x) => x.id !== altId);
      if (rest.some((x) => x.id === q.id)) throw new Error(`${q.id}: ${Q.kennung}`);
      await speichernListe([...rest, q]);
      bearbeitet = null; zeichnen();
    });
  };

  $("#qNeu").onclick = () => oeffnen({}, null);
  $("#qCurl").onclick = () => { $("#qCurlBox").hidden = !$("#qCurlBox").hidden; };
  $("#qCurlOk").onclick = (ev) => aktion(ev.target, async () => {
    const r = await senden("/api/quellen/curl", { befehl: $("#qCurlText").value }).catch((e) => ({ ok: false, fehler: e.message }));
    if (!r.ok) throw new Error(r.fehler);
    $("#qCurlBox").hidden = true; $("#qCurlText").value = "";
    oeffnen(r.quelle, null);
    if (r.hinweise && r.hinweise.length) $("#qTestErg").innerHTML = `<p class="warn">${esc(Q.hinweise)}: ${esc(r.hinweise.join(" · "))}</p>`;
  }, null);
  $("#qBsp").onchange = () => {
    const b = QBEISPIELE[$("#qBsp").value]; $("#qBsp").value = "";
    if (b) oeffnen(JSON.parse(JSON.stringify(b)), null);
  };
  await liste();
  timer = setInterval(() => { if (!bearbeitet) liste().catch(() => {}); }, 15000);
}
