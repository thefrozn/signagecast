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
        heute: "Heute", morgen: "Morgen", keineTermine: "Keine Termine", locale: "de-DE",
        bis: "bis", keineWarnung: "Keine Unwetterwarnung", dwd: "Quelle: Deutscher Wetterdienst" },
  en: { lage: { "clear-night": "Clear night", "cloudy": "Cloudy", "exceptional": "Exceptional", "fog": "Fog", "hail": "Hail",
          "lightning": "Thunderstorm", "lightning-rainy": "Thunderstorm, rain", "partlycloudy": "Partly cloudy",
          "pouring": "Pouring", "rainy": "Rainy", "snowy": "Snowy", "snowy-rainy": "Sleet", "sunny": "Sunny",
          "windy": "Windy", "windy-variant": "Windy, cloudy" },
        feuchte: "Humidity", wind: "Wind", keinStream: "No live stream right now", naechstes: "Up next", wetterQuelle: "Weather data: MET Norway",
        heute: "Today", morgen: "Tomorrow", keineTermine: "No events", locale: "en-GB",
        bis: "until", keineWarnung: "No weather warning", dwd: "Source: Deutscher Wetterdienst" },
};
const FAKTOR = { uhr: 0.82, temperatur: 0.72, datum: 0.5, wetterlage: 0.6, feuchte: 0.5, wind: 0.5, sender: 0.5, text: 0.55, meldung: 0.42, countdown: 0.55 };
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
  for (const b of bausteine) if (b.stopp) b.stopp();          // Kameras/Webseiten sauber beenden
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
    if (e.typ === "apiwert") d.innerHTML = (e.optionen.icon ? `<span class="mdi ${esc(e.optionen.icon)}"></span>` : "") +
      `<div>${e.optionen.name ? `<div class="name">${esc(e.optionen.name)}</div>` : ""}<div class="wert"></div></div>`;
    if (e.typ === "apiliste") {
      if (e.optionen.laufband) { d.classList.add("laufband"); d.innerHTML = "<span></span>"; }
      else d.innerHTML = (e.optionen.titel ? `<div class="titel">${esc(e.optionen.titel)}</div>` : "") + `<div class="zeilen"></div>`;
    }
    if (e.typ === "apibild") { d.innerHTML = `<img alt="">`; d.classList.add(e.optionen.anpassung === "fuellen" ? "fuellen" : "einpassen"); }
    if (e.typ === "anzeige") d.innerHTML = e.optionen.darstellung === "ampel"
      ? `<span class="lampe"></span><div><div class="name">${esc(e.optionen.name)}</div><div class="wert"></div></div>`
      : `<div class="kopf"><span class="name">${esc(e.optionen.name)}</span><span class="wert"></span></div><div class="spur"><div class="fuellung"></div></div>`;
    if (e.typ === "qrcode") d.innerHTML = `<div class="qr"></div>${e.optionen.beschriftung ? `<div class="beschriftung">${esc(e.optionen.beschriftung)}</div>` : ""}`;
    if (e.typ === "diagramm") d.innerHTML = `<div class="kopf"><span class="name">${esc(e.optionen.name)}</span><span class="wert"></span></div><div class="kurve"></div>`;
    if (e.typ === "webcam") d.classList.add(e.optionen.anpassung === "einpassen" ? "einpassen" : "fuellen");
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
  const w = (daten.werte[b.entity || `api:${b.quelle}:${b.pfad}`] || {}).state;
  if (w === undefined || w === null) return false;
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
        const aus_ical = o.quelle ? ((daten.api || {})[e.id] || {}).termine : null;
        const termine = (aus_ical || (daten.kalender || {})[o.entity] || []).slice(0, o.anzahl);
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
      case "text": {
        const a = (daten.api || {})[e.id];
        if (a && a.text !== b.apiText) {
          b.apiText = a.text;
          if (o.laufband) { d.querySelector("span").textContent = a.text; delete d.dataset.laeuft; }
          else d.textContent = a.text;
        }
        break;
      }
      case "apiwert": {
        const a = (daten.api || {})[e.id] || {};
        d.querySelector(".wert").textContent = a.text || "";
        d.style.fontSize = Math.min(d.clientHeight * (o.name ? 0.3 : 0.5), 120) + "px";
        for (let i = 0; i < 15 && d.scrollWidth > d.clientWidth + 1; i++) d.style.fontSize = parseFloat(d.style.fontSize) * 0.9 + "px";
        sichtbar = sichtbar && (a.da !== false || !o.quelle);
        break;
      }
      case "apiliste": {
        const a = (daten.api || {})[e.id] || { zeilen: [] };
        const neu = JSON.stringify(a.zeilen);
        if (neu !== b.apiText) {
          b.apiText = neu;
          if (o.laufband) {
            d.querySelector("span").textContent = a.zeilen.join("   ·   "); delete d.dataset.laeuft;
          } else {
            const z = d.querySelector(".zeilen");
            z.innerHTML = a.zeilen.map((x) => `<div class="zeile">${esc(x)}</div>`).join("");
            const n = Math.max(1, a.zeilen.length + (o.titel ? 1.3 : 0));
            d.style.fontSize = Math.min(d.clientHeight / n * 0.62, 44) + "px";
            for (let i = 0; i < 15 && d.scrollHeight > d.clientHeight + 1; i++) d.style.fontSize = parseFloat(d.style.fontSize) * 0.92 + "px";
          }
        }
        sichtbar = sichtbar && a.zeilen.length > 0;
        break;
      }
      case "apibild": {
        const a = (daten.api || {})[e.id];
        const img = d.querySelector("img");
        if (a && a.bild && img.dataset.src !== a.bild) { img.dataset.src = a.bild; img.src = a.bild; }
        sichtbar = sichtbar && !!(a && a.bild);
        break;
      }
      case "anzeige": {
        const a = (daten.api || {})[e.id] || {};
        const z = a.zahl;
        d.querySelector(".wert").textContent = a.text || "";
        let farbe = "gruen";
        if (z != null) {
          const schlecht = (g) => (o.umkehren ? z <= g : z >= g);
          farbe = schlecht(o.rot) ? "rot" : schlecht(o.gelb) ? "gelb" : "gruen";
        }
        d.dataset.farbe = z == null ? "" : farbe;
        if (o.darstellung === "ampel") d.style.fontSize = Math.min(d.clientHeight * 0.22, d.clientWidth * 0.1) + "px";
        else {
          d.style.fontSize = Math.min(d.clientHeight * 0.28, d.clientWidth * 0.08) + "px";
          const anteil = z == null || o.max === o.min ? 0 : Math.max(0, Math.min(1, (z - o.min) / (o.max - o.min)));
          d.querySelector(".fuellung").style.width = anteil * 100 + "%";
        }
        break;
      }
      case "countdown": {
        b.ziel = ((daten.api || {})[e.id] || {}).ziel || "";
        sichtbar = sichtbar && !!b.ziel;
        countdown(b);
        break;
      }
      case "qrcode": {
        const inhalt = ((daten.api || {})[e.id] || {}).inhalt || "";
        if (inhalt !== b.apiText && typeof qrcode === "function") {
          b.apiText = inhalt;
          const q = d.querySelector(".qr");
          if (inhalt) {
            qrcode.stringToBytes = qrcode.stringToBytesFuncs["UTF-8"];
            const qr = qrcode(0, "M"); qr.addData(inhalt); qr.make();
            q.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 2, scalable: true });
          } else q.innerHTML = "";
        }
        sichtbar = sichtbar && !!inhalt;
        break;
      }
      case "unwetter": {
        const ws = (daten.unwetter || []).slice(0, o.anzahl);
        sichtbar = sichtbar && (ws.length > 0 || o.immer);
        const bis = (x) => x ? new Date(x).toLocaleString(T.locale, { weekday: "short", hour: "2-digit", minute: "2-digit" }) : "";
        d.dataset.stufe = ws.length ? ws[0].stufe : 0;
        d.innerHTML = (ws.length ? ws.map((w) => `<div class="warnung"><b>⚠ ${esc(w.titel)}</b><span class="leise"> · ${esc(T.bis)} ${esc(bis(w.bis))}</span></div>`).join("")
          : `<div class="warnung">${esc(T.keineWarnung)}</div>`) + `<div class="dwd">${esc(T.dwd)}</div>`;
        d.style.fontSize = Math.min(d.clientHeight / (Math.max(1, ws.length) + 0.8) * 0.55, 40) + "px";
        break;
      }
      case "webcam": {
        const a = (daten.api || {})[e.id];
        sichtbar = sichtbar && !!a;
        if (sichtbar) kameraStarten(b, a); else kameraStoppen(b);
        break;
      }
      case "diagramm": {
        const a = (daten.api || {})[e.id] || { punkte: [] };
        d.querySelector(".wert").textContent = a.text || "";
        d.style.fontSize = Math.min(d.clientHeight * 0.12, 36) + "px";
        diagrammZeichnen(d.querySelector(".kurve"), a.punkte);
        break;
      }
      case "webseite": {
        sichtbar = sichtbar && !!o.url;
        if (sichtbar) webseite(b); else if (b.stopp) { b.stopp(); }
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
    if (sichtbar && (e.typ === "text" || e.typ === "apiliste") && e.optionen.laufband) laufband(d);
    else if (sichtbar && e.typ === "text" && d.classList.contains("mehrzeilig")) einpassenMehrzeilig(d);
    else if (sichtbar && FAKTOR[e.typ] && e.typ !== "uhr" && e.typ !== "datum") einpassen(d, FAKTOR[e.typ]);
  }
  uhr();
}

// ---------- Kamera: HLS (über MediaMTX im Container, mit hls.js) oder MJPEG (über den Datendienst) ----------
let hlsLaden = null;
function hlsBereit() {
  if (window.Hls) return Promise.resolve();
  if (!hlsLaden) hlsLaden = new Promise((ok, fehler) => {            // nur laden, wenn eine Kamera im Layout ist
    const sc = document.createElement("script"); sc.src = "hls/hls.light.min.js"; sc.onload = ok; sc.onerror = fehler;
    document.head.appendChild(sc);
  });
  return hlsLaden;
}
function kameraStoppen(b) {
  if (b.hls) { b.hls.destroy(); b.hls = null; }
  if (b.medien) { b.medien.remove(); b.medien = null; }
  clearTimeout(b.neuVersuch); b.kamUrl = "";
}
function kameraStarten(b, a) {
  if (b.kamUrl === a.url) return;
  kameraStoppen(b);
  b.kamUrl = a.url;
  b.stopp = () => kameraStoppen(b);
  const neu = () => { b.neuVersuch = setTimeout(() => { const u = b.kamUrl; kameraStoppen(b); if (u) kameraStarten(b, a); }, 10000); };
  if (a.art === "mjpeg") {
    const img = document.createElement("img");
    img.onerror = neu;
    img.src = a.url + "?t=" + Date.now();
    b.d.appendChild(img); b.medien = img;
    return;
  }
  const v = document.createElement("video");
  v.muted = !b.e.optionen.ton; v.autoplay = true; v.playsInline = true;
  b.d.appendChild(v); b.medien = v;
  hlsBereit().then(() => {
    if (b.medien !== v) return;
    const h = new Hls({ lowLatencyMode: false, liveSyncDurationCount: 2, manifestLoadingMaxRetry: 4, levelLoadingMaxRetry: 4 });
    b.hls = h;
    h.on(Hls.Events.ERROR, (_, x) => { if (x.fatal) neu(); });
    h.loadSource(a.url); h.attachMedia(v);
    v.play().catch(() => {});
  }).catch(neu);
}

// ---------- Diagramm: Verlauf als Linie mit Fläche, kleinster/größter Wert am Rand ----------
function diagrammZeichnen(z, punkte) {
  const w = z.clientWidth, h = z.clientHeight;
  if (!w || !h) return;
  if (!punkte || punkte.length < 2) { z.innerHTML = ""; return; }
  const ts = punkte.map((p) => p[0]), vs = punkte.map((p) => p[1]);
  let lo = Math.min(...vs), hi = Math.max(...vs);
  if (hi === lo) { hi += 1; lo -= 1; }
  const t0 = ts[0], t1 = ts[ts.length - 1] || t0 + 1, rand = 4, beschr = 40;
  const x = (t) => beschr + (t - t0) / Math.max(1, t1 - t0) * (w - beschr - rand);
  const y = (v) => rand + (1 - (v - lo) / (hi - lo)) * (h - 2 * rand);
  const linie = punkte.map((p) => `${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(" ");
  const f = "var(--akzent)";
  const zahl1 = (n) => zahl(n, Math.abs(hi - lo) < 10 ? 1 : 0);
  z.innerHTML = `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
    <polygon points="${beschr},${h - rand} ${linie} ${x(t1).toFixed(1)},${h - rand}" fill="${f}" opacity=".18"/>
    <polyline points="${linie}" fill="none" stroke="${f}" stroke-width="3" stroke-linejoin="round"/>
    <text x="0" y="${rand + 14}" class="achse">${zahl1(hi)}</text><text x="0" y="${h - rand}" class="achse">${zahl1(lo)}</text></svg>`;
}

// ---------- Webseite: eingebettet (nur wenn die Seite es erlaubt), mit Zoom, Ausschnitt und Neuladen ----------
function webseite(b) {
  const o = b.e.optionen, d = b.d;
  const skala = (o.zoom || 100) / 100;
  if (!b.rahmen || b.rahmenUrl !== o.url) {
    if (b.rahmen) b.rahmen.remove();
    const f = document.createElement("iframe");
    f.setAttribute("sandbox", "allow-scripts allow-same-origin");   // keine Pop-ups, keine Formulare, kein Wegnavigieren
    f.setAttribute("referrerpolicy", "no-referrer");
    f.setAttribute("scrolling", "no");                                  // keine Bildlaufleisten am Fernseher
    f.src = o.url; b.rahmen = f; b.rahmenUrl = o.url; b.geladen = Date.now();
    d.appendChild(f);
    b.stopp = () => { if (b.rahmen) { b.rahmen.remove(); b.rahmen = null; b.rahmenUrl = ""; } };
  }
  Object.assign(b.rahmen.style, { left: -o.versatz_x * skala + "px", top: -o.versatz_y * skala + "px",
    width: d.clientWidth / skala + o.versatz_x + "px", height: d.clientHeight / skala + o.versatz_y + "px", transform: `scale(${skala})` });
  if (o.neu_laden_min > 0 && Date.now() - b.geladen > o.neu_laden_min * 60000) { b.geladen = Date.now(); b.rahmen.src = o.url; }
}

// Countdown: Rest bis zum Ziel in Tagen/Stunden/Minuten/Sekunden nach der Vorlage, danach der Ende-Text
function countdown(b) {
  const o = b.e.optionen, d = b.d;
  if (!b.ziel) { d.textContent = ""; return; }
  const rest = Math.floor((new Date(b.ziel).getTime() - jetztMs()) / 1000);
  let text;
  if (isNaN(rest)) text = "";
  else if (rest <= 0) text = o.ende || "";
  else {
    const w = { tage: Math.floor(rest / 86400), stunden: Math.floor(rest % 86400 / 3600), minuten: Math.floor(rest % 3600 / 60), sekunden: rest % 60 };
    // ohne {tage} in der Vorlage zählen die Stunden alles mit
    if (!/\{tage\}/.test(o.vorlage)) w.stunden += w.tage * 24;
    text = (o.vorlage || "{tage}").replace(/\{(tage|stunden|minuten|sekunden)\}/g, (_, k) => (k === "tage" || k === "stunden" ? String(w[k]) : String(w[k]).padStart(2, "0")));
  }
  if (text !== d.textContent) { d.textContent = text; if (!d.classList.contains("versteckt")) einpassen(d, FAKTOR.countdown); }
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
    } else if (e.typ === "countdown") {
      countdown(bausteine.find((x) => x.e === e));
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
    meldungExtern(d.meldung_extern);
  } catch (_) { /* nächster Versuch */ }
}

// Meldung per Webhook (seit 0.16): Banner über jedem Layout, auch bei „schwarz“
function meldungExtern(m) {
  const el = $("meldung-extern");
  if (!m || m.bis * 1000 < Date.now()) { el.hidden = true; return; }
  el.textContent = m.text;
  el.className = m.stil === "warnung" ? "warnung" : "";
  el.hidden = false;
}

const start = Date.now();
laden(); setInterval(laden, 15000);
setInterval(uhr, 1000);
// Speicher frei halten: alle 6 h einmal neu laden
setInterval(() => { if (new Date().getSeconds() < 5 && Date.now() - start > 6 * 3600 * 1000) location.reload(); }, 1000);
