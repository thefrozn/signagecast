// SignageCast – Live-Videos (seit 0.56): Übersicht, Sammlung, Themen, Automatik. Gleiche Logik und Schnittstellen wie
// bisher, neue Gliederung: schlanke Listen, Details in einem Seitenfeld rechts, Technik unter „Erweitert“, Alltagssprache.
// Nutzt Hilfen aus tv.js (esc, el, $, holen, senden, aktion, speichernE, schalter, katName, katOptionen, E, T …).
"use strict";

const LIVE_TEXTE = {
  de: {
    schliessen: "Schließen", speichern: "Speichern", mehr: "Weitere Aktionen", erweitert: "Erweitert",
    // Übersicht
    uTitel: "Live-Videos", musik: "Musik in der Öffentlichkeit ist lizenzpflichtig: Wer Radio, Livestreams oder eigene Videos mit Ton in Praxis, Laden, Gaststätte, Hotel, Verein oder an einem anderen öffentlichen Ort abspielt, braucht dafür in fast allen Ländern eine Lizenz der zuständigen Verwertungsgesellschaft – auch für Internetradio. Bitte vorher klären; zu Hause gilt das nicht.", recht: "YouTube erlaubt nur die private, nicht-gewerbliche Nutzung. In Praxis, Laden, Hotel, Verein oder an anderen öffentlichen Orten bitte nur eigene Medien zeigen oder die Rechte selbst klären (YouTube-Bedingungen, Betreiber der Kamera, GEMA bei Ton).", uText: "Live-Kameras von YouTube laufen im Videofenster der Layouts – automatisch gesucht, nach Themen sortiert und nur dort, wo gerade Tag ist.",
    laeuftAuf: "Läuft gerade", nichts: "– (Kanal zeigt gerade kein Live-Video)", kanalAus: "Kette aus (niemand schaut zu)",
    zahlen: { rotation: "in der Rotation", bereit: "bereit", nacht: "dunkel vor Ort", probleme: "mit Problemen" },
    probleme: "Probleme", keineProbleme: "Keine Probleme – alles läuft.", ansehen: "Ansehen",
    suche: "Automatische Suche", sucheAn: (u) => `täglich um ${u} Uhr`, sucheAus: "ausgeschaltet", letzte: "Letzte Suche",
    jetztSuchen: "Jetzt suchen", laeuft: "Suche läuft …", ergebnis: (n, g) => `${n} neu, ${g} gefunden`, einstellen: "Einstellen",
    // Sammlung
    sTitel: "Sammlung", sText: "Alle Live-Streams. Klick auf eine Zeile zeigt Details und Einstellungen.",
    neu: "+ Stream hinzufügen", suchen: "Suchen …", alleThemen: "alle Themen",
    gruppen: { alle: "Alle", rotation: "Läuft", bereit: "Bereit", nacht: "Dunkel vor Ort", probleme: "Probleme", aus: "Aus", gefunden: "Neu gefunden" },
    anzahl: (n, g) => `${n} von ${g} Streams`,
    status: { rotation: "läuft in der Rotation", bereit: "bereit", nacht: "dunkel vor Ort", nachlauf: "läuft aus (gerade dunkel geworden)",
      nicht_live: "gerade nicht live", qualitaet: "Bild zu unscharf", pause: "pausiert nach Ausfällen", gesperrt: "gesperrt – zu oft ausgefallen",
      ohne_ort: "Ort unbekannt", ungeprueft: "noch nicht geprüft", inaktiv: "ausgeschaltet", kategorie_aus: "Thema ausgeschaltet" },
    hellIn: (d) => `hell in ${d}`, bis: (z) => `bis ${z}`, angebot: (p) => `nur ${p}`,
    ort: "Ort", ohneOrt: "Ort unbekannt", gefundenMarke: "neu gefunden",
    zeigen: "Jetzt zeigen", zeigenAuf: "auf", alleKanaele: "allen Kanälen", zeigenOk: "Läuft gleich am Fernseher (für einen Wechsel)",
    nieWieder: "Nie wieder vorschlagen", entfernen: "Entfernen",
    wirklichEntfernen: "Stream entfernen? Die Suche kann ihn wieder finden.", wirklichNie: "Stream entfernen und bei der Suche nie wieder aufnehmen?",
    name: "Name", nameLeer: "leer = Titel von YouTube", thema: "Thema", breite: "Breite", laenge: "Länge",
    ortAuto: "Leer lassen: der Ort wird aus dem Titel erkannt (für Tag/Nacht).", ortSuchen: "Ort suchen …", suchenKnopf: "Suchen",
    keineOrte: "nichts gefunden", link: "YouTube-Link oder Video-ID",
    aktiv: "In der Rotation zeigen", geschuetzt: "Ausfälle nicht zählen", geschuetztText: "Für Streams, die du auf jeden Fall behalten willst: kurze Aussetzer führen dann nicht zur Pause oder Sperre.",
    uebernehmen: "In die feste Sammlung übernehmen", uebernehmenText: "Gefundene Streams entfernt die Suche nach einiger Zeit wieder, wenn sie sie nicht mehr findet – feste nie.",
    technik: "Technik", aufloesung: "Angebotene Auflösung", anteil: (a, n) => `${a} % der ${n} Prüfungen mit mindestens 720p`,
    codecs: "Codecs", ausfaelle: "Ausfälle", ausfaelleWeg: "Ausfälle zurücksetzen", keine: "keine",
    nieListe: (n) => `Nie wieder vorschlagen (${n})`, nieText: "Diese Streams nimmt die Suche nie wieder auf.", freigeben: "Freigeben",
    hinzu: "Hinzufügen",
    // Themen
    tTitel: "Themen", tText: "Ein Thema bestimmt, wonach gesucht wird und welche Streams dazugehören. Schalter = Thema zeigen ja/nein; Klick öffnet die Einstellungen.",
    neuesThema: "+ Neues Thema", tierSuche: "Suche für Tiere …", tierSucheTitel: "Suche für alle Tier-Themen",
    tierSucheText: "Tier-Streams werden mit diesen Begriffen gesucht und dann nach den Wörtern im Titel auf die Tier-Themen verteilt (sonst „Neu gefunden“).",
    begriffe: "Suchbegriffe bei YouTube (je Zeile einer)", tierwoerter: "Titel muss eines dieser Wörter enthalten (je Zeile eines)",
    streams: (n) => (n === 1 ? "1 Stream" : `${n} Streams`), mitSuche: (n) => `${n} Suchbegriffe`, ausBei: (x) => `aus bei ${x}`,
    passt: (n) => `passt auf ${n} der vorhandenen Streams`, zeigeStreams: "Streams ansehen",
    // Automatik
    aTitel: "Automatik", aText: "Wie oft gewechselt und wann gesucht wird. Alles andere regelt SignageCast selbst.",
    abspielen: "Abspielen", suchenTitel: "Suchen", sperrwoerter: "Sperrwörter: Titel darf keines enthalten (je Zeile eines)",
    orte: "Ortserkennung aus dem Titel", orteText: "Steht eines der Wörter im Titel, gilt dieser Ort (für Tag/Nacht). Mehrere Wörter mit | trennen.",
    muster: "Wörter im Titel", zeileNeu: "+ Zeile", testen: "Mit einem Titel testen …", erkannt: (m, b, l) => `erkannt: „${m}“ → ${b} / ${l}`,
    nichtErkannt: "kein Ort erkannt", musterFehler: "ungültiges Muster", weg: "Zeile entfernen",
    takt: "Minuten je Stream", nurTag: "Nur Streams zeigen, wo vor Ort Tag ist", sonne: "Sonne mindestens so hoch (Grad)",
    mindeststufe: "Mindest-Auflösung", schlecht: "So lange darf das Bild schlecht sein (s)", grenze: "Ausfälle bis zur Sperre", sperre: "Sperre dauert (h)",
    sucheAktiv: "Täglich nach neuen Streams suchen", begriffeWo: "Wonach gesucht wird, steht bei den", uhrzeit: "Uhrzeit", max: "Höchstens neue Streams je Suche", behalten: "Nicht mehr gefundene entfernen nach (Tagen)",
  },
  en: {
    schliessen: "Close", speichern: "Save", mehr: "More actions", erweitert: "Advanced",
    uTitel: "Live videos", musik: "Playing music in public needs a licence: if you play radio, live streams or own videos with sound in a practice, shop, restaurant, hotel, club or other public place, you need a licence from the music rights organisation in your country in almost every country – internet radio included. Please check this first; at home it does not apply.", recht: "YouTube only allows private, non-commercial use. In a practice, shop, hotel, club or other public place please show own media only or clear the rights yourself (YouTube terms, camera operator, music licensing for sound).", uText: "Live cams from YouTube play in the video window of the layouts – found automatically, sorted by topic and only where it is daytime.",
    laeuftAuf: "Playing now", nichts: "– (channel shows no live video right now)", kanalAus: "chain off (nobody watching)",
    zahlen: { rotation: "in rotation", bereit: "ready", nacht: "dark on site", probleme: "with problems" },
    probleme: "Problems", keineProbleme: "No problems – everything is running.", ansehen: "Show",
    suche: "Automatic search", sucheAn: (u) => `daily at ${u}`, sucheAus: "switched off", letzte: "Last search",
    jetztSuchen: "Search now", laeuft: "Searching …", ergebnis: (n, g) => `${n} new, ${g} found`, einstellen: "Settings",
    sTitel: "Collection", sText: "All live streams. Click a row for details and settings.",
    neu: "+ Add stream", suchen: "Search …", alleThemen: "all topics",
    gruppen: { alle: "All", rotation: "Playing", bereit: "Ready", nacht: "Dark on site", probleme: "Problems", aus: "Off", gefunden: "Newly found" },
    anzahl: (n, g) => `${n} of ${g} streams`,
    status: { rotation: "in rotation", bereit: "ready", nacht: "dark on site", nachlauf: "running out (just got dark)",
      nicht_live: "not live right now", qualitaet: "picture too blurry", pause: "paused after failures", gesperrt: "blocked – failed too often",
      ohne_ort: "location unknown", ungeprueft: "not checked yet", inaktiv: "switched off", kategorie_aus: "topic switched off" },
    hellIn: (d) => `light in ${d}`, bis: (z) => `until ${z}`, angebot: (p) => `only ${p}`,
    ort: "Location", ohneOrt: "location unknown", gefundenMarke: "newly found",
    zeigen: "Show now", zeigenAuf: "on", alleKanaele: "all channels", zeigenOk: "Plays on the TV shortly (for one turn)",
    nieWieder: "Never suggest again", entfernen: "Remove",
    wirklichEntfernen: "Remove the stream? The search may find it again.", wirklichNie: "Remove the stream and never take it in again?",
    name: "Name", nameLeer: "empty = YouTube title", thema: "Topic", breite: "Latitude", laenge: "Longitude",
    ortAuto: "Leave empty: the location is recognised from the title (for day/night).", ortSuchen: "Search place …", suchenKnopf: "Search",
    keineOrte: "nothing found", link: "YouTube link or video ID",
    aktiv: "Show in the rotation", geschuetzt: "Don't count failures", geschuetztText: "For streams you want to keep in any case: short dropouts then don't lead to a pause or a block.",
    uebernehmen: "Keep permanently", uebernehmenText: "The search removes found streams again after a while when it no longer finds them – permanent ones never.",
    technik: "Technical", aufloesung: "Offered resolution", anteil: (a, n) => `${a} % of ${n} checks with at least 720p`,
    codecs: "Codecs", ausfaelle: "Failures", ausfaelleWeg: "Reset failures", keine: "none",
    nieListe: (n) => `Never suggest again (${n})`, nieText: "The search never takes these streams in again.", freigeben: "Release",
    hinzu: "Add",
    tTitel: "Topics", tText: "A topic decides what is searched for and which streams belong to it. Switch = show topic yes/no; click opens its settings.",
    neuesThema: "+ New topic", tierSuche: "Search for animals …", tierSucheTitel: "Search for all animal topics",
    tierSucheText: "Animal streams are searched with these terms and then sorted into the animal topics by the words in their title (otherwise “Newly found”).",
    begriffe: "Search terms on YouTube (one per line)", tierwoerter: "Title must contain one of these words (one per line)",
    streams: (n) => (n === 1 ? "1 stream" : `${n} streams`), mitSuche: (n) => `${n} search terms`, ausBei: (x) => `off on ${x}`,
    passt: (n) => `matches ${n} of the existing streams`, zeigeStreams: "Show streams",
    aTitel: "Automation", aText: "How often the picture changes and when to search. SignageCast handles everything else itself.",
    abspielen: "Playback", suchenTitel: "Search", sperrwoerter: "Blocked words: title must not contain any (one per line)",
    orte: "Location from the title", orteText: "If one of the words is in the title, this location applies (for day/night). Separate several words with |.",
    muster: "Words in the title", zeileNeu: "+ Row", testen: "Test with a title …", erkannt: (m, b, l) => `recognised: “${m}” → ${b} / ${l}`,
    nichtErkannt: "no location recognised", musterFehler: "invalid pattern", weg: "Remove row",
    takt: "Minutes per stream", nurTag: "Only show streams where it is daytime", sonne: "Sun at least this high (degrees)",
    mindeststufe: "Minimum resolution", schlecht: "Picture may be bad for (s)", grenze: "Failures until blocked", sperre: "Block lasts (h)",
    sucheAktiv: "Search for new streams daily", begriffeWo: "What is searched for is set in", uhrzeit: "Time", max: "At most new streams per search", behalten: "Remove streams no longer found after (days)",
  },
};
const LT = () => LIVE_TEXTE[E && E.sprache === "en" ? "en" : "de"];

// ---------- Seitenfeld (Details rechts) ----------
let SF_ZU = null;
function seitenfeld(titel, koerper, beimSchliessen) {
  seitenfeldZu();
  const f = el(`<aside class="seitenfeld" role="dialog" aria-label="${esc(titel)}">
    <div class="sf-kopf"><h2>${esc(titel)}</h2><button type="button" class="knopf klein" data-zu aria-label="${esc(LT().schliessen)}">✕</button></div>
    <div class="sf-inhalt"></div></aside>`);
  f.querySelector(".sf-inhalt").appendChild(koerper);
  f.querySelector("[data-zu]").onclick = () => seitenfeldZu();
  document.body.appendChild(f);
  SF_ZU = beimSchliessen || null;
  const erstes = koerper.querySelector("input, select, textarea, button");
  if (erstes) erstes.focus({ preventScroll: true });
  return f;
}
function seitenfeldZu() {
  document.querySelectorAll(".seitenfeld").forEach((x) => x.remove());
  document.querySelectorAll(".lzeile.gewaehlt").forEach((x) => x.classList.remove("gewaehlt"));
  if (SF_ZU) { const z = SF_ZU; SF_ZU = null; z(); }
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && document.querySelector(".seitenfeld")) seitenfeldZu(); });

// ⋯-Menü (seltene und gefährliche Aktionen); Klicks darin öffnen nicht die Zeile
function mehrMenue(knoepfe) {
  const d = el(`<details class="mehr lz-mehr"><summary class="knopf klein" aria-label="${esc(LT().mehr)}">⋯</summary><div class="mehr-menue"></div></details>`);
  for (const [text, fn, gefahr] of knoepfe) {
    const b = el(`<button type="button" class="knopf ${gefahr ? "gefahr" : ""}">${esc(text)}</button>`);
    b.onclick = (e) => { e.stopPropagation(); d.open = false; fn(b); };
    d.querySelector(".mehr-menue").appendChild(b);
  }
  d.addEventListener("click", (e) => e.stopPropagation());
  return d;
}

// Ort suchen (OpenStreetMap über den Dienst) – füllt Breite/Länge
function ortSuche(fertig) {
  const L = LT();
  const w = el(`<div class="ortsuche"><div class="zeile"><input type="text" placeholder="${esc(L.ortSuchen)}" aria-label="${esc(L.ortSuchen)}">
    <button type="button" class="knopf">${esc(L.suchenKnopf)}</button></div><div class="ortsuche-erg"></div></div>`);
  const inp = w.querySelector("input"), erg = w.querySelector(".ortsuche-erg");
  const los = (knopf) => aktion(knopf, async () => {
    const d = await holen("/api/ort/suche?q=" + encodeURIComponent(inp.value.trim()));
    erg.innerHTML = "";
    if (!d.orte || !d.orte.length) { erg.textContent = L.keineOrte; return; }
    for (const o of d.orte) {
      const b = el(`<button type="button" class="knopf klein ortsuche-treffer">${esc(o.name)}</button>`);
      b.onclick = () => { fertig(o.breite, o.laenge, o.name); erg.innerHTML = ""; inp.value = ""; };
      erg.appendChild(b);
    }
  }, null);
  w.querySelector("button").onclick = (e) => los(e.target);
  inp.onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); los(w.querySelector("button")); } };
  return w;
}

// ---------- Übersicht ----------
const PROBLEME = ["nicht_live", "qualitaet", "pause", "gesperrt", "ohne_ort"];
async function liveSeite(inhalt) {
  const L = LT();
  const [st, status] = await Promise.all([holen("/api/streams"), holen("/api/status")]);
  STREAMS = st;
  const z = (f) => st.streams.filter(f).length;
  const probleme = PROBLEME.map((p) => [p, z((s) => s.zustand === p)]).filter(([, n]) => n);
  const letzte = status.liste && status.liste.suche;
  inhalt.innerHTML = `<div class="karte"><h2>${esc(L.uTitel)}</h2><p class="leise">${esc(L.uText)}</p>${rechtHinweis("youtube", L.recht)}${rechtHinweis("musik", L.musik)}
      <div class="kennzahlen">
        ${[["rotation", z((s) => s.in_rotation)], ["bereit", z((s) => s.zustand === "bereit")], ["nacht", z((s) => s.zustand === "nacht")],
          ["probleme", z((s) => PROBLEME.includes(s.zustand))]].map(([k, n]) =>
          `<button type="button" class="kennzahl ${k === "probleme" && n ? "warn" : ""}" data-gruppe="${k}"><b>${n}</b><span>${esc(L.zahlen[k])}</span></button>`).join("")}
      </div></div>
    <div class="karte"><h3>${esc(L.laeuftAuf)}</h3>
      ${status.fernseher.map((t) => `<div class="zeile"><b class="lv-kanal">${esc(t.name)}</b>
        <span>${t.aktuell ? esc(t.aktuell.name) : t.laeuft ? esc(L.nichts) : `<span class="leise">${esc(L.kanalAus)}</span>`}</span></div>`).join("")}</div>
    <div class="karte"><h3>${esc(L.probleme)}</h3>
      ${probleme.length ? probleme.map(([p, n]) => `<div class="zeile"><span>${esc(L.streams(n))}: ${esc(L.status[p])}</span>
        <button type="button" class="knopf klein" data-gruppe="probleme" data-zustand="${p}">${esc(L.ansehen)}</button></div>`).join("")
        : `<p class="gut">${esc(L.keineProbleme)}</p>`}</div>
    <div class="karte"><h3>${esc(L.suche)}</h3>
      <p>${esc(E.suche.aktiv ? L.sucheAn(E.suche.uhrzeit) : L.sucheAus)}${letzte ? ` · ${esc(L.letzte)}: ${esc(letzte.zeit || "")}${letzte.neu ? " – " + esc(L.ergebnis(letzte.neu.length, letzte.gefunden ?? "?")) : ""}` : ""}</p>
      <div class="zeile"><button type="button" class="knopf" id="lvSuchen">${esc(L.jetztSuchen)}</button>
        <a class="knopf" href="#automatik">${esc(L.einstellen)}</a><span class="leise" id="lvErg"></span></div></div>`;
  inhalt.querySelectorAll("[data-gruppe]").forEach((b) => {
    b.onclick = () => { SF = Object.assign(SF, { gruppe: b.dataset.gruppe, zustand: b.dataset.zustand || "", kat: "", text: "" }); sfMerken(); zeigeSeite("streams"); };
  });
  $("#lvSuchen").onclick = (e) => aktion(e.target, async () => {
    $("#lvErg").textContent = L.laeuft;
    const r = await senden("/api/suche/starten");
    $("#lvErg").textContent = r.suche.pause ? T.pause : L.ergebnis((r.suche.neu || []).length, r.suche.gefunden ?? "?");
  }, null);
}

// ---------- Sammlung ----------
let STREAMS = null;
let SF = { text: "", kat: "", gruppe: "alle", zustand: "" };           // Filter der Sammlung, merkt sich der Browser
try { SF = Object.assign(SF, JSON.parse(localStorage.getItem("signagecast-sammlung") || "{}")); } catch (_) { /* egal */ }
function sfMerken() { try { localStorage.setItem("signagecast-sammlung", JSON.stringify(SF)); } catch (_) { /* egal */ } }
const GRUPPE = {
  alle: () => true, rotation: (s) => s.in_rotation, bereit: (s) => s.zustand === "bereit", nacht: (s) => s.zustand === "nacht",
  probleme: (s) => PROBLEME.includes(s.zustand), aus: (s) => ["inaktiv", "kategorie_aus"].includes(s.zustand), gefunden: (s) => s.herkunft === "entdeckt",
};
function dauerKurz(s) { const m = Math.max(0, Math.round(s / 60)); return m >= 60 ? `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")} h` : `${m} min`; }
function statusText(s) {
  const L = LT(), z = s.in_rotation ? "rotation" : s.zustand;
  if (!z) return ["", ""];
  let t = L.status[z] || z;
  if (z === "nacht" && s.nachlauf) t = L.status.nachlauf;
  else if (z === "nacht" && s.hell_ab) t += " · " + L.hellIn(dauerKurz(s.hell_ab - Date.now() / 1000));
  if (z === "pause" && s.pause_bis) t += " " + L.bis(new Date(s.pause_bis * 1000).toLocaleTimeString(ORT(), { hour: "2-digit", minute: "2-digit" }));
  if (z === "qualitaet" && s.angeboten_hoehe) t += " (" + L.angebot(s.angeboten_hoehe + "p") + ")";
  const stil = { rotation: "gut", bereit: "gut", qualitaet: "schlecht", gesperrt: "schlecht", pause: "warn", ohne_ort: "warn", ungeprueft: "warn", nicht_live: "warn" }[z] || "";
  return [t, stil];
}
async function streamsSeite(inhalt) {
  const L = LT();
  inhalt.innerHTML = `<div class="karte"><div class="lv-kopf"><div><h2>${esc(L.sTitel)}</h2><p class="leise">${esc(L.sText)}</p></div>
        <button type="button" class="knopf haupt" id="sNeu">${esc(L.neu)}</button></div>
      <div class="zeile"><input type="search" id="sText" placeholder="${esc(L.suchen)}" aria-label="${esc(L.suchen)}" value="${esc(SF.text)}">
        <select id="sKat" aria-label="${esc(L.thema)}"><option value="">${esc(L.alleThemen)}</option>${katOptionen(SF.kat)}</select></div>
      <div class="marken" id="sGruppen" role="group"></div><div class="leise" id="sZahl"></div></div>
    <div class="lliste" id="sListe"></div>
    <details class="karte" id="sNie"><summary></summary><p class="leise">${esc(L.nieText)}</p><div id="sNieListe"></div></details>`;
  $("#sNeu").onclick = () => streamNeu();
  $("#sText").addEventListener("input", (e) => { SF.text = e.target.value; sfMerken(); sammlungZeichnen(); });
  $("#sKat").onchange = (e) => { SF.kat = e.target.value; sfMerken(); sammlungZeichnen(); };
  await streamsLaden();
}
async function streamsLaden() { STREAMS = await holen("/api/streams"); sammlungZeichnen(); }
function sammlungZeichnen() {
  const L = LT(), liste = $("#sListe");
  if (!liste || !STREAMS) return;
  const t = SF.text.toLowerCase();
  const vor = STREAMS.streams.filter((s) => (!t || (s.name + " " + (s.titel || "") + " " + s.id).toLowerCase().includes(t)) && (!SF.kat || s.kategorie === SF.kat));
  const gezeigt = vor.filter((s) => (GRUPPE[SF.gruppe] || GRUPPE.alle)(s) && (!SF.zustand || s.zustand === SF.zustand));
  const g = $("#sGruppen"); g.innerHTML = "";
  for (const k of Object.keys(L.gruppen)) {
    const n = vor.filter(GRUPPE[k]).length;
    if (k !== "alle" && !n && SF.gruppe !== k) continue;
    const an = SF.gruppe === k;
    const b = el(`<button type="button" class="knopf klein ${an ? "haupt" : ""}" aria-pressed="${an}">${esc(L.gruppen[k])} ${n}</button>`);
    b.onclick = () => { SF.gruppe = k; SF.zustand = ""; sfMerken(); sammlungZeichnen(); };
    g.appendChild(b);
  }
  $("#sZahl").textContent = L.anzahl(gezeigt.length, STREAMS.streams.length);
  liste.innerHTML = "";
  for (const s of gezeigt) liste.appendChild(streamZeile(s));
  const nie = STREAMS.abgelehnt || [];
  $("#sNie").hidden = !nie.length;
  $("#sNie summary").textContent = L.nieListe(nie.length);
  $("#sNieListe").innerHTML = "";
  for (const a of nie) {
    const z = el(`<div class="zeile"><code>${esc(a)}</code><button type="button" class="knopf klein">${esc(L.freigeben)}</button></div>`);
    z.querySelector("button").onclick = (e) => aktion(e.target, async () => { await senden(`/api/abgelehnt/${encodeURIComponent(a)}/freigeben`); await streamsLaden(); });
    $("#sNieListe").appendChild(z);
  }
}
const streamPfad = (s) => `/api/streams/${encodeURIComponent(s.id)}`;
function streamZeile(s) {
  const L = LT(), [st, stil] = statusText(s);
  const z = el(`<div class="lzeile" tabindex="0" role="button" data-id="${esc(s.id)}">
    <div class="lz-haupt"><div class="lz-name">${esc(s.name)}${s.herkunft === "entdeckt" ? ` <span class="marke">${esc(L.gefundenMarke)}</span>` : ""}</div>
      <div class="lz-info">${esc(katName(s.kategorie))}${s.breite == null ? ` · <span class="warn">${esc(L.ohneOrt)}</span>` : ""}</div></div>
    <div class="lz-status ${stil}">${esc(st)}</div>
    <div class="lz-aktion">${schalter("aktiv", s.aktiv !== false)}</div></div>`);
  const sw = z.querySelector(".schalter");
  sw.title = L.aktiv;
  sw.addEventListener("click", (e) => e.stopPropagation());
  sw.querySelector("input").onchange = (e) => aktion(null, async () => { await senden(streamPfad(s), { aktiv: e.target.checked }); await streamsLaden(); });
  z.querySelector(".lz-aktion").appendChild(mehrMenue([
    [L.zeigen, (b) => aktion(b, () => senden(streamPfad(s) + "/zeigen", { video_id: s.video_id, tv: null }), L.zeigenOk)],
    [L.nieWieder, (b) => { if (confirm(L.wirklichNie)) aktion(b, async () => { await senden(streamPfad(s) + "/entfernen", { ablehnen: true }); seitenfeldZu(); await streamsLaden(); }); }, true],
    [L.entfernen, (b) => { if (confirm(L.wirklichEntfernen)) aktion(b, async () => { await senden(streamPfad(s) + "/entfernen"); seitenfeldZu(); await streamsLaden(); }); }, true],
  ]));
  const oeffnen = () => { streamDetails(s); z.classList.add("gewaehlt"); };
  z.onclick = oeffnen;
  z.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); oeffnen(); } };
  return z;
}
function streamFelder(s) {
  const L = LT();
  const f = el(`<div>
    <div class="feld"><label>${esc(L.name)}</label><input type="text" name="name" value="${esc(s.name || "")}" placeholder="${esc(L.nameLeer)}"></div>
    <div class="feld"><label>${esc(L.thema)}</label><select name="kategorie">${katOptionen(s.kategorie || "neu")}</select></div>
    <div class="feld"><label>${esc(L.ort)}</label><div class="zeile"><input type="number" step="0.0001" name="breite" class="b120" value="${s.breite ?? ""}" placeholder="${esc(L.breite)}" aria-label="${esc(L.breite)}">
      <input type="number" step="0.0001" name="laenge" class="b120" value="${s.laenge ?? ""}" placeholder="${esc(L.laenge)}" aria-label="${esc(L.laenge)}"></div>
      <p class="leise">${esc(L.ortAuto)}</p></div></div>`);
  f.querySelector(".feld:last-child").appendChild(ortSuche((b, l) => { f.querySelector("[name=breite]").value = b; f.querySelector("[name=laenge]").value = l; }));
  f.lesen = () => {
    const d = { name: f.querySelector("[name=name]").value.trim(), kategorie: f.querySelector("[name=kategorie]").value };
    const b = f.querySelector("[name=breite]").value, l = f.querySelector("[name=laenge]").value;
    d.breite = b === "" ? null : Number(b); d.laenge = l === "" ? null : Number(l);
    return d;
  };
  return f;
}
function streamNeu() {
  const L = LT();
  const k = el(`<div><div class="feld"><label>${esc(L.link)}</label><input type="url" name="link" placeholder="https://www.youtube.com/watch?v=…"></div></div>`);
  const felder = streamFelder({ kategorie: "neu" });
  k.appendChild(felder);
  k.appendChild(el(`<div class="zeile"><button type="button" class="knopf haupt">${esc(L.hinzu)}</button></div>`));
  k.querySelector(".haupt").onclick = (e) => aktion(e.target, async () => {
    await senden("/api/streams", Object.assign({ link: k.querySelector("[name=link]").value }, felder.lesen()));
    seitenfeldZu(); await streamsLaden();
  });
  seitenfeld(L.neu.replace(/^\+\s*/, ""), k);
}
function streamDetails(s) {
  const L = LT(), q = s.qualitaet || {}, [st, stil] = statusText(s);
  const anteil = q.anteil_720p_plus != null ? Math.round(q.anteil_720p_plus * 100) : null;
  const k = el(`<div>
    <p><span class="marke ${stil}">${esc(st)}</span> <a href="https://www.youtube.com/watch?v=${encodeURIComponent(s.video_id || s.id)}" target="_blank" rel="noopener">YouTube ↗</a></p>
    ${s.titel && s.titel !== s.name ? `<p class="leise">${esc(s.titel)}</p>` : ""}
    <div class="zeile">${schalter("aktiv", s.aktiv !== false)}<span>${esc(L.aktiv)}</span></div>
    <div class="zeile">${schalter("geschuetzt", s.geschuetzt)}<span>${esc(L.geschuetzt)}</span></div>
    <p class="leise">${esc(L.geschuetztText)}</p></div>`);
  const felder = streamFelder(s);
  k.appendChild(felder);
  k.appendChild(el(`<div class="zeile"><button type="button" class="knopf haupt" data-a="speichern">${esc(L.speichern)}</button>
    <button type="button" class="knopf" data-a="zeigen">${esc(L.zeigen)}</button>
    ${E.fernseher.length > 1 ? `<label>${esc(L.zeigenAuf)} <select name="tv"><option value="">${esc(L.alleKanaele)}</option>${E.fernseher.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select></label>` : ""}</div>`));
  if (s.herkunft === "entdeckt") k.appendChild(el(`<div class="feld"><button type="button" class="knopf" data-a="uebernehmen">${esc(L.uebernehmen)}</button><p class="leise">${esc(L.uebernehmenText)}</p></div>`));
  k.appendChild(el(`<details class="erweitert"><summary>${esc(L.technik)}</summary>
    <p>${esc(L.aufloesung)}: ${s.angeboten_hoehe ? esc(s.angeboten_hoehe + "p") : "–"}</p>
    ${anteil != null ? `<p>${esc(L.anteil(anteil, q.proben))}</p>` : ""}
    ${q.codecs && q.codecs.length ? `<p>${esc(L.codecs)}: ${esc(q.codecs.map((c) => c.split(".")[0]).join(", "))}</p>` : ""}
    <p>${esc(L.ausfaelle)}: ${s.strikes ? s.strikes : esc(L.keine)}</p>
    ${(s.strike_gruende || []).length ? `<ul class="leise">${s.strike_gruende.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>` : ""}
    ${s.strikes ? `<button type="button" class="knopf" data-a="strikes">${esc(L.ausfaelleWeg)}</button>` : ""}
    <p class="leise">ID ${esc(s.id)}</p></details>`));
  k.appendChild(el(`<div class="zeile gefahrzone"><button type="button" class="knopf gefahr" data-a="entfernen">${esc(L.entfernen)}</button>
    <button type="button" class="knopf gefahr" data-a="nie">${esc(L.nieWieder)}</button></div>`));
  const pfad = streamPfad(s);
  k.querySelectorAll(".schalter input").forEach((i) => { i.onchange = () => aktion(null, async () => { await senden(pfad, { [i.name]: i.checked }); await streamsLaden(); }); });
  k.querySelectorAll("[data-a]").forEach((b) => {
    b.onclick = () => {
      const a = b.dataset.a;
      if (a === "speichern") return aktion(b, async () => { await senden(pfad, felder.lesen()); await streamsLaden(); seitenfeldZu(); });
      if (a === "zeigen") return aktion(b, () => senden(pfad + "/zeigen", { video_id: s.video_id, tv: (k.querySelector("[name=tv]") || {}).value || null }), L.zeigenOk);
      if (a === "uebernehmen") return aktion(b, async () => { await senden(pfad, { herkunft: "fest" }); await streamsLaden(); seitenfeldZu(); });
      if (a === "strikes") return aktion(b, async () => { await senden(pfad + "/strikes-zuruecksetzen", { video_id: s.video_id }); await streamsLaden(); seitenfeldZu(); });
      if (a === "entfernen" && confirm(L.wirklichEntfernen)) return aktion(b, async () => { await senden(pfad + "/entfernen"); seitenfeldZu(); await streamsLaden(); });
      if (a === "nie" && confirm(L.wirklichNie)) return aktion(b, async () => { await senden(pfad + "/entfernen", { ablehnen: true }); seitenfeldZu(); await streamsLaden(); });
    };
  });
  seitenfeld(s.name, k);
}

// ---------- Themen (früher Kategorien) ----------
async function kategorienSeite(inhalt) {
  const L = LT();
  const st = await holen("/api/streams");
  STREAMS = st;
  const anzahl = {};
  for (const x of st.streams) anzahl[x.kategorie] = (anzahl[x.kategorie] || 0) + 1;
  const ks = JSON.parse(JSON.stringify(E.kategorien));
  const zeilen = (t) => t.value.split("\n").map((x) => x.trim()).filter(Boolean);
  const aus = (k, i) => (i == null ? E.video.kategorien_aus.includes(k.id) : E.fernseher[i].kategorien_aus.includes(k.id));
  // alle Themen auf einmal speichern (wie bisher): Inhalte + wo ein-/ausgeschaltet
  const speichern = (knopf, an) => aktion(knopf, async () => {
    const istAn = (k, i) => (an && an[k.id] && an[k.id][i == null ? "alle" : i] != null ? an[k.id][i == null ? "alle" : i] : !aus(k, i));
    E = (await senden("/api/einstellungen", {
      kategorien: ks.map(({ id, name, gruppe, begriffe, woerter, ohne_tag, ohne_tag_woerter }) => ({ id, name, gruppe, begriffe, woerter, ohne_tag, ohne_tag_woerter })),
      video: { kategorien_aus: ks.filter((k) => !istAn(k)).map((k) => k.id) },
      fernseher: E.fernseher.map((t, i) => ({ ...t, kategorien_aus: ks.filter((k) => !istAn(k, i)).map((k) => k.id) })),
    })).einstellungen;
    seitenfeldZu();
    await kategorienSeite(inhalt);
  });
  inhalt.innerHTML = `<div class="karte"><div class="lv-kopf"><div><h2>${esc(L.tTitel)}</h2><p class="leise">${esc(L.tText)}</p></div>
      <button type="button" class="knopf haupt" id="tNeu" ${ks.length >= KAT_GRENZEN[0] ? "disabled" : ""}>${esc(L.neuesThema)}</button></div></div>
    <div id="tListe"></div>`;
  const liste = $("#tListe");
  for (const g of ["tiere", "themen"]) {
    const inGruppe = ks.filter((k) => k.gruppe === g);
    if (!inGruppe.length) continue;
    const kopf = el(`<div class="gruppenkopf"><h3>${esc(T.katGruppe[g])}</h3></div>`);
    if (g === "tiere") {
      const b = el(`<button type="button" class="knopf klein">${esc(L.tierSuche)}</button>`);
      b.onclick = () => tierSuche();
      kopf.appendChild(b);
    }
    liste.appendChild(kopf);
    const l = el(`<div class="lliste"></div>`);
    for (const k of inGruppe) l.appendChild(zeile(k));
    liste.appendChild(l);
  }
  $("#tNeu").onclick = () => {
    let id; do { id = "k" + Math.random().toString(36).slice(2, 7).replace(/[^a-z0-9]/g, "0"); } while (ks.some((x) => x.id === id));
    const k = { id, eingebaut: false, name: "", gruppe: "themen", begriffe: [], woerter: [], ohne_tag: false, ohne_tag_woerter: [], neu: true };
    ks.push(k);
    details(k, () => { const i = ks.indexOf(k); if (i >= 0 && k.neu && !k._gespeichert) ks.splice(i, 1); });
  };

  function zeile(k) {
    const n = anzahl[k.id] || 0;
    const tvAus = E.fernseher.filter((t, i) => aus(k, i));
    const info = [L.streams(n), aus(k) ? "" : tvAus.length ? L.ausBei(tvAus.map((t) => t.name).join(", ")) : "", k.begriffe.length ? L.mitSuche(k.begriffe.length) : ""].filter(Boolean).join(" · ");
    const z = el(`<div class="lzeile" tabindex="0" role="button">
      <div class="lz-haupt"><div class="lz-name">${esc(k.name || T.kat[k.id] || k.id)}${!k.eingebaut ? ` <span class="marke">${esc(T.katEigene)}</span>` : k.standard === false ? ` <span class="marke">${esc(T.katGeaendert)}</span>` : ""}</div>
        <div class="lz-info">${esc(info)}</div></div>
      <div class="lz-aktion">${schalter("alle", !aus(k))}</div></div>`);
    const sw = z.querySelector(".schalter");
    sw.addEventListener("click", (e) => e.stopPropagation());
    sw.querySelector("input").onchange = (e) => speichern(null, { [k.id]: { alle: e.target.checked } });
    const oeffnen = () => { details(k); z.classList.add("gewaehlt"); };
    z.onclick = oeffnen;
    z.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); oeffnen(); } };
    return z;
  }

  function details(k, beimSchliessen) {
    const n = anzahl[k.id] || 0, std = KAT_STANDARD.find((x) => x.id === k.id), istNeu = k.id === "neu";
    const f = el(`<div>
      <div class="feld"><label>${esc(T.katNameFeld)}</label><input type="text" name="name" maxlength="40" value="${esc(k.name)}" placeholder="${esc(k.eingebaut ? T.kat[k.id] || k.id : T.katNamePflicht)}"></div>
      ${istNeu ? `<p class="leise">${esc(T.katNeuText)}</p>` : `<div class="feld"><label>${esc(T.katGruppeWahl)}</label><select name="gruppe">${["tiere", "themen"].map((g) =>
        `<option value="${g}" ${g === k.gruppe ? "selected" : ""}>${esc(T.katGruppe[g])}</option>`).join("")}</select></div>`}
      <h4>${esc(T.katWo)}</h4>
      <div class="zeile">${schalter("alle", !aus(k))}<span>${esc(T.katAlle)}</span></div>
      ${E.fernseher.length > 1 ? E.fernseher.map((t, i) => `<div class="zeile">${schalter("tv" + i, !aus(k, i))}<span>${esc(t.name)}</span></div>`).join("") : ""}
      ${istNeu ? "" : `
      <div class="feld"><label>${esc(T.katBegriffe(KAT_GRENZEN[1]))}</label><p class="leise">${esc(k.gruppe === "tiere" ? T.katBegriffeTiere : T.katBegriffeThemen)}</p>
        <textarea name="begriffe" rows="3" spellcheck="false">${esc((k.begriffe || []).join("\n"))}</textarea></div>
      <div class="feld"><label>${esc(T.katWoerter)}</label><p class="leise">${esc(k.gruppe === "tiere" ? T.katWoerterTiere : T.katWoerterThemen)}</p>
        <textarea name="woerter" rows="3" spellcheck="false">${esc((k.woerter || []).join("\n"))}</textarea><p class="leise" data-passt></p></div>
      <div class="zeile">${schalter("ohne_tag", k.ohne_tag)}<span>${esc(T.katOhneTag)}</span></div>
      <details class="erweitert"><summary>${esc(T.katOhneTagWoerter)}</summary>
        <textarea name="ohne_tag_woerter" rows="2" spellcheck="false">${esc((k.ohne_tag_woerter || []).join("\n"))}</textarea></details>`}
      <div class="zeile"><button type="button" class="knopf haupt" data-a="speichern">${esc(L.speichern)}</button>
        ${n ? `<button type="button" class="knopf" data-a="streams">${esc(L.zeigeStreams)}</button>` : ""}
        ${std && !istNeu ? `<button type="button" class="knopf" data-a="standard">${esc(T.katStandard)}</button>` : ""}</div>
      ${!k.eingebaut && !k.neu ? `<div class="gefahrzone"><div class="zeile"><label>${esc(T.katVerschieben(n))}</label>
        <select name="ziel">${ks.filter((x) => x.id !== k.id && !x.neu).map((x) => `<option value="${esc(x.id)}" ${x.id === "neu" ? "selected" : ""}>${esc(x.name || T.kat[x.id] || x.id)}</option>`).join("")}</select>
        <button type="button" class="knopf gefahr" data-a="loeschen">${esc(T.entfernen)}</button></div></div>` : ""}</div>`);
    const w = (name) => f.querySelector(`[name=${name}]`);
    // Wie viele vorhandene Streams passen auf die Wörter im Titel? (Hilfe beim Formulieren)
    const passt = () => {
      const p = f.querySelector("[data-passt]"); if (!p) return;
      const rx = zeilen(w("woerter")).map((x) => { try { return new RegExp(x, "i"); } catch (_) { return null; } }).filter(Boolean);
      p.textContent = rx.length ? L.passt(STREAMS.streams.filter((s) => rx.some((r) => r.test(s.titel || s.name))).length) : "";
    };
    if (w("woerter")) { w("woerter").addEventListener("input", passt); passt(); }
    const lesen = () => {
      k.name = w("name").value.trim();
      if (w("gruppe")) {
        k.gruppe = w("gruppe").value; k.begriffe = zeilen(w("begriffe")); k.woerter = zeilen(w("woerter"));
        k.ohne_tag = w("ohne_tag").checked; k.ohne_tag_woerter = zeilen(w("ohne_tag_woerter"));
      }
      const an = { alle: w("alle").checked };
      E.fernseher.forEach((_, i) => { an[i] = w("tv" + i) ? w("tv" + i).checked : an.alle; });
      return { [k.id]: an };
    };
    f.querySelectorAll("[data-a]").forEach((b) => {
      b.onclick = () => {
        const a = b.dataset.a;
        if (a === "speichern") { k._gespeichert = true; return speichern(b, lesen()); }
        if (a === "streams") { SF = Object.assign(SF, { kat: k.id, text: "", gruppe: "alle", zustand: "" }); sfMerken(); seitenfeldZu(); return zeigeSeite("streams"); }
        if (a === "standard") {
          w("name").value = ""; w("gruppe").value = std.gruppe; w("begriffe").value = std.begriffe.join("\n");
          w("woerter").value = std.woerter.join("\n"); w("ohne_tag").checked = std.ohne_tag; w("ohne_tag_woerter").value = std.ohne_tag_woerter.join("\n");
          return passt();
        }
        if (a === "loeschen") return aktion(b, async () => {
          E = (await senden("/api/kategorien/loeschen", { id: k.id, ziel: w("ziel").value })).einstellungen;
          seitenfeldZu(); await kategorienSeite(inhalt);
        });
      };
    });
    seitenfeld(k.name || T.kat[k.id] || L.neuesThema.replace(/^\+\s*/, ""), f, beimSchliessen);
  }

  function tierSuche() {
    const f = el(`<div><p class="leise">${esc(L.tierSucheText)}</p>
      <div class="feld"><label>${esc(L.begriffe)}</label><textarea name="begriffe" rows="8" spellcheck="false">${esc(E.suche.begriffe.join("\n"))}</textarea></div>
      <div class="feld"><label>${esc(L.tierwoerter)}</label><textarea name="tier" rows="8" spellcheck="false">${esc(E.suche.tierwoerter.join("\n"))}</textarea></div>
      <div class="zeile"><button type="button" class="knopf haupt">${esc(L.speichern)}</button></div></div>`);
    f.querySelector("button").onclick = (e) => aktion(e.target, async () => {
      await speichernE({ suche: { begriffe: zeilen(f.querySelector("[name=begriffe]")), tierwoerter: zeilen(f.querySelector("[name=tier]")) } }, null);
      seitenfeldZu();
    });
    seitenfeld(L.tierSucheTitel, f);
  }
}

// ---------- Automatik (früher Stream-Suche + Regeln) ----------
async function automatikSeite(inhalt) {
  const L = LT(), v = E.video, s = E.suche;
  const status = await holen("/api/status");
  const letzte = status.liste && status.liste.suche;
  const zahl = (id, w, min, max, step) => `<input type="number" id="${id}" value="${w}" min="${min}" max="${max}" step="${step || 1}" class="b120">`;
  inhalt.innerHTML = `<div class="karte"><h2>${esc(L.aTitel)}</h2><p class="leise">${esc(L.aText)}</p></div>
    <div class="karte"><h3>${esc(L.abspielen)}</h3>
      <div class="zeile"><label>${esc(L.takt)}</label>${zahl("aTakt", v.takt_min, 1, 30)}</div>
      <div class="zeile"><label>${esc(L.nurTag)}</label>${schalter("nurTag", v.nur_tag)}</div>
      <div class="zeile"><label>${esc(L.sonne)}</label>${zahl("aSonne", v.min_sonnenhoehe, -18, 30, 0.5)}</div>
      <details class="erweitert"><summary>${esc(L.erweitert)}</summary>
        <div class="zeile"><label>${esc(L.mindeststufe)}</label><select id="aStufe">${STUFEN.map((x) => `<option value="${x}" ${x === v.mindeststufe ? "selected" : ""}>${esc(stufeText(x))}</option>`).join("")}</select></div>
        <div class="zeile"><label>${esc(L.schlecht)}</label>${zahl("aSchlecht", v.schlecht_s, 5, 170)}</div>
        <div class="zeile"><label>${esc(L.grenze)}</label>${zahl("aGrenze", v.strike_grenze, 1, 20)}</div>
        <div class="zeile"><label>${esc(L.sperre)}</label>${zahl("aSperre", v.sperre_h, 0, 72, 0.5)}</div></details></div>
    <div class="karte"><h3>${esc(L.suchenTitel)}</h3>
      <div class="zeile"><label>${esc(L.sucheAktiv)}</label>${schalter("sAktiv", s.aktiv)}</div>
      <div class="zeile"><label>${esc(L.uhrzeit)}</label><input type="time" id="aUhr" value="${esc(s.uhrzeit)}"></div>
      <div class="zeile"><label>${esc(L.max)}</label>${zahl("aMax", s.max, 0, 200)}</div>
      <div class="zeile"><label>${esc(L.behalten)}</label>${zahl("aBehalten", s.behalten_tage, 1, 365)}</div>
      <div class="zeile"><button type="button" class="knopf" id="aJetzt">${esc(L.jetztSuchen)}</button>
        <span class="leise" id="aErg">${letzte ? esc(L.letzte + ": " + (letzte.zeit || "")) + (letzte.neu ? " – " + esc(L.ergebnis(letzte.neu.length, letzte.gefunden ?? "?")) : "") : ""}</span></div>
      <p class="leise">${esc(L.begriffeWo)} <a href="#kategorien">${esc(L.tTitel)}</a></p>
      <details class="erweitert"><summary>${esc(L.erweitert)}</summary>
        <div class="feld"><label>${esc(L.sperrwoerter)}</label><textarea id="aNein" rows="5" spellcheck="false">${esc(s.ausschluss.join("\n"))}</textarea></div>
        <div class="feld"><label>${esc(L.orte)}</label><p class="leise">${esc(L.orteText)}</p>
          <div class="tabelle-rahmen"><table class="tabelle orte"><thead><tr><th>${esc(L.muster)}</th><th>${esc(L.breite)}</th><th>${esc(L.laenge)}</th><th></th></tr></thead>
            <tbody id="aOrte"></tbody></table></div>
          <div class="zeile"><button type="button" class="knopf klein" id="aOrtNeu">${esc(L.zeileNeu)}</button></div>
          <div class="zeile"><input type="text" id="aTest" placeholder="${esc(L.testen)}" aria-label="${esc(L.testen)}" class="breit"><span id="aTestErg" class="leise"></span></div></div>
      </details></div>
    <div class="zeile"><button type="button" class="knopf haupt" id="aOk">${esc(L.speichern)}</button></div>`;
  const body = $("#aOrte");
  const ortZeile = (o) => {
    const tr = el(`<tr><td><input type="text" name="muster" value="${esc(o.muster)}" spellcheck="false" aria-label="${esc(L.muster)}"></td>
      <td><input type="number" step="0.01" name="breite" value="${o.breite ?? ""}" class="b90" aria-label="${esc(L.breite)}"></td>
      <td><input type="number" step="0.01" name="laenge" value="${o.laenge ?? ""}" class="b90" aria-label="${esc(L.laenge)}"></td>
      <td><button type="button" class="knopf klein" data-ort title="${esc(L.ortSuchen)}">📍</button>
        <button type="button" class="knopf klein gefahr" data-weg title="${esc(L.weg)}" aria-label="${esc(L.weg)}">✕</button></td></tr>`);
    tr.querySelector("[data-weg]").onclick = () => { tr.remove(); testen(); };
    tr.querySelector("[data-ort]").onclick = () => {
      const alt = body.querySelector(".ortzeile-suche"); if (alt) alt.remove();
      const z = el(`<tr class="ortzeile-suche"><td colspan="4"></td></tr>`);
      z.firstElementChild.appendChild(ortSuche((b, l) => { tr.querySelector("[name=breite]").value = b; tr.querySelector("[name=laenge]").value = l; z.remove(); }));
      tr.after(z); z.querySelector("input").focus();
    };
    tr.querySelector("[name=muster]").addEventListener("input", testen);
    return tr;
  };
  const orte = () => [...body.querySelectorAll("tr:not(.ortzeile-suche)")].map((tr) => ({ muster: tr.querySelector("[name=muster]").value.trim(),
    breite: Number(tr.querySelector("[name=breite]").value), laenge: Number(tr.querySelector("[name=laenge]").value) })).filter((o) => o.muster);
  // wie der Dienst: das erste passende Muster gewinnt (Groß/klein egal)
  function testen() {
    const t = $("#aTest").value, erg = $("#aTestErg");
    if (!t.trim()) { erg.textContent = ""; return; }
    for (const o of orte()) {
      let r; try { r = new RegExp(o.muster, "i"); } catch (_) { erg.textContent = L.musterFehler + ": " + o.muster; return; }
      const m = t.match(r);
      if (m) { erg.textContent = L.erkannt(m[0], o.breite, o.laenge); return; }
    }
    erg.textContent = L.nichtErkannt;
  }
  for (const o of s.orte) body.appendChild(ortZeile(o));
  $("#aOrtNeu").onclick = () => { const tr = ortZeile({ muster: "", breite: "", laenge: "" }); body.appendChild(tr); tr.querySelector("input").focus(); };
  $("#aTest").addEventListener("input", testen);
  const n = (id) => Number($("#" + id).value);
  const zeilen = (id) => $("#" + id).value.split("\n").map((x) => x.trim()).filter(Boolean);
  $("#aOk").onclick = (e) => speichernE({
    video: { takt_min: n("aTakt"), nur_tag: $("[name=nurTag]").checked, min_sonnenhoehe: n("aSonne"), mindeststufe: $("#aStufe").value,
             schlecht_s: n("aSchlecht"), strike_grenze: n("aGrenze"), sperre_h: n("aSperre") },
    suche: { aktiv: $("[name=sAktiv]").checked, uhrzeit: $("#aUhr").value, max: n("aMax"), behalten_tage: n("aBehalten"), ausschluss: zeilen("aNein"), orte: orte() },
  }, e.target);
  $("#aJetzt").onclick = (e) => aktion(e.target, async () => {
    $("#aErg").textContent = L.laeuft;
    const r = await senden("/api/suche/starten");
    $("#aErg").textContent = r.suche.pause ? T.pause : L.ergebnis((r.suche.neu || []).length, r.suche.gefunden ?? "?");
  }, null);
}
