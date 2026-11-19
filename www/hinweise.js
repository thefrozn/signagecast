// Lesbarkeits-Hinweise (seit 0.60): misst auf der fertig gezeichneten TV-Seite je Baustein die echten Schriftgrößen,
// den Kontrast zwischen Schrift und deckendem Hintergrund und ob der Inhalt hineinpasst. Dieselben Regeln nutzen der
// Layout-Designer (Live-Vorschau, seit 0.58) und das MCP-Werkzeug „preview“ (?vorschau=1&hinweise=1: das Ergebnis
// steht nach dem Zeichnen als JSON in #sc-hinweise, der Server liest es aus dem DOM). Ergebnis ohne Sprache:
// { "<Baustein-id>": [{art: "klein", px}, {art: "kontrast", wert}, {art: "ueberlauf"}] }
"use strict";
(function () {
  const SCHRIFT_MIN = 18;     // px bei 1920 × 1080: größte Schrift im Baustein darunter = „Schrift klein“
  const SCHRIFT_NEBEN = 12;   // Nebentexte (z. B. Tiefstwert der Vorhersage) dürfen kleiner sein, aber nicht darunter
  const KONTRAST_MIN = 3;     // WCAG für große Schrift
  function kontrast(a, b) {
    const lum = (c) => {
      const [r, g, bl] = (c.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map((v) => { v = Number(v) / 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; });
      return 0.2126 * r + 0.7152 * g + 0.0722 * bl;
    };
    const [h, d] = [lum(a), lum(b)].sort((x, y) => y - x);
    return (h + 0.05) / (d + 0.05);
  }
  const alpha = (c) => { const m = (c || "").match(/rgba?\(([^)]+)\)/); if (!m) return 0; const t = m[1].split(","); return t.length > 3 ? Number(t[3]) : 1; };
  function messen(doc) {
    doc = doc || document;
    const win = doc.defaultView, w = {};
    for (const b of doc.querySelectorAll(".baustein[data-id]")) {
      if (!b.offsetWidth || win.getComputedStyle(b).display === "none") continue;
      const liste = [];
      let klein = Infinity, gross = 0, schwach = Infinity;
      const gehe = doc.createTreeWalker(b, 4);         // Textknoten
      for (let t = gehe.nextNode(); t; t = gehe.nextNode()) {
        const p = t.parentElement;
        if (!t.nodeValue.trim() || !p || p.closest(".mdi") || !p.getClientRects().length) continue;
        const st = win.getComputedStyle(p);
        if (st.visibility === "hidden" || Number(st.opacity) === 0) continue;
        klein = Math.min(klein, parseFloat(st.fontSize)); gross = Math.max(gross, parseFloat(st.fontSize));
        for (let a = p; a && a !== b.parentElement; a = a.parentElement) {     // Hintergrund: erster deckender Vorfahr im Baustein
          const bg = win.getComputedStyle(a).backgroundColor;
          if (alpha(bg) >= 0.6) { schwach = Math.min(schwach, kontrast(st.color, bg)); break; }
        }
      }
      if (gross && gross < SCHRIFT_MIN) liste.push({ art: "klein", px: Math.round(gross) });
      else if (klein < SCHRIFT_NEBEN) liste.push({ art: "klein", px: Math.round(klein) });
      if (schwach < KONTRAST_MIN) liste.push({ art: "kontrast", wert: Math.round(schwach * 10) / 10 });
      if (!b.classList.contains("laufband") && !b.querySelector(".laufband") && (b.scrollHeight > b.clientHeight + 4 || b.scrollWidth > b.clientWidth + 4)) liste.push({ art: "ueberlauf" });
      if (liste.length) w[b.dataset.id] = liste;
    }
    return w;
  }
  window.scHinweise = messen;
  if (/[?&]hinweise=1(&|$)/.test(location.search)) {
    setTimeout(() => {
      const s = document.createElement("script");
      s.type = "application/json"; s.id = "sc-hinweise";
      try { s.textContent = JSON.stringify(messen(document)); } catch (f) { s.textContent = JSON.stringify({ fehler: String(f) }); }
      document.body.appendChild(s);
    }, 9000);
  }
})();
