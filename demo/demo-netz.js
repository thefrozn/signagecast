// SignageCast – Live-Demo (GitHub Pages, seit 0.64). Wird nur in die Demo-Kopie der TV-Seite eingebunden
// (werkzeug/demo_bauen.py), vor allen anderen Skripten. Ersetzt den Datendienst: fetch() für /daten.json,
// /durchsage.json und /meldung/… antwortet aus demo-daten.json (Beispieldaten, gebaut aus dem aktuellen Code);
// Uhrzeit, Datum und Sonnenstand (Tageszeit) rechnet der Browser. Anfragen an fremde Server werden abgelehnt.
// Adresszeile: ?vorlage=wohnzimmer|praxis|imbiss|hotel&tz=auto|morgen|tag|abend|nacht&sprache=de|en
"use strict";
(function () {
  const P = new URLSearchParams(location.search);
  const echt = window.fetch.bind(window);
  const hier = location.origin;
  let basis = null;
  const geladen = echt("demo-daten.json", { cache: "no-store" }).then((r) => r.json()).then((d) => { basis = d; return d; });

  // Sonnenhöhe in Grad (NOAA-Näherung wie streams.sonnenhoehe) und Tageszeit wie layouts.tageszeit
  function sonnenhoehe(breite, laenge, t) {
    const d = new Date(t), anfang = Date.UTC(d.getUTCFullYear(), 0, 1);
    const tag = Math.floor((t - anfang) / 86400000) + 1, stunde = d.getUTCHours() + d.getUTCMinutes() / 60;
    const g = 2 * Math.PI / 365 * (tag - 1 + (stunde - 12) / 24);
    const zeitgl = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
    const dekl = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g)
      + 0.000907 * Math.sin(2 * g) - 0.002697 * Math.cos(3 * g) + 0.00148 * Math.sin(3 * g);
    const sw = ((stunde * 60 + zeitgl + 4 * laenge) / 4 - 180) * Math.PI / 180, b = breite * Math.PI / 180;
    return Math.asin(Math.sin(b) * Math.sin(dekl) + Math.cos(b) * Math.cos(dekl) * Math.cos(sw)) * 180 / Math.PI;
  }
  function tageszeit(ort) {
    const t = Date.now(), jetzt = sonnenhoehe(ort.breite, ort.laenge, t), spaeter = sonnenhoehe(ort.breite, ort.laenge, t + 600000);
    if (jetzt < -6) return "nacht";
    if (jetzt >= 8) return "tag";
    return spaeter > jetzt ? "morgen" : "abend";
  }
  const zwei = (n) => String(n).padStart(2, "0");
  const tagIso = (d) => `${d.getFullYear()}-${zwei(d.getMonth() + 1)}-${zwei(d.getDate())}`;
  const plusTage = (n) => { const d = new Date(); d.setHours(12, 0, 0, 0); d.setDate(d.getDate() + n); return d; };

  function daten() {
    const sprache = basis.vorlagen.wohnzimmer[P.get("sprache")] ? P.get("sprache") : "de";
    const v = (basis.vorlagen[P.get("vorlage")] || basis.vorlagen[basis.reihenfolge[0]])[sprache];
    const b = basis.beispiel, wahl = P.get("tz");
    const tz = ["morgen", "tag", "abend", "nacht"].includes(wahl) ? wahl : tageszeit(b.ort);
    const jetzt = new Date();
    const api = JSON.parse(JSON.stringify(v.api));
    for (const k of Object.keys(api)) {             // Countdown: ein vergangenes Datum ins nächste Jahr schieben
      const z = api[k] && api[k].ziel;
      if (z && /^\d{4}-\d{2}-\d{2}/.test(z)) {
        let d = new Date(z.length === 10 ? z + "T00:00" : z), n = 0;
        while (d < jetzt && n++ < 5) d.setFullYear(d.getFullYear() + 1);
        api[k].ziel = tagIso(d) + z.slice(10);
      }
    }
    const kalender = {};
    for (const [ent, liste] of Object.entries(b.kalender)) {
      kalender[ent] = liste.map((x) => ({ titel: (x.titel && x.titel[sprache]) || x.titel.de, ganztag: !!x.ganztag,
        start: tagIso(plusTage(x.tage)) + (x.ganztag ? "" : "T" + x.zeit + ":00") }));
    }
    const stil = v.layout.hintergrund && v.layout.hintergrund.art === "stil" ? v.layout.hintergrund.stil : "natur";
    return {
      ok: true, ha_ok: true, zeit: Math.floor(Date.now() / 1000), sprache, tageszeit: tz, version: basis.version,
      tv: "demo", layout: v.layout, api, werte: v.werte, kalender,
      wetter: Object.assign({ entity: "" }, b.wetter, tz === "nacht" && b.wetter.zustand !== "rainy" ? { zustand: "clear-night" } : {}),
      vorhersage: b.vorhersage.map((x) => ({ tag: tagIso(plusTage(x.tage)), zustand: x.zustand, max: x.max, min: x.min })),
      medien: b.medien.map((s, i) => ({ id: "demo" + i, name: s, art: "bild", url: `bilder/stile/${s}-${tz}.jpg`, dauer_s: 12 })),
      medien_modus: "medien", medien_alle: 3,
      regeln: { takt_s: 180, mindeststufe: "hd720", schlecht_s: 20, sperre_s: 7200 },   // nur für Live-Streams (gibt es hier nicht)
      offline: false, ersatz: { medien: [], bild: `bilder/stile/${stil}-${tz}.jpg` },
      einspieler: [], einspieler_jetzt: null, streams: [], allgemein: null, vorrang: null, versatz: 1,
      zeit_abweichung_ms: 0, zeitzone: null, jetzt_lokal: `${tagIso(jetzt)}T${zwei(jetzt.getHours())}:${zwei(jetzt.getMinutes())}`,
      webbild: {}, pdf: {}, galerie: {}, alarm: null, unwetter: [], meldung_extern: null, durchsage: null,
      ton: "aus", lautstaerke: 0, radio: { name: "", anzeigen: false, url: "" },
    };
  }
  const antwort = (obj) => new Response(JSON.stringify(obj), { status: 200, headers: { "Content-Type": "application/json" } });

  window.fetch = async function (eingabe, optionen) {
    const url = new URL(typeof eingabe === "string" ? eingabe : eingabe.url, location.href);
    if (url.origin !== hier) throw new TypeError("Demo: keine Anfragen an fremde Server");
    if (url.pathname.endsWith("/daten.json")) { await geladen; return antwort(daten()); }
    if (url.pathname.endsWith("/durchsage.json")) {     // wie das Long-Polling des Dienstes: nach 20 s „nichts Neues“
      await new Promise((w) => setTimeout(w, 20000));
      return antwort({ ok: true, stand: "demo", durchsage: null, alarm: null });
    }
    if (url.pathname.includes("/meldung/")) return antwort({ ok: true });
    return echt(eingabe, optionen);
  };
})();
