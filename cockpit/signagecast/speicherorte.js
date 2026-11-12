// SignageCast – Speicherorte (seit 0.48): Einstellungen → Speicherorte, der gemeinsame Dateidialog „Aus Speicherort“
// und ein Knopf neben jedem Dateifeld der Verwaltung. Nutzt die Hilfsfunktionen aus tv.js (holen, senden, aktion, esc,
// el, $, schalter, melden, E, T, CONTAINER).
//
// Zwei Wege für eine gewählte Datei:
//  - klein (CSV, Playlist, Layout, Bild für den Hintergrund …): der Server liest sie (höchstens 25 MB) und der Browser
//    setzt sie in das Dateifeld ein – die vorhandene Verarbeitung läuft unverändert (soDateiKnoepfe).
//  - groß (Galerie, Medien, Sicherungen): der Server holt sie direkt (/api/speicherorte/holen bzw. /api/sicherung/zip),
//    nichts geht doppelt durchs Netz. Diese Felder tragen data-so="aus" und haben eigene Knöpfe.
"use strict";

const SOTEXTE = {
  de: {
    text: "Ordner auf einem NAS, in einer Cloud (Nextcloud, ownCloud) oder auf dem Server einmal hier eintragen – dann gibt es überall, wo du eine Datei wählst, zusätzlich „Aus Speicherort“. " +
      "Galerie-Ordner und Datenquellen lassen sich außerdem mit einem Ordner bzw. einer Datei verknüpfen und bleiben dann von selbst aktuell.",
    neu: "Neuer Speicherort", keine: "Noch kein Speicherort eingetragen.", name: "Name", art: "Art",
    artName: { webdav: "WebDAV (Nextcloud, ownCloud, NAS)", smb: "SMB (Windows-Freigabe, NAS)", lokal: "Ordner auf dem Server" },
    artKurz: { webdav: "WebDAV", smb: "SMB", lokal: "Server-Ordner" },
    adresse: "Adresse", benutzer: "Benutzer", passwort: "Passwort",
    platzhalter: { webdav: "https://cloud.example.org/remote.php/dav/files/name/Bilder/", smb: "smb://nas/freigabe/ordner", lokal: "/mnt/nas/bilder" },
    hilfe: {
      webdav: "Nextcloud/ownCloud: Adresse unter Dateien → Einstellungen (unten links) → WebDAV. Am besten ein App-Passwort anlegen (Einstellungen → Sicherheit) statt des echten Passworts.",
      smb: "Nur SMB3 (verschlüsselt ausgehandelt). Benutzer mit Domäne als DOMÄNE\\name. Am besten ein eigenes Konto nur mit Leserechten auf diesen Ordner.",
      lokal: (w, c) => c ? `Im Container: ein Volume nach /speicherorte einbinden, z. B. „- /pfad/zum/nas:/speicherorte/nas:ro“ in compose.yaml. Erlaubt sind Ordner unter ${w}.`
        : `Erlaubt sind Ordner unter ${w}. Proxmox: das NAS auf dem Host einbinden und nur lesbar in den Container reichen, z. B. „pct set <ID> -mp0 /mnt/pve/nas,mp=/mnt/nas,ro=1“.`,
    },
    schreiben: "Schreiben erlauben (nur für das Ziel der automatischen Sicherung nötig)",
    schreibenHinweis: "Ohne diesen Haken liest SignageCast nur – es ändert und löscht dort nie etwas.",
    http: "Achtung: http:// ist unverschlüsselt – Passwort und Dateien gehen lesbar durchs Netz. Wenn möglich https:// verwenden.",
    smbFehlt: "SMB ist auf diesem Server noch nicht verfügbar (Paket python3-smbc). Nach dem Update auf diese Version wird es mit installiert.",
    speichern: "Speichern", abbrechen: "Abbrechen", bearbeiten: "Bearbeiten", loeschen: "Löschen", pruefen: "Verbindung prüfen",
    pruefOk: (n, ms, w) => `Verbindung in Ordnung · ${n} Einträge · ${ms} ms${w ? " · Schreiben geht" : ""}`,
    ok: "erreichbar", fehler: "Fehler", nochNicht: "noch nicht benutzt", zuletzt: "zuletzt",
    nurLesen: "nur lesen", lesenSchreiben: "lesen und schreiben",
    wegFrage: (n, wo) => `Speicherort „${n}“ löschen?${wo.length ? "\n\nEr wird noch benutzt von: " + wo.join(", ") + ". Diese Verknüpfungen funktionieren danach nicht mehr." : ""}`,
    benutzt: { galerie: (n) => `Galerie „${n}“`, quelle: (n) => `Datenquelle „${n}“`, sicherung: "automatische Sicherung" },
    wahl: "Aus Speicherort", wahlTitel: "Datei aus Speicherort wählen", wahlTitelMehr: "Dateien aus Speicherort wählen", ordnerTitel: "Ordner wählen",
    hoch: "eine Ebene höher", leer: "Dieser Ordner ist leer.", ausgeblendet: (n) => n === 1 ? "1 weitere Datei passt hier nicht und ist ausgeblendet." : `${n} weitere Dateien passen hier nicht und sind ausgeblendet.`,
    mehr: "Es sind nicht alle Einträge zu sehen (zu viele).", uebernehmen: (n) => n > 1 ? `${n} Dateien übernehmen` : "Übernehmen",
    dieserOrdner: "Diesen Ordner wählen", alle: "Alle wählen", keineWahl: "Keine", laedt: "lädt …", holt: (n, i, name) => `${i} von ${n}: ${name} …`,
    gross: (mb) => `Größer als ${mb} MB – bitte direkt hochladen`,
    // Galerie
    galAus: "Aus Speicherort", galVerkn: "Mit Speicherort-Ordner verknüpfen",
    galVerknText: "Neue und geänderte Bilder kommen von selbst dazu, gelöschte verschwinden auch hier. Von Hand hochgeladene Bilder bleiben.",
    uebernommen: (ok, f) => `${ok} übernommen` + (f ? `, ${f} nicht übernommen` : ""),
    galVerknMit: (o, p) => `🔗 Verknüpft mit ${o}: /${p}`, galIntervall: "Abgleich alle (Minuten)", galUnter: "Unterordner einbeziehen (bis 3 Ebenen)",
    galLoeschen: "Am Speicherort gelöschte Bilder auch hier entfernen", galJetzt: "Jetzt abgleichen", galLoesen: "Verknüpfung lösen",
    galLoesenFrage: "Verknüpfung lösen? Die schon übernommenen Bilder bleiben im Ordner.", galOrdnerAendern: "Anderen Ordner wählen",
    galStand: (z, n, w, a) => `Letzter Abgleich ${z}: ${a} Bilder · ${n} neu · ${w} entfernt`, galLaeuft: (n) => `Abgleich läuft … ${n || 0} neu`,
    galWartet: "Abgleich startet gleich …", galNie: "Noch nicht abgeglichen.", galUnbrauchbar: (n) => `${n} Dateien ließen sich nicht übernehmen`,
    // Medien, Sicherung, Datenquellen
    sichAus: "Sicherung aus Speicherort", sichGewaehlt: (o, p) => `Gewählt: ${o} – ${p}`,
    sichZiel: "Zusätzlich speichern in", sichZielAus: "– nur auf dem Server –", sichZielOrdner: "Ordner wählen",
    sichZielHinweis: "Eine Kopie jeder automatischen Sicherung geht dorthin; dort bleiben ebenfalls die letzten wie oben eingestellt. Nur Speicherorte mit Schreibrecht. Experimentell.",
    sichZielOk: "Kopie im Speicherort angelegt", sichZielFehler: "Kopie in den Speicherort fehlgeschlagen",
    qHerkunft: "Datei aus Speicherort", qWahl: "Datei wählen", qHinweis: "Die Datei wird bei jedem Abruf (Intervall) neu gelesen – Änderungen erscheinen von selbst.",
    experimentell: "experimentell",
  },
  en: {
    text: "Enter folders on a NAS, in a cloud (Nextcloud, ownCloud) or on the server here once – then every place where you choose a file also offers “From storage location”. " +
      "Gallery folders and data sources can also be linked to a folder or file and then stay up to date by themselves.",
    neu: "New storage location", keine: "No storage location yet.", name: "Name", art: "Type",
    artName: { webdav: "WebDAV (Nextcloud, ownCloud, NAS)", smb: "SMB (Windows share, NAS)", lokal: "Folder on the server" },
    artKurz: { webdav: "WebDAV", smb: "SMB", lokal: "Server folder" },
    adresse: "Address", benutzer: "User", passwort: "Password",
    platzhalter: { webdav: "https://cloud.example.org/remote.php/dav/files/name/Pictures/", smb: "smb://nas/share/folder", lokal: "/mnt/nas/pictures" },
    hilfe: {
      webdav: "Nextcloud/ownCloud: address under Files → Settings (bottom left) → WebDAV. Best create an app password (Settings → Security) instead of your real password.",
      smb: "SMB3 only (negotiated encrypted). User with domain as DOMAIN\\name. Best a dedicated account with read-only access to this folder.",
      lokal: (w, c) => c ? `In the container: mount a volume to /speicherorte, e.g. “- /path/to/nas:/speicherorte/nas:ro” in compose.yaml. Allowed are folders below ${w}.`
        : `Allowed are folders below ${w}. Proxmox: mount the NAS on the host and pass it read-only into the container, e.g. “pct set <ID> -mp0 /mnt/pve/nas,mp=/mnt/nas,ro=1”.`,
    },
    schreiben: "Allow writing (only needed as target of the automatic backup)",
    schreibenHinweis: "Without this tick SignageCast only reads – it never changes or deletes anything there.",
    http: "Caution: http:// is unencrypted – password and files travel readable through the network. Use https:// if possible.",
    smbFehlt: "SMB is not available on this server yet (package python3-smbc). It is installed with the update to this version.",
    speichern: "Save", abbrechen: "Cancel", bearbeiten: "Edit", loeschen: "Delete", pruefen: "Test connection",
    pruefOk: (n, ms, w) => `Connection fine · ${n} entries · ${ms} ms${w ? " · writing works" : ""}`,
    ok: "reachable", fehler: "Error", nochNicht: "not used yet", zuletzt: "last",
    nurLesen: "read only", lesenSchreiben: "read and write",
    wegFrage: (n, wo) => `Delete storage location “${n}”?${wo.length ? "\n\nIt is still used by: " + wo.join(", ") + ". These links stop working afterwards." : ""}`,
    benutzt: { galerie: (n) => `gallery “${n}”`, quelle: (n) => `data source “${n}”`, sicherung: "automatic backup" },
    wahl: "From storage location", wahlTitel: "Choose file from storage location", wahlTitelMehr: "Choose files from storage location", ordnerTitel: "Choose folder",
    hoch: "one level up", leer: "This folder is empty.", ausgeblendet: (n) => n === 1 ? "1 more file does not fit here and is hidden." : `${n} more files do not fit here and are hidden.`,
    mehr: "Not all entries are shown (too many).", uebernehmen: (n) => n > 1 ? `Take ${n} files` : "Take",
    dieserOrdner: "Choose this folder", alle: "Select all", keineWahl: "None", laedt: "loading …", holt: (n, i, name) => `${i} of ${n}: ${name} …`,
    gross: (mb) => `Larger than ${mb} MB – please upload directly`,
    galAus: "From storage location", galVerkn: "Link to storage location folder",
    galVerknText: "New and changed pictures are added by themselves, deleted ones disappear here too. Pictures uploaded by hand stay.",
    uebernommen: (ok, f) => `${ok} taken` + (f ? `, ${f} not taken` : ""),
    galVerknMit: (o, p) => `🔗 Linked to ${o}: /${p}`, galIntervall: "Sync every (minutes)", galUnter: "Include subfolders (up to 3 levels)",
    galLoeschen: "Also remove pictures deleted at the storage location", galJetzt: "Sync now", galLoesen: "Unlink",
    galLoesenFrage: "Unlink? Pictures already taken stay in the folder.", galOrdnerAendern: "Choose another folder",
    galStand: (z, n, w, a) => `Last sync ${z}: ${a} pictures · ${n} new · ${w} removed`, galLaeuft: (n) => `Sync running … ${n || 0} new`,
    galWartet: "Sync starts shortly …", galNie: "Not synced yet.", galUnbrauchbar: (n) => `${n} files could not be taken`,
    sichAus: "Backup from storage location", sichGewaehlt: (o, p) => `Chosen: ${o} – ${p}`,
    sichZiel: "Also store in", sichZielAus: "– only on the server –", sichZielOrdner: "Choose folder",
    sichZielHinweis: "A copy of every automatic backup goes there; the last ones as set above are kept there too. Only storage locations with write permission. Experimental.",
    sichZielOk: "Copy stored in the storage location", sichZielFehler: "Copy to the storage location failed",
    qHerkunft: "File from storage location", qWahl: "Choose file", qHinweis: "The file is read again on every fetch (interval) – changes show up by themselves.",
    experimentell: "experimental",
  },
};
const SOT = () => SOTEXTE[E && E.sprache === "en" ? "en" : "de"];
let SO_DATEN = null;                                   // {orte, smb, lokal_wurzeln, container} – Zwischenspeicher
async function soLaden(neu) {
  if (!SO_DATEN || neu) SO_DATEN = await holen("/api/speicherorte");
  return SO_DATEN;
}
const soName = (id) => ((SO_DATEN && SO_DATEN.orte.find((o) => o.id === id)) || {}).name || id;
const soGroesse = (b) => b >= 1024 ** 3 ? (b / 1024 ** 3).toFixed(1) + " GB" : b >= 1024 ** 2 ? (b / 1024 ** 2).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB";
const soZeit = (ts) => ts ? new Date(ts * 1000).toLocaleString(E && E.sprache === "en" ? "en-GB" : "de-DE", { dateStyle: "short", timeStyle: "short" }) : "";

// ---------- Einstellungen → Speicherorte ----------
async function speicherorteSeite(inhalt) {
  const S = SOT();
  let d = await soLaden(true), bearbeitet = null, pruefung = {};
  const benutzt = (id) => [
    ...(E.galerie.ordner || []).filter((o) => o.quelle && o.quelle.ort === id).map((o) => S.benutzt.galerie(o.name)),
    ...(E.quellen || []).filter((q) => q.herkunft === "speicherort" && q.speicherort && q.speicherort.ort === id).map((q) => S.benutzt.quelle(q.name)),
    ...(E.sicherung.ziel && E.sicherung.ziel.ort === id ? [S.benutzt.sicherung] : [])];
  const speichern = async (orte) => { const r = await senden("/api/speicherorte", { orte }); d.orte = r.orte; SO_DATEN = d; };
  const zeichnen = () => {
    inhalt.innerHTML = `<div class="karte"><p class="leise">${esc(S.text)}</p>
        <div class="zeile"><button class="knopf haupt" id="soNeu">+ ${esc(S.neu)}</button></div></div>
      <div id="soEditor"></div>
      ${d.orte.length ? d.orte.map((o) => {
        const z = o.zustand, p = pruefung[o.id];
        return `<div class="karte" data-ort="${esc(o.id)}"><h2>${esc(o.name)} <span class="leise">${esc(S.artKurz[o.art])} · ${esc(o.schreiben ? S.lesenSchreiben : S.nurLesen)}</span></h2>
          <p class="umbruch">${esc(o.adresse)}${o.benutzer ? ` <span class="leise">· ${esc(o.benutzer)}</span>` : ""}</p>
          ${o.unverschluesselt ? `<p class="warn">${esc(S.http)}</p>` : ""}
          <p class="leise">${!z ? esc(S.nochNicht) : z.ok ? `<span class="gut">✓ ${esc(S.ok)}</span> · ${esc(S.zuletzt)} ${esc(soZeit(z.zeit))}`
            : `<span class="schlecht">✗ ${esc(meldungText(z.fehler_m, S.fehler))}</span> · ${esc(soZeit(z.zeit))}`}</p>
          ${p ? `<p class="${p.ok ? "gut" : "schlecht"}">${esc(p.text)}</p>` : ""}
          <div class="zeile"><button class="knopf" data-pruefen>${esc(S.pruefen)}</button><button class="knopf" data-bearbeiten>${esc(S.bearbeiten)}</button>
            <button class="knopf gefahr" data-weg>${esc(S.loeschen)}</button></div></div>`;
      }).join("") : `<div class="karte"><p class="leise">${esc(S.keine)}</p></div>`}`;
    $("#soNeu").onclick = () => { bearbeitet = { id: "", name: "", art: "webdav", adresse: "", benutzer: "", passwort: "", schreiben: false }; editor(); };
    inhalt.querySelectorAll("[data-ort]").forEach((k) => {
      const o = d.orte.find((x) => x.id === k.dataset.ort);
      k.querySelector("[data-bearbeiten]").onclick = () => { bearbeitet = Object.assign({}, o); editor(); };
      k.querySelector("[data-pruefen]").onclick = (ev) => aktion(ev.target, async () => {
        try {
          const r = await senden("/api/speicherorte/pruefen", { id: o.id });
          pruefung[o.id] = { ok: true, text: S.pruefOk(r.pruefung.eintraege, r.pruefung.ms, r.pruefung.schreiben) }; d.orte = r.orte;
        } catch (e) { pruefung[o.id] = { ok: false, text: e.message }; d = await soLaden(true); }
        zeichnen();
      }, null);
      k.querySelector("[data-weg]").onclick = (ev) => {
        if (!confirm(S.wegFrage(o.name, benutzt(o.id)))) return;
        aktion(ev.target, async () => { await speichern(d.orte.filter((x) => x.id !== o.id)); zeichnen(); });
      };
    });
    editor();
  };
  const editor = () => {
    const z = $("#soEditor"), o = bearbeitet;
    if (!o) { z.innerHTML = ""; return; }
    z.innerHTML = `<div class="karte"><h2>${esc(o.id ? o.name : S.neu)}</h2>
      <div class="zeile"><label for="soName">${esc(S.name)}</label><input type="text" id="soName" maxlength="40" value="${esc(o.name)}"></div>
      <div class="zeile"><label for="soArt">${esc(S.art)}</label><select id="soArt">${["webdav", "smb", "lokal"].map((a) =>
        `<option value="${a}" ${a === o.art ? "selected" : ""}>${esc(S.artName[a])}</option>`).join("")}</select></div>
      <p class="warn" id="soSmbFehlt" hidden>${esc(S.smbFehlt)}</p>
      <div class="zeile"><label for="soAdresse">${esc(S.adresse)}</label><input type="text" id="soAdresse" class="voll640" spellcheck="false" value="${esc(o.adresse)}"></div>
      <p class="leise" id="soHilfe"></p><p class="warn" id="soHttp" hidden>${esc(S.http)}</p>
      <div data-zugang><div class="zeile"><label for="soBenutzer">${esc(S.benutzer)}</label><input type="text" id="soBenutzer" autocomplete="off" spellcheck="false" value="${esc(o.benutzer)}"></div>
        <div class="zeile"><label for="soPw">${esc(S.passwort)}</label><input type="password" id="soPw" autocomplete="new-password" value="${esc(o.passwort)}"></div></div>
      <div class="zeile"><label><input type="checkbox" id="soSchreiben" ${o.schreiben ? "checked" : ""}> ${esc(S.schreiben)}</label></div>
      <p class="leise">${esc(S.schreibenHinweis)}</p>
      <div class="zeile"><button class="knopf haupt" id="soOk">${esc(S.speichern)}</button><button class="knopf" id="soAbbr">${esc(S.abbrechen)}</button></div></div>`;
    const art = () => {
      const a = $("#soArt").value, h = S.hilfe[a];
      $("#soAdresse").placeholder = S.platzhalter[a];
      $("#soHilfe").textContent = typeof h === "function" ? h(d.lokal_wurzeln.join(", "), d.container) : h;
      z.querySelector("[data-zugang]").hidden = a === "lokal";
      $("#soSmbFehlt").hidden = a !== "smb" || d.smb;
      $("#soHttp").hidden = a !== "webdav" || !/^http:\/\//i.test($("#soAdresse").value.trim());
    };
    $("#soArt").onchange = art; $("#soAdresse").oninput = art; art();
    $("#soAbbr").onclick = () => { bearbeitet = null; editor(); };
    $("#soOk").onclick = (ev) => aktion(ev.target, async () => {
      const neu = { id: o.id, name: $("#soName").value.trim(), art: $("#soArt").value, adresse: $("#soAdresse").value.trim(),
                    benutzer: $("#soBenutzer").value.trim(), passwort: $("#soPw").value, schreiben: $("#soSchreiben").checked };
      const liste = o.id ? d.orte.map((x) => x.id === o.id ? neu : x) : [...d.orte, neu];
      await speichern(liste.map((x) => ({ id: x.id, name: x.name, art: x.art, adresse: x.adresse, benutzer: x.benutzer, passwort: x.passwort, schreiben: x.schreiben })));
      bearbeitet = null; zeichnen();
    });
    z.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };
  zeichnen();
}

// ---------- Dateidialog „Aus Speicherort“ ----------
// soWaehlen({ titel, filter: RegExp für Dateinamen, mehrere, ordner: true = einen Ordner wählen, nurSchreiben })
//  -> null (abgebrochen) | Ordner: { ort, pfad } | Dateien: [{ ort, pfad, name, groesse }]
async function soWaehlen(opt = {}) {
  const S = SOT(), d = await soLaden(true);
  const orte = d.orte.filter((o) => !opt.nurSchreiben || o.schreiben);
  if (!orte.length) { melden(S.keine, true); return null; }
  return new Promise((fertig) => {
    let ort = orte.some((o) => o.id === soWaehlen.ort) ? soWaehlen.ort : orte[0].id, pfad = soWaehlen.pfade[ort] || "", liste = null, fehler = "", wahl = new Map();
    const dlg = el(`<dialog class="sowahl"><h2>${esc(opt.titel || (opt.ordner ? S.ordnerTitel : opt.mehrere ? S.wahlTitelMehr : S.wahlTitel))}</h2>
      <div class="zeile"><select id="soOrt" aria-label="${esc(T.reiter.speicherorte)}">${orte.map((o) => `<option value="${esc(o.id)}">${esc(o.name)}</option>`).join("")}</select></div>
      <div class="sopfad" id="soPfad"></div><div class="soliste" id="soListe"></div><p class="leise" id="soInfo"></p>
      <div class="zeile"><button class="knopf" id="soZu">${esc(S.abbrechen)}</button>
        ${opt.ordner ? `<button class="knopf haupt" id="soOrdnerOk">${esc(S.dieserOrdner)}</button>` : `${opt.mehrere ? `<button class="knopf" id="soAlle">${esc(S.alle)}</button>` : ""}
        <button class="knopf haupt" id="soOk" disabled>${esc(S.uebernehmen(1))}</button>`}</div></dialog>`);
    document.body.appendChild(dlg);
    const ende = (wert) => { soWaehlen.ort = ort; soWaehlen.pfade[ort] = pfad; dlg.close(); dlg.remove(); fertig(wert); };
    dlg.addEventListener("cancel", (ev) => { ev.preventDefault(); ende(null); });
    $("#soOrt", dlg).value = ort;
    $("#soOrt", dlg).onchange = () => { ort = $("#soOrt", dlg).value; pfad = soWaehlen.pfade[ort] || ""; wahl.clear(); laden(); };
    $("#soZu", dlg).onclick = () => ende(null);
    if (opt.ordner) $("#soOrdnerOk", dlg).onclick = () => ende({ ort, pfad });
    const knopf = () => {
      if (opt.ordner) return;
      $("#soOk", dlg).disabled = !wahl.size; $("#soOk", dlg).textContent = S.uebernehmen(wahl.size);
      if ($("#soAlle", dlg)) $("#soAlle", dlg).textContent = liste && wahl.size && wahl.size === dateien().length ? S.keineWahl : S.alle;
    };
    const dateien = () => (liste ? liste.eintraege : []).filter((x) => !x.ordner && (!opt.filter || opt.filter.test(x.name)));
    if (!opt.ordner) $("#soOk", dlg).onclick = () => ende([...wahl.values()]);
    if ($("#soAlle", dlg)) $("#soAlle", dlg).onclick = () => {
      const alle = dateien(), an = wahl.size !== alle.length;
      wahl.clear(); if (an) alle.forEach((x) => wahl.set(x.pfad, x));
      zeichnen();
    };
    const zeichnen = () => {
      const teile = pfad ? pfad.split("/") : [];
      $("#soPfad", dlg).innerHTML = [`<button class="link" data-zu="">${esc(soName(ort))}</button>`, ...teile.map((t, i) =>
        `<button class="link" data-zu="${esc(teile.slice(0, i + 1).join("/"))}">${esc(t)}</button>`)].join(" / ");
      $("#soPfad", dlg).querySelectorAll("[data-zu]").forEach((b) => { b.onclick = () => { pfad = b.dataset.zu; laden(); }; });
      const z = $("#soListe", dlg);
      if (fehler) { z.innerHTML = `<p class="schlecht">${esc(fehler)}</p>`; $("#soInfo", dlg).textContent = ""; knopf(); return; }
      if (!liste) { z.innerHTML = `<p class="leise">${esc(S.laedt)}</p>`; return; }
      const ordner = liste.eintraege.filter((x) => x.ordner), passend = opt.ordner ? [] : dateien();
      const versteckt = liste.eintraege.length - ordner.length - passend.length;
      z.innerHTML = (pfad ? `<button class="soeintrag" data-hoch>⬑ ${esc(S.hoch)}</button>` : "") +
        ordner.map((x) => `<button class="soeintrag" data-ordner="${esc(x.name)}">📁 ${esc(x.name)}</button>`).join("") +
        passend.map((x) => `<label class="soeintrag"><input type="${opt.mehrere ? "checkbox" : "radio"}" name="soDatei" data-datei="${esc(x.name)}" ${wahl.has(x.pfad) ? "checked" : ""}>
          <span class="flex1">📄 ${esc(x.name)}</span><span class="leise">${esc(soGroesse(x.groesse))}${x.zeit ? " · " + esc(soZeit(x.zeit)) : ""}</span></label>`).join("") +
        (!ordner.length && !passend.length ? `<p class="leise">${esc(S.leer)}</p>` : "");
      $("#soInfo", dlg).textContent = [versteckt > 0 && !opt.ordner ? S.ausgeblendet(versteckt) : "", liste.mehr ? S.mehr : ""].filter(Boolean).join(" ");
      const hoch = z.querySelector("[data-hoch]");
      if (hoch) hoch.onclick = () => { pfad = pfad.split("/").slice(0, -1).join("/"); laden(); };
      z.querySelectorAll("[data-ordner]").forEach((b) => { b.onclick = () => { pfad = (pfad ? pfad + "/" : "") + b.dataset.ordner; laden(); }; });
      z.querySelectorAll("[data-datei]").forEach((c) => {
        const x = passend.find((y) => y.name === c.dataset.datei);
        c.onchange = () => {
          if (!opt.mehrere) wahl.clear();
          if (c.checked) wahl.set(x.pfad, x); else wahl.delete(x.pfad);
          knopf();
        };
        c.ondblclick = () => { if (!opt.mehrere) ende([x]); };
      });
      knopf();
    };
    const laden = async () => {
      liste = null; fehler = ""; zeichnen();
      try {
        const r = await holen(`/api/speicherorte/ordner?ort=${encodeURIComponent(ort)}&pfad=${encodeURIComponent(pfad)}`);
        if (!r.ok) throw new Error(meldungText(r, r.fehler));
        r.eintraege.forEach((x) => { x.pfad = (pfad ? pfad + "/" : "") + x.name; x.ort = ort; });
        liste = r;
      } catch (e) {
        fehler = e.message || String(e);
        if (pfad && /fehlt|exist/i.test(fehler)) { pfad = ""; return laden(); }        // gemerkter Ordner gibt es nicht mehr
      }
      zeichnen();
    };
    dlg.showModal();
    laden();
  });
}
soWaehlen.ort = null;
soWaehlen.pfade = {};

// accept="…" eines Dateifelds als Filter für Dateinamen
const SO_TYPEN = { "image/jpeg": ["jpg", "jpeg"], "image/png": ["png"], "image/webp": ["webp"], "image/gif": ["gif"], "application/pdf": ["pdf"],
                   "video/mp4": ["mp4", "m4v"], "video/webm": ["webm"], "application/zip": ["zip"], "application/json": ["json"],
                   "text/calendar": ["ics"], "text/csv": ["csv"], "text/plain": ["txt"], "audio/x-mpegurl": ["m3u", "m3u8"], "audio/x-scpls": ["pls"] };
const SO_MIME = { jpg: "image/jpeg", jpeg: "image/jpeg", png: "image/png", webp: "image/webp", gif: "image/gif", pdf: "application/pdf",
                  mp4: "video/mp4", webm: "video/webm", zip: "application/zip", json: "application/json", ics: "text/calendar", csv: "text/csv",
                  tsv: "text/tab-separated-values", txt: "text/plain", xml: "application/xml", m3u: "audio/x-mpegurl", m3u8: "audio/x-mpegurl", pls: "audio/x-scpls" };
function soFilter(accept) {
  const endungen = new Set();
  for (const a of String(accept || "").split(",").map((x) => x.trim().toLowerCase()).filter(Boolean)) {
    if (a.startsWith(".")) endungen.add(a.slice(1));
    else if (SO_TYPEN[a]) SO_TYPEN[a].forEach((e) => endungen.add(e));
    else if (a.endsWith("/*")) Object.entries(SO_TYPEN).filter(([k]) => k.startsWith(a.slice(0, -1))).forEach(([, es]) => es.forEach((e) => endungen.add(e)));
  }
  return endungen.size ? new RegExp(`\\.(${[...endungen].join("|")})$`, "i") : null;
}

// Neben jedes Dateifeld (ohne data-so="aus") ein Knopf „Aus Speicherort“ – nur, wenn es Speicherorte gibt. Die gewählte
// Datei liest der Server, der Browser setzt sie ins Feld ein und löst „change“ aus: die Seite verarbeitet sie wie gewohnt.
async function soDateiKnoepfe(wurzel) {
  const felder = [...wurzel.querySelectorAll('input[type="file"]:not([data-so]):not([webkitdirectory])')];
  if (!felder.length) return;
  felder.forEach((f) => { f.dataset.so = "ja"; });
  let d;
  try { d = await soLaden(); } catch (_) { return; }
  if (!d.orte.length) return;
  const S = SOT();
  for (const f of felder) {
    const k = el(`<button type="button" class="knopf soknopf">📁 ${esc(S.wahl)}</button>`);
    const anker = f.hidden && f.closest("label") ? f.closest("label") : f;
    anker.insertAdjacentElement("afterend", k);
    k.onclick = () => aktion(k, async () => {
      const wahl = await soWaehlen({ filter: soFilter(f.accept), mehrere: f.multiple });
      if (!wahl || !wahl.length) return;
      const dt = new DataTransfer();
      for (const x of wahl) {
        const r = await senden("/api/speicherorte/lesen", { ort: x.ort, pfad: x.pfad });
        const roh = Uint8Array.from(atob(r.daten), (c) => c.charCodeAt(0));
        const endung = (r.name.split(".").pop() || "").toLowerCase();
        dt.items.add(new File([roh], r.name, { type: SO_MIME[endung] || "application/octet-stream", lastModified: (x.zeit || 0) * 1000 || Date.now() }));
      }
      f.files = dt.files;
      f.dispatchEvent(new Event("change", { bubbles: true }));
      f.dispatchEvent(new Event("input", { bubbles: true }));
    }, null);
  }
}
// Alles, was neu in die Seite kommt, bekommt die Knöpfe (Seiten zeichnen sich oft neu)
document.addEventListener("DOMContentLoaded", () => {
  const ziel = document.getElementById("inhalt");
  if (!ziel) return;
  let geplant = false;
  new MutationObserver(() => {
    if (geplant) return;
    geplant = true;
    requestAnimationFrame(() => { geplant = false; soDateiKnoepfe(ziel); });
  }).observe(ziel, { childList: true, subtree: true });
});

// Große Dateien direkt auf den Server holen (Galerie, Medien): nacheinander, mit Stand und gesammelten Fehlern
const SO_ABBRUCH = (c) => ["sp_voll", "gal_voll", "gal_viele", "gal_ordner"].includes(c) || /^so_/.test(c || "") && !["so_gross", "so_fehlt", "so_typ"].includes(c);
async function soHolenViele(liste, daten, stand) {
  const S = SOT();
  let ok = 0, letzte = null, abbruch = "";
  const fehler = [];
  for (let i = 0; i < liste.length && !abbruch; i++) {
    const x = liste[i];
    if (stand) stand(S.holt(liste.length, i + 1, x.name));
    const d = JSON.parse(await dienst.post("/api/speicherorte/holen", JSON.stringify(Object.assign({ ort: x.ort, pfad: x.pfad }, daten)), KOPF));
    if (d.ok) { ok++; letzte = d; continue; }
    if (SO_ABBRUCH(d.code)) abbruch = meldungText(d, d.fehler);          // betrifft die übrigen auch
    else fehler.push(`${x.name}: ${meldungText(d, d.fehler)}`);
  }
  return { ok, fehler, abbruch, letzte, rest: liste.length - ok - fehler.length };
}
