// SignageCast – CSV-Import (seit 0.26), allgemein gehalten: nicht an die Datenquellen gebunden, damit andere Reiter ihn
// wiederverwenden können. Der Dienst liest die Datei (POST /api/csv/analysieren, app/csvimport.py), hier wählt man
// Trennzeichen, Anführungszeichen, Kopfzeile, Zeichensatz und welche Spalten unter welchem Namen übernommen werden.
//
//   const imp = await csvImport(ziel, herkunft, optionen, beiAenderung)
//     herkunft: { daten: "<base64>" } | { datei: "<hash>" } | { quelle: {…} }   – woher der Dienst die CSV liest
//     optionen: { trenner, anfuehrung, kopfzeile, kodierung, felder: [{ spalte, name }] }  (fehlende werden erkannt)
//     beiAenderung(optionen, analyse): nach jeder Änderung; imp.optionen() / imp.felder() liefern den Stand
// Nutzt die Hilfsfunktionen aus tv.js (senden, esc, E).
"use strict";

const CTEXTE = {
  de: {
    trenner: "Trennzeichen", anfuehrung: "Anführungszeichen", kopfzeile: "erste Zeile enthält die Spaltennamen", kodierung: "Zeichensatz",
    trennerName: { ",": "Komma ( , )", ";": "Semikolon ( ; )", tab: "Tabulator", "|": "senkrechter Strich ( | )", " ": "Leerzeichen" },
    anfName: { '"': 'doppelte ( " )', "'": "einfache ( ' )", "": "keine" },
    kodName: { auto: "automatisch", "utf-8": "UTF-8", cp1252: "Windows (Excel)", "latin-1": "ISO-8859-1" },
    erkannt: "erkannt", spalten: "Spalten – Haken = übernehmen, Name frei wählbar", spalte: "Spalte", feld: "Feldname", beispiele: "Beispiele",
    zeilen: (n) => `${n} Datenzeilen`, abgeschnitten: "(nur die ersten 5000)", vorschau: "Vorschau", alle: "alle", keine: "keine",
    laedt: "Lese die Datei …",
  },
  en: {
    trenner: "Delimiter", anfuehrung: "Quote character", kopfzeile: "first row contains the column names", kodierung: "Character set",
    trennerName: { ",": "comma ( , )", ";": "semicolon ( ; )", tab: "tab", "|": "vertical bar ( | )", " ": "space" },
    anfName: { '"': 'double ( " )', "'": "single ( ' )", "": "none" },
    kodName: { auto: "automatic", "utf-8": "UTF-8", cp1252: "Windows (Excel)", "latin-1": "ISO-8859-1" },
    erkannt: "detected", spalten: "Columns – tick = import, name can be changed", spalte: "Column", feld: "Field name", beispiele: "Examples",
    zeilen: (n) => `${n} data rows`, abgeschnitten: "(first 5000 only)", vorschau: "Preview", alle: "all", keine: "none",
    laedt: "Reading the file …",
  },
};
const CT = () => CTEXTE[E.sprache] || CTEXTE.de;

async function csvImport(ziel, herkunft, optionen, beiAenderung) {
  const C = CT();
  const o = Object.assign({ felder: [] }, JSON.parse(JSON.stringify(optionen || {})));
  let a = null;                       // letzte Analyse des Dienstes
  let breite = null;                  // Spaltenzahl der letzten Analyse (ändert sie sich, gilt die Auswahl nicht mehr)

  const analysieren = async () => {
    ziel.innerHTML = `<p class="leise">${esc(C.laedt)}</p>`;
    try {
      a = await senden("/api/csv/analysieren", Object.assign({}, herkunft,
        { optionen: { trenner: o.trenner, anfuehrung: o.anfuehrung, kopfzeile: o.kopfzeile, kodierung: o.kodierung } }));
    } catch (e) {
      ziel.innerHTML = `<p class="schlecht">${esc(e.message)}</p>`;
      throw e;
    }
    Object.assign(o, { trenner: a.optionen.trenner, anfuehrung: a.optionen.anfuehrung, kopfzeile: a.optionen.kopfzeile, kodierung: a.optionen.kodierung });
    // Auswahl behalten, solange die Spalten passen; sonst (oder beim ersten Mal) alle Spalten unter ihrem Namen
    if (!o.felder.length || (breite !== null && breite !== a.spalten.length) || o.felder.some((f) => f.spalte >= a.spalten.length))
      o.felder = a.spalten.map((s) => ({ spalte: s.nr, name: s.name }));
    breite = a.spalten.length;
    zeichnen();
    if (beiAenderung) beiAenderung(kopie(), a);
  };
  const kopie = () => JSON.parse(JSON.stringify(o));
  const auswahl = (wert, namen, gewaehlt) => Object.keys(namen).map((k) =>
    `<option value="${esc(k)}" ${k === gewaehlt ? "selected" : ""}>${esc(namen[k])}${a.erkannt && a.erkannt[wert] === k ? " · " + esc(C.erkannt) : ""}</option>`).join("");

  const zeichnen = () => {
    const gewaehlt = new Map(o.felder.map((f) => [f.spalte, f.name]));
    const sicht = o.felder.slice().sort((x, y) => x.spalte - y.spalte);
    ziel.innerHTML = `<div class="zeile"><label>${esc(C.trenner)}</label><select name="cTrenner">${auswahl("trenner", C.trennerName, o.trenner)}</select>
        <label>${esc(C.anfuehrung)}</label><select name="cAnf">${auswahl("anfuehrung", C.anfName, o.anfuehrung)}</select></div>
      <div class="zeile"><label>${esc(C.kodierung)}</label><select name="cKod">${Object.keys(C.kodName).map((k) =>
        `<option value="${k}" ${k === o.kodierung ? "selected" : ""}>${esc(C.kodName[k])}${k === "auto" && o.kodierung === "auto" ? " (" + esc(a.kodierung) + ")" : ""}</option>`).join("")}</select>
        <label><input type="checkbox" name="cKopf" ${o.kopfzeile ? "checked" : ""}> ${esc(C.kopfzeile)}</label></div>
      <p class="leise">${esc(C.zeilen(a.zeilen))} ${a.abgeschnitten ? esc(C.abgeschnitten) : ""}</p>
      <h3>${esc(C.spalten)} <button class="knopf mini" type="button" name="cAlle">${esc(C.alle)}</button>
        <button class="knopf mini" type="button" name="cKeine">${esc(C.keine)}</button></h3>
      <div class="tabelle-rahmen"><table class="tabelle"><tr><th></th><th>${esc(C.spalte)}</th><th>${esc(C.feld)}</th><th>${esc(C.beispiele)}</th></tr>
        ${a.spalten.map((s) => `<tr data-nr="${s.nr}"><td><input type="checkbox" name="cAn" ${gewaehlt.has(s.nr) ? "checked" : ""}></td>
          <td>${esc(s.name)}</td><td><input type="text" name="cName" value="${esc(gewaehlt.get(s.nr) || s.name)}" maxlength="60"></td>
          <td class="leise">${esc(s.beispiele.join(" · "))}</td></tr>`).join("")}</table></div>
      ${sicht.length ? `<h3>${esc(C.vorschau)}</h3><div class="tabelle-rahmen"><table class="tabelle"><tr>${sicht.map((f) => `<th>${esc(f.name)}</th>`).join("")}</tr>
        ${a.vorschau.map((z) => `<tr>${sicht.map((f) => `<td>${esc(z[f.spalte] || "")}</td>`).join("")}</tr>`).join("")}</table></div>` : ""}`;
    const neuLesen = () => analysieren().catch(() => {});
    ziel.querySelector("[name=cTrenner]").onchange = (ev) => { o.trenner = ev.target.value; neuLesen(); };
    ziel.querySelector("[name=cAnf]").onchange = (ev) => { o.anfuehrung = ev.target.value; neuLesen(); };
    ziel.querySelector("[name=cKod]").onchange = (ev) => { o.kodierung = ev.target.value; neuLesen(); };
    ziel.querySelector("[name=cKopf]").onchange = (ev) => { o.kopfzeile = ev.target.checked; o.felder = []; neuLesen(); };
    const uebernehmen = () => {           // Haken und Namen aus der Tabelle lesen
      o.felder = [...ziel.querySelectorAll("tr[data-nr]")].filter((r) => r.querySelector("[name=cAn]").checked)
        .map((r) => ({ spalte: Number(r.dataset.nr), name: r.querySelector("[name=cName]").value.trim() || a.spalten[Number(r.dataset.nr)].name }));
      zeichnen();
      if (beiAenderung) beiAenderung(kopie(), a);
    };
    ziel.querySelectorAll("[name=cAn], [name=cName]").forEach((x) => { x.onchange = uebernehmen; });
    ziel.querySelector("[name=cAlle]").onclick = () => { ziel.querySelectorAll("[name=cAn]").forEach((x) => { x.checked = true; }); uebernehmen(); };
    ziel.querySelector("[name=cKeine]").onclick = () => { ziel.querySelectorAll("[name=cAn]").forEach((x) => { x.checked = false; }); uebernehmen(); };
  };

  await analysieren();
  return { optionen: kopie, felder: () => o.felder.map((f) => f.name), analyse: () => a, neu: analysieren };
}

// Datei aus <input type="file"> als base64 (für senden); Grenze in Bytes
function dateiBase64(datei, grenze) {
  return new Promise((ok, fehler) => {
    if (grenze && datei.size > grenze) { fehler(new Error(`> ${Math.round(grenze / 1e6)} MB`)); return; }
    const r = new FileReader();
    r.onload = () => ok(String(r.result).split(",").pop());
    r.onerror = () => fehler(r.error);
    r.readAsDataURL(datei);
  });
}
