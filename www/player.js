// SignageCast – Live-Video der TV-Seite.
// - Rotation: Stream Nr. ⌊Sekunde des Tages / Takt⌋ mod Anzahl; ein Stream bleibt für seinen ganzen Takt fest.
// - "Jetzt zeigen" aus der Verwaltung (vorrang) hat für einen Takt Vorrang.
// - Offizieller YouTube-Einbettungsplayer, intern 1920x1080 (YouTube wählt die Stufe nach der Playergröße), verkleinert.
// - Qualität: Statusmeldungen des Players (enablejsapi). Startet nicht, puffert, Bild steht, Fehler oder läuft
//   länger als erlaubt unter der Mindeststufe (obwohl mehr angeboten wird) -> Strike, lokal überspringen, sofort weiter.
//   Geschützte Streams werden nie wegen Auflösung übersprungen. Regeln kommen aus den Einstellungen (daten.regeln).
// - Mehrere Fernseher: versatz (Nummer des Fernsehers) verschiebt die Reihenfolge, damit nicht alle dasselbe zeigen.
// - Ton: nur bei ton = "tiere" mit Originalton (Lautstärke aus den Einstellungen), sonst stumm.
// - Einspieler (z. B. tagesschau in 100 Sekunden): zur eingestellten Minute unterbricht der Beitrag die Rotation und läuft
//   ganz durch (MP4 als <video> oder YouTube-Video), danach geht es normal weiter. Mit Ton pausiert solange das Radio
//   (Ereignisse "einspieler-start"/"einspieler-ende" an die Seite). Keine Strikes während eines Einspielers.
// - Eigene Medien (seit 0.15): Bilder (für ihre Anzeigedauer) und Videos (ganz) laufen als Einschub wie Einspieler –
//   Quelle je Fernseher „medien“ (nur eigene Medien im Kreis) oder „gemischt“ (bei jedem N-ten Stream-Wechsel ein Medium).
// Zeit: Abweichung zur Zeitquelle (NTP, vom Datendienst gemessen) und optionale Zeitzone – für Uhr, Takt, Einspieler
const ZEIT = { abweichung: 0, zone: null };
function jetztMs() { return Date.now() + ZEIT.abweichung; }
function ortszeit() {
  const d = new Date(jetztMs());
  if (!ZEIT.zone) return { h: d.getHours(), m: d.getMinutes(), s: d.getSeconds(), tag: d.toDateString(), d };
  const t = Object.fromEntries(new Intl.DateTimeFormat("en-GB", { timeZone: ZEIT.zone, hour12: false, year: "numeric", month: "2-digit",
    day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }).formatToParts(d).map((x) => [x.type, x.value]));
  return { h: Number(t.hour) % 24, m: Number(t.minute), s: Number(t.second), tag: `${t.year}-${t.month}-${t.day}`, d };
}

const STUFEN = ["tiny", "small", "medium", "large", "hd720", "hd1080", "hd1440", "hd2160", "highres"];
const PRUEFUNG = { startetNichtS: 30, puffertS: 15, stehtS: 20, startMeldenS: 30, endeVorWechselS: 20 };

class LivePlayer {
  constructor(box, texte) {
    this.box = box;
    this.texte = texte;
    box.innerHTML = '<div class="leer"></div><div class="leiste live"></div><div class="leiste naechstes"></div>';
    this.live = box.querySelector(".live");
    this.naechstes = box.querySelector(".naechstes");
    this.leer = box.querySelector(".leer");
    this.streams = [];
    this.vorrang = null;
    this.versatz = 0; this.ton = "aus"; this.lautstaerke = 70;
    this.einspielerListe = []; this.einspieler = null; this.gespielt = {}; this.video = null;
    this.medien = []; this.medienModus = "youtube"; this.medienAlle = 3; this.medienPos = 0; this.slotZaehler = 0; this.zaehlSlot = null;
    this.regeln = { takt_s: 180, mindeststufe: "hd720", schlecht_s: 20, sperre_s: 7200 };
    this.gesperrt = {};
    this.fest = null; this.festSlot = null; this.id = null; this.frame = null; this.z = null;
    this.aus = false;                       // Baustein versteckt (Bedingung) -> kein Video laden, spart Rechenzeit
    this.empfang = (e) => this.nachricht(e);
    window.addEventListener("message", this.empfang);
    this.uhr = setInterval(() => this.tick(), 1000);
  }

  setze(d) {
    this.streams = Array.isArray(d.streams) ? d.streams : [];
    this.vorrang = d.vorrang && d.vorrang.bis * 1000 > Date.now() ? d.vorrang : null;
    if (d.regeln) this.regeln = d.regeln;
    this.versatz = d.versatz || 0;
    this.einspielerListe = Array.isArray(d.einspieler) ? d.einspieler : [];
    this.medien = Array.isArray(d.medien) ? d.medien : [];
    this.medienModus = d.medien_modus || "youtube"; this.medienAlle = d.medien_alle || 3;
    ZEIT.abweichung = d.zeit_abweichung_ms || 0;
    ZEIT.zone = d.zeitzone || null;
    const j = d.einspieler_jetzt;               // „Jetzt zeigen“ aus der Verwaltung
    if (j && !this.gespielt["jetzt " + j.nr] && !this.einspieler) {
      const e = this.einspielerListe.find((x) => x.id === j.id);
      this.gespielt["jetzt " + j.nr] = 1;
      if (e) { this.einspieler = { ...e, start: Date.now() }; window.dispatchEvent(new CustomEvent("einspieler-start", { detail: { ton: e.ton } })); }
    }
    const ton = d.ton || "aus", laut = d.lautstaerke ?? 70;
    if (ton !== this.ton || laut !== this.lautstaerke) { this.ton = ton; this.lautstaerke = laut; this.tonSetzen(); }
  }

  befehl(func, args) {
    if (this.frame && this.frame.contentWindow)
      this.frame.contentWindow.postMessage(JSON.stringify({ event: "command", func, args: args || [] }), "*");
  }

  tonSetzen() {
    if (this.einspieler) return;
    if (this.ton === "tiere") { this.befehl("unMute"); this.befehl("setVolume", [this.lautstaerke]); }
    else this.befehl("mute");
  }

  gut(stufe) { return STUFEN.indexOf(stufe) >= STUFEN.indexOf(this.regeln.mindeststufe); }

  // Fälliger Einspieler: Minute passt, in den ersten 50 s der Minute, im Zeitfenster, für diese Minute noch nicht gespielt
  faelligPruefen() {                      // ohne „gespielt“ zu markieren
    const merk = this.gespielt; this.gespielt = Object.assign({}, merk);
    const e = this.faellig(); this.gespielt = merk; return !!e;
  }

  faellig() {
    const o = ortszeit(), hhmm = String(o.h).padStart(2, "0") + ":" + String(o.m).padStart(2, "0");
    if (o.s >= 50) return null;
    for (const e of this.einspielerListe) {
      const drin = e.von <= e.bis ? hhmm >= e.von && hhmm <= e.bis : hhmm >= e.von || hhmm <= e.bis;
      const schluessel = `${e.id} ${o.tag} ${hhmm}`;
      if (e.minuten.includes(o.m) && drin && !this.gespielt[schluessel]) { this.gespielt[schluessel] = 1; return e; }
    }
    return null;
  }

  einspielerEnde() {
    if (!this.einspieler) return;
    const ton = this.einspieler.ton;
    this.einspieler = null;
    clearInterval(this.einspielerWache);
    if (this.video) { this.video.remove(); this.video = null; }
    this.id = null;                         // Rotation lädt im nächsten tick neu
    window.dispatchEvent(new CustomEvent("einspieler-ende", { detail: { ton } }));
  }

  plan() {
    const jetzt = Date.now();
    const o = ortszeit();
    const sekTag = o.h * 3600 + o.m * 60 + o.s;
    const takt = this.regeln.takt_s || 180;
    const slot = Math.floor(sekTag / takt) + this.versatz * 7, rest = takt - (sekTag % takt);
    const frei = this.streams.filter((s) => !(this.gesperrt[s.video_id] > jetzt));
    if (this.vorrang && !(this.gesperrt[this.vorrang.video_id] > jetzt)) {
      const rv = Math.max(0, Math.round((this.vorrang.bis * 1000 - jetzt) / 1000));
      const n = frei.length ? frei[(slot + 1) % frei.length] : null;
      return { aktuell: { video_id: this.vorrang.video_id, name: this.vorrang.name }, naechster: n, rest: rv };
    }
    if (!frei.length) { this.fest = null; return { aktuell: null, naechster: null, rest }; }
    const gesperrtJetzt = this.fest && this.gesperrt[this.fest.video_id] > jetzt;
    const verfuegbar = (x) => x && frei.find((f) => f.video_id === x.video_id);
    if (!this.fest || this.festSlot !== slot || gesperrtJetzt) {
      // Angekündigten Stream nehmen, wenn er noch verfügbar ist – sonst wie bisher nach der Position im Takt
      // (die Liste kann sich bis zum Wechsel ändern: Strike, Sperre, Nacht am Ort, neue Streams)
      const angekuendigt = this.naechsterSlot === slot - 1 && !gesperrtJetzt ? verfuegbar(this.naechsterFest) : null;
      let i = slot % frei.length;
      if (this.fest && frei.length > 1 && frei[i].video_id === this.fest.video_id) i = (i + 1) % frei.length;
      this.fest = angekuendigt || frei[i]; this.festSlot = slot;
    }
    // Nächsten einmal je Takt festlegen und so ankündigen; fällt er weg, neu wählen (Anzeige stimmt dann sofort)
    if (this.naechsterSlot !== slot || !verfuegbar(this.naechsterFest) || (this.naechsterFest && this.naechsterFest.video_id === this.fest.video_id)) {
      const pos = frei.findIndex((s) => s.video_id === this.fest.video_id);
      const n = frei.length > 1 ? frei[((pos >= 0 ? pos : slot) + 1) % frei.length] : null;
      this.naechsterFest = n && n.video_id !== this.fest.video_id ? n : null;
      this.naechsterSlot = slot;
    }
    return { aktuell: this.fest, naechster: this.naechsterFest, rest };
  }

  stoppen() {                               // Layout wird neu gebaut
    clearInterval(this.uhr);
    if (this.einspieler) this.einspielerEnde();
    window.removeEventListener("message", this.empfang);
    if (this.frame) { this.frame.remove(); this.frame = null; }
  }

  medienStart() {                           // nächstes eigenes Medium als Einschub
    const m = this.medien[this.medienPos++ % this.medien.length];
    const ton = m.art === "video" && this.ton === "tiere";
    this.einspieler = { id: "medium-" + m.id, name: m.name, art: m.art === "bild" ? "bild" : "video", url: m.url, ton,
                        dauer_s: m.dauer_s, medium: true, start: Date.now() };
    window.dispatchEvent(new CustomEvent("einspieler-start", { detail: { ton } }));
  }

  tick() {
    const T = this.texte();
    if (!this.einspieler && !this.aus && this.medienModus === "medien" && this.medien.length && !this.faelligPruefen()) this.medienStart();
    if (!this.einspieler && !this.aus) {
      const e = this.faellig();
      if (e) {
        this.einspieler = { ...e, start: Date.now() };
        window.dispatchEvent(new CustomEvent("einspieler-start", { detail: { ton: e.ton } }));
      }
    }
    if (this.einspieler) {
      const e = this.einspieler, laeuft = Date.now() - e.start;
      if (e.art === "bild" && laeuft > e.dauer_s * 1000) { this.einspielerEnde(); return; }   // Bild: Anzeigedauer vorbei
      if (laeuft > (e.medium ? (e.dauer_s + 60) * 1000 : 10 * 60 * 1000)) this.einspielerEnde();   // Sicherheitsgrenze
      else {
        const kennung = "einspieler:" + this.einspieler.id;
        if (this.id !== kennung) this.ladeEinspieler(kennung);
        this.live.style.display = this.einspieler.medium ? "none" : "block";       // eigene Medien ohne Leiste
        this.live.textContent = `● ${this.einspieler.name}`;
        this.naechstes.style.display = "none";
        this.skaliere();
        if (this.einspieler.art === "youtube" && this.z && this.z.status === 0) this.einspielerEnde();   // Video zu Ende
        return;
      }
    }
    const p = this.plan();
    // gemischt: bei jedem N-ten Wechsel des Streams zuerst ein eigenes Medium
    if (this.medienModus === "gemischt" && this.medien.length && p.aktuell && !this.aus && this.festSlot !== this.zaehlSlot) {
      this.zaehlSlot = this.festSlot;
      if (++this.slotZaehler % this.medienAlle === 0) { this.medienStart(); return; }
    }
    this.aktuell = p.aktuell;
    const id = p.aktuell && !this.aus ? p.aktuell.video_id : "";
    if (id !== this.id) this.lade(id);
    this.leer.textContent = T.keinStream;
    this.live.style.display = p.aktuell ? "block" : "none";
    if (p.aktuell) this.live.textContent = `● LIVE  ·  ${p.aktuell.name}`;
    this.naechstes.style.display = p.naechster ? "block" : "none";
    if (p.naechster) {
      const mm = Math.floor(p.rest / 60), ss = String(p.rest % 60).padStart(2, "0");
      this.naechstes.textContent = `⏱ ${mm}:${ss}  ·  ${T.naechstes}: ${p.naechster.name}`;
    }
    this.skaliere();
    this.pruefe(p.rest);
  }

  ladeEinspieler(kennung) {
    if (this.frame) { this.frame.remove(); this.frame = null; }
    if (this.video) { this.video.remove(); this.video = null; }
    this.id = kennung;
    this.leer.style.display = "none";
    const e = this.einspieler;
    if (e.art === "bild") {
      const b = document.createElement("img");
      b.className = "einspieler"; b.src = e.url; b.alt = "";
      b.addEventListener("error", () => this.einspielerEnde());
      this.box.insertBefore(b, this.box.firstChild);
      this.video = b;
    } else if (e.art === "video") {
      // Puffer: „vorab“ kommt schon als lokale Datei aus dem Container; bei „vorlauf“ erst starten, wenn so viele Sekunden
      // im Browser gepuffert sind (höchstens 30 s warten). Steht das Bild danach 20 s still, Einspieler abbrechen.
      const vorlauf = e.vorlauf_s || 0;
      const v = document.createElement("video");
      Object.assign(v, { src: e.url, autoplay: !vorlauf, preload: "auto", muted: !e.ton, playsInline: true });
      v.volume = Math.max(0, Math.min(1, this.lautstaerke / 100));
      v.className = "einspieler";
      v.addEventListener("ended", () => this.einspielerEnde());
      v.addEventListener("error", () => this.einspielerEnde());
      this.box.insertBefore(v, this.box.firstChild);
      this.video = v;
      const beginn = Date.now();
      let gestartet = !vorlauf, letzteZeit = -1, steht = 0;
      if (!vorlauf) v.play().catch(() => {});
      clearInterval(this.einspielerWache);
      this.einspielerWache = setInterval(() => {
        if (this.video !== v) { clearInterval(this.einspielerWache); return; }
        if (!gestartet) {
          const vorne = v.buffered.length ? v.buffered.end(v.buffered.length - 1) - v.currentTime : 0;
          if (vorne >= vorlauf || v.readyState >= 4 || Date.now() - beginn > 30000) { gestartet = true; v.play().catch(() => {}); }
          return;
        }
        if (v.currentTime !== letzteZeit) { letzteZeit = v.currentTime; steht = 0; return; }
        if (++steht >= 20) this.einspielerEnde();          // 20 s ohne Fortschritt: zurück zum Live-Video
      }, 1000);
    } else {
      this.z = { start: Date.now(), status: null, angemeldet: false };
      const f = document.createElement("iframe");
      f.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(e.video_id)}?autoplay=1&mute=${e.ton ? 0 : 1}&controls=0&rel=0&playsinline=1` +
              `&modestbranding=1&enablejsapi=1&origin=${encodeURIComponent(location.origin)}`;
      f.allow = "autoplay; encrypted-media; picture-in-picture";
      f.referrerPolicy = "strict-origin-when-cross-origin";
      f.addEventListener("load", () => { if (f.contentWindow) f.contentWindow.postMessage(JSON.stringify({ event: "listening", id: kennung, channel: "widget" }), "*"); });
      this.box.insertBefore(f, this.box.firstChild);
      this.frame = f;
    }
  }

  lade(id) {
    if (this.frame) { this.frame.remove(); this.frame = null; }
    if (this.video) { this.video.remove(); this.video = null; }
    this.id = id;
    this.z = { start: Date.now(), laeuft: false, puffer: 0, letzteZeit: null, letzteBewegung: Date.now(),
               qualitaet: null, angemeldet: false, status: null, stufe: null, startGemeldet: false, endeGemeldet: false,
               schlechtSeit: null };
    this.leer.style.display = id ? "none" : "flex";
    if (!id) return;
    const f = document.createElement("iframe");
    f.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&mute=${this.ton === "tiere" ? 0 : 1}&controls=0&rel=0&playsinline=1` +
            `&modestbranding=1&enablejsapi=1&origin=${encodeURIComponent(location.origin)}`;
    f.allow = "autoplay; encrypted-media; picture-in-picture";
    f.referrerPolicy = "strict-origin-when-cross-origin";
    f.addEventListener("load", () => this.anmelden());
    this.box.insertBefore(f, this.box.firstChild);
    this.frame = f;
    this.skaliere();
  }

  skaliere() {
    if (!this.frame) return;
    const b = this.box.clientWidth, h = this.box.clientHeight;
    if (b && h) this.frame.style.transform = `scale(${b / 1920}, ${h / 1080})`;
  }

  anmelden() {
    if (this.frame && this.frame.contentWindow)
      this.frame.contentWindow.postMessage(JSON.stringify({ event: "listening", id: this.id, channel: "widget" }), "*");
    this.tonSetzen();
  }

  nachricht(e) {
    let host; try { host = new URL(e.origin).hostname; } catch (_) { return; }
    if (!/(^|\.)youtube(-nocookie)?\.com$/.test(host) || !this.frame || e.source !== this.frame.contentWindow) return;
    let d; try { d = typeof e.data === "string" ? JSON.parse(e.data) : e.data; } catch (_) { return; }
    const z = this.z; if (!z || !d) return;
    z.angemeldet = true;
    if (d.event === "onError") return this.einspieler ? this.einspielerEnde() : this.strike("fehler");
    const info = d.info && typeof d.info === "object" ? d.info : {};
    if (d.event === "onStateChange" && typeof d.info === "number") info.playerState = d.info;
    if (info.playerState !== undefined) z.status = info.playerState;
    if (info.currentTime !== undefined) {
      if (z.letzteZeit === null || info.currentTime > z.letzteZeit + 0.1) z.letzteBewegung = Date.now();
      z.letzteZeit = info.currentTime;
    }
    if (Array.isArray(info.availableQualityLevels) && info.availableQualityLevels.length) z.qualitaet = info.availableQualityLevels;
    if (typeof info.playbackQuality === "string") z.stufe = info.playbackQuality;
  }

  pruefe(rest) {
    const z = this.z; if (!this.id || !z || this.einspieler) return;
    const jetzt = Date.now(), alter = (jetzt - z.start) / 1000;
    const geschuetzt = !!(this.aktuell && this.aktuell.geschuetzt);
    if (!z.angemeldet && alter > 3 && alter < 15) this.anmelden();
    if (z.status === 1) z.laeuft = true;
    if (z.status === 3) z.puffer += 1;
    if (!z.angemeldet) return;
    if (!z.laeuft && alter > PRUEFUNG.startetNichtS) return this.strike("startet_nicht");
    if (z.puffer > PRUEFUNG.puffertS) return this.strike("puffert");
    if (z.status === 1 && (jetzt - z.letzteBewegung) / 1000 > PRUEFUNG.stehtS) return this.strike("steht");
    // Läuft unter der Mindeststufe, obwohl mehr angeboten wird – nach schlecht_s am Stück weiter
    const angebotGut = z.qualitaet && z.qualitaet.some((q) => STUFEN.includes(q) && this.gut(q));
    if (!geschuetzt && z.laeuft && alter > 20 && z.qualitaet && !angebotGut) return this.strike("aufloesung");
    const unter = !geschuetzt && z.status === 1 && STUFEN.includes(z.stufe) && !this.gut(z.stufe) && angebotGut;
    z.schlechtSeit = unter ? (z.schlechtSeit || jetzt) : null;
    if (unter && (jetzt - z.schlechtSeit) / 1000 > this.regeln.schlecht_s) {
      if (!z.startGemeldet) { z.startGemeldet = true; this.meldeStufe("start"); }
      return this.strike("aufloesung");
    }
    if (z.laeuft && !z.startGemeldet && alter > PRUEFUNG.startMeldenS) { z.startGemeldet = true; this.meldeStufe("start"); }
    if (z.laeuft && z.startGemeldet && !z.endeGemeldet && rest > 0 && rest <= PRUEFUNG.endeVorWechselS) {
      z.endeGemeldet = true; this.meldeStufe("ende");
    }
  }

  meldeStufe(phase) {
    const z = this.z;
    const beste = (z.qualitaet || []).filter((q) => STUFEN.includes(q))
      .sort((a, b) => STUFEN.indexOf(b) - STUFEN.indexOf(a))[0] || "unknown";
    const stufe = STUFEN.includes(z.stufe) || z.stufe === "auto" ? z.stufe : "unknown";
    melde("qualitaet", { video_id: this.id, stufe, beste, phase });
  }

  strike(grund) {
    const id = this.id; if (!id) return;
    this.gesperrt[id] = Date.now() + (this.regeln.sperre_s || 7200) * 1000;
    if (this.vorrang && this.vorrang.video_id === id) this.vorrang = null;
    melde("strike", { video_id: id, grund });
    this.tick();
  }
}

function melde(art, daten) {
  fetch(`/meldung/${art}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(daten) })
    .catch(() => {});
}
