#!/bin/sh
# SignageCast – Render-Kette für EINEN Fernseher. MediaMTX startet sie auf Abruf, sobald jemand http://<IP>:8888/<id>
# öffnet (MTX_PATH = Kennung des Fernsehers), und beendet sie, wenn niemand mehr zuschaut.
# Xvfb + Chromium zeigen die TV-Seite (http://127.0.0.1:8080/?tv=<id>) in Full HD und spielen den Ton (Radio oder
# Tierton) in einen eigenen virtuellen Tonkanal (PulseAudio-Null-Sink); ffmpeg nimmt Bild und Ton auf, die
# Grafikeinheit (VAAPI) rechnet auf die Ausgabegröße hoch und kodiert H.265, der Ton wird AAC. Ohne nutzbare Grafik
# (KODIERUNG=software, erkennt der Datendienst) kodiert die CPU H.264 in Full HD.
# Werte je Fernseher (Bildschirm, DevTools-Port, Größe, Bitrate) aus /var/lib/signagecast/render-<id>.env (Datendienst).
set -u
TV=${MTX_PATH:-tv}
case "$TV" in *[!a-z0-9]*|"") echo "ungültige Kennung"; exit 1;; esac
DATEN=/var/lib/signagecast
DISP=:99; DEVPORT=9222; AUSGABE="3840 2160"; BITRATE=16; KODIERUNG=vaapi; CODEC=h265; TON=live
[ -r "$DATEN/render-$TV.env" ] && . "$DATEN/render-$TV.env"
OW=${AUSGABE% *}; OH=${AUSGABE#* }
W=1920; H=1080                                   # Chromium zeichnet in Full HD (in 4K wäre er überlastet)
PROFIL=$DATEN/chromium-$TV
ERW=/opt/signagecast/render/h264-fluessig
# Docker gibt /dev/shm nur 64 MB – zu wenig für Chromium; dann nimmt er /tmp
SHM=""; [ "$(df -Pk /dev/shm 2>/dev/null | awk 'NR==2 {print $2}')" -lt 524288 ] 2>/dev/null && SHM=--disable-dev-shm-usage
SINK=tv_$TV
export XDG_RUNTIME_DIR=$DATEN/run
export PULSE_SERVER=unix:$XDG_RUNTIME_DIR/pulse/native
PIDS=$DATEN/kette-$TV.pids
echo $$ > "$DATEN/kette-$TV.skript"       # damit die Verwaltung genau diese Kette neu starten kann

# Reste einer früheren Kette DIESES Fernsehers entfernen (Sitzungen aus der PID-Datei; andere Fernseher bleiben)
if [ -r "$PIDS" ]; then
  for s in $(cat "$PIDS"); do pkill -KILL -s "$s" 2>/dev/null; done
fi
rm -f "/tmp/.X${DISP#:}-lock" "/tmp/.X11-unix/X${DISP#:}"
rm -rf "$PROFIL/Default/VideoDecodeStats"     # Chromium soll alte Bildverluste vergessen (sonst meldet er "nicht flüssig")

# Ton: ein PulseAudio für alle Fernseher (endet 60 s nach dem letzten Nutzer), je Fernseher ein Null-Sink
mkdir -p "$XDG_RUNTIME_DIR" && chmod 700 "$XDG_RUNTIME_DIR"
pactl info >/dev/null 2>&1 || pulseaudio --daemonize=yes --exit-idle-time=60 -n \
  -L "module-native-protocol-unix" -L "module-always-sink" >/dev/null 2>&1
for _ in 1 2 3 4 5; do pactl info >/dev/null 2>&1 && break; sleep 0.5; done
pactl list short sinks 2>/dev/null | grep -q "	$SINK	" || \
  pactl load-module module-null-sink sink_name="$SINK" sink_properties=device.description="$SINK" >/dev/null 2>&1

# Aufräumen: ganze Sitzungen beenden. Wichtig: /usr/bin/kill bzw. pkill – das kill von dash kennt weder "--" noch
# negative PIDs (Prozessgruppen); sonst bleiben ffmpeg/Xvfb übrig (schwarzes Bild).
aufraeumen() {
  for p in ${FF:-} ${CR:-} ${XV:-}; do /usr/bin/kill -TERM -- "-$p" 2>/dev/null; done
  sleep 2
  for p in ${FF:-} ${CR:-} ${XV:-}; do pkill -KILL -s "$p" 2>/dev/null; done
  [ -n "${LESER:-}" ] && kill "$LESER" 2>/dev/null
  rm -f "$PIDS" "$DATEN/kette-$TV.skript" "$FIFO" "$FORTSCHRITT"
}
trap 'aufraeumen; exit 0' INT TERM
trap aufraeumen EXIT

setsid Xvfb $DISP -screen 0 ${W}x${H}x24 -nolisten tcp -nocursor & XV=$!
echo "$XV" > "$PIDS"
sleep 1
# Erweiterung h264-fluessig: meldet YouTube H.264 bis 1080p als flüssig (ohne Hardware-Dekodierung sagt Chromium
# sonst "nicht flüssig" und YouTube liefert nur 144p). DevTools nur lokal: daraus liest die Wache die Qualität.
PULSE_SINK=$SINK LANG=de_DE.UTF-8 LANGUAGE=de DISPLAY=$DISP setsid chromium --lang=de-DE --accept-lang=de-DE,de,en \
  --kiosk --no-sandbox --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble \
  --disable-features=Translate,TranslateUI,MediaRouter,DisableLoadExtensionCommandLineSwitch --disable-translate \
  --check-for-update-interval=31536000 --autoplay-policy=no-user-gesture-required --force-device-scale-factor=1 \
  --window-position=0,0 --window-size=${W},${H} --user-data-dir="$PROFIL" \
  --remote-debugging-port=$DEVPORT --remote-debugging-address=127.0.0.1 --load-extension="$ERW" $SHM \
  "http://127.0.0.1:8080/?tv=$TV" >/dev/null 2>&1 & CR=$!
echo "$CR" >> "$PIDS"
sleep 12   # Seite und Videos laden lassen

if [ "$KODIERUNG" = software ]; then
  # Notbetrieb ohne Grafik: H.264 Full HD per CPU (ca. 1–2 Kerne), höchstens 8 Mbit/s
  [ "$BITRATE" -gt 8 ] && BITRATE=8
  VIDEO="-c:v libx264 -preset veryfast -tune zerolatency -pix_fmt yuv420p"
else
  # H.265 (4K, kleiner) oder H.264 (läuft auf praktisch jedem Fernseher/Browser) – beides über die Grafikeinheit
  if [ "$CODEC" = h264 ]; then ENC="h264_vaapi -profile:v high"; else ENC="hevc_vaapi -profile:v main"; fi
  VIDEO="-vaapi_device /dev/dri/renderD128 -vf hwupload,scale_vaapi=w=${OW}:h=${OH}:format=nv12 -c:v $ENC"
fi
# Ton: nur wenn auf diesem Fernseher Ton laufen kann (TON=live) aus PulseAudio – ein Echtzeit-Toneingang lässt ffmpeg
# bei x11grab viele Bilder doppeln (Ruckeln); ohne Ton daher eine stille Spur (HLS-Player erwarten eine Tonspur).
if [ "$TON" = stille ]; then TONEINGANG="-f lavfi -i anullsrc=r=48000:cl=stereo"; else TONEINGANG="-f pulse -i $SINK.monitor"; fi
# Fortschritt von ffmpeg (Bildrate, Tempo, doppelte/verworfene Bilder) für den Leistungstest: alle 2 s ein Block über
# eine benannte Pipe; nur der letzte Block bleibt im Arbeitsspeicher (/dev/shm) – nichts wächst, nichts auf die Platte.
FORTSCHRITT=/dev/shm/signagecast-ff-$TV; FIFO=$FORTSCHRITT.fifo
rm -f "$FIFO"; mkfifo -m 600 "$FIFO"
( blk=""; while IFS= read -r z; do blk="$blk$z
"; case $z in progress=*) printf '%s' "$blk" > "$FORTSCHRITT.neu" && mv -f "$FORTSCHRITT.neu" "$FORTSCHRITT"; blk="";; esac
  done ) < "$FIFO" & LESER=$!
setsid ffmpeg -hide_banner -loglevel error -nostats -stats_period 2 -progress "$FIFO" -thread_queue_size 512 -f x11grab -draw_mouse 0 -framerate 25 \
  -video_size ${W}x${H} -i $DISP -thread_queue_size 512 $TONEINGANG \
  $VIDEO -b:v ${BITRATE}M -maxrate $((BITRATE * 5 / 4))M -bufsize $((BITRATE * 2))M -g 50 -bf 0 \
  -c:a aac -b:a 128k -ac 2 \
  -f rtsp -rtsp_transport tcp "rtsp://127.0.0.1:${RTSP_PORT:-8554}/$TV" & FF=$!
echo "$FF" >> "$PIDS"

# Wache: endet ffmpeg oder fehlt der Browser 15 s lang, ganze Kette beenden (MediaMTX startet neu, solange jemand
# schaut) – sonst würde ein leerer Bildschirm gestreamt. "sleep & wait", damit Signale sofort wirken.
fehlt=0
while kill -0 "$FF" 2>/dev/null && [ $fehlt -lt 3 ]; do
  if kill -0 "$CR" 2>/dev/null; then fehlt=0; else fehlt=$((fehlt + 1)); fi
  sleep 5 & wait $!
done
