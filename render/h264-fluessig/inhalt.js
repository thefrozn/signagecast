// Chromium im Render-Container dekodiert H.264 ohne Grafikeinheit und meldet es über 144p als "nicht flüssig" –
// YouTube liefert solche Streams dann nur in 144p. Gemessen (2026-10-28): H.264 1080p30 läuft ohne verlorene Bilder.
// Deshalb hier bis 1080p "flüssig" melden; alles andere bleibt unverändert.
(() => {
  const mc = navigator.mediaCapabilities;
  if (!mc || !mc.decodingInfo) return;
  const original = mc.decodingInfo.bind(mc);
  mc.decodingInfo = async (cfg) => {
    const r = await original(cfg);
    const v = cfg && cfg.video;
    if (r.supported && v && /avc1/.test(v.contentType || "") && (v.height || 0) <= 1080 && (v.framerate || 0) <= 30)
      return { supported: true, smooth: true, powerEfficient: r.powerEfficient, keySystemAccess: r.keySystemAccess || null };
    return r;
  };
})();
