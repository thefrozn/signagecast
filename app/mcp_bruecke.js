#!/usr/bin/env node
// SignageCast – Brücke für Claude Desktop (seit 0.40). Liegt in der Erweiterung (.mcpb), die die Verwaltung erzeugt.
//
// Claude Desktop startet dieses Programm und spricht mit ihm über stdio (MCP, eine JSON-Nachricht je Zeile). Die Brücke
// reicht jede Nachricht per HTTPS an SignageCast im Heimnetz weiter (POST /mcp) und gibt die Antwort zurück.
// Vertraut wird nur dem Zertifikat dieses SignageCast (steht in verbindung.json) – kein Mitlesen im Netz.
// Beim ersten Start tauscht sie den Einmal-Code aus verbindung.json gegen einen Schlüssel und speichert ihn in
// ~/.signagecast/ (nur für den eigenen Benutzer lesbar). Entfernt man den Computer in der Verwaltung, gilt er nicht mehr.
// Nur Node.js-Bordmittel (Node bringt Claude Desktop mit).
"use strict";
const fs = require("fs"), https = require("https"), os = require("os"), path = require("path"), readline = require("readline");

const V = JSON.parse(fs.readFileSync(path.join(__dirname, "verbindung.json"), "utf8"));
const ORDNER = path.join(os.homedir(), ".signagecast");
const SCHLUESSEL_DATEI = path.join(ORDNER, `mcp-${V.id}.json`);
const ziel = new URL(V.url);

function senden(pfad, inhalt, kopf) {
  return new Promise((ok, fehler) => {
    const roh = Buffer.from(JSON.stringify(inhalt));
    const r = https.request({
      host: ziel.hostname, port: ziel.port || 443, path: pfad, method: "POST", ca: V.zertifikat,
      checkServerIdentity: () => undefined,      // Name egal (IP oder .local) – es zählt nur, dass es genau dieses Zertifikat ist
      headers: Object.assign({ "Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                               "Content-Length": roh.length }, kopf || {}),
      timeout: 120000,
    }, (a) => {
      const teile = [];
      a.on("data", (t) => teile.push(t));
      a.on("end", () => ok({ status: a.statusCode, text: Buffer.concat(teile).toString("utf8") }));
    });
    r.on("timeout", () => r.destroy(new Error("Zeitüberschreitung")));
    r.on("error", fehler);
    r.end(roh);
  });
}

function schluesselLesen() {
  try { return JSON.parse(fs.readFileSync(SCHLUESSEL_DATEI, "utf8")).schluessel || ""; } catch (_) { return ""; }
}

let schluessel = schluesselLesen(), koppeln = null;
async function schluesselHolen() {
  if (schluessel) return schluessel;
  if (!koppeln) koppeln = (async () => {
    const a = await senden("/mcp/koppeln", { code: V.code, name: os.hostname() });
    if (a.status !== 200) {
      throw new Error(a.status === 403
        ? `Der Einmal-Code dieser Datei ist abgelaufen oder schon benutzt. In SignageCast (Einstellungen → KI-Assistenten) den Computer „${V.name}“ entfernen und neu verbinden.`
        : `SignageCast antwortet ${a.status} beim Verbinden.`);
    }
    const s = JSON.parse(a.text).schluessel;
    fs.mkdirSync(ORDNER, { recursive: true, mode: 0o700 });
    fs.writeFileSync(SCHLUESSEL_DATEI, JSON.stringify({ url: V.url, name: V.name, schluessel: s }), { mode: 0o600 });
    schluessel = s;
    return s;
  })().finally(() => { koppeln = null; });
  return koppeln;
}

function ausgeben(m) { process.stdout.write(JSON.stringify(m) + "\n"); }
function fehlerAntwort(m, text) {
  if (m && m.id !== undefined && m.id !== null) ausgeben({ jsonrpc: "2.0", id: m.id, error: { code: -32000, message: text } });
}

async function weiterreichen(m) {
  try {
    const s = await schluesselHolen();
    const a = await senden(ziel.pathname || "/mcp", m, { Authorization: "Bearer " + s });
    if (a.status === 202) return;
    if (a.status === 401) {
      return fehlerAntwort(m, `Dieser Computer ist in SignageCast nicht (mehr) verbunden. In SignageCast unter Einstellungen → KI-Assistenten neu verbinden und die neue Datei installieren.`);
    }
    if (a.status !== 200) return fehlerAntwort(m, `SignageCast antwortet ${a.status}.`);
    const d = JSON.parse(a.text);
    for (const x of Array.isArray(d) ? d : [d]) ausgeben(x);
  } catch (e) {
    const text = e && /certificate|self.signed|CERT|SSL|TLS/i.test(String(e.code || e.message))
      ? "Das Zertifikat von SignageCast passt nicht zu dieser Datei (neu aufgesetzt?). Bitte in SignageCast neu verbinden."
      : (e && e.message) || String(e);
    fehlerAntwort(m, `SignageCast (${ziel.host}) nicht erreichbar: ${text}`);
  }
}

const zeilen = readline.createInterface({ input: process.stdin, terminal: false });
zeilen.on("line", (z) => {
  z = z.trim();
  if (!z) return;
  let m;
  try { m = JSON.parse(z); } catch (_) { return ausgeben({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "kein JSON" } }); }
  weiterreichen(m);
});
