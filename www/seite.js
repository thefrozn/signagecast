// SignageCast – TV-Seite. Baut das Bild aus dem Layout des Fernsehers (Raster 48 x 27 à 40 px) und füllt die
// Bausteine mit Werten aus /daten.json?tv=<kennung> (alle 15 s). Live-Video über player.js, Radio über <audio>.
// Wechselt das Layout (Verwaltung oder Zeitplan), wird die Fläche neu gebaut – ohne Neustart des Streams.
const RASTER = 40;
const BILDER = { "sunny": "sunny", "clear-night": "clear-night", "partlycloudy": "partlycloudy", "cloudy": "cloudy",
  "exceptional": "cloudy", "fog": "fog", "rainy": "rainy", "pouring": "rainy", "lightning": "lightning",
  "lightning-rainy": "lightning", "hail": "snowy", "snowy": "snowy", "snowy-rainy": "snowy", "windy": "windy",
  "windy-variant": "windy" };
const SYMBOL = { "clear-night": "weather-night", "cloudy": "weather-cloudy", "exceptional": "alert-circle-outline",
  "fog": "weather-fog", "hail": "weather-hail", "lightning": "weather-lightning", "lightning-rainy": "weather-lightning-rainy",
  "partlycloudy": "weather-partly-cloudy", "pouring": "weather-pouring", "rainy": "weather-rainy", "snowy": "weather-snowy",
  "snowy-rainy": "weather-snowy-rainy", "sunny": "weather-sunny", "windy": "weather-windy", "windy-variant": "weather-windy-variant" };
const TEXTE = {
  de: { lage: { "clear-night": "Klare Nacht", "cloudy": "Bewölkt", "exceptional": "Außergewöhnlich", "fog": "Nebel",
          "hail": "Hagel", "lightning": "Gewitter", "lightning-rainy": "Gewitter, Regen", "partlycloudy": "Teilweise bewölkt",
          "pouring": "Starkregen", "rainy": "Regnerisch", "snowy": "Schnee", "snowy-rainy": "Schneeregen", "sunny": "Sonnig",
          "windy": "Windig", "windy-variant": "Windig, bewölkt" },
        feuchte: "Luftfeuchte", wind: "Wind", keinStream: "Gerade kein Live-Stream", naechstes: "Als Nächstes", wetterQuelle: "Wetterdaten: MET Norway",
        heute: "Heute", morgen: "Morgen", keineTermine: "Keine Termine", locale: "de-DE" },
  en: { lage: { "clear-night": "Clear night", "cloudy": "Cloudy", "exceptional": "Exceptional", "fog": "Fog", "hail": "Hail",
          "lightning": "Thunderstorm", "lightning-rainy": "Thunderstorm, rain", "partlycloudy": "Partly cloudy",
          "pouring": "Pouring", "rainy": "Rainy", "snowy": "Snowy", "snowy-rainy": "Sleet", "sunny": "Sunny",
          "windy": "Windy", "windy-variant": "Windy, cloudy" },
        feuchte: "Humidity", wind: "Wind", keinStream: "No live stream right now", naechstes: "Up next", wetterQuelle: "Weather data: MET Norway",
        heute: "Today", morgen: "Tomorrow", keineTermine: "No events", locale: "en-GB" },
};
const FAKTOR = { uhr: 0.82, temperatur: 0.72, datum: 0.5, wetterlage: 0.6, feuchte: 0.5, wind: 0.5, sender: 0.5, text: 0.55, meldung: 0.42 };
let T = TEXTE.de;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const zahl = (w, nachkomma) => {
  const n = Number(w);
  if (w === null || w === undefined || w === "" || isNaN(n)) return w ?? "–";
  return n.toLocaleString(T.locale, { minimumFractionDigits: nachkomma, maximumFractionDigits: nachkomma });
};
const stellen = (einheit, wert) => (!einheit || einheit === "W" || einheit === "%" ? 0 : Math.abs(Number(wert)) >= 100 ? 0 : 1);

const TV = new URLSearchParams(location.search).get("tv") || "tv";
let daten = null, layoutJson = "", bausteine = [], player = null;
const meldungen = {};                         // entity -> {wert, seit}

// ---------- Fläche aus dem Layout bauen ----------
function bauen(layout) {
  const f = $("flaeche");
  f.querySelectorAll(".baustein").forEach((b) => b.remove());
  if (player) { player.stoppen(); player = null; }
  bausteine = [];
  if (layout.schwarz) { f.className = ""; $("hg").style.background = "#000"; return; }
  const th = layout.thema || {};
  f.className = (th.schema || "dunkel") + (layout.hintergrund.art === "wetter" && layout.hintergrund.abdunkeln ? " abdunkeln" : "");
  f.style.setProperty("--akzent", th.akzent || "#3d8cd0");
  f.style.setProperty("--schrift", th.schrift || "Roboto");
  for (const e of layout.elemente) {
    const d = document.createElement("div");
    // Ausrichtung "oben-links" usw.; alte Werte "links"/"mitte"/"rechts" = senkrecht mittig
    const [v, h] = (e.ausrichtung || "links").includes("-") ? e.ausrichtung.split("-") : ["mitte", e.ausrichtung || "links"];
    d.className = `baustein typ-${e.typ} v-${v} h-${h}${e.karte ? " karte" : ""}${e.gewicht ? " " + e.gewicht : ""}`;
    if (e.schrift) d.style.fontFamily = `"${e.schrift}", var(--schrift), sans-serif`;
    if (e.textfarbe) { d.style.color = e.textfarbe; d.style.textShadow = "none"; }
    Object.assign(d.style, { left: e.x * RASTER + "px", top: e.y * RASTER + "px", width: e.w * RASTER - (e.karte && e.typ !== "video" ? 10 : 0) + "px",
                             height: e.h * RASTER - (e.karte && e.typ !== "video" ? 10 : 0) + "px" });
    if (e.typ === "flaeche") {
      const f = e.optionen.farbe || "#f0f0f0", a = (e.optionen.deckkraft ?? 100) / 100;
      d.style.background = `rgba(${parseInt(f.slice(1, 3), 16)}, ${parseInt(f.slice(3, 5), 16)}, ${parseInt(f.slice(5, 7), 16)}, ${a})`;
    }
    if (e.typ === "text") {
      if (e.optionen.laufband) {
        // Laufband: Text läuft von rechts nach links durch, Tempo nach Textlänge (ca. 120 px/s)
        d.classList.add("laufband");
        d.innerHTML = `<span>${esc(e.optionen.text)}</span>`;
      } else {
        d.textContent = e.optionen.text;
        if (e.h >= 3) d.classList.add("mehrzeilig");
      }
    }
    if (e.typ === "logo") d.innerHTML = e.optionen.bild ? `<img src="bild/${esc(e.optionen.bild)}" alt="">` : `<div class="platzhalter">Logo</div>`;
    if (e.typ === "video") {
      if (!e.optionen.leiste) d.classList.add("ohneleiste");
      player = new LivePlayer(d, () => T);
    }
    f.appendChild(d);
    bausteine.push({ e, d, sichtbar: e.sichtbar });
  }
  hintergrund(layout);
}

// Hintergrund: Wetterbild, Bilderset nach Tageszeit (optional mit Wetter oder als Diashow), eigenes Bild (auch je
// Tageszeit) oder Farbe. Tageszeit kommt vom Datendienst (Sonnenstand am Standort). Nachts optional gedimmt.
const STILE = ["natur", "stadt", "himmel", "berge", "meer"];
const SCHLECHTWETTER = ["rainy", "pouring", "snowy", "snowy-rainy", "hail", "fog", "lightning", "lightning-rainy"];
function hintergrund(layout) {
  const hg = layout.hintergrund, h = $("hg");
  const tz = (daten && daten.tageszeit) || "tag";
  const wetter = daten && daten.wetter.zustand;
  const wetterbild = () => `bilder/${BILDER[wetter] || "cloudy"}.jpg`;
  const stil = () => {
    if (hg.stil !== "gemischt") return hg.stil;
    const tag = Math.floor(Date.now() / 86400000);           // gemischt: jeden Tag ein anderer Stil
    return STILE[tag % STILE.length];
  };
  let url = null;
  if (hg.art === "farbe") { h.style.backgroundImage = "none"; h.style.backgroundColor = hg.farbe; }
  else if (hg.art === "bild") {
    const b = (hg.bilder_tageszeit || {})[tz] || hg.bild;
    url = b ? `bild/${b}` : wetterbild();
  } else if (hg.art === "stil") {
    if (hg.wechsel === "diashow") {
      const alle = hg.stil === "gemischt" ? STILE.flatMap((s) => ["morgen", "tag", "abend", "nacht"].map((z) => `${s}-${z}`))
                                          : ["morgen", "tag", "abend", "nacht"].map((z) => `${hg.stil}-${z}`);
      url = `bilder/stile/${alle[Math.floor(Date.now() / (hg.diashow_min * 60000)) % alle.length]}.jpg`;
    } else if (hg.wechsel === "tageszeit_wetter" && SCHLECHTWETTER.includes(wetter) && tz !== "nacht") {
      url = wetterbild();
    } else {
      url = `bilder/stile/${stil()}-${tz}.jpg`;
    }
  } else url = wetterbild();
  if (url) { const css = `url("${url}")`; if (h.style.backgroundImage !== css) h.style.backgroundImage = css; }
  // Bereich (Raster), Füllart und Ausschnitt; außerhalb des Bereichs die Hintergrundfarbe
  const b = hg.bereich || { x: 0, y: 0, w: 48, h: 27 };
  for (const el of [h, $("verlauf")]) Object.assign(el.style, { left: b.x * RASTER + "px", top: b.y * RASTER + "px", width: b.w * RASTER + "px", height: b.h * RASTER + "px" });
  h.style.backgroundSize = { fuellen: "cover", einpassen: "contain", strecken: "100% 100%" }[hg.anpassung] || "cover";
  h.style.backgroundPosition = { mitte: "center", oben: "center top", unten: "center bottom", links: "left center", rechts: "right center" }[hg.ausschnitt] || "center";
  if (hg.art !== "farbe") h.style.backgroundColor = "transparent";
  document.body.style.background = hg.farbe || "#000";
  h.style.filter = hg.nachts_dunkler ? { nacht: "brightness(.55)", abend: "brightness(.8)", morgen: "brightness(.85)" }[tz] || "none" : "none";
}

// Schrift so groß wie die Box erlaubt (Faktor je Typ), dann verkleinern, bis der Text in die Breite passt
function einpassen(d, faktor) {
  // Zum Messen linksbündig: Text, der nach links übersteht (rechts/mittig ausgerichtet), zählt sonst nicht als Überlauf
  const ausrichtung = d.style.alignItems;
  d.style.alignItems = "flex-start";
  let groesse = Math.max(10, d.clientHeight * faktor);
  d.style.fontSize = groesse + "px";
  for (let i = 0; i < 20 && d.scrollWidth > d.clientWidth + 1; i++) { groesse *= 0.9; d.style.fontSize = groesse + "px"; }
  d.style.alignItems = ausrichtung;
}

// Mehrzeiliger Text: so groß wie möglich, bis er in Breite und Höhe passt
function einpassenMehrzeilig(d) {
  let groesse = Math.min(d.clientHeight * 0.4, 90);
  d.style.fontSize = groesse + "px";
  for (let i = 0; i < 25 && (d.scrollHeight > d.clientHeight + 1 || d.scrollWidth > d.clientWidth + 1); i++) { groesse *= 0.92; d.style.fontSize = groesse + "px"; }
}

function laufband(d) {
  if (d.dataset.laeuft) return;
  d.dataset.laeuft = 1;
  d.style.fontSize = d.clientHeight * 0.5 + "px";
  const sp = d.querySelector("span");
  const weg = sp.offsetWidth + d.clientWidth;
  sp.style.animationDuration = Math.max(8, weg / 120) + "s";
}

function bedingungErfuellt(b) {
  if (!b) return true;
  const w = (daten.werte[b.entity] || {}).state;
  if (w === undefined) return false;
  const an = ["on", "open", "home", "true", "playing", "detected", "unlocked"].includes(String(w).toLowerCase());
  switch (b.op) {
    case "=": return String(w) === b.wert;
    case "!=": return String(w) !== b.wert;
    case ">": return Number(w) > Number(b.wert);
    case "<": return Number(w) < Number(b.wert);
    case "an": return an;
    case "aus": return !an;
  }
  return true;
}

function wert(entity, feld) {
  const w = daten.werte[entity] || {};
  return feld ? w[feld] : w.state;
}

// ---------- Werte eintragen ----------
function fuellen() {
  const w = daten.wetter || {};
  for (const b of bausteine) {
    const { e, d } = b;
    const o = e.optionen;
    let sichtbar = e.sichtbar && bedingungErfuellt(e.bedingung);
    switch (e.typ) {
      case "temperatur": {
        const t = o.entity && !o.entity.startsWith("weather.") ? wert(o.entity) : (o.entity ? wert(o.entity, "temperature") : w.temperatur);
        d.textContent = t != null ? `${zahl(t, 1)} °C` : ""; break;
      }
      case "wetterlage": { const z = o.entity ? wert(o.entity) : w.zustand; d.textContent = T.lage[z] || z || ""; break; }
      case "feuchte": {
        const f = o.entity && !o.entity.startsWith("weather.") ? wert(o.entity) : (o.entity ? wert(o.entity, "humidity") : w.feuchte);
        d.textContent = f != null ? `${T.feuchte} ${zahl(f, 0)} %` : ""; break;
      }
      case "wind": {
        const v = o.entity && !o.entity.startsWith("weather.") ? wert(o.entity) : (o.entity ? wert(o.entity, "wind_speed") : w.wind);
        d.textContent = v != null ? `${T.wind} ${zahl(v, 1)} ${w.wind_einheit || "km/h"}` : ""; break;
      }
      case "raeume": {
        const n = Math.max(1, o.liste.length);
        d.innerHTML = o.liste.map((r) => `<div>${esc(r.name)} ${zahl(wert(r.entity), 1)} ${esc(wert(r.entity, "einheit"))}</div>`).join("");
        d.style.fontSize = Math.min(d.clientHeight / n * 0.3, 40) + "px"; break;
      }
      case "kachel": {
        const x = daten.werte[o.entity] || {};
        const gr = Math.min(d.clientHeight * 0.085, d.clientWidth * 0.075);
        d.innerHTML = `<span class="mdi ${esc(o.icon)}" style="font-size:${gr * 1.75}px"></span><div><div class="name" style="font-size:${gr}px">${esc(o.name || x.name || o.entity)}</div>` +
                      `<div class="wert" style="font-size:${gr * 0.87}px">${zahl(x.state, stellen(x.einheit, x.state))} ${esc(x.einheit)}</div></div>`;
        break;
      }
      case "vorhersage": {
        const tage = (daten.vorhersage || []).slice(0, o.tage);
        const gr = Math.min(d.clientHeight * 0.075, d.clientWidth / Math.max(1, tage.length) * 0.16);
        d.innerHTML = tage.map((v) => {
          const t = new Date(v.tag + "T12:00:00");
          return `<div class="tag" style="font-size:${gr}px">${t.toLocaleDateString(T.locale, { weekday: "short" }).replace(".", "")}` +
                 `<span class="mdi mdi-${SYMBOL[v.zustand] || "weather-cloudy"}" style="font-size:${gr * 2.3}px"></span>` +
                 `<div class="max" style="font-size:${gr * 1.2}px">${zahl(v.max, 1)}°</div><div class="min">${zahl(v.min, 1)}°</div></div>`;
        }).join("");
        break;
      }
      case "sender":
        d.textContent = daten.radio && daten.radio.anzeigen ? `♪ ${daten.radio.name}` : "";
        sichtbar = sichtbar && !!d.textContent; break;
      case "kalender": {
        const termine = ((daten.kalender || {})[o.entity] || []).slice(0, o.anzahl);
        const zeilen = termine.length + (o.titel ? 1 : 0) || 1;
        d.style.fontSize = Math.min(d.clientHeight / zeilen * 0.5, 34) + "px";
        const heute = new Date(); heute.setHours(0, 0, 0, 0);
        d.innerHTML = (o.titel ? `<div class="titel">${esc(o.titel)}</div>` : "") + (termine.length ? termine.map((t) => {
          const s = new Date(t.start); const tag = new Date(s); tag.setHours(0, 0, 0, 0);
          const diff = Math.round((tag - heute) / 86400000);
          const wann = diff === 0 ? T.heute : diff === 1 ? T.morgen : s.toLocaleDateString(T.locale, { weekday: "short", day: "2-digit", month: "2-digit" });
          const zeit = t.ganztag ? "" : " " + s.toLocaleTimeString(T.locale, { hour: "2-digit", minute: "2-digit" });
          return `<div class="zeile"><span class="wann">${esc(wann + zeit)}</span>${esc(t.titel)}</div>`;
        }).join("") : `<div class="zeile">${esc(T.keineTermine)}</div>`);
        break;
      }
      case "kamera": {
        if (!o.entity) { sichtbar = false; break; }
        if (sichtbar) {
          if (!b.bild) { b.bild = document.createElement("img"); d.appendChild(b.bild); }
          if (!b.letztes || Date.now() - b.letztes > o.intervall * 1000) {
            b.letztes = Date.now(); b.bild.src = `/kamera/${o.entity}.jpg?t=${Date.now()}`;
          }
        }
        break;
      }
      case "meldung": {
        const s = wert(o.entity);
        const m = meldungen[o.entity];
        if (!m) meldungen[o.entity] = { wert: s, seit: 0 };          // beim Laden alte Meldung nicht zeigen
        else if (s !== m.wert) { m.wert = s; m.seit = Date.now(); }
        const aktuell = meldungen[o.entity];
        const leer = !s || ["unknown", "unavailable", ""].includes(s);
        sichtbar = sichtbar && !leer && aktuell.seit && Date.now() - aktuell.seit < o.dauer * 1000;
        d.textContent = s || "";
        break;
      }
    }
    d.classList.toggle("versteckt", !sichtbar);
    if (e.typ === "video" && player) player.aus = !sichtbar;
    if (sichtbar && e.typ === "text" && e.optionen.laufband) laufband(d);
    else if (sichtbar && e.typ === "text" && d.classList.contains("mehrzeilig")) einpassenMehrzeilig(d);
    else if (sichtbar && FAKTOR[e.typ] && e.typ !== "uhr" && e.typ !== "datum") einpassen(d, FAKTOR[e.typ]);
  }
  uhr();
}

function uhr() {
  const jetzt = new Date(jetztMs());
  const zone = ZEIT.zone ? { timeZone: ZEIT.zone } : {};
  for (const { e, d } of bausteine) {
    if (e.typ === "uhr") {
      d.textContent = jetzt.toLocaleTimeString(T.locale, { hour: "2-digit", minute: "2-digit", ...(e.optionen.sekunden ? { second: "2-digit" } : {}), ...zone });
      if (!d.dataset.gepasst) { einpassen(d, FAKTOR.uhr); d.dataset.gepasst = 1; }
    } else if (e.typ === "datum") {
      d.textContent = jetzt.toLocaleDateString(T.locale, { ...(e.optionen.wochentag ? { weekday: "long" } : {}), day: "numeric", month: "long",
                                                           ...(e.optionen.jahr ? { year: "numeric" } : {}), ...zone });
      if (!d.dataset.gepasst) { einpassen(d, FAKTOR.datum); d.dataset.gepasst = 1; }
    } else if (e.typ === "meldung" && !d.classList.contains("versteckt")) {
      const m = meldungen[e.optionen.entity];
      if (m && Date.now() - m.seit > e.optionen.dauer * 1000) d.classList.add("versteckt");
    }
  }
}

// ---------- Radio ----------
const radio = $("radio");
let radioUrl = "", radioFehler = 0;
function radioSetzen(d) {
  const r = d.ton === "radio" && d.radio ? d.radio : null;
  radio.volume = Math.max(0, Math.min(1, (d.lautstaerke ?? 70) / 100));
  const url = r ? r.url : "";
  if (url !== radioUrl) {
    radioUrl = url; radioFehler = 0;
    if (url) { radio.src = url; radio.play().catch(() => {}); } else { radio.pause(); radio.removeAttribute("src"); radio.load(); }
  } else if (url && radio.paused) {
    radio.play().catch(() => {});
  }
}
// Abbruch des Senders: nach kurzer Pause neu verbinden (länger warten, je öfter es scheitert).
// NICHT auf "stalled" reagieren: mit Puffer lädt der Browser zeitweise nichts nach und meldet das – das ist normal.
function radioNeu() {
  if (!radioUrl) return;
  const url = radioUrl;
  setTimeout(() => { if (radioUrl === url) { radio.src = url; radio.play().catch(() => {}); } }, Math.min(60, 5 * ++radioFehler) * 1000);
}
for (const ereignis of ["error", "ended"]) radio.addEventListener(ereignis, radioNeu);
radio.addEventListener("playing", () => { radioFehler = 0; });
// Einspieler mit Ton: Radio solange stumm
window.addEventListener("einspieler-start", (e) => { if (e.detail.ton) radio.muted = true; });
window.addEventListener("einspieler-ende", () => { radio.muted = false; });
// Wache: läuft die Wiedergabezeit 90 s nicht weiter (obwohl ein Sender gewählt ist), neu verbinden
let radioZeit = -1, radioSteht = 0;
setInterval(() => {
  if (!radioUrl) { radioSteht = 0; return; }
  if (radio.currentTime !== radioZeit) { radioZeit = radio.currentTime; radioSteht = 0; return; }
  if (++radioSteht >= 9) { radioSteht = 0; radio.src = radioUrl; radio.play().catch(() => {}); }
}, 10000);

// ---------- Laden ----------
async function laden() {
  try {
    const r = await fetch("/daten.json?tv=" + encodeURIComponent(TV), { cache: "no-store" });
    const d = await r.json();
    if (!d || !d.ok) return;
    daten = d;
    T = TEXTE[d.sprache] || TEXTE.de;
    document.documentElement.lang = d.sprache || "de";
    const lj = JSON.stringify(d.layout);
    if (lj !== layoutJson) { layoutJson = lj; bauen(d.layout); }
    if (!d.layout.schwarz) { hintergrund(d.layout); fuellen(); }
    if (player) player.setze(d); else { ZEIT.abweichung = d.zeit_abweichung_ms || 0; ZEIT.zone = d.zeitzone || null; }
    // Quellenhinweis für das eigene Wetter (Lizenz CC BY 4.0 von MET Norway)
    $("quelle").textContent = d.wetter && d.wetter.quelle === "MET Norway" && !d.layout.schwarz ? T.wetterQuelle : "";
    radioSetzen(d);
  } catch (_) { /* nächster Versuch */ }
}

const start = Date.now();
laden(); setInterval(laden, 15000);
setInterval(uhr, 1000);
// Speicher frei halten: alle 6 h einmal neu laden
setInterval(() => { if (new Date().getSeconds() < 5 && Date.now() - start > 6 * 3600 * 1000) location.reload(); }, 1000);
