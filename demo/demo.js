// SignageCast – Hülle der Live-Demo: Umschalter (Vorlage, Tageszeit, Sprache) und Skalierung der TV-Seite.
// Die Auswahl steht in der Adresszeile (teilbar, keine Cookies, kein Speicher im Browser).
"use strict";
(function () {
  const T = {
    de: { hinweis: "Demo mit Beispieldaten", vorlage: "Vorlage", tz: "Tageszeit", sprache: "Sprache", auto: "echt (Sonnenstand)",
          morgen: "Morgen", tag: "Tag", abend: "Abend", nacht: "Nacht", tour: "Tour der Verwaltung" },
    en: { hinweis: "Demo with sample data", vorlage: "Template", tz: "Time of day", sprache: "Language", auto: "real (sun position)",
          morgen: "Morning", tag: "Day", abend: "Evening", nacht: "Night", tour: "Admin tour" },
  };
  const $ = (id) => document.getElementById(id);
  const tv = $("tv"), buehne = $("buehne");
  const P = new URLSearchParams(location.search);
  // ohne Angabe: Sprache des Browsers (nur gelesen, nirgends gespeichert oder gesendet)
  const wahl = { vorlage: P.get("vorlage"), tz: P.get("tz"),
                 sprache: P.get("sprache") || (/^de\b/i.test(navigator.language || "") ? "de" : "en") };
  for (const k of Object.keys(wahl)) {
    const s = $(k);
    if (wahl[k] && [...s.options].some((o) => o.value === wahl[k])) s.value = wahl[k];
    wahl[k] = s.value;
  }
  let namen = null;           // Namen der Vorlagen je Sprache aus demo-daten.json

  function texte() {
    const t = T[wahl.sprache] || T.de;
    document.documentElement.lang = wahl.sprache;
    document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = t[el.dataset.t]; });
    $("tour").href = "https://github.com/thefrozn/signagecast/blob/main/docs/" + (wahl.sprache === "en" ? "TOUR.md" : "TOUR.de.md");
    if (namen) for (const o of $("vorlage").options) o.textContent = (namen[o.value] || {})[wahl.sprache] || o.textContent;
  }
  function laden() {
    const q = new URLSearchParams({ tv: "demo", vorlage: wahl.vorlage, tz: wahl.tz, sprache: wahl.sprache });
    tv.src = "tv/index.html?" + q;
    history.replaceState(null, "", "?" + new URLSearchParams({ vorlage: wahl.vorlage, tz: wahl.tz, sprache: wahl.sprache }));
    texte();
  }
  function passen() {
    const w = buehne.clientWidth, h = buehne.clientHeight, f = Math.min(w / 1920, h / 1080);
    // schmale Bildschirme (Handy hochkant): direkt unter den Balken statt senkrecht mittig
    const oben = w / h < 16 / 9 ? Math.min((h - 1080 * f) / 2, 16) : (h - 1080 * f) / 2;
    tv.style.transform = `translate(${(w - 1920 * f) / 2}px, ${oben}px) scale(${f})`;
  }
  for (const k of Object.keys(wahl)) $(k).addEventListener("change", (e) => { wahl[k] = e.target.value; laden(); });
  addEventListener("resize", passen);
  fetch("tv/demo-daten.json").then((r) => r.json()).then((d) => {
    namen = Object.fromEntries(Object.entries(d.vorlagen).map(([k, v]) => [k, { de: v.de.name, en: v.en.name }]));
    texte();
  }).catch(() => {});
  passen(); laden();
})();
