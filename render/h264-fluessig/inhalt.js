// Chromium im Render-Container dekodiert H.264 ohne Grafikeinheit und meldet es über 144p als "nicht flüssig" –
// YouTube liefert solche Streams dann nur in 144p. Gemessen (2026-10-28): H.264 1080p30 läuft ohne verlorene Bilder.
// Deshalb hier bis 1080p "flüssig" melden (seit 0.29 höchstens Aufnahmegröße) und VP9/AV1 als "nicht flüssig".
(() => {
  const mc = navigator.mediaCapabilities;
  if (!mc || !mc.decodingInfo) return;
  const original = mc.decodingInfo.bind(mc);
  mc.decodingInfo = async (cfg) => {
    const r = await original(cfg);
    const v = cfg && cfg.video;
    const typ = (v && v.contentType) || "";
    // Seit 0.29: höchstens in der Größe der Aufnahme (720p-Aufnahme → 720p-Video, spart Dekodieren)
    const hoehe = Math.min(1080, Math.round(screen.height * (window.devicePixelRatio || 1)) || 1080);
    if (r.supported && v && /avc1/.test(typ) && (v.height || 0) <= hoehe && (v.framerate || 0) <= 30)
      return { supported: true, smooth: true, powerEfficient: true, keySystemAccess: r.keySystemAccess || null };
    if (r.supported && v && /avc1/.test(typ) && (v.height || 0) > hoehe)    // größer als die Aufnahme bringt nichts
      return { supported: true, smooth: false, powerEfficient: false, keySystemAccess: r.keySystemAccess || null };
    // VP9 und AV1 dekodiert die CPU deutlich teurer als H.264 – als „nicht flüssig“ melden, dann nimmt YouTube H.264
    if (r.supported && v && /^video\/webm|vp09|vp9|av01/.test(typ))
      return { supported: true, smooth: false, powerEfficient: false, keySystemAccess: r.keySystemAccess || null };
    return r;
  };
})();
