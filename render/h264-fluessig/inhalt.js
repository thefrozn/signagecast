// Chromium im Render-Container dekodiert Videos ohne Grafikeinheit in Software. H.264 ist dabei am günstigsten,
// VP9 und vor allem AV1 kosten deutlich mehr CPU (gemessen 2026-11-06 auf CT 103: AV1 1080p ~160 % statt ~113 % eines
// Kerns mit H.264). Deshalb:
// 1. VP9 und AV1 als „nicht unterstützt“ melden (wie h264ify) – dann bleibt YouTube bei H.264. „Nur nicht flüssig“
//    reicht nicht: YouTube fragt auch MediaSource.isTypeSupported/canPlayType und nahm sonst trotzdem AV1.
// 2. H.264 bis zur Aufnahmehöhe (höchstens 1080p, 30 fps) als „flüssig“ melden – ohne Grafikeinheit sagt Chromium
//    sonst über 144p „nicht flüssig“ und YouTube liefert nur 144p (gemessen 2026-10-28: 1080p30 ohne Bildverlust).
//    Größer als die Aufnahme bringt nichts (720p-Aufnahme → 720p-Video).
(() => {
  const teuer = (typ) => /vp0?9|av01|av1/i.test(String(typ || ""));
  const hoehe = () => Math.min(1080, Math.round(screen.height * (window.devicePixelRatio || 1)) || 1080);

  if (window.MediaSource && MediaSource.isTypeSupported) {
    const orig = MediaSource.isTypeSupported.bind(MediaSource);
    MediaSource.isTypeSupported = (typ) => !teuer(typ) && orig(typ);
  }
  const cpt = HTMLMediaElement.prototype.canPlayType;
  HTMLMediaElement.prototype.canPlayType = function (typ) { return teuer(typ) ? "" : cpt.call(this, typ); };

  const mc = navigator.mediaCapabilities;
  if (!mc || !mc.decodingInfo) return;
  const original = mc.decodingInfo.bind(mc);
  mc.decodingInfo = async (cfg) => {
    const v = cfg && cfg.video;
    const typ = (v && v.contentType) || "";
    if (v && teuer(typ)) return { supported: false, smooth: false, powerEfficient: false, keySystemAccess: null };
    const r = await original(cfg);
    if (r.supported && v && /avc1/.test(typ)) {
      const ok = (v.height || 0) <= hoehe() && (v.framerate || 0) <= 30;
      return { supported: true, smooth: ok, powerEfficient: ok, keySystemAccess: r.keySystemAccess || null };
    }
    return r;
  };
})();
